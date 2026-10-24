"""Daily Vapor Pressure Deficit (VPD) model.

Computes VPD from air temperature and dew-point temperature (or relative
humidity) using the FAO-56 / Tetens saturation vapor pressure equation.

All temperatures are expected in degrees Celsius.  Kelvin inputs are
explicitly converted before computation; unit guessing is not permitted.

Reference: FAO-56, Equation 11-13 (saturation vapor pressure).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from engine.hydroma.simulation.quality_status import QualityStatus


@dataclass
class VPDInput:
    """Daily inputs for VPD computation.

    Attributes:
        date: ISO date string.
        t_mean_c: Mean air temperature in °C (required if t_max/t_min not given).
        t_max_c: Maximum air temperature in °C (optional).
        t_min_c: Minimum air temperature in °C (optional).
        dewpoint_c: Dew-point temperature in °C (optional).
        relative_humidity_pct: Relative humidity in percent 0-100 (optional).
        source: Data source label (e.g. "ERA5-Land", "Open-Meteo").
        source_product: Product identifier (e.g. "ERA5-Land", "NASA POWER").
        quality_status: QualityStatus of the input data.
    """

    date: str
    t_mean_c: float | None = None
    t_max_c: float | None = None
    t_min_c: float | None = None
    dewpoint_c: float | None = None
    relative_humidity_pct: float | None = None
    source: str = ""
    source_product: str = ""
    quality_status: QualityStatus = QualityStatus.REANALYSIS_ESTIMATE


@dataclass
class VPDOutput:
    """Daily VPD computation output.

    Attributes:
        date: ISO date string.
        vpd_kpa: Vapor pressure deficit in kPa (>= 0).
        es_kpa: Saturation vapor pressure at mean temperature (kPa).
        ea_kpa: Actual vapor pressure (kPa).
        t_mean_c: Mean temperature used (°C).
        dewpoint_c: Dew-point temperature used (°C, if available).
        relative_humidity_pct: Relative humidity used (%, if available).
        source: Data source label.
        source_product: Product identifier.
        quality_status: QualityStatus of the output.
        computation_method: "dewpoint" or "relative_humidity".
        hourly_coverage: Fraction of hours with valid data (0-1, if known).
    """

    date: str
    vpd_kpa: float
    es_kpa: float
    ea_kpa: float
    t_mean_c: float
    dewpoint_c: float | None = None
    relative_humidity_pct: float | None = None
    source: str = ""
    source_product: str = ""
    quality_status: QualityStatus = QualityStatus.REANALYSIS_ESTIMATE
    computation_method: str = "dewpoint"
    hourly_coverage: float | None = None


def saturation_vapor_pressure(t_c: float) -> float:
    """Saturation vapor pressure using the Tetens equation (FAO-56 Eq. 11).

    es(T) = 0.6108 * exp(17.27 * T / (T + 237.3))

    Args:
        t_c: Temperature in degrees Celsius.

    Returns:
        Saturation vapor pressure in kPa.

    Raises:
        ValueError: if temperature is outside [-50, 60] °C.
    """
    if t_c < -50.0 or t_c > 60.0:
        raise ValueError(
            f"Temperature {t_c}°C outside valid range [-50, 60] °C"
        )
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def kelvin_to_celsius(t_k: float) -> float:
    """Convert Kelvin to degrees Celsius.

    Args:
        t_k: Temperature in Kelvin.

    Returns:
        Temperature in degrees Celsius.
    """
    return t_k - 273.15


def compute_vpd_from_dewpoint(
    t_mean_c: float,
    dewpoint_c: float,
) -> VPDOutput | None:
    """Compute VPD from mean temperature and dew-point temperature.

    VPD = max(es(T) - es(Td), 0)

    Args:
        t_mean_c: Mean air temperature in °C.
        dewpoint_c: Dew-point temperature in °C.

    Returns:
        :class:`VPDOutput` with VPD and component values, or None if
        dewpoint > temperature (physically impossible for the given inputs).
    """
    if dewpoint_c > t_mean_c:
        return None  # Physically impossible: Td cannot exceed T

    es = saturation_vapor_pressure(t_mean_c)
    ea = saturation_vapor_pressure(dewpoint_c)
    vpd = max(es - ea, 0.0)

    return VPDOutput(
        date="",
        vpd_kpa=vpd,
        es_kpa=es,
        ea_kpa=ea,
        t_mean_c=t_mean_c,
        dewpoint_c=dewpoint_c,
        relative_humidity_pct=None,
        computation_method="dewpoint",
    )


def compute_vpd_from_relative_humidity(
    t_mean_c: float,
    relative_humidity_pct: float,
) -> VPDOutput:
    """Compute VPD from mean temperature and relative humidity.

    ea = es(T) * RH / 100
    VPD = max(es(T) - ea, 0)

    Args:
        t_mean_c: Mean air temperature in °C.
        relative_humidity_pct: Relative humidity in percent (0-100).

    Returns:
        :class:`VPDOutput` with VPD and component values.

    Raises:
        ValueError: if RH is outside [0, 100].
    """
    if relative_humidity_pct < 0.0 or relative_humidity_pct > 100.0:
        raise ValueError(
            f"Relative humidity {relative_humidity_pct}% outside [0, 100]"
        )

    es = saturation_vapor_pressure(t_mean_c)
    ea = es * relative_humidity_pct / 100.0
    vpd = max(es - ea, 0.0)

    # Derive equivalent dewpoint from ea for reporting
    # Td = 237.3 * ln(ea/0.6108) / (17.27 - ln(ea/0.6108))
    dewpoint_c: float | None = None
    if ea > 0:
        ln_ea_over_06108 = math.log(ea / 0.6108)
        dewpoint_c = 237.3 * ln_ea_over_06108 / (17.27 - ln_ea_over_06108)

    return VPDOutput(
        date="",
        vpd_kpa=vpd,
        es_kpa=es,
        ea_kpa=ea,
        t_mean_c=t_mean_c,
        dewpoint_c=dewpoint_c,
        relative_humidity_pct=relative_humidity_pct,
        computation_method="relative_humidity",
    )


def compute_daily_vpd(
    inputs: VPDInput,
) -> VPDOutput:
    """Compute daily VPD from a :class:`VPDInput`.

    Priority:
    1. If dewpoint_c is provided, use the dewpoint method.
    2. Else if relative_humidity_pct is provided, use the RH method.
    3. Else, raise ValueError.

    If both dewpoint and RH are provided, the dewpoint method is used
    and the RH is reported for cross-checking only (not substituted).

    Args:
        inputs: :class:`VPDInput` with temperature and moisture data.

    Returns:
        :class:`VPDOutput` with computed VPD.

    Raises:
        ValueError: if no moisture variable (dewpoint or RH) is provided,
            or if dewpoint > temperature (physically impossible).
    """
    t_mean = inputs.t_mean_c
    if t_mean is None:
        # Try to derive from t_max and t_min
        if inputs.t_max_c is not None and inputs.t_min_c is not None:
            t_mean = (inputs.t_max_c + inputs.t_min_c) / 2.0
        else:
            raise ValueError(
                "VPD requires t_mean_c (or t_max_c and t_min_c)"
            )

    date_str = inputs.date

    # Priority 1: dewpoint temperature
    if inputs.dewpoint_c is not None:
        result = compute_vpd_from_dewpoint(t_mean, inputs.dewpoint_c)
        if result is None:
            raise ValueError(
                f"Dewpoint {inputs.dewpoint_c}°C exceeds temperature "
                f"{t_mean}°C on {date_str} — physically impossible"
            )
        result.date = date_str
        result.source = inputs.source
        result.source_product = inputs.source_product
        result.quality_status = inputs.quality_status
        if inputs.relative_humidity_pct is not None:
            result.relative_humidity_pct = inputs.relative_humidity_pct
        return result

    # Priority 2: relative humidity
    if inputs.relative_humidity_pct is not None:
        result = compute_vpd_from_relative_humidity(t_mean, inputs.relative_humidity_pct)
        result.date = date_str
        result.source = inputs.source
        result.source_product = inputs.source_product
        result.quality_status = inputs.quality_status
        return result

    raise ValueError(
        "VPD requires either dewpoint_c or relative_humidity_pct"
    )


def aggregate_hourly_to_daily(
    hourly_temps: list[float],
    hourly_dewpoints: list[float] | None = None,
    hourly_rh: list[float] | None = None,
    date: str = "",
) -> VPDOutput:
    """Aggregate hourly temperature/moisture data into daily VPD.

    VPD is computed per hour from paired temperature and moisture, then
    averaged across the day.  This is preferred over computing VPD from
    daily-mean temperature and daily-mean moisture, which can bias the
    result.

    Args:
        hourly_temps: List of hourly temperatures in °C.
        hourly_dewpoints: Optional list of hourly dewpoints in °C.
        hourly_rh: Optional list of hourly relative humidity in percent.
        date: ISO date string for the output.

    Returns:
        :class:`VPDOutput` with daily-mean VPD.

    Raises:
        ValueError: if no moisture data is provided, or if input lists
            are empty or mismatched in length.
    """
    n = len(hourly_temps)
    if n == 0:
        raise ValueError("hourly_temps must not be empty")

    if hourly_dewpoints is not None and len(hourly_dewpoints) != n:
        raise ValueError(
            f"hourly_dewpoints length {len(hourly_dewpoints)} != "
            f"hourly_temps length {n}"
        )
    if hourly_rh is not None and len(hourly_rh) != n:
        raise ValueError(
            f"hourly_rh length {len(hourly_rh)} != "
            f"hourly_temps length {n}"
        )

    hourly_vpds: list[float] = []
    for i in range(n):
        t = hourly_temps[i]
        if hourly_dewpoints is not None:
            dp = hourly_dewpoints[i]
            if dp is not None:
                result = compute_vpd_from_dewpoint(t, dp)
                if result is not None:
                    hourly_vpds.append(result.vpd_kpa)
        elif hourly_rh is not None:
            rh = hourly_rh[i]
            if rh is not None:
                result = compute_vpd_from_relative_humidity(t, rh)
                hourly_vpds.append(result.vpd_kpa)

    if not hourly_vpds:
        raise ValueError("No valid hourly VPD values could be computed")

    daily_vpd = float(np.mean(hourly_vpds))
    daily_tmean = float(np.mean(hourly_temps))

    # Compute daily es/ea from daily mean temp for reporting
    es_daily = saturation_vapor_pressure(daily_tmean)

    if hourly_dewpoints is not None:
        valid_dps = [d for d in hourly_dewpoints if d is not None]
        ea_daily = (
            saturation_vapor_pressure(float(np.mean(valid_dps)))
            if valid_dps
            else es_daily - daily_vpd
        )
        method = "dewpoint"
    else:
        ea_daily = es_daily - daily_vpd
        method = "relative_humidity"

    return VPDOutput(
        date=date,
        vpd_kpa=daily_vpd,
        es_kpa=es_daily,
        ea_kpa=ea_daily,
        t_mean_c=daily_tmean,
        computation_method=method,
        hourly_coverage=len(hourly_vpds) / n,
    )


def vpd_stress(
    vpd_values: np.ndarray | list[float],
    vpd_low: float,
    vpd_high: float,
) -> np.ndarray:
    """Convert VPD values to a water stress index in [0, 1].

    S_VPD = clip((VPD - VPD_low) / (VPD_high - VPD_low), 0, 1)

    Requires VPD_high > VPD_low.  When VPD_high <= VPD_low, raises ValueError.

    Args:
        vpd_values: VPD array in kPa.
        vpd_low: VPD below which stress is 0 (no stress).
        vpd_high: VPD above which stress is 1 (severe stress).

    Returns:
        Stress array in [0, 1].

    Raises:
        ValueError: if VPD_high <= VPD_low.
    """
    if vpd_high <= vpd_low:
        raise ValueError(
            f"VPD_high ({vpd_high}) must be greater than VPD_low ({vpd_low})"
        )

    arr = np.asarray(vpd_values, dtype=float)
    stress = (arr - vpd_low) / (vpd_high - vpd_low)
    return np.clip(stress, 0.0, 1.0)
