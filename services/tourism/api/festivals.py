"""Festival router — CRUD, editions, bookings, dynamic pricing."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_user
from services.tourism.festival_service import FestivalError, FestivalService

router = APIRouter(prefix="/festivals", tags=["tourism-festivals"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


def _uid(user) -> str:
    return str(user.id) if hasattr(user, "id") else str(user.get("id"))


def _http_error(exc: Exception, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(exc))


# ═══════════════════════════════════════════════════════════════
# schemas
# ═══════════════════════════════════════════════════════════════


class FestivalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    festival_type: str = Field(min_length=1, max_length=50)
    season: str = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date
    capacity: int = Field(ge=1)
    base_ticket_price: Decimal = Field(gt=0)
    recurrence: str = Field(default="annual", max_length=20)
    landscape_fee_bps: int = Field(default=200, ge=0, le=10000)
    is_regenerative: bool = Field(default=False)


class FestivalResponse(BaseModel):
    id: str
    village_id: str
    name: str
    name_en: str | None
    festival_type: str
    season: str
    start_date: date
    end_date: date
    recurrence: str
    capacity: int
    base_ticket_price: str
    landscape_fee_bps: int
    is_regenerative: bool
    status: str
    created_by: str
    created_at: datetime


class EditionCreate(BaseModel):
    year: int = Field(ge=1900, le=2100)
    total_seats: int = Field(ge=1)


class EditionResponse(BaseModel):
    id: str
    festival_id: str
    year: int
    total_seats: int
    seats_available: int
    total_revenue: str
    landscape_fees: str
    status: str
    created_at: datetime


class BookingCreate(BaseModel):
    edition_id: str
    participants_count: int = Field(ge=1)


class BookingResponse(BaseModel):
    id: str
    festival_id: str
    edition_id: str
    guest_id: str
    participants_count: int
    ticket_price: str
    subtotal: str
    platform_fee: str
    landscape_fee: str
    total: str
    status: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════
# festivals
# ═══════════════════════════════════════════════════════════════


@router.post("", response_model=FestivalResponse)
async def create_festival(
    payload: FestivalCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """ثبت جشنواره جدید — فقط روستای effective (governance-active) مجاز است."""
    service = FestivalService(db)
    try:
        festival = await service.create_festival(
            village_id=_uid(user),
            name=payload.name,
            name_en=payload.name_en,
            festival_type=payload.festival_type,
            season=payload.season,
            start_date=payload.start_date,
            end_date=payload.end_date,
            capacity=payload.capacity,
            base_ticket_price=payload.base_ticket_price,
            created_by=_uid(user),
            recurrence=payload.recurrence,
            landscape_fee_bps=payload.landscape_fee_bps,
            is_regenerative=payload.is_regenerative,
        )
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _festival_response(festival)


@router.get("", response_model=list[FestivalResponse])
async def list_festivals(
    village_id: Annotated[str | None, Query(max_length=100)] = None,
    season: Annotated[str | None, Query(max_length=20)] = None,
    festival_type: Annotated[str | None, Query(max_length=50)] = None,
    status: Annotated[str | None, Query(max_length=20)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    service = FestivalService(db)
    festivals = await service.list_festivals(
        village_id=village_id,
        season=season,
        festival_type=festival_type,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_festival_response(f) for f in festivals]


@router.get("/{festival_id}", response_model=FestivalResponse)
async def get_festival(
    festival_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = FestivalService(db)
    festival = await service.get_festival(festival_id)
    if festival is None:
        raise HTTPException(status_code=404, detail="Festival not found")
    return _festival_response(festival)


@router.post("/{festival_id}/activate", response_model=FestivalResponse)
async def activate_festival(
    festival_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = FestivalService(db)
    try:
        festival = await service.activate_festival(festival_id, actor_id=_uid(user))
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _festival_response(festival)


@router.post("/{festival_id}/complete", response_model=FestivalResponse)
async def complete_festival(
    festival_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = FestivalService(db)
    try:
        festival = await service.complete_festival(festival_id, actor_id=_uid(user))
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _festival_response(festival)


# ═══════════════════════════════════════════════════════════════
# editions
# ═══════════════════════════════════════════════════════════════


@router.post("/{festival_id}/editions", response_model=EditionResponse)
async def create_edition(
    festival_id: str,
    payload: EditionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = FestivalService(db)
    try:
        edition = await service.create_edition(
            festival_id=festival_id,
            year=payload.year,
            total_seats=payload.total_seats,
            created_by=_uid(user),
        )
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _edition_response(edition)


@router.get("/editions/{edition_id}", response_model=EditionResponse)
async def get_edition(
    edition_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = FestivalService(db)
    edition = await service.get_edition(edition_id)
    if edition is None:
        raise HTTPException(status_code=404, detail="Edition not found")
    return _edition_response(edition)


# ═══════════════════════════════════════════════════════════════
# bookings
# ═══════════════════════════════════════════════════════════════


@router.post("/bookings", response_model=BookingResponse)
async def book_festival(
    payload: BookingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """رزرو شرکت در جشنواره — قیمت پویا بر اساس fill ratio."""
    # Note: festival_id is derived from edition; we need to look it up.
    service = FestivalService(db)
    edition = await service.get_edition(payload.edition_id)
    if edition is None:
        raise HTTPException(status_code=404, detail="Edition not found")
    try:
        booking = await service.book_festival(
            festival_id=str(edition.festival_id),
            edition_id=payload.edition_id,
            guest_id=_uid(user),
            participants_count=payload.participants_count,
            created_by=_uid(user),
        )
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _booking_response(booking)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = FestivalService(db)
    try:
        booking = await service.cancel_booking(booking_id=booking_id, actor_id=_uid(user))
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _booking_response(booking)


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    service = FestivalService(db)
    booking = await service.get_booking(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return _booking_response(booking)


@router.get("/{festival_id}/report", response_model=dict)
async def festival_report(
    festival_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = FestivalService(db)
    try:
        return await service.festival_report(festival_id=festival_id)
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e


# ═══════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════


def _festival_response(f) -> FestivalResponse:
    return FestivalResponse(
        id=f.id,
        village_id=f.village_id,
        name=f.name,
        name_en=f.name_en,
        festival_type=f.festival_type,
        season=f.season,
        start_date=f.start_date,
        end_date=f.end_date,
        recurrence=f.recurrence,
        capacity=f.capacity,
        base_ticket_price=str(f.base_ticket_price),
        landscape_fee_bps=f.landscape_fee_bps,
        is_regenerative=f.is_regenerative,
        status=f.status,
        created_by=f.created_by,
        created_at=f.created_at,
    )


def _edition_response(e) -> EditionResponse:
    return EditionResponse(
        id=e.id,
        festival_id=str(e.festival_id),
        year=e.year,
        total_seats=e.total_seats,
        seats_available=e.seats_available,
        total_revenue=str(e.total_revenue),
        landscape_fees=str(e.landscape_fees),
        status=e.status,
        created_at=e.created_at,
    )


def _booking_response(b) -> BookingResponse:
    return BookingResponse(
        id=b.id,
        festival_id=str(b.festival_id),
        edition_id=str(b.edition_id),
        guest_id=b.guest_id,
        participants_count=b.participants_count,
        ticket_price=str(b.ticket_price),
        subtotal=str(b.subtotal),
        platform_fee=str(b.platform_fee),
        landscape_fee=str(b.landscape_fee),
        total=str(b.total),
        status=b.status,
        created_at=b.created_at,
    )


# ═══════════════════════════════════════════════════════════════
# nomadic community tours
# ═══════════════════════════════════════════════════════════════


class NomadicTourCreate(BaseModel):
    nomadic_community_id: str = Field(..., min_length=1)
    guide_id: str = Field(..., min_length=1)
    village_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=300)
    slug: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    tour_type: str = Field(..., min_length=1, max_length=50)
    duration_hours: int = Field(..., ge=1)
    price_per_person: Decimal = Field(..., gt=0)
    capacity: int = Field(default=10, ge=1)
    min_participants: int = Field(default=2, ge=1)
    difficulty: str = Field(default="moderate", max_length=30)
    includes: list | None = None
    excludes: list | None = None
    itinerary: list | None = None
    meeting_point: dict | None = None
    images: list | None = None
    ecological_capacity: int | None = None


class NomadicTourResponse(BaseModel):
    id: str
    guide_id: str
    nomadic_community_id: str | None
    village_id: str
    title: str
    slug: str
    description: str | None
    tour_type: str
    duration_hours: int
    max_participants: int
    min_participants: int
    difficulty: str
    price_per_person: str
    currency: str
    includes: list
    excludes: list
    itinerary: list
    meeting_point: dict | None
    images: list
    ecological_capacity: int | None
    status: str
    is_regenerative: bool
    created_at: datetime


@router.post("/nomadic-tours", response_model=NomadicTourResponse)
async def create_nomadic_tour(
    payload: NomadicTourCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
):
    """Create an ecotourism tour led by a nomadic community."""
    service = FestivalService(db)
    try:
        tour = await service.create_tour_for_nomadic_community(
            nomadic_community_id=payload.nomadic_community_id,
            guide_id=payload.guide_id,
            village_id=payload.village_id,
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
            tour_type=payload.tour_type,
            duration_hours=payload.duration_hours,
            price_per_person=payload.price_per_person,
            capacity=payload.capacity,
            min_participants=payload.min_participants,
            difficulty=payload.difficulty,
            includes=payload.includes,
            excludes=payload.excludes,
            itinerary=payload.itinerary,
            meeting_point=payload.meeting_point,
            images=payload.images,
            ecological_capacity=payload.ecological_capacity,
        )
    except FestivalError as e:
        raise _http_error(e, 400) from e
    except ValueError as e:
        raise _http_error(e, 400) from e
    return _nomadic_tour_response(tour)


def _nomadic_tour_response(t) -> NomadicTourResponse:
    return NomadicTourResponse(
        id=t.id,
        guide_id=t.guide_id,
        nomadic_community_id=t.nomadic_community_id,
        village_id=t.village_id,
        title=t.title,
        slug=t.slug,
        description=t.description,
        tour_type=t.tour_type,
        duration_hours=t.duration_hours,
        max_participants=t.max_participants,
        min_participants=t.min_participants,
        difficulty=t.difficulty,
        price_per_person=str(t.price_per_person),
        currency=t.currency,
        includes=t.includes,
        excludes=t.excludes,
        itinerary=t.itinerary,
        meeting_point=t.meeting_point,
        images=t.images,
        ecological_capacity=t.ecological_capacity,
        status=t.status,
        is_regenerative=t.is_regenerative,
        created_at=t.created_at,
    )
