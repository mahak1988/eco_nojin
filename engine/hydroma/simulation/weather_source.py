"""Real weather source for the simulation chain.

Fetches historical daily weather from the free Open-Meteo archive API (no
API key) and converts it into the aquacrop 3.x format. Reference ET0 is
computed locally with the FAO-56 Hargreaves equation (Allen et al. 1998),
so no external ET0 product is required.

In addition to temperature and precipitation, the fetcher now also retrieves
daily shortwave downward radiation (global horizontal irradiance, GHI) from
both Open-Meteo and NASA POWER.  The shortwave values are **preserved in their
raw form** (column ``ShortwaveRadiation`` in MJ/m²/day) and a separate,
independently testable function :func:`convert_shortwave_to_par` derives PAR
(Photosynthetically Active Radiation) from them.

PAR conversion coefficient status:
    The fraction of shortwave radiation that falls in the 400–700 nm PAR
    band depends on atmospheric composition, solar zenith angle, and aerosol
    loading.  The value used here (0.5) follows the widely cited approximation
    in agricultural meteorology (Monteith & Unsworth 2013, *Principles of
    Environmental Physics*, ch. 9; FAO-56 uses 0.5 in the absence of spectral
    data).  It is a **calibration-grade assumption**, NOT a measured crop
    parameter: consumers of PAR must treat it as ``estimated`` provenance
    unless a real PAR measurement overrides it.

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
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Literal

import pandas as pd
import requests

#: Default HTTP request timeout: (connect_seconds, read_seconds).
REQUEST_TIMEOUT = (10.0, 60.0)


@dataclass
class RetryConfig:
    """Configuration for HTTP retry with exponential backoff."""

    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_factor: float = 2.0
    retry_on_status: frozenset[int] = field(
        default_factory=lambda: frozenset({429, 500, 502, 503, 504})
    )


@dataclass
class RateLimiter:
    """Simple token-bucket rate limiter for API calls.

    Not thread-safe; intended for single-threaded use within one process.
    """

    max_requests: int = 60
    window_seconds: float = 60.0
    _tokens: float = field(init=False, default=0.0)
    _last_update: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self._tokens = float(self.max_requests)
        self._last_update = time.time()

    def acquire(self) -> None:
        """Block until a token is available (respects rate limit)."""
        while True:
            now = time.time()
            elapsed = now - self._last_update
            self._last_update = now
            self._tokens = min(
                float(self.max_requests),
                self._tokens + elapsed * (self.max_requests / self.window_seconds),
            )
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            sleep_time = (1.0 - self._tokens) * (
                self.window_seconds / self.max_requests
            )
            time.sleep(min(sleep_time, 1.0))


@dataclass
class WeatherCacheEntry:
    """Cached weather response."""

    url: str
    params: dict[str, Any]
    response_json: dict[str, Any]
    fetched_at: float


class WeatherCache:
    """Simple in-memory cache for weather API responses.

    Cache key is based on URL + sorted params.  Entries have a TTL.
    Not persistent across process restarts (intentional: weather data
    should be re-fetched for reproducibility audits).
    """

    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, WeatherCacheEntry] = {}

    def _key(self, url: str, params: dict[str, Any]) -> str:
        import hashlib
        import json

        payload = {"url": url, "params": dict(sorted(params.items()))}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:32]

    def get(self, url: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Return cached response if present and not expired."""
        key = self._key(url, params)
        entry = self._entries.get(key)
        if entry is None:
            return None
        if time.time() - entry.fetched_at > self.ttl_seconds:
            del self._entries[key]
            return None
        return entry.response_json

    def put(self, url: str, params: dict[str, Any], response_json: dict[str, Any]) -> None:
        """Store a response in the cache."""
        key = self._key(url, params)
        self._entries[key] = WeatherCacheEntry(
            url=url,
            params=params,
            response_json=response_json,
            fetched_at=time.time(),
        )

    def clear(self) -> None:
        """Clear all cache entries."""
        self._entries.clear()


#: Shared cache instance for weather API responses.
WEATHER_CACHE = WeatherCache(ttl_seconds=3600.0)

