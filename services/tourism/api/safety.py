"""The tourism safety surface over HTTP (P8): departures, incidents, refunds.

The services exist since P8 (`services/tourism/departures.py`,
`safety_service.py`) and are migration-backed, but nothing mounted them — the
frontend measured the 404s and honestly disabled the flows. This router is the
missing half; it adds no business logic of its own.

Rules carried from the services (all pinned by their tests):

* a departure can only ever be **tighter** than the tour's ecological capacity;
* a safety-severity incident **closes the departure** until it is resolved;
* a refund is **reviewed before it is settled**, and the settlement names the
  finance reference — the money never moves here;
* a caller only ever reads **their own** refunds and incident reports, or
  everything when they carry an approver role;
* money figures are the server's strings, verbatim — and money values cross the
  wire as ``Decimal``, never binary floats.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_user
from services.api_gateway.errors import domain_detail
from services.tourism.api._roles import APPROVER_ROLES, require_tourism_approver
from services.tourism.departure_service import DepartureError, DepartureService
from services.tourism.incidents import IncidentSeverity
from services.tourism.safety_service import RefundError, TourismSafetyService

router = APIRouter(prefix="/api/v1/tourism", tags=["tourism"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


def _is_approver(user: User) -> bool:
    # The same approver set the tours router guards writes with: one source,
    # so "who may write" and "who may read across guests" cannot drift.
    return str(getattr(user, "role", "")) in APPROVER_ROLES


class DepartureCreate(BaseModel):
    departure_date: date
    capacity: int | None = Field(default=None, ge=1)
    price_override: Decimal | None = Field(default=None, gt=0)
    village_id: str | None = Field(default=None, max_length=100)


class RefundRequest(BaseModel):
    booking_id: str = Field(..., max_length=36)
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=2000)


class RefundReview(BaseModel):
    approve: bool
    note: str | None = Field(default=None, max_length=2000)


class RefundSettle(BaseModel):
    settlement_ref: str = Field(..., min_length=1, max_length=120)


class IncidentCreate(BaseModel):
    departure_id: str = Field(..., max_length=36)
    summary: str = Field(..., min_length=3, max_length=2000)
    severity: str = Field(default=IncidentSeverity.LOW.value, max_length=20)


class IncidentResolve(BaseModel):
    resolution: str = Field(..., min_length=3, max_length=2000)


# --------------------------------------------------------------------------
# departures
# --------------------------------------------------------------------------


@router.post("/tours/{tour_id}/departures", status_code=201)
async def create_departure(
    tour_id: str,
    payload: DepartureCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_tourism_approver)],
):
    service = DepartureService(db)
    try:
        departure = await service.create_departure(
            tour_id=tour_id,
            departure_date=payload.departure_date,
            capacity=payload.capacity,
            price_override=payload.price_override,
            village_id=payload.village_id,
        )
    except DepartureError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return _departure_view(departure)


@router.get("/tours/{tour_id}/departures")
async def list_departures(
    tour_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    limit: int = Query(default=50, ge=1, le=200),
):
    from sqlalchemy import select

    from services.tourism.departures import TourDeparture

    rows = (
        await db.execute(
            select(TourDeparture)
            .where(TourDeparture.tour_id == tour_id)
            .order_by(TourDeparture.departure_date)
            .limit(limit)
        )
    ).scalars().all()
    return {"items": [_departure_view(d) for d in rows], "count": len(rows)}


@router.get("/departures")
async def list_all_departures(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    village_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    from sqlalchemy import select

    from services.tourism.departures import TourDeparture
    from services.tourism.models import TourismBooking

    query = select(TourDeparture)
    if village_id:
        query = query.where(TourDeparture.village_id == village_id)
    if not _is_approver(user):
        # A plain caller sees the departures of tours they are booked on —
        # the global operational list is an approver's view.
        booked_tours = select(TourismBooking.tour_id).where(
            TourismBooking.guest_id == str(user.id)
        )
        query = query.where(TourDeparture.tour_id.in_(booked_tours))
    rows = (
        await db.execute(query.order_by(TourDeparture.departure_date).limit(limit))
    ).scalars().all()
    return {"items": [_departure_view(d) for d in rows], "count": len(rows)}


# --------------------------------------------------------------------------
# incidents
# --------------------------------------------------------------------------


@router.post("/incidents", status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = TourismSafetyService(db)
    try:
        incident = await service.report_incident(
            departure_id=payload.departure_id,
            reported_by=str(user.id),
            summary=payload.summary,
            severity=payload.severity,
        )
    except RefundError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return _incident_view(incident)


@router.get("/incidents")
async def list_incidents(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    departure_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    from sqlalchemy import select

    from services.tourism.incidents import TourIncident

    query = select(TourIncident)
    if departure_id:
        query = query.where(TourIncident.departure_id == departure_id)
    if not _is_approver(user):
        # A plain caller sees only the incidents they reported themselves;
        # the cross-village operational list is an approver's view.
        query = query.where(TourIncident.reported_by == str(user.id))
    rows = (
        await db.execute(query.order_by(TourIncident.reported_at.desc()).limit(limit))
    ).scalars().all()
    return {"items": [_incident_view(i) for i in rows], "count": len(rows)}


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    payload: IncidentResolve,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_tourism_approver)],
):
    service = TourismSafetyService(db)
    try:
        incident = await service.resolve_incident(
            incident_id, resolver_id=str(user.id), resolution=payload.resolution
        )
    except RefundError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return _incident_view(incident)


# --------------------------------------------------------------------------
# refunds
# --------------------------------------------------------------------------


@router.post("/refunds", status_code=201)
async def request_refund(
    payload: RefundRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = TourismSafetyService(db)
    try:
        refund = await service.request_refund(
            booking_id=payload.booking_id,
            requested_by=str(user.id),
            amount=payload.amount,
            reason=payload.reason,
        )
    except RefundError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return _refund_view(refund)


@router.get("/refunds")
async def list_refunds(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    booking_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    from sqlalchemy import select

    from services.tourism.incidents import TourRefund

    query = select(TourRefund)
    if booking_id:
        query = query.where(TourRefund.booking_id == booking_id)
    if not _is_approver(user):
        # A refund carries another guest's financial record: a plain caller
        # only ever lists their own requests.
        query = query.where(TourRefund.requested_by == str(user.id))
    rows = (
        await db.execute(query.order_by(TourRefund.requested_at.desc()).limit(limit))
    ).scalars().all()
    return {"items": [_refund_view(r) for r in rows], "count": len(rows)}


@router.post("/refunds/{refund_id}/review")
async def review_refund(
    refund_id: str,
    payload: RefundReview,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_tourism_approver)],
):
    service = TourismSafetyService(db)
    try:
        refund = await service.review_refund(
            refund_id, reviewer_id=str(user.id), approve=payload.approve, note=payload.note
        )
    except RefundError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return _refund_view(refund)


@router.post("/refunds/{refund_id}/settle")
async def settle_refund(
    refund_id: str,
    payload: RefundSettle,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_tourism_approver)],
):
    """Settlement only records the finance reference — the money moved in finance."""
    service = TourismSafetyService(db)
    try:
        refund = await service.settle_refund(refund_id, settlement_ref=payload.settlement_ref)
    except RefundError as exc:
        raise HTTPException(status_code=400, detail=domain_detail(exc, 400)) from exc
    return _refund_view(refund)


def _departure_view(departure) -> dict:
    return {
        "id": str(departure.id),
        "tour_id": departure.tour_id,
        "departure_date": departure.departure_date.isoformat(),
        "capacity": departure.capacity,
        "booked": departure.booked,
        "remaining": departure.remaining(),
        "price_override": str(departure.price_override) if departure.price_override else None,
        "status": departure.status,
        "village_id": departure.village_id,
    }


def _incident_view(incident) -> dict:
    return {
        "id": str(incident.id),
        "departure_id": incident.departure_id,
        "severity": incident.severity,
        "status": incident.status,
        "summary": incident.summary,
        "resolution": incident.resolution,
        "blocks_bookings": incident.blocks_bookings,
        "reported_by": incident.reported_by,
        "reported_at": incident.reported_at.isoformat(),
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
    }


def _refund_view(refund) -> dict:
    return {
        "id": str(refund.id),
        "booking_id": refund.booking_id,
        "amount": str(refund.amount),
        "currency": refund.currency,
        "reason": refund.reason,
        "status": refund.status,
        "settlement_ref": refund.settlement_ref,
        "requested_by": refund.requested_by,
        "reviewed_by": refund.reviewed_by,
        "requested_at": refund.requested_at.isoformat(),
        "settled_at": refund.settled_at.isoformat() if refund.settled_at else None,
    }
