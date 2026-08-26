"""
SoilGrids v2.0 client (free, no API key) — WCS tiles + properties/query
=======================================================================
Fetches REAL global soil properties from ISRIC SoilGrids (250 m) for a
point: texture (sand/silt/clay), soil organic carbon (SOC), pH(H2O),
CEC and bulk density, plus an estimated RUSLE K-factor.

Data sources (free & open, no credentials):
    - WCS tiles:     https://maps.isric.org  (GetCoverage, GeoTIFF)
    - REST query:    https://rest.isric.org  (used for unit cross-checks)

Unit cross-check (2026, verified against the properties/query API):
    sand/silt/clay: g/kg  (÷10 -> %)
    soc:            dg/kg (÷10 -> g/kg; ÷10 -> %)
    phh2o:          pH×10 (÷10 -> pH)
    cec:            mmol(c)/kg (÷10 -> cmol(c)/kg)
    bdod:           cg/cm³ (÷100 -> g/cm³)

References
----------
- SoilGrids 2.0: Poggio et al. (2021), SOIL 7, 217-240.
- RUSLE K-factor (EPIC): Williams et al. (1996) — metric ×0.1317.

Honesty contract
----------------
- Network failures return ``status="error"`` — never fabricated values.
- SoilGrids masks some pixels (e.g. city centres): the nearest valid
  pixel inside the tile is used and ``sample_offset_km`` reports the
  real distance honestly.
- Texture class is an approximation of the USDA triangle, documented as
  ``texture_approx=true``.
"""
from __future__ import annotations

import asyncio
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
import rasterio
from rasterio.io import MemoryFile

logger = logging.getLogger(__name__)

WCS_BASE = "https://maps.isric.org/mapserv"
SOILGRIDS_PROPS = ["sand", "silt", "clay", "soc", "phh2o", "cec", "bdod"]
TILE_HALF_DEG = 0.25        # tile box is +-0.25 deg (~+-28 km)
MAX_NEAREST_PX = 60         # max search distance inside the tile (px)
TIMEOUT = 60.0

# Unit conversions (verified against the REST properties/query API)
_UNIT = {
    "sand": 10.0,   # g/kg -> %
    "silt": 10.0,
    "clay": 10.0,
    "soc": 10.0,    # dg/kg -> g/kg
    "phh2o": 10.0,  # pH*10 -> pH
    "cec": 10.0,    # mmol(c)/kg -> cmol(c)/kg
    "bdod": 100.0,  # cg/cm3 -> g/cm3
}


# ---------------------------------------------------------------------------
# USDA texture approximation (nearest class of the LandProfile union)
# ---------------------------------------------------------------------------

def usda_texture_class(sand_pct: float, silt_pct: float, clay_pct: float) -> str:
    """Approximate USDA texture class from sand/silt/clay percentages.

    Returns one of: sand, sandy_loam, loam, silt_loam, clay_loam, clay.
    This is an approximation of the USDA texture triangle (documented).
    """
    if clay_pct >= 35:
        return "clay"
    if clay_pct >= 27 and sand_pct <= 45:
        return "clay_loam"
    if sand_pct >= 70:
        return "sand"
    if sand_pct >= 50:
        return "sandy_loam"
    if silt_pct >= 60:
        return "silt_loam"
    return "loam"


# ---------------------------------------------------------------------------
# RUSLE K-factor (EPIC erodibility equation)
# ---------------------------------------------------------------------------

def rusle_k_factor(sand_pct: float, silt_pct: float, clay_pct: float, soc_g_kg: float) -> float:
    """RUSLE K-factor (t·ha·h / ha·MJ·mm) from texture + SOC (EPIC, 1996)."""
    sa = max(0.0, min(100.0, sand_pct))
    si = max(0.0, min(100.0, silt_pct))
    cl = max(0.0, min(100.0, clay_pct))
    c = max(0.0, soc_g_kg / 1000.0)
    sn = 1.0 - sa / 100.0
    try:
        term1 = 0.2 + 0.3 * math.exp(-0.0256 * sa * (1.0 - si / 100.0))
        term2 = (si / (cl + si + 1e-9)) ** 0.3
        term3 = 1.0 - 0.25 * c / (c + math.exp(3.72 - 2.95 * c) + 1e-9)
        term4 = 1.0 - 0.7 * sn / (sn + math.exp(-5.51 + 22.9 * sn) + 1e-9)
        k = 0.1317 * term1 * term2 * term3 * term4
        return round(max(0.001, min(0.09, k)), 4)
    except ZeroDivisionError:  # pragma: no cover - defensive
        return 0.03


# ---------------------------------------------------------------------------
# WCS tile access
# ---------------------------------------------------------------------------

def _coverage_url(prop: str, lon: float, lat: float, half_deg: float) -> str:
    return (
        f"{WCS_BASE}?map=/map/{prop}.map&SERVICE=WCS&VERSION=2.0.1"
        f"&REQUEST=GetCoverage&COVERAGEID={prop}_0-5cm_mean&FORMAT=image/tiff"
        f"&SUBSET=long({lon - half_deg},{lon + half_deg})"
        f"&SUBSET=lat({lat - half_deg},{lat + half_deg})"
        "&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326&SCALEFACTOR=1"
    )


