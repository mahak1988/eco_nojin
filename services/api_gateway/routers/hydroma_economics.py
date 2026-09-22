"""HyDroMa economics-tools API (NPV/payback, costing, revenue, ROI,
employment, risk).

Endpoints
---------
GET  /api/v1/hydroma/economics          -> metadata
GET  /api/v1/hydroma/economics/{id}     -> one tool's metadata
POST /api/v1/hydroma/economics/{id}/run -> execute (pure compute)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.economics.analysis import calculate_npv, calculate_payback
from engine.hydroma.economics.costing import calculate_agricultural_cost
from engine.hydroma.economics.employment import estimate_direct_employment
from engine.hydroma.economics.revenue import calculate_agricultural_revenue
from engine.hydroma.economics.risk import assess_market_price_risk, assess_yield_risk
from engine.hydroma.economics.roi import calculate_financial_metrics
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/economics", tags=["hydroma-economics"])

_SPECS: list[dict[str, Any]] = [
    {
        "id": "econ-analysis",
        "name_en": "Project economic analysis",
        "description": "NPV (discounted cashflows) and simple payback period.",
        "reference": "FAO Investment Centre",
        "params": [
            {
                "name": "cashflows",
                "label": "Cashflows (year 0 first)",
                "unit": "",
                "kind": "list_float",
                "default": [-1000, 300, 400, 500, 600],
            },
            {
                "name": "discount_rate",
                "label": "Discount rate",
                "unit": "",
                "kind": "float",
                "default": 0.1,
            },
        ],
    },
    {
        "id": "econ-costing",
        "name_en": "Costing engine",
        "description": "Agricultural production cost breakdown per hectare and total.",
        "reference": "HyDroMa",
        "params": [
            {
                "name": "area_hectares",
                "label": "Area",
                "unit": "ha",
                "kind": "float",
                "default": 10.0,
            },
            {"name": "crop_type", "label": "Crop", "unit": "", "kind": "str", "default": "wheat"},
            {
                "name": "labor_hours_per_hectare",
                "label": "Labor hours/ha",
                "unit": "h",
                "kind": "float",
                "default": 80.0,
            },
            {
                "name": "labor_cost_per_hour",
                "label": "Labor cost/h",
                "unit": "",
                "kind": "float",
                "default": 0.5,
            },
            {
                "name": "seed_cost_per_hectare",
                "label": "Seed cost/ha",
                "unit": "",
                "kind": "float",
                "default": 500.0,
            },
            {
                "name": "fertilizer_cost_per_hectare",
                "label": "Fertilizer cost/ha",
                "unit": "",
                "kind": "float",
                "default": 800.0,
            },
            {
                "name": "machinery_cost_per_hectare",
                "label": "Machinery cost/ha",
                "unit": "",
                "kind": "float",
                "default": 600.0,
            },
            {
                "name": "land_rent_per_hectare",
                "label": "Land rent/ha",
                "unit": "",
                "kind": "float",
                "default": 0.0,
            },
            {
                "name": "other_variable_costs_per_hectare",
                "label": "Other variable costs/ha",
                "unit": "",
                "kind": "float",
                "default": 0.0,
            },
        ],
    },
    {
        "id": "econ-revenue",
        "name_en": "Revenue engine",
        "description": "Agricultural revenue with quality and market-access factors.",
        "reference": "HyDroMa",
        "params": [
            {
                "name": "area_hectares",
                "label": "Area",
                "unit": "ha",
                "kind": "float",
                "default": 10.0,
            },
            {
                "name": "yield_ton_per_ha",
                "label": "Yield",
                "unit": "t/ha",
                "kind": "float",
                "default": 5.0,
            },
            {
                "name": "market_price_per_ton",
                "label": "Market price",
                "unit": "/t",
                "kind": "float",
                "default": 300.0,
            },
            {
                "name": "quality_factor",
                "label": "Quality factor",
                "unit": "",
                "kind": "float",
                "default": 1.0,
            },
            {
                "name": "market_access_factor",
                "label": "Market access",
                "unit": "",
                "kind": "float",
                "default": 1.0,
            },
        ],
    },
    {
        "id": "econ-roi",
        "name_en": "NPV / IRR / payback",
        "description": "Full financial metrics from investment, cashflows and lifetime.",
        "reference": "HyDroMa",
        "params": [
            {
                "name": "initial_investment",
                "label": "Initial investment",
                "unit": "",
                "kind": "float",
                "default": 10000.0,
            },
            {
                "name": "cash_flows",
                "label": "Annual cashflows",
                "unit": "",
                "kind": "list_float",
                "default": [3000, 3500, 4000, 4500],
            },
            {
                "name": "discount_rate",
                "label": "Discount rate",
                "unit": "",
                "kind": "float",
                "default": 0.1,
            },
            {
                "name": "project_lifetime_years",
                "label": "Lifetime",
                "unit": "year",
                "kind": "int",
                "default": 4,
            },
            {
                "name": "salvage_value",
                "label": "Salvage value",
                "unit": "",
                "kind": "float",
                "default": 0.0,
            },
        ],
    },
    {
        "id": "econ-employment",
        "name_en": "Employment generation",
        "description": "Direct employment estimate for an activity type and scale.",
        "reference": "HyDroMa",
        "params": [
            {
                "name": "activity_type",
                "label": "Activity",
                "unit": "",
                "kind": "str",
                "default": "nursery",
            },
            {
                "name": "scale_of_activity",
                "label": "Scale",
                "unit": "",
                "kind": "float",
                "default": 10.0,
            },
            {
                "name": "employment_intensity_per_unit",
                "label": "Jobs per unit",
                "unit": "",
                "kind": "float",
                "default": 0.5,
            },
            {
                "name": "job_type",
                "label": "Job type",
                "unit": "",
                "kind": "select",
                "default": "full_time_equivalent",
                "options": ["full_time_equivalent", "seasonal", "part_time"],
            },
            {
                "name": "duration_months",
                "label": "Duration",
                "unit": "month",
                "kind": "float",
                "default": 12.0,
            },
        ],
    },
    {
        "id": "econ-risk",
        "name_en": "Financial risk assessment",
        "description": "Market-price risk (VaR-style) plus yield risk for a production area.",
        "reference": "HyDroMa",
        "params": [
            {
                "name": "base_price",
                "label": "Base price",
                "unit": "",
                "kind": "float",
                "default": 300.0,
            },
            {
                "name": "volatility",
                "label": "Price volatility",
                "unit": "",
                "kind": "float",
                "default": 0.2,
            },
            {
                "name": "time_horizon_years",
                "label": "Horizon",
                "unit": "year",
                "kind": "int",
                "default": 5,
            },
            {
                "name": "confidence_level",
                "label": "Confidence level",
                "unit": "",
                "kind": "float",
                "default": 0.05,
            },
            {
                "name": "expected_yield",
                "label": "Expected yield",
                "unit": "t/ha",
                "kind": "float",
                "default": 5.0,
            },
            {
                "name": "yield_std_dev",
                "label": "Yield std dev",
                "unit": "t/ha",
                "kind": "float",
                "default": 0.8,
            },
            {
                "name": "area_hectares",
                "label": "Area",
                "unit": "ha",
                "kind": "float",
                "default": 10.0,
            },
            {
                "name": "price_per_unit",
                "label": "Price per unit",
                "unit": "",
                "kind": "float",
                "default": 300.0,
            },
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}


def _run_econ_analysis(kw: dict[str, Any]) -> dict[str, Any]:
    return {
        "npv": calculate_npv(kw["cashflows"], kw["discount_rate"]),
        "payback_years": calculate_payback(kw["cashflows"]),
    }


def _run_econ_costing(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_agricultural_cost(**kw)


def _run_econ_revenue(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_agricultural_revenue(**kw)


def _run_econ_roi(kw: dict[str, Any]) -> dict[str, Any]:
    return calculate_financial_metrics(**kw)


def _run_econ_employment(kw: dict[str, Any]) -> dict[str, Any]:
    return estimate_direct_employment(**kw)


def _run_econ_risk(kw: dict[str, Any]) -> dict[str, Any]:
    return {
        "market_price_risk": assess_market_price_risk(
            base_price=kw["base_price"],
            volatility=kw["volatility"],
            time_horizon_years=int(kw["time_horizon_years"]),
            confidence_level=kw["confidence_level"],
        ),
        "yield_risk": assess_yield_risk(
            expected_yield=kw["expected_yield"],
            yield_std_dev=kw["yield_std_dev"],
            area_hectares=kw["area_hectares"],
            price_per_unit=kw["price_per_unit"],
            confidence_level=kw["confidence_level"],
        ),
    }


_RUNNERS = {
    "econ-analysis": _run_econ_analysis,
    "econ-costing": _run_econ_costing,
    "econ-revenue": _run_econ_revenue,
    "econ-roi": _run_econ_roi,
    "econ-employment": _run_econ_employment,
    "econ-risk": _run_econ_risk,
}


@router.get("")
def list_economics_tools() -> dict[str, Any]:
    """List all HyDroMa economics tools with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_economics_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa economics tool: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_economics_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa economics tool with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa economics tool: {model_id}")
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
