"""Phase 7: models API router (public — scientific models are open knowledge)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from services.api_gateway.errors import safe_detail_for_status
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
    """Expose only the user-facing availability of the optional surrogate."""
    from services.models.pinn_surrogate import status

    return {"available": status()["available"]}


@router.get("/cpp-status", response_model=dict)
def cpp_status():
    """C++20 native-core capability (single source of truth).

    This used to read a second, ctypes-based loader
    (``services/models/cpp_bridge.py``) that probed for a ``hydroma_core.dll``.
    That loader had no build path -- its source ``bindings/c_api.cpp`` is in no
    CMake target -- so it always reported ``available: false`` while ``/health``
    reported ``cpp_core: "ok"`` for the pybind11 module. Two endpoints answered
    the same question about the same capability with different numbers.

    Both now read ``engine.hydroma.cpp_bridge.backend_status()``, so the numbers
    cannot disagree.
    """
    from engine.hydroma.cpp_bridge import backend_status

    state = backend_status()
    return {
        "available": state["cpp_available"],
    }


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
def models_run(slug: str, params: dict[str, Any] = ...):
    """Run a model with validated parameters (honest errors, no fallbacks)."""
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")
    if get_model(slug) is None:
        raise HTTPException(status_code=404, detail=f"unknown model: {slug}")
    try:
        return run_model(slug, params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc
