"""Model dispatch machinery for the Engine Gateway (A-1 step 3).

The route table (`_ROUTES_FOR_REGISTERED_IDS`), the `model_id` route
functions, the registered-id route targets (`_ROUTE_TARGETS`) and every
dispatch-only helper are extracted here from `engine/gateway/__init__.py`.
Each branch of the former `EngineGateway._dispatch_by_type` is one `_route_*`
function, so the routing comparisons the model registry wiring audit statically
scans (`engine/models/registry.py::_gateway_dispatch_literals` reads
`engine/gateway/__init__.py`) can stay there while the computation lives here.

`_execute` is the verbatim execution pipeline; it and its helpers take the
gateway as `self`. Every computation is reproduced verbatim; only the module
boundary moved, so behaviour and the public surface are byte-identical.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from engine.gateway.contracts import (
    ExecutionMetadata,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ModelSpec,
    ProvenanceSpec,
    UncertaintySpec,
    UnitSpec,
    ValidationResult,
)
from engine.gateway.input_validator import (
    _missing_required_inputs,
    _route_array_or_float,
    _route_float,
    _route_int,
    _route_optional_float,
    _route_optional_str,
    _route_str,
)


def _as_plain_dict(obj: Any) -> Any:
    """Best-effort conversion of a dataclass/object to a plain dict.

    Keeps gateway results JSON-serializable regardless of whether the
    underlying implementation returns dataclasses (e.g. QAReport,
    Recommendation) or plain dicts.
    """
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return obj


def _plain(obj: Any, _depth: int = 0) -> Any:
    """Recursive JSON-friendly conversion for pydantic models and dataclasses.

    ``_as_plain_dict`` handles the top level; this walks nested results so a
    ``ChainResult`` carrying a ``ScenarioParams`` and ``SignalFeatures`` still
    serializes end to end. Enums collapse to their value and the depth cap
    keeps a pathological cycle from breaking the gateway call.
    """
    from enum import Enum

    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Enum):
        return obj.value if isinstance(obj.value, (bool, int, float, str)) else obj.name
    if _depth > 8:
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): _plain(v, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_plain(v, _depth + 1) for v in obj]
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        return _plain(dump(), _depth + 1)
    plain = _as_plain_dict(obj)
    if plain is not obj:
        return _plain(plain, _depth + 1)
    return str(obj)


#: Intervention presets for the simulation chain's ``ScenarioParams`` when the
#: route is called with a scenario *name* rather than an explicit parameter
#: set. Documented gateway convention, not a scientific model.
_CHAIN_SCENARIO_PRESETS: dict[str, dict[str, float]] = {
    "Baseline": {"cn_change": 0.0, "c_factor_factor": 1.0, "p_factor": 1.0},
    "Medium": {"cn_change": -5.0, "c_factor_factor": 0.7, "p_factor": 0.8},
    "Intensive": {"cn_change": -10.0, "c_factor_factor": 0.5, "p_factor": 0.7},
}


def _build_chain_inputs(inputs: dict[str, Any]) -> Any:
    """Build a ``ChainInputs`` model from a flat gateway input mapping.

    The orchestrator's contract is a pydantic ``ChainInputs`` object; the
    gateway's contract is a JSON-friendly mapping. Missing fields surface as
    the pydantic validation error, which names every missing field.
    """
    from engine.hydroma.simulation.contracts import ScenarioParams
    from engine.hydroma.simulation.orchestrator import ChainInputs

    payload = dict(inputs)
    scenario = payload.get("scenario")
    if isinstance(scenario, str):
        if scenario not in _CHAIN_SCENARIO_PRESETS:
            raise ValueError(
                f"unknown chain scenario {scenario!r}; expected one of "
                f"{sorted(_CHAIN_SCENARIO_PRESETS)} or an explicit parameter dict"
            )
        scenario = dict(name=scenario, **_CHAIN_SCENARIO_PRESETS[scenario])
    if isinstance(scenario, dict):
        payload["scenario"] = ScenarioParams(**scenario)
    return ChainInputs(**payload)


#: Project-internal import roots. A failed import of one of these is a
#: missing implementation, not a missing third-party dependency.
_INTERNAL_IMPORT_ROOTS = ("engine", "services", "database")


def _watershed_geometry(inputs: dict[str, Any]) -> tuple[float, float]:
    """Resolve ``(area_m2, slope_pct)`` from a gateway input mapping.

    The three watershed design functions take the catchment area in m2 and
    the gully slope in percent. The routes used to forward
    ``drainage_area_ha`` into the slope-percent slot and ``peak_flow`` into
    the area slot, so a real-looking request designed a dam for a 1.5 m2
    catchment on a 50 % slope without failing (S17 review R-6). Areas are
    accepted in m2 or hectares; slopes in percent or as a fraction.
    """
    area = None
    for key in ("area_m2", "drainage_area_m2"):
        if inputs.get(key) is not None:
            area = float(inputs[key])
            break
    if area is None:
        for key in ("drainage_area_ha", "area_ha", "area_hectares"):
            if inputs.get(key) is not None:
                area = float(inputs[key]) * 10_000.0
                break
    slope_pct = None
    for key in ("slope_pct", "slope_percent"):
        if inputs.get(key) is not None:
            slope_pct = float(inputs[key])
            break
    if slope_pct is None and inputs.get("slope") is not None:
        slope_pct = float(inputs["slope"]) * 100.0
    return (area if area is not None else 0.0), (slope_pct if slope_pct is not None else 0.0)


def _import_failure_message(model_id: str, error: ImportError) -> str:
    """Classify an ImportError raised while dispatching ``model_id``.

    An unavailable third-party package is an availability problem and keeps
    the "install" guidance. A missing internal symbol or module is an
    unimplemented route and must say so: telling the operator to install a
    package for a name this engine never had is the misleading answer S17
    (T-02) replaced.
    """
    missing = getattr(error, "name", "") or ""
    internal = missing.startswith(_INTERNAL_IMPORT_ROOTS)
    symbol_missing = "cannot import name" in str(error)
    if internal or symbol_missing:
        return (
            f"Model {model_id} is not implemented in this engine: {error}. "
            f"The dispatch target this route names is missing from its "
            f"implementation module, so no package installation can enable it."
        )
    return (
        f"Model {model_id} requires dependencies that are not available: {error}. "
        f"Install required packages to enable this model."
    )


#: The implementation each routed id reaches, as ``path::symbol``. This map
#: names the computation, not the wrapper that calls it. It is what the
#: registry's status fields quote (``engine/models/registry.py::
#: _overlay_gateway_wiring``), so a reader of a registered id can see where
#: it actually runs rather than which gateway line sorted the request.
_ROUTE_TARGETS: dict[str, str] = {
    "CANON-007": (
        "engine/cpp_core/src/erosion.cpp::ls_factor "
        "(engine.hydroma.cpp_bridge.ls_factor; rusle_annual_soil_loss "
        "when the request states the RUSLE factor set)"
    ),
    "RUSLE_LS": (
        "engine/cpp_core/src/erosion.cpp::ls_factor "
        "(engine.hydroma.cpp_bridge.ls_factor)"
    ),
    "CANON-008": "engine/land/hydrology.py::flow_direction + flow_accumulation",
    "CANON-009": "engine/land/terrain_analysis.py::TerrainAnalyzer.analyze",
    "CANON-010": "engine/hydroma/groundwater/models.py::run_groundwater_bucket",
    "CANON-011": (
        "engine/cpp_core/src/climate.cpp::extraterrestrial_radiation + "
        "fao56_net_radiation (engine.hydroma.cpp_bridge)"
    ),
    "CANON-012": "engine/hydroma/formulas/registry.py::summary + all_records",
    "CANON-013": "engine/hydroma/provenance.py::ResultProvenance",
    "CANON-014": "engine/models/registry.py::ModelRegistry.status_summary",
    "CANON-018": (
        "engine/hydroma/scenarios/climate_scenarios.py::"
        "get_climate_projection + apply_climate_change"
    ),
    "CANON-019": (
        "engine/hydroma/data_pipeline STAC search via the planetary_computer "
        "connector, collection gpm-imerg-hhr"
    ),
    "CANON-020": (
        "engine/hydroma/data_pipeline STAC search via the planetary_computer "
        "connector, collection modis-16A3GF-061"
    ),
    "CANON-021": (
        "engine/hydroma/data_pipeline STAC search via the planetary_computer "
        "connector, collection landsat-c2-l2"
    ),
    "CANON-022": (
        "engine/hydroma/data_pipeline STAC search via the planetary_computer "
        "connector, collection sentinel-2-l2a; the cdse_sentinel connector "
        "downloads the pixels and names the credentials it needs"
    ),
}


def _alias(inputs: dict[str, Any], *names: str) -> Any:
    """First present, non-None value among ``names`` in ``inputs``.

    An alias the request does not carry stays absent. Substituting a default
    for it is what lets a request look answerable when the data needed to
    answer it was never supplied, so the routes below resolve through this
    helper and then report what is missing.
    """
    for name in names:
        value = inputs.get(name)
        if value is not None:
            return value
    return None


def _alias_float(inputs: dict[str, Any], *names: str) -> float | None:
    """``_alias`` coerced to ``float``, or ``None`` when it is not supplied."""
    value = _alias(inputs, *names)
    return None if value is None else float(value)


def _alias_int(inputs: dict[str, Any], *names: str) -> int | None:
    """``_alias`` coerced to ``int``, or ``None`` when it is not supplied."""
    value = _alias(inputs, *names)
    return None if value is None else int(value)


def _enum_value(value: Any) -> Any:
    """An enum member's ``value``, or the value itself when it is not an enum."""
    return getattr(value, "value", value)


def _dem_array(inputs: dict[str, Any], model_id: str) -> Any:
    """The request's DEM as a 2-D array of finite float elevations in metres.

    A DEM route needs the raster itself. The gateway's contract carries it as
    a nested list, and there is no scalar value to fall back to when it is
    missing: a synthesised DEM would derive slope, aspect and flow directions
    from terrain the caller never described.
    """
    import numpy as np

    dem = _alias(inputs, "dem", "dem_array", "dem_m")
    if dem is None:
        raise ValueError(
            f"{model_id} needs the digital elevation model as a 2-D array of "
            f"metres: supply 'dem' as a list of equal-length rows of "
            f"elevations. No synthetic DEM is substituted for a missing one."
        )
    array = np.asarray(dem, dtype=float)
    if array.ndim != 2:
        raise ValueError(
            f"{model_id} needs a 2-D DEM (a list of rows); the request "
            f"supplied a {array.ndim}-D array."
        )
    if array.shape[0] < 3 or array.shape[1] < 3:
        raise ValueError(
            f"{model_id} needs at least a 3x3 DEM so a full 3x3 neighbourhood "
            f"exists; the request supplied {array.shape[0]}x{array.shape[1]}."
        )
    if not np.isfinite(array).all():
        raise ValueError(
            f"{model_id} needs a DEM of finite elevations; the request "
            f"supplied a cell that is NaN or infinite, and a gradient across "
            f"it is not a gradient."
        )
    return array


def _native_core(module_name: str, symbols: tuple[str, ...]) -> Any:
    """The compiled ``hydroma_core`` module, or a named refusal.

    Several registered ids are wired to C++ kernels whose Python fallbacks
    are deliberately ``NotImplementedError`` (``engine/hydroma/cpp_bridge``):
    the engine refuses rather than return a number nobody has shown agrees
    with the kernel. This helper states which kernel and where it lives, so a
    host without the extension gets an actionable message instead of a bare
    "not implemented".
    """
    from engine.hydroma.cpp_bridge import get_module

    native = get_module()
    if native is None or not all(hasattr(native, name) for name in symbols):
        raise NotImplementedError(
            f"{module_name} requires the compiled hydroma_core extension "
            f"(engine/cpp_core::{symbols[0]} and its siblings), which is "
            f"unavailable on this host. The engine ships no Python fallback "
            f"for these kernels: an unverified twin is not a substitute."
        )
    return native


