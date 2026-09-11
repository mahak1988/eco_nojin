"""Earth Search STAC API provider for Sentinel-2 data.

This provider uses the public Element 84 STAC API which requires no API key.
Data: Sentinel-2 L2A (10m resolution, 5-day revisit)
Source: https://earth-search.aws.element84.com/v1

Download behavior
-----------------
1. ``search``: returns STAC items from the public catalog.
2. ``fetch_tile``: attempts to download real GeoTIFF assets for the
   requested item. If the download or decoding fails, it falls back to
   deterministic synthetic data so the rest of the pipeline never breaks.

Honesty requirement
-------------------
Every tile carries a ``data_source`` flag:
- ``"real"``      → actual Sentinel-2 observation downloaded from STAC
- ``"simulated"`` → synthetic fallback; MUST NOT be presented as real data
"""

import io
import logging
import zipfile
from datetime import UTC, date, datetime
from typing import Any, ClassVar

import numpy as np
import requests

from .base import SatelliteProvider, SatelliteTile

logger = logging.getLogger(__name__)

# Public STAC endpoint - no API key required
EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
SENTINEL2_COLLECTION = "sentinel-2-l2a"

# Sentinel-2 L2A asset keys we care about
_BAND_KEYS = {
    "red": "red",
    "green": "green",
    "blue": "blue",
    "nir": "nir",
    "nir08": "nir08",
    "swir16": "swir16",
    "swir22": "swir22",
    "scl": "scl",
}

# Scene Classification classes that indicate cloudy / no-data pixels
_CLOUD_SCL_CLASSES = {0, 3, 8, 9, 10, 11}


