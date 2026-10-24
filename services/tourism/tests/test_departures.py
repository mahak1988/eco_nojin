"""P8 — departures are additive and capacity is per departure."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.tourism.departure_service import DepartureError, DepartureService
from services.tourism.departures import DepartureStatus
from services.tourism.models import TourismTour, TourismTourType

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def _tour(session, *, capacity: int = 4) -> str:
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
            max_participants=capacity,
            min_participants=1,
            ecological_capacity=capacity,
            status="active",
        )
    )
    await session.commit()
    return "tour-1"


async def test_a_departure_cannot_exceed_the_ecological_capacity(session):
    service = DepartureService(session)
    await _tour(session, capacity=4)
    with pytest.raises(DepartureError):
        await service.create_departure(
            tour_id="tour-1",
            departure_date=datetime.now(UTC).date() + timedelta(days=10),
            capacity=9,  # over the tour's ecological capacity of 4
        )


async def test_capacity_is_per_departure_not_per_tour(session):
    service = DepartureService(session)
    await _tour(session, capacity=4)
    first = datetime.now(UTC).date() + timedelta(days=5)
    second = datetime.now(UTC).date() + timedelta(days=12)

    d1 = await service.create_departure(tour_id="tour-1", departure_date=first, capacity=2)
    d2 = await service.create_departure(tour_id="tour-1", departure_date=second, capacity=2)

    await service.consume(str(d1.id), 2)  # the first departure fills up…
    assert d1.status == DepartureStatus.CLOSED.value
    # …but the tour can still be booked on the other date.
    still_open = await service.consume(str(d2.id), 1)
    assert still_open.remaining() == 1


async def test_overbooking_a_departure_is_refused(session):
    service = DepartureService(session)
    await _tour(session, capacity=4)
    departure = await service.create_departure(
        tour_id="tour-1",
        departure_date=datetime.now(UTC).date() + timedelta(days=5),
        capacity=2,
    )
    await service.consume(str(departure.id), 2)
    with pytest.raises(DepartureError):
        await service.consume(str(departure.id), 1)


async def test_a_past_departure_is_refused(session):
    service = DepartureService(session)
    await _tour(session)
    with pytest.raises(DepartureError):
        await service.create_departure(
            tour_id="tour-1",
            departure_date=datetime.now(UTC).date() - timedelta(days=1),
        )


async def test_the_tour_plane_keeps_working_untouched(session):
    """The additive promise: nothing about the tour itself changed."""
    await _tour(session)
    tour = (
        await session.execute(select(TourismTour).where(TourismTour.id == "tour-1"))
    ).scalar_one()
    assert tour.ecological_capacity == 4
    assert str(tour.title) == "Hyrcanian Forests"