#: Shared rate limiter instance (60 requests per minute = 1 per second).
WEATHER_RATE_LIMITER = RateLimiter(max_requests=60, window_seconds=60.0)

#: Shared retry config.
WEATHER_RETRY_CONFIG = RetryConfig()


def _fetch_with_retry(
    http: requests.Session,
    url: str,
    params: dict[str, Any],
    timeout: tuple[float, float],
    retry_config: RetryConfig,
    cache: WeatherCache | None = None,
    rate_limiter: RateLimiter | None = None,
) -> dict[str, Any]:
    """Fetch JSON from a URL with retry, backoff, caching, and rate limiting.

    Args:
        http: Requests session.
        url: Target URL.
        params: Query parameters.
        timeout: (connect, read) timeout tuple.
        retry_config: Retry configuration.
        cache: Optional cache instance.
        rate_limiter: Optional rate limiter instance.

    Returns:
        Parsed JSON response.

    Raises:
        WeatherUnavailable: if all retries fail.
    """
    limiter = rate_limiter or WEATHER_RATE_LIMITER
    cache_inst = cache or WEATHER_CACHE

    # Check cache first
    cached = cache_inst.get(url, params)
    if cached is not None:
        return cached

    last_exc: Exception | None = None
    for attempt in range(retry_config.max_retries):
        try:
            limiter.acquire()
            resp = http.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                cache_inst.put(url, params, data)
                return data
            if resp.status_code in retry_config.retry_on_status:
                last_exc = Exception(f"HTTP {resp.status_code}")
                delay = min(
                    retry_config.base_delay_seconds
                    * (retry_config.backoff_factor ** attempt),
                    retry_config.max_delay_seconds,
                )
                time.sleep(delay)
                continue
            # Non-retryable status code
            raise WeatherUnavailable(f"API returned HTTP {resp.status_code}")
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retry_config.max_retries - 1:
                delay = min(
                    retry_config.base_delay_seconds
                    * (retry_config.backoff_factor ** attempt),
                    retry_config.max_delay_seconds,
                )
                time.sleep(delay)
            continue

    raise WeatherUnavailable(
        f"All {retry_config.max_retries} retries failed for {url}: {last_exc}"
    )


#: Daily variables requested from Open-Meteo archive (all verified working).
OPEN_METEO_DAILY_VARS = (
    "temperature_2m_min,temperature_2m_max,precipitation_sum,"
    "shortwave_radiation_sum,dew_point_2m_mean,relative_humidity_2m_mean,"
    "soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean,"
    "soil_moisture_28_to_100cm_mean"
)

#: Hourly variables requested from Open-Meteo archive (all verified working).
OPEN_METEO_HOURLY_VARS = (
    "vapour_pressure_deficit"
)


def _fetch_open_meteo_hourly_vpd(
    http: requests.Session,
    latitude: float,
    longitude: float,
    start: str,
    end: str,
) -> dict[str, list[float]]:
    """Fetch hourly vapour pressure deficit from Open-Meteo.

    Aggregates hourly VPD to daily mean for EWSI computation.

    Returns:
        Dict mapping ISO date string -> list of hourly VPD values (kPa).
        Empty dict if the fetch fails.
    """
    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start,
        "end_date": end,
        "hourly": OPEN_METEO_HOURLY_VARS,
        "timezone": "UTC",
    }
    try:
        body = _fetch_with_retry(
            http=http,
            url=ARCHIVE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            retry_config=WEATHER_RETRY_CONFIG,
        )
    except WeatherUnavailable:
        return {}

    hourly = body.get("hourly") or {}
    times = hourly.get("time") or []
    vpd_vals = hourly.get("vapour_pressure_deficit") or []
    if not times or not vpd_vals:
        return {}

    # Group hourly VPD by date
    daily_vpd: dict[str, list[float]] = {}
    for t, v in zip(times, vpd_vals, strict=False):
        if v is None:
            continue
        date_key = t[:10]  # "YYYY-MM-DDTHH:MM" -> "YYYY-MM-DD"
        daily_vpd.setdefault(date_key, []).append(float(v))

    return daily_vpd


