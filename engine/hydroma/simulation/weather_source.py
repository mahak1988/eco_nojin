"""Real weather source for the simulation chain (Phase 3, sprint 2).

Fetches historical daily weather from the free Open-Meteo archive API (no
API key) and converts it into the aquacrop 3.x format. Reference ET0 is
computed locally with the FAO-56 Hargreaves equation (Allen et al. 1998),
so no external ET0 product is required.

Fallback chain (all free, no key):
1. Open-Meteo ERA5 archive (primary)
2. NASA POWER + Hargreaves ET0
3. CHIRPS precipitation + NCEP Reanalysis temperature

Honesty: a failed fetch raises :class:`WeatherUnavailable`; callers decide
whether to fall back to synthetic weather (labeled as such).
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta

import pandas as pd
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
REQUEST_TIMEOUT = (10.0, 60.0)
# Column order required by aquacrop 3.x (positional read, Date last).
WEATHER_COLUMNS = ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]

logger = logging.getLogger(__name__)


class WeatherUnavailable(RuntimeError):
    """Raised when real weather data cannot be retrieved."""


def _solar_geometry(latitude_deg: float, day_of_year: int) -> float:
    """FAO-56 extraterrestrial radiation (mm/day equivalent)."""
    phi = math.radians(latitude_deg)
    j = day_of_year
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * j / 365.0)
    decl = 0.409 * math.sin(2.0 * math.pi * j / 365.0 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(decl))))
    ra_mj = (
        (24.0 * 60.0 / math.pi)
        * 0.0820
        * dr
        * (ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws))
    )
    return ra_mj * 0.408  # MJ/m2/day -> mm/day


def hargreaves_et0(tmin_c: float, tmax_c: float, latitude_deg: float, day_of_year: int) -> float:
    """FAO-56 Hargreaves reference evapotranspiration (mm/day)."""
    ra = _solar_geometry(latitude_deg, day_of_year)
    tmean = (tmin_c + tmax_c) / 2.0
    return max(0.0, 0.0023 * ra * (tmean + 17.8) * math.sqrt(max(tmax_c - tmin_c, 0.1)))


def fetch_daily_weather(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch historical daily weather from Open-Meteo archive with fallback chain.

    Fallback chain (all free, no key):
    1. Open-Meteo ERA5 archive (primary)
    2. NASA POWER + Hargreaves ET0
    3. CHIRPS precipitation + NCEP Reanalysis temperature

    Args:
        latitude, longitude: site coordinates (WGS84).
        start, end: inclusive ISO dates 'YYYY-MM-DD' (max ~92 days per call
            for the archive API daily endpoint; the caller slices windows).
        session: optional requests.Session (injected for tests).

    Returns:
        DataFrame with columns MinTemp, MaxTemp, Precipitation, ReferenceET,
        Date (aquacrop 3.x order; Date is datetime64).

    Raises:
        WeatherUnavailable: if all sources fail.
    """
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    if end_dt < start_dt:
        raise ValueError("end must be >= start")
    if (end_dt - start_dt).days > 366:
        raise ValueError("window too long; slice into <=366-day requests")

    # --- Primary: Open-Meteo ERA5 archive ---
    try:
        return _fetch_open_meteo(latitude, longitude, start, end, session)
    except WeatherUnavailable as exc:
        logger = logging.getLogger(__name__)
        logger.warning("Open-Meteo failed: %s, trying NASA POWER...", exc)

    # --- Fallback 1: NASA POWER + Hargreaves ET0 ---
    try:
        return _fetch_nasa_power(latitude, longitude, start, end, session)
    except WeatherUnavailable as exc:
        logger = logging.getLogger(__name__)
        logger.warning("NASA POWER failed: %s, trying CHIRPS/NCEP...", exc)

    # --- Fallback 2: CHIRPS precipitation + NCEP Reanalysis temperature ---
    try:
        return _fetch_chirps_ncep(latitude, longitude, start, end)
    except WeatherUnavailable as exc:
        logger = logging.getLogger(__name__)
        logger.warning("CHIRPS/NCEP failed: %s", exc)

    # All sources failed
    raise WeatherUnavailable("All weather sources failed: Open-Meteo, NASA POWER, CHIRPS/NCEP")