def _extract_output_units(raw_result: dict[str, Any]) -> dict[str, UnitSpec]:
    """Extract UnitSpec from a model's raw result dict.

    Looks for common unit keys: 'unit', 'units', 'output_units', or nested
    dicts with 'unit' keys. Returns a dict mapping output key -> UnitSpec.
    """
    units: dict[str, UnitSpec] = {}

    # Direct unit keys
    if isinstance(raw_result, dict):
        for key in ("unit", "units"):
            if key in raw_result and raw_result[key]:
                val = raw_result[key]
                if isinstance(val, str):
                    units[key] = UnitSpec(unit=val)
                elif isinstance(val, dict):
                    for k, v in val.items():
                        if isinstance(v, str):
                            units[k] = UnitSpec(unit=v)

        # Look for 'unit' or 'units' in nested dicts
        for k, v in raw_result.items():
            if isinstance(v, dict) and ("unit" in v or "units" in v):
                unit_val = v.get("unit") or v.get("units")
                if isinstance(unit_val, str):
                    units[k] = UnitSpec(unit=unit_val)

    return units


def _route_canon_007_rusle_ls(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-007 / RUSLE_LS â€” the RUSLE topographic factor.

    Wired to the native kernel ``engine/cpp_core/src/erosion.cpp::ls_factor``
    (reached through ``engine.hydroma.cpp_bridge.ls_factor``), the engine twin
    of the ``rusle.ls`` formula contract: steepness ``S`` per McCool et al.
    (1987) for slopes of 9% and over (with the low-slope form below that),
    slope-length exponent ``m`` from the RUSLE handbook, and ``L = (خ»/22.13)^m``.
    The same native module supplies ``soil_erodibility_k`` (the USDA texture
    table), ``estimate_rainfall_erosivity`` (Renard & Freimund 1994) and
    ``rusle_annual_soil_loss`` when the request states the full factor set.

    The slope length is never defaulted. It is a measured catchment property,
    and a made-up length would put a fabricated L inside the product; a
    request that supplies the factor set but not the length is told so.
    """
    slope_percent = _alias_float(inputs, "slope_percent", "slope_pct", "slope")
    slope_length_m = _alias_float(inputs, "slope_length_m", "slope_length")
    if slope_length_m is None:
        raise ValueError(
            "CANON-007 needs the RUSLE slope length in metres: supply "
            "'slope_length_m' (or 'slope_length'). The length factor is "
            "L = (خ»/22.13)^m over the measured length خ», and no default "
            "length is substituted for it."
        )
    if slope_percent is None:
        raise ValueError(
            "CANON-007 needs the slope gradient in percent: supply "
            "'slope_percent' (or 'slope_pct')."
        )
    if slope_length_m <= 0.0:
        raise ValueError(
            f"CANON-007 needs a positive slope length in metres; the request "
            f"supplied {slope_length_m} m. A zero or negative length has no "
            f"length factor."
        )
    if slope_percent < 0.0:
        raise ValueError(
            f"CANON-007 needs a non-negative slope gradient in percent; the "
            f"request supplied {slope_percent}%. Downslope water stores energy "
            f"regardless of direction, and a negative gradient is not one."
        )

    native = _native_core("CANON-007", ("ls_factor", "rusle_annual_soil_loss"))
    ls_factor = float(native.ls_factor(slope_length_m, slope_percent))
    result: dict[str, Any] = {
        "ls_factor": ls_factor,
        "ls_factor_inputs": {"slope_length_m": slope_length_m, "slope_percent": slope_percent},
    }

    r_factor = _alias_float(inputs, "r_factor", "rainfall_erosivity")
    annual_rainfall_mm = _alias_float(
        inputs, "annual_rainfall_mm", "rainfall_mm", "rainfall"
    )
    k_factor = _alias_float(inputs, "k_factor", "soil_erodibility_k")
    texture = _alias(inputs, "texture", "soil_type")
    c_factor = _alias_float(inputs, "c_factor", "ground_cover", "cover_management")
    p_factor = _alias_float(inputs, "p_factor", "support_practice")
    factor_set = (r_factor, annual_rainfall_mm, k_factor, texture, c_factor, p_factor)
    if any(value is not None for value in factor_set):
        r_value: float | None
        if r_factor is None and annual_rainfall_mm is not None:
            r_value = float(native.estimate_rainfall_erosivity(annual_rainfall_mm))
        else:
            r_value = r_factor
        k_value = k_factor
        if k_value is None and texture is not None:
            k_value = float(native.soil_erodibility_k(str(texture)))
        missing = [
            name
            for name, value in (
                ("r_factor or annual_rainfall_mm", r_value),
                ("k_factor or texture", k_value),
                ("c_factor or ground_cover", c_factor),
                ("p_factor", p_factor),
            )
            if value is None
        ]
        if missing:
            raise ValueError(
                "CANON-007 was asked for the annual soil loss A = Rآ·Kآ·LSآ·Cآ·P "
                f"but the request does not state {missing}. A partial factor "
                f"set is not a smaller computation: it is a product with some "
                f"factors invented."
            )
        annual_soil_loss = float(
            native.rusle_annual_soil_loss(r_value, k_value, ls_factor, c_factor, p_factor)
        )
        result["annual_soil_loss_t_ha_yr"] = annual_soil_loss
        result["rusle_factor_set"] = {
            "r": r_value,
            "k": k_value,
            "ls": ls_factor,
            "c": c_factor,
            "p": p_factor,
        }
    result["data_source"] = "modelled"
    result["units"] = "dimensionless"
    return result


def _route_canon_008_d8_flow(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-008 â€” D8 flow direction and flow accumulation.

    Wired to ``engine/land/hydrology.py::flow_direction`` and
    ``flow_accumulation``: one code table (1=N through 8=NW clockwise) scanned
    in the same order that reads it, so a code and its offset cannot drift
    apart; distance by scan position; a topological accumulation by in-degree;
    and ``FlowCycleError`` instead of a silently truncated watershed. This is
    the implementation CANON-008's own card names.

    The hydroma candidate (``engine/hydroma/analyses/topography_analysis.py::
    _calculate_flow_direction``) was measured and rejected here. It computes a
    real steepest-descent gradient, but its offset table is the transpose of
    its labels (the entry labelled "0: N" carries the row/column offset of
    west) and ``_calculate_flow_accumulation`` reads its output through a
    third, different table -- so seven of the eight codes name the wrong
    neighbour and the accumulation moves each cell's water to a cell the
    direction did not name. That file's own honest labels for its slope
    placeholder, constant aspect and zero curvature are untouched, and this
    route does not route to it.

    The direction array is returned alongside the accumulation because a code
    a caller cannot look up is not evidence of anything.
    """
    from engine.land.hydrology import flow_accumulation, flow_direction

    dem = _dem_array(inputs, "CANON-008")
    cell_size = _alias_float(inputs, "cell_size", "cell_size_m", "resolution")
    if _alias(inputs, "flat_resolution_strategy") is not None:
        raise ValueError(
            "CANON-008 does not implement flat resolution and does not pretend "
            "to: the wired D8 twin leaves a flat cell as direction 0 (a pit) "
            "and raises FlowCycleError on a cycle rather than guessing a flow "
            "through flat space. Resolve flats before the request reaches the "
            "gateway, or omit 'flat_resolution_strategy'."
        )
    codes = flow_direction(dem)
    accumulation = flow_accumulation(codes, dem)
    return {
        "flow_direction": [[int(value) for value in row] for row in codes],
        "flow_accumulation": [[float(value) for value in row] for row in accumulation],
        "flow_direction_codes": (
            "1=N 2=NE 3=E 4=SE 5=S 6=SW 7=W 8=NW (clockwise); "
            "0 marks a pit or a border cell with no full 3x3 neighbourhood"
        ),
        "accumulation_units": "upstream cell count",
        "cell_size_m": cell_size,
        "cell_size_note": (
            "Cell size does not enter the D8 codes or the cell-count "
            "accumulation; it is echoed for the caller's raster bookkeeping."
        ),
        "data_source": "modelled",
        "model": "engine.land.hydrology.flow_direction/flow_accumulation",
    }


def _route_canon_009_terrain(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-009 â€” DEM terrain derivatives: slope, aspect, curvature, TWI, TPI.

    Wired to ``engine/land/terrain_analysis.py::TerrainAnalyzer``: Horn's
    3x3 kernel for slope and aspect, a second-difference curvature, the
    slope-area ratio for TWI and a 3-cell ring for TPI, each classified
    against its own published table. This is the implementation CANON-009's
    own card names.

    The hydroma candidate (``engine/hydroma/analyses/topography_analysis.py::
    TopographyAnalyzer``) was measured and rejected: its slope is a constant
    1.0 placeholder, its aspect a constant 45 degrees, and its curvature
    zeros. Routing a request there would return invented derivatives under a
    Horn label, which is the failure mode that file's own docstring
    criticises. Its honest labels for those placeholders stay as they are.

    The returned figures are statistics over the DEM's valid cells. Horn's
    kernel needs a full 3x3 neighbourhood, so the border ring is NaN by
    construction; the underlying grid is not returned here, and the mean is
    taken over the cells that have one.
    """
    from engine.land.terrain_analysis import TerrainAnalyzer

    dem = _dem_array(inputs, "CANON-009")
    resolution = _alias_float(inputs, "cell_size_m", "cell_size", "resolution")
    if resolution is None:
        raise ValueError(
            "CANON-009 needs the cell size in metres: supply 'cell_size_m' "
            "(or 'cell_size'/'resolution'). Slope in degrees is dz/dx over "
            "that spacing, so a default spacing would silently rescale every "
            "derivative the analysis returns."
        )
    if resolution <= 0.0:
        raise ValueError(
            f"CANON-009 needs a positive cell size in metres; the request "
            f"supplied {resolution} m."
        )
    profile_id = _alias(inputs, "profile_id")
    analysis = TerrainAnalyzer(resolution=resolution).analyze(
        dem, profile_id=str(profile_id) if profile_id is not None else None
    )
    curvature = analysis.curvature
    indices = analysis.indices
    if curvature is None or indices is None:
        # The pydantic result type marks both blocks optional even though the
        # analysis always fills them; an absent block is refused here rather
        # than surfacing as an AttributeError on the route's own attribute
        # access below.
        raise ValueError(
            "CANON-009's terrain analysis returned no curvature or index "
            "block, so no derivative is reported. The DEM produced no valid "
            "3x3 neighbourhoods for the analysis to average over."
        )
    return {
        "terrain_type": _enum_value(analysis.terrain_type),
        "slope_mean_deg": analysis.slope_mean,
        "slope_max_deg": analysis.slope_max,
        "slope_class_dominant": _enum_value(analysis.slope_class_dominant),
        "slope_mean_pct": (
            math.tan(math.radians(analysis.slope_mean)) * 100.0
        ),
        "aspect_dominant": analysis.aspect_dominant,
        "profile_curvature_1_m": curvature.profile_curvature,
        "plan_curvature_1_m": curvature.plan_curvature,
        "total_curvature_1_m": curvature.total_curvature,
        "convergence_index": curvature.convergence_index,
        "twi": indices.twi,
        "tpi": indices.tpi,
        "roughness_index": indices.roughness_index,
        "landform": _enum_value(indices.landform),
        "wetness_class": indices.wetness_class,
        "elevation_mean_m": analysis.elevation_mean,
        "elevation_min_m": analysis.elevation_min,
        "elevation_max_m": analysis.elevation_max,
        "cell_size_m": resolution,
        "data_source": analysis.data_source,
        "model": "engine.land.terrain_analysis.TerrainAnalyzer.analyze",
    }


def _route_canon_010_water_balance(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-010 â€” the monthly water balance of the linear reservoir.

    Wired to ``engine/hydroma/groundwater/models.py::run_groundwater_bucket``,
    the implementation CANON-010's own card names: ``S(t+1) = S(t) + R - B -
    P`` with baseflow ``B = alphaآ·S(t)``, recharge from the stated
    ``recharge_mm`` or from ``soil_water_mm أ— rcoeff``, and pumping capped at
    what the reservoir can actually deliver so the unmet part is reported
    instead of silently creating water.

    Every parameter the bucket used is echoed in ``inputs_used``, defaults
    included, so the published series can be read against the request instead
    of against an assumed configuration. The mass-closing twin in this engine
    is ``engine/hydroma/water_balance.py::water_balance`` (``P = ET + Q + dS``
    over a flux series); it takes a flux series where this one takes a
    reservoir configuration, and neither is substituted for the other.
    """
    from engine.hydroma.groundwater.models import (
        GroundwaterBucketInput,
        run_groundwater_bucket,
    )

    initial_storage_mm = _alias_float(
        inputs, "initial_storage_mm", "storage0_mm", "storage_mm"
    )
    months = _alias_int(inputs, "months", "time_steps", "n_periods")
    if initial_storage_mm is None:
        raise ValueError(
            "CANON-010 needs the initial storage in millimetres: supply "
            "'initial_storage_mm' (or 'storage0_mm'). A reservoir that starts "
            "at an assumed full store is a configuration, not a computation."
        )
    if months is None:
        raise ValueError(
            "CANON-010 needs the number of periods: supply 'months' (or "
            "'time_steps'). The run has to know where it ends."
        )
    if initial_storage_mm < 0.0:
        raise ValueError(
            f"CANON-010 needs a non-negative initial storage in millimetres; "
            f"the request supplied {initial_storage_mm} mm."
        )
    if months <= 0:
        raise ValueError(
            f"CANON-010 needs a positive number of periods; the request "
            f"supplied {months}."
        )
    recharge_mm = _alias_float(inputs, "recharge_mm", "net_inflow_mm")
    soil_water_mm = _alias_float(inputs, "soil_water_mm", "soil_water")
    rcoeff = _alias_float(inputs, "rcoeff", "recharge_coefficient")
    if recharge_mm is None and (soil_water_mm is None or rcoeff is None):
        raise ValueError(
            "CANON-010 needs a recharge source: state 'recharge_mm' for the "
            "monthly recharge, or 'soil_water_mm' together with 'rcoeff' "
            "(recharge = soil_water_mm أ— rcoeff). An aquifer with no stated "
            "inflow cannot have its storage followed, and borrowing one from "
            "the module default would answer a question nobody asked."
        )
    alpha = _alias_float(inputs, "alpha", "recession_coefficient", "baseflow_coefficient")
    pumping_mm = _alias_float(inputs, "pumping_mm", "extraction_mm")
    bucket_input = GroundwaterBucketInput(
        initial_storage_mm=initial_storage_mm,
        recharge_mm=recharge_mm,
        pumping_mm=pumping_mm if pumping_mm is not None else 0.0,
        alpha=alpha if alpha is not None else 0.03,
        rcoeff=rcoeff if rcoeff is not None else 0.15,
        soil_water_mm=soil_water_mm if soil_water_mm is not None else 150.0,
        months=months,
    )
    output = run_groundwater_bucket(bucket_input)
    return {
        "storage_series_mm": list(output.storage_series_mm),
        "baseflow_series_mm": list(output.baseflow_series_mm),
        "recharge_series_mm": list(output.recharge_series_mm),
        "pumping_series_mm": list(output.pumping_series_mm),
        "unmet_pumping_series_mm": list(output.unmet_pumping_series_mm),
        "final_storage_mm": output.final_storage_mm,
        "total_baseflow_mm": output.total_baseflow_mm,
        "total_recharge_mm": output.total_recharge_mm,
        "total_pumping_mm": output.total_pumping_mm,
        "total_unmet_pumping_mm": output.total_unmet_pumping_mm,
        "inputs_used": {
            "initial_storage_mm": bucket_input.initial_storage_mm,
            "recharge_mm": bucket_input.recharge_mm,
            "pumping_mm": bucket_input.pumping_mm,
            "alpha": bucket_input.alpha,
            "rcoeff": bucket_input.rcoeff,
            "soil_water_mm": bucket_input.soil_water_mm,
            "months": bucket_input.months,
        },
        "units": "mm",
        "data_source": output.data_source,
        "model": "engine.hydroma.groundwater.models.run_groundwater_bucket",
    }


def _route_canon_011_solar(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-011 â€” extraterrestrial radiation, and FAO-56 net radiation.

    Wired to the native climate kernels at ``engine/cpp_core/src/climate.cpp``:
    ``extraterrestrial_radiation`` (FAO-56 eq. 21, the same quantity the
    ``CANON-011_RAD`` route reaches through its Python twin in
    ``engine/hydroma/climate/et_calculator.py``) and ``fao56_net_radiation``
    (FAO-56 eq. 38) when the request states the net-radiation inputs.

    The two backends are not assumed to agree: ``engine/tests/
    test_unwired_model_wiring.py`` asserts this route's Ra against the
    CANON-011_RAD Python twin and against a by-hand eq. 21 integration, which
    is what makes a single value reportable at all.

    Net radiation is computed only when the request names its drivers. A
    partly-stated request gets an error naming the missing terms instead of a
    closed-sky assumption nobody made.
    """
    latitude = _alias_float(inputs, "latitude", "lat")
    doy = _alias_int(inputs, "doy", "day_of_year")
    if latitude is None:
        raise ValueError(
            "CANON-011 needs the latitude in degrees: supply 'latitude' (or "
            "'lat'). Extraterrestrial radiation is a declination integral over "
            "the day, and without a latitude there is no day to integrate."
        )
    if doy is None:
        raise ValueError(
            "CANON-011 needs the day of year: supply 'doy' (or "
            "'day_of_year'). Without it the solar declination is undefined."
        )
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(
            f"CANON-011 needs a latitude between -90 and 90 degrees; the "
            f"request supplied {latitude}."
        )
    if not 1 <= doy <= 366:
        raise ValueError(
            f"CANON-011 needs a day of year between 1 and 366; the request "
            f"supplied {doy}."
        )

    native = _native_core("CANON-011", ("extraterrestrial_radiation", "fao56_net_radiation"))
    ra = float(native.extraterrestrial_radiation(latitude, doy))
    result: dict[str, Any] = {
        "ra_mj_m2_day": ra,
        "method": "engine/cpp_core/src/climate.cpp::extraterrestrial_radiation",
        "units": "MJ/m2/day",
    }

    t_min = _alias_float(inputs, "temp_min", "tmin")
    t_max = _alias_float(inputs, "temp_max", "tmax")
    rh_mean = _alias_float(inputs, "rh_mean", "rh", "relative_humidity")
    solar_radiation = _alias_float(
        inputs, "solar_radiation", "rs_mj_m2_day", "incoming_solar_radiation"
    )
    elevation_m = _alias_float(inputs, "elevation", "elevation_m")
    net_requested = (t_min, t_max, rh_mean, solar_radiation, elevation_m)
    if any(value is not None for value in net_requested):
        missing = [
            name
            for name, value in (
                ("temp_min", t_min),
                ("temp_max", t_max),
                ("rh_mean", rh_mean),
                ("solar_radiation", solar_radiation),
                ("elevation", elevation_m),
            )
            if value is None
        ]
        if missing:
            raise ValueError(
                "CANON-011 was asked for the FAO-56 net radiation but the "
                f"request does not state {missing}. Net radiation needs every "
                f"term: the long-wave exchange depends on the humidity, the "
                f"air temperatures and the site elevation together, and a "
                f"substituted one would be an assumption presented as a "
                f"measurement."
            )
        result["rn_mj_m2_day"] = float(
            native.fao56_net_radiation(
                t_min, t_max, rh_mean, solar_radiation, elevation_m, latitude, doy
            )
        )
        result["method"] = (
            "engine/cpp_core/src/climate.cpp::extraterrestrial_radiation + "
            "fao56_net_radiation"
        )
    return result


def _route_canon_012_formula_catalog(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-012 â€” the formula catalog, read-only.

    Wired to the registry the engine's own request-path formulas are read
    from: ``engine/hydroma/formulas/registry.py::summary``,
    ``all_records``, ``on_request_path`` and ``unservable_on_request_path``,
    re-exported by ``engine.hydroma.formulas``. The route reads that registry
    and registers, replaces and changes nothing.

    The invariant this route exists to expose is the catalog's servability
    rule: a formula whose backends disagree (``status == "divergent"``) may
    not be served on a request path, and ``unservable_on_request_path`` names
    the quantities that break it. Today that list is empty; the route reports
    the count it was derived from rather than asserting an emptiness nobody
    re-checked.

    The request states which read it wants: ``quantity`` for one record, or
    ``view: "summary"`` for the whole catalog. The gateway rejects an empty
    input mapping, so a read that needs nothing to state still has to state
    the read -- and the view is validated rather than ignored.
    """
    from engine.hydroma.formulas import all_records, on_request_path
    from engine.hydroma.formulas import get as formula_get
    from engine.hydroma.formulas import summary as formula_summary
    from engine.hydroma.formulas.registry import (
        REQUEST_PATH_FORMULAS,
        unservable_on_request_path,
    )

    quantity = _alias(inputs, "quantity")
    view = _alias(inputs, "view", "action")
    if view is not None and str(view) != "summary":
        raise ValueError(
            f"CANON-012 has no view {view!r}: the catalog is read-only through "
            f"the gateway, and the only read it offers is \"summary\". Use "
            f"'quantity' to read one record instead."
        )
    if quantity is not None:
        record = formula_get(str(quantity))
        if record is None:
            raise ValueError(
                f"CANON-012 has no formula record for quantity {quantity!r}. "
                f"The catalog is read-only through the gateway: a quantity "
                f"that is not registered cannot be looked up, and inventing "
                f"one would put an unverified formula on the request path."
            )
        return {
            "quantity": record.quantity,
            "canonical": record.canonical,
            "literature_ref": record.literature_ref,
            "units": record.units,
            "status": record.status,
            "verified": bool(getattr(record, "is_verified", False)),
            "on_request_path": bool(on_request_path(record.quantity)),
            "provenance": _enum_value(record.provenance),
            "stub_reason": record.stub_reason,
            "data_source": "registry",
            "model": "Formula Catalog v1.0",
        }

    counts = dict(formula_summary())
    records = all_records()
    return {
        "formula_count": counts["total"],
        "verified": counts["verified"],
        "divergent": counts["divergent"],
        "stub": counts["stub"],
        "by_standard": counts["by_standard"],
        "by_novel": counts["by_novel"],
        "by_composite": counts["by_composite"],
        "request_path_quantities": sorted(REQUEST_PATH_FORMULAS),
        "unservable_on_request_path": sorted(unservable_on_request_path()),
        "quantities": sorted(records),
        "data_source": "registry",
        "model": "Formula Catalog v1.0",
    }


def _route_canon_013_provenance(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-013 â€” the provenance envelope a result must carry.

    Wired to ``engine/hydroma/provenance.py::ResultProvenance``, the pydantic
    mixin every engine result type must carry, and to its ``DataSource``
    vocabulary: ``measured``, ``modelled``, ``simulated``, ``unavailable``
    and ``degraded``. The route attaches the envelope to the request's stated
    ``values`` (or to the request itself, when no values are given) and
    returns the three fields the engine requires of every result.

    The route's use is the negative case. A value that cannot name its source
    is refused here rather than floating free of provenance, a source outside
    the vocabulary is refused rather than coerced, and ``computed=False``
    survives instead of being normalised to True -- that flag is what tells a
    consumer the result exists only to explain why a value is missing.
    """
    from engine.hydroma.provenance import DataSource, ResultProvenance

    model = _alias(inputs, "model", "model_id")
    data_source = _alias(inputs, "data_source", "source")
    computed = _alias(inputs, "computed", "engine_ran")
    if model is None:
        raise ValueError(
            "CANON-013 requires the model that produced the result: supply "
            "'model' (name and version where known). A provenance record "
            "without a producing model is attributable to nothing."
        )
    if data_source is None:
        raise ValueError(
            "CANON-013 requires the result's data_source: supply 'data_source' "
            "(one of measured, modelled, simulated, unavailable, degraded). "
            "ResultProvenance carries no default for it, because a default "
            "makes a field optional in practice and any of the twenty call "
            "sites could then omit it while returning a measured number."
        )
    envelope = ResultProvenance(
        # The request's own string is passed through unchanged: pydantic
        # still rejects a value outside the DataSource vocabulary at
        # construction, exactly as before this cast.
        data_source=cast(DataSource, str(data_source)),
        model=str(model),
        computed=True if computed is None else bool(computed),
    )
    values = _alias(inputs, "values")
    return {
        "data_source": envelope.data_source,
        "model": envelope.model,
        "computed": envelope.computed,
        "provenance": {
            "data_source": envelope.data_source,
            "model": envelope.model,
            "computed": envelope.computed,
        },
        "values": values if values is not None else {},
        "valid_data_sources": ["measured", "modelled", "simulated", "unavailable", "degraded"],
    }


def _route_canon_014_registry(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-014 â€” the model registry inventory, read-only.

    Wired to ``engine/models/registry.py`` itself: ``get_registry()`` and
    ``ModelRegistry.status_summary()``. The route exposes the same summary the
    cards are seeded from -- how many models are registered, how each status
    is distributed, and what the gateway's dispatch scan found -- together
    with the ids the scan could not route.

    The inventory describes the registry rather than computing over the
    request: the request selects nothing, so no request can make the count
    wrong. That is also why it is reported with ``computed: False`` -- the
    route reads a fact, it does not produce one.

    The request states which read it wants: ``view: "summary"`` for the whole
    inventory, or ``model_id`` for one registered model's status record.
    """
    from engine.models import get_registry

    registry = get_registry()
    payload = registry.status_summary()
    registry_block = payload["registry"]
    wiring = payload["gateway_wiring"]
    inventory: dict[str, Any] = {
        "model_count": registry_block["models"],
        "status_tracked": registry_block["status_tracked"],
        "with_card": registry_block["with_card"],
        "without_card": registry_block["without_card"],
        "domains": registry_block["domains"],
        "model_types": registry_block["model_types"],
        "status_counts": payload["status_counts"],
        "gateway_wiring": {
            "dispatch_literals": wiring["dispatch_literals"],
            "dispatch_prefixes": wiring["dispatch_prefixes"],
            "unwired": list(wiring["unwired"]),
            "unwired_count": wiring["unwired_count"],
            "wired_count": wiring["wired_count"],
        },
        "data_source": "registry",
        "model": "Model Registry v1.0",
    }
    view = _alias(inputs, "view", "action")
    if view is not None and str(view) != "summary":
        raise ValueError(
            f"CANON-014 has no view {view!r}: the registry is read-only through "
            f"the gateway, and the only read it offers is \"summary\". Use "
            f"'model_id' to read one registered model's status record instead."
        )
    model_id = _alias(inputs, "model_id")
    if model_id is not None:
        record = payload["models"].get(str(model_id))
        if record is None:
            raise ValueError(
                f"CANON-014 has no registered model {model_id!r}. The registry "
                f"reports the models it holds, and an id it does not hold "
                f"cannot be inventoried."
            )
        return {
            "model": record,
            "data_source": "registry",
            "model_summary": "engine.models.registry.ModelRegistry.status_summary",
        }
    return inventory


def _route_canon_018_climate_projection(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """CANON-018 â€” the SSP climate projection.

    Wired to ``engine/hydroma/scenarios/climate_scenarios.py::
    get_climate_projection`` with its ``apply_climate_change`` companion: the
    IPCC AR6 Table 4.2 multi-model means this engine carries for the
    Middle-East / Iran region, the nearest horizon held in that table, and
    the ET0 sensitivity ``delta_et0 = 2.5 أ— delta_temp`` that turns a
    temperature change into a water-demand change.

    The card is right that this is neither a measurement nor a reanalysis:
    the projections are the engine's own scenario table, and the route reports
    them as ``modelled``. The three baselines are required because a
    projection that has no baseline to apply itself to cannot report an
    outcome, and defaulting them (as the older CLIMATE_PROJECTION route does)
    would put a number on the caller's site that nobody stated.
    """
    from engine.hydroma.scenarios.climate_scenarios import (
        apply_climate_change,
        get_climate_projection,
    )

    scenario = _alias(inputs, "ssp", "scenario")
    horizon = _alias_int(inputs, "year", "time_horizon")
    baseline_temp = _alias_float(inputs, "baseline_temp", "baseline_temp_c")
    baseline_precip = _alias_float(inputs, "baseline_precip", "baseline_precip_mm")
    baseline_et0 = _alias_float(inputs, "baseline_et0", "baseline_et0_mm")
    if scenario is None:
        raise ValueError(
            "CANON-018 needs the SSP pathway: supply 'ssp' (one of SSP1-2.6, "
            "SSP2-4.5, SSP3-7.0, SSP5-8.5 -- the scenarios this engine holds "
            "a table for)."
        )
    if horizon is None:
        raise ValueError(
            "CANON-018 needs the target year: supply 'year'. The projection "
            "is the table entry nearest it, so an absent year has no nearest "
            "entry."
        )
    if baseline_temp is None or baseline_precip is None or baseline_et0 is None:
        missing = [
            name
            for name, value in (
                ("baseline_temp", baseline_temp),
                ("baseline_precip", baseline_precip),
                ("baseline_et0", baseline_et0),
            )
            if value is None
        ]
        raise ValueError(
            f"CANON-018 needs the site's baselines and the request does not "
            f"state {missing}. A delta applied to an invented baseline is an "
            f"invented outcome."
        )
    projection = get_climate_projection(
        str(scenario), horizon, baseline_temp, baseline_precip, baseline_et0
    )
    applied = apply_climate_change(
        baseline_temp, baseline_precip, baseline_et0, projection
    )
    return {
        "scenario": projection.scenario,
        "time_horizon": projection.time_horizon,
        "requested_year": horizon,
        "delta_temp_c": projection.delta_temp,
        "delta_precip_pct": projection.delta_precip,
        "delta_et0_pct": projection.delta_et0,
        "confidence": projection.confidence,
        "description": projection.description,
        "projected_temperature_c": applied["temperature"],
        "projected_precipitation_mm": applied["precipitation"],
        "projected_et0_mm": applied["et0"],
        "projected_water_balance_change_mm": applied["water_balance_change"],
        "data_source": projection.data_source,
        "model": projection.model,
    }


#: The four satellite product routes. Each names the connector that actually
#: serves the product and the collection that holds it, checked against the
#: live catalogs on 2026-10-10 (Planetary Computer exposes ``gpm-imerg-hhr``,
#: ``modis-16A3GF-061``, ``landsat-c2-l2`` and ``sentinel-2-l2a``). The route
#: returns the scene metadata the catalog really holds; nobody fabricates a
#: pixel, a reflectance or a precipitation rate on the way through.
_SATELLITE_PRODUCTS: dict[str, dict[str, str]] = {
    "CANON-019": {
        "product": "GPM IMERG half-hourly precipitation",
        "source": "planetary_computer",
        "collection": "gpm-imerg-hhr",
    },
    "CANON-020": {
        "product": "MODIS MOD16A3GF v061 annual evapotranspiration",
        "source": "planetary_computer",
        "collection": "modis-16A3GF-061",
    },
    "CANON-021": {
        "product": "Landsat Collection 2 Level-2 surface reflectance and temperature",
        "source": "planetary_computer",
        "collection": "landsat-c2-l2",
    },
    "CANON-022": {
        "product": "Sentinel-2 L2A surface reflectance",
        "source": "planetary_computer",
        "collection": "sentinel-2-l2a",
    },
}


def _satellite_route_factory(
    model_id: str,
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Build the gateway route for one satellite product id.

    The four routes share one body because they share one contract and one
    honesty rule: the request states an area and a date, the route searches
    the real connector for real scenes, and every way the search cannot
    deliver scenes -- no connector, no network, no credential, no item in the
    catalog -- ends in a named ``ConnectorUnavailable`` rather than an empty
    success. The route returns scene metadata (ids, datetimes, bounding
    boxes, asset hrefs, checksums); downloading pixels is the download
    connector's job, not this one's.
    """

    def _route(inputs: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        from engine.hydroma.data_pipeline import get_pipeline
        from engine.hydroma.data_pipeline.connectors import ConnectorUnavailable

        product = _SATELLITE_PRODUCTS[model_id]
        pipeline = get_pipeline()
        connectors = pipeline.connectors
        source_id = str(_alias(inputs, "source", "connector") or product["source"])
        if source_id not in connectors:
            raise ValueError(
                f"{model_id} ({product['product']}) has no connector "
                f"{source_id!r} in the data pipeline; available connectors: "
                f"{sorted(connectors)}. The product is served by whichever "
                f"connector actually holds it, and an unknown source is not a "
                f"silent fallback to one that does."
            )
        collections = _alias(inputs, "collections", "collection") or [product["collection"]]
        if isinstance(collections, str):
            collections = [collections]
        raw_bbox = _alias(inputs, "bbox", "bounds")
        if raw_bbox is None:
            raise ValueError(
                f"{model_id} needs the search area: supply 'bbox' as "
                f"[minx, miny, maxx, maxy] in degrees. A satellite route "
                f"searches an area, and an undefined area is not a smaller "
                f"search."
            )
        bbox = [float(value) for value in list(raw_bbox)]
        if len(bbox) != 4:
            raise ValueError(
                f"{model_id} needs 'bbox' as four numbers [minx, miny, maxx, "
                f"maxy]; the request supplied {len(bbox)}."
            )
        datetime_range = str(_alias(inputs, "datetime", "date", "date_range"))
        query: dict[str, Any] = {
            "bbox": bbox,
            "datetime": datetime_range,
            "collections": [str(value) for value in list(collections)],
            "limit": int(_alias(inputs, "limit") or 10),
        }
        try:
            assets = pipeline.fetch_data(source_id, query)
        except ConnectorUnavailable:
            # Already names the missing credential, endpoint or licence; the
            # connector's own message is the most specific one available.
            raise
        except PermissionError as exc:
            # The ZED 2.2j download gate refused the request: an external
            # fetch is disabled in this process.
            raise ConnectorUnavailable(
                f"{model_id} ({product['product']}) cannot reach its source: "
                f"{exc} The route may not reach the network in this process; "
                f"set the download gate to permit external fetches to enable "
                f"it."
            ) from exc
        except Exception as exc:
            connector_source = getattr(connectors[source_id], "source", None)
            endpoint = getattr(connector_source, "base_url", "unknown")
            raise ConnectorUnavailable(
                f"{model_id} ({product['product']}) could not reach the "
                f"{source_id!r} connector at {endpoint} while searching "
                f"collection(s) {query['collections']} over bbox {bbox} for "
                f"{datetime_range}: {type(exc).__name__}: {exc}. No satellite "
                f"value is reported without a catalog that actually answered."
            ) from exc
        if not assets:
            raise ConnectorUnavailable(
                f"{model_id} ({product['product']}) searched collection(s) "
                f"{query['collections']} over bbox {bbox} for {datetime_range} "
                f"through the {source_id!r} connector and the catalog returned "
                f"0 items. That is not a value: the product does not cover "
                f"this area and date set, and no precipitation, ET or "
                f"reflectance is derived from an empty scene list."
            )
        return {
            "product": product["product"],
            "scenes": [asset.to_dict() for asset in assets],
            "scene_count": len(assets),
            "searched": {
                "source": source_id,
                "collections": query["collections"],
                "bbox": bbox,
                "datetime": datetime_range,
                "limit": query["limit"],
            },
            "data_source": "measured",
            "model": product["product"],
        }

    return _route


#: Route for each registered id that used to end at the terminal
#: ``NotImplementedError``. Consulted by ``_dispatch_by_type`` as a table
#: lookup (``.get(model_id)``) so the per-id target above stays the one place
#: a reader can audit, and so the registry's dispatch-literal scan -- which
#: models ``==``/``startswith`` branches -- keeps a stable view of this file.
_ROUTES_FOR_REGISTERED_IDS: dict[
    str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
] = {
    "CANON-007": _route_canon_007_rusle_ls,
    "RUSLE_LS": _route_canon_007_rusle_ls,
    "CANON-008": _route_canon_008_d8_flow,
    "CANON-009": _route_canon_009_terrain,
    "CANON-010": _route_canon_010_water_balance,
    "CANON-011": _route_canon_011_solar,
    "CANON-012": _route_canon_012_formula_catalog,
    "CANON-013": _route_canon_013_provenance,
    "CANON-014": _route_canon_014_registry,
    "CANON-018": _route_canon_018_climate_projection,
    "CANON-019": _satellite_route_factory("CANON-019"),
    "CANON-020": _satellite_route_factory("CANON-020"),
    "CANON-021": _satellite_route_factory("CANON-021"),
    "CANON-022": _satellite_route_factory("CANON-022"),
}


def _route_et_pm_group(model_id, inputs, parameters, result):
    """Dispatch branch: model_id in ('CANON-001', 'CANON-002', 'CANON-003', 'CANON-011_RAD')."""
    from engine.hydroma.et import compute_et
    et_result = compute_et(model_id, inputs, parameters)
    result.update(et_result)
    result["units"] = "mm/day"
    return result


def _route_rothtc_temp_factor(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ROTHTC_TEMP_FACTOR'."""
    from engine.hydroma.simulation.runners.rothc_runner import (
        temp_factor as _temp_factor,
    )
    value: Any = float(
        _temp_factor(
            float(
                inputs.get("temperature", inputs.get("temperature_c", 0.0))
            )
        )
    )
    result["value"] = value
    result["units"] = "dimensionless"
    return result


def _route_canon_004(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CANON-004'."""
    from engine.hydroma.runoff import compute_runoff as _compute_runoff
    r: Any = _compute_runoff(inputs, parameters)
    result.update(r)
    result["units"] = "mm"
    return result


def _route_canon_005(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CANON-005'."""
    from engine.hydroma.theis import compute_theis as _compute_theis
    r = _compute_theis(inputs, parameters)
    result.update(r)
    result["units"] = "m"
    return result


def _route_canon_006(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CANON-006'."""
    from engine.hydroma.soil.physics import (
        van_genuchten_theta as _van_genuchten_theta,
    )
    alpha = inputs.get("vg_alpha", inputs.get("alpha"))
    n = inputs.get("vg_n", inputs.get("n"))
    r = _van_genuchten_theta(
        _route_float(inputs, "matric_potential"),
        _route_float(inputs, "theta_r"),
        _route_float(inputs, "theta_s"),
        _route_float({"vg_alpha": alpha}, "vg_alpha"),
        _route_float({"vg_n": n}, "vg_n"),
    )
    result.update({"van_genuchten_theta": r})
    result["units"] = "cm3/cm3"
    return result


def _route_canon_016(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CANON-016'."""
    # C++ climate kernel: FAO-56 Penman-Monteith through the compiled
    # extension's real binding. With rh_min == rh_max the native
    # single-RH convention reproduces the Python eq. 17 computation
    # exactly (S11); with rh_min != rh_max the two conventions differ
    # by the humidity treatment and the result stays within ~2 % of
    # CANON-001, which S11 pins.
    from engine.hydroma.cpp_bridge import get_module

    native = get_module()
    if native is None or not hasattr(native, "penman_monteith_et0"):
        raise NotImplementedError(
            "CANON-016 requires the compiled hydroma_core extension, "
            "which is unavailable on this host (no MSVC/cmake build). "
            "No Python fallback is wired for this kernel."
        )
    rh_min = inputs.get("rh_min", inputs.get("rh_mean", inputs.get("rh")))
    rh_max = inputs.get("rh_max", rh_min)
    rh_mean = (float(rh_min) + float(rh_max)) / 2.0
    et0 = native.penman_monteith_et0(
        float(inputs.get("temp_min", inputs.get("tmin", 0.0))),
        float(inputs.get("temp_max", inputs.get("tmax", 0.0))),
        rh_mean,
        float(inputs.get("wind_speed", 0.0)),
        float(inputs.get("solar_radiation", 0.0)),
        float(inputs.get("elevation", 0.0)),
        float(inputs.get("latitude", 0.0)),
        int(inputs.get("doy", 1)),
    )
    result["et0_mm_day"] = float(et0)
    result["method"] = "penman_monteith_cpp_kernel"
    result["units"] = "mm/day"
    return result


def _route_canon_017(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CANON-017'."""
    # C++ soil kernel: van Genuchten retention through the compiled
    # extension's real binding. The embedded Carsel & Parrish (1988)
    # parameter table is the same table the Python path reads, so the
    # two agree exactly (S17).
    from engine.hydroma.cpp_bridge import get_module

    native = get_module()
    if native is None or not hasattr(native, "soil_water_content"):
        raise NotImplementedError(
            "CANON-017 requires the compiled hydroma_core extension, "
            "which is unavailable on this host (no MSVC/cmake build). "
            "No Python fallback is wired for this kernel."
        )
    heads = inputs.get("pressure_head_cm", inputs.get("pressure_head"))
    if not heads:
        raise ValueError(
            "pressure_head_cm must be a non-empty list of matric heads [cm]"
        )
    texture = str(inputs.get("texture", inputs.get("texture_class", "loam")))
    theta = native.soil_water_content([float(h) for h in heads], texture)
    result["theta"] = [float(t) for t in theta]
    result["texture"] = texture
    result["units"] = "cm3/cm3"
    return result


def _route_soil_cec(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_CEC'."""
    from engine.hydroma.soil.chemistry import calculate_cec as _calculate_cec
    r = _calculate_cec(
        inputs.get("clay_pct", 0),
        inputs.get("organic_matter_pct", 0),
        inputs.get("ph", 7),
    )
    result.update(r if isinstance(r, dict) else {"cec": r})
    result["units"] = "cmol_c/kg"
    return result


def _route_soil_esp(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_ESP'."""
    from engine.hydroma.soil.chemistry import calculate_esp as _calculate_esp
    r = _calculate_esp(inputs.get("na", 0), inputs.get("cex", 0))
    result.update(r if isinstance(r, dict) else {"esp": r})
    result["units"] = "%"
    return result


def _route_soil_sar(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_SAR'."""
    from engine.hydroma.soil.chemistry import calculate_sar as _calculate_sar
    r = _calculate_sar(inputs.get("na", 0), inputs.get("ca", 0), inputs.get("mg", 0))
    result.update(r if isinstance(r, dict) else {"sar": r})
    return result


def _route_soil_health(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_HEALTH'."""
    from engine.hydroma.soil.health import (
        calculate_soil_health_index as _soil_health_index,
    )
    r = _soil_health_index(
        _route_float(inputs, "ph"),
        _route_float(inputs, "organic_matter"),
        _route_float(inputs, "nitrogen"),
        _route_float(inputs, "phosphorus"),
        _route_float(inputs, "potassium"),
        _route_optional_float(inputs, "cec"),
        _route_optional_str(inputs, "texture"),
    )
    result.update(r if isinstance(r, dict) else {"health_index": r})
    result["units"] = "index"
    return result


def _route_soil_awc(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_AWC'."""
    from engine.hydroma.soil.physics import (
        available_water_capacity as _available_water_capacity,
    )
    r = _available_water_capacity(_route_str(inputs, "texture_class"))
    result.update(r if isinstance(r, dict) else {"awc": r})
    result["units"] = "mm/m"
    return result


def _route_soil_water_content(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_WATER_CONTENT'."""
    from engine.hydroma.soil.physics import water_content_at as _water_content_at
    r = _water_content_at(
        _route_float(inputs, "matric_potential"),
        _route_str(inputs, "texture_class"),
    )
    result.update(r if isinstance(r, dict) else {"theta": r})
    return result


def _route_soil_leaching(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_LEACHING'."""
    from engine.hydroma.soil.salinity import (
        calculate_leaching_requirement as _leaching_requirement,
    )
    # Accept both the canonical (ec_soil, ec_water) names and
    # the legacy facade names (ec_drainage, ec_irrigation).
    ec_soil = inputs.get("ec_soil", inputs.get("ec_drainage"))
    ec_water = inputs.get("ec_water", inputs.get("ec_irrigation"))
    r = _leaching_requirement(ec_soil, ec_water, inputs.get("target_ec"))
    result.update(r if isinstance(r, dict) else {"lr": r})
    return result


def _route_soil_amendment(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_AMENDMENT'."""
    from engine.hydroma.soil.salinity import (
        calculate_sodic_soil_amendment as _sodic_amendment,
    )
    r = _sodic_amendment(
        _route_float(inputs, "esp"),
        _route_float(inputs, "soil_depth"),
        # Decision record (gap G-H20): the API contract declares this
        # parameter optional with default 1.4 g/cm3, and the kernel
        # documents it as "accepted and not used" (verified by AST: the
        # function reads no ``bulk_density`` name). So the declared
        # default is applied here instead of failing the request; every
        # published rate is unchanged (10000 kg/ha at 30 cm).
        _route_float(inputs, "bulk_density", 1.4),
    )
    result.update(r if isinstance(r, dict) else {"amendment": r})
    # The engine reports the requirement in kg/ha (gypsum_kg_per_ha);
    # labelling it t/ha here was a 1000x units error in the envelope
    # (S18 review).
    result["units"] = "kg/ha"
    return result


def _route_soil_salinity_classify(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_SALINITY_CLASSIFY'."""
    from engine.hydroma.soil.salinity import classify_salinity as _classify_salinity
    r = _classify_salinity(_route_float(inputs, "ec"))
    result.update(r if isinstance(r, dict) else {"salinity_class": r})
    return result


def _route_soil_taxonomy(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_TAXONOMY'."""
    from engine.hydroma.soil.taxonomy import (
        get_soil_taxonomy as _soil_taxonomy,
    )
    r = _soil_taxonomy(
        inputs.get("clay_pct", inputs.get("clay")),
        inputs.get("silt_pct", inputs.get("silt")),
        inputs.get("sand_pct", inputs.get("sand")),
        inputs.get(
            "organic_matter_pct", inputs.get("organic_matter")
        ),
        _route_float(inputs, "ph"),
        _route_optional_float(inputs, "cec"),
    )
    result.update(r if isinstance(r, dict) else {"taxonomy": r})
    return result


def _route_soil_texture(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_TEXTURE'."""
    from engine.hydroma.soil.texture import classify_texture as _classify_texture
    r = _classify_texture(
        inputs.get("sand_pct", 0),
        inputs.get("silt_pct", 0),
        inputs.get("clay_pct", 0),
    )
    result["texture_class"] = r if isinstance(r, str) else str(r)
    return result


def _route_soil_texture_coords(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_TEXTURE_COORDS'."""
    from engine.hydroma.soil.texture import (
        texture_triangle_coords as _texture_coords,
    )
    r = _texture_coords(
        _route_float(inputs, "sand_pct"),
        _route_float(inputs, "silt_pct"),
        _route_float(inputs, "clay_pct"),
    )
    result.update(r if isinstance(r, dict) else {"coords": r})
    return result


def _route_soil_water_retention(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_WATER_RETENTION'."""
    from engine.hydroma.soil.water_retention import (
        calculate_water_retention_curve as _retention_curve,
    )
    r = _retention_curve(
        _route_str(inputs, "texture_class"),
        inputs.get("pressure_range"),
    )
    result.update(r if isinstance(r, dict) else {"retention_curve": r})
    return result


def _route_soil_vg_parameters(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_VG_PARAMETERS'."""
    from engine.hydroma.soil.water_retention import (
        get_vg_parameters as _vg_parameters,
    )
    r = _vg_parameters(inputs.get("texture_class", ""))
    result.update(r if isinstance(r, dict) else {"vg_params": r})
    return result


def _route_soil_pedotransfer(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_PEDOTRANSFER'."""
    from engine.hydroma.soil.pedotransfer import (
        estimate_soil_parameters as _soil_parameters,
    )
    r = _soil_parameters(
        _route_float(inputs, "sand_pct"),
        _route_float(inputs, "clay_pct"),
        inputs.get(
            "om_pct", inputs.get("organic_matter_pct", 1.0)
        ),
    )
    result.update(r if isinstance(r, dict) else {"params": r})
    return result


def _route_carbon_seq(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CARBON_SEQ'."""
    from engine.hydroma.carbon.calculator import (
        CarbonProjectType,
    )
    from engine.hydroma.carbon.calculator import (
        calculate_carbon_sequestration as _carbon_sequestration,
    )
    project_type = inputs.get("project_type", "afforestation")
    if isinstance(project_type, str):
        project_type = CarbonProjectType(project_type)
    r = _carbon_sequestration(
        project_type,
        _route_float(inputs, "area_ha"),
        _route_int(inputs, "duration_years", default=10),
        _route_str(inputs, "region"),
    )
    result.update(r if isinstance(r, dict) else {"carbon_sequestered": r})
    result["units"] = "tC/ha"
    return result


def _route_econ_npv(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_NPV'."""
    from engine.hydroma.economics.analysis import calculate_npv as _calculate_npv
    r = _calculate_npv(inputs.get("cash_flows", []), inputs.get("discount_rate", 0.1))
    result.update(r if isinstance(r, dict) else {"npv": r})
    return result


def _route_econ_payback(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_PAYBACK'."""
    from engine.hydroma.economics.analysis import (
        calculate_payback as _calculate_payback,
    )
    cash_flows = inputs.get("cash_flows")
    if cash_flows is None:
        # Backward-compatible construction from the legacy
        # (initial_investment, annual_cash_flow) pair.
        initial = float(inputs.get("initial_investment", 0.0) or 0.0)
        annual = float(inputs.get("annual_cash_flow", 0.0) or 0.0)
        cash_flows = [-initial] + [annual] * 30
    r = _calculate_payback(cash_flows)
    result.update(r if isinstance(r, dict) else {"payback_years": r})
    return result


def _route_econ_ag_cost(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_AG_COST'."""
    from engine.hydroma.economics.costing import (
        calculate_agricultural_cost as _ag_cost,
    )
    costs = inputs.get("input_costs", {}) or {}
    if not isinstance(costs, dict):
        result.update({"total_cost_irr": 0.0, "error": "input_costs must be a dict"})
        return result
    r = _ag_cost(
        float(inputs.get("area_ha", 0.0)),
        str(inputs.get("crop_type", "")),
        float(costs.get("labor_hours_per_hectare", 0.0)),
        float(costs.get("labor_cost_per_hour", 0.0)),
        float(costs.get("seed_cost_per_hectare", 0.0)),
        float(costs.get("fertilizer_cost_per_hectare", 0.0)),
        float(costs.get("machinery_cost_per_hectare", 0.0)),
        float(costs.get("land_rent_per_hectare", 0.0)),
        float(costs.get("other_variable_costs_per_hectare", 0.0)),
    )
    result.update(r if isinstance(r, dict) else {"total_cost": r})
    return result


def _route_econ_ag_revenue(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_AG_REVENUE'."""
    from engine.hydroma.economics.revenue import (
        calculate_agricultural_revenue as _ag_revenue,
    )
    # The adapter's second parameter is a per-hectare yield; accept
    # either the per-hectare form, a season total for the area, or
    # a per-hectare alias (yield_tonnes_ha).
    if "yield_ton_per_ha" in inputs:
        yield_per_ha = float(inputs["yield_ton_per_ha"])
    elif "yield_tonnes_ha" in inputs:
        yield_per_ha = float(inputs["yield_tonnes_ha"])
    else:
        area_ha = float(inputs.get("area_ha", 0.0))
        yield_per_ha = (
            float(inputs.get("yield_tonnes", 0.0)) / area_ha
            if area_ha
            else 0.0
        )
    r = _ag_revenue(
        float(inputs.get("area_ha", 0.0)),
        yield_per_ha,
        float(inputs.get("price_per_tonne", 0.0)),
        float(inputs.get("quality_factor", 1.0)),
        float(inputs.get("market_access_factor", 1.0)),
    )
    result.update(r if isinstance(r, dict) else {"revenue": r})
    return result


def _route_econ_price_risk(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_PRICE_RISK'."""
    from engine.hydroma.economics.risk import (
        assess_market_price_risk as _price_risk,
    )
    r = _price_risk(
        float(inputs.get("base_price", 0.0)),
        float(inputs.get("volatility", 0.0)),
        int(inputs.get("time_horizon_years", 1)),
        float(inputs.get("confidence_level", 0.05)),
    )
    result.update(r if isinstance(r, dict) else {"risk": r})
    return result


def _route_econ_yield_risk(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_YIELD_RISK'."""
    from engine.hydroma.economics.risk import assess_yield_risk as _yield_risk
    r = _yield_risk(
        float(inputs.get("expected_yield", 0.0)),
        float(inputs.get("yield_std_dev", 0.0)),
        float(inputs.get("area_hectares", 0.0)),
        float(inputs.get("price_per_unit", 0.0)),
        float(inputs.get("confidence_level", 0.05)),
    )
    result.update(r if isinstance(r, dict) else {"risk": r})
    return result


def _route_econ_financial(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'ECON_FINANCIAL'."""
    from engine.hydroma.economics.roi import (
        calculate_financial_metrics as _financial_metrics,
    )
    cash_flows = inputs.get("cash_flows", []) or []
    r = _financial_metrics(
        float(inputs.get("initial_investment", 0.0)),
        [float(cf) for cf in cash_flows],
        float(inputs.get("discount_rate", 0.1)),
        int(inputs.get("project_lifetime_years", len(cash_flows))),
        float(inputs.get("salvage_value", inputs.get("terminal_value", 0.0))),
    )
    result.update(r if isinstance(r, dict) else {"metrics": r})
    return result


def _route_watershed_struct(model_id, inputs, parameters, result):
    """Dispatch branch: model_id in ('WATERSHED_STRUCT', 'CANON-015')."""
    from engine.hydroma.watershed.calculator import (
        design_watershed_structure as _design_structure,
    )
    structure_type = inputs.get("structure_type", "")
    area_m2, slope_pct = _watershed_geometry(inputs)
    r = _design_structure(
        str(structure_type), slope_pct, area_m2, float(inputs.get("rainfall_mm", 100.0))
    )
    result.update(r if isinstance(r, dict) else {"structure": r})
    return result


def _route_watershed_check_dam(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'WATERSHED_CHECK_DAM'."""
    from engine.hydroma.watershed.calculator import design_check_dam as _design_check_dam
    area_m2, slope_pct = _watershed_geometry(inputs)
    r = _design_check_dam(slope_pct, area_m2, float(inputs.get("rainfall_mm", 100.0)))
    result.update(r if isinstance(r, dict) else {"design": r})
    return result


def _route_watershed_contour_trench(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'WATERSHED_CONTOUR_TRENCH'."""
    from engine.hydroma.watershed.calculator import (
        design_contour_trench as _design_contour_trench,
    )
    area_m2, slope_pct = _watershed_geometry(inputs)
    r = _design_contour_trench(slope_pct, area_m2, float(inputs.get("rainfall_mm", 100.0)))
    result.update(r if isinstance(r, dict) else {"design": r})
    return result


def _route_watershed_half_moon(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'WATERSHED_HALF_MOON'."""
    from engine.hydroma.watershed.calculator import design_half_moon as _design_half_moon
    area_m2, slope_pct = _watershed_geometry(inputs)
    r = _design_half_moon(slope_pct, area_m2, float(inputs.get("rainfall_mm", 100.0)))
    result.update(r if isinstance(r, dict) else {"design": r})
    return result


def _route_plant_neuro(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'PLANT_NEURO'."""
    # The engine's real API is ``analyze_from_signals`` on a raw
    # electrical signal; there is no NDVI-series path in the
    # underlying engine, so the route exposes the signal path and
    # says so rather than inventing an NDVI detector.
    import numpy as _np

    from engine.hydroma.plant_neuro import PlantNeuroEngine

    signal = inputs.get("signal_mv", inputs.get("signal"))
    if not signal:
        raise ValueError(
            "signal_mv must be a non-empty list of electrical signal "
            "samples [mV] (the underlying engine analyses electrical "
            "signals, not NDVI time series)"
        )
    if len(signal) < 16:
        # The engine's feature extraction smooths with a Savitzky-
        # Golay filter of window 15, so a shorter vector fails deep
        # inside scipy; an honest message names the real minimum.
        raise ValueError(
            f"signal_mv has {len(signal)} samples; at least 16 are "
            "required for the engine's smoothing filter"
        )
    r = PlantNeuroEngine().analyze_from_signals(
        _np.asarray(signal, dtype=float)
    )
    result["neuro"] = _plain(r)
    return result


def _route_mrv_metrics(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'MRV_METRICS'."""
    # Composes the module's real functions; the module defines no
    # ``MRVMetrics`` class, which the route used to import.
    from engine.hydroma.mrv.metrics import rusle_annual_loss, soc_stock_tha

    metrics: dict[str, Any] = {}
    if inputs.get("soc_pct") is not None:
        metrics["soc_stock_tha"] = float(
            soc_stock_tha(
                float(inputs["soc_pct"]),
                float(inputs.get("depth_m", 0.3)),
                float(inputs.get("bulk_density_g_cm3", 1.3)),
            )
        )
    if None not in (
        inputs.get("rainfall_mm"),
        inputs.get("slope_length_m"),
        inputs.get("slope_percent"),
    ):
        metrics["rusle_annual_loss_tha"] = float(
            rusle_annual_loss(
                float(inputs["rainfall_mm"]),
                float(inputs["slope_length_m"]),
                float(inputs["slope_percent"]),
                float(inputs.get("c_factor", 0.5)),
                float(inputs.get("p_factor", 0.8)),
                str(inputs.get("texture", "loam")),
            )
        )
    if not metrics:
        raise ValueError(
            "MRV_METRICS requires 'soc_pct' and/or the trio "
            "'rainfall_mm', 'slope_length_m', 'slope_percent'"
        )
    result["mrv"] = metrics
    return result


def _route_mrv_dashboard(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'MRV_DASHBOARD'."""
    from engine.hydroma.mrv.metrics import compute_dashboard as _compute_dashboard
    r = _compute_dashboard(inputs.get("metrics_data", {}))
    result.update(r if isinstance(r, dict) else {"dashboard": r})
    return result


def _route_mrv_validate(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'MRV_VALIDATE'."""
    from engine.hydroma.mrv.qa import validate_reading as _validate_reading
    reading = inputs.get("reading")
    if isinstance(reading, dict):
        r = _validate_reading(
            _route_str(reading, "sensor_type"),
            _route_float(reading, "value"),
            _route_optional_str(reading, "unit"),
        )
    else:
        r = _validate_reading(
            _route_str(inputs, "sensor_type"),
            _route_float(inputs, "value"),
            _route_optional_str(inputs, "unit"),
        )
    r = _as_plain_dict(r)
    result.update(r if isinstance(r, dict) else {"valid": r})
    return result


def _route_mrv_validate_sat(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'MRV_VALIDATE_SAT'."""
    from engine.hydroma.mrv.qa import (
        validate_satellite_index as _validate_satellite_index,
    )
    index = inputs.get("index")
    value = inputs.get("value")
    if index is None and isinstance(inputs.get("index_data"), dict):
        entries = list(inputs["index_data"].items())
        if len(entries) == 1:
            index, value = entries[0]
    if index is None or value is None:
        raise ValueError(
            "MRV_VALIDATE_SAT requires 'index' and 'value', or a "
            "single-entry 'index_data' mapping"
        )
    r = _as_plain_dict(_validate_satellite_index(str(index), float(value)))
    result.update(r if isinstance(r, dict) else {"valid": r})
    return result


def _route_compost_cn(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'COMPOST_CN'."""
    from engine.hydroma.materials.compost_formulator import (
        CompostMaterial as _CompostMaterial,
    )
    from engine.hydroma.materials.compost_formulator import (
        calculate_mix_cn_ratio as _mix_cn_ratio,
    )
    raw_materials = inputs.get("materials", [])
    materials: list[Any] = []
    for item in raw_materials:
        if isinstance(item, _CompostMaterial):
            materials.append(item)
        elif isinstance(item, dict):
            materials.append(
                _CompostMaterial(
                    name=item.get("name", "material"),
                    mass_kg=item.get("mass_kg", item.get("mass", 1.0)),
                    carbon_content=item.get(
                        "carbon_content", item.get("carbon", 0.0)
                    ),
                    nitrogen_content=item.get(
                        "nitrogen_content", item.get("nitrogen", 0.0)
                    ),
                )
            )
        elif hasattr(item, "mass_kg"):
            materials.append(
                _CompostMaterial(
                    name=getattr(item, "name", "material"),
                    mass_kg=item.mass_kg,
                    carbon_content=getattr(item, "carbon_content", 0.0),
                    nitrogen_content=getattr(item, "nitrogen_content", 0.0),
                )
            )
        else:
            materials.append(item)
    r = _mix_cn_ratio(materials)
    result.update(r if isinstance(r, dict) else {"cn_ratio": r})
    return result


def _route_scenario(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SCENARIO'."""
    from engine.hydroma.wrapper import apply_scenario as _apply_scenario
    # The adapter's scenario keys are lowercase-compressed SSP names
    # ("ssp245"); accept the dashed FAO form too.
    raw = str(inputs.get("scenario", inputs.get("scenario_name", "")))
    scenario = "".join(ch for ch in raw.lower() if ch.isalnum())
    baseline = inputs.get("baseline", {})
    if not isinstance(baseline, dict):
        baseline = {}
    r = _apply_scenario(
        float(inputs.get("baseline_temp", baseline.get("temp", 0.0))),
        float(inputs.get("baseline_precip", baseline.get("precip", 0.0))),
        scenario,
        int(inputs.get("target_year", 2050)),
    )
    if isinstance(r, dict) and "error" in r:
        raise ValueError(
            f"unknown scenario {raw!r} (normalized {scenario!r}); "
            "expected one of ssp126, ssp245, ssp370, ssp585"
        )
    result["scenario_impact"] = _as_plain_dict(r)
    return result


def _route_climate_scenario(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CLIMATE_SCENARIO'."""
    from engine.hydroma.scenarios.climate_scenarios import (
        CLIMATE_PROJECTION_BASELINE_YEAR,
        apply_climate_change,
        get_climate_projection,
    )
    baseline = inputs.get("baseline_data", inputs.get("baseline", {}))
    if not isinstance(baseline, dict):
        baseline = {}
    baseline_temp = float(
        inputs.get("baseline_temp", baseline.get("temp", 18.0))
    )
    baseline_precip = float(
        inputs.get("baseline_precip", baseline.get("precip", 300.0))
    )
    baseline_et0 = float(
        inputs.get("baseline_et0", baseline.get("et0", 1500.0))
    )
    rcp = str(inputs.get("rcp", inputs.get("scenario", "SSP2-4.5")))
    years_ahead = int(inputs.get("years_ahead", 30))
    # ``get_climate_projection`` takes an absolute target year, but the route
    # was handed a *duration* and forwarded it unchanged, so ``years_ahead=30``
    # resolved to the 2030 row instead of ~2050. The duration is converted
    # against the projection baseline year first.
    target_year = CLIMATE_PROJECTION_BASELINE_YEAR + years_ahead
    projection = get_climate_projection(
        rcp, target_year, baseline_temp, baseline_precip, baseline_et0
    )
    r = apply_climate_change(
        baseline_temp, baseline_precip, baseline_et0, projection
    )
    result["climate_change"] = _as_plain_dict(r)
    result["projection"] = _plain(projection)
    return result


def _route_climate_projection(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CLIMATE_PROJECTION'."""
    from engine.hydroma.scenarios.climate_scenarios import (
        get_climate_projection as _climate_projection,
    )
    r = _climate_projection(
        str(inputs.get("rcp", inputs.get("scenario", "SSP2-4.5"))),
        int(inputs.get("year", 2050)),
        float(inputs.get("baseline_temp", 18.0)),
        float(inputs.get("baseline_precip", 300.0)),
        float(inputs.get("baseline_et0", 1500.0)),
    )
    result["projection"] = _plain(r)
    return result


def _route_crop_compare(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CROP_COMPARE'.

    ``compare_crops(available_water, mean_temp, co2_concentration)`` takes
    *scalars*. The route used to forward ``crop_a`` / ``crop_b`` /
    ``climate_data`` positionally, so a string ``available_water`` made every
    ``simulate_crop_yield`` call raise and ``compare_crops`` swallowed it --
    the route answered with an empty ranking and
    ``best_economic_choice=None``. The scalars are now pulled out of the
    climate mapping, as the CROP_YIELD route does.
    """
    from engine.hydroma.scenarios.crop_scenarios import compare_crops as _compare_crops

    climate = inputs.get("climate_data", inputs.get("climate", {}))
    if not isinstance(climate, dict):
        climate = {}
    available_water = float(
        climate.get("available_water", inputs.get("available_water", 0.0))
    )
    mean_temp = float(climate.get("mean_temp", inputs.get("mean_temp", 20.0)))
    co2 = float(
        climate.get("co2_concentration", inputs.get("co2_concentration", 420.0))
    )
    r = _compare_crops(available_water, mean_temp, co2)
    result.update(r if isinstance(r, dict) else {"comparison": r})
    return result


def _route_crop_yield(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'CROP_YIELD'."""
    from engine.hydroma.scenarios.crop_scenarios import (
        simulate_crop_yield as _crop_yield,
    )
    # The adapter takes scalars (available water, mean temperature,
    # growing-season precipitation), not climate/soil mappings.
    climate = inputs.get("climate_data", inputs.get("climate", {}))
    if not isinstance(climate, dict):
        climate = {}
    r = _crop_yield(
        str(inputs.get("crop_type", "")),
        float(climate.get("available_water", inputs.get("available_water", 0.0))),
        float(climate.get("mean_temp", inputs.get("mean_temp", 20.0))),
        float(
            climate.get(
                "growing_season_precip",
                inputs.get("growing_season_precip", 0.0),
            )
        ),
        float(
            climate.get(
                "irrigation_efficiency",
                inputs.get("irrigation_efficiency", 0.6),
            )
        ),
        float(
            climate.get(
                "co2_concentration",
                inputs.get("co2_concentration", 420.0),
            )
        ),
    )
    result["yield"] = _as_plain_dict(r)
    result["units"] = "kg/ha"
    return result


def _route_data_pipeline(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'DATA_PIPELINE'."""
    # ``get_pipeline()`` is the process singleton and takes no
    # arguments; the route resolves a named connector from it.
    from engine.hydroma.data_pipeline import get_pipeline

    pipeline = get_pipeline()
    connectors = pipeline.connectors
    connectors = connectors() if callable(connectors) else connectors
    if not isinstance(connectors, dict):
        connectors = {}
    name = inputs.get("name")
    info: dict[str, Any] = {
        "name": name,
        "data_root": str(getattr(pipeline, "data_root", "")),
        "available_connectors": sorted(connectors),
        "connector_class": None,
    }
    if name:
        if name not in connectors:
            raise ValueError(
                f"unknown pipeline connector {name!r}; available: "
                f"{sorted(connectors)}"
            )
        info["connector_class"] = type(connectors[name]).__name__
    result["pipeline"] = info
    return result


def _route_irrigation_depth(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'IRRIGATION_DEPTH'."""
    from engine.hydroma.irrigation.scheduler import (
        calculate_application_depth as _application_depth,
    )
    r = _application_depth(
        _route_float(inputs, "etc_mm") if "etc_mm" in inputs else _route_float(inputs, "etc"),
        _route_float(inputs, "efficiency"),
        (
            _route_float(inputs, "effective_rain_mm")
            if "effective_rain_mm" in inputs
            else _route_float(inputs, "effective_rain")
        ),
    )
    result.update(r if isinstance(r, dict) else {"depth_mm": r})
    result["units"] = "mm"
    return result


def _route_irrigation_interval(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'IRRIGATION_INTERVAL'."""
    from engine.hydroma.irrigation.scheduler import (
        calculate_interval as _irrigation_interval,
    )
    r = _irrigation_interval(
        (
            _route_float(inputs, "etc_mm_per_day")
            if "etc_mm_per_day" in inputs
            else _route_float(inputs, "etc_mm_day")
        ),
        _route_float(inputs, "raw_mm"),
        _route_float(inputs, "allowable_depletion"),
    )
    result.update(r if isinstance(r, dict) else {"interval_days": r})
    result["units"] = "days"
    return result


def _route_sim_chain(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SIM_CHAIN'."""
    # ``run_chain`` takes a single ``ChainInputs`` model plus an
    # optional progress callback, not (steps, inputs).
    from engine.hydroma.simulation.orchestrator import run_chain

    chain = _build_chain_inputs(inputs)
    r = run_chain(chain)
    result["chain"] = _plain(r)
    return result


def _route_sim_orchestrate(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SIM_ORCHESTRATE'."""
    # The orchestrator module exposes ``run_chain`` and the runners;
    # it defines no ``SimulationOrchestrator`` class. Orchestration is
    # running every requested chain and reporting each outcome,
    # including the honest "not computed" markers of unavailable
    # external binaries.
    from engine.hydroma.simulation.orchestrator import run_chain

    chains = inputs.get("chains", inputs.get("chain_inputs", []))
    if not isinstance(chains, list):
        raise ValueError("'chains' must be a list of chain input mappings")
    runs = [_plain(run_chain(_build_chain_inputs(entry))) for entry in chains]
    result["orchestration"] = {"chain_count": len(runs), "runs": runs}
    return result


def _route_recommend(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'RECOMMEND'."""
    from engine.hydroma.decision_support.dss import (
        DecisionSupportSystem as _DSS,
    )
    context = inputs.get("context", inputs)
    scenario_comparison = context.get(
        "scenario_comparison", context.get("scenarios", {})
    )
    optimization_results = context.get("optimization_results", [])
    recommendations = _DSS().generate_recommendations(
        context.get("project_id", "gateway-request"),
        scenario_comparison,
        optimization_results,
    )
    # The DSS only emits recommendations from an input `scenario_comparison`
    # (alias `scenarios`) mapping and/or a non-empty `optimization_results`
    # list, and no code here can invent those economic/risk results from a
    # bare request. Returning `{"recommendations": []}` in that case would
    # be a silent empty success, so the route instead raises an honest
    # NOT_IMPLEMENTED naming exactly what input is required.
    if not recommendations:
        raise NotImplementedError(
            "RECOMMEND: no recommendation can be computed from this "
            "request. The Decision Support System emits recommendations "
            "only when the input context carries an 'optimization_results' "
            "list or a 'scenario_comparison' (alias 'scenarios') mapping "
            "of {scenario_id: {npv_irr, projected_risk_score, ...}} "
            "(see engine/hydroma/decision_support/dss.py::"
            "generate_recommendations). NOT_IMPLEMENTED for requests "
            "that supply neither."
        )
    result.update({
        "recommendations": [
            _as_plain_dict(x) for x in recommendations
        ]
    })
    return result


def _route_soil_recommendations(model_id, inputs, parameters, result):
    """Dispatch branch: model_id == 'SOIL_RECOMMENDATIONS'."""
    from engine.hydroma.soil.recommendations import (
        generate_recommendations as _soil_recommendations,
    )
    soil_data = {k: v for k, v in inputs.items() if not k.endswith("_unit")}
    r = _soil_recommendations(soil_data.get("soil_data", soil_data))
    result.update(r if isinstance(r, dict) else {"recommendations": r})
    return result


def _route_ewsi_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('EWSI')."""
    from engine.hydroma.models.ewsi import EWSI as _EWSI
    r = _EWSI().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


_HYRUE_CROP_BY_ID: dict[str, str] = {
    "HYRUE_WHEAT": "wheat",
    "HYRUE_CORN": "maize",
}


def _route_hyrue_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('HYRUE').

    HYRUE_CORN and HYRUE_WHEAT select crop-specific presets (maize, wheat) via
    ``HYRUEParams.for_crop``; other HYRUE_* ids use the generic crop-neutral
    default. An explicit ``crop`` in ``parameters`` overrides the model-id
    derivation so a caller can select a preset per request.

    Inputs are validated via ``compute_checked`` so that out-of-range values
    (negative PAR, ewsi outside [0,1], NaN, Infinity) are rejected with a
    ``GatewayError`` rather than silently producing nonsensical output.
    """
    from engine.hydroma.models.base import compute_checked
    from engine.hydroma.models.hyrue import HYRUE as _HYRUE

    crop = parameters.get("crop") if isinstance(parameters, dict) else None
    if crop is None:
        crop = _HYRUE_CROP_BY_ID.get(model_id)
    model = _HYRUE(crop=crop) if crop else _HYRUE()

    validated = {
        "par": _route_array_or_float(inputs, "par"),
        "lai": _route_array_or_float(inputs, "lai"),
        "ewsi": _route_array_or_float(inputs, "ewsi"),
        "t_mean": _route_array_or_float(inputs, "t_mean"),
        "days": _route_int(inputs, "days", default=1),
    }
    r = compute_checked(model, **validated)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _route_ecsi_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('ECSI')."""
    from engine.hydroma.models.ecsi import ECSI as _ECSI
    r = _ECSI().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _route_epia_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('EPIA')."""
    from engine.hydroma.models.epia import EPIA as _EPIA
    r = _EPIA().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _route_hdvi_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('HDVI')."""
    from engine.hydroma.models.hdvi import HDVI as _HDVI
    r = _HDVI().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _route_esri_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('ESRI')."""
    from engine.hydroma.models.esri import ESRI as _ESRI
    r = _ESRI().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _route_hlhs_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('HLHS')."""
    from engine.hydroma.models.hlhs import HLHS as _HLHS
    r = _HLHS().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _route_hpheno_family(model_id, inputs, parameters, result):
    """Dispatch branch: model_id.startswith('HPheno')."""
    from engine.hydroma.models.hpheno import HPheno as _HPheno
    r = _HPheno().compute(**inputs, **parameters)
    result.update(r if isinstance(r, dict) else {"result": r})
    return result


def _resolve_provenance_ids(self, request: GatewayRequest) -> list[str]:
    """Return upstream Evidence ids referenced by the request.

    Only references that resolve to a collected Evidence item are
    returned, so the provenance chain never carries dangling links.
    """
    ids: list[str] = []
    if request.provenance and request.provenance.provenance_id:
        pid = request.provenance.provenance_id
        if self._evidence_engine.get(pid) is not None:
            ids.append(pid)
    return ids


def _snapshot_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Capture a plain (JSON-safe) view of request inputs for records."""
    snapshot: dict[str, Any] = {}
    for key, value in inputs.items():
        if isinstance(value, (int, float, str, bool)) or value is None:
            snapshot[key] = value
        elif isinstance(value, UnitSpec):
            snapshot[key] = {"unit": value.unit, "si_equivalent": value.si_equivalent}
        elif hasattr(value, "__dict__"):
            snapshot[key] = value.__dict__
        else:
            snapshot[key] = str(value)
    return snapshot


def _validate_request(request: GatewayRequest) -> ValidationResult:
    """Validate the gateway request structure."""
    errors = []
    warnings = []

    if not request.model_id:
        errors.append("model_id is required")
    if not request.inputs:
        errors.append("inputs is required")
    if not request.provenance:
        warnings.append("provenance not provided; using default")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _dispatch_to_model(
    self, model: ModelSpec, inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Dispatch to the appropriate model implementation.

    Routes model_id to the registered computation handler.
    Falls back to model type-based dispatch for known model types.
    """
    model_id = model.model_id

    # Try explicit handler registration first
    handler = self._handlers.get(model_id)
    if handler is not None:
        # A registered handler's contract is (inputs, parameters) -> dict
        # (see register_handler); Callable[..., Any] cannot state the
        # return type, so the contract is asserted here.
        return cast("dict[str, Any]", handler(inputs, parameters))

    # Try model class instantiation for registered scientific models
    model_type = model.model_type
    # Attempt to route to engine.hydroma models where available
    # For models requiring numpy, this will raise ImportError which is caught by execute()
    try:
        # The EngineGateway method this delegates to is typed
        # ``(str, str, dict, dict) -> dict[str, Any]``; ``self`` is unannotated in
        # this module-level dispatcher, so the contract is asserted rather than
        # inferred -- the same reason the handler branch above casts.
        return cast(
            "dict[str, Any]",
            self._dispatch_by_type(model_id, model_type, inputs, parameters),
        )
    except ImportError as e:
        raise NotImplementedError(
            _import_failure_message(model_id, e)
        ) from e

    raise NotImplementedError(
        f"No computation handler registered for model {model_id}. "
        f"Register a computation handler with the gateway via register_handler()."
    )


def _execute(self, request: GatewayRequest) -> GatewayResult | GatewayError:
    """Execute a model through the gateway.

    Pipeline:
    1. Validate request
    2. Select model
    3. Normalize units
    4. Validate inputs against model constraints
    5. Initialize provenance
    6. Execute computation
    7. Normalize result
    8. Return result with full metadata

    On every call â€” success or failure â€” an Evidence item is generated and
    collected by the Evidence Engine. The Evidence id and the shared
    ``trace_id`` (also on ``ExecutionMetadata``) link the result back to the
    full provenance chain. When an ``EvidenceAdapter`` is configured, a
    ``ComputationRecord`` is persisted for the run.
    """
    from engine.evidence import Evidence, EvidenceSource, EvidenceType
    from engine.ports.evidence_adapter import ComputationRecord

    # One trace_id per execution: shared by ExecutionMetadata, the Evidence
    # item, and any persisted ComputationRecord so the chain is linkable.
    trace_id = f"trace_{uuid4().hex[:12]}"
    execution_metadata = request.execution_metadata or ExecutionMetadata()
    execution_metadata.trace_id = trace_id
    execution_id = execution_metadata.execution_id or f"exec_{uuid4().hex[:12]}"
    execution_metadata.execution_id = execution_id
    if not execution_metadata.timestamp:
        execution_metadata.timestamp = datetime.now().isoformat()
    execution_metadata.gateway_version = self._version
    if not execution_metadata.engine_version:
        execution_metadata.engine_version = "1.0.0"
    started_at = execution_metadata.timestamp

    # Resolve upstream evidence that funded this request, so the generated
    # evidence provenance links input -> output. Only references that
    # resolve to a collected Evidence item are followed (others are treated
    # as external markers).
    provenance_ids = _resolve_provenance_ids(self, request)

    provenance = request.provenance or ProvenanceSpec(
        source="engine_gateway",
        source_type="MODEL_OUTPUT",
    )

    evidence_id_holder: list[str] = []

    def _emit_evidence(
        *,
        value: Any,
        confidence: float,
        status: str,
        error: str | None = None,
    ) -> str:
        evidence = Evidence(
            source=EvidenceSource.MODEL,
            evidence_type=EvidenceType.QUANTITATIVE,
            value=value,
            confidence=confidence,
            provenance=list(provenance_ids),
            metadata={
                "model_id": request.model_id,
                "parameters": dict(request.parameters),
                "inputs": request.inputs,
                "source": provenance.source,
                "source_type": provenance.source_type,
                "status": status,
                "trace_id": trace_id,
                "execution_id": execution_id,
                "gateway_version": self._version,
                "error": error,
            },
        )
        collected = self._evidence_engine.collect(evidence)
        evidence_id_holder.append(collected.id)
        return str(collected.id)

    def _persist_record(
        model: ModelSpec | None,
        outputs: dict[str, Any],
        status: str,
        error: str | None,
    ) -> None:
        if self._evidence_adapter is None:
            return
        record = ComputationRecord(
            trace_id=trace_id,
            model_id=request.model_id,
            model_version=model.model_version if model else "",
            model_name=model.model_name if model else "",
            inputs=_snapshot_inputs(request.inputs),
            parameters=dict(request.parameters),
            outputs=outputs,
            evidence_id=evidence_id_holder[-1] if evidence_id_holder else None,
            execution_id=execution_id,
            started_at=started_at,
            completed_at=datetime.now().isoformat(),
            status=status,
            error=error,
            gateway_version=self._version,
            provenance=list(provenance_ids),
        )
        try:
            self._evidence_adapter.store_computation_record(record)
        except Exception:
            # Provenance persistence must never break a computation.
            pass

    # Step 1: Validate request
    validation_result = _validate_request(request)
    if not validation_result.is_valid:
        evidence_id = _emit_evidence(
            value={"error": "Request validation failed",
                   "errors": validation_result.errors},
            confidence=0.0,
            status="error",
            error="Request validation failed",
        )
        _persist_record(None, {}, "error", "Request validation failed")
        return GatewayError(
            error_code="INVALID_REQUEST",
            message="Request validation failed",
            model_id=request.model_id,
            validation_errors=validation_result.errors,
            execution=execution_metadata,
            evidence_id=evidence_id,
        )

    # Step 2: Select model
    model = self._model_registry.get(request.model_id)
    if model is None:
        evidence_id = _emit_evidence(
            value={"error": f"Model {request.model_id} not registered"},
            confidence=0.0,
            status="error",
            error=f"Model {request.model_id} not registered",
        )
        _persist_record(None, {}, "error", f"Model {request.model_id} not registered")
        return GatewayError(
            error_code="MODEL_NOT_FOUND",
            message=f"Model {request.model_id} not registered",
            model_id=request.model_id,
            execution=execution_metadata,
            evidence_id=evidence_id,
        )

    # Step 2b: per-route required-input contract. Incomplete requests are
    # rejected here -- naming the missing groups -- rather than reaching
    # the computation and failing with a raw TypeError (S17, D-20).
    missing_inputs = _missing_required_inputs(request.model_id, request.inputs)
    if missing_inputs:
        message = f"Request validation failed: missing required inputs {missing_inputs}"
        evidence_id = _emit_evidence(
            value={"error": message, "errors": missing_inputs},
            confidence=0.0,
            status="error",
            error=message,
        )
        _persist_record(None, {}, "error", message)
        return GatewayError(
            error_code="INVALID_REQUEST",
            message=message,
            model_id=request.model_id,
            validation_errors=list(missing_inputs),
            execution=execution_metadata,
            evidence_id=evidence_id,
        )

    # Steps 3â€“6: Normalize units, validate inputs and execute the
    # computation. Normalization runs inside the guard so a malformed
    # or non-finite input yields a normalized GatewayError (with
    # evidence) instead of an escaped exception.
    try:
        normalized_inputs, input_validations = self._normalize_inputs(
            request, model
        )
        raw_result = self._dispatch_to_model(
            model, normalized_inputs, request.parameters
        )
    except Exception as e:
        evidence_id = _emit_evidence(
            value={"error": str(e)},
            confidence=0.0,
            status="error",
            error=str(e),
        )
        _persist_record(model, {}, "error", str(e))
        return GatewayError(
            error_code="EXECUTION_ERROR",
            message=str(e),
            model_id=request.model_id,
            execution=execution_metadata,
            evidence_id=evidence_id,
        )

    # Step 7 & 8: Normalize result
    evidence_id = _emit_evidence(
        value=raw_result,
        confidence=1.0,
        status="success",
    )
    _persist_record(model, raw_result, "success", None)

    # Extract output units from model result
    output_units = _extract_output_units(raw_result)

    result = GatewayResult(
        values=raw_result,
        output_units=output_units,
        model=model,
        provenance=provenance,
        uncertainty=request.uncertainty or UncertaintySpec(),
        execution=execution_metadata,
        data_source="modelled",
        validation=input_validations,
        evidence_id=evidence_id,
        evidence=self._evidence_engine.get(evidence_id),
    )

    return result

__all__: list[str] = []
