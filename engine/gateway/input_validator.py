"""Input validation and unit-normalisation for the Engine Gateway (A-1 step 2).

The per-route required-input contract (S17, defect D-20), the required-input
resolver, the flat-input boundary validators and the unit-normalisation entry
point are extracted verbatim from `engine/gateway/__init__.py`.
`EngineGateway._normalize_inputs` stays on the class but delegates to the
module-level :func:_normalize_inputs here. Scalar unit scaling is delegated
to :func:engine.gateway.unit_converter.scale_scalar_to_si.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from engine.gateway.contracts import (
    GatewayRequest,
    ModelSpec,
    UnitSpec,
    ValidationResult,
)
from engine.gateway.unit_converter import scale_scalar_to_si

#: Per-route required-input contract (S17, defect D-20).
#:
#: Each entry lists the input groups a wired route cannot compute without:
#: every group is a tuple of accepted aliases and at least one alias must be
#: present and non-None. A request that omits a required group is rejected
#: with ``INVALID_REQUEST`` naming the missing groups instead of crashing
#: inside the computation with a raw TypeError.
REQUIRED_INPUTS: dict[str, tuple[tuple[str, ...], ...]] = {
    # Evapotranspiration and the compiled kernels. Penman-Monteith needs
    # humidity, wind and radiation as well: compute_et forwards None for a
    # missing key and the PM equation rejects it with an honest but late
    # error, so the contract map catches it first (S17 review).
    "CANON-001": (
        ("temp_min", "tmin"),
        ("temp_max", "tmax"),
        ("rh_min", "rh"),
        ("rh_max",),
        ("wind_speed",),
        ("solar_radiation",),
        ("elevation",),
        ("latitude",),
        ("doy",),
    ),
    "CANON-016": (
        ("temp_min", "tmin"),
        ("temp_max", "tmax"),
        ("rh_min", "rh_mean", "rh"),
        ("wind_speed",),
        ("solar_radiation",),
        ("elevation",),
        ("latitude",),
        ("doy",),
    ),
    "CANON-017": (("pressure_head_cm", "pressure_head"), ("texture", "texture_class")),
    # Hydrology and groundwater. CANON-004's adapter accepts the aliases the
    # S16 suite exercises ("precipitation", "rainfall_mm", "rain_mm", "cn").
    "CANON-004": (
        ("precipitation_mm", "precipitation", "rainfall_mm", "rain_mm"),
        ("curve_number", "cn"),
    ),
    "CANON-005": (
        ("transmissivity_m2day",),
        ("storativity",),
        ("pumping_rate_m3day",),
        ("distance_from_well_m",),
        ("time_since_pumping_start_days",),
    ),
    "CANON-006": (
        ("matric_potential",),
        ("theta_r",),
        ("theta_s",),
        ("vg_alpha", "alpha"),
        ("vg_n", "n"),
    ),
    # Soil.
    "SOIL_AWC": (("texture_class", "texture"),),
    "SOIL_WATER_CONTENT": (("matric_potential",), ("texture_class", "texture")),
    "SOIL_HEALTH": (
        ("ph",),
        ("organic_matter",),
        ("nitrogen",),
        ("phosphorus",),
        ("potassium",),
        ("cec",),
        ("texture",),
    ),
    "SOIL_TAXONOMY": (("clay_pct", "clay"), ("silt_pct", "silt"), ("sand_pct", "sand")),
    "SOIL_ESP": (("na",), ("cex",)),
    "SOIL_SAR": (("na",), ("ca",), ("mg",)),
    "SOIL_SALINITY_CLASSIFY": (("ec",),),
    "SOIL_TEXTURE_COORDS": (("sand_pct", "sand"), ("silt_pct", "silt"), ("clay_pct", "clay")),
    # Irrigation.
    "IRRIGATION_DEPTH": (
        ("etc_mm", "etc"),
        ("efficiency",),
        ("effective_rain_mm", "effective_rain"),
    ),
    "IRRIGATION_INTERVAL": (
        ("etc_mm_per_day", "etc_mm_day"),
        ("raw_mm",),
        ("allowable_depletion",),
    ),
    # Economics.
    "ECON_NPV": (("cash_flows",), ("discount_rate",)),
    "ECON_AG_COST": (("area_ha",), ("crop_type",), ("input_costs",)),
    "ECON_AG_REVENUE": (("area_ha",), ("price_per_tonne",)),
    "ECON_FINANCIAL": (("initial_investment",), ("cash_flows",), ("discount_rate",)),
    "ECON_PRICE_RISK": (("base_price",), ("volatility",), ("time_horizon_years",)),
    "ECON_YIELD_RISK": (
        ("expected_yield",),
        ("yield_std_dev",),
        ("area_hectares",),
        ("price_per_unit",),
    ),
    # Scenarios and crop simulation. CROP_YIELD accepts either a nested
    # climate mapping or the flat scalar form, so both spellings satisfy the
    # contract (S17 review: the flat form was rejected while the handler
    # supported it).
    "SCENARIO": (
        ("scenario", "scenario_name"),
        ("baseline_temp",),
        ("baseline_precip",),
        ("target_year",),
    ),
    "CLIMATE_SCENARIO": (
        ("rcp", "scenario"),
        ("years_ahead",),
        ("baseline_temp",),
        ("baseline_precip",),
        ("baseline_et0",),
    ),
    "CLIMATE_PROJECTION": (("rcp", "scenario"), ("year",)),
    "CROP_YIELD": (
        ("crop_type",),
        ("climate_data", "climate", "available_water"),
        ("mean_temp",),
    ),
    # Simulation.
    "SIM_CHAIN": (        ("site_id",),
        ("area_ha",),
        ("scenario",),
        ("r_factor",),
        ("k_factor",),
        ("ls_factor",),
        ("c_factor_base",),
        ("initial_soc_t_ha",),
        ("clay_pct",),
    ),
    "SIM_ORCHESTRATE": (("chains", "chain_inputs"),),
    # Watershed structure design: area in m2 or hectares, slope in percent or
    # as a fraction (S17 review R-6 -- the area and slope must never be
    # silently defaulted to zero, which designed a dam for an empty catchment).
    "WATERSHED_STRUCT": (
        ("structure_type",),
        ("area_m2", "drainage_area_m2", "drainage_area_ha", "area_ha", "area_hectares"),
        ("slope_pct", "slope_percent", "slope"),
    ),
    "WATERSHED_CHECK_DAM": (
        ("area_m2", "drainage_area_m2", "drainage_area_ha", "area_ha", "area_hectares"),
        ("slope_pct", "slope_percent", "slope"),
    ),
    "WATERSHED_CONTOUR_TRENCH": (
        ("area_m2", "drainage_area_m2", "drainage_area_ha", "area_ha", "area_hectares"),
        ("slope_pct", "slope_percent", "slope"),
    ),
    "WATERSHED_HALF_MOON": (
        ("area_m2", "drainage_area_m2", "drainage_area_ha", "area_ha", "area_hectares"),
        ("slope_pct", "slope_percent", "slope"),
    ),
    # MRV and plant neurology.
    "MRV_METRICS": (
        ("soc_pct",),
        ("rainfall_mm",),
        ("slope_length_m",),
        ("slope_percent",),
    ),
    "MRV_VALIDATE_SAT": (("index",), ("value",)),
    "PLANT_NEURO": (("signal_mv", "signal"),),
    # Data pipeline.
    "DATA_PIPELINE": (("name",),),
    # Ids routed through _ROUTES_FOR_REGISTERED_IDS below. Each group lists
    # the aliases the route accepts; a group that the request omits is
    # rejected here rather than reaching a computation that would have to
    # invent the value (the gateway must never default a slope length, a
    # baseline climate, or the date and area a satellite scene is searched
    # over).
    "CANON-007": (("slope_percent", "slope_pct", "slope"), ("slope_length_m", "slope_length")),
    "RUSLE_LS": (("slope_percent", "slope_pct", "slope"), ("slope_length_m", "slope_length")),
    "CANON-008": (("dem", "dem_array", "dem_m"),),
    # CANON-009 needs the cell size because slope in degrees is dz/dx over
    # that spacing: a default spacing would silently rescale every
    # derivative the analysis returns.
    "CANON-009": (("dem", "dem_array", "dem_m"), ("cell_size_m", "cell_size", "resolution")),
    "CANON-010": (
        ("initial_storage_mm", "storage0_mm", "storage_mm"),
        ("months", "time_steps", "n_periods"),
    ),
    "CANON-011": (("latitude", "lat"), ("doy", "day_of_year")),
    "CANON-012": (("quantity", "view"),),
    "CANON-013": (("model", "model_id"), ("data_source", "source")),
    "CANON-014": (("model_id", "view"),),
    "CANON-018": (
        ("ssp", "scenario"),
        ("year", "time_horizon"),
        ("baseline_temp", "baseline_temp_c"),
        ("baseline_precip", "baseline_precip_mm"),
        ("baseline_et0", "baseline_et0_mm"),
    ),
    "CANON-019": (("bbox", "bounds"), ("datetime", "date", "date_range")),
    "CANON-020": (("bbox", "bounds"), ("datetime", "date", "date_range")),
    "CANON-021": (("bbox", "bounds"), ("datetime", "date", "date_range")),
    "CANON-022": (("bbox", "bounds"), ("datetime", "date", "date_range")),
}


def _missing_required_inputs(model_id: str, inputs: dict[str, Any]) -> list[str]:
    """Names of the input groups ``model_id`` requires but the request omits.

    ``MRV_VALIDATE_SAT`` also accepts a single-entry ``index_data`` mapping,
    which supplies both required groups at once. ``CROP_YIELD`` accepts either
    the nested climate mapping or the flat scalar pair, so the required keys
    are resolved inside the mapping when one is given (S17 review R-2).
    """
    groups = REQUIRED_INPUTS.get(model_id)
    if not groups:
        return []
    if model_id == "MRV_VALIDATE_SAT" and isinstance(inputs.get("index_data"), dict):
        if len(inputs["index_data"]) == 1:
            return []
    if model_id == "CROP_YIELD":
        missing: list[str] = []
        climate = inputs.get("climate_data", inputs.get("climate"))
        if isinstance(climate, dict):
            if climate.get("mean_temp") is None and inputs.get("mean_temp") is None:
                missing.append("climate_data.mean_temp or mean_temp")
            if climate.get("available_water") is None and inputs.get("available_water") is None:
                missing.append("climate_data.available_water or available_water")
            return missing
        for group in groups[1:]:  # crop_type first, then the climate pair
            if not any(inputs.get(alias) is not None for alias in group):
                missing.append(" or ".join(group))
        return missing
    missing_groups: list[str] = []
    for group in groups:
        if not any(inputs.get(alias) is not None for alias in group):
            missing_groups.append(" or ".join(group))
    return missing_groups


def _route_float(
    inputs: dict[str, Any], key: str, default: float | None = None
) -> float:
    """A gateway route's float input, validated at the boundary.

    The flat-input contract types every value ``Any | None`` (an omitted key is
    absent, not zero) while the handlers this router calls declare ``float`` or
    ``str`` parameters. That gap was 28 mypy errors and, worse, a silent channel
    where a string could reach arithmetic as a ``TypeError`` inside a handler.

    This validates before dispatch instead: a JSON number passes through
    unchanged (``float(70) is 70.0``), and anything else raises the same
    ``TypeError`` the handler would have raised itself -- only earlier, and
    with the key named. Required-input presence is already enforced upstream by
    ``REQUIRED_INPUTS`` (``INVALID_REQUEST``), so a missing key here is an
    optional-but-used one and the TypeError keeps that contract visible.

    An explicit ``default`` is accepted for the keys the route's contract marks
    optional (the same capability :func:`_route_int` has), so a declared default
    is applied here instead of a ``TypeError``.
    """
    value = inputs.get(key)
    if value is None:
        if default is None:
            raise TypeError(f"{key} is required for this route")
        return float(default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{key} must be a JSON number, got {type(value).__name__}"
        )
    return float(value)


def _route_int(inputs: dict[str, Any], key: str, default: int | None = None) -> int:
    """A gateway route's integer input, validated at the boundary.

    Same contract as :func:`_route_float`, with an explicit ``default`` for the
    keys the contract marks optional (the flat-input contract types an omitted
    key as absent, and the route's own default supplies the value instead of a
    ``TypeError``).
    """
    value = inputs.get(key)
    if value is None:
        if default is None:
            raise TypeError(f"{key} is required for this route")
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be a JSON number, got {type(value).__name__}")
    return int(value)


def _route_array_or_float(
    inputs: dict[str, Any], key: str, default: float | None = None
) -> float | np.ndarray:
    """A gateway route's float-or-array input.

    Like :func:`_route_float`, but also accepts a JSON array of numbers,
    which is converted to a ``numpy.ndarray``. This is used by models that
    can operate in either scalar (single representative day) or array
    (daily time-series) mode, such as HYRUE.
    """
    import numpy as np

    value = inputs.get(key)
    if value is None:
        if default is None:
            raise TypeError(f"{key} is required for this route")
        return float(default)
    if isinstance(value, bool):
        raise TypeError(f"{key} must be a JSON number or array, got bool")
    if isinstance(value, (list, tuple)):
        return np.asarray([float(v) for v in value], dtype=float)
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{key} must be a JSON number or array, got {type(value).__name__}"
        )
    return float(value)


def _route_optional_float(inputs: dict[str, Any], key: str) -> float | None:
    """A gateway route's OPTIONAL float input.

    Same contract as :func:`_route_float`, except that an absent key returns
    ``None`` instead of raising -- which is what the handler's own
    ``float | None = None`` signature declares. The flat-input contract passes
    ``None`` through for those keys, and a handler that accepts None must keep
    receiving it: validating an optional key as required changed the route's
    behaviour (S17 caught it: ``cec is required for this route``).
    """
    value = inputs.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be a JSON number, got {type(value).__name__}")
    return float(value)


def _route_optional_str(inputs: dict[str, Any], key: str) -> str | None:
    """A gateway route's OPTIONAL string input (see :func:`_route_optional_float`)."""
    value = inputs.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string, got {type(value).__name__}")
    return value


