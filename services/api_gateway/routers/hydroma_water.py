"""HyDroMa water-tools API (surface runoff + groundwater drawdown).

Endpoints
---------
GET  /api/v1/hydroma/water          -> metadata
GET  /api/v1/hydroma/water/{id}     -> one tool's metadata
POST /api/v1/hydroma/water/{id}/run -> execute (pure compute)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.models.groundwater_model import GroundwaterInput, GroundwaterModel
from engine.hydroma.groundwater.service import (
    AquiferType,
    GroundwaterInput as ServiceGroundwaterInput,
    GroundwaterService,
)
from engine.hydroma.watershed.calculator import calculate_runoff
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/water", tags=["hydroma-water"])

_SPECS: list[dict[str, Any]] = [
    {
        "id": "runoff-model",
        "name_en": "Surface runoff model",
        "description": "Event runoff volume from catchment area, rainfall and runoff coefficient "
                       "(SCS-style rational method).",
        "reference": "SCS-CN / rational method",
        "params": [
            {"name": "area_m2", "label": "Catchment area", "unit": "m2", "kind": "float", "default": 10000.0},
            {"name": "rainfall_mm", "label": "Rainfall", "unit": "mm", "kind": "float", "default": 30.0},
            {"name": "runoff_coefficient", "label": "Runoff coefficient", "unit": "", "kind": "float", "default": 0.5},
        ],
    },
    {
        "id": "runoff-surface",
        "name_en": "Surface runoff (catchment service)",
        "description": "Runoff volume for a catchment using the watershed engine service.",
        "reference": "SCS-CN / rational method",
        "params": [
            {"name": "area_m2", "label": "Catchment area", "unit": "m2", "kind": "float", "default": 25000.0},
            {"name": "rainfall_mm", "label": "Rainfall", "unit": "mm", "kind": "float", "default": 45.0},
            {"name": "runoff_coefficient", "label": "Runoff coefficient", "unit": "", "kind": "float", "default": 0.4},
        ],
    },
    {
        "id": "groundwater-model",
        "name_en": "Groundwater drawdown model",
        "description": "Analytical drawdown around a pumping well (Theis-based); "
                       "modflow_link reports the coupled-model handoff.",
        "reference": "Todd & Mays 2005",
        "params": [
            {"name": "model_type", "label": "Model type", "unit": "", "kind": "select",
             "default": "analytical", "options": ["analytical", "modflow_link"]},
            {"name": "transmissivity_m2day", "label": "Transmissivity", "unit": "m2/day", "kind": "float", "default": 500.0},
            {"name": "storativity", "label": "Storativity", "unit": "", "kind": "float", "default": 0.0002},
            {"name": "pumping_rate_m3day", "label": "Pumping rate", "unit": "m3/day", "kind": "float", "default": 1000.0},
            {"name": "observation_distance_m", "label": "Observation distance", "unit": "m", "kind": "float", "default": 100.0},
            {"name": "time_days", "label": "Time since pumping", "unit": "day", "kind": "float", "default": 30.0},
        ],
    },
    {
        "id": "groundwater-service",
        "name_en": "Groundwater service",
        "description": "Darcy flux, transmissivity, sustainability index, safe yield and quality class for a well scenario.",
        "reference": "Todd & Mays 2005",
        "params": [
            {"name": "land_profile_id", "label": "Profile id", "unit": "", "kind": "str", "default": "profile-1"},
            {"name": "well_depth_m", "label": "Well depth", "unit": "m", "kind": "float", "default": 80.0},
            {"name": "water_table_depth_m", "label": "Water table depth", "unit": "m", "kind": "float", "default": 25.0},
            {"name": "hydraulic_conductivity_m_s", "label": "Hydraulic conductivity", "unit": "m/s", "kind": "float", "default": 0.00001},
            {"name": "aquifer_thickness_m", "label": "Aquifer thickness", "unit": "m", "kind": "float", "default": 40.0},
            {"name": "aquifer_type", "label": "Aquifer type", "unit": "", "kind": "select",
             "default": "UNCONFINED", "options": ["UNCONFINED", "CONFINED", "SEMI_CONFINED", "FRACTURED"]},
            {"name": "recharge_rate_mm_yr", "label": "Recharge", "unit": "mm/yr", "kind": "float", "default": 60.0},
            {"name": "abstraction_rate_m3_yr", "label": "Abstraction", "unit": "m3/yr", "kind": "float", "default": 20000.0},
            {"name": "tds_mg_l", "label": "TDS", "unit": "mg/L", "kind": "float", "default": 450.0},
            {"name": "porosity", "label": "Porosity", "unit": "", "kind": "float", "default": 0.3},
            {"name": "specific_yield", "label": "Specific yield", "unit": "", "kind": "float", "default": 0.2},
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}


def _run_runoff(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_runoff(
        kw["area_m2"],
        kw["rainfall_mm"],
        kw["runoff_coefficient"],
    )


def _run_groundwater(kw: dict[str, Any]) -> dict[str, Any]:
    model_input = GroundwaterInput(
        model_type=kw["model_type"],
        transmissivity_m2day=kw["transmissivity_m2day"],
        storativity=kw["storativity"],
        pumping_rate_m3day=kw["pumping_rate_m3day"],
        observation_distance_m=kw["observation_distance_m"],
        time_days=kw["time_days"],
    )
    return GroundwaterModel().execute(model_input)


def _run_groundwater_service(kw: dict[str, Any]) -> dict[str, Any]:
    model_input = ServiceGroundwaterInput(
        land_profile_id=kw["land_profile_id"],
        well_depth_m=kw["well_depth_m"],
        water_table_depth_m=kw["water_table_depth_m"],
        hydraulic_conductivity_m_s=kw["hydraulic_conductivity_m_s"],
        aquifer_thickness_m=kw["aquifer_thickness_m"],
        aquifer_type=AquiferType[kw["aquifer_type"]],
        recharge_rate_mm_yr=kw["recharge_rate_mm_yr"],
        abstraction_rate_m3_yr=kw["abstraction_rate_m3_yr"],
        tds_mg_l=kw["tds_mg_l"],
        porosity=kw["porosity"],
        specific_yield=kw["specific_yield"],
    )
    return GroundwaterService().analyze(model_input)

_RUNNERS = {
    "groundwater-service": _run_groundwater_service,
"runoff-model": _run_runoff,
    "runoff-surface": _run_runoff,
    "groundwater-model": _run_groundwater,
}


@router.get("")
def list_water_tools() -> dict[str, Any]:
    """List all HyDroMa water tools with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_water_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa water tool: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_water_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa water tool with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa water tool: {model_id}")
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")
    try:
        kwargs = build_kwargs(spec, params)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid parameters: {exc}") from exc
    try:
        result = _RUNNERS[model_id](kwargs)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=f"tool rejected inputs: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - explicit failure, never silent
        raise HTTPException(status_code=500, detail=f"tool execution failed: {exc}") from exc
    return {"id": model_id, "result": jsonable(result)}
