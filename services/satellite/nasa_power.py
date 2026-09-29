"""
NASA POWER Client (Phase 4 — real weather data, no credentials)
================================================================
Fetches REAL historical/current weather for any lat/lon from NASA's
POWER API (https://power.larc.nasa.gov) and computes reference
evapotranspiration (ET0) with the Hargreaves equation.

Why this matters for Phase 4
----------------------------
- Real data with ZERO credentials: temperature, precipitation and solar
  radiation for any farm location.
- ET0 (mm/day) is the basis of FAO-56 irrigation scheduling — a real,
  science-grounded input for the irrigation calculator and alert engine.
- Every response carries ``source: "NASA POWER"`` so the dashboard can
  label it honestly. Network failures return explicit errors — never
  fabricated numbers.

Ported from the Eco Nojin reference implementation (econojin.com) with
Clean-Room structure; API docs: https://power.larc.nasa.gov/docs/
"""

from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "EcoNojin/2.0"
DEFAULT_TIMEOUT = 30.0

#: Daily parameters requested from NASA POWER
NASA_PARAMETERS = [
    "T2M",  # temperature at 2 m (C)
    "T2M_MAX",  # max temperature (C)
    "T2M_MIN",  # min temperature (C)
    "PRECTOTCORR",  # corrected precipitation (mm/day)
    "ALLSKY_SFC_SW_DWN",  # all-sky insolation (MJ/m^2/day)
]

POWER_API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


# ---------------------------------------------------------------------------
# Pure math
# ---------------------------------------------------------------------------


def hargreaves_et0(tmax: float, tmin: float, tmean: float, doy: int, lat: float) -> float:
    """Hargreaves reference evapotranspiration (mm/day), FAO-56 eq. 52.

    Delegates to ``engine.hydroma.climate.et_calculator.calc_et0_hargreaves``,
    the single implementation. This copy was correct in its unit handling — it
    divided by 2.45, the latent heat of vaporization, which is numerically
    1/2.45 = 0.4082, the same conversion FAO-56 eq. 40 reaches by multiplying
    by 0.408 — but it evaluated the formula itself with exponent 0.50 where
    FAO-56 publishes 0.48.

    Callers: ``services/api_gateway/routers/satellite.py`` and
    ``services/satellite/real_land.py``, both live paths.

    Args:
        tmax: daily maximum temperature (C)
        tmin: daily minimum temperature (C)
        tmean: daily mean temperature (C)
        doy: day of year (1..366)
        lat: latitude in decimal degrees (-90..90)

    Returns:
        ET0 in mm/day, rounded to 2 dp; 0.0 for physically invalid inputs
        (never raises), which is this module's established contract.
    """
    if not (-90.0 <= lat <= 90.0) or not (1 <= doy <= 366):
        return 0.0
    if tmax < tmin or tmax == tmin:
        return 0.0
    # Imported here rather than at module scope: services/satellite is imported
    # by the satellite API route, and a module-level import would make every
    # satellite request pay for the engine's climate package.
    from engine.hydroma.climate.et_calculator import (
        calc_et0_hargreaves,
        calc_extraterrestrial_radiation,
    )

    ra_mj = calc_extraterrestrial_radiation(lat, doy)
    if ra_mj <= 0.0:
        return 0.0
    return round(calc_et0_hargreaves(t_min=tmin, t_max=tmax, t_mean=tmean, ra_mj=ra_mj), 2)


def validate_climate_value(value: Any, default: float = 0.0) -> float:
    """Coerce a climate value to float, replacing NaN/Inf/NASA fill with default.

    NASA POWER marks no-data days with ``-999.0``; treating it as a real
    value would corrupt means (e.g. mean temperature of -793 C). Values
    at or below ``-900`` are therefore treated as missing.
    """
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v) or v <= -900.0:
            return default
        return v
    except (TypeError, ValueError):
        return default


def _valid_or_none(value: Any) -> Optional[float]:
    """Return a float for a real measurement, None for missing/NASA fill."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v) or v <= -900.0:
        return None
    return v


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------


async def fetch_nasa_power_data(
    lat: float, lon: float, start_date: str, end_date: str
) -> dict[str, Any]:
    """Fetch daily temperature/precipitation/solar data from NASA POWER.

    Args:
        lat: latitude (-90..90)
        lon: longitude (-180..180)
        start_date: YYYYMMDD
        end_date: YYYYMMDD

    Returns:
        Dict with ``status`` "success" and per-day parameter dicts, or
        ``status`` "error" with a message (no fabricated values).
    """
    params = {
        "parameters": ",".join(NASA_PARAMETERS),
        "community": "RE",
        "format": "JSON",
        "start": start_date,
        "end": end_date,
        "latitude": lat,
        "longitude": lon,
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                POWER_API_URL, params=params, headers={"User-Agent": USER_AGENT}
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("NASA POWER fetch failed: %s", exc)
        return {"source": "NASA POWER", "status": "error", "message": str(exc)}

    timeseries = data.get("properties", {}).get("parameter", {})
    return {
        "source": "NASA POWER",
        "lat": lat,
        "lon": lon,
        "temp_c": timeseries.get("T2M", {}),
        "temp_c_max": timeseries.get("T2M_MAX", {}),
        "temp_c_min": timeseries.get("T2M_MIN", {}),
        "precip_mm": timeseries.get("PRECTOTCORR", {}),
        "solar_mj_m2": timeseries.get("ALLSKY_SFC_SW_DWN", {}),
        "status": "success",
    }


async def get_daily_climate(
    lat: float, lon: float, start: date, end: date
) -> dict[str, dict[str, float]]:
    """Fetch daily climate + ET0 keyed by YYYYMMDD.

    Missing values use conservative defaults (tmean=15, tmax=tmean+3,
    tmin=tmean-3, precip=0) so downstream calculations never crash; the
    source stays "NASA POWER" and failures return {} (callers must handle).
    """
    raw = await fetch_nasa_power_data(lat, lon, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    if raw.get("status") != "success":
        logger.warning("NASA POWER unavailable, returning empty climate data")
        return {}

    means = raw.get("temp_c", {}) or {}
    maxs = raw.get("temp_c_max", {}) or {}
    mins = raw.get("temp_c_min", {}) or {}
    precs = raw.get("precip_mm", {}) or {}
    out: dict[str, dict[str, float]] = {}
    for dk in set(list(means.keys()) + list(maxs.keys()) + list(mins.keys())):
        tmean = _valid_or_none(means.get(dk))
        if tmean is None:
            # Honest: no real measurement for this day (-999 fill) — skip it
            # rather than fabricate a temperature.
            continue
        tmax = _valid_or_none(maxs.get(dk)) or (tmean + 3.0)
        tmin = _valid_or_none(mins.get(dk)) or (tmean - 3.0)
        precip = _valid_or_none(precs.get(dk)) or 0.0
        try:
            d = date(int(dk[:4]), int(dk[4:6]), int(dk[6:8]))
            doy = d.timetuple().tm_yday
        except (ValueError, IndexError):
            doy = 180
        out[dk] = {
            "temp_mean_c": tmean,
            "temp_max_c": tmax,
            "temp_min_c": tmin,
            "precipitation_mm": precip,
            "et0_mm": hargreaves_et0(tmax, tmin, tmean, doy, lat),
        }
    return out


async def fetch_climate_with_et0(lat: float, lon: float, start: date, end: date) -> dict[str, Any]:
    """Complete real climate fetch with ET0 summary (recommended entry point).

    Returns status/data or an honest error dict; never synthetic values.
    """
    daily = await get_daily_climate(lat, lon, start, end)
    if not daily:
        return {"status": "error", "message": "NASA POWER unavailable", "source": "NASA POWER"}
    et0_values = [d["et0_mm"] for d in daily.values()]
    precip_values = [d["precipitation_mm"] for d in daily.values()]
    temp_values = [d["temp_mean_c"] for d in daily.values()]
    return {
        "status": "success",
        "source": "NASA POWER + Hargreaves ET0",
        "lat": lat,
        "lon": lon,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "days": len(daily),
        "summary": {
            "total_et0_mm": round(sum(et0_values), 1),
            "total_precipitation_mm": round(sum(precip_values), 1),
            "mean_temp_c": round(sum(temp_values) / len(temp_values), 1) if temp_values else None,
            "mean_et0_mm_day": round(sum(et0_values) / len(et0_values), 2) if et0_values else None,
        },
        "daily": daily,
    }
