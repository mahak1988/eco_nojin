"""End-to-end seasonal prediction orchestrator for HY-RUE.

This module is the **single entry point** that connects the weather data
pipeline, the scientific models, and the evaluation framework into one
executable flow:

    SeasonalPredictionRequest
        -> fetch/accept weather data
        -> resolve PAR  (direct measurement -> shortwave conversion)
        -> resolve LAI  (observed -> empirical NDVI -> GDD model -> fail)
        -> resolve EWSI (external array -> compute from inputs -> fail)
        -> build_seasonal_climate_inputs
        -> compute_hyrue_seasonal
        -> wrap in PredictionResult with full provenance
        -> OperationalReport for diagnostics

Design rules (Stage 26):

1.  This module coordinates; it does NOT re-implement scientific equations.
    All conversion, model execution, and provenance tracking happen in the
    existing modules: ``weather_source``, ``par_pipeline``, ``lai_model``,
    ``ewsi_pipeline``, ``hyrue``.

2.  ``input_source_policy`` controls how aggressively the pipeline fills gaps:
    - ``strict``             — require measured/retrieved data for all inputs;
                                 fail if any are estimated/model-generated.
    - ``allow_estimated``    — accept model-generated LAI and converted PAR,
                                 but never silently replace observations.
    - ``diagnostic``         — run with whatever is available for debugging,
                                 clearly flag every limitation.

3.  ``computation_status`` (SUCCESS / FAIL_CLOSED / PARTIAL / NOT_ATTEMPTED)
    is **never** confused with
    ``external_validation_status`` (VALIDATED_EXTERNAL / BLOCKED / ...).
    A successful computation with no independent observations remains
    ``external_validation_status = BLOCKED``.

4.  Synthetic data, if used, is only accepted when explicitly passed in;
    real predictions never silently substitute synthetic data for measured data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

import numpy as np
import pandas as pd

from engine.hydroma.eval.prediction import (
    ComputationStatus,
    ExternalValidationStatus,
    InputQuality,
    PredictionResult,
    ScientificSupportStatus,
)
from engine.hydroma.models.hyrue import HYRUEParams
from engine.hydroma.simulation.ewsi_pipeline import (
    EWSIComputationPolicy,
    EWSIInputSeries,
    compute_daily_ewsi,
)
from engine.hydroma.simulation.par_pipeline import (
    SeasonalClimateInputs,
    build_seasonal_climate_inputs,
    compute_hyrue_seasonal,
)
from engine.hydroma.simulation.weather_source import (
    WeatherUnavailable,
    fetch_daily_weather,
    normalize_par_provenance,
)


class InputSourcePolicy(StrEnum):
    """Policy controlling how aggressively the pipeline fills data gaps."""

    STRICT = "strict"
    ALLOW_ESTIMATED = "allow_estimated_inputs"
    DIAGNOSTIC = "diagnostic"


@dataclass
class EWSIInputs:
    """Daily inputs for EWSI computation from external sources."""

    nir: np.ndarray | None = None
    swir: np.ndarray | None = None
    vpd: np.ndarray | None = None
    soil_moisture: np.ndarray | None = None
    soil_field_capacity: float = 0.35


@dataclass
class SeasonalPredictionRequest:
    """Request to run an end-to-end seasonal HYRUE prediction.

    Attributes:
        site_id: Stable site identifier.
        season_id: Season identifier (crop + year, e.g. ``"wheat_2024"``).
        crop: Crop name (``"wheat"``, ``"maize"``, ``"rice"``, ``"potato"``).
        planting_date: ISO date string ``YYYY-MM-DD``.
        harvest_date: ISO date string ``YYYY-MM-DD``.
        latitude: Site latitude (WGS84 decimal degrees).
        longitude: Site longitude (WGS84 decimal degrees).
        hyrue_params: Explicit :class:`HYRUEParams` for the model run.  When
            ``None`` (the default) the crop preset is used.  Supplying it
            evaluates a specific, frozen parameter set instead of the
            preset, which is what a calibrated model evaluation requires.
        input_source_policy: How aggressively to fill data gaps.
        weather_data: Optional pre-fetched weather DataFrame. If provided,
            ``fetch_daily_weather`` is **not** called (enables testing without
            network access). The caller is responsible for labeling the data
            source.
        lai_array: Optional directly-measured LAI array (highest priority).
        ndvi_array: Optional NDVI array for empirical LAI (LAI = 3.5 * NDVI).
        ewsi_inputs: Optional EWSI input series from external data.
        ewsi_array: Optional pre-computed EWSI array.
        data_label: Label for the data source (default ``"weather_source"``).
    """

    site_id: str
    season_id: str
    crop: str
    planting_date: str
    harvest_date: str
    latitude: float
    longitude: float
    input_source_policy: InputSourcePolicy = InputSourcePolicy.ALLOW_ESTIMATED
    weather_data: pd.DataFrame | None = None
    lai_array: np.ndarray | None = None
    ndvi_array: np.ndarray | None = None
    ewsi_inputs: EWSIInputs | None = None
    ewsi_array: np.ndarray | None = None
    data_label: str = "weather_source"
    hyrue_params: HYRUEParams | None = None

    def start_date(self) -> str:
        return self.planting_date

    def end_date(self) -> str:
        return self.harvest_date

    def n_days(self) -> int:
        start = datetime.strptime(self.planting_date, "%Y-%m-%d").date()
        end = datetime.strptime(self.harvest_date, "%Y-%m-%d").date()
        return (end - start).days + 1


@dataclass
class OperationalReport:
    """Diagnostic report produced alongside every seasonal prediction.

    Attributes:
        prediction_id: Matches the PredictionResult.
        request: Echo of the original request parameters.
        data_acquisition: How weather and ancillary data were obtained.
        input_provenance: Provenance of each input (PAR, LAI, EWSI, T_mean).
        computation: Model version, parameters, computation mode.
        quality: Input quality, computation status, validation status.
        warnings: Non-fatal issues encountered.
        errors: Fatal errors that prevented computation.
        scientific_limitations: Human-readable summary of limitations.
        reproducibility: Hash, version, and source identifiers for re-running.
    """

    prediction_id: str
    request: dict[str, Any]
    data_acquisition: dict[str, Any]
    input_provenance: dict[str, Any]
    computation: dict[str, Any]
    quality: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    scientific_limitations: list[str] = field(default_factory=list)
    reproducibility: dict[str, Any] = field(default_factory=dict)
    #: Where the report's inputs came from.  The engine resolves weather
    #: from ERA5 (NASA POWER fallback), LAI from the GDD model, and EWSI
    #: from Sentinel-2 L2A plus VPD and soil moisture.
    data_source: str = "engine_seasonal_pipeline"

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "request": self.request,
            "data_acquisition": self.data_acquisition,
            "input_provenance": self.input_provenance,
            "computation": self.computation,
            "quality": self.quality,
            "warnings": self.warnings,
            "errors": self.errors,
            "scientific_limitations": self.scientific_limitations,
            "reproducibility": self.reproducibility,
            "data_source": self.data_source,
        }


InputSourcePolicyLiteral = Literal["strict", "allow_estimated_inputs", "diagnostic"]


def _resolve_ewsi_array(
    request: SeasonalPredictionRequest,
    n_days: int,
    climate_inputs_preview: SeasonalClimateInputs | None = None,
) -> tuple[np.ndarray | None, dict[str, Any] | None, list[str]]:
    """Resolve EWSI data for the growing season.

    Priority:
    1. ``request.ewsi_array`` — pre-computed EWSI from an external source.
    2. ``request.ewsi_inputs`` — compute EWSI from NIR/SWIR/VPD/SM via EWSI model,
       respecting ``request.ewsi_computation_policy``.
    3. None — EWSI is missing.

    Returns (ewsi_array, provenance_dict, warnings).
    """
    warnings_list: list[str] = []

    if request.ewsi_array is not None:
        arr = np.asarray(request.ewsi_array, dtype=float)
        if arr.shape != (n_days,):
            raise ValueError(
                f"ewsi_array length {arr.size} does not match season length {n_days}"
            )
        ewsi_clipped = np.clip(arr, 0.0, 1.0)
        provenance = {
            "source_model": "external",
            "quality_status": "observed" if request.ewsi_inputs is None else "model_generated",
            "scientific_status": "observed",
            "method": "pre-computed from external source",
            "unit": "dimensionless",
            "valid_range": (0.0, 1.0),
        }
        return ewsi_clipped, provenance, warnings_list

    if request.ewsi_inputs is not None and (
        request.ewsi_inputs.nir is not None
        or request.ewsi_inputs.vpd is not None
        or request.ewsi_inputs.soil_moisture is not None
    ):
        dates_list = _dates_from_request(request)
        input_series = EWSIInputSeries(
            dates=dates_list,
            nir=(
                np.asarray(request.ewsi_inputs.nir, dtype=float)
                if request.ewsi_inputs.nir is not None
                else None
            ),
            swir=(
                np.asarray(request.ewsi_inputs.swir, dtype=float)
                if request.ewsi_inputs.swir is not None
                else None
            ),
            vpd=(
                np.asarray(request.ewsi_inputs.vpd, dtype=float)
                if request.ewsi_inputs.vpd is not None
                else None
            ),
            soil_moisture=(
                np.asarray(request.ewsi_inputs.soil_moisture, dtype=float)
                if request.ewsi_inputs.soil_moisture is not None
                else None
            ),
            soil_field_capacity=request.ewsi_inputs.soil_field_capacity,
        )

        # Determine EWSI computation policy from request
        policy = EWSIComputationPolicy.STRICT
        if request.input_source_policy == InputSourcePolicy.ALLOW_ESTIMATED:
            policy = EWSIComputationPolicy.ALLOW_ESTIMATED
        elif request.input_source_policy == InputSourcePolicy.DIAGNOSTIC:
            policy = EWSIComputationPolicy.ALLOW_ESTIMATED

        try:
            output = compute_daily_ewsi(input_series, policy=policy)
        except ValueError as exc:
            warnings_list.append(f"EWSI computation blocked: {exc}")
            return None, None, warnings_list

        provenance = {
            "source_model": "EWSI",
            "quality_status": output.quality_status,
            "scientific_status": output.scientific_status,
            "method": output.method,
            "unit": output.unit,
            "valid_range": output.valid_range,
            "weights": output.weights,
            "missing_fields": output.missing_fields,
            "computation_policy": output.computation_policy,
            "component_provenance": [
                {
                    "component": cp.component,
                    "present": cp.present,
                    "quality_status": cp.quality_status,
                    "source": cp.source,
                    "source_product": cp.source_product,
                    "weight": cp.weight,
                    "original_weight": cp.original_weight,
                }
                for cp in output.component_provenance
            ],
        }
        warnings_list.append(
            "EWSI computed from NIR/SWIR/VPD/SM inputs (novel composite index, "
            "not externally validated)."
        )
        if output.missing_fields:
            warnings_list.append(
                f"EWSI missing components: {', '.join(output.missing_fields)}; "
                f"weights redistributed among available components."
            )
        return output.ewsi, provenance, warnings_list

    warnings_list.append("EWSI: no EWSI data provided (external or computed from inputs).")
    return None, None, warnings_list


def _dates_from_request(request: SeasonalPredictionRequest) -> list[str]:
    """Generate a list of ISO date strings for the growing season."""
    start = datetime.strptime(request.planting_date, "%Y-%m-%d").date()
    end = datetime.strptime(request.harvest_date, "%Y-%m-%d").date()
    n_days = (end - start).days + 1
    return [(start + timedelta(days=i)).isoformat() for i in range(n_days)]


def _resolve_lai_with_policy(
    request: SeasonalPredictionRequest,
    daily_tmean: np.ndarray,
) -> tuple[np.ndarray | None, dict[str, Any] | None, list[str]]:
    """Resolve LAI data respecting the input source policy.

    Priority:
    1. ``request.lai_array`` — directly observed LAI.
    2. ``request.ndvi_array`` — empirical LAI from NDVI (3.5 * NDVI).
    3. GDD model — if policy allows estimated inputs.
    4. None — if policy is strict, this is an error.

    Returns (lai_array, provenance_dict, warnings).
    """
    from engine.hydroma.simulation.lai_model import (
        LAIModel,
        LAIModelConfig,
    )

    warnings_list: list[str] = []
    n_days = len(daily_tmean)

    if request.lai_array is not None:
        lai = np.asarray(request.lai_array, dtype=float)
        if lai.shape != (n_days,):
            raise ValueError(
                f"lai_array length {lai.size} does not match season length {n_days}"
            )
        provenance = {
            "source_model": "user_provided",
            "quality_status": "observed",
            "scientific_status": "observed",
            "method": "direct field or satellite measurement",
            "unit": "m²/m²",
            "valid_range": (0.1, 8.0),
        }
        return lai, provenance, warnings_list

    if request.ndvi_array is not None:
        ndvi = np.asarray(request.ndvi_array, dtype=float)
        if ndvi.shape != (n_days,):
            raise ValueError(
                f"ndvi_array length {ndvi.size} does not match season length {n_days}"
            )
        config = LAIModelConfig(crop=request.crop.lower())
        model = LAIModel(config=config)
        lai, provenance = model.compute_with_provenance(daily_tmean, ndvi=ndvi)
        if lai is not None:
            provenance["source_model"] = "LAIModel"
            return lai, provenance, warnings_list

    if request.input_source_policy == InputSourcePolicy.STRICT:
        warnings_list.append(
            "LAI: no observed or empirical LAI available; strict policy blocks "
            "GDD model fallback."
        )
        return None, None, warnings_list

    if request.ndvi_array is not None and len(warnings_list) == 0:
        warnings_list.append(
            "LAI: NDVI provided but produced no LAI output; "
            "falling back to GDD model."
        )

    config = LAIModelConfig(crop=request.crop.lower(), lai_max=4.0)
    model = LAIModel(config=config)
    lai, provenance = model.compute_with_provenance(daily_tmean)
    provenance["source_model"] = "LAIModel"
    warnings_list.append(
        "LAI: no observed or NDVI data available; GDD model fallback used "
        "(provenance: model_generated)."
    )
    return lai, provenance, warnings_list


def _validate_request(request: SeasonalPredictionRequest) -> list[str]:
    """Validate the request structure and date range.

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []
    try:
        start = datetime.strptime(request.planting_date, "%Y-%m-%d").date()
        end = datetime.strptime(request.harvest_date, "%Y-%m-%d").date()
    except ValueError:
        errors.append("planting_date and harvest_date must be ISO format 'YYYY-MM-DD'")
        return errors

    if end < start:
        errors.append("harvest_date must not precede planting_date")

    if (end - start).days > 366:
        errors.append("growing season exceeds 366 days; slice into shorter requests")

    if request.latitude < -90.0 or request.latitude > 90.0:
        errors.append(f"latitude {request.latitude} out of range [-90, 90]")

    if request.longitude < -180.0 or request.longitude > 180.0:
        errors.append(f"longitude {request.longitude} out of range [-180, 180]")

    if request.crop.strip() == "":
        errors.append("crop must be a non-empty string")

    return errors


