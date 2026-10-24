"""Dispute API — POST /api/v1/disputes ... (auth: require_user on writes/list)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from services.api_gateway.auth import require_user
from services.api_gateway.errors import safe_detail_for_status
from services.dispute_resolution.service import DisputeService

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])


def get_db():
    with hub.get_session() as session:
        yield session


class DisputeCreate(BaseModel):
    order_id: str = Field(min_length=1)
    complainant_id: str = Field(min_length=1)
    category: str
    description: str = Field(min_length=10)
    respondent_id: str | None = None
    marketplace_id: str | None = None


class DisputeResolve(BaseModel):
    resolved_by: str
    resolution: str = Field(min_length=5)
    outcome: str = "resolved"


@router.post("")
def create_dispute(
    payload: DisputeCreate, db: Annotated[Session, Depends(get_db)], user: Annotated[Any, Depends(require_user)]
) -> dict[str, Any]:
    """Open a dispute for an order (authenticated buyers/vendors)."""
    try:
        d = DisputeService(db).create(**payload.model_dump())
        return {"ok": True, "dispute": d.to_dict()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.get("")
def list_disputes(
    status: str | None = None,
    limit: int = 50,
    db: Annotated[Session, Depends(get_db)] = None,
    user: Annotated[Any, Depends(require_user)] = None,
) -> dict[str, Any]:
    items = DisputeService(db).list(status=status, limit=limit)
    return {"count": len(items), "disputes": [d.to_dict() for d in items]}


@router.get("/{dispute_id}")
def get_dispute(
    dispute_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
) -> dict[str, Any]:
    """
    Read one dispute by id.

    The ``require_user`` dependency was missing here while both neighbours gate:
    ``create_dispute`` at :39 and ``list_disputes`` at :54. That left an
    unauthenticated read of any dispute record by guessing or enumerating an id,
    and a dispute carries the parties, the evidence and the money in dispute.
    The module docstring above already stated the intent — "auth: require_user on
    writes/list" — so this is a gap in a surface that was meant to be gated, not
    a deliberate public read.
    """
    svc = DisputeService(db)
    try:
        d = svc.get(dispute_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(exc, 404)) from exc
    return {"dispute": d.to_dict(), "events": [e.id for e in svc.events(dispute_id)]}


@router.post("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str,
    payload: DisputeResolve,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Any, Depends(require_user)],
) -> dict[str, Any]:
    try:
        d = DisputeService(db).resolve(
            dispute_id, payload.resolved_by, payload.resolution, payload.outcome
        )
        return {"ok": True, "dispute": d.to_dict()}
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc


@router.post("/{dispute_id}/escalate")
def escalate_dispute(
    dispute_id: str, actor: str, db: Annotated[Session, Depends(get_db)], user: Annotated[Any, Depends(require_user)]
) -> dict[str, Any]:
    try:
        d = DisputeService(db).escalate(dispute_id, actor)
        return {"ok": True, "dispute": d.to_dict()}
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(exc, 400)) from exc