def _route_str(inputs: dict[str, Any], key: str) -> str:
    """A gateway route's string input, validated at the boundary.

    Same contract as :func:`_route_float`: the declared value passes through,
    and anything else raises the ``TypeError`` the handler would have raised.
    """
    value = inputs.get(key)
    if value is None:
        raise TypeError(f"{key} is required for this route")
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string, got {type(value).__name__}")
    return value


def _normalize_inputs(
    request: GatewayRequest, model: ModelSpec
) -> tuple[dict[str, Any], list[ValidationResult]]:
    """Normalize input units to SI.

Scalar numeric inputs are multiplied by ``si_equivalent``.
Non-scalar inputs (strings, lists, dicts, ``None``, booleans)
pass through untouched: multiplicative unit scaling is only
defined for scalars, and many models carry enum labels or
structured payloads. Non-finite scalars are rejected â€” silently
propagating NaN/inf would poison every downstream computation."""
    normalized: dict[str, Any] = {}
    validations: list[ValidationResult] = []

    for name, value in request.inputs.items():
        unit_spec = request.input_units.get(name, UnitSpec(unit="unknown"))
        vr = ValidationResult(is_valid=True)

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            normalized[name] = value
        else:
            normalized[name] = scale_scalar_to_si(name, value, unit_spec)
        normalized[f"{name}_unit"] = unit_spec.unit

        validations.append(vr)

    return normalized, validations


__all__ = ["REQUIRED_INPUTS"]
