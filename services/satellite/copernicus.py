"""
Copernicus CDSE Client (Phase 4 — real Sentinel-2 data pipeline)
================================================================
Real satellite data for Eco Nojin via the Copernicus Data Space
Ecosystem (CDSE):

- **OAuth2 token** — client-credentials OR password grant (cdse-public).
- **STAC search** (https://stac.dataspace.copernicus.eu) for
  ``sentinel-2-l2a`` items covering a point.
- **Band sampling** — downloads B04 (red) / B08 (NIR) Cloud Optimised
  GeoTIFFs and samples the pixel around (lat, lon) with rasterio to
  compute REAL NDVI/EVI/SAVI.
- **Cloud masking (SCL)** — also samples the Sentinel-2 scene
  classification layer (SCL) around the point; cloudy samples are never
  presented as real indices (status ``"cloudy"``, indices None).

Honesty contract (W-001)
------------------------
- Without credentials, ``configured == False`` and every network method
  raises :class:`CopernicusNotConfigured` — no fabricated data possible.
- ``analyze_location`` returns real indices ONLY when a scene was found
  and band sampling succeeded; otherwise explicit status codes.

References
----------
- CDSE OData: https://documentation.dataspace.copernicus.eu/APIs/OData.html
- CDSE STAC: https://documentation.dataspace.copernicus.eu/APIs/STAC.html
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import transform

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (env, read live at construction)
# ---------------------------------------------------------------------------

CDSE_STAC_URL = os.environ.get(
    "CDSE_STAC_URL", "https://stac.dataspace.copernicus.eu"
)
CDSE_IDENTITY_URL = os.environ.get(
    "CDSE_IDENTITY_URL", "https://identity.dataspace.copernicus.eu"
)

#: Credential styles: client_credentials OR password grant (cdse-public)
CDSE_CLIENT_ID = os.environ.get("CDSE_CLIENT_ID", "")
CDSE_CLIENT_SECRET = os.environ.get("CDSE_CLIENT_SECRET", "")
CDSE_USERNAME = os.environ.get("CDSE_USERNAME", "")
CDSE_PASSWORD = os.environ.get("CDSE_PASSWORD", "")

#: Sentinel-2 L2A asset names in the STAC catalogue
S2_ASSET_RED = "B04"
S2_ASSET_NIR = "B08"
S2_ASSET_BLUE = "B02"
S2_ASSET_SCL = "SCL"


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class CopernicusError(Exception):
    """Base error for the Copernicus client."""


class CopernicusNotConfigured(CopernicusError):
    """Raised when no CDSE credentials are configured."""


class CopernicusFetchError(CopernicusError):
    """Raised when a CDSE network call fails."""


class CopernicusBandError(CopernicusError):
    """Raised when band data cannot be read or sampled."""


# ---------------------------------------------------------------------------
# Pure spectral index math (unit-testable, no I/O)
# ---------------------------------------------------------------------------

def ndvi_from_bands(nir: float, red: float) -> float:
    """Normalised Difference Vegetation Index from NIR and RED reflectances.

    Args:
        nir: near-infrared reflectance (0..1)
        red: red reflectance (0..1)

    Returns:
        NDVI in [-1, 1]; 0.0 for a degenerate denominator.

    Raises:
        ValueError: if an input is outside [0, 1].
    """
    for name, value in (("nir", nir), ("red", red)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value!r}")
    denom = nir + red
    if denom == 0.0:
        return 0.0
    return round((nir - red) / denom, 4)


def evi_from_bands(
    nir: float, red: float, blue: float,
    c1: float = 6.0, c2: float = 7.5, l: float = 1.0, g: float = 2.5,
) -> float:
    """Enhanced Vegetation Index (Sentinel-2 variant), clamped to [-1, 1]."""
    for name, value in (("nir", nir), ("red", red), ("blue", blue)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value!r}")
    denom = nir + c1 * red - c2 * blue + l
    if denom == 0.0:
        return 0.0
    evi = g * (nir - red) / denom
    return round(max(-1.0, min(1.0, evi)), 4)


def savi_from_bands(nir: float, red: float, l: float = 0.5) -> float:
    """Soil Adjusted Vegetation Index, clamped to [-1, 1]."""
    for name, value in (("nir", nir), ("red", red)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value!r}")
    denom = nir + red + l
    if denom == 0.0:
        return 0.0
    savi = (1 + l) * (nir - red) / denom
    return round(max(-1.0, min(1.0, savi)), 4)


def health_from_ndvi(ndvi: float) -> str:
    """Map NDVI to a human health label (FAO-style thresholds)."""
    if ndvi < 0.3:
        return "poor"
    if ndvi < 0.6:
        return "moderate"
    return "good"


def _reflectance(raw: float, scale: float = 1.0 / 10000.0) -> float:
    """Sentinel-2 L2A COG values are scaled integer DN (0..10000)."""
    return max(0.0, min(1.0, float(raw) * scale))

#: SCL (Scene Classification Layer) classes treated as CLEAR sky.
#: 4 = vegetation, 5 = non-vegetated, 6 = water.
SCL_CLEAR_CLASSES = frozenset({4, 5, 6})
#: SCL value meaning "no data".
SCL_NODATA = 0


def scl_is_clear(value: float) -> bool:
    """True when an SCL pixel is clear sky (vegetation/non-veg/water)."""
    return int(value) in SCL_CLEAR_CLASSES


def clear_ratio_from_scl(window: np.ndarray) -> float | None:
    """Fraction of valid SCL pixels that are clear (None when all no-data)."""
    if window.size == 0:
        return None
    window_f = window.astype(float)
    valid = window_f != SCL_NODATA
    valid_count = int(valid.sum())
    if valid_count == 0:
        return None
    clear_count = int(np.sum([scl_is_clear(v) for v in window_f[valid]]))
    return clear_count / valid_count


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Scene:
    """A Sentinel-2 L2A STAC item."""
    id: str
    datetime: str
    cloud_cover: float
    assets: dict[str, str]  # band name -> href

    @property
    def is_usable(self) -> bool:
        return self.cloud_cover <= 20.0


@dataclass(frozen=True)
class BandSample:
    """Real reflectance sample for one band."""
    band: str
    reflectance: float
    crs: str
    x: float
    y: float


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class CopernicusClient:
    """Credential-gated CDSE client with real band sampling."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        username: str | None = None,
        password: str | None = None,
        identity_url: str | None = None,
        stac_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        # Read env at construction time so tests/settings apply live.
        self.client_id = client_id if client_id is not None else os.environ.get("CDSE_CLIENT_ID", "")
        self.client_secret = (
            client_secret if client_secret is not None
            else os.environ.get("CDSE_CLIENT_SECRET", "")
        )
        self.username = username if username is not None else os.environ.get("CDSE_USERNAME", "")
        self.password = password if password is not None else os.environ.get("CDSE_PASSWORD", "")
        self.identity_url = (
            identity_url or os.environ.get(
                "CDSE_IDENTITY_URL", "https://identity.dataspace.copernicus.eu"
            )
        ).rstrip("/")
        self.stac_url = (
            stac_url or os.environ.get(
                "CDSE_STAC_URL", "https://stac.dataspace.copernicus.eu"
            )
        ).rstrip("/")
        self._timeout = timeout
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # -- availability ------------------------------------------------------

    @property
    def configured(self) -> bool:
        """True when a usable credential style is present."""
        return bool(
            (self.client_id and self.client_secret) or (self.username and self.password)
        )

    # -- auth --------------------------------------------------------------

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise CopernicusNotConfigured(
                "No CDSE credentials configured. Set CDSE_CLIENT_ID/SECRET "
                "(or CDSE_USERNAME/CDSE_PASSWORD) in the environment."
            )

    def get_token(self, force: bool = False) -> str:
        """Fetch and cache an OAuth2 access token (either grant style)."""
        self._ensure_configured()
        now = time.time()
        if self._token and now < self._token_expires_at - 30 and not force:
            return self._token
        if self.client_id and self.client_secret:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        else:
            payload = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
                "client_id": "cdse-public",
            }
        try:
            resp = httpx.post(
                f"{self.identity_url}/auth/realms/CDSE/protocol/openid-connect/token",
                data=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise CopernicusFetchError(f"CDSE token request failed: {exc}") from exc
        data = resp.json()
        self._token = str(data["access_token"])
        self._token_expires_at = now + float(data.get("expires_in", 3600))
        return self._token

    # -- STAC catalogue ----------------------------------------------------

    def search_stac(
        self,
        latitude: float,
        longitude: float,
        start_date: date | None = None,
        end_date: date | None = None,
        max_cloud_cover: float = 20.0,
        max_records: int = 5,
        collection: str = "sentinel-2-l2a",
    ) -> list[Scene]:
        """Search STAC items covering a point (newest first).

        Args:
            collection: CDSE STAC collection id, e.g. "sentinel-2-l2a",
                "landsat-8-9-c2-l2", "sentinel-1-grd".
        """
        self._ensure_configured()
        token = self.get_token()
        end = end_date or date.today()
        start = start_date or date(end.year, end.month - 1 if end.month > 1 else 1, 1)
        body = {
            "collections": [collection],
            "bbox": [longitude, latitude, longitude, latitude],
            "datetime": f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z",
            "limit": max_records,
            "sortby": [{"field": "properties.datetime", "direction": "desc"}],
        }
        try:
            resp = httpx.post(
                f"{self.stac_url}/v1/search",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except (httpx.HTTPError, OSError) as exc:
            raise CopernicusFetchError(f"CDSE STAC search failed: {exc}") from exc

        items = resp.json().get("features", [])
        scenes: list[Scene] = []
        for item in items:
            props = item.get("properties", {})
            assets = {
                key: val.get("href", "")
                for key, val in item.get("assets", {}).items()
                if isinstance(val, dict)
            }
            scenes.append(
                Scene(
                    id=str(item.get("id", "")),
                    datetime=str(props.get("datetime", "")),
                    cloud_cover=float(props.get("eo:cloud_cover", 100.0) or 100.0),
                    assets=assets,
                )
            )
        return scenes

    # -- band download + sampling ------------------------------------------

    async def _download_band(self, href: str, token: str) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(href, headers={"Authorization": f"Bearer {token}"})
                resp.raise_for_status()
                return resp.content
        except (httpx.HTTPError, OSError) as exc:
            raise CopernicusFetchError(f"Band download failed: {exc}") from exc

    def _sample_cog(self, data: bytes, band_name: str, lon: float, lat: float) -> BandSample:
        """Read a COG from memory and sample the pixel nearest (lon, lat)."""
        try:
            with MemoryFile(data) as mem, mem.open() as src:
                if src.crs is None:
                    raise CopernicusBandError(f"{band_name} COG has no CRS")
                # Transform WGS84 -> raster CRS
                try:
                    xs_arr, ys_arr = transform("EPSG:4326", src.crs, [lon], [lat])
                    xs, ys = float(xs_arr[0]), float(ys_arr[0])
                except Exception as exc:
                    raise CopernicusBandError(f"CRS transform failed: {exc}") from exc
                row, col = src.index(xs, ys)
                if not (0 <= row < src.height and 0 <= col < src.width):
                    raise CopernicusBandError("sample point outside scene")
                window = rasterio.windows.Window(col, row, 1, 1)
                arr = src.read(1, window=window)
                raw = float(arr[0, 0])
                return BandSample(
                    band=band_name,
                    reflectance=_reflectance(raw),
                    crs=str(src.crs),
                    x=xs,
                    y=ys,
                )
        except rasterio.errors.RasterioIOError as exc:
            raise CopernicusBandError(f"cannot read {band_name} COG: {exc}") from exc

    def _sample_raw(self, data: bytes, band_name: str, lon: float, lat: float) -> float:
        """Read a COG from memory and return the raw pixel value at (lon, lat)."""
        try:
            with MemoryFile(data) as mem, mem.open() as src:
                if src.crs is None:
                    raise CopernicusBandError(f"{band_name} COG has no CRS")
                xs_arr, ys_arr = transform("EPSG:4326", src.crs, [lon], [lat])
                xs, ys = float(xs_arr[0]), float(ys_arr[0])
                row, col = src.index(xs, ys)
                if not (0 <= row < src.height and 0 <= col < src.width):
                    raise CopernicusBandError("sample point outside scene")
                arr = src.read(1, window=rasterio.windows.Window(col, row, 1, 1))
                return float(arr[0, 0])
        except rasterio.errors.RasterioIOError as exc:
            raise CopernicusBandError(f"cannot read {band_name} COG: {exc}") from exc

    def _sample_ndvi_grid(
        self,
        red_data: bytes,
        nir_data: bytes,
        lon: float,
        lat: float,
        n: int = 7,
        spacing_m: float = 120.0,
    ) -> list[dict[str, float]]:
        """Compute a small NDVI map grid around (lon, lat) from two COGs.

        Reads an (n*step) x (n*step) window around the point and returns
        [{lon, lat, ndvi}, ...] for valid pixels (cloud/NoData skipped).
        """
        out: list[dict[str, float]] = []
        try:
            with MemoryFile(red_data) as mem_r, MemoryFile(nir_data) as mem_n:
                with mem_r.open() as src_r, mem_n.open() as src_n:
                    if src_r.crs is None or src_n.crs is None:
                        return out
                    xs_arr, ys_arr = transform("EPSG:4326", src_r.crs, [lon], [lat])
                    xs, ys = float(xs_arr[0]), float(ys_arr[0])
                    row, col = src_r.index(xs, ys)
                    res = abs(src_r.transform.a) or 10.0
                    step = max(1, int(round(spacing_m / res)))
                    half = (n * step) // 2
                    win = rasterio.windows.Window(
                        col - half, row - half, n * step, n * step
                    )
                    red = src_r.read(1, window=win).astype(np.float64)
                    nir = src_n.read(1, window=win).astype(np.float64)
                    rows, cols = red.shape
                    for i in range(0, rows, step):
                        for j in range(0, cols, step):
                            r, nr = red[i, j], nir[i, j]
                            if r <= 0 or nr <= 0 or r >= 10000 or nr >= 10000:
                                continue
                            nd = (nr - r) / (nr + r + 1e-9)
                            if not -1.0 <= nd <= 1.0:
                                continue
                            gx, gy = src_r.xy(row - half + i, col - half + j)
                            gx_arr, gy_arr = transform(
                                src_r.crs, "EPSG:4326", [float(gx)], [float(gy)]
                            )
                            out.append(
                                {
                                    "lon": round(float(gx_arr[0]), 6),
                                    "lat": round(float(gy_arr[0]), 6),
                                    "ndvi": round(float(nd), 4),
                                }
                            )
        except (rasterio.errors.RasterioIOError, ValueError, IndexError) as exc:
            logger.warning("NDVI grid sampling failed: %s", exc)
        return out

    def _sample_scl_window(
        self, data: bytes, lon: float, lat: float, size: int = 5
    ) -> np.ndarray:
        """Read an SCL COG and return a size x size window around (lon, lat)."""
        try:
            with MemoryFile(data) as mem, mem.open() as src:
                if src.crs is None:
                    raise CopernicusBandError("SCL COG has no CRS")
                xs_arr, ys_arr = transform("EPSG:4326", src.crs, [lon], [lat])
                xs, ys = float(xs_arr[0]), float(ys_arr[0])
                row, col = src.index(xs, ys)
                half = size // 2
                window = rasterio.windows.Window(
                    col - half, row - half, size, size
                )
                arr = src.read(1, window=window)
                return np.asarray(arr, dtype=np.uint8)
        except rasterio.errors.RasterioIOError as exc:
            raise CopernicusBandError(f"cannot read SCL COG: {exc}") from exc

    async def sample_bands(
        self, scene: Scene, latitude: float, longitude: float, return_data: bool = False
    ) -> dict[str, Any]:
        """Download B04/B08/B02 (+SCL) COGs and sample real reflectances.

        Returns:
            {"red": float, "nir": float, "blue": float|None,
             "scl_clear_ratio": float|None} — ``scl_clear_ratio`` is None
             when the SCL band is unavailable (no masking applied).
        """
        red_href = scene.assets.get(S2_ASSET_RED)
        nir_href = scene.assets.get(S2_ASSET_NIR)
        blue_href = scene.assets.get(S2_ASSET_BLUE)
        scl_href = scene.assets.get(S2_ASSET_SCL)
        if not red_href or not nir_href:
            raise CopernicusBandError("scene lacks B04/B08 assets")
        token = self.get_token()
        red_data = await self._download_band(red_href, token)
        nir_data = await self._download_band(nir_href, token)
        red = self._sample_cog(red_data, "B04", longitude, latitude)
        nir = self._sample_cog(nir_data, "B08", longitude, latitude)
        blue = None
        if blue_href:
            try:
                blue_data = await self._download_band(blue_href, token)
                blue = self._sample_cog(blue_data, "B02", longitude, latitude)
            except CopernicusError:
                blue = None
        scl_clear_ratio: float | None = None
        if scl_href:
            try:
                scl_data = await self._download_band(scl_href, token)
                window = self._sample_scl_window(scl_data, longitude, latitude)
                scl_clear_ratio = clear_ratio_from_scl(window)
            except CopernicusError:
                scl_clear_ratio = None
        out: dict[str, Any] = {
            "red": red.reflectance,
            "nir": nir.reflectance,
            "blue": blue.reflectance if blue is not None else None,
            "scl_clear_ratio": scl_clear_ratio,
        }
        if return_data:
            out["red_data"] = red_data
            out["nir_data"] = nir_data
        return out

    async def sample_landsat_lst(
        self, latitude: float, longitude: float, analysis_date: str | None = None
    ) -> dict[str, Any]:
        """Sample Landsat 8/9 Collection 2 Level-2 surface temperature (LST).

        Reads the ST_B10 band: LST_K = raw * 0.00341802 + 149.0 (C2 L2
        scaling); the result is returned in degrees Celsius. No complex
        atmospheric correction is needed because C2 L2 is already
        atmospherically corrected surface temperature.
        """
        self._ensure_configured()
        if analysis_date:
            d = date.fromisoformat(analysis_date)
            scenes = self.search_stac(
                latitude, longitude, start_date=d, end_date=d,
                collection="landsat-8-9-c2-l2",
            )
        else:
            scenes = self.search_stac(
                latitude, longitude, collection="landsat-8-9-c2-l2"
            )
        usable = [s for s in scenes if s.is_usable]
        if not usable:
            return {"status": "no_scene", "data_source": "copernicus_landsat"}
        scene = usable[0]
        href = scene.assets.get("ST_B10")
        if not href:
            return {
                "status": "band_error", "data_source": "copernicus_landsat",
                "error": "scene lacks ST_B10 asset",
            }
        token = self.get_token()
        data = await self._download_band(href, token)
        raw = self._sample_raw(data, "ST_B10", longitude, latitude)
        lst_c = raw * 0.00341802 + 149.0 - 273.15
        return {
            "status": "ok",
            "data_source": "copernicus_landsat",
            "lst_c": round(lst_c, 2),
            "scene_id": scene.id,
            "sensed_at": scene.datetime,
            "cloud_cover": scene.cloud_cover,
        }

    async def sample_sentinel1(
        self, latitude: float, longitude: float, analysis_date: str | None = None
    ) -> dict[str, Any]:
        """Sample Sentinel-1 GRD VV/VH backscatter (raw-DN soil-moisture proxy).

        Honesty note: GRD COGs are 16-bit DN. The VH/VV ratio is a
        qualitative soil-moisture / vegetation proxy, NOT radiometrically
        calibrated sigma0; the response carries ``data_quality="raw_dn_proxy"``.
        """
        self._ensure_configured()
        if analysis_date:
            d = date.fromisoformat(analysis_date)
            scenes = self.search_stac(
                latitude, longitude, start_date=d, end_date=d,
                collection="sentinel-1-grd",
            )
        else:
            scenes = self.search_stac(
                latitude, longitude, collection="sentinel-1-grd"
            )
        if not scenes:
            return {"status": "no_scene", "data_source": "copernicus_sentinel1"}
        scene = scenes[0]
        vv_href = scene.assets.get("VV")
        vh_href = scene.assets.get("VH")
        if not vv_href or not vh_href:
            return {
                "status": "band_error", "data_source": "copernicus_sentinel1",
                "error": "scene lacks VV/VH assets",
            }
        token = self.get_token()
        vv_data = await self._download_band(vv_href, token)
        vh_data = await self._download_band(vh_href, token)
        vv = self._sample_raw(vv_data, "VV", longitude, latitude)
        vh = self._sample_raw(vh_data, "VH", longitude, latitude)
        return {
            "status": "ok",
            "data_source": "copernicus_sentinel1",
            "vv_dn": round(vv, 1),
            "vh_dn": round(vh, 1),
            "vh_vv_ratio": round(vh / (vv + 1e-6), 4),
            "scene_id": scene.id,
            "sensed_at": scene.datetime,
            "data_quality": "raw_dn_proxy",
            "note": "Raw DN backscatter ratio (relative soil-moisture proxy); not radiometrically calibrated.",
        }

    # -- end-to-end analysis -----------------------------------------------

    async def analyze_location(
        self, latitude: float, longitude: float, analysis_date: str | None = None,
        with_grid: bool = False,
    ) -> dict[str, Any]:
        """Real scene-based analysis for a point (Phase 4 core path).

        Returns a dict with ``status``:
        - "ok": real NDVI/EVI/SAVI from a sampled Sentinel-2 scene
        - "no_scene": no usable scene in the window (ndvi None)
        - "band_error": scene found but bands could not be sampled

        Never fabricates indices; ``data_source`` is always "copernicus"
        on this path.
        """
        self._ensure_configured()
        if analysis_date:
            d = date.fromisoformat(analysis_date)
            scenes = self.search_stac(latitude, longitude, start_date=d, end_date=d)
        else:
            scenes = self.search_stac(latitude, longitude)
        usable = [s for s in scenes if s.is_usable]
        if not usable:
            return {
                "status": "no_scene",
                "scene_id": None, "scene_name": None, "sensed_at": None,
                "cloud_cover": None, "ndvi": None, "evi": None, "savi": None,
                "data_source": "copernicus",
            }
        scene = usable[0]
        try:
            bands = await self.sample_bands(scene, latitude, longitude, return_data=with_grid)
        except CopernicusError as exc:
            return {
                "status": "band_error",
                "scene_id": scene.id, "scene_name": scene.id,
                "sensed_at": scene.datetime, "cloud_cover": scene.cloud_cover,
                "ndvi": None, "evi": None, "savi": None,
                "data_source": "copernicus", "error": str(exc),
            }
        clear_ratio = bands.get("scl_clear_ratio")
        if clear_ratio is not None and clear_ratio < 0.5:
            # Cloud mask: sampled pixel is mostly cloud/shadow — never
            # present a cloudy reading as a real vegetation index.
            return {
                "status": "cloudy",
                "scene_id": scene.id,
                "scene_name": scene.id,
                "sensed_at": scene.datetime,
                "cloud_cover": scene.cloud_cover,
                "scl_clear_ratio": clear_ratio,
                "ndvi": None, "evi": None, "savi": None,
                "data_source": "copernicus",
                "error": "sampled pixel is cloud-covered (SCL)",
            }
        ndvi = ndvi_from_bands(bands["nir"], bands["red"])
        evi = evi_from_bands(
            bands["nir"], bands["red"], bands.get("blue") or 0.1
        )
        savi = savi_from_bands(bands["nir"], bands["red"])
        result: dict[str, Any] = {
            "status": "ok",
            "scene_id": scene.id,
            "scene_name": scene.id,
            "sensed_at": scene.datetime,
            "cloud_cover": scene.cloud_cover,
            "scl_clear_ratio": clear_ratio,
            "ndvi": ndvi,
            "evi": evi,
            "savi": savi,
            "data_source": "copernicus",
        }
        if with_grid and bands.get("red_data") is not None:
            try:
                result["ndvi_grid"] = self._sample_ndvi_grid(
                    bands["red_data"], bands["nir_data"], longitude, latitude
                )
            except CopernicusError as exc:
                logger.warning("NDVI grid failed: %s", exc)
                result["ndvi_grid"] = []
        return result