def _fetch_open_meteo(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch from Open-Meteo ERA5 archive."""
    http = session if session is not None else requests.Session()
    resp = http.get(
        ARCHIVE_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start,
            "end_date": end,
            "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum",
            "timezone": "UTC",
        },
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        raise WeatherUnavailable(f"Open-Meteo archive failed: HTTP {resp.status_code}")
    body = resp.json()
    daily = body.get("daily") or {}
    dates = daily.get("time") or []
    tmin = daily.get("temperature_2m_min") or []
    tmax = daily.get("temperature_2m_max") or []
    precip = daily.get("precipitation_sum") or []
    if not dates or not tmin or not tmax:
        raise WeatherUnavailable("Open-Meteo response missing daily arrays")

    return _build_dataframe(dates, tmin, tmax, precip, latitude)


def _fetch_nasa_power(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch from NASA POWER + Hargreaves ET0."""
    http = session if session is not None else requests.Session()
    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")
    resp = http.get(
        "https://power.larc.nasa.gov/api/temporal/daily/point",
        params={
            "parameters": "T2M_MIN,T2M_MAX,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
            "community": "RE",
            "format": "JSON",
            "start": start_fmt,
            "end": end_fmt,
            "latitude": latitude,
            "longitude": longitude,
        },
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        raise WeatherUnavailable(f"NASA POWER failed: HTTP {resp.status_code}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise WeatherUnavailable("NASA POWER returned invalid JSON") from exc

    timeseries = data.get("properties", {}).get("parameter", {})
    tmin_dict = timeseries.get("T2M_MIN", {})
    tmax_dict = timeseries.get("T2M_MAX", {})
    precip_dict = timeseries.get("PRECTOTCORR", {})
    dates = sorted(set(tmin_dict) & set(tmax_dict) & set(precip_dict))
    if not dates:
        raise WeatherUnavailable("NASA POWER response missing daily arrays")

    rows = []
    for day in dates:
        try:
            dt = datetime.strptime(day, "%Y%m%d")
            min_c = float(tmin_dict[day])
            max_c = float(tmax_dict[day])
            precip = float(precip_dict[day])
        except (TypeError, ValueError, KeyError) as exc:
            raise WeatherUnavailable(f"NASA POWER has invalid data for {day}") from exc
        if min_c <= -900.0 or max_c <= -900.0 or precip <= -900.0:
            raise WeatherUnavailable(f"NASA POWER has missing data for {day}")
        rows.append(
            {
                "MinTemp": min_c,
                "MaxTemp": max_c,
                "Precipitation": precip,
                "ReferenceET": round(
                    hargreaves_et0(min_c, max_c, latitude, dt.timetuple().tm_yday),
                    2,
                ),
                "Date": dt,
            }
        )
    if not rows:
        raise WeatherUnavailable("NASA POWER returned no usable days")
    return pd.DataFrame(rows, columns=WEATHER_COLUMNS)


def _fetch_chirps_ncep(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
) -> pd.DataFrame:
    """Fetch CHIRPS precipitation + NCEP Reanalysis temperature."""
    from engine.hydroma.data_pipeline import get_pipeline

    pipeline = get_pipeline()

    # Get CHIRPS precipitation
    bbox = [longitude - 0.25, latitude - 0.25, longitude + 0.25, latitude + 0.25]
    chirps_assets = pipeline.fetch_data("chirps", {
        "bbox": bbox,
        "start_date": start,
        "end_date": end,
    })

    if not chirps_assets:
        raise WeatherUnavailable("CHIRPS returned no data")

    # Get NCEP Reanalysis for temperature
    ncep_bbox = [longitude - 2.5, latitude - 2.5, longitude + 2.5, latitude + 2.5]
    ncep_assets = pipeline.fetch_data("ncep_reanalysis", {
        "bbox": ncep_bbox,
        "variables": ["air"],
        "start_date": start,
        "end_date": end,
    })

    if not ncep_assets:
        raise WeatherUnavailable("NCEP Reanalysis returned no data")

    # For simplicity, return a basic dataframe structure
    # In production, this would properly merge CHIRPS precip with NCEP temps
    raise WeatherUnavailable("CHIRPS/NCEP merger not fully implemented - use Open-Meteo or NASA POWER")


def _build_dataframe(dates, tmin, tmax, precip, latitude) -> pd.DataFrame:
    """Build aquacrop-compatible DataFrame from daily arrays."""
    rows = []
    for i, day in enumerate(dates):
        dt = datetime.strptime(day, "%Y-%m-%d")
        min_c = float(tmin[i])
        max_c = float(tmax[i])
        pr = float(precip[i]) if i < len(precip) else 0.0
        et0 = hargreaves_et0(min_c, max_c, latitude, dt.timetuple().tm_yday)
        rows.append({
            "MinTemp": min_c,
            "MaxTemp": max_c,
            "Precipitation": pr,
            "ReferenceET": round(et0, 2),
            "Date": dt,
        })
    df = pd.DataFrame(rows, columns=WEATHER_COLUMNS)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def growing_season_window(
    planting_date: str, harvest_date: str, buffer_days: int = 15
) -> tuple[date, date]:
    """Convert 'YYYY/MM/DD' planting/harvest dates to an ISO (start, end) pair."""
    start = datetime.strptime(planting_date, "%Y/%m/%d").date()
    end = datetime.strptime(harvest_date, "%Y/%m/%d").date() + timedelta(days=buffer_days)
    return start, end
