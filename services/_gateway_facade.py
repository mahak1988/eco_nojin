"""
Gateway Facade
==============

Service-facing facade that re-exports engine computation functions through
the Engine Gateway. This is the **only** approved way for services to access
engine computation capabilities.

Instead of:
    from engine.hydroma.soil.chemistry import calculate_cec  # ❌ VIOLATION

Use:
    from services.gateway_facade import calculate_cec          # ✅ APPROVED

The facade lazily instantiates an EngineGateway and delegates all calls.
All results carry provenance, uncertainty, and execution metadata.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)

# --- Domain adapters (A-2 step 1). Each one holds that domain's direct
#     ``engine.*`` imports plus a thin wrapper exposing the public name the
#     facade has always published; the facade imports them and re-exports them,
#     so the public surface is unchanged. The six modules carry the
#     engine-import sites that used to sit in this file and each is recorded in
#     ``tools/import_guard_policy.json`` under
#     ``SERVICES_NO_ENGINE_INTERNALS.facade_files`` as a continuation of the
#     one sanctioned bridge.
from services._gateway_facade_adapters.carbon import (  # noqa: F401
    CarbonProjectType,
    CdseConfig,
    CdseUnavailable,
    CitizenBatch,
    CitizenReport,
    IoTReading,
    SatelliteIndex,
    build_bbox,
    parse_ttn_v3,
    persist_iot_reading,
    retrieve_ndvi,
    satellite_cdse,
    webhook_key_ok,
)
from services._gateway_facade_adapters.climate import (  # noqa: F401
    ChainInputs,
    ChainResult,
    CropWaterReqInput,
    CropWaterRequirementCalculator,
    ishigami,
    run_chain,
    sensitivity_of_metric,
)
from services._gateway_facade_adapters.cppbackend import (  # noqa: F401
    backend_status,
    get_cpp_backend_status,
    get_telemetry,
    is_cpp_available,
    ndvi_array,
    penman_monteith_et0,
    reset_telemetry,
    rusle_annual_soil_loss,
)
from services._gateway_facade_adapters.economics import (  # noqa: F401
    estimate_direct_employment,
)
from services._gateway_facade_adapters.groundwater import (  # noqa: F401
    RunoffCalculator,
    RunoffInput,
    assess_water_quality,
)
from services._gateway_facade_adapters.runoff import (  # noqa: F401
    scs_cn_raster_depth_mm,
)
from services._gateway_facade_adapters.soil import (  # noqa: F401
    ECSI,
    EPIA,
    ESRI,
    EWSI,
    HDVI,
    HLHS,
    HYRUE,
    AnalysisType,
    HPheno,
    LandscapeMetric,
    LandscapeMetrics,
    TopographyAnalyzer,
    TopographyInput,
    TopographyOutput,
    estimate_rainfall_erosivity,
    run_validation_summary,
)

# --- D4: the typed error a failed gateway call raises. ``GatewayCallError``
#     subclasses ``RuntimeError`` and keeps the message this facade has always
#     produced, so every ``except RuntimeError`` arm and every ``str(exc)``
#     consumer sees exactly what it saw before, while ``error_code``,
#     ``validation_errors`` and ``evidence_id`` survive the boundary.
from services.api_gateway.errors_gateway import GatewayCallError

# NOTE: ``ChainInput``, ``compare_crop`` and ``calculate_financial_metric``
# alias facade wrappers defined further down this file, so they are bound near
# the bottom rather than here.


_gateway: EngineGateway | None = None


def get_gateway() -> EngineGateway:
    """Get or create the singleton EngineGateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = EngineGateway()
    return _gateway


def _execute(
    model_id: str,
    inputs: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    source: str = "service_gateway_facade",
    source_type: str = "SERVICE_CALL",
) -> dict[str, Any]:
    """Execute a model through the gateway.

    Returns the GatewayResult values dict on success.
    Raises GatewayError on failure.
    """
    return _execute_full(model_id, inputs, parameters, source, source_type).values


def _execute_full(
    model_id: str,
    inputs: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    source: str = "service_gateway_facade",
    source_type: str = "SERVICE_CALL",
) -> GatewayResult:
    """Execute a model through the gateway.

    Returns the full GatewayResult (with provenance, metadata, model spec).
    Raises GatewayCallError on failure — it subclasses RuntimeError and carries
    the gateway's error_code, validation_errors and evidence_id (D4).
    """
    gw = get_gateway()
    request = GatewayRequest(
        model_id=model_id,
        inputs=inputs,
        input_units={},
        provenance=ProvenanceSpec(source=source, source_type=source_type),
        parameters=parameters or {},
    )
    result = gw.execute(request)
    if isinstance(result, GatewayError):
        raise GatewayCallError.from_gateway_error(result)
    return result


