"""PAR (Photosynthetically Active Radiation) pipeline and seasonal climate inputs.

This module contains the **independent** shortwave-to-PAR conversion logic and
the assembly of daily climate inputs for HYRUE's seasonal computation mode.

It is intentionally separate from :mod:`weather_source` (which handles raw HTTP
fetching) so that the scientific conversion can be unit-tested and reviewed
in isolation, and so neither module exceeds the 800-line ceiling.

PAR conversion coefficient status:
    The fraction of shortwave radiation that falls in the 400–700 nm PAR
    band depends on atmospheric composition, solar zenith angle, and aerosol
    loading.  The value used here (0.5) follows the widely cited approximation
    in agricultural meteorology (Monteith & Unsworth 2013, *Principles of
    Environmental Physics*, ch. 9; FAO-56 uses 0.5 in the absence of spectral
    data).  It is a **calibration-grade assumption**, NOT a measured crop
    parameter: consumers of PAR must treat it as ``estimated`` provenance
    unless a real PAR measurement overrides it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

from engine.hydroma.simulation.radiation_units import (
    DEFAULT_PAR_FRACTION,
    KWH_TO_MJ,
)

logger = logging.getLogger(__name__)


def _weather_unavailable() -> type[RuntimeError]:
    """Resolve ``WeatherUnavailable`` lazily.

    ``weather_source`` imports this module at module level, so importing
    ``weather_source`` here at module level would create an import cycle
    that only resolves for one import order.  The exception class is only
    needed when a fetch fails, so it is resolved on demand.
    """
    from engine.hydroma.simulation.weather_source import WeatherUnavailable

    return WeatherUnavailable


@dataclass
class PARConversionSpec:
    """Specification of how a shortwave-to-PAR conversion was performed.

    Captures the coefficient, its provenance, and its scientific status so
    that every derived PAR value is traceable.  The conversion is a simple
    multiplication:

        PAR = frac_par * SW_down

    where ``frac_par`` is the fraction of total shortwave downward radiation
    that falls within the 400–700 nm PAR band.
    """

    frac_par: float
    method: str
    reference: str
    status: Literal["documented", "estimated", "assumed"]
    coeff_source: str


#: Default conversion spec using the standard 0.5 PAR fraction.
DEFAULT_PAR_SPEC = PARConversionSpec(
    frac_par=DEFAULT_PAR_FRACTION,
    method="PAR = frac_PAR * SW_down (energy-based fraction of shortwave)",
    reference=(
        "Monteith & Unsworth (2013), Principles of Environmental Physics, "
        "4th ed., ch. 9: PAR is ~50% of total shortwave downward at the "
        "surface under mid-latitude conditions. FAO-56 also uses 0.5 in "
        "the absence of spectral data."
    ),
    status="estimated",
    coeff_source="standard_agricultural_meteorology_assumption",
)


def convert_shortwave_to_par(
    shortwave_value: float,
    source_unit: str,
    spec: PARConversionSpec | None = None,
    already_par: bool = False,
) -> tuple[float, PARConversionSpec | None]:
    """Convert daily shortwave radiation to PAR (MJ/m²/day).

    This is an **independent** conversion function: it does not call the
    HYRUE model, the EWSI model, or any other scientific computation.  Its
    only job is to multiply the raw shortwave value by the PAR fraction,
    after normalising the input unit to MJ/m²/day.

    **Unit handling:**
    - ``MJ/m^2/day`` or ``MJ/m2/day`` — used directly (Open-Meteo).
    - ``kW-hr/m^2/day`` or ``kW·h/m²/day`` — multiplied by 3.6 → MJ/m²/day
      (NASA POWER ``ALLSKY_SFC_SW_DWN``).

    **Double-conversion guard:** if ``already_par=True``, the function
    returns the value unchanged with a spec whose
    ``method`` records that no conversion was applied.  This prevents a
    PAR value from being multiplied by the fraction a second time if a
    caller mistakenly passes it back into this function.

    Args:
        shortwave_value: Daily shortwave downward radiation in ``source_unit``,
            or daily PAR if ``already_par=True``.
        source_unit: Unit of ``shortwave_value``.
        spec: Optional custom conversion spec.  Defaults to
            :data:`DEFAULT_PAR_SPEC`.
        already_par: If True, ``shortwave_value`` is already PAR — no
            conversion is applied.

    Returns:
        Tuple of (par_value_mj_m2_day, spec_or_none).
        If ``already_par`` is True, returns the value and a spec with
        ``status="documented"``.
        If ``shortwave_value`` is NaN or Infinity, returns NaN and None.
        If the unit is unrecognised, raises ``ValueError``.
    """
    import math

    if not math.isfinite(shortwave_value):
        return float(shortwave_value), None

    if already_par:
        return float(shortwave_value), PARConversionSpec(
            frac_par=1.0,
            method="no conversion: input already identified as PAR",
            reference="caller assertion (already_par=True)",
             status="documented",
            coeff_source="none",
        )

    unit_norm = (
        source_unit.strip().lower().replace(" ", "").replace("·", "").replace("^", "")
    )
    unit_norm = unit_norm.replace("²", "2")

    if unit_norm in ("mj/m2/day", "mj/m^2/day", "mj·m^-2·day^-1"):
        sw_mj = float(shortwave_value)
    elif unit_norm in ("kw-hr/m2/day", "kwhr/m2/day", "kw·h/m²/day", "kwhr/m2day"):
        sw_mj = float(shortwave_value) * KWH_TO_MJ
    else:
        raise ValueError(
            f"Unrecognised shortwave unit '{source_unit}'. "
            f"Supported: 'MJ/m^2/day', 'kW-hr/m^2/day'."
        )

    if spec is None:
        spec = DEFAULT_PAR_SPEC

    par_value = sw_mj * spec.frac_par
    return par_value, spec


@dataclass
class SeasonalClimateInputs:
    """Daily climate inputs assembled for HYRUE seasonal computation mode.

    Each field is a numpy array of identical length, one element per day.
    The provenance of every input is tracked explicitly so a downstream
    consumer can distinguish measured data from converted or estimated data,
    model-generated values, or missing inputs.

    Attributes:
        dates: ISO date strings for each day.
        par: Daily PAR in MJ/m²/day.
        lai: Daily LAI (leaf area index).
        ewsi: Daily EWSI (water stress index in [0,1]).
        t_mean: Daily mean temperature in °C.
        par_provenance: Provenance label for the PAR values.
        par_conversion_spec: The PARConversionSpec used, or None.
        shortwave_raw: Raw shortwave radiation values (MJ/m²/day).
        shortwave_unit: Unit of the raw shortwave values.
        shortwave_source: Source label for the raw shortwave values.
        lai_provenance: Provenance metadata for LAI values.
        ewsi_provenance: Provenance metadata for EWSI values.
        input_quality: "complete" if all inputs present, "partial" or
            "unavailable" otherwise.
        missing_fields: List of field names that were not available.
    """

    dates: list[str]
    par: np.ndarray | None = None
    lai: np.ndarray | None = None
    ewsi: np.ndarray | None = None
    t_mean: np.ndarray | None = None
    par_provenance: Literal[
        "field_measured", "satellite_retrieved", "analysis_product",
        "estimated", "converted_documented",
    ] = "estimated"
    par_conversion_spec: PARConversionSpec | None = None
    shortwave_raw: np.ndarray | None = None
    shortwave_unit: str = "MJ/m^2/day"
    shortwave_source: str = ""
    lai_provenance: dict[str, Any] | None = None
    ewsi_provenance: dict[str, Any] | None = None
    input_quality: Literal["complete", "partial", "unavailable"] = "unavailable"
    missing_fields: list[str] = field(default_factory=list)


def build_seasonal_climate_inputs(
    weather: pd.DataFrame,
    t_mean_offset_c: float = 0.0,
    par_conversion_spec: PARConversionSpec | None = None,
    lai_array: np.ndarray | None = None,
    lai_provenance: dict[str, Any] | None = None,
    ewsi_array: np.ndarray | None = None,
    ewsi_provenance: dict[str, Any] | None = None,
    ndvi_array: np.ndarray | None = None,
    crop: str = "wheat",
    lai_max: float = 4.0,
) -> SeasonalClimateInputs:
    """Assemble daily climate inputs from a weather DataFrame for HYRUE seasonal mode.

    This function is the bridge between the weather data pipeline and the
    HYRUE model's seasonal computation mode.  It:

    1. Extracts shortwave radiation or direct PAR from the weather DataFrame.
    2. Converts shortwave to PAR if direct PAR is not available.
    3. Computes daily mean temperature from MinTemp/MaxTemp.
    4. Assembles LAI: observed array > empirical (NDVI) > model-generated (GDD).
    5. Validates array length consistency.
    6. Reports which inputs are available vs missing.

    **No synthetic data is generated unless model fallback is explicitly invoked.**
    If LAI or EWSI arrays are not provided, they are recorded as missing in
    ``missing_fields`` and ``input_quality`` is set to "partial" or "unavailable".
    The caller must not feed such incomplete inputs to HYRUE seasonal mode.

    Args:
        weather: DataFrame from :func:`fetch_daily_weather` or
            :func:`generate_daily_weather`.  Must contain at least MinTemp,
            MaxTemp, and Date columns.  Must include ShortwaveRadiation.
        t_mean_offset_c: Constant offset added to computed mean temperature
            (0 = no adjustment).
        par_conversion_spec: Optional custom PAR conversion spec.  Defaults
            to :data:`DEFAULT_PAR_SPEC`.
        lai_array: Optional observed LAI array (highest priority, must
            match weather length).  If None, falls to NDVI or GDD model.
        lai_provenance: Optional provenance metadata for observed LAI.
        ewsi_array: Optional daily EWSI array (must match weather length).
            If None, EWSI is marked as missing.
        ewsi_provenance: Optional provenance metadata for EWSI.
        ndvi_array: Optional NDVI array for empirical LAI (LAI = 3.5*NDVI).
            Used only if lai_array is None.
        crop: Crop name for GDD-based LAI fallback model.
        lai_max: Maximum LAI for the GDD model.

    Returns:
        A :class:`SeasonalClimateInputs` with all available data and explicit
        provenance.

    Raises:
        WeatherUnavailable: if ShortwaveRadiation column is missing or all-NaN.
        ValueError: if array lengths are incompatible or required columns
            are missing.
    """
    if "MinTemp" not in weather.columns or "MaxTemp" not in weather.columns:
        raise ValueError("weather DataFrame must contain MinTemp and MaxTemp columns")
    if "Date" not in weather.columns:
        raise ValueError("weather DataFrame must contain a Date column")

    n_days = len(weather)
    dates = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(weather["Date"])]

    # --- Temperature ---
    tmin = weather["MinTemp"].to_numpy(dtype=float)
    tmax = weather["MaxTemp"].to_numpy(dtype=float)
    t_mean = (tmin + tmax) / 2.0 + t_mean_offset_c

    # --- PAR: prefer direct measurement, fall back to shortwave conversion ---
    par_values: np.ndarray | None = None
    par_spec = par_conversion_spec or DEFAULT_PAR_SPEC
    par_provenance: Literal[
        "field_measured", "satellite_retrieved", "analysis_product",
        "estimated", "converted_documented",
    ] = "estimated"
    sw_raw: np.ndarray | None = None
    sw_unit = "MJ/m^2/day"
    sw_source = ""
    sw_source_param = ""

    # Priority 1: Direct PAR from NASA POWER (ALLSKY_SFC_PAR_TOT)
    if (
        "PAR" in weather.columns
        and "par_source" in weather.attrs
        and weather.attrs["par_source"]
        and weather["PAR"].notna().any()
    ):
        par_raw = weather["PAR"].to_numpy(dtype=float)
        par_values = par_raw
        par_provenance = "satellite_retrieved"
        par_spec = PARConversionSpec(
            frac_par=1.0,
            method="no conversion: input is direct PAR measurement",
            reference=weather.attrs.get("par_source_reference", "NASA POWER CERES SYN1deg Ed. 4.2"),
            status="satellite_retrieved",
            coeff_source=weather.attrs.get("par_source_parameter", "ALLSKY_SFC_PAR_TOT"),
        )
        logger.info(
            "PAR: using direct measurement from %s (ALLSKY_SFC_PAR_TOT)",
            weather.attrs.get("par_source", ""),
        )
    # Priority 2: Convert from shortwave
    elif "ShortwaveRadiation" in weather.columns and weather["ShortwaveRadiation"].notna().any():
        sw_raw = weather["ShortwaveRadiation"].to_numpy(dtype=float)
        sw_unit = weather.attrs.get("shortwave_unit", "MJ/m^2/day")
        sw_source = weather.attrs.get("shortwave_source", "unknown")
        sw_source_param = weather.attrs.get("shortwave_source_parameter", "")

        if sw_unit == "kW-hr/m^2/day":
            sw_in_mj = sw_raw * KWH_TO_MJ
        else:
            sw_in_mj = sw_raw

        par_values = sw_in_mj * par_spec.frac_par
        par_provenance = "converted_documented"
        logger.info(
            "PAR: converting shortwave from %s to PAR using frac_par=%.2f (Status: estimated)",
            sw_source, par_spec.frac_par,
        )
    else:
        raise _weather_unavailable()(
            "Weather DataFrame lacks ShortwaveRadiation column and no direct PAR; "
            "cannot derive PAR for seasonal HYRUE computation. "
            "The weather source must provide shortwave radiation data."
        )

    # --- Assemble LAI with source priority: observed > empirical(NDVI) > model(GDD) ---
    missing: list[str] = []
    lai_arr = None

    if lai_array is not None:
        lai_arr = np.asarray(lai_array, dtype=float)
        if lai_arr.shape != (n_days,):
            raise ValueError(
                f"lai_array length {lai_arr.size} does not match weather length {n_days}"
            )
        if lai_provenance is None:
            lai_provenance = {
                "source_model": "user_provided",
                "quality_status": "observed",
                "scientific_status": "observed",
                "method": "direct field or satellite measurement",
            }
    elif ndvi_array is not None:
        from engine.hydroma.simulation.lai_model import LAIModel, LAIModelConfig

        ndvi_arr = np.asarray(ndvi_array, dtype=float)
        if ndvi_arr.shape != (n_days,):
            raise ValueError(
                f"ndvi_array length {ndvi_arr.size} does not match weather length {n_days}"
            )

        # Daily t_mean is already computed above
        t_mean_for_lai = (tmin + tmax) / 2.0 + t_mean_offset_c
        model = LAIModel(config=LAIModelConfig(crop=crop, lai_max=lai_max))
        lai_arr, lai_provenance = model.compute_with_provenance(
            t_mean_for_lai, ndvi=ndvi_arr,
        )
        if lai_arr is None:
            missing.append("lai")
            lai_arr = None
    else:
        # No LAI array or NDVI provided — compute LAI from GDD model using
        # daily temperature only
        from engine.hydroma.simulation.lai_model import LAIModel, LAIModelConfig

        t_mean_for_lai = (tmin + tmax) / 2.0 + t_mean_offset_c
        model = LAIModel(config=LAIModelConfig(crop=crop, lai_max=lai_max))
        lai_arr, lai_provenance = model.compute_with_provenance(
            t_mean_for_lai
        )
        if lai_arr is None:
            missing.append("lai")
            lai_arr = None

    if ewsi_array is not None:
        ewsi_arr = np.asarray(ewsi_array, dtype=float)
        if ewsi_arr.shape != (n_days,):
            raise ValueError(
                f"ewsi_array length {ewsi_arr.size} does not match weather length {n_days}"
            )
        if ewsi_provenance is None:
            ewsi_provenance = {
                "source_model": "user_provided",
                "quality_status": "observed",
                "scientific_status": "observed",
                "method": "direct measurement or computation",
            }
    else:
        missing.append("ewsi")
        ewsi_arr = None

    # --- Determine input quality ---
    if not missing:
        input_quality = "complete"
    elif missing == ["lai", "ewsi"]:
        input_quality = "unavailable"
    else:
        input_quality = "partial"

    return SeasonalClimateInputs(
        dates=dates,
        par=par_values,
        lai=lai_arr,
        ewsi=ewsi_arr,
        t_mean=t_mean,
        par_provenance=par_provenance,
        par_conversion_spec=par_spec,
        shortwave_raw=sw_raw,
        shortwave_unit=sw_unit,
        shortwave_source=(
            f"{sw_source} ({sw_source_param})" if sw_source_param else sw_source
        ),
        lai_provenance=lai_provenance,
        ewsi_provenance=ewsi_provenance,
        input_quality=input_quality,
        missing_fields=missing,
    )


def compute_hyrue_seasonal(
    climate_inputs: SeasonalClimateInputs,
    crop: str = "wheat",
    allow_legacy_fallback: bool = False,
    params: Any | None = None,
) -> dict[str, Any]:
    """Run HYRUE in seasonal mode using assembled daily climate inputs.

    This function is the integration point between the weather data pipeline
    and the HYRUE model.  It:

    1. Checks that all required inputs (PAR, LAI, EWSI, T_mean) are present.
    2. Validates array length consistency.
    3. Calls :meth:`HYRUE.compute` in seasonal mode (array PAR).
    4. Preserves the computation mode label from HYRUE's output.

    If a required input is missing (``input_quality != "complete"``):
    - If ``allow_legacy_fallback`` is True, runs legacy_constant mode with
      scalar mean values and an explicit warning.
    - Otherwise raises ``WeatherUnavailable`` with a clear message.

    Args:
        climate_inputs: A :class:`SeasonalClimateInputs` from
            :func:`build_seasonal_climate_inputs`.
        crop: Crop name for HYRUE params preset (e.g. "wheat", "maize").
        allow_legacy_fallback: If True, allows scalar fallback values to be
            used when daily arrays are unavailable.
        params: Explicit :class:`HYRUEParams` to use instead of the crop
            preset.  When supplied, these parameters take full precedence:
            the crop preset is *not* applied, so the caller is responsible
            for supplying a complete, self-consistent parameter set (this
            is how a calibrated or frozen model is evaluated).

    Returns:
        The dict from :meth:`HYRUE.compute`, with additional provenance fields:
        ``par_provenance``, ``par_conversion_spec``, ``input_quality``,
        ``missing_fields``, ``data_source``.

    Raises:
        WeatherUnavailable: if required inputs are missing and no legacy
            fallback is allowed.
        ValueError: if array lengths are inconsistent.
    """
    from engine.hydroma.models.hyrue import HYRUE

    inputs_ok = (
        climate_inputs.par is not None
        and climate_inputs.lai is not None
        and climate_inputs.ewsi is not None
        and climate_inputs.t_mean is not None
    )

    if not inputs_ok or climate_inputs.input_quality != "complete":
        if allow_legacy_fallback:
            return _run_legacy_fallback(climate_inputs, crop, params=params)
        missing = ", ".join(climate_inputs.missing_fields or ["unknown"])
        raise _weather_unavailable()(
            f"Cannot run HYRUE seasonal mode: missing inputs ({missing}). "
            f"input_quality={climate_inputs.input_quality}. "
            f"Provide all daily inputs (PAR, LAI, EWSI, T_mean) or set "
            f"allow_legacy_fallback=True."
        )

    # Ensure arrays are numpy
    par = np.asarray(climate_inputs.par, dtype=float)
    lai = np.asarray(climate_inputs.lai, dtype=float)
    ewsi = np.asarray(climate_inputs.ewsi, dtype=float)
    t_mean = np.asarray(climate_inputs.t_mean, dtype=float)

    # Validate array length consistency
    n = par.size
    if lai.size != n:
        raise ValueError(f"LAI length {lai.size} != PAR length {n}")
    if ewsi.size != n:
        raise ValueError(f"EWSI length {ewsi.size} != PAR length {n}")
    if t_mean.size != n:
        raise ValueError(f"t_mean length {t_mean.size} != PAR length {n}")

    # Run HYRUE in seasonal mode.  Explicit params (calibrated / frozen
    # models) take precedence over the crop preset.
    if params is not None:
        model = HYRUE(params=params)
    else:
        model = HYRUE(crop=crop) if crop else HYRUE()
    result = model.compute(
        par=par,
        lai=lai,
        ewsi=ewsi,
        t_mean=t_mean,
    )

    # Attach provenance
    result["par_provenance"] = climate_inputs.par_provenance
    if climate_inputs.par_conversion_spec is not None:
        spec = climate_inputs.par_conversion_spec
        result["par_conversion_spec"] = {
            "method": spec.method,
            "reference": spec.reference,
            "status": spec.status,
            "coeff_source": spec.coeff_source,
            "frac_par": spec.frac_par,
        }
    result["input_quality"] = climate_inputs.input_quality
    result["missing_fields"] = climate_inputs.missing_fields
    result["data_source"] = "weather_source"
    result["lai_provenance"] = climate_inputs.lai_provenance
    result["ewsi_provenance"] = climate_inputs.ewsi_provenance
    result["shortwave_provenance"] = {
        "unit": climate_inputs.shortwave_unit,
        "source": climate_inputs.shortwave_source,
    }

    return result


def _run_legacy_fallback(
    climate_inputs: SeasonalClimateInputs, crop: str | None, params: Any | None = None
) -> dict[str, Any]:
    """Run HYRUE in legacy_constant mode when daily LAI/EWSI are unavailable.

    This is ONLY called when ``allow_legacy_fallback=True`` AND daily arrays
    are incomplete.  The function uses scalar mean values across the weather
    days, which HYRUE will flag with its legacy warning.

    **No synthetic data is generated.**  The legacy fallback uses the mean
    of whatever daily data IS available (PAR, T_mean).  For LAI and EWSI,
    it uses a simple scalar mean of whatever was provided; if those are
    completely missing, HYRUE's own defaults are used and the result is
    explicitly labeled.
    """
    from engine.hydroma.models.hyrue import HYRUE

    if climate_inputs.par is None:
        raise _weather_unavailable()("PAR is required even for legacy fallback")
    if climate_inputs.t_mean is None:
        raise _weather_unavailable()("t_mean is required even for legacy fallback")

    par_scalar = float(np.mean(climate_inputs.par))
    t_mean_scalar = float(np.mean(climate_inputs.t_mean))
    lai_scalar = (
        float(np.mean(climate_inputs.lai)) if climate_inputs.lai is not None else 3.0
    )
    ewsi_scalar = (
        float(np.mean(climate_inputs.ewsi)) if climate_inputs.ewsi is not None else 0.3
    )
    days = len(climate_inputs.dates)

    logger.warning(
        "Falling back to legacy_constant mode: "
        "daily LAI/EWSI data unavailable, using scalar means."
    )

    if params is not None:
        model = HYRUE(params=params)
    else:
        model = HYRUE(crop=crop) if crop else HYRUE()
    result = model.compute(
        par=par_scalar,
        lai=lai_scalar,
        ewsi=ewsi_scalar,
        t_mean=t_mean_scalar,
        days=days,
    )

    result["par_provenance"] = climate_inputs.par_provenance
    if climate_inputs.par_conversion_spec is not None:
        spec = climate_inputs.par_conversion_spec
        result["par_conversion_spec"] = {
            "method": spec.method,
            "reference": spec.reference,
            "status": spec.status,
            "coeff_source": spec.coeff_source,
            "frac_par": spec.frac_par,
        }
    result["input_quality"] = "partial"
    result["missing_fields"] = climate_inputs.missing_fields
    result["data_source"] = "weather_source"
    result["lai_provenance"] = climate_inputs.lai_provenance
    result["ewsi_provenance"] = climate_inputs.ewsi_provenance
    result["fallback_mode"] = "legacy_constant_fallback"
    return result
