"""Sponsor admin API.

Modelled on services/api_gateway/routers/admin_*.py: an `APIRouter` with a
`require_admin` dependency, mounted under /api/v1/admin.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.sponsors.models import SlotPlacement, SponsorTier
from services.sponsors.policy import PolicyViolation
from services.sponsors.service import SponsorshipNotFound, SponsorshipService

router = APIRouter(prefix="/api/v1/admin/sponsors", tags=["Admin: Sponsors"])


def get_db():
    from database.hub import hub

    with hub.get_session() as session:
        yield session


async def require_admin() -> str:
    """Placeholder replaced at wiring time by the gateway's real dependency.

    Kept as a local symbol so this router can be imported and tested without
    pulling in the whole auth stack.
    """
    from fastapi import HTTPException as _HTTPException

    raise _HTTPException(status_code=501, detail="admin auth not wired")


class SponsorshipCreate(BaseModel):
    sponsor_name: str = Field(min_length=2, max_length=200)
    sponsor_url: str = Field(max_length=500)
    amount: Decimal = Field(gt=0)
    starts_on: date
    ends_on: date
    placement: SlotPlacement
    tier: SponsorTier = SponsorTier.PAGE
    sponsor_name_fa: str | None = None
    logo_url: str | None = None
    tagline: str | None = None
    tagline_fa: str | None = None
    currency: str = "USD"
    is_project_funder: bool = False
    is_revenue_source_funder: bool = False
    #: Sector check happens in policy; a forbidden value is refused, not flagged.
    category: str | None = None
    #: The route this sponsorship will appear on, checked against the
    #: protected-prefix list.
    placement_path: str = ""
    internal_notes: str | None = None


class SponsorshipOut(BaseModel):
    id: str
    sponsor_name: str
    status: str
    placement: str
    amount: str
    currency: str
    starts_on: date
    ends_on: date
    green_claims_reviewed_at: str | None = None


@router.get("", response_model=list[SponsorshipOut])
async def list_all(
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    from sqlalchemy import select

    from services.sponsors.models import Sponsorship

    rows = db.execute(select(Sponsorship).order_by(Sponsorship.created_at)).scalars()
    return [
        SponsorshipOut(
            id=s.id,
            sponsor_name=s.sponsor_name,
            status=str(s.status),
            placement=str(s.placement),
            amount=str(s.amount),
            currency=s.currency,
            starts_on=s.starts_on,
            ends_on=s.ends_on,
            green_claims_reviewed_at=(
                s.green_claims_reviewed_at.isoformat() if s.green_claims_reviewed_at else None
            ),
        )
        for s in rows
    ]


@router.post("", response_model=SponsorshipOut, status_code=201)
async def create(
    payload: SponsorshipCreate,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    if payload.ends_on <= payload.starts_on:
        raise HTTPException(status_code=422, detail="ends_on must be after starts_on")
    service = SponsorshipService(db)
    try:
        sponsor = service.create(**payload.model_dump())
    except PolicyViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    db.commit()
    return SponsorshipOut(
        id=sponsor.id,
        sponsor_name=sponsor.sponsor_name,
        status=str(sponsor.status),
        placement=str(sponsor.placement),
        amount=str(sponsor.amount),
        currency=sponsor.currency,
        starts_on=sponsor.starts_on,
        ends_on=sponsor.ends_on,
    )


@router.post("/{sponsor_id}/activate", response_model=SponsorshipOut)
async def activate(
    sponsor_id: str,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    service = SponsorshipService(db)
    try:
        sponsor = service.activate(sponsor_id)
    except SponsorshipNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    db.commit()
    return SponsorshipOut(
        id=sponsor.id,
        sponsor_name=sponsor.sponsor_name,
        status=str(sponsor.status),
        placement=str(sponsor.placement),
        amount=str(sponsor.amount),
        currency=sponsor.currency,
        starts_on=sponsor.starts_on,
        ends_on=sponsor.ends_on,
    )


@router.post("/{sponsor_id}/suspend", response_model=SponsorshipOut)
async def suspend(
    sponsor_id: str,
    reason: str,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    service = SponsorshipService(db)
    try:
        sponsor = service.suspend(sponsor_id, reason)
    except SponsorshipNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return SponsorshipOut(
        id=sponsor.id,
        sponsor_name=sponsor.sponsor_name,
        status=str(sponsor.status),
        placement=str(sponsor.placement),
        amount=str(sponsor.amount),
        currency=sponsor.currency,
        starts_on=sponsor.starts_on,
        ends_on=sponsor.ends_on,
    )


@router.post("/{sponsor_id}/terminate", response_model=SponsorshipOut)
async def terminate(
    sponsor_id: str,
    reason: str,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    service = SponsorshipService(db)
    try:
        sponsor = service.terminate(sponsor_id, reason)
    except SponsorshipNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return SponsorshipOut(
        id=sponsor.id,
        sponsor_name=sponsor.sponsor_name,
        status=str(sponsor.status),
        placement=str(sponsor.placement),
        amount=str(sponsor.amount),
        currency=sponsor.currency,
        starts_on=sponsor.starts_on,
        ends_on=sponsor.ends_on,
    )


@router.post("/{sponsor_id}/green-review", response_model=SponsorshipOut)
async def green_review(
    sponsor_id: str,
    attested_by: str,
    db: Session = Depends(get_db),
    _admin: str = Depends(require_admin),
):
    service = SponsorshipService(db)
    try:
        sponsor = service.record_green_review(sponsor_id, attested_by)
    except SponsorshipNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return SponsorshipOut(
        id=sponsor.id,
        sponsor_name=sponsor.sponsor_name,
        status=str(sponsor.status),
        placement=str(sponsor.placement),
        amount=str(sponsor.amount),
        currency=sponsor.currency,
        starts_on=sponsor.starts_on,
        ends_on=sponsor.ends_on,
        green_claims_reviewed_at=sponsor.green_claims_reviewed_at.isoformat(),
    )
