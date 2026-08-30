"""Real DEM elevation service — Phase 1 (real-site terrain).

GET /api/v1/elevation/grid/{site_id}?size=129&span_m=2000

Samples a size×size elevation grid around a manual-dataset site using the
free Open-Meteo Elevation API (Copernicus DEM 90m, no key), bilinearly
upsamples to the requested resolution and caches the result on disk
(data/manual/elevation_cache/). Falls back with honest 503 on network errors.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import httpx
from typing import Any
from fastapi import APIRouter, HTTPException, Query

from services.data_manual import manual

router = APIRouter(prefix="/api/v1/elevation", tags=["elevation"])

CACHE_DIR = Path("data/manual/elevation_cache")
SOURCE = "open-meteo (Copernicus DEM GLO-90m)"
M_PER_DEG_LAT = 111_320.0


def _cache_path(site_id: str, size: int, span_m: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{site_id}_{size}_{span_m}.json"


def _site_latlon(site_id: str) -> tuple[float, float, str]:
    row = manual.site(site_id)
    if row.empty:
        raise HTTPException(404, f"site '{site_id}' not found")
    rec = row.iloc[0]
    return float(rec["lat"]), float(rec["lon"]), str(rec.get("country", ""))


def _sample_grid(lat: float, lon: float, span_m: int, step: int) -> list[list[float]]:
    """step×step grid of elevation samples (m) centered on (lat, lon)."""
    half = span_m / 2
    dlat = half / M_PER_DEG_LAT
    dlon = half / (M_PER_DEG_LAT * max(0.2, math.cos(math.radians(lat))))
    lats = [lat - dlat + (2 * dlat) * (i / (step - 1)) for i in range(step)]
    lons = [lon - dlon + (2 * dlon) * (i / (step - 1)) for i in range(step)]

    grid = [[0.0] * step for _ in range(step)]
    points = [(la, lo, i, j) for i, la in enumerate(lats) for j, lo in enumerate(lons)]

    BATCH = 100
    delays = [0, 6, 14, 30, 60]
    for b in range(0, len(points), BATCH):
        chunk = points[b:b + BATCH]
        las = ",".join(f"{p[0]:.6f}" for p in chunk)
        los = ",".join(f"{p[1]:.6f}" for p in chunk)
        values = None
        for attempt, wait in enumerate(delays):
            if wait:
                time.sleep(wait)
            resp = httpx.get(
                "https://api.open-meteo.com/v1/elevation",
                params={"latitude": las, "longitude": los},
                timeout=30,
            )
            if resp.status_code == 200:
                values = resp.json().get("elevation", [])
                break
            if resp.status_code in (429, 502, 503):
                continue
            resp.raise_for_status()
        if values is None:
            raise HTTPException(502, "elevation API rate-limited after retries (try again in a minute)")
        if len(values) != len(chunk):
            raise HTTPException(502, f"elevation API returned {len(values)}/{len(chunk)} values")
        values = resp.json().get("elevation", [])
        if len(values) != len(chunk):
            raise HTTPException(502, f"elevation API returned {len(values)}/{len(chunk)} values")
        for (la, lo, i, j), v in zip(chunk, values):
            grid[i][j] = float(v) if v is not None else 0.0
    return grid


def _bilinear_upsample(grid: list[list[float]], size: int) -> list[list[float]]:
    src_n = len(grid)
    out = [[0.0] * size for _ in range(size)]
    for oy in range(size):
        fy = oy / (size - 1) * (src_n - 1)
        y0, y1 = int(fy), min(int(fy) + 1, src_n - 1)
        ty = fy - y0
        for ox in range(size):
            fx = ox / (size - 1) * (src_n - 1)
            x0, x1 = int(fx), min(int(fx) + 1, src_n - 1)
            tx = fx - x0
            v = (
                grid[y0][x0] * (1 - ty) * (1 - tx)
                + grid[y1][x0] * ty * (1 - tx)
                + grid[y0][x1] * (1 - ty) * tx
                + grid[y1][x1] * ty * tx
            )
            out[oy][ox] = round(v, 2)
    return out


@router.get("/grid/{site_id}")
def elevation_grid(
    site_id: str,
    size: int = Query(129, ge=33, le=257),
    span_m: int = Query(2000, ge=200, le=10000),
    refresh: bool = Query(False),
) -> dict:
    """Real DEM grid (meters, size×size) centered on the site. Cached on disk."""
    cache = _cache_path(site_id, size, span_m)
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text(encoding="utf-8"))
        data["cached"] = True
        return data

    lat, lon, country = _site_latlon(site_id)

    # coarse sampling (33×33) -> upsample to `size` (keeps API calls ~11)
    coarse = _sample_grid(lat, lon, span_m, step=25)
    grid = _bilinear_upsample(coarse, size)

    flat = [v for row in grid for v in row]
    result = {
        "site_id": site_id,
        "country": country,
        "lat": lat,
        "lon": lon,
        "span_m": span_m,
        "size": size,
        "min_elev": min(flat),
        "max_elev": max(flat),
        "elevation": grid,
        "source": SOURCE,
        "cached": False,
        "fetched_at": datetime_now(),
    }
    cache.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


def datetime_now() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


# ============================================================================
# Phase 3: real engineering-op effects (RUSLE before/after) â€” manual dataset
# ============================================================================

_OP_P_FACTOR = {
    "terrace": 0.35,   # bench terraces cut LS effectiveness strongly
    "checkdam": 0.50,
    "gabion": 0.60,
    "spillway": 0.80,
    "pond": 1.00,      # storage â€” no direct erosion change
    "well": 1.00,      # water supply â€” groundwater effect instead
}
_OP_FA = {
    "terrace": "طھط±ط§ط³â€Œط¨ظ†ط¯غŒ", "checkdam": "ط¨ظ†ط¯ ط®ط§ع©غŒ", "gabion": "ع¯ط§ط¨غŒظˆظ†",
    "spillway": "ط³ط±ط±غŒط²", "pond": "ط§ط³طھط®ط± ط¢ط¨", "well": "ع†ط§ظ‡",
}


@router.post("/erosion-effect/{site_id}")
def erosion_effect(
    site_id: str,
    op_type: str,
    crop: str = Query("wheat"),
    slope_length_m: float = Query(100, gt=1, le=400),
) -> dict:
    """RUSLE before/after for an engineering op â€” real rainfall, soil and DEM slope.

    A = R أ— K أ— LS أ— C أ— P  (t/ha/yr). Terrace/gabion/checkdam reduce the
    support-practice factor P; well/pond report groundwater effects instead.
    """
    if op_type not in _OP_P_FACTOR:
        raise HTTPException(400, f"unknown op '{op_type}'")

    # R â€” real annual rainfall (mean of the site's weather history)
    ann = manual.weather_annual(site_id)
    annual_rain = float(ann["precip_mm"].mean()) if not ann.empty else 300.0
    r_factor = 0.5 * annual_rain  # Wischmeier-style approximation for semi-arid

    # K â€” from texture class + organic carbon (EPIC-style approximation)
    province = None
    sites_df = manual.sites()
    row = sites_df[sites_df["site_id"] == site_id]
    if not row.empty and "province" in row.columns:
        province = row.iloc[0].get("province")
    soil = manual.soil_regions(province=province)
    k_factor, om_pct, texture_fa, mean_slope = 0.32, None, None, 3.0
    if not soil.empty:
        s0 = soil.iloc[0]
        om_pct = s0.get("organic_carbon_pct")
        texture_fa = (s0.get("texture_class_fa") or "").strip()
        # sandy soils erode less per-unit but shard more; clay binds â€” mid classes worst
        base_k = 0.34 if "ظ„ظˆظ…" in texture_fa else (0.28 if "ط±ط³غŒ" in texture_fa else 0.24)
        om_adj = max(0.0, (2.0 - (om_pct or 2.0)) * 0.02)  # low OM raises K slightly
        k_factor = round(min(0.45, base_k + om_adj), 3)

    # LS â€” from the REAL cached DEM slope (mean slope degrees of the 2km grid)
    cache = _cache_path(site_id, 129, 2000)
    if cache.exists():
        grid = json.loads(cache.read_text(encoding="utf-8"))["elevation"]
        n = len(grid)
        cell = 2000.0 / (n - 1)
        slopes = []
        for y in range(1, n - 1):
            for x in range(1, n - 1):
                dzdx = (grid[y][x + 1] - grid[y][x - 1]) / (2 * cell)
                dzdy = (grid[y + 1][x] - grid[y - 1][x]) / (2 * cell)
                slopes.append(math.degrees(math.atan(math.sqrt(dzdx**2 + dzdy**2))))
        mean_slope = sum(slopes) / len(slopes) if slopes else 3.0
    ls_factor = round((slope_length_m / 22.13) ** 0.5 * (0.76 + 0.53 * math.sin(math.radians(mean_slope)) / math.sin(math.radians(5))), 3) if mean_slope > 0 else 0.5

    # C â€” cover factor by crop (FAO-ish defaults)
    c_factor = {"wheat": 0.25, "maize": 0.35, "orchard": 0.18, "cover": 0.08}.get(crop.lower(), 0.3)

    p_before = 1.0
    p_after = _OP_P_FACTOR[op_type]

    def rusle(p: float) -> float:
        return round(r_factor * k_factor * ls_factor * c_factor * p, 3)

    a_before = rusle(p_before)
    a_after = rusle(p_after)
    reduction = round((1 - a_after / a_before) * 100, 1) if a_before > 0 else 0.0

    result: dict[str, Any] = {
        "site_id": site_id,
        "op": op_type,
        "op_fa": _OP_FA[op_type],
        "rusle": {
            "R": round(r_factor, 1), "K": k_factor, "LS": ls_factor,
            "C": c_factor, "P_before": p_before, "P_after": p_after,
        },
        "annual_rainfall_mm": round(annual_rain, 1),
        "mean_slope_deg": round(mean_slope, 2),
        "texture_fa": texture_fa,
        "organic_carbon_pct": om_pct,
        "A_before_t_ha_yr": a_before,
        "A_after_t_ha_yr": a_after if op_type in ("terrace", "checkdam", "gabion", "spillway") else a_before,
        "reduction_pct": reduction,
        "note_fa": "",
    }
    if op_type == "well":
        result["note_fa"] = "ع†ط§ظ‡: طھط£ط«غŒط± ط§طµظ„غŒ ط¨ط± ظ„ط§غŒظ‡â€ŒغŒ ط¢ط¨ ط²غŒط±ط²ظ…غŒظ†غŒ ط§ط³طھ (طھط®ظ„غŒظ‡/ط´ط§ط±عک) â€” ط±طµط¯ ط§ط² ظ„ط§غŒظ‡â€ŒغŒ Groundwater"
    elif op_type == "pond":
        result["note_fa"] = "ط§ط³طھط®ط±: ط°ط®غŒط±ظ‡â€ŒغŒ ط±ظˆط§ظ†ط§ط¨ ظˆ ع©ط§ظ‡ط´ ط§ظˆط¬ ط³غŒظ„ط§ط¨ â€” ط§ط«ط± ط¨ط± Water Budget"
    elif op_type in ("terrace", "checkdam", "gabion"):
        result["note_fa"] = f"{_OP_FA[op_type]}: ع©ط§ظ‡ط´ ظپط±ط³ط§غŒط´ ({reduction}ظھ) ط±ظˆغŒ ظ„ط§غŒظ‡â€ŒغŒ Erosion ط§ط¹ظ…ط§ظ„ ظ…غŒâ€Œط´ظˆط¯"
    return result

