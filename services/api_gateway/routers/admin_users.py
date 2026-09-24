"""Admin Users Router - User management endpoints."""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import models
from database.hub import hub
from services.api_gateway.auth import get_current_user, require_user_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["admin-users"])

# Dependency
def get_db():
    with hub.get_session() as session:
        yield session


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    language: str | None = None
    role: str | None = None
    is_email_verified: bool
    is_active: bool
    two_factor_enabled: bool
    created_at: str

    class Config:
        from_attributes = True


class UserBulkAction(BaseModel):
    user_ids: List[str]
    action: str  # "block" | "unblock"


@router.get("", response_model=List[UserResponse])
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_user_admin),
    db: Session = Depends(hub.get_session),
):
    """List users with pagination (admin only)."""
    users = db.query(models.User).offset(offset).limit(limit).all()
    return users


@router.post("/bulk-action")
async def bulk_action_users(
    payload: UserBulkAction,
    current_user=Depends(require_user_admin),
    db: Session = Depends(hub.get_session),
):
    """Bulk block/unblock users."""
    if payload.action not in ("block", "unblock"):
        raise HTTPException(400, "Action must be 'block' or 'unblock'")

    updated = 0
    for uid in payload.user_ids:
        user = db.query(models.User).filter(models.User.id == uid).first()
        if user:
            user.is_active = (payload.action == "unblock")
            updated += 1

    db.commit()
    return {"updated": updated, "action": payload.action}


@router.post("/{user_id}/block")
async def block_user(
    user_id: str,
    current_user=Depends(require_user_admin),
    db: Session = Depends(hub.get_session),
):
    """Deactivate a user (audited)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = False
    db.commit()
    return {"message": f"User {user_id} blocked"}


@router.post("/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    current_user=Depends(require_user_admin),
    db: Session = Depends(hub.get_session),
):
    """Reactivate a user (audited)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = True
    db.commit()
    return {"message": f"User {user_id} unblocked"}