def _check_alignment(
    request: SeasonalPredictionRequest,
    climate_inputs: SeasonalClimateInputs,
) -> list[str]:
    """Verify temporal and spatial alignment of assembled inputs.

    Checks:
    - All daily arrays have the same length as the date list.
    - Dates are monotonically increasing with no duplicates.
    - Dates fall within the requested growing season window.
    """
    warnings_list: list[str] = []
    dates = climate_inputs.dates
    n = len(dates)

    if n == 0:
        warnings_list.append("alignment: no dates in climate inputs")
        return warnings_list

    # Check for duplicate dates
    if len(set(dates)) != n:
        dupes = [d for d in dates if dates.count(d) > 1]
        warnings_list.append(f"alignment: duplicate dates detected: {set(dupes)}")

    # Check monotonic ordering
    parsed = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
    for i in range(1, n):
        if parsed[i] < parsed[i - 1]:
            warnings_list.append(
                f"alignment: dates not monotonic at index {i}: "
                f"{dates[i-1]} -> {dates[i]}"
            )
            break

    # Check dates within growing season window
    season_start = datetime.strptime(request.planting_date, "%Y-%m-%d").date()
    season_end = datetime.strptime(request.harvest_date, "%Y-%m-%d").date()
    for i, d in enumerate(parsed):
        if d < season_start or d > season_end:
            warnings_list.append(
                f"alignment: date {d} at index {i} falls outside "
                f"growing season [{season_start}, {season_end}]"
            )

    # Check array lengths
    for name, arr in [
        ("par", climate_inputs.par),
        ("lai", climate_inputs.lai),
        ("ewsi", climate_inputs.ewsi),
        ("t_mean", climate_inputs.t_mean),
    ]:
        if arr is not None:
            arr_size = np.asarray(arr).size
            if arr_size != n:
                warnings_list.append(
                    f"alignment: {name} length {arr_size} != date count {n}"
                )

    return warnings_list