def execute_with_provenance(
    model_id: str,
    inputs: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    source: str = "service_gateway_facade",
    source_type: str = "SERVICE_CALL",
) -> dict[str, Any]:
    """Execute a model and return the full result with provenance, uncertainty, and metadata.

    Returns a dict with:
    - values: the model output
    - provenance: source, source_type, trust_level, provenance_id
    - uncertainty: uncertainty_type, value, unit, method, confidence_level
    - execution: gateway_version, timestamp, execution_id, engine_version, cpp_backend, trace_id
    - model: model_id, model_version, model_name, model_type, domain, purpose, assumptions, limitations
    - output_units: dict of unit specifications
    - data_source: "modelled" | "measured" | "reference"
    - validation: list of validation results
    - evidence_id: str | None
    - evidence: the Evidence item if available
    """
    result = _execute_full(model_id, inputs, parameters, source, source_type)
    return {
        "values": result.values,
        "provenance": {
            "source": result.provenance.source,
            "source_type": result.provenance.source_type,
            "trust_level": result.provenance.trust_level,
            "provenance_id": result.provenance.provenance_id,
        },
        "uncertainty": {
            "uncertainty_type": result.uncertainty.uncertainty_type,
            "value": result.uncertainty.value,
            "unit": result.uncertainty.unit,
            "method": result.uncertainty.method,
            "confidence_level": result.uncertainty.confidence_level,
        },
        "execution": {
            "gateway_version": result.execution.gateway_version,
            "timestamp": result.execution.timestamp,
            "execution_id": result.execution.execution_id,
            "engine_version": result.execution.engine_version,
            "cpp_backend": result.execution.cpp_backend,
            "trace_id": result.execution.trace_id,
        },
        "model": {
            "model_id": result.model.model_id,
            "model_version": result.model.model_version,
            "model_name": result.model.model_name,
            "model_type": result.model.model_type,
            "domain": result.model.domain,
            "purpose": result.model.purpose,
            "assumptions": result.model.assumptions,
            "limitations": result.model.limitations,
        },
        "output_units": {k: {"unit": v.unit, "si_equivalent": v.si_equivalent, "uncertainty": v.uncertainty} for k, v in result.output_units.items()},
        "data_source": result.data_source,
        "validation": [{"is_valid": v.is_valid, "errors": v.errors, "warnings": v.warnings} for v in result.validation],
        "evidence_id": result.evidence_id,
        "evidence": str(result.evidence) if result.evidence else None,
    }


# === Soil Chemistry ===
def calculate_cec(clay_pct: float, organic_matter_pct: float, ph: float) -> dict[str, Any]:
    """Calculate cation exchange capacity."""
    return _execute("SOIL_CEC", {
        "clay_pct": clay_pct,
        "organic_matter_pct": organic_matter_pct,
        "ph": ph,
    })


def calculate_cec_with_provenance(clay_pct: float, organic_matter_pct: float, ph: float) -> dict[str, Any]:
    """Calculate CEC with full provenance, uncertainty, and execution metadata."""
    return execute_with_provenance("SOIL_CEC", {
        "clay_pct": clay_pct,
        "organic_matter_pct": organic_matter_pct,
        "ph": ph,
    })


def calculate_esp(na: float, cex: float) -> dict[str, Any]:
    """Calculate exchangeable sodium percentage."""
    return _execute("SOIL_ESP", {"na": na, "cex": cex})


def calculate_esp_with_provenance(na: float, cex: float) -> dict[str, Any]:
    """Calculate ESP with full provenance, uncertainty, and execution metadata."""
    return execute_with_provenance("SOIL_ESP", {"na": na, "cex": cex})


def calculate_sar(na: float, ca: float, mg: float) -> dict[str, Any]:
    """Calculate sodium adsorption ratio."""
    return _execute("SOIL_SAR", {"na": na, "ca": ca, "mg": mg})


def calculate_sar_with_provenance(na: float, ca: float, mg: float) -> dict[str, Any]:
    """Calculate SAR with full provenance, uncertainty, and execution metadata."""
    return execute_with_provenance("SOIL_SAR", {"na": na, "ca": ca, "mg": mg})


# === Soil Health ===
def calculate_soil_health_index(
    ph: float,
    organic_matter: float,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    cec: float | None = None,
    texture: str | None = None,
) -> dict[str, Any]:
    """Calculate soil health index (USDA NRCS indicators)."""
    return _execute("SOIL_HEALTH", {
        "ph": ph,
        "organic_matter": organic_matter,
        "nitrogen": nitrogen,
        "phosphorus": phosphorus,
        "potassium": potassium,
        "cec": cec,
        "texture": texture,
    })


def generate_recommendations(inputs: dict[str, Any]) -> dict[str, Any]:
    """Generate soil/agricultural recommendations."""
    return _execute("SOIL_RECOMMENDATIONS", inputs)


# === Soil Physics ===
def available_water_capacity(texture_class: str) -> dict[str, Any]:
    """Calculate plant-available water capacity from soil texture."""
    return _execute("SOIL_AWC", {"texture_class": texture_class})

def water_content_at(
    matric_potential_cm: float, texture_class: str
) -> dict[str, Any]:
    """Calculate water content at given matric potential."""
    return _execute("SOIL_WATER_CONTENT", {
        "matric_potential": matric_potential_cm,
        "texture_class": texture_class,
    })


def van_genuchten_theta(
    matric_potential: float,
    theta_r: float,
    theta_s: float,
    alpha: float,
    n: float,
) -> float:
    """Soil water content via the Van Genuchten (1980) retention curve.

    theta(h) = theta_r + (theta_s - theta_r) / (1 + |alpha*h|^n)^m,
    with m = 1 - 1/n. ``matric_potential`` is the suction in cm (negative).
    """
    return float(
        _execute(
            "CANON-006",
            {
                "matric_potential": matric_potential,
                "theta_r": theta_r,
                "theta_s": theta_s,
                "vg_alpha": alpha,
                "vg_n": n,
            },
        )["van_genuchten_theta"]
    )


# === Soil Salinity ===
def calculate_leaching_requirement(
    ec_soil: float, ec_water: float, target_ec: float | None = None
) -> dict[str, Any]:
    """Calculate leaching requirement to control soil salinity."""
    return _execute("SOIL_LEACHING", {
        "ec_soil": ec_soil,
        "ec_water": ec_water,
        "target_ec": target_ec,
    })

def calculate_sodic_soil_amendment(
    esp: float, soil_depth: float, bulk_density: float
) -> dict[str, Any]:
    """Calculate gypsum requirement for sodic soil amendment."""
    return _execute("SOIL_AMENDMENT", {
        "esp": esp,
        "soil_depth": soil_depth,
        "bulk_density": bulk_density,
    })

def classify_salinity(ec: float) -> dict[str, Any]:
    """Classify soil salinity level."""
    return _execute("SOIL_SALINITY_CLASSIFY", {"ec": ec})


# === Soil Taxonomy ===
def get_soil_taxonomy(
    clay: float,
    silt: float,
    sand: float,
    organic_matter: float,
    ph: float,
    cec: float | None = None,
) -> dict[str, Any]:
    """Determine soil taxonomy class."""
    return _execute("SOIL_TAXONOMY", {
        "clay": clay,
        "silt": silt,
        "sand": sand,
        "organic_matter": organic_matter,
        "ph": ph,
        "cec": cec,
    })


# === Soil Texture ===
TEXTURE_NAMES: dict[str, str] = {
    "clay": "Clay",
    "silty_clay": "Silty Clay",
    "sandy_clay": "Sandy Clay",
    "clay_loam": "Clay Loam",
    "silty_clay_loam": "Silty Clay Loam",
    "sandy_clay_loam": "Sandy Clay Loam",
    "loam": "Loam",
    "silt_loam": "Silt Loam",
    "silt": "Silt",
    "sandy_loam": "Sandy Loam",
    "loamy_sand": "Loamy Sand",
    "sand": "Sand",
}

def classify_texture(sand_pct: float, silt_pct: float, clay_pct: float) -> str:
    """Classify soil texture from percentages."""
    result = _execute("SOIL_TEXTURE", {
        "sand_pct": sand_pct,
        "silt_pct": silt_pct,
        "clay_pct": clay_pct,
    })
    # mypy: the gateway result dict is typed dict[str, Any], so bind the
    # returned value instead of returning the Any directly.
    texture_class: str = result.get("texture_class", "unknown")
    return texture_class

def is_clayey(texture_class: str) -> bool:
    """Check if soil texture is clayey (clay, silty_clay, sandy_clay)."""
    return texture_class in {"clay", "silty_clay", "sandy_clay"}


def is_sandy(texture_class: str) -> bool:
    """Check if soil texture is sandy (sand, loamy_sand, sandy_loam)."""
    return texture_class in {"sand", "loamy_sand", "sandy_loam"}


def is_silty(texture_class: str) -> bool:
    """Check if soil texture is silty (silt, silt_loam, silty_clay_loam, silty_clay)."""
    return texture_class in {"silt", "silt_loam", "silty_clay_loam", "silty_clay"}


def texture_triangle_coords(
    sand_pct: float, silt_pct: float, clay_pct: float
) -> tuple[float, float]:
    """Get (x, y) USDA triangle coordinates from sand/silt/clay percentages.

    Mirrors ``engine.hydroma.soil.texture.texture_triangle_coords``.
    """
    coords = _execute("SOIL_TEXTURE_COORDS", {
        "sand_pct": sand_pct,
        "silt_pct": silt_pct,
        "clay_pct": clay_pct,
    })
    return tuple(coords["coords"])


# === Water Retention ===
def calculate_water_retention_curve(
    texture_class: str, h_values: list[float] | None = None
) -> dict[str, Any]:
    """Calculate water retention curve for a USDA texture class."""
    return _execute("SOIL_WATER_RETENTION", {
        "texture_class": texture_class,
        "pressure_range": h_values,
    })

def get_vg_parameters(texture_class: str) -> dict[str, Any]:
    """Get Van Genuchten parameters for a soil texture class."""
    return _execute("SOIL_VG_PARAMETERS", {"texture_class": texture_class})


# === Soil Pedotransfer ===
def estimate_soil_parameters(
    sand_pct: float, clay_pct: float, om_pct: float = 1.0
) -> dict[str, Any]:
    """Estimate hydraulic parameters from basic properties."""
    return _execute("SOIL_PEDOTRANSFER", {
        "sand_pct": sand_pct,
        "clay_pct": clay_pct,
        "om_pct": om_pct,
    })


# === Climate / ET ===
def calc_et0_penman_monteith(
    temp_max: float, temp_min: float, temp_mean: float,
    rh_max: float, rh_min: float, rh_mean: float,
    wind_speed: float, solar_radiation: float,
    elevation: float, latitude: float, doy: int,
    albedo: float = 0.23,
) -> dict[str, Any]:
    """Calculate reference ET0 using FAO-56 Penman-Monteith.

    Returns a rich response dict with model_id, data, provenance and
    execution_metadata.
    """
    result = _execute_full("CANON-001", {
        "temp_max": temp_max,
        "temp_min": temp_min,
        "temp_mean": temp_mean,
        "rh_max": rh_max,
        "rh_min": rh_min,
        "rh_mean": rh_mean,
        "wind_speed": wind_speed,
        "solar_radiation": solar_radiation,
        "elevation": elevation,
        "latitude": latitude,
        "doy": doy,
        "albedo": albedo,
    })
    return {
        "model_id": result.model.model_id,
        "model_name": result.model.model_name,
        "data": result.values,
        "provenance": {
            "source": result.provenance.source,
            "source_type": result.provenance.source_type,
            "trust_level": result.provenance.trust_level,
        },
        "execution_metadata": {
            "gateway_version": result.execution.gateway_version,
            "engine_version": result.execution.engine_version,
            "cpp_backend": result.execution.cpp_backend,
            "timestamp": result.execution.timestamp,
        },
    }

def calc_et0_hargreaves(
    temp_max: float, temp_min: float,
    elevation: float, latitude: float, doy: int,
) -> dict[str, Any]:
    """Calculate reference ET0 using Hargreaves method.

    Returns a rich response dict with model_id, data (containing
    ``et0_mm_day``), provenance and execution_metadata.
    """
    result = _execute_full("CANON-002", {
        "temp_max": temp_max,
        "temp_min": temp_min,
        "elevation": elevation,
        "latitude": latitude,
        "doy": doy,
    })
    return {
        "model_id": result.model.model_id,
        "model_name": result.model.model_name,
        "data": result.values,
        "provenance": {
            "source": result.provenance.source,
            "source_type": result.provenance.source_type,
            "trust_level": result.provenance.trust_level,
        },
        "execution_metadata": {
            "gateway_version": result.execution.gateway_version,
            "engine_version": result.execution.engine_version,
            "cpp_backend": result.execution.cpp_backend,
            "timestamp": result.execution.timestamp,
        },
    }

def calc_extraterrestrial_radiation(
    latitude: float, doy: int
) -> dict[str, Any]:
    """Calculate extraterrestrial radiation.

    Returns a rich response dict with model_id, data, provenance and
    execution_metadata.
    """
    result = _execute_full("CANON-011_RAD", {
        "latitude": latitude,
        "doy": doy,
    })
    return {
        "model_id": result.model.model_id,
        "model_name": result.model.model_name,
        "data": result.values,
        "provenance": {
            "source": result.provenance.source,
            "source_type": result.provenance.source_type,
            "trust_level": result.provenance.trust_level,
        },
        "execution_metadata": {
            "gateway_version": result.execution.gateway_version,
            "engine_version": result.execution.engine_version,
            "cpp_backend": result.execution.cpp_backend,
            "timestamp": result.execution.timestamp,
        },
    }

def hargreaves_et0(
    t_min: float, t_max: float, latitude: float, doy: int
) -> float:
    """Convenience wrapper: Hargreaves ET0 as a plain float.

    Delegates to :func:`calc_et0_hargreaves` with ``elevation=0`` and
    returns only the ``et0_mm_day`` value.
    """
    result = calc_et0_hargreaves(
        temp_max=t_max,
        temp_min=t_min,
        elevation=0.0,
        latitude=latitude,
        doy=doy,
    )
    # mypy: nested Any lookup through the gateway result dict.
    et0_mm_day: float = result["data"]["et0_mm_day"]
    return et0_mm_day

def fetch_daily_weather(
    latitude: float, longitude: float, start_date: str, end_date: str
) -> Any:
    """Fetch daily weather data from an external source.

    Raises ``NotImplementedError`` — requires API configuration and
    network access that is not available in the test environment.
    """
    raise NotImplementedError(
        "fetch_daily_weather requires external API configuration "
        "(Open-Meteo ERA5) not available in the test environment."
    )

class ClimateData:
    """Climate data container (re-exported through gateway)."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# === Carbon ===
def calculate_carbon_sequestration(
    project_type: CarbonProjectType | str,
    area_ha: float,
    duration_years: int = 10,
    region: str = "temperate",
) -> dict[str, Any]:
    """Calculate soil carbon sequestration (IPCC 2019 Refinement)."""
    if isinstance(project_type, CarbonProjectType):
        project_type = project_type.value
    return _execute("CARBON_SEQ", {
        "project_type": project_type,
        "area_ha": area_ha,
        "duration_years": duration_years,
        "region": region,
    })


# === Economics ===
def calculate_npv(cash_flows: list[float], discount_rate: float) -> dict[str, Any]:
    """Calculate net present value."""
    return _execute("ECON_NPV", {
        "cash_flows": cash_flows,
        "discount_rate": discount_rate,
    })

def calculate_payback(cash_flows: list[float]) -> dict[str, Any]:
    """Calculate payback period from a cash-flow series."""
    return _execute("ECON_PAYBACK", {"cash_flows": cash_flows})

def calculate_agricultural_cost(
    area_ha: float, crop_type: str, input_costs: dict[str, float]
) -> dict[str, Any]:
    """Calculate agricultural production cost."""
    return _execute("ECON_AG_COST", {
        "area_ha": area_ha,
        "crop_type": crop_type,
        "input_costs": input_costs,
    })

def calculate_agricultural_revenue(
    area_ha: float, crop_type: str, yield_tonnes: float, price_per_tonne: float
) -> dict[str, Any]:
    """Calculate agricultural revenue."""
    return _execute("ECON_AG_REVENUE", {
        "area_ha": area_ha,
        "crop_type": crop_type,
        "yield_tonnes": yield_tonnes,
        "price_per_tonne": price_per_tonne,
    })
def assess_market_price_risk(
    base_price: float,
    volatility: float,
    time_horizon_years: int = 1,
    confidence_level: float = 0.05,
) -> dict[str, Any]:
    """Assess market price risk (VaR-style) for a price level and volatility.

    The keyword contract matches the engine's ``economics.risk`` function and
    the engine's own integration layer; the pre-S17 ``price_history`` form did
    not (T-03).
    """
    return _execute("ECON_PRICE_RISK", {
        "base_price": base_price,
        "volatility": volatility,
        "time_horizon_years": time_horizon_years,
        "confidence_level": confidence_level,
    })


def assess_yield_risk(
    expected_yield: float,
    yield_std_dev: float,
    area_hectares: float,
    price_per_unit: float,
    confidence_level: float = 0.05,
) -> dict[str, Any]:
    """Assess yield risk for a production area and unit price.

    The keyword contract matches the engine's ``economics.risk`` function and
    the engine's own integration layer; the pre-S17 ``yield_history`` form did
    not (T-03).
    """
    return _execute("ECON_YIELD_RISK", {
        "expected_yield": expected_yield,
        "yield_std_dev": yield_std_dev,
        "area_hectares": area_hectares,
        "price_per_unit": price_per_unit,
        "confidence_level": confidence_level,
    })

def calculate_financial_metrics(
    initial_investment: float, cash_flows: list[float],
    discount_rate: float, terminal_value: float = 0.0
) -> dict[str, Any]:
    """Calculate comprehensive financial metrics."""
    return _execute("ECON_FINANCIAL", {
        "initial_investment": initial_investment,
        "cash_flows": cash_flows,
        "discount_rate": discount_rate,
        "terminal_value": terminal_value,
    })


# === Watershed ===
def calculate_runoff(
    precipitation: float,
    curve_number: float = 75.0,
    ia_factor: float = 0.2,
    method: str = "SCS-CN",
    area_ha: float = 1.0,
    rational_coefficient: float = 0.6,
) -> dict[str, Any]:
    """Calculate runoff using the SCS-CN or Rational method (NRCS TR-55)."""
    return _execute("CANON-004", {
        "precipitation": precipitation,
        "curve_number": curve_number,
        "ia_factor": ia_factor,
        "method": method,
        "area_ha": area_ha,
        "rational_coefficient": rational_coefficient,
    })


def calculate_runoff_raster(
    precipitation: Any,
    curve_number: Any,
    ia_factor: float = 0.2,
) -> Any:
    """SCS-CN runoff depth for whole grids, in one engine-owned call.

    The scalar ``calculate_runoff`` dispatches through the gateway per call,
    which is one round trip per distinct (precipitation, curve number) pair —
    fine for a point, prohibitive for a raster. This entry evaluates the same
    triplet (``engine.hydroma.runoff.scs_cn_raster_depth_mm``, CANON-004's
    relation) over the arrays in a single vector pass and returns the depths
    with the inputs' shape. A cell below the initial abstraction, or with a
    non-finite value, carries depth 0, exactly as the scalar path answers.
    """
    return scs_cn_raster_depth_mm(precipitation, curve_number, ia_factor=ia_factor)

class StructureType:
    """Watershed structure types."""
    CHECK_DAM = "check_dam"
    CONTOUR_TRENCH = "contour_trench"
    HALF_MOON = "half_moon"
    SOIL_BERM = "soil_berm"

def design_watershed_structure(
    structure_type: str, drainage_area_ha: float,
    peak_flow: float, slope: float,
) -> dict[str, Any]:
    """Design a watershed structure."""
    return _execute("WATERSHED_STRUCT", {
        "structure_type": structure_type,
        "drainage_area_ha": drainage_area_ha,
        "peak_flow": peak_flow,
        "slope": slope,
    })

def design_check_dam(
    drainage_area_ha: float, peak_flow: float, slope: float
) -> dict[str, Any]:
    """Design a check dam."""
    return _execute("WATERSHED_CHECK_DAM", {
        "drainage_area_ha": drainage_area_ha,
        "peak_flow": peak_flow,
        "slope": slope,
    })

def design_contour_trench(
    drainage_area_ha: float, peak_flow: float, slope: float
) -> dict[str, Any]:
    """Design a contour trench."""
    return _execute("WATERSHED_CONTOUR_TRENCH", {
        "drainage_area_ha": drainage_area_ha,
        "peak_flow": peak_flow,
        "slope": slope,
    })

def design_half_moon(
    drainage_area_ha: float, peak_flow: float, slope: float
) -> dict[str, Any]:
    """Design a half-moon structure."""
    return _execute("WATERSHED_HALF_MOON", {
        "drainage_area_ha": drainage_area_ha,
        "peak_flow": peak_flow,
        "slope": slope,
    })


# === Plant Neurology ===
class StressLevel:
    """Plant stress level enum."""
    HEALTHY = "healthy"
    MILD_STRESS = "mild_stress"
    SEVERE_STRESS = "severe_stress"
    RECOVERY = "recovery"

class VOCProfile:
    """Volatile organic compound profile."""
    def __init__(self, compounds: list[str] | None = None):
        self.compounds = compounds or []

class PlantNeuroEngine:
    """Plant neurology engine facade."""
    def detect_stress(self, ndvi_time_series: list[float]) -> dict[str, Any]:
        return _execute("PLANT_NEURO", {"ndvi_time_series": ndvi_time_series})


# === Scientific Models ===
#: The eight index models are re-exported at module level (see the soil adapter
#: import block near the top of this file) because ``routers/
#: hydroma_indices.py`` imports them by name. This lookup therefore reads the
#: module-level bindings; the function-local import that used to live here
#: shadowed them and was flagged as a redefinition.
_MODEL_CLASS_MAP = {
    "EWSI": EWSI, "HYRUE": HYRUE, "ECSI": ECSI, "HDVI": HDVI,
    "EPIA": EPIA, "ESRI": ESRI, "HLHS": HLHS, "HPheno": HPheno,
}


def _get_model_class(model_name: str):
    """Return one of the HyDroMa index model classes, or None if unknown."""
    return _MODEL_CLASS_MAP.get(model_name)



# === Groundwater ===
class AquiferType(StrEnum):
    """Aquifer type enum."""
    CONFINED = "confined"
    UNCONFINED = "unconfined"
    SEMI_CONFINED = "semi_confined"


class GroundwaterInput(BaseModel):
    """Groundwater model input contract.

    Unions the two shapes the gateway routers construct, because both import
    this one facade name:

    * the analytical/Theis contract (``analyses.py``,
      ``hydroma_water._run_groundwater``) — ``model_type``,
      ``transmissivity_m2day``, ``storativity``, ``pumping_rate_m3day``,
      ``observation_distance_m``, ``time_days``;
    * the service/sustainability contract (``hydroma_water.
      _run_groundwater_service``, imported as ``ServiceGroundwaterInput``) —
      ``land_profile_id``, ``well_depth_m``, ``water_table_depth_m``,
      ``hydraulic_conductivity_m_s``, ``aquifer_thickness_m``, ``aquifer_type``,
      ``recharge_rate_mm_yr``, ``abstraction_rate_m3_yr``, ``tds_mg_l``,
      ``porosity``, ``specific_yield``.

    Every field is optional and extras are allowed so either construction
    site validates; the caller is responsible for supplying the fields its
    chosen model reads.
    """

    model_config = ConfigDict(extra="allow")

    model_type: str = "analytical"
    transmissivity_m2day: float | None = None
    storativity: float | None = None
    pumping_rate_m3day: float = 0.0
    observation_distance_m: float | None = None
    time_days: float | None = None
    land_profile_id: str | None = None
    well_depth_m: float | None = None
    water_table_depth_m: float | None = None
    hydraulic_conductivity_m_s: float | None = None
    aquifer_thickness_m: float | None = None
    aquifer_type: str | None = None
    recharge_rate_mm_yr: float = 0.0
    abstraction_rate_m3_yr: float = 0.0
    tds_mg_l: float = 0.0
    porosity: float = 0.3
    specific_yield: float = 0.15


def _as_payload(inputs: Any) -> Any:
    """Coerce a Pydantic model, object or mapping into a gateway payload."""
    if inputs is None:
        return {}
    if hasattr(inputs, "model_dump"):
        return inputs.model_dump(mode="json")
    if isinstance(inputs, dict):
        return inputs
    return {k: v for k, v in vars(inputs).items() if not k.startswith("_")}


class GroundwaterModel:
    """Groundwater model facade."""
    def simulate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return _execute("CANON-005", _as_payload(inputs))

    def execute(self, input_data: Any) -> dict[str, Any]:
        """Execute the groundwater model.

        ``analyses.py`` and ``hydroma_water.py`` call ``.execute``; the
        canonical facade entry point is :meth:`simulate`.
        """
        return self.simulate(_as_payload(input_data))


# === C++ Bindings ===
# ``is_cpp_available``, ``get_cpp_backend_status``, ``backend_status`` and the
# accelerated kernels come from the cppbackend adapter, which holds the
# ``engine.hydroma.cpp_bridge`` import and the capability probe this file used
# to carry.


# === Simulation ===
# ``run_chain``, ``ChainInputs`` and ``ChainResult`` are imported at the top of
# this file (see the domain-adapter blocks); the simulation router uses them
# directly rather than a ``**kwargs`` container.


# === MRV ===
class MRVMetrics:
    """MRV metrics facade."""
    def compute(self, data: dict[str, Any]) -> dict[str, Any]:
        return _execute("MRV_METRICS", data)

def compute_dashboard(metrics_data: dict[str, Any]) -> dict[str, Any]:
    """Compute MRV dashboard data."""
    return _execute("MRV_DASHBOARD", metrics_data)

def validate_reading(reading: dict[str, Any]) -> dict[str, Any]:
    """Validate an MRV reading."""
    return _execute("MRV_VALIDATE", reading)

def validate_satellite_index(index_data: dict[str, Any]) -> dict[str, Any]:
    """Validate satellite index data."""
    return _execute("MRV_VALIDATE_SAT", index_data)


# === Biofertilizer ===
class NojinMaterial:
    MATERIALS = ["compost", "manure", "biochar", "chemical_fertilizer"]

class NojinFormulationRecipe:
    """Biofertilizer formulation recipe."""
    def __init__(self, materials: list[str], ratios: list[float]):
        self.materials = materials
        self.ratios = ratios

class NojinSoilType:
    """Soil type for Nojin formulations."""
    CLAY = "clay"
    LOAM = "loam"
    SAND = "sand"


# === Materials ===
class CompostMaterial(BaseModel):
    """Compost material descriptor (mirrors the engine model)."""

    name: str = Field(..., description="Name of the material (e.g., Straw, Cow Manure)")
    mass_kg: float = Field(..., gt=0, description="Mass of the material in kg")
    carbon_content: float = Field(..., ge=0, le=100, description="Carbon percentage (0-100)")
    nitrogen_content: float = Field(..., ge=0, le=100, description="Nitrogen percentage (0-100)")

def calculate_mix_cn_ratio(materials: list[CompostMaterial]) -> float:
    """Calculate carbon-to-nitrogen ratio for compost mix."""
    # mypy: Any from the gateway result dict.
    cn_ratio: float = _execute("COMPOST_CN", {"materials": materials}).get("cn_ratio", 0.0)
    return cn_ratio


# === Wrapper functions (high-level) ===
def compute_erosion(
    rainfall: float, slope: float, area_ha: float,
    soil_type: str, ground_cover: float,
) -> dict[str, Any]:
    """Compute soil erosion using RUSLE."""
    return _execute("CANON-007", {
        "rainfall": rainfall,
        "slope": slope,
        "area_ha": area_ha,
        "soil_type": soil_type,
        "ground_cover": ground_cover,
    })

def apply_scenario(
    scenario_name: str, inputs: dict[str, Any]
) -> dict[str, Any]:
    """Apply a climate scenario to inputs."""
    # Unpack inputs to match SCENARIO model expectations
    return _execute("SCENARIO", {
        "scenario": scenario_name,
        "baseline_temp": float(inputs.get("baseline_temp", 20.0)),
        "baseline_precip": float(inputs.get("baseline_precip", 400.0)),
        "target_year": int(inputs.get("year", inputs.get("target_year", 2050))),
    })


# === Scenarios ===
SCENARIOS = {
    "rcp26": {"description": "Low emissions scenario"},
    "rcp45": {"description": "Moderate emissions scenario"},
    "rcp60": {"description": "High emissions scenario"},
    "rcp85": {"description": "Very high emissions scenario"},
}

def apply_climate_change(
    baseline_data: dict[str, Any], rcp: str, years_ahead: int
) -> dict[str, Any]:
    """Apply climate change scenario to baseline data.

    The three baselines are sent *flat*. They used to be nested under
    ``baseline``, which the gateway's required-input check does not look at,
    so every call failed with "missing required inputs ['baseline_temp',
    'baseline_precip', 'baseline_et0']" before the model ever ran.
    """
    return _execute("CLIMATE_SCENARIO", {
        "baseline_temp": float(
            baseline_data.get("temp", baseline_data.get("baseline_temp", 18.0))
        ),
        "baseline_precip": float(
            baseline_data.get("precip", baseline_data.get("baseline_precip", 300.0))
        ),
        "baseline_et0": float(
            baseline_data.get("et0", baseline_data.get("baseline_et0", 1500.0))
        ),
        "rcp": rcp,
        "years_ahead": int(years_ahead),
    })

def get_climate_projection(
    latitude: float, longitude: float, rcp: str, year: int
) -> dict[str, Any]:
    """Get climate projection for a location."""
    return _execute("CLIMATE_PROJECTION", {
        "latitude": latitude,
        "longitude": longitude,
        "rcp": rcp,
        "year": year,
    })

def compare_crops(
    crop_a: str, crop_b: str, climate_data: dict[str, Any]
) -> dict[str, Any]:
    """Compare two crops under given climate."""
    return _execute("CROP_COMPARE", {
        "crop_a": crop_a,
        "crop_b": crop_b,
        "climate": climate_data,
    })

def simulate_crop_yield(
    crop_type: str, climate_data: dict[str, Any], soil_data: dict[str, Any]
) -> dict[str, Any]:
    """Simulate crop yield."""
    return _execute("CROP_YIELD", {
        "crop_type": crop_type,
        "climate": climate_data,
        "soil": soil_data,
    })


# === Data Pipeline ===
def get_pipeline(name: str) -> dict[str, Any]:
    """Get a data pipeline by name."""
    return _execute("DATA_PIPELINE", {"name": name})


# === Irrigation ===
def calculate_application_depth(
    etc_mm: float, efficiency: float, effective_rain_mm: float
) -> dict[str, Any]:
    """Calculate irrigation application depth: GAR = (ETc - Pe) / Ea."""
    return _execute("IRRIGATION_DEPTH", {
        "etc_mm": etc_mm,
        "efficiency": efficiency,
        "effective_rain_mm": effective_rain_mm,
    })

def calculate_interval(
    etc_mm_per_day: float, raw_mm: float, allowable_depletion: float
) -> dict[str, Any]:
    """Calculate irrigation interval: I = (TAW * p) / ETc."""
    return _execute("IRRIGATION_INTERVAL", {
        "etc_mm_per_day": etc_mm_per_day,
        "raw_mm": raw_mm,
        "allowable_depletion": allowable_depletion,
    })


# === Simulation Orchestration ===
class SimulationOrchestrator:
    """Simulation orchestrator facade."""
    def run(self, config: dict[str, Any]) -> dict[str, Any]:
        return _execute("SIM_ORCHESTRATE", config)


# === Decision Support ===
class RecommenderEngine:
    """Recommendation engine facade."""
    def recommend(self, context: dict[str, Any]) -> dict[str, Any]:
        return _execute("RECOMMEND", context)


# === Satellite Processing ===
def calculate_ndwi(green: Any, nir: Any) -> dict[str, Any]:
    """Calculate Normalized Difference Water Index (NDWI)."""
    return _execute("SAT_NDWI", {"green": list(green) if hasattr(green, '__iter__') else green, "nir": list(nir) if hasattr(nir, '__iter__') else nir})


def calculate_ndvi(nir: Any, red: Any) -> dict[str, Any]:
    """Calculate Normalized Difference Vegetation Index (NDVI)."""
    return _execute("SAT_NDVI", {"nir": nir, "red": red})


# === CPP Bindings ===
# NOTE: ``is_cpp_available`` is now defined once, in the cppbackend adapter that
# owns the ``engine.hydroma.cpp_bridge`` probe. A second definition used to
# shadow it and route the probe through a ``CPP_STATUS`` gateway model that
# does not exist, raising RuntimeError on every import-time call
# (``scientific_motors/irrigation_scheduler.py`` caches the result in a module
# global). A capability probe must never raise.


# === Climate Adaptation Engines ===
class UncertaintyAndKnowledgeEngine:
    """Uncertainty and knowledge engine facade."""
    def assess(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return _execute("UNCERTAINTY_ASSESS", inputs)


class DynamicStressEngine:
    """Dynamic stress engine facade."""
    def evaluate(self, climate_data: dict[str, Any]) -> dict[str, Any]:
        return _execute("DYNAMIC_STRESS", climate_data)


class SeedOptimizationEngine:
    """Seed optimization engine facade."""
    def optimize(self, constraints: dict[str, Any]) -> dict[str, Any]:
        return _execute("SEED_OPTIMIZE", constraints)


class SoilDegradationModel:
    """Soil degradation model facade."""
    def simulate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return _execute("SOIL_DEGRADATION", inputs)


class ClimateAdaptivePhenology:
    """Climate adaptive phenology model facade."""
    def predict(self, climate: dict[str, Any]) -> dict[str, Any]:
        return _execute("PHENLOGY_PREDICT", climate)


# === Calculation Engine ===
class CalculationEngine:
    """Calculation engine facade."""
    def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return _execute("CALCULATE", inputs)


# === MRV Metrics ===
# Typing note: the later ``MRVMetrics`` in this file deliberately supersedes the
# identically named class above (that one is unreachable); renaming either
# definition would change which object ``MRVMetrics`` resolves to, so the
# documented shadowing stays and is typed around.
class MRVMetrics:  # type: ignore[no-redef]
    """MRV metrics facade."""
    @staticmethod
    def compute_dashboard(data: dict[str, Any]) -> dict[str, Any]:
        return _execute("MRV_DASHBOARD", data)


# === RothC Runner ===
class RothCRunner:
    """RothC simulation runner facade."""
    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return _execute("ROTHTC_RUN", inputs)


def temp_factor(temperature: float) -> float:
    """Calculate temperature factor for RothC."""
    result = _execute("ROTHTC_TEMP_FACTOR", {"temperature": temperature})
    # mypy: Any from the gateway result dict.
    value: float = result.get("value", 0.0)
    return value


# === Scenario Wrapper ===
# Typing note: deliberate shadowing — this ``compute_erosion`` supersedes the
# earlier RUSLE/CANON-007 one, and ``routers/soil.py`` / ``models/registry.py``
# import exactly this signature. Removal or renaming would change which callable
# ``compute_erosion`` resolves to, so it is typed around instead.
def compute_erosion(  # type: ignore[no-redef]
    slope_length: float, slope_percent: float, annual_rainfall: float,
    texture: str, c_factor: float = 0.5, p_factor: float = 0.8
) -> dict[str, Any]:
    """Compute soil erosion using RUSLE.

    This definition supersedes the earlier one in this module (which took
    ``rainfall/slope/area_ha/soil_type/ground_cover``). It used to route to
    ``SOIL_EROSION``, a gateway id that is **not registered** in the engine,
    so every call raised ``GatewayCallError: Model SOIL_EROSION not
    registered``. The RUSLE topographic factor and the full annual-soil-loss
    product live in ``CANON-007`` / ``RUSLE_LS``; that handler accepts the
    whole factor set (``slope_length``, ``slope_percent``,
    ``annual_rainfall``, ``texture``, ``c_factor``, ``p_factor``) and refuses
    a partial one rather than inventing the missing factors.
    """
    return _execute("CANON-007", {
        "slope_length_m": slope_length,
        "slope_percent": slope_percent,
        "annual_rainfall_mm": annual_rainfall,
        "texture": texture,
        "c_factor": c_factor,
        "p_factor": p_factor,
    })


# === MRV IoT Ingest ===
# ``parse_ttn_v3`` and ``persist_iot_reading`` are imported at the top of this
# file. ``routers/mrv.py`` and ``business_modules/iot/device_connector.py`` are
# the consumers; both call ``persist_iot_reading(session, reading)``, which is
# the engine's ``iot_ingest`` signature. The previous facade versions routed
# through ``PARSE_TTN`` / ``PERSIST_IOT`` gateway ids that do not exist and took
# one argument, so every call raised.


# === Biofertilizer ===
class ScaleCalculator:
    """Biofertilizer scale calculator facade."""
    def calculate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return _execute("SCALE_CALCULATE", inputs)


MATERIALS: dict[str, Any] = {}



# === Employment Estimation ===
# ``estimate_direct_employment`` is the public facade entry point, now defined in
# the economics adapter that owns the ``engine.hydroma.economics.employment``
# import; it is re-exported from there so the signature below is unchanged.


# === Simulation / Sensitivity ===
# ``ishigami`` and ``sensitivity_of_metric`` are imported at the top of this
# file from the climate adapter and re-exported under their public names.


# === Soil Physics (singular wrapper) ===
def estimate_soil_parameter(
    sand_pct: float, clay_pct: float, om_pct: float = 1.0
) -> dict[str, Any]:
    """Singular wrapper for estimate_soil_parameters (plural)."""
    return estimate_soil_parameters(
        sand_pct=sand_pct,
        clay_pct=clay_pct,
        om_pct=om_pct,
    )


# === Groundwater Service (wrapper) ===
class GroundwaterService:
    """Groundwater service facade — requires GROUNDWATER_SERVICE model (D-13/D-06).

    Currently no dedicated model is registered; CANON-005 (Theis) expects
    transmissivity/storativity inputs, not the hydrogeological profile used
    by the 'groundwater-service' endpoint. Returns 503 until the model is
    registered or the endpoint is re-scoped.
    """
    def __init__(self) -> None:
        pass

    def analyze(self, model_input: dict[str, Any]) -> dict[str, Any]:
        """Analyze groundwater — disabled pending model registration."""
        raise RuntimeError(
            "GROUNDWATER_SERVICE model not registered (D-13/D-06). "
            "Endpoint 'groundwater-service' requires a dedicated model; "
            "current CANON-005 (Theis) expects transmissivity/storativity inputs."
        )


# === Rainfall Erosivity ===
# ``estimate_rainfall_erosivity`` is defined in the soil adapter, which owns the
# ``engine.hydroma.land.erosion_risk`` import; it is re-exported from there.


# === Hargreaves ET0 (singular alias) ===
def calc_et0_hargreave(
    temp_max: float, temp_min: float,
    elevation: float, latitude: float, doy: int,
) -> dict[str, Any]:
    """Singular alias for calc_et0_hargreaves (plural)."""
    return calc_et0_hargreaves(
        temp_max=temp_max,
        temp_min=temp_min,
        elevation=elevation,
        latitude=latitude,
        doy=doy,
    )


# === Machine Evidence ===
# ``run_validation_summary`` is defined in the soil adapter, which owns the
# ``engine.hydroma.models.validation.runner`` import and keeps it
# function-local so this facade still imports when the optional corpus
# dependencies are absent; the caller sees the ImportError.


# === Scenarios (already defined above) ===
# ``SCENARIOS`` is defined near the simulation section above.


# ---------------------------------------------------------------------------
# Singular aliases for facade wrappers defined above.
#
# Several gateway routers import the singular spelling but use the plural one
# in their bodies (or the reverse). Both spellings resolve to the same
# callable, so either name works at a call site.
# ---------------------------------------------------------------------------

#: ``routers/simulation.py`` reads ``ChainInputs``; the singular resolves to it.
ChainInput = ChainInputs

#: ``models/registry.py`` reads ``compare_crops``; the singular resolves to it.
compare_crop = compare_crops

#: ``routers/hydroma_economics.py`` reads ``calculate_financial_metrics``.
calculate_financial_metric = calculate_financial_metrics


# ---------------------------------------------------------------------------
# Note: the domain adapters hold the engine re-export imports (index models,
# C++ kernels, water quality, runoff / crop-water calculators, MRV contracts,
# the simulation chain, topography / employment / sensitivity / CDSE
# contracts) and this file re-exports their names at the top, so the public
# surface is unchanged while the engine-import sites that made this file a
# God-object sit behind a domain boundary (A-2 step 1).
# ---------------------------------------------------------------------------