"""Phase 7: models API router (public — scientific models are open knowledge)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from services.models.registry import get_model, list_models, model_card, run_model

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("", response_model=dict)
def models_index():
    """List all 22 models with fidelity badges (official/simplified/experimental)."""
    models = list_models()
    return {
        "count": len(models),
        "fidelity_counts": {
            "official": sum(1 for m in models if m["fidelity"] == "official"),
            "simplified": sum(1 for m in models if m["fidelity"] == "simplified"),
            "experimental": sum(1 for m in models if m["fidelity"] == "experimental"),
        },
        "models": models,
    }


@router.get("/pinn-status", response_model=dict)
def pinn_status():
    """PINN surrogate capability (PyTorch optional, honest)."""
    from services.models.pinn_surrogate import status

    return status()


@router.get("/cpp-status", response_model=dict)
def cpp_status():
    """C++20 parity bridge status (hot kernels)."""
    from services.models.cpp_bridge import status

    return status()


@router.get("/{slug}", response_model=dict)
def models_detail(slug: str):
    model = get_model(slug)
    if model is None:
        raise HTTPException(status_code=404, detail=f"unknown model: {slug}")
    return {
        "slug": model.slug,
        "name_fa": model.name_fa,
        "name_en": model.name_en,
        "domain": model.domain,
        "fidelity": model.fidelity,
        "reference": model.reference,
        "description": model.description,
        "validity": model_card(model.slug)["validity"],
        "limitations": model_card(model.slug)["limitations"],
        "params": [
            {
                "name": p.name,
                "label": p.label,
                "unit": p.unit,
                "default": p.default,
                "kind": p.kind,
            }
            for p in model.params
        ],
    }


@router.post("/{slug}/run", response_model=dict)
def models_run(slug: str, params: Dict[str, Any] = ...):
    """Run a model with validated parameters (honest errors, no fallbacks)."""
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")
    try:
        return run_model(slug, params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
