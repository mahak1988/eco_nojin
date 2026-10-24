"""HTTP surface for the rural/tribal tourism (بوم‌گردی) module (P2-17).

The service layer (``services.tourism.service.TourismService``) has always
implemented the full lifecycle — guide registration and verification, tour
creation and landscape-manager approval, booking with ecological-capacity
enforcement, payment confirmation and regenerative completion, and the
800/200/200 bps fee split — but nothing ever mounted it, so no guide, tour or
booking could be created through the API. This router maps
``/api/v1/tourism`` onto those service methods; it re-implements none of the
business logic and follows the conventions of
``services.inventory.routers.inventory`` and
``services.api_gateway.routers.marketplace``.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import ROLE_ADMIN, require_roles, require_user
from services.api_gateway.errors import safe_detail_for_status
from services.tourism.api import festivals, unesco
from services.tourism.api._roles import APPROVER_ROLES
from services.tourism.models import TourismBooking, TourismGuide, TourismTour
from services.tourism.schemas import (
    BookingCancel,
    BookingCreate,
    BookingResponse,
    GuideCreate,
    GuideResponse,
    PaymentConfirm,
    TourCreate,
    TourResponse,
)
from services.tourism.service import TourismService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tourism", tags=["tourism"])

# Guide verification and tour approval are landscape-governance actions: the
# platform admin and the landscape manager — the same write roles the village
# hub accepts for village content (services.marketplace.hub_service).
_require_approver = require_roles(ROLE_ADMIN, "landscape_manager")


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, "id") else str(user.get("id"))


def _is_approver(user) -> bool:
    return getattr(user, "role", None) in APPROVER_ROLES


def _http_error(exc: ValueError, status_code: int) -> HTTPException:
    """Map a service-layer ``ValueError`` onto an HTTPException (no internals)."""
    return HTTPException(status_code=status_code, detail=safe_detail_for_status(exc, status_code))


# ═══════════════════════════════════════════════════════════════
# راهنمایان تور — Guides
# ═══════════════════════════════════════════════════════════════


@router.post("/guides", response_model=GuideResponse)
async def register_guide(
    payload: GuideCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """ثبت راهنمای تور جدید — requires an authenticated user."""
    service = TourismService(db)
    try:
        guide = await service.register_guide(
            user_id=_uid(user),
            village_id=payload.village_id,
            full_name=payload.full_name,
            bio=payload.bio,
            languages=payload.languages,
            specialties=payload.specialties,
            license_number=payload.license_number,
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return guide


@router.get("/guides", response_model=list[GuideResponse])
async def list_guides(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    is_verified: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Public guide directory."""
    q = select(TourismGuide).order_by(TourismGuide.created_at.desc())
    if village_id:
        q = q.where(TourismGuide.village_id == village_id)
    if is_verified is not None:
        q = q.where(TourismGuide.is_verified == is_verified)
    result = await db.execute(q.limit(limit).offset(offset))
    return list(result.scalars().all())