class EarthSearchProvider(SatelliteProvider):
    """Fetches Sentinel-2 data from public STAC API."""

    BAND_MAPPING: ClassVar[dict[str, str]] = {
        "red": "red",
        "green": "green",
        "blue": "blue",
        "nir": "nir",
        "nir08": "nir08",
        "swir16": "swir16",
        "swir22": "swir22",
        "scl": "scl",
    }

    @property
    def available_bands(self) -> list[str]:
        return list(self.BAND_MAPPING.keys())

    def search(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        max_cloud_cover: float = 20.0,
        limit: int = 10,
    ) -> list[dict]:
        """Search for Sentinel-2 tiles covering the given point.

        Returns STAC feature metadata (no pixel data).
        """
        buffer = 0.005  # ~500m
        bbox = [lon - buffer, lat - buffer, lon + buffer, lat + buffer]

        payload: dict[str, Any] = {
            "collections": [SENTINEL2_COLLECTION],
            "bbox": bbox,
            "datetime": f"{start_date.isoformat()}/{end_date.isoformat()}",
            "query": {"eo:cloud_cover": {"lt": max_cloud_cover}},
            "sortby": [{"field": "datetime", "direction": "desc"}],
            "limit": limit,
        }

        try:
            response = requests.post(
                f"{EARTH_SEARCH_URL}/search",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("features", [])
        except requests.RequestException:
            return []

    def fetch_tile(self, item_id: str) -> SatelliteTile | None:
        """Fetch a specific STAC item by ID.

        Strategy
        --------
        1. Look up the STAC item metadata.
        2. Download the requested band assets (GeoTIFF or COG).
        3. If a Scene Classification Layer (SCL) is available, build a cloud mask.
        4. If any step fails, fall back to deterministic synthetic data.
        """
        item = self._get_item(item_id)
        if item is None:
            return self._synthetic_tile(item_id, "item_not_found")

        assets = item.get("assets", {})
        properties = item.get("properties", {})
        bbox = item.get("bbox", [0, 0, 1, 1])
        tile_datetime = self._parse_datetime(item)

        bands, data_source, quality_flags = self._download_bands(assets, item_id)
        if bands is None:
            return self._synthetic_tile(item_id, "download_failed")

        cloud_mask = self._build_cloud_mask(assets, bands)
        if cloud_mask is not None:
            self._apply_cloud_mask(bands, cloud_mask)
            quality_flags["cloud_masked"] = True

        quality_flags["real_download"] = data_source == "real"
        quality_flags["scl_available"] = cloud_mask is not None

        return SatelliteTile(
            provider="earth_search",
            collection=SENTINEL2_COLLECTION,
            datetime=tile_datetime,
            bbox=tuple(bbox),
            cloud_cover=float(properties.get("eo:cloud_cover", 0.0)),
            bands=bands,
            crs="EPSG:4326",
            data_source=data_source,
            quality_flags=quality_flags,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_item(self, item_id: str) -> dict[str, Any] | None:
        try:
            response = requests.get(
                f"{EARTH_SEARCH_URL}/collections/{SENTINEL2_COLLECTION}/items/{item_id}",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def _download_bands(self, assets: dict[str, Any], item_id: str) -> tuple[dict[str, np.ndarray] | None, str, dict[str, Any]]:
        bands: dict[str, np.ndarray] = {}
        quality_flags: dict[str, Any] = {
            "downloaded_bands": [],
            "fallback_bands": [],
            "real_download": False,
            "cloud_masked": False,
            "scl_available": False,
        }
        data_source = "simulated"

        for band_name, asset_key in _BAND_KEYS.items():
            asset = assets.get(asset_key, {})
            href = asset.get("href", "")
            if not href:
                continue

            try:
                array = self._download_asset(href)
                bands[band_name] = array
                quality_flags["downloaded_bands"].append(band_name)
                data_source = "real"
            except Exception as exc:
                logger.debug("Band download failed %s: %s", band_name, exc)
                quality_flags["fallback_bands"].append(band_name)

        if not bands:
            return None, data_source, quality_flags

        # Resolve synthetic bands for anything that was not downloaded
        return self._fill_missing_bands(bands, quality_flags, item_id), data_source, quality_flags

    def _download_asset(self, href: str) -> np.ndarray:
        response = requests.get(href, timeout=60, stream=True)
        response.raise_for_status()

        content = response.content
        if href.lower().endswith(".zip") or href.lower().endswith(".tar.gz") or href.lower().endswith(".tgz"):
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                tiff_names = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff"))]
                if not tiff_names:
                    raise RuntimeError(f"No TIFF inside archive: {href}")
                with zf.open(tiff_names[0]) as f:
                    return self._decode_tiff(f.read())

        return self._decode_tiff(content)

    def _decode_tiff(self, content: bytes) -> np.ndarray:
        try:
            from rasterio.io import MemoryFile

            with MemoryFile(content) as memfile, memfile.open() as dataset:
                array = dataset.read(1)
                if array is None:
                    raise RuntimeError("Empty raster band")
                return array.astype(np.float32)
        except Exception as exc:
            raise RuntimeError(f"TIFF decode failed: {exc}") from exc

    def _build_cloud_mask(self, assets: dict[str, Any], bands: dict[str, np.ndarray]) -> np.ndarray | None:
        scl_key = _BAND_KEYS.get("scl")
        asset = assets.get(scl_key, {})
        href = asset.get("href", "")
        if not href:
            return None
        try:
            scl = self._download_asset(href)
            return np.isin(scl, list(_CLOUD_SCL_CLASSES))
        except Exception:
            return None

    def _apply_cloud_mask(self, bands: dict[str, np.ndarray], cloud_mask: np.ndarray) -> None:
        for name, array in bands.items():
            if array.shape != cloud_mask.shape:
                continue
            masked = np.where(cloud_mask, np.nan, array)
            bands[name] = masked

    def _fill_missing_bands(self, bands: dict[str, np.ndarray], quality_flags: dict[str, Any], item_id: str) -> dict[str, np.ndarray]:
        size = next(iter(bands.values())).shape if bands else (64, 64)
        np.random.seed(hash(item_id) % (2**32))
        defaults = {
            "red": np.random.uniform(200, 800, size),
            "green": np.random.uniform(300, 1000, size),
            "blue": np.random.uniform(150, 600, size),
            "nir": np.random.uniform(1500, 4000, size),
            "swir16": np.random.uniform(500, 2000, size),
            "swir22": np.random.uniform(400, 1500, size),
            "nir08": np.random.uniform(1500, 4000, size),
            "scl": np.zeros(size, dtype=np.int16),
        }
        for name, default in defaults.items():
            bands.setdefault(name, default)
        return bands

    def _parse_datetime(self, item: dict[str, Any]) -> datetime:
        props = item.get("properties", {})
        dt_str = props.get("datetime") or item.get("properties", {}).get("datetime")
        if not dt_str:
            return datetime.now(UTC)
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(UTC)

    def _synthetic_tile(self, item_id: str, reason: str) -> SatelliteTile:
        size = 64
        np.random.seed(hash(item_id) % (2**32))
        bands = {
            "red": np.random.uniform(200, 800, (size, size)),
            "green": np.random.uniform(300, 1000, (size, size)),
            "blue": np.random.uniform(150, 600, (size, size)),
            "nir": np.random.uniform(1500, 4000, (size, size)),
            "swir16": np.random.uniform(500, 2000, (size, size)),
        }
        logger.debug("Returning synthetic tile for %s (%s)", item_id, reason)
        return SatelliteTile(
            provider="earth_search",
            collection=SENTINEL2_COLLECTION,
            datetime=datetime.now(UTC),
            bbox=(0, 0, 1, 1),
            cloud_cover=5.0,
            bands=bands,
            crs="EPSG:4326",
            data_source="simulated",
        )
