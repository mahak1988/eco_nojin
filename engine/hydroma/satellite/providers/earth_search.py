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
- ``"real"``            -> actual Sentinel-2 observation downloaded from STAC
- ``"partially_synthetic"`` -> at least one band downloaded, at least one
  FABRICATED (see below). The real bands are measurements; the others are not.
- ``"simulated"``       -> synthetic fallback; MUST NOT be presented as real data

Why ``partially_synthetic`` exists
----------------------------------
``_fill_missing_bands`` fills in every Sentinel-2 band that failed to download
with ``np.random.uniform(...)`` drawn from a plausible reflectance range. That
is a fabrication, and before this revision nothing said so: the tile kept its
real ``item_id``, ``datetime`` and ``eo:cloud_cover``, its ``data_source`` was
set to ``"real"`` by the mere fact that *one* band succeeded, and the fabricated
arrays went straight into NDVI/EVI/SAVI/NDWI/NBR, vegetation classification and
everything downstream of those. A reader of the tile could not tell which pixels
were invented.

So a tile now reports:

* ``data_source`` -- downgraded to ``"partially_synthetic"`` as soon as any
  band is fabricated, so it cannot be read as an observation;
* ``quality_flags["synthetic_bands"]`` -- which bands are fabricated;
* ``quality_flags["synthetic"]`` / ``["synthetic_pixels"]`` -- booleans, so a
  consumer does not have to parse the list to notice;
* ``quality_flags["reason"]`` -- a named reason, in the S-HONEST vocabulary.

``quality_flags`` is the field that survives, and it is not the only one any
more. ``SatelliteAnalyzer.analyze_point`` copies it onto the ``FieldAnalysis``
it returns, and as of the fix that closed the label gap it also derives that
result's ``data_source`` from *this tile's* ``data_source`` and flags:
``"real"`` becomes ``"measured"``, ``"partially_synthetic"`` becomes
``"degraded"``, and anything else becomes ``"simulated"``. See
``engine/hydroma/satellite/analyzer.py::_analysis_data_source``.

Before that fix the flag survived and the label did not. ``analyze_point``
copied ``quality_flags`` onto the result and then hard-coded its own
``data_source`` to ``"measured"``, so a tile that had just recorded five
fabricated bands reported ``data_source="measured"`` next to
``quality_flags["synthetic"] = True`` -- the truth in the payload and a
contradicting label beside it.