@router.get("/guides/{guide_id}", response_model=GuideResponse)
async def get_guide(guide_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get one guide from the directory."""
    result = await db.execute(select(TourismGuide).where(TourismGuide.id == guide_id))
    guide = result.scalar_one_or_none()
    if guide is None:
        raise HTTPException(status_code=404, detail="Guide not found")
    return guide


@router.post("/guides/{guide_id}/verify", response_model=GuideResponse)
async def verify_guide(
    guide_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    approver: Annotated[User, Depends(_require_approver)],
):
    """تأیید راهنما — admin or landscape manager only."""
    service = TourismService(db)
    try:
        guide = await service.verify_guide(guide_id)
    except ValueError as e:
        raise _http_error(e, 404) from e
    return guide


# ═══════════════════════════════════════════════════════════════
# تورها — Tours
# ═══════════════════════════════════════════════════════════════


@router.post("/tours", response_model=TourResponse)
async def create_tour(
    payload: TourCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """ثبت تور جدید — the guide must already be verified (service enforces it)."""
    service = TourismService(db)
    try:
        tour = await service.create_tour(
            guide_id=payload.guide_id,
            village_id=payload.village_id,
            title=payload.title,
            tour_type=payload.tour_type,
            duration_hours=payload.duration_hours,
            price_per_person=payload.price_per_person,
            description=payload.description,
            max_participants=payload.max_participants,
            min_participants=payload.min_participants,
            difficulty=payload.difficulty,
            ecological_capacity=payload.ecological_capacity,
            is_regenerative=payload.is_regenerative,
            regenerative_activity=payload.regenerative_activity,
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return tour


@router.get("/tours", response_model=list[TourResponse])
async def list_tours(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    tour_type: Annotated[str | None, Query(max_length=50)] = None,
    status: Annotated[str | None, Query(max_length=20)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Public catalogue — only ``active`` tours unless another status is asked for."""
    q = select(TourismTour).order_by(TourismTour.created_at.desc())
    if village_id:
        q = q.where(TourismTour.village_id == village_id)
    if tour_type:
        q = q.where(TourismTour.tour_type == tour_type)
    q = q.where(TourismTour.status == status) if status else q.where(TourismTour.status == "active")
    result = await db.execute(q.limit(limit).offset(offset))
    return list(result.scalars().all())


@router.get("/tours/{tour_id}", response_model=TourResponse)
async def get_tour(tour_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get one tour from the catalogue."""
    result = await db.execute(select(TourismTour).where(TourismTour.id == tour_id))
    tour = result.scalar_one_or_none()
    if tour is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour


@router.post("/tours/{tour_id}/approve", response_model=TourResponse)
async def approve_tour(
    tour_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    approver: Annotated[User, Depends(_require_approver)],
):
    """تأیید تور توسط مدیر منظر — admin or landscape manager only."""
    service = TourismService(db)
    try:
        tour = await service.approve_tour(tour_id, approved_by=_uid(approver))
    except ValueError as e:
        raise _http_error(e, 404) from e
    return tour


# ═══════════════════════════════════════════════════════════════
# رزروها — Bookings
# ═══════════════════════════════════════════════════════════════


async def _load_booking(db: AsyncSession, booking_id: str) -> TourismBooking:
    result = await db.execute(
        select(TourismBooking).where(TourismBooking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


def _require_booking_access(booking: TourismBooking, user) -> None:
    """The booking guest, or an approver acting on the booking."""
    if str(booking.guest_id) == _uid(user) or _is_approver(user):
        return
    raise HTTPException(status_code=403, detail="Not your booking")


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(
    payload: BookingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """ایجاد رزرو — the service enforces capacity, min/max and future-date rules."""
    service = TourismService(db)
    try:
        booking = await service.create_booking(
            tour_id=payload.tour_id,
            guest_id=_uid(user),
            participants_count=payload.participants_count,
            tour_date=payload.tour_date,
            village_id=payload.village_id,
            special_requests=payload.special_requests,
            regenerative_commitment=payload.regenerative_commitment,
            departure_id=payload.departure_id,
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return booking


@router.get("/bookings", response_model=list[BookingResponse])
async def list_bookings(
    guest_id: Annotated[str | None, Query(max_length=36)] = None,
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    status: Annotated[str | None, Query(max_length=20)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    user: Annotated[User, Depends(require_user)] = None,
):
    """List bookings — the caller's own by default; ``guest_id`` needs an approver."""
    target_guest = guest_id or _uid(user)
    if guest_id and guest_id != _uid(user) and not _is_approver(user):
        raise HTTPException(status_code=403, detail="Cannot list another guest's bookings")
    q = select(TourismBooking).where(TourismBooking.guest_id == target_guest)
    if village_id:
        q = q.where(TourismBooking.village_id == village_id)
    if status:
        q = q.where(TourismBooking.status == status)
    q = q.order_by(TourismBooking.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """Get one booking — guest or approver only."""
    booking = await _load_booking(db, booking_id)
    _require_booking_access(booking, user)
    return booking


@router.post("/bookings/{booking_id}/confirm-payment", response_model=BookingResponse)
async def confirm_payment(
    booking_id: str,
    payload: PaymentConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """تأیید پرداخت رزرو — guest or approver only."""
    booking = await _load_booking(db, booking_id)
    _require_booking_access(booking, user)
    service = TourismService(db)
    try:
        booking = await service.confirm_booking(booking_id, payload.payment_tx_hash)
    except ValueError as e:
        raise _http_error(e, 404) from e
    return booking


@router.post("/bookings/{booking_id}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """طھع©ظ…غŒظ„ ط±ط²ط±ظˆ (ظ¾ط³ ط§ط² ط¨ط±ع¯ط²ط§ط±غŒ طھظˆط±) â€” guest or approver only."""
    booking = await _load_booking(db, booking_id)
    _require_booking_access(booking, user)
    service = TourismService(db)
    try:
        booking = await service.complete_booking(booking_id)
    except ValueError as e:
        raise _http_error(e, 400) from e
    return booking


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    payload: BookingCancel,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """لغو ط±ط²ط±ظˆ با بازپرداخت اختیاری — guest or approver only."""
    booking = await _load_booking(db, booking_id)
    _require_booking_access(booking, user)
    service = TourismService(db)
    try:
        booking = await service.cancel_booking(
            booking_id,
            reason=payload.reason,
            refund_requested=payload.refund_requested,
        )
    except ValueError as e:
        raise _http_error(e, 400) from e
    return booking


# Mount festival and UNESCO sub-routers
router.include_router(festivals.router)
router.include_router(unesco.router)