def _build_prediction_result(
    request: SeasonalPredictionRequest,
    hyrue_result: dict[str, Any],
    climate_inputs: SeasonalClimateInputs,
    prediction_id: str,
    warnings_list: list[str],
) -> PredictionResult:
    """Wrap a HYRUE seasonal computation result into a PredictionResult."""
    yield_t_ha = hyrue_result.get("yield_t_ha")
    if yield_t_ha is not None and np.ndim(yield_t_ha) > 0:
        yield_val = float(np.mean(yield_t_ha))
    elif yield_t_ha is not None:
        yield_val = float(yield_t_ha)
    else:
        yield_val = None

    par_prov = climate_inputs.par_provenance or "estimated"
    if par_prov == "converted_documented":
        par_prov = "estimated"

    lai_prov = climate_inputs.lai_provenance
    lai_quality = lai_prov.get("quality_status", "unknown") if lai_prov else "unknown"

    ewsi_prov = climate_inputs.ewsi_provenance
    ewsi_quality = ewsi_prov.get("quality_status", "unknown") if ewsi_prov else "unknown"

    computation_mode = hyrue_result.get("computation_mode", "unknown")

    if computation_mode == "legacy_constant":
        computation_status = ComputationStatus.PARTIAL
        warnings_list.append(
            "Computation used legacy_constant mode (not seasonal integration); "
            "daily LAI/EWSI data was incomplete."
        )
    else:
        computation_status = ComputationStatus.COMPUTED

    if "warning" in hyrue_result:
        warnings_list.append(f"HYRUE: {hyrue_result['warning']}")

    # Scientific support: depends on data sources
    if lai_quality == "observed" and ewsi_quality in ("observed", "model_generated"):
        scientific_status = ScientificSupportStatus.REFERENCED
    elif lai_quality == "model_generated" or par_prov == "estimated":
        scientific_status = ScientificSupportStatus.PARTIAL
        warnings_list.append(
            "Scientific support is PARTIAL: LAI is model-generated or PAR is estimated."
        )
    else:
        scientific_status = ScientificSupportStatus.DEFAULTED

    has_external_evidence = not request.data_label.startswith("synthetic")
    external_val_status = (
        ExternalValidationStatus.BLOCKED
        if not has_external_evidence
        else ExternalValidationStatus.UNVALIDATED
    )

    input_quality_map = {
        "complete": InputQuality.COMPLETE,
        "partial": InputQuality.PARTIAL,
        "unavailable": InputQuality.UNAVAILABLE,
    }
    input_quality = input_quality_map.get(
        climate_inputs.input_quality, InputQuality.PARTIAL
    )

    data_source = request.data_label

    return PredictionResult(
        prediction_id=prediction_id,
        site_id=request.site_id,
        season_id=request.season_id,
        variable="yield",
        value=yield_val,
        unit="t/ha",
        computation_status=computation_status.value,
        scientific_support_status=scientific_status.value,
        external_validation_status=external_val_status.value,
        input_quality=input_quality.value,
        model_name="HY-RUE",
        model_version="2.0.0",
        data_source=data_source,
        computed=True,
        par_provenance=par_prov,
        par_conversion_spec=(
            {
                "method": climate_inputs.par_conversion_spec.method,
                "reference": climate_inputs.par_conversion_spec.reference,
                "status": climate_inputs.par_conversion_spec.status,
                "coeff_source": climate_inputs.par_conversion_spec.coeff_source,
                "frac_par": climate_inputs.par_conversion_spec.frac_par,
            }
            if climate_inputs.par_conversion_spec is not None
            else None
        ),
        lai_provenance=lai_prov,
        ewsi_provenance=ewsi_prov,
        shortwave_source=(
            climate_inputs.shortwave_source or "missing"
        ),
        missing_fields=list(climate_inputs.missing_fields),
        metadata={
            "computation_mode": computation_mode,
            "crop": request.crop,
            "planting_date": request.planting_date,
            "harvest_date": request.harvest_date,
            "input_source_policy": request.input_source_policy.value,
            "season_length_days": len(climate_inputs.dates),
        },
    )


