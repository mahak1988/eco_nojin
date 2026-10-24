"""P8 — the tourism safety surface over HTTP: capacity, incidents, refunds."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import User
from services.api_gateway.auth import require_user
from services.tourism.api.safety import router as safety_router
from services.tourism.departure_service import DepartureService
from services.tourism.departures import DepartureStatus
from services.tourism.incidents import IncidentSeverity, RefundStatus
from services.tourism.models import TourismBooking, TourismTour, TourismTourType

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seeded():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with maker() as session:
        session.add(User(id="admin-1", email="a@b.c", password_hash="x", full_name="A", role="admin"))
        session.add(User(id="user-1", email="u@b.c", password_hash="x", full_name="U", role="farmer"))
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
            TourismBooking(
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
        service = DepartureService(session)
        departure = await service.create_departure(
            tour_id="tour-1",
            departure_date=datetime.now(UTC).date() + timedelta(days=9),
            capacity=3,
        )
        await session.commit()
    yield maker, str(departure.id)
    await engine.dispose()


def _client(maker, *, user_id: str, role: str = "farmer"):
    from services.tourism.api import safety as safety_module

    app = FastAPI()
    app.include_router(safety_router)

    def _db():
        async def _dependency():
            session = maker()
            try:
                yield session
            finally:
                await session.close()

        return _dependency

    app.dependency_overrides[safety_module.get_db] = _db()
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id=user_id, role=role, is_active=True
    )
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_departures_are_served_with_capacity(seeded):
    maker, _dep = seeded
    async with _client(maker, user_id="user-1") as client:
        response = await client.get("/api/v1/tourism/tours/tour-1/departures")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["capacity"] == 3
    assert items[0]["remaining"] == 3


async def test_a_departure_cannot_exceed_the_tour_capacity(seeded):
    maker, _dep = seeded
    async with _client(maker, user_id="admin-1", role="admin") as client:
        response = await client.post(
            "/api/v1/tourism/tours/tour-1/departures",
            json={"departure_date": "2027-05-01", "capacity": 99},
        )
    assert response.status_code == 400
    assert "ecological" in response.json()["detail"]


async def test_a_farmer_cannot_create_a_departure(seeded):
    maker, _dep = seeded
    async with _client(maker, user_id="user-1") as client:
        response = await client.post(
            "/api/v1/tourism/tours/tour-1/departures",
            json={"departure_date": "2027-05-01"},
        )
    assert response.status_code == 403


async def test_a_safety_incident_closes_the_departure_over_http(seeded):
    maker, departure_id = seeded
    async with _client(maker, user_id="user-1") as client:
        created = await client.post(
            "/api/v1/tourism/incidents",
            json={
                "departure_id": departure_id,
                "summary": "landslide on the approach road",
                "severity": IncidentSeverity.SAFETY.value,
            },
        )
        assert created.status_code == 201
        assert created.json()["blocks_bookings"] is True

        listed = await client.get("/api/v1/tourism/departures")
        assert listed.status_code == 200
        closed = [d for d in listed.json()["items"] if d["id"] == departure_id]
        assert closed and closed[0]["status"] == DepartureStatus.CLOSED.value


async def test_a_refund_requires_review_before_settlement(seeded):
    maker, _dep = seeded
    async with _client(maker, user_id="user-1") as client:
        refund = await client.post(
            "/api/v1/tourism/refunds",
            json={
                "booking_id": "book-1",
                "amount": 88.0,
                "reason": "weather window missed",
            },
        )
        assert refund.status_code == 201
        assert refund.json()["status"] == RefundStatus.REQUESTED.value

        early = await client.post(
            f"/api/v1/tourism/refunds/{refund.json()['id']}/settle",
            json={"settlement_ref": "pay-1"},
        )
        # a farmer may not settle at all: the role gate answers before the
        # state gate, and neither may be bypassed by a caller
        assert early.status_code == 403

    async with _client(maker, user_id="admin-1", role="admin") as client:
        reviewed = await client.post(
            f"/api/v1/tourism/refunds/{refund.json()['id']}/review",
            json={"approve": True, "note": "verified"},
        )
        assert reviewed.status_code == 200
        settled = await client.post(
            f"/api/v1/tourism/refunds/{refund.json()['id']}/settle",
            json={"settlement_ref": "pay-1"},
        )
        assert settled.status_code == 200
        assert settled.json()["settlement_ref"] == "pay-1"
        assert settled.json()["status"] == RefundStatus.SETTLED.value