Determinism
-----------
The random draws are seeded from ``hashlib.blake2b(item_id)``, not from
``hash(item_id)``. Python salts ``str.__hash__`` per process (PEP 456), so the
old seed produced a different "deterministic" scene on every interpreter start;
a tile fetched twice was never reproducible and could not be cached, compared
or diffed. The generator is a local ``np.random.default_rng`` rather than a call
to ``np.random.seed``, which was additionally reseeding the whole process-global
NumPy RNG from inside a network provider.
"""

import hashlib
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

#: Plausible Sentinel-2 L2A surface-reflectance ranges (scaled DN) used when a
#: band cannot be downloaded. The values are chosen to sit in the real sensor
#: range so downstream indices do not blow up -- which is exactly why they are
#: dangerous. A fabricated band that produces a plausible NDVI is a fabricated
#: band, and the whole point of ``SYNTHETIC_BANDS`` is that it is declared.
_SYNTHETIC_BAND_RANGES: dict[str, tuple[float, float]] = {
    "red": (200.0, 800.0),
    "green": (300.0, 1000.0),
    "blue": (150.0, 600.0),
    "nir": (1500.0, 4000.0),
    "nir08": (1500.0, 4000.0),
    "swir16": (500.0, 2000.0),
    "swir22": (400.0, 1500.0),
}
_SYNTHETIC_SCL = 0


def stable_seed(item_id: str) -> int:
    """A reproducible seed for ``item_id``, identical across processes.

    ``hash(item_id)`` is NOT usable for this. ``str.__hash__`` is salted per
    interpreter process (PEP 456), so ``hash("S2A_x")`` differs between runs
    and the "deterministic" fallback scene was different every time the process
    started -- unverifiable, uncacheable and unreproducible. ``blake2b`` is a
    fixed, documented cryptographic hash with no per-process salt.
    """
    return int.from_bytes(hashlib.blake2b(item_id.encode("utf-8"), digest_size=8).digest(), "big")


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
            features: list[dict[str, Any]] = data.get("features", [])
            return features
        except requests.RequestException:
            return []

    # Every return path yields a tile: the fallback helper builds a synthetic
    # one when the item or a band is missing, so the base class's non-optional
    # SatelliteTile is the honest signature.
    def fetch_tile(self, item_id: str) -> SatelliteTile:
        """Fetch a specific STAC item by ID.

        Strategy
        --------
        1. Look up the STAC item metadata.
        2. Download the requested band assets (GeoTIFF or COG).
        3. If a Scene Classification Layer (SCL) is available, build a cloud mask.
        4. If any step fails, fall back to deterministic synthetic data.

        The returned tile's ``data_source`` is ``"real"`` only when every band
        is a real download. A partial download that needed a fabricated band
        returns ``"partially_synthetic"``, and the same fact is repeated in
        ``quality_flags["synthetic_bands"]``. Before this revision step 2
        succeeding once was enough to label the whole tile ``"real"``, while
        the missing bands -- including NIR, which NDVI needs -- were filled with
        ``np.random.uniform`` values and nothing recorded it.
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
            item: dict[str, Any] = response.json()
            return item
        except requests.RequestException:
            return None

    def _download_bands(
        self, assets: dict[str, Any], item_id: str
    ) -> tuple[dict[str, np.ndarray] | None, str, dict[str, Any]]:
        bands: dict[str, np.ndarray] = {}
        quality_flags: dict[str, Any] = {
            "downloaded_bands": [],
            "fallback_bands": [],
            "synthetic_bands": [],
            "synthetic": False,
            "synthetic_pixels": False,
            "real_download": False,
            "cloud_masked": False,
            "scl_available": False,
        }
        real_downloads = 0

        for band_name, asset_key in _BAND_KEYS.items():
            asset = assets.get(asset_key, {})
            href = asset.get("href", "")
            if not href:
                continue

            try:
                array = self._download_asset(href)
                bands[band_name] = array
                quality_flags["downloaded_bands"].append(band_name)
                real_downloads += 1
            except Exception as exc:
                logger.debug("Band download failed %s: %s", band_name, exc)
                quality_flags["fallback_bands"].append(band_name)

        if not bands:
            return None, "simulated", quality_flags

        bands, data_source = self._fill_missing_bands(bands, quality_flags, item_id)

        # The flag is derived from what was ACTUALLY fabricated, not from
        # whether at least one download succeeded. ``data_source = "real"`` on
        # the strength of one surviving band is what let fabricated NIR reach
        # NDVI while the tile advertised itself as an observation.
        quality_flags["real_download"] = real_downloads > 0 and not quality_flags["synthetic_bands"]
        quality_flags["synthetic"] = bool(quality_flags["synthetic_bands"])
        quality_flags["synthetic_pixels"] = quality_flags["synthetic"]
        if quality_flags["synthetic_bands"]:
            quality_flags["reason"] = "fabricated_bands"
            quality_flags["synthetic_band_note"] = (
                f"{len(quality_flags['synthetic_bands'])} of "
                f"{len(_BAND_KEYS)} bands ({', '.join(sorted(quality_flags['synthetic_bands']))}) "
                "were not downloaded and were replaced by random values in a "
                "plausible reflectance range. Any index, classification or "
                "carbon derivation that uses them is not a measurement."
            )
        return bands, data_source, quality_flags

    def _download_asset(self, href: str) -> np.ndarray:
        response = requests.get(href, timeout=60, stream=True)
        response.raise_for_status()

        content = response.content
        if (
            href.lower().endswith(".zip")
            or href.lower().endswith(".tar.gz")
            or href.lower().endswith(".tgz")
        ):
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
                decoded: np.ndarray = array.astype(np.float32)
                return decoded
        except Exception as exc:
            raise RuntimeError(f"TIFF decode failed: {exc}") from exc

    def _build_cloud_mask(
        self, assets: dict[str, Any], bands: dict[str, np.ndarray]
    ) -> np.ndarray | None:
        scl_key = _BAND_KEYS.get("scl")
        if scl_key is None:
            # A None key misses the assets dict below and leaves the href
            # empty, which is exactly this early return.
            return None
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

    def _fill_missing_bands(
        self, bands: dict[str, np.ndarray], quality_flags: dict[str, Any], item_id: str
    ) -> tuple[dict[str, np.ndarray], str]:
        """Fill in bands that failed to download, and record that we did.

        Returns ``(bands, data_source)`` where ``data_source`` is ``"real"`` only
        when every band is a real download. Anything else returns
        ``"partially_synthetic"`` (or ``"simulated"`` if nothing was downloaded,
        which ``_download_bands`` handles before calling this) so that a tile
        containing invented pixels cannot be read as an observation.

        The seed comes from :func:`stable_seed`, so the same ``item_id`` yields
        the same fabricated scene in every process and on every machine.
        """
        if not bands:
            return bands, "simulated"

        size = next(iter(bands.values())).shape
        rng = np.random.default_rng(stable_seed(item_id))

        fabricated: list[str] = []
        for name, (low, high) in _SYNTHETIC_BAND_RANGES.items():
            if name in bands:
                continue
            bands[name] = rng.uniform(low, high, size)
            fabricated.append(name)
        if "scl" not in bands:
            bands["scl"] = np.full(size, _SYNTHETIC_SCL, dtype=np.int16)
            fabricated.append("scl")

        quality_flags.setdefault("synthetic_bands", []).extend(fabricated)
        if fabricated:
            logger.warning(
                "Fabricating %d band(s) for item %s: %s. The tile is NOT a "
                "measurement and is labelled data_source='partially_synthetic'.",
                len(fabricated),
                item_id,
                ", ".join(sorted(fabricated)),
            )
            return bands, "partially_synthetic"
        return bands, "real"

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
        """A wholly fabricated tile, for when the item could not be retrieved.

        Produces the **full** band set, not the five it used to. The old
        version returned only red/green/blue/nir/swir16, and
        ``SatelliteAnalyzer.analyze_point`` indexes ``bands["blue"]``
        unconditionally (analyzer.py:104) -- so the synthetic path, the one
        that is *supposed* to keep the pipeline alive, raised ``KeyError``
        instead. The same ``_SYNTHETIC_BAND_RANGES`` are used as
        ``_fill_missing_bands`` so the two fabrication paths cannot drift apart,
        and both carry the same explicit flags.
        """
        size = 64
        rng = np.random.default_rng(stable_seed(item_id))
        bands: dict[str, np.ndarray] = {
            name: rng.uniform(low, high, (size, size))
            for name, (low, high) in _SYNTHETIC_BAND_RANGES.items()
        }
        bands["scl"] = np.full((size, size), _SYNTHETIC_SCL, dtype=np.int16)
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
            quality_flags={
                "synthetic": True,
                "synthetic_pixels": True,
                "synthetic_bands": sorted(bands),
                "real_download": False,
                "reason": f"synthetic_tile:{reason}",
                "synthetic_band_note": (
                    "Every band was fabricated. The bbox, datetime and cloud_cover "
                    "on this tile are placeholders, not from the STAC item."
                ),
            },
        )