def compute_seasonal_prediction(
    request: SeasonalPredictionRequest,
    input_sink: list[dict[str, Any]] | None = None,
) -> tuple[PredictionResult, OperationalReport]:
    """Run the full end-to-end seasonal HYRUE prediction pipeline.

    This is the **single entry point** for seasonal predictions. It:

    1. Validates the request.
    2. Acquires weather data (fetches from real sources or uses injected data).
    3. Resolves LAI, EWSI, and PAR per the input source policy.
    4. Assembles ``SeasonalClimateInputs``.
    5. Runs ``compute_hyrue_seasonal``.
    6. Wraps the result in a :class:`PredictionResult` with full provenance.
    7. Produces an :class:`OperationalReport` for diagnostics.

    Args:
        request: A :class:`SeasonalPredictionRequest` describing the site,
            season, crop, and data source policy.
        input_sink: Optional list.  When given, the resolved daily inputs
            (PAR, LAI, EWSI, T_mean) are appended to it after assembly, in
            the exact form the model consumed them.  Calibration tooling
            uses this so that a fitted parameter set is fitted against the
            same input basis it is later evaluated on; it changes nothing
            about the computation.

    Returns:
        A tuple of (PredictionResult, OperationalReport).

    Raises:
        ValueError: if the request is structurally invalid.
        WeatherUnavailable: if weather data cannot be obtained and no
            pre-fetched data was provided, or if required inputs are missing
            under the current policy.
    """
    prediction_id = f"PRED-{uuid4().hex[:12].upper()}"
    warnings_list: list[str] = []
    errors_list: list[str] = []
    scientific_limitations: list[str] = []

    request_echo = {
        "site_id": request.site_id,
        "season_id": request.season_id,
        "crop": request.crop,
        "planting_date": request.planting_date,
        "harvest_date": request.harvest_date,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "input_source_policy": request.input_source_policy.value,
        "data_label": request.data_label,
    }

    data_acquisition: dict[str, Any] = {
        "weather": "not_attempted",
        "lai": "not_attempted",
        "ewsi": "not_attempted",
        "par": "not_attempted",
    }

    # --- Step 1: Validate request ---
    request_errors = _validate_request(request)
    if request_errors:
        errors_list.extend(request_errors)
        report = OperationalReport(
            prediction_id=prediction_id,
            request=request_echo,
            data_acquisition=data_acquisition,
            input_provenance={},
            computation={},
            quality={
                "computation_status": ComputationStatus.NOT_ATTEMPTED.value,
                "external_validation_status": ExternalValidationStatus.BLOCKED.value,
                "input_quality": InputQuality.UNAVAILABLE.value,
            },
            warnings=warnings_list,
            errors=errors_list,
            scientific_limitations=[
                "Request validation failed; computation not attempted."
            ],
            reproducibility={
                "model_name": "HY-RUE",
                "model_version": "2.0.0",
                "prediction_id": prediction_id,
            },
        )
        raise ValueError(f"Invalid seasonal prediction request: {'; '.join(request_errors)}")

    n_days = request.n_days()

    # --- Step 2: Acquire weather data ---
    if request.weather_data is not None:
        weather_df = request.weather_data
        data_acquisition["weather"] = (
            f"pre_fetched ({request.data_label})"
        )
    else:
        try:
            weather_df = fetch_daily_weather(
                request.latitude,
                request.longitude,
                request.planting_date,
                request.harvest_date,
            )
            data_acquisition["weather"] = "fetched (Open-Meteo/NASA POWER)"
        except WeatherUnavailable as exc:
            data_acquisition["weather"] = f"failed: {exc}"
            errors_list.append(f"Weather unavailable: {exc}")
            report = OperationalReport(
                prediction_id=prediction_id,
                request=request_echo,
                data_acquisition=data_acquisition,
                input_provenance={},
                computation={},
                quality={
                    "computation_status": ComputationStatus.NOT_ATTEMPTED.value,
                    "external_validation_status": ExternalValidationStatus.BLOCKED.value,
                    "input_quality": InputQuality.UNAVAILABLE.value,
                },
                warnings=warnings_list,
                errors=errors_list,
                scientific_limitations=[
                    "Weather data acquisition failed; "
                    "computation not attempted."
                ],
                reproducibility={
                    "model_name": "HY-RUE",
                    "model_version": "2.0.0",
                    "prediction_id": prediction_id,
                },
            )
            raise WeatherUnavailable(
                f"Cannot acquire weather data for {request.site_id}: {exc}"
            ) from exc

    # --- Step 3: Resolve LAI ---
    tmin = weather_df["MinTemp"].to_numpy(dtype=float)
    tmax = weather_df["MaxTemp"].to_numpy(dtype=float)
    daily_tmean = (tmin + tmax) / 2.0

    lai_arr, lai_prov, lai_warnings = _resolve_lai_with_policy(request, daily_tmean)
    warnings_list.extend(lai_warnings)
    if lai_prov is not None:
        data_acquisition["lai"] = lai_prov.get("quality_status", "unknown")
    else:
        data_acquisition["lai"] = "unavailable"

    # --- Step 4: Resolve EWSI ---
    ewsi_arr, ewsi_prov, ewsi_warnings = _resolve_ewsi_array(request, n_days)
    warnings_list.extend(ewsi_warnings)
    if ewsi_prov is not None:
        data_acquisition["ewsi"] = ewsi_prov.get("quality_status", "unknown")
    else:
        data_acquisition["ewsi"] = "unavailable"

    # --- Step 5: Build seasonal climate inputs ---
    try:
        climate_inputs = build_seasonal_climate_inputs(
            weather=weather_df,
            lai_array=lai_arr,
            lai_provenance=lai_prov,
            ewsi_array=ewsi_arr,
            ewsi_provenance=ewsi_prov,
            ndvi_array=request.ndvi_array,
            crop=request.crop,
        )
    except (WeatherUnavailable, ValueError) as exc:
        errors_list.append(f"Failed to build seasonal climate inputs: {exc}")
        report = OperationalReport(
            prediction_id=prediction_id,
            request=request_echo,
            data_acquisition=data_acquisition,
            input_provenance={
                "par": climate_inputs.par_provenance if "climate_inputs" in dir() else "not_built",
                "lai": lai_prov,
                "ewsi": ewsi_prov,
            },
            computation={},
            quality={
                "computation_status": ComputationStatus.NOT_ATTEMPTED.value,
                "external_validation_status": ExternalValidationStatus.BLOCKED.value,
                "input_quality": InputQuality.UNAVAILABLE.value,
            },
            warnings=warnings_list,
            errors=errors_list,
            scientific_limitations=["Climate input assembly failed."],
            reproducibility={
                "model_name": "HY-RUE",
                "model_version": "2.0.0",
                "prediction_id": prediction_id,
            },
        )
        raise

    # Determine PAR provenance string
    par_prov_str = normalize_par_provenance(climate_inputs.par_provenance)
    data_acquisition["par"] = par_prov_str

    # --- Step 5b: Capture the resolved daily inputs (optional) ---
    # Calibration tooling needs the *exact* arrays this pipeline resolved so
    # that a fitted parameter set is fitted against the same basis it is
    # evaluated on.  Capturing here, after assembly, guarantees that.
    if input_sink is not None:
        input_sink.append(
            {
                "par": np.asarray(climate_inputs.par, dtype=float),
                "lai": np.asarray(climate_inputs.lai, dtype=float),
                "ewsi": np.asarray(climate_inputs.ewsi, dtype=float),
                "t_mean": np.asarray(climate_inputs.t_mean, dtype=float),
                "dates": list(climate_inputs.dates),
                "input_quality": climate_inputs.input_quality,
                "missing_fields": list(climate_inputs.missing_fields or []),
                "lai_provenance": lai_prov,
                "ewsi_provenance": ewsi_prov,
                "par_provenance": climate_inputs.par_provenance,
            }
        )

    # --- Step 6: Check alignment ---
    alignment_warnings = _check_alignment(request, climate_inputs)
    warnings_list.extend(alignment_warnings)

    # --- Step 7: Check policy compliance ---
    if request.input_source_policy == InputSourcePolicy.STRICT:
        if lai_prov is not None and lai_prov.get("quality_status") in (
            "model_generated",
            "estimated",
        ):
            errors_list.append(
                "Strict policy: LAI is model-generated, not observed."
            )
        if par_prov_str in ("estimated", "converted_documented", "not_converted"):
            errors_list.append(
                "Strict policy: PAR is estimated/converted, not measured."
            )
        if ewsi_prov is not None and ewsi_prov.get("scientific_status") != "observed":
            errors_list.append(
                "Strict policy: EWSI scientific status is not observed."
            )
        if not errors_list:
            data_acquisition["par"] = f"strict-accepted: {par_prov_str}"
        else:
            report = OperationalReport(
                prediction_id=prediction_id,
                request=request_echo,
                data_acquisition=data_acquisition,
                input_provenance={
                    "par": par_prov_str,
                    "lai": lai_prov,
                    "ewsi": ewsi_prov,
                    "t_mean": "computed from MinTemp/MaxTemp",
                    "shortwave": climate_inputs.shortwave_source or "unknown",
                },
                computation={
                    "model_name": "HY-RUE",
                    "model_version": "2.0.0",
                    "computation_mode": "not_attempted",
                    "reason": "strict policy rejected estimated/model-generated inputs",
                },
                quality={
                    "computation_status": ComputationStatus.NOT_ATTEMPTED.value,
                    "external_validation_status": ExternalValidationStatus.BLOCKED.value,
                    "input_quality": climate_inputs.input_quality,
                    "missing_fields": list(climate_inputs.missing_fields),
                },
                warnings=warnings_list,
                errors=errors_list,
                scientific_limitations=[
                    "Strict policy blocked computation due to estimated inputs."
                ],
                reproducibility={
                    "model_name": "HY-RUE",
                    "model_version": "2.0.0",
                    "prediction_id": prediction_id,
                },
            )
            raise WeatherUnavailable("; ".join(errors_list))

    # --- Step 8: Run HYRUE seasonal ---
    try:
        hyrue_result = compute_hyrue_seasonal(
            climate_inputs,
            crop=request.crop,
            allow_legacy_fallback=(
                request.input_source_policy == InputSourcePolicy.DIAGNOSTIC
            ),
            params=request.hyrue_params,
        )
    except WeatherUnavailable as exc:
        errors_list.append(str(exc))
        report = OperationalReport(
            prediction_id=prediction_id,
            request=request_echo,
            data_acquisition=data_acquisition,
            input_provenance={
                "par": par_prov_str,
                "lai": lai_prov,
                "ewsi": ewsi_prov,
                "t_mean": "computed from MinTemp/MaxTemp",
                "shortwave": climate_inputs.shortwave_source or "unknown",
            },
            computation={},
            quality={
                "computation_status": ComputationStatus.FAIL_CLOSED.value,
                "external_validation_status": ExternalValidationStatus.BLOCKED.value,
                "input_quality": climate_inputs.input_quality,
                "missing_fields": list(climate_inputs.missing_fields),
            },
            warnings=warnings_list,
            errors=errors_list,
                            scientific_limitations=[
                    "HYRUE seasonal computation could not complete "
                    "due to missing inputs."
                ],
            reproducibility={
                "model_name": "HY-RUE",
                "model_version": "2.0.0",
                "prediction_id": prediction_id,
            },
        )
        raise

    # --- Step 9: Wrap in PredictionResult ---
    prediction = _build_prediction_result(
        request, hyrue_result, climate_inputs, prediction_id, warnings_list
    )

    # --- Step 10: Scientific limitations ---
    if lai_prov is not None and lai_prov.get("quality_status") == "model_generated":
        scientific_limitations.append(
            "LAI was generated by the GDD sigmoid model (placeholder growth curve, "
            "not a validated crop model)."
        )
    if par_prov_str in ("estimated", "converted_documented"):
        scientific_limitations.append(
            "PAR was derived via the 0.5 shortwave-to-PAR conversion (calibration-"
            "grade assumption, not site-measured)."
        )
    if ewsi_prov is not None and ewsi_prov.get("scientific_status") == "novel":
        scientific_limitations.append(
            "EWSI is a novel composite index (NDMI+VPD+soil moisture); sub-indices "
            "other than NDMI have no external validation."
        )
    if "legacy_constant" in hyrue_result.get("computation_mode", ""):
        scientific_limitations.append(
            "Legacy constant-conditions mode was used due to incomplete daily data; "
            "seasonal total may be overstated."
        )
    if not scientific_limitations:
        scientific_limitations.append(
            "No specific limitations: inputs are measured or satellite-retrieved."
        )

    data_hash = _compute_data_hash(
        weather_df, lai_arr, ewsi_arr, request.crop, request.hyrue_params
    )

    report = OperationalReport(
        prediction_id=prediction_id,
        request=request_echo,
        data_acquisition=data_acquisition,
        input_provenance={
            "par": par_prov_str,
            "lai": lai_prov,
            "ewsi": ewsi_prov,
            "t_mean": "computed from MinTemp/MaxTemp",
            "shortwave": climate_inputs.shortwave_source or "unknown",
        },
        computation={
            "model_name": hyrue_result.get("model_name", "HY-RUE"),
            "model_version": hyrue_result.get("model_version", "2.0.0"),
            "computation_mode": hyrue_result.get("computation_mode", "unknown"),
            "yield_t_ha": prediction.value,
            "total_biomass_g_m2": hyrue_result.get("total_biomass_g_m2"),
            "season_length_days": hyrue_result.get("season_length_days", n_days),
            "params_used": {
                "epsilon": _get_param(hyrue_result),
                "crop": request.crop,
            },
        },
        quality={
            "computation_status": prediction.computation_status,
            "scientific_support_status": prediction.scientific_support_status,
            "external_validation_status": prediction.external_validation_status,
            "input_quality": prediction.input_quality,
            "missing_fields": list(climate_inputs.missing_fields),
        },
        warnings=warnings_list,
        errors=errors_list,
        scientific_limitations=scientific_limitations,
        reproducibility={
            "model_name": "HY-RUE",
            "model_version": "2.0.0",
            "prediction_id": prediction_id,
            "data_hash": data_hash,
            "par_conversion_spec": (
                hyrue_result.get("par_conversion_spec")
                if "par_conversion_spec" in hyrue_result
                else (
                    {
                        "method": climate_inputs.par_conversion_spec.method,
                        "status": climate_inputs.par_conversion_spec.status,
                        "frac_par": climate_inputs.par_conversion_spec.frac_par,
                    }
                    if climate_inputs.par_conversion_spec
                    else None
                ),
            ),
            "planting_date": request.planting_date,
            "harvest_date": request.harvest_date,
            "season_id": request.season_id,
            "site_id": request.site_id,
        },
    )

    return prediction, report