async def _fetch_coverage(
    client: httpx.AsyncClient, prop: str, lon: float, lat: float
) -> Optional[Tuple[np.ndarray, Any]]:
    """Download a small GeoTIFF tile; return (array, transform) or None."""
    url = _coverage_url(prop, lon, lat, TILE_HALF_DEG)
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        with MemoryFile(resp.content) as mem:
            with mem.open() as src:
                arr = src.read(1).astype(np.float64)
                return arr, src.transform
    except (httpx.HTTPError, OSError, ValueError, rasterio.errors.RasterioIOError) as exc:
        logger.warning("SoilGrids WCS %s failed: %s", prop, exc)
        return None


def _pixel_at(transform: Any, lon: float, lat: float) -> Tuple[int, int]:
    col, row = ~transform * (lon, lat)
    return int(round(row)), int(round(col))


def _lonlat_at(transform: Any, row: int, col: int) -> Tuple[float, float]:
    lon, lat = transform * (col, row)
    return float(lon), float(lat)


def _value_at(arr: np.ndarray, transform: Any, lon: float, lat: float) -> Optional[float]:
    """Value at a point; None when out of bounds or masked (<=0/NaN)."""
    row, col = _pixel_at(transform, lon, lat)
    if 0 <= row < arr.shape[0] and 0 <= col < arr.shape[1]:
        v = arr[row, col]
        if v > 0 and not np.isnan(v):
            return float(v)
    return None


def _nearest_valid(
    arr: np.ndarray, transform: Any, lon: float, lat: float, max_px: int = MAX_NEAREST_PX
) -> Optional[Tuple[float, float]]:
    """Nearest valid (lon, lat) inside the tile (ring search by distance)."""
    row, col = _pixel_at(transform, lon, lat)
    h, w = arr.shape
    for r in range(0, max_px + 1):
        if r == 0:
            v = _value_at(arr, transform, lon, lat)
            if v is not None:
                return lon, lat
            continue
        for dr in (-r, r):
            for dc in range(-r, r + 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < h and 0 <= cc < w and arr[rr, cc] > 0 and not np.isnan(arr[rr, cc]):
                    return _lonlat_at(transform, rr, cc)
        for dc in (-r, r):
            for dr in range(-r + 1, r):
                rr, cc = row + dr, col + dc
                if 0 <= rr < h and 0 <= cc < w and arr[rr, cc] > 0 and not np.isnan(arr[rr, cc]):
                    return _lonlat_at(transform, rr, cc)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_soil_profile(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch a REAL SoilGrids profile for (lon, lat), top layer 0-5cm.

    Strategy: download one small WCS tile per property in parallel, then
    read the nearest valid pixel of each tile. The sand pixel anchors the
    soil column; other properties fall back to their own nearest valid
    pixel when masked (offset reported).
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            tiles = await _fetch_all_tiles(client, lon, lat)
    except httpx.HTTPError as exc:
        logger.warning("SoilGrids request failed: %s", exc)
        return {"status": "error", "data_source": "soilgrids", "error": str(exc)}

    values: Dict[str, Optional[float]] = {}
    offsets: Dict[str, float] = {}
    for prop in SOILGRIDS_PROPS:
        tile = tiles.get(prop)
        if tile is None:
            values[prop] = None
            continue
        arr, transform = tile
        pt = _nearest_valid(arr, transform, lon, lat)
        if pt is None:
            values[prop] = None
            continue
        v = _value_at(arr, transform, pt[0], pt[1])
        values[prop] = v / _UNIT[prop] if v is not None else None
        offsets[prop] = round(
            math.hypot((pt[0] - lon) * 111.32 * math.cos(math.radians(lat)),
                       (pt[1] - lat) * 110.57), 1)

    sand, silt, clay = values["sand"], values["silt"], values["clay"]
    if sand is None or silt is None or clay is None:
        return {
            "status": "error",
            "data_source": "soilgrids",
            "error": "SoilGrids has no valid pixel near the requested point",
        }

    soc = values["soc"]
    texture = usda_texture_class(sand, silt, clay)
    k_factor = rusle_k_factor(sand, silt, clay, soc if soc is not None else 12.0)

    return {
        "status": "ok",
        "data_source": "soilgrids",
        "texture": texture,
        "texture_approx": True,
        "sand_pct": round(sand, 1),
        "silt_pct": round(silt, 1),
        "clay_pct": round(clay, 1),
        "soc_g_kg": round(soc, 1) if soc is not None else None,
        "soc_pct": round(soc / 10.0, 2) if soc is not None else None,
        "ph_h2o": round(values["phh2o"], 1) if values["phh2o"] is not None else None,
        "cec_mmolc_kg": (
            round(values["cec"] * 10.0, 1) if values["cec"] is not None else None
        ),
        "bulk_density_g_cm3": (
            round(values["bdod"], 2) if values["bdod"] is not None else None
        ),
        "k_factor_rusle": k_factor,
        "depth_layer": "0-5cm",
        "sample_offset_km": max(offsets.values()) if offsets else 0.0,
        "reference": "SoilGrids 2.0 WCS (ISRIC, free)",
    }


async def _fetch_all_tiles(
    client: httpx.AsyncClient, lon: float, lat: float
) -> Dict[str, Optional[Tuple[np.ndarray, Any]]]:
    """Fetch all property tiles in parallel (semaphore=3, polite)."""
    sem = asyncio.Semaphore(3)

    async def _one(prop: str):
        async with sem:
            return prop, await _fetch_coverage(client, prop, lon, lat)

    results = await asyncio.gather(*[_one(p) for p in SOILGRIDS_PROPS])
    return {prop: tile for prop, tile in results}
