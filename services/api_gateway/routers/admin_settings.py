"""Admin Settings Router - Settings management endpoints."""

from __future__ import annotations

import logging
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.api_gateway.auth import require_admin_with_mfa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["admin-settings"])


class SettingResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    is_secret: bool = False
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class SettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None


# In-memory settings store (replace with actual database)
SETTINGS_STORE = {}


@router.get("", response_model=List[SettingResponse])
async def list_settings(
    prefix: Optional[str] = None,
    current_user=Depends(require_admin_with_mfa),
):
    """List all settings."""
    settings = []
    for key, value in SETTINGS_STORE.items():
        if prefix and not key.startswith(prefix):
            continue
        settings.append(SettingResponse(
            key=key,
            value="***" if "secret" in key.lower() or "key" in key.lower() or "password" in key.lower() else str(value.get("value", "")),
            description=value.get("description"),
            is_secret="secret" in key.lower() or "key" in key.lower() or "password" in key.lower(),
            updated_at=value.get("updated_at"),
            updated_by=value.get("updated_by"),
        ))
    return settings


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Get a specific setting."""
    if key not in SETTINGS_STORE:
        raise HTTPException(404, "Setting not found")
    value = SETTINGS_STORE[key]
    return SettingResponse(
        key=key,
        value=value.get("value", ""),
        description=value.get("description"),
        is_secret="secret" in key.lower() or "key" in key.lower() or "password" in key.lower(),
        updated_at=value.get("updated_at"),
        updated_by=value.get("updated_by"),
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    payload: SettingUpdate,
    current_user=Depends(require_admin_with_mfa),
):
    """Update a setting."""
    from datetime import UTC, datetime
    SETTINGS_STORE[key] = {
        "value": payload.value,
        "description": payload.description,
        "updated_at": datetime.now(UTC).isoformat(),
        "updated_by": "admin",
    }
    return SettingResponse(
        key=key,
        value=payload.value,
        description=payload.description,
        is_secret="secret" in key.lower() or "key" in key.lower() or "password" in key.lower(),
        updated_at=SETTINGS_STORE[key]["updated_at"],
        updated_by="admin",
    )


@router.delete("/{key}")
async def delete_setting(
    key: str,
    current_user=Depends(require_admin_with_mfa),
):
    """Delete a setting."""
    if key not in SETTINGS_STORE:
        raise HTTPException(404, "Setting not found")
    del SETTINGS_STORE[key]
    return {"message": "Setting deleted"}


@router.post("/bulk")
async def bulk_update_settings(
    settings: dict[str, Any],
    current_user=Depends(require_admin_with_mfa),
):
    """Bulk update settings."""
    from datetime import UTC, datetime
    for key, value in settings.items():
        SETTINGS_STORE[key] = {
            "value": value,
            "updated_at": datetime.now(UTC).isoformat(),
            "updated_by": "admin",
        }
    return {"updated": len(settings)}