def _get_param(hyrue_result: dict[str, Any]) -> float:
    """Extract epsilon from HYRUE result metadata if available."""
    return hyrue_result.get("epsilon", 2.5)


def _compute_data_hash(
    weather_df: pd.DataFrame,
    lai_arr: np.ndarray | None,
    ewsi_arr: np.ndarray | None,
    crop: str,
    hyrue_params: HYRUEParams | None = None,
) -> str:
    """Compute a deterministic hash of the input data for reproducibility."""
    import hashlib
    import json

    payload = {"crop": crop}

    if hyrue_params is not None:
        # The model parameters are part of the evaluation identity: the same
        # inputs under a different (e.g. calibrated) parameter set are a
        # different result and must not share a data hash.
        payload["hyrue_params"] = {
            "epsilon": float(hyrue_params.epsilon),
            "hi": float(hyrue_params.hi),
            "k": float(hyrue_params.k),
            "t_opt": float(hyrue_params.t_opt),
            "t_min": float(hyrue_params.t_min),
            "t_max": float(hyrue_params.t_max),
            "lai_max": float(hyrue_params.lai_max),
        }

    if weather_df is not None and len(weather_df) > 0:
        payload["weather_shape"] = list(weather_df.shape)
        payload["weather_dtypes"] = {
            col: str(weather_df[col].dtype) for col in weather_df.columns
        }
        if "ShortwaveRadiation" in weather_df.columns:
            payload["shortwave_mean"] = float(weather_df["ShortwaveRadiation"].mean())
        if "MinTemp" in weather_df.columns:
            payload["tmin_mean"] = float(weather_df["MinTemp"].mean())
        if "MaxTemp" in weather_df.columns:
            payload["tmax_mean"] = float(weather_df["MaxTemp"].mean())

    if lai_arr is not None:
        payload["lai_shape"] = list(lai_arr.shape)
        payload["lai_mean"] = float(np.mean(lai_arr)) if lai_arr.size > 0 else None

    if ewsi_arr is not None:
        payload["ewsi_shape"] = list(ewsi_arr.shape)
        payload["ewsi_mean"] = float(np.mean(ewsi_arr)) if ewsi_arr.size > 0 else None

    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_synthetic_weather(
    n_days: int,
    start_date: str = "2024-04-01",
    latitude: float = 40.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a synthetic weather DataFrame for testing.

    **This data is explicitly labeled ``synthetic_test_data`` and must never
    be used for scientific predictions.** It is provided so the end-to-end
    pipeline can be tested without network access.

    Args:
        n_days: Number of days to generate.
        start_date: ISO date string for the first day.
        latitude: Site latitude (affects ET0 computation).
        seed: RNG seed for reproducibility.

    Returns:
        A weather DataFrame with the same structure as
        :func:`weather_source.fetch_daily_weather`.
    """
    from engine.hydroma.simulation.weather_source import _build_dataframe

    rng = np.random.default_rng(seed)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    dates = [start_dt + timedelta(days=i) for i in range(n_days)]

    day_of_year = np.array([d.timetuple().tm_yday for d in dates])

    # Synthetic temperature with seasonal sinusoid
    tmax = 20.0 + 8.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365.0) + rng.normal(0, 3, n_days)
    tmin = tmax - 5.0 - rng.normal(0, 1, n_days)
    tmin = np.maximum(tmin, -10.0)

    # Synthetic shortwave (MJ/m²/day)
    sw = 15.0 + 5.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365.0)
    sw = np.maximum(sw + rng.normal(0, 1, n_days), 0.0)

    # Synthetic precipitation (mostly dry with occasional rain)
    precip = np.where(rng.random(n_days) < 0.1, rng.uniform(0, 15, n_days), 0.0)


    df = _build_dataframe(
        dates=[d.isoformat() for d in dates],
        tmin=tmin.tolist(),
        tmax=tmax.tolist(),
        precip=precip.tolist(),
        latitude=latitude,
        shortwave=sw.tolist(),
        shortwave_unit="MJ/m^2/day",
        source_label="synthetic_test_data",
        par_values=None,
        par_unit="MJ/m^2/day",
        par_source="",
        par_source_parameter="",
        par_source_reference="",
    )
    df.attrs["data_label"] = "synthetic_test_data"
    return df
