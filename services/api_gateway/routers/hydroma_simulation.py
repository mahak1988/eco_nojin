"""HyDroMa simulation-tools API (Sobol sensitivity on the Ishigami function).

Endpoints
---------
GET  /api/v1/hydroma/simulation          -> metadata
GET  /api/v1/hydroma/simulation/{id}     -> one tool's metadata
POST /api/v1/hydroma/simulation/{id}/run -> execute (pure compute)
"""

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.simulation.calibration import ishigami, sensitivity_of_metric
from engine.hydroma.simulation.scenarios import SCENARIOS
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/simulation", tags=["hydroma-simulation"])

_SPECS: list[dict[str, Any]] = [
    {
        "id": "sim-calibration",
        "name_en": "Sensitivity & uncertainty",
        "description": "Saltelli sampling + Sobol first/total-order indices "
        "(validated on the Ishigami test function).",
        "reference": "Saltelli 2010 (Sobol)",
        "params": [
            {"name": "a", "label": "Ishigami a", "unit": "", "kind": "float", "default": 7.0},
            {"name": "b", "label": "Ishigami b", "unit": "", "kind": "float", "default": 0.1},
            {"name": "n", "label": "Samples", "unit": "", "kind": "int", "default": 2048},
            {"name": "seed", "label": "RNG seed", "unit": "", "kind": "int", "default": 42},
        ],
    },
    {
        "id": "sim-scenarios",
        "name_en": "Scenario matrices",
        "description": "Baseline / Medium / Intensive scenario parameters: CN reduction, C-factor and RUSLE P factor.",
        "reference": "HyDroMa scenario matrices (doc 28)",
        "params": [],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in _SPECS}


def _run_sim_calibration(kw: dict[str, Any]) -> dict[str, Any]:
    a = kw["a"]
    b = kw["b"]

    def metric(x):
        return ishigami(x, a=a, b=b)

    bounds = [(-math.pi, math.pi)] * 3
    return sensitivity_of_metric(metric, bounds, n=int(kw["n"]), seed=int(kw["seed"]))


def _run_sim_scenarios(_kw: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for name, sc in SCENARIOS.items():
        try:
            from dataclasses import asdict

            out[name] = asdict(sc)
        except TypeError:
            out[name] = {
                "name": getattr(sc, "name", name),
                "cn_change": getattr(sc, "cn_change", None),
                "c_factor_factor": getattr(sc, "c_factor_factor", None),
                "p_factor": getattr(sc, "p_factor", None),
            }
    return {"scenarios": out, "count": len(out)}


_RUNNERS = {
    "sim-scenarios": _run_sim_scenarios,
    "sim-calibration": _run_sim_calibration,
}


@router.get("")
def list_simulation_tools() -> dict[str, Any]:
    """List all HyDroMa simulation tools with their parameter metadata."""
    return {"count": len(_SPECS), "models": _SPECS}


@router.get("/{model_id}")
def get_simulation_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa simulation tool: {model_id}")
    return spec


@router.post("/{model_id}/run")
def run_simulation_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run a HyDroMa simulation tool with validated inputs (pure computation)."""
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown HyDroMa simulation tool: {model_id}")
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
