"""HyDroMa soil-tools API.

Exposes the soil-science modules from ``engine.hydroma.soil`` through a
uniform, stateless JSON API so the dashboard soil model pages can run them
live: texture triangle, taxonomy, water retention, pedotransfer, physics,
chemistry, salinity, health and recommendations.

Endpoints
---------
GET  /api/v1/hydroma/soil          -> metadata for every soil tool
GET  /api/v1/hydroma/soil/{id}     -> metadata for one soil tool
POST /api/v1/hydroma/soil/{id}/run -> execute one tool (pure compute)

Pure, side-effect-free computations: nothing is written to the database and
no personal data is accepted. Errors are explicit (no silent fallbacks).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.soil.chemistry import calculate_cec, calculate_esp, calculate_sar
from engine.hydroma.soil.health import calculate_soil_health_index
from engine.hydroma.soil.pedotransfer import estimate_soil_parameters
from engine.hydroma.soil.physics import available_water_capacity, water_content_at
from engine.hydroma.soil.recommendations import generate_recommendations
from engine.hydroma.soil.salinity import (
    calculate_leaching_requirement,
    calculate_sodic_soil_amendment,
    classify_salinity,
)
from engine.hydroma.soil.taxonomy import get_soil_taxonomy
from engine.hydroma.soil.texture import (
    TEXTURE_NAMES,
    classify_texture,
    is_clayey,
    is_sandy,
    is_silty,
    texture_triangle_coords,
)
from engine.hydroma.soil.water_retention import (
    calculate_water_retention_curve,
    get_vg_parameters,
)
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/soil", tags=["hydroma-soil"])

_TEXTURES = [
    "clay",
    "silty_clay",
    "sandy_clay",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_loam",
    "loamy_sand",
    "sand",
]

_SPECS: list[dict[str, Any]] = [
    {
        "id": "soil-texture",
        "name_en": "USDA texture triangle",
        "description": "12-class texture classification from sand/silt/clay.",
        "reference": "USDA NRCS Soil Texture Triangle",
        "params": [
            {"name": "sand", "label": "Sand", "unit": "%", "kind": "float", "default": 40.0},
            {"name": "silt", "label": "Silt", "unit": "%", "kind": "float", "default": 40.0},
            {"name": "clay", "label": "Clay", "unit": "%", "kind": "float", "default": 20.0},
        ],
    },
    {
        "id": "soil-taxonomy",
        "name_en": "Soil taxonomy",
        "description": "USDA taxonomy classification with texture details.",
        "reference": "Keys to Soil Taxonomy 13th ed.",
        "params": [
            {"name": "clay", "label": "Clay", "unit": "%", "kind": "float", "default": 25.0},
            {"name": "silt", "label": "Silt", "unit": "%", "kind": "float", "default": 35.0},
            {"name": "sand", "label": "Sand", "unit": "%", "kind": "float", "default": 40.0},
            {"name": "organic_matter", "label": "Organic matter", "unit": "%", "kind": "float", "default": 2.0},
            {"name": "ph", "label": "pH", "unit": "", "kind": "float", "default": 6.5},
            {"name": "cec", "label": "CEC", "unit": "meq/100g", "kind": "float", "default": 20.0, "optional": True},
        ],
    },
    {
        "id": "soil-water-retention",
        "name_en": "Soil water retention",
        "description": "van Genuchten water-retention curve and parameters.",
        "reference": "van Genuchten 1980; Mualem 1976",
        "params": [
            {"name": "texture", "label": "Texture", "unit": "", "kind": "select", "default": "loam", "options": _TEXTURES},
        ],
    },
    {
        "id": "pedotransfer",
        "name_en": "Pedotransfer functions",
        "description": "Hydraulic estimates (theta_33, theta_1500, AWC, Ks) from texture and organic matter.",
        "reference": "Saxton & Rawls 2006",
        "params": [
            {"name": "sand_pct", "label": "Sand", "unit": "%", "kind": "float", "default": 40.0},
            {"name": "clay_pct", "label": "Clay", "unit": "%", "kind": "float", "default": 25.0},
            {"name": "om_pct", "label": "Organic matter", "unit": "%", "kind": "float", "default": 1.5},
        ],
    },
    {
        "id": "soil-physics",
        "name_en": "Soil physics",
        "description": "Available water capacity and water content at a matric potential.",
        "reference": "Brooks-Corey 1964; Campbell 1974",
        "params": [
            {"name": "texture", "label": "Texture", "unit": "", "kind": "select", "default": "loam", "options": _TEXTURES},
            {"name": "matric_potential_cm", "label": "Matric potential", "unit": "cm", "kind": "float", "default": -33.0},
        ],
    },
    {
        "id": "soil-chemistry",
        "name_en": "Soil chemistry",
        "description": "CEC, ESP and SAR from soil and water properties.",
        "reference": "Brady & Weil 2017",
        "params": [
            {"name": "clay", "label": "Clay", "unit": "%", "kind": "float", "default": 25.0},
            {"name": "organic_matter", "label": "Organic matter", "unit": "%", "kind": "float", "default": 2.0},
            {"name": "ph", "label": "pH", "unit": "", "kind": "float", "default": 6.5},
            {"name": "exchangeable_na", "label": "Exchangeable Na", "unit": "meq/100g", "kind": "float", "default": 2.0},
            {"name": "cec", "label": "CEC (for ESP)", "unit": "meq/100g", "kind": "float", "default": 20.0},
            {"name": "na", "label": "Na (water)", "unit": "meq/L", "kind": "float", "default": 10.0},
            {"name": "ca", "label": "Ca (water)", "unit": "meq/L", "kind": "float", "default": 20.0},
            {"name": "mg", "label": "Mg (water)", "unit": "meq/L", "kind": "float", "default": 5.0},
        ],
    },
    {
        "id": "soil-salinity",
        "name_en": "Soil salinity",
        "description": "Salinity classification, leaching requirement and sodic amendment.",
        "reference": "USDA Handbook 60; FAO-29",
        "params": [
            {"name": "ec", "label": "Soil EC", "unit": "dS/m", "kind": "float", "default": 4.0},
            {"name": "ec_soil", "label": "EC (leaching)", "unit": "dS/m", "kind": "float", "default": 4.0},
            {"name": "ec_water", "label": "Irrigation EC", "unit": "dS/m", "kind": "float", "default": 1.0},
            {"name": "esp", "label": "ESP", "unit": "%", "kind": "float", "default": 10.0},
            {"name": "soil_depth", "label": "Soil depth", "unit": "m", "kind": "float", "default": 0.3},
            {"name": "bulk_density", "label": "Bulk density", "unit": "g/cm3", "kind": "float", "default": 1.4},
        ],
    },
    {
        "id": "soil-health",
        "name_en": "Soil health",
        "description": "Comprehensive soil health index (pH, OM, N, P, K, CEC, texture).",
        "reference": "USDA NRCS 2023",
        "params": [
            {"name": "ph", "label": "pH", "unit": "", "kind": "float", "default": 6.5},
            {"name": "organic_matter", "label": "Organic matter", "unit": "%", "kind": "float", "default": 2.0},
            {"name": "nitrogen", "label": "Nitrogen", "unit": "mg/kg", "kind": "float", "default": 50.0},
            {"name": "phosphorus", "label": "Phosphorus", "unit": "mg/kg", "kind": "float", "default": 20.0},
            {"name": "potassium", "label": "Potassium", "unit": "mg/kg", "kind": "float", "default": 150.0},
            {"name": "cec", "label": "CEC", "unit": "meq/100g", "kind": "float", "default": 20.0, "optional": True},
            {"name": "texture", "label": "Texture", "unit": "", "kind": "select", "default": "loam", "options": _TEXTURES, "optional": True},
        ],
    },
    {
        "id": "soil-recommendations",
        "name_en": "Soil recommendations",
        "description": "Management recommendations from soil fertility test values.",
        "reference": "USDA NRCS 2023",
        "params": [
            {"name": "ph", "label": "pH", "unit": "", "kind": "float", "default": 6.5},
            {"name": "organic_matter", "label": "Organic matter", "unit": "%", "kind": "float", "default": 2.0},
            {"name": "nitrogen", "label": "Nitrogen", "unit": "mg/kg", "kind": "float", "default": 50.0},
            {"name": "phosphorus", "label": "Phosphorus", "unit": "mg/kg", "kind": "float", "default": 20.0},
            {"name": "potassium", "label": "Potassium", "unit": "mg/kg", "kind": "float", "default": 150.0},
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------

def _run_soil_texture(kw: dict[str, Any]) -> dict[str, Any]:
    texture = classify_texture(kw["sand"], kw["silt"], kw["clay"])
    x, y = texture_triangle_coords(kw["sand"], kw["silt"], kw["clay"])
    return {
        "texture": texture,
        "texture_name": TEXTURE_NAMES.get(texture, texture),
        "triangle_coords": {"x": x, "y": y},
        "is_sandy": is_sandy(texture),
        "is_clayey": is_clayey(texture),
        "is_silty": is_silty(texture),
    }


def _run_soil_taxonomy(kw: dict[str, Any]) -> dict[str, Any]:
    return get_soil_taxonomy(**kw)


def _run_soil_water_retention(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_water_retention_curve(kw["texture"])


def _run_pedotransfer(kw: dict[str, Any]) -> dict[str, Any]:
    return estimate_soil_parameters(**kw)


def _run_soil_physics(kw: dict[str, Any]) -> dict[str, Any]:
    return {
        "texture": kw["texture"],
        "available_water_capacity": available_water_capacity(kw["texture"]),
        "matric_potential_cm": kw["matric_potential_cm"],
        "water_content": water_content_at(kw["matric_potential_cm"], kw["texture"]),
        "vg_parameters": get_vg_parameters(kw["texture"]),
    }


def _run_soil_chemistry(kw: dict[str, Any]) -> dict[str, Any]:
    return {
        "cec": calculate_cec(kw["clay"], kw["organic_matter"], kw["ph"]),
        "esp": calculate_esp(kw["exchangeable_na"], kw["cec"]),
        "sar": calculate_sar(kw["na"], kw["ca"], kw["mg"]),
    }


def _run_soil_salinity(kw: dict[str, Any]) -> dict[str, Any]:
    return {
        "classification": classify_salinity(kw["ec"]),
        "leaching_requirement": calculate_leaching_requirement(kw["ec_soil"], kw["ec_water"]),
        "sodic_amendment": calculate_sodic_soil_amendment(kw["esp"], kw["soil_depth"], kw["bulk_density"]),
    }


def _run_soil_health(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_soil_health_index(**kw)


def _run_soil_recommendations(kw: dict[str, Any]) -> dict[str, Any]:
    return generate_recommendations(dict(kw))


_RUNNERS = {
    "soil-texture": _run_soil_texture,
    "soil-taxonomy": _run_soil_taxonomy,
    "soil-water-retention": _run_soil_water_retention,
    "pedotransfer": _run_pedotransfer,
    "soil-physics": _run_soil_physics,
    "soil-chemistry": _run_soil_chemistry,
    "soil-salinity": _run_soil_salinity,
    "soil-health": _run_soil_health,
    "soil-recommendations": _run_soil_recommendations,
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
def list_soil_tools() -> dict[str, Any]:
    """List all HyDroMa soil tools with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_soil_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa soil tool: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_soil_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa soil tool with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa soil tool: {model_id}")
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
