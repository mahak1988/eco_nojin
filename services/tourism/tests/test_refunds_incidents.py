"""P8 — refunds are reviewed (never auto-approved) and safety incidents brake."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.tourism.departures import DepartureStatus, TourDeparture
from services.tourism.incidents import IncidentSeverity, IncidentStatus, RefundStatus
from services.tourism.models import TourismTour, TourismTourType
from services.tourism.safety_service import RefundError, TourismSafetyService
from services.tourism.service import TourismService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def _departure(session) -> str:
    session.add(
        TourismTour(
            id="tour-1",
            guide_id="g-1",
            village_id="village-1",
            title="Hyrcanian Forests",
            slug="hyrcanian-forests",
            tour_type=TourismTourType.ECOTOURISM,
            duration_hours=4,
            price_per_person=Decimal("100.00"),
            max_participants=4,
            min_participants=1,
            ecological_capacity=4,
            status="active",
        )
    )
    session.add(
        TourDeparture(
            id="dep-1",
            tour_id="tour-1",
            departure_date=datetime.now(UTC).date() + timedelta(days=9),
            capacity=4,
            status=DepartureStatus.OPEN.value,
        )
    )
    session.add(
        __import__("services.tourism.models", fromlist=["TourismBooking"]).TourismBooking(
            id="book-1",
            booking_number="BK-1",
            tour_id="tour-1",
            guest_id="user-1",
            participants_count=1,
            village_id="village-1",
            tour_date=datetime.now(UTC) + timedelta(days=9),
            subtotal=Decimal("80.00"),
            total=Decimal("88.00"),
            status="pending",
        )
    )
    await session.commit()
    return "dep-1"


async def test_a_refund_is_reviewed_before_it_is_settled(session):
    service = TourismSafetyService(session)
    await _departure(session)
    refund = await service.request_refund(
        booking_id="book-1",
        requested_by="user-1",
        amount=Decimal("88.00"),
        reason="weather window missed",
    )
    assert refund.status == RefundStatus.REQUESTED.value

    with pytest.raises(RefundError):
        await service.settle_refund(str(refund.id), settlement_ref="pay-1")  # not approved yet

    await service.review_refund(str(refund.id), reviewer_id="admin-1", approve=True)
    with pytest.raises(RefundError):
        await service.settle_refund(str(refund.id), settlement_ref="")  # no reference

    settled = await service.settle_refund(str(refund.id), settlement_ref="pay-1")
    assert settled.status == RefundStatus.SETTLED.value
    assert settled.settlement_ref == "pay-1"


async def test_a_second_open_refund_for_one_booking_is_refused(session):
    service = TourismSafetyService(session)
    await _departure(session)
    await service.request_refund(
        booking_id="book-1", requested_by="user-1", amount=Decimal("10"), reason="a"
    )
    with pytest.raises(RefundError):
        await service.request_refund(
            booking_id="book-1", requested_by="user-1", amount=Decimal("10"), reason="b"
        )


async def test_a_safety_incident_brakes_the_departure(session):
    service = TourismSafetyService(session)
    departure_id = await _departure(session)
    incident = await service.report_incident(
        departure_id=departure_id,
        reported_by="guide-1",
        summary="landslide on the approach road",
        severity=IncidentSeverity.SAFETY.value,
    )
    assert incident.blocks_bookings is True
    departure = (
        await session.execute(
            select(TourDeparture).where(TourDeparture.id == departure_id)
        )
    ).scalar_one()
    assert departure.status == DepartureStatus.CLOSED.value
    assert await service.departure_is_blocked(departure_id) is True

    resolved = await service.resolve_incident(
        str(incident.id), resolver_id="manager-1", resolution="road cleared, route re-walked"
    )
    assert resolved.status == IncidentStatus.RESOLVED.value
    assert await service.departure_is_blocked(departure_id) is False

    # the brake the incident wrote is lifted with it: the departure re-opens
    await session.refresh(departure)
    assert departure.status == DepartureStatus.OPEN.value


async def test_cancelling_a_booking_frees_the_departures_seats(session):
    """The departure ledger unwinds with the booking, and re-opens when full."""
    await _departure(session)
    service = TourismService(session)
    booking = await service.create_booking(
        tour_id="tour-1",
        guest_id="user-1",
        participants_count=2,
        tour_date=datetime.now(UTC) + timedelta(days=9),
        village_id="village-1",
        departure_id="dep-1",
    )
    departure = (
        await session.execute(select(TourDeparture).where(TourDeparture.id == "dep-1"))
    ).scalar_one()
    assert departure.booked == 2
    assert departure.remaining() == 2

    cancelled = await service.cancel_booking(str(booking.id), reason="trip postponed")
    assert cancelled.status == "cancelled"
    await session.refresh(departure)
    assert departure.booked == 0
    assert departure.remaining() == 4
    assert departure.status == DepartureStatus.OPEN.value


async def test_a_full_departure_reopens_after_a_cancellation(session):
    await _departure(session)
    service = TourismService(session)
    booking = await service.create_booking(
        tour_id="tour-1",
        guest_id="user-1",
        participants_count=4,
        tour_date=datetime.now(UTC) + timedelta(days=9),
        village_id="village-1",
        departure_id="dep-1",
    )
    departure = (
        await session.execute(select(TourDeparture).where(TourDeparture.id == "dep-1"))
    ).scalar_one()
    assert departure.status == DepartureStatus.CLOSED.value  # filled up

    with pytest.raises(ValueError, match="closed"):
        await service.create_booking(
            tour_id="tour-1",
            guest_id="user-3",
            participants_count=1,
            tour_date=datetime.now(UTC) + timedelta(days=9),
            village_id="village-1",
            departure_id="dep-1",
        )

    await service.cancel_booking(str(booking.id), reason="guest withdrew")
    await session.refresh(departure)
    assert departure.status == DepartureStatus.OPEN.value
    assert departure.remaining() == 4


async def test_a_low_severity_incident_does_not_block(session):
    service = TourismSafetyService(session)
    departure_id = await _departure(session)
    incident = await service.report_incident(
        departure_id=departure_id,
        reported_by="guide-1",
        summary="one participant arrived late",
        severity=IncidentSeverity.LOW.value,
    )
    assert incident.blocks_bookings is False
    assert await service.departure_is_blocked(departure_id) is False
