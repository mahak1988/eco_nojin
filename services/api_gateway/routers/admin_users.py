"""Admin Users Router - User management endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import models
from database.hub import hub
from services.api_gateway.auth import require_user_admin

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

    model_config = ConfigDict(from_attributes=True)


class UserBulkAction(BaseModel):
    user_ids: list[str]
    action: str  # "block" | "unblock"


def _user_response(user: models.User) -> UserResponse:
    """Serialize a user row for the wire.

    ``User.created_at`` is a ``DateTime`` column and pydantic v2 does not
    coerce a datetime into a ``str`` field, so returning the ORM rows
    directly raised ``ResponseValidationError`` (HTTP 500) on every row —
    the endpoint only looked healthy while the table was empty. The
    conversion is done here, once, in one place.
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        country=user.country,
        city=user.city,
        language=user.language,
        role=user.role,
        is_email_verified=bool(user.is_email_verified),
        is_active=bool(user.is_active),
        two_factor_enabled=bool(user.two_factor_enabled),
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.get("", response_model=list[UserResponse])
async def list_users(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: Annotated[Any, Depends(require_user_admin)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """List users with pagination (admin only)."""
    users = (
        db.query(models.User)
        .order_by(models.User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_user_response(user) for user in users]


@router.post("/bulk-action")
async def bulk_action_users(
    payload: UserBulkAction,
    current_user: Annotated[Any, Depends(require_user_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Bulk block/unblock users."""
    if payload.action not in ("block", "unblock"):
        raise HTTPException(400, "Action must be 'block' or 'unblock'")

    updated = 0
    for uid in payload.user_ids:
        user = db.query(models.User).filter(models.User.id == uid).first()
        if user:
            user.is_active = payload.action == "unblock"
            updated += 1

    db.commit()
    return {"updated": updated, "action": payload.action}


@router.post("/{user_id}/block")
async def block_user(
    user_id: str,
    current_user: Annotated[Any, Depends(require_user_admin)],
    db: Annotated[Session, Depends(get_db)],
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
    current_user: Annotated[Any, Depends(require_user_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Reactivate a user (audited)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = True
    db.commit()
    return {"message": f"User {user_id} unblocked"}
