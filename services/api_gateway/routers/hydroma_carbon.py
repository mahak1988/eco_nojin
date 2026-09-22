"""HyDroMa carbon-tools API (project sequestration calculator).

Endpoints
---------
GET  /api/v1/hydroma/carbon          -> metadata
GET  /api/v1/hydroma/carbon/{id}     -> one tool's metadata
POST /api/v1/hydroma/carbon/{id}/run -> execute (pure compute)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.carbon.calculator import CarbonProjectType, calculate_carbon_sequestration
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/carbon", tags=["hydroma-carbon"])

_PROJECT_TYPES = [t.value for t in CarbonProjectType]

_SPECS: list[dict[str, Any]] = [
    {
        "id": "carbon-calculator",
        "name_en": "Carbon sequestration calculator",
        "description": "Sequestration for afforestation, soil-carbon, biochar and agroforestry projects.",
        "reference": "Verra VCS, Gold Standard, IPCC",
        "params": [
            {
                "name": "project_type",
                "label": "Project type",
                "unit": "",
                "kind": "select",
                "default": "afforestation",
                "options": _PROJECT_TYPES,
            },
            {"name": "area_ha", "label": "Area", "unit": "ha", "kind": "float", "default": 100.0},
            {
                "name": "duration_years",
                "label": "Duration",
                "unit": "year",
                "kind": "int",
                "default": 10,
            },
            {
                "name": "region",
                "label": "Region",
                "unit": "",
                "kind": "select",
                "default": "temperate",
                "options": ["temperate", "tropical"],
            },
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}


def _run_carbon_calculator(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_carbon_sequestration(
        CarbonProjectType(kw["project_type"]),
        kw["area_ha"],
        int(kw["duration_years"]),
        kw["region"],
    )


_RUNNERS = {
    "carbon-calculator": _run_carbon_calculator,
}


@router.get("")
def list_carbon_tools() -> dict[str, Any]:
    """List all HyDroMa carbon tools with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_carbon_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa carbon tool: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_carbon_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa carbon tool with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa carbon tool: {model_id}")
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"tool execution failed: {exc}") from exc
    return {"id": model_id, "result": jsonable(result)}
