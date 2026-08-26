"""
Open-Meteo ERA5 Client (Phase 4 — real FAO ET0, no credentials)
================================================================
Fetches REAL ERA5-Land archive data (Open-Meteo) for any lat/lon:
temperature, precipitation, humidity and **FAO-56 reference ET0**
(``et0_fao_evapotranspiration``) — the standard irrigation-scheduling
input, no API key required.

Honesty contract
----------------
- Network failures return ``status="error"`` — never fabricated values.
- Every response carries ``source: "Open-Meteo ERA5"``.

Docs: https://open-meteo.com/en/docs/era5-api
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

ERA5_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/era5"
DEFAULT_TIMEOUT = 30.0

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "et0_fao_evapotranspiration",
]


async def fetch_era5_daily(
    lat: float, lon: float, start: date, end: date
) -> Dict[str, Any]:
    """Fetch ERA5-Land daily series for a location.

    Returns:
        Dict with ``status`` "success" and daily arrays (time-aligned
        lists per Open-Meteo), or ``status`` "error" with message.
    """
    # ERA5 archive lags ~1 day: never request today (returns HTTP 400)
    if end >= date.today():
        end = date.today() - timedelta(days=1)
    if start >= end:
        start = end - timedelta(days=365)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARS),
        "timezone": "UTC",
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(
                ERA5_ARCHIVE_URL, params=params, headers={"User-Agent": "EcoNojin/2.0"}
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, OSError, ValueError) as exc:
        logger.warning("Open-Meteo ERA5 fetch failed: %s", exc)
        return {"source": "Open-Meteo ERA5", "status": "error", "message": str(exc)}

    daily = data.get("daily", {})
    return {
        "source": "Open-Meteo ERA5",
        "lat": lat,
        "lon": lon,
        "status": "success",
        "days": len(daily.get("time", [])),
        "daily": daily,
    }


def era5_to_daily_map(raw: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Convert the Open-Meteo daily arrays into {YYYY-MM-DD: values} dicts.

    Only complete days (all six variables present, no None) are included —
    missing measurements are skipped, never defaulted.
    """
    daily = raw.get("daily", {})
    times = daily.get("time", [])
    out: Dict[str, Dict[str, float]] = {}
    for i, day in enumerate(times):
        values: Dict[str, float] = {}
        ok = True
        for var in ("temperature_2m_max", "temperature_2m_min",
                    "temperature_2m_mean", "precipitation_sum",
                    "relative_humidity_2m_mean", "et0_fao_evapotranspiration"):
            raw_val = daily.get(var, [None] * len(times))[i]
            if raw_val is None:
                ok = False
                break
            values[var] = float(raw_val)
        if ok:
            out[str(day)] = values
    return out


async def fetch_era5_summary(
    lat: float, lon: float, start: date, end: date
) -> Dict[str, Any]:
    """Complete ERA5 fetch with a summary block (recommended entry point)."""
    raw = await fetch_era5_daily(lat, lon, start, end)
    if raw.get("status") != "success":
        return {"status": "error", "source": "Open-Meteo ERA5",
                "message": raw.get("message", "unavailable")}
    daily = era5_to_daily_map(raw)
    if not daily:
        return {"status": "error", "source": "Open-Meteo ERA5",
                "message": "no complete days in ERA5 response"}
    et0 = [d["et0_fao_evapotranspiration"] for d in daily.values()]
    precip = [d["precipitation_sum"] for d in daily.values()]
    tmean = [d["temperature_2m_mean"] for d in daily.values()]
    rh = [d["relative_humidity_2m_mean"] for d in daily.values()]
    return {
        "status": "success",
        "source": "Open-Meteo ERA5 (FAO-56 ET0)",
        "lat": lat,
        "lon": lon,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "days": len(daily),
        "summary": {
            "total_et0_mm": round(sum(et0), 1),
            "total_precipitation_mm": round(sum(precip), 1),
            "mean_temp_c": round(sum(tmean) / len(tmean), 1) if tmean else None,
            "mean_et0_mm_day": round(sum(et0) / len(et0), 2) if et0 else None,
            "mean_humidity_pct": round(sum(rh) / len(rh), 1) if rh else None,
        },
        "daily": daily,
    }
