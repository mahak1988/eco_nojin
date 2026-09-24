"""Admin Bots Router - Bot management endpoints."""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.api_gateway.auth import require_admin_with_mfa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["admin-bots"])


class BotStatusResponse(BaseModel):
    key: str
    name: str
    enabled: bool
    platform: str
    status: str
    last_activity: Optional[str] = None
    message_count: int = 0


class BotToggleRequest(BaseModel):
    enabled: bool


# Mock bot registry (replace with actual bot manager)
BOT_REGISTRY = {
    "telegram": {"key": "telegram", "name": "Telegram Bot", "enabled": True, "platform": "telegram", "status": "running"},
    "eitaa": {"key": "eitaa", "name": "Eitaa Bot", "enabled": False, "platform": "eitaa", "status": "stopped"},
    "bale": {"key": "bale", "name": "Bale Bot", "enabled": False, "platform": "bale", "status": "stopped"},
    "rubika": {"key": "rubika", "name": "Rubika Bot", "enabled": False, "platform": "rubika", "status": "stopped"},
}


@router.get("", response_model=List[BotStatusResponse])
async def list_bots(
    current_user=Depends(require_admin_with_mfa),
):
    """List all bot statuses."""
    return list(BOT_REGISTRY.values())


@router.post("/{key}/toggle", response_model=BotStatusResponse)
async def toggle_bot(
    key: str,
    payload: BotToggleRequest,
    current_user=Depends(require_admin_with_mfa),
):
    """Toggle bot enabled state."""
    if key not in BOT_REGISTRY:
        raise HTTPException(404, f"Bot '{key}' not found")

    BOT_REGISTRY[key]["enabled"] = payload.enabled
    BOT_REGISTRY[key]["status"] = "running" if payload.enabled else "stopped"
    return BOT_REGISTRY[key]


@router.post("/{key}/restart", response_model=BotStatusResponse)
async def restart_bot(
    key: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Restart a bot."""
    if key not in BOT_REGISTRY:
        raise HTTPException(404, f"Bot '{key}' not found")

    BOT_REGISTRY[key]["status"] = "restarting"
    # Actual restart logic would go here
    BOT_REGISTRY[key]["status"] = "running"
    return BOT_REGISTRY[key]