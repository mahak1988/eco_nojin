"""Admin Models Router - Ollama/local model management endpoints."""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.api_gateway.auth import require_admin_with_mfa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["admin-models"])


class ModelResponse(BaseModel):
    name: str
    size: str
    modified_at: str
    digest: str
    family: Optional[str] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None
    running: bool = False


class ModelActionRequest(BaseModel):
    name: str


# Mock model store (replace with actual Ollama client)
MODEL_STORE = {
    "qwen3:4b": {
        "name": "qwen3:4b",
        "size": "2.6 GB",
        "modified_at": "2024-01-15T10:30:00Z",
        "digest": "sha256:abc123...",
        "family": "qwen",
        "parameter_size": "4B",
        "quantization_level": "Q4_K_M",
        "running": True,
    },
    "qwen2.5-coder:3b": {
        "name": "qwen2.5-coder:3b",
        "size": "1.9 GB",
        "modified_at": "2024-01-10T14:20:00Z",
        "digest": "sha256:def456...",
        "family": "qwen",
        "parameter_size": "3B",
        "quantization_level": "Q4_K_M",
        "running": False,
    },
    "gemma3:4b": {
        "name": "gemma3:4b",
        "size": "2.4 GB",
        "modified_at": "2024-02-01T09:15:00Z",
        "digest": "sha256:ghi789...",
        "family": "gemma",
        "parameter_size": "4B",
        "quantization_level": "Q4_K_M",
        "running": False,
    },
}


@router.get("", response_model=List[ModelResponse])
async def list_models(
    current_user=Depends(require_admin_with_mfa),
):
    """List all available Ollama models."""
    return list(MODEL_STORE.values())


@router.get("/{name}", response_model=ModelResponse)
async def get_model(
    name: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Get model details."""
    if name not in MODEL_STORE:
        raise HTTPException(404, f"Model '{name}' not found")
    return MODEL_STORE[name]


@router.post("/{name}/pull")
async def pull_model(
    name: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Pull/download a model from Ollama registry."""
    # Mock - would call Ollama API
    return {"message": f"Pulling model '{name}'... (mock)"}


@router.post("/{name}/stop")
async def stop_model(
    name: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Unload a model from memory."""
    if name not in MODEL_STORE:
        raise HTTPException(404, f"Model '{name}' not found")
    MODEL_STORE[name]["running"] = False
    return {"message": f"Model '{name}' stopped"}


@router.post("/{name}/load")
async def load_model(
    name: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Load a model into memory."""
    if name not in MODEL_STORE:
        raise HTTPException(404, f"Model '{name}' not found")
    MODEL_STORE[name]["running"] = True
    return {"message": f"Model '{name}' loaded"}


@router.delete("/{name}")
async def delete_model(
    name: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Delete a model from local storage."""
    if name not in MODEL_STORE:
        raise HTTPException(404, f"Model '{name}' not found")
    del MODEL_STORE[name]
    return {"message": f"Model '{name}' deleted"}