def _aggregate_hourly_vpd_to_daily(
    hourly_vpd: dict[str, list[float]],
    dates: list[str],
) -> list[float | None]:
    """Aggregate hourly VPD values to daily means.

    Args:
        hourly_vpd: Date -> list of hourly VPD values (kPa).
        dates: Target dates (ISO format).

    Returns:
        List of daily mean VPD values (kPa), or None when no hourly data
        exists for that date.
    """
    result: list[float | None] = []
    for d in dates:
        vals = hourly_vpd.get(d)
        if vals:
            result.append(sum(vals) / len(vals))
        else:
            result.append(None)
    return result
#:
#: ``field_measured``  — instrument deployed in the field (ceptometer, quantum sensor).
#: ``satellite_retrieved`` — satellite-derived product (e.g. NASA POWER ALLSKY_SFC_PAR_TOT).
#: ``analysis_product`` — reanalysis / modelled gridded product.
#: ``estimated`` — derived via the 0.5 shortwave conversion (Status B calibration assumption).
#: ``missing`` — no PAR data available for this day.
#: ``not_converted`` — PAR column not populated.
#:
#: ``observed`` is retained as a legacy alias for ``satellite_retrieved``: NASA
#: POWER's ``ALLSKY_SFC_PAR_TOT`` is a CERES SYN1deg Ed. 4.2 satellite retrieval,
#: not a ground-based measurement, so labelling it ``observed`` was misleading.
#: Consumers that still check for ``observed`` will receive ``satellite_retrieved``
#: from the canonical source (see :func:`normalize_par_provenance`).
PAR_SOURCE_FIELD_MEASURED = "field_measured"
PAR_SOURCE_SATELLITE_RETRIEVED = "satellite_retrieved"
PAR_SOURCE_ANALYSIS = "analysis_product"
PAR_SOURCE_ESTIMATED = "estimated"
PAR_SOURCE_MISSING = "missing"
PAR_SOURCE_NOT_CONVERTED = "not_converted"
LEGACY_OBSERVED = "observed"

VALID_PAR_SOURCES: frozenset[str] = frozenset(
    {
        PAR_SOURCE_FIELD_MEASURED,
        PAR_SOURCE_SATELLITE_RETRIEVED,
        PAR_SOURCE_ANALYSIS,
        PAR_SOURCE_ESTIMATED,
        PAR_SOURCE_MISSING,
        PAR_SOURCE_NOT_CONVERTED,
        LEGACY_OBSERVED,
    }
)


def normalize_par_provenance(value: str | None) -> str:
    """Normalise legacy provenance labels to the current vocabulary.

    ``observed`` (the old label for NASA POWER PAR) is mapped to
    ``satellite_retrieved``. Unknown labels pass through unchanged so they
    remain visible rather than being silently swallowed.
    """
    if value is None:
        return PAR_SOURCE_NOT_CONVERTED
    if value == LEGACY_OBSERVED:
        return PAR_SOURCE_SATELLITE_RETRIEVED
    return value


from engine.hydroma.climate.et_calculator import (  # noqa: E402
    ClimateData,
    calc_et0_hargreaves,
)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
REQUEST_TIMEOUT = (10.0, 60.0)

DEFAULT_WEATHER_COLUMNS = ["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]
WEATHER_COLUMNS = DEFAULT_WEATHER_COLUMNS + [
    "ShortwaveRadiation", "PAR",
    "DewPoint", "RelativeHumidity", "VapourPressureDeficit",
    "SoilMoisture_0_7cm", "SoilMoisture_7_28cm", "SoilMoisture_28_100cm",
]
PAR_COLUMNS = ["ShortwaveRadiation", "PAR"]

# Fractional PAR in shortwave downward radiation.
# Source: Monteith & Unsworth (2013), Principles of Environmental Physics,
# 4th ed., ch. 9 — the diffuse+direct PAR at the surface is ~50% of total
# shortwave downward for mid-latitude conditions with moderate aerosol load.
# This is a calibration-grade assumption (Status B in the Stage 22 framework):
# it is not field-measured for any specific site but is the standard default
# in crop models when spectral data is unavailable.
# Canonical values live in the Stage 37 radiation unit contract.
from engine.hydroma.simulation.radiation_units import (  # noqa: E402
    KWH_TO_MJ,
)

# Conversion factor: 1 kW·h/m² = 3.6 MJ/m².

# NASA POWER parameter for direct PAR measurements.
# Source: https://power.larc.nasa.gov/docs/methodology/energy-fluxes/derived-parameters/
# "POWER provides an estimate of the total Photosynthetically Active Radiation (PAR)
# and it is available in all temporal levels from 1984 to within months of NRT.
# Total PAR from CERES SYN1deg Ed. 4.2 is computed from both diffuse and direct
# horizontal irradiance PAR... methodology and validation described in Su et al., 2007."
NASA_POWER_PAR_PARAMETER = "ALLSKY_SFC_PAR_TOT"

logger = logging.getLogger(__name__)


class WeatherUnavailable(RuntimeError):
    """Raised when real weather data cannot be retrieved."""


@dataclass
class DailyWeatherRecord:
    """Provenance track for a single day's weather observation.

    Records the raw shortwave radiation value, its source, the unit, and
    (if a conversion occurred) the derived PAR value with its method
    provenance.  This is the unit of lineage: a downstream consumer can
    trace why PAR has a particular value and whether it was measured,
    converted with a documented coefficient, or estimated.
    """

    date: str
    source: str
    raw_shortwave_value: float
    raw_shortwave_unit: str
    par_value: float | None = None
    par_unit: str = "MJ/m^2/day"
    par_conversion_method: str | None = None
    par_conversion_status: Literal[
        "field_measured", "satellite_retrieved", "analysis_product",
        "estimated", "missing", "not_converted",
        "observed",
    ] = "not_converted"
    source_parameter: str = ""
    quality_status: str = "valid"


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
    """FAO-56 eq. 52 reference evapotranspiration (mm/day).

    Delegates to ``climate.et_calculator.calc_et0_hargreaves``, which is the
    single implementation. This copy used to evaluate the formula itself with
    ``math.sqrt`` — exponent 0.50, which is the published form (FAO-56 eq. 52
    uses 0.5) — but with the MJ-to-mm conversion missing. Callers of this
    function are the simulation orchestrator and
    ``services/api_gateway/routers/hydroma_climate.py``.

    The 0.1 degC floor on the diurnal range is preserved from the original
    expression; FAO-56 gives zero for a flat day and this module's callers have
    always received a small positive number instead.

    The core is given `data=` rather than a precomputed Ra so that it derives
    the extraterrestrial radiation itself. The local `_solar_geometry` returns
    the millimetre-equivalent, and passing that as `ra_mj` would apply the
    0.408 conversion a second time and return a 2.45x underestimate.
    """
    return calc_et0_hargreaves(
        data=ClimateData(tmin=tmin_c, tmax=tmax_c, latitude=latitude_deg, doy=day_of_year),
        dtr_floor=0.1,
    )


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
    """Fetch from Open-Meteo ERA5 archive, including shortwave radiation.

    Now also fetches dew point, relative humidity, soil moisture (3 layers),
    and hourly vapour pressure deficit (aggregated to daily mean) for EWSI.
    """
    http = session if session is not None else requests.Session()
    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start,
        "end_date": end,
        "daily": OPEN_METEO_DAILY_VARS,
        "timezone": "UTC",
    }
    body = _fetch_with_retry(
        http=http,
        url=ARCHIVE_URL,
        params=params,
        timeout=REQUEST_TIMEOUT,
        retry_config=WEATHER_RETRY_CONFIG,
    )
    daily = body.get("daily") or {}
    dates = daily.get("time") or []
    tmin = daily.get("temperature_2m_min") or []
    tmax = daily.get("temperature_2m_max") or []
    precip = daily.get("precipitation_sum") or []
    swrad = daily.get("shortwave_radiation_sum") or []
    dewpoint = daily.get("dew_point_2m_mean") or []
    rh = daily.get("relative_humidity_2m_mean") or []
    sm_0_7 = daily.get("soil_moisture_0_to_7cm_mean") or []
    sm_7_28 = daily.get("soil_moisture_7_to_28cm_mean") or []
    sm_28_100 = daily.get("soil_moisture_28_to_100cm_mean") or []
    if not dates or not tmin or not tmax:
        raise WeatherUnavailable("Open-Meteo response missing daily arrays")

    # Fetch hourly VPD and aggregate to daily mean
    hourly_vpd = _fetch_open_meteo_hourly_vpd(http, latitude, longitude, start, end)
    vpd_daily = _aggregate_hourly_vpd_to_daily(hourly_vpd, dates)

    # Open-Meteo shortwave_radiation_sum is in MJ/m²/day
    return _build_dataframe(
        dates,
        tmin,
        tmax,
        precip,
        latitude,
        shortwave=swrad,
        shortwave_unit="MJ/m^2/day",
        source_label="Open-Meteo ERA5",
        par_values=None,
        par_unit="MJ/m^2/day",
        par_source="",
        par_source_parameter="",
        par_source_reference="",
        dewpoint=dewpoint,
        dewpoint_unit="°C",
        dewpoint_source="Open-Meteo ERA5",
        relative_humidity=rh,
        rh_unit="%",
        rh_source="Open-Meteo ERA5",
        vpd=vpd_daily,
        vpd_unit="kPa",
        vpd_source="Open-Meteo ERA5 (hourly aggregated)",
        soil_moisture_0_7=sm_0_7,
        soil_moisture_0_7_unit="m³/m³",
        soil_moisture_0_7_source="Open-Meteo ERA5",
        soil_moisture_7_28=sm_7_28,
        soil_moisture_7_28_unit="m³/m³",
        soil_moisture_7_28_source="Open-Meteo ERA5",
        soil_moisture_28_100=sm_28_100,
        soil_moisture_28_100_unit="m³/m³",
        soil_moisture_28_100_source="Open-Meteo ERA5",
    )


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
    params: dict[str, Any] = {
        "parameters": "T2M_MIN,T2M_MAX,PRECTOTCORR,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_PAR_TOT",
        "community": "RE",
        "format": "JSON",
        "start": start_fmt,
        "end": end_fmt,
        "latitude": latitude,
        "longitude": longitude,
    }
    data = _fetch_with_retry(
        http=http,
        url="https://power.larc.nasa.gov/api/temporal/daily/point",
        params=params,
        timeout=REQUEST_TIMEOUT,
        retry_config=WEATHER_RETRY_CONFIG,
    )

    timeseries = data.get("properties", {}).get("parameter", {})
    tmin_dict = timeseries.get("T2M_MIN", {})
    tmax_dict = timeseries.get("T2M_MAX", {})
    precip_dict = timeseries.get("PRECTOTCORR", {})
    sw_dict = timeseries.get("ALLSKY_SFC_SW_DWN", {})
    par_dict = timeseries.get("ALLSKY_SFC_PAR_TOT", {})
    dates = sorted(set(tmin_dict) & set(tmax_dict) & set(precip_dict))
    if not dates:
        raise WeatherUnavailable("NASA POWER response missing daily arrays")

    # NASA POWER ALLSKY_SFC_SW_DWN is in kW-hr/m^2/day; convert to MJ/m²/day
    # NASA POWER ALLSKY_SFC_PAR_TOT is in MJ/m²/day (direct PAR, from CERES SYN1deg)
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
        sw_raw = float(sw_dict.get(day, -999.0))
        sw_val = sw_raw * KWH_TO_MJ if sw_raw > -900.0 else 0.0
        # Direct PAR from CERES SYN1deg Ed. 4.2 (Su et al., 2007)
        par_raw = float(par_dict.get(day, -999.0))
        par_val = par_raw if par_raw > -900.0 else 0.0
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
                "ShortwaveRadiation": round(sw_val, 2),
                "PAR": round(par_val, 2),
            }
        )
    if not rows:
        raise WeatherUnavailable("NASA POWER returned no usable days")
    df = pd.DataFrame(rows, columns=WEATHER_COLUMNS)
    df["Date"] = pd.to_datetime(df["Date"])
    df.attrs["shortwave_unit"] = "MJ/m^2/day"
    df.attrs["shortwave_source"] = "NASA POWER"
    df.attrs["shortwave_source_parameter"] = "ALLSKY_SFC_SW_DWN"
    df.attrs["par_unit"] = "MJ/m^2/day"
    df.attrs["par_source"] = "NASA POWER"
    df.attrs["par_source_parameter"] = NASA_POWER_PAR_PARAMETER
    df.attrs["par_source_reference"] = (
        "Su et al. (2007), CERES SYN1deg Ed. 4.2"
    )
    return df


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
    chirps_assets = pipeline.fetch_data(
        "chirps",
        {
            "bbox": bbox,
            "start_date": start,
            "end_date": end,
        },
    )

    if not chirps_assets:
        raise WeatherUnavailable("CHIRPS returned no data")

    # Get NCEP Reanalysis for temperature
    ncep_bbox = [longitude - 2.5, latitude - 2.5, longitude + 2.5, latitude + 2.5]
    ncep_assets = pipeline.fetch_data(
        "ncep_reanalysis",
        {
            "bbox": ncep_bbox,
            "variables": ["air"],
            "start_date": start,
            "end_date": end,
        },
    )

    if not ncep_assets:
        raise WeatherUnavailable("NCEP Reanalysis returned no data")

    # For simplicity, return a basic dataframe structure
    # In production, this would properly merge CHIRPS precip with NCEP temps
    raise WeatherUnavailable(
        "CHIRPS/NCEP merger not fully implemented - use Open-Meteo or NASA POWER"
    )


def _build_dataframe(
    dates, tmin, tmax, precip, latitude,
    shortwave=None, shortwave_unit: str = "MJ/m^2/day",
    source_label: str = "Open-Meteo ERA5",
    par_values=None, par_unit: str = "MJ/m^2/day",
    par_source: str = "", par_source_parameter: str = "",
    par_source_reference: str = "",
    dewpoint=None, dewpoint_unit: str = "degC", dewpoint_source: str = "",
    relative_humidity=None, rh_unit: str = "%", rh_source: str = "",
    vpd=None, vpd_unit: str = "kPa", vpd_source: str = "",
    soil_moisture_0_7=None,
    soil_moisture_0_7_unit: str = "m3/m3",
    soil_moisture_0_7_source: str = "",
    soil_moisture_7_28=None,
    soil_moisture_7_28_unit: str = "m3/m3",
    soil_moisture_7_28_source: str = "",
    soil_moisture_28_100=None,
    soil_moisture_28_100_unit: str = "m3/m3",
    soil_moisture_28_100_source: str = "",
) -> pd.DataFrame:
    """Build aquacrop-compatible DataFrame from daily arrays.

    If ``shortwave`` is provided, it is added as a ``ShortwaveRadiation``
    column in MJ/m²/day.  If ``par_values`` is provided (direct PAR from the
    data source), it is added as a ``PAR`` column.  When PAR is not directly
    available, the PAR column is set to NaN — downstream code must not
    silently convert shortwave to PAR without recording the conversion.
    """
    rows = []
    for i, day in enumerate(dates):
        dt = datetime.strptime(day, "%Y-%m-%d")
        min_c = float(tmin[i])
        max_c = float(tmax[i])
        pr = float(precip[i]) if i < len(precip) else 0.0
        et0 = hargreaves_et0(min_c, max_c, latitude, dt.timetuple().tm_yday)
        sw_val = (
            float(shortwave[i]) if shortwave is not None and i < len(shortwave)
            else float("nan")
        )
        par_val = (
            float(par_values[i]) if par_values is not None and i < len(par_values)
            else float("nan")
        )
        dp_val = (
            float(dewpoint[i]) if dewpoint is not None and i < len(dewpoint)
            else float("nan")
        )
        rh_val = (
            float(relative_humidity[i])
            if relative_humidity is not None and i < len(relative_humidity)
            else float("nan")
        )
        vpd_val = (
            float(vpd[i]) if vpd is not None and i < len(vpd)
            else float("nan")
        )
        sm07_val = (
            float(soil_moisture_0_7[i])
            if soil_moisture_0_7 is not None and i < len(soil_moisture_0_7)
            else float("nan")
        )
        sm728_val = (
            float(soil_moisture_7_28[i])
            if soil_moisture_7_28 is not None and i < len(soil_moisture_7_28)
            else float("nan")
        )
        sm28100_val = (
            float(soil_moisture_28_100[i])
            if soil_moisture_28_100 is not None and i < len(soil_moisture_28_100)
            else float("nan")
        )
        rows.append(
            {
                "MinTemp": min_c,
                "MaxTemp": max_c,
                "Precipitation": pr,
                "ReferenceET": round(et0, 2),
                "Date": dt,
                "ShortwaveRadiation": round(sw_val, 2) if sw_val == sw_val else float("nan"),
                "PAR": round(par_val, 2) if par_val == par_val else float("nan"),
                "DewPoint": round(dp_val, 2) if dp_val == dp_val else float("nan"),
                "RelativeHumidity": round(rh_val, 1) if rh_val == rh_val else float("nan"),
                "VapourPressureDeficit": round(vpd_val, 3) if vpd_val == vpd_val else float("nan"),
                "SoilMoisture_0_7cm": round(sm07_val, 4) if sm07_val == sm07_val else float("nan"),
                                "SoilMoisture_7_28cm": round(sm728_val, 4)
                if sm728_val == sm728_val else float("nan"),
                                "SoilMoisture_28_100cm": round(sm28100_val, 4)
                if sm28100_val == sm28100_val else float("nan"),
            }
        )
    df = pd.DataFrame(rows, columns=WEATHER_COLUMNS)
    df["Date"] = pd.to_datetime(df["Date"])
    df.attrs["shortwave_unit"] = "MJ/m^2/day"
    df.attrs["shortwave_source"] = source_label
    df.attrs["shortwave_source_parameter"] = (
        "shortwave_radiation_sum" if "Open-Meteo" in source_label else "ALLSKY_SFC_SW_DWN"
    )
    df.attrs["par_unit"] = par_unit
    df.attrs["par_source"] = par_source
    df.attrs["par_source_parameter"] = par_source_parameter
    df.attrs["par_source_reference"] = par_source_reference
    df.attrs["dewpoint_unit"] = dewpoint_unit
    df.attrs["dewpoint_source"] = dewpoint_source
    df.attrs["relative_humidity_unit"] = rh_unit
    df.attrs["relative_humidity_source"] = rh_source
    df.attrs["vpd_unit"] = vpd_unit
    df.attrs["vpd_source"] = vpd_source
    df.attrs["soil_moisture_0_7cm_unit"] = soil_moisture_0_7_unit
    df.attrs["soil_moisture_0_7cm_source"] = soil_moisture_0_7_source
    df.attrs["soil_moisture_7_28cm_unit"] = soil_moisture_7_28_unit
    df.attrs["soil_moisture_7_28cm_source"] = soil_moisture_7_28_source
    df.attrs["soil_moisture_28_100cm_unit"] = soil_moisture_28_100_unit
    df.attrs["soil_moisture_28_100cm_source"] = soil_moisture_28_100_source
    return df


def growing_season_window(
    planting_date: str, harvest_date: str, buffer_days: int = 15
) -> tuple[date, date]:
    """Convert 'YYYY/MM/DD' planting/harvest dates to an ISO (start, end) pair."""
    start = datetime.strptime(planting_date, "%Y/%m/%d").date()
    end = datetime.strptime(harvest_date, "%Y/%m/%d").date() + timedelta(days=buffer_days)
    return start, end


# PAR conversion and seasonal climate inputs live in par_pipeline.py to keep
# this module focused on raw weather fetching and under the 800-line ceiling.
# They are re-exported here for backward-compatible imports.
from engine.hydroma.simulation.par_pipeline import (  # noqa: E402,F401
    DEFAULT_PAR_SPEC,
    PARConversionSpec,
    SeasonalClimateInputs,
    build_seasonal_climate_inputs,
    compute_hyrue_seasonal,
    convert_shortwave_to_par,
)


# PAR conversion and seasonal climate inputs are in par_pipeline.py to keep
# this module focused on raw weather fetching and under the 800-line ceiling.
# They are re-exported here for backward-compatible imports.
