"""HTTP-surface tests for the rural/tribal tourism router (P2-17).

The tourism service layer was complete but unreachable: no router was ever
mounted, so no guide, tour or booking could be created through the API. These
tests exercise the mounted lifecycle end to end over a FastAPI TestClient with
in-memory SQLite and dependency overrides for auth + DB, following
``services/finance/tests/test_finance_router_wallet.py``:

(a) the happy path guide → verify → tour → approve → booking → confirm →
    complete, asserting the 800/200/200 bps fee split;
(b) ecological-capacity enforcement rejects an overbooking;
(c) verify/approve reject callers without the admin/landscape-manager role,
    and unauthenticated writes are rejected with 401.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from services.api_gateway.auth import _get_async_db, get_current_user
from services.tourism.api.router import get_db, router
from services.tourism.models import TourismBooking, TourismGuide, TourismTour

pytestmark = pytest.mark.asyncio

_BASE = "/api/v1/tourism"
_TOURISM_TABLES = (
    TourismGuide.__table__,
    TourismTour.__table__,
    TourismBooking.__table__,
)


@pytest.fixture
async def db_session():
    """One in-memory database shared by every app built in a test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for table in _TOURISM_TABLES:
            await conn.run_sync(table.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


def _build_app(session, *, user_id="guest-1", role="farmer", authenticate=True):
    """Mount the tourism router with auth + DB overrides.

    ``authenticate=False`` leaves the real ``get_current_user`` in place, so
    requests without a token exercise the genuine 401 path.
    """
    app = FastAPI()
    app.include_router(router)

    async def database_override():
        yield session

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[_get_async_db] = database_override
    if authenticate:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=user_id, role=role
        )
    return app


async def _request(app, method: str, path: str, payload: dict | None = None, params=None):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, f"{_BASE}{path}", json=payload, params=params)


def _future_date(days: int = 7) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


async def _register_guide(app, village_id: str = "village-001") -> dict:
    response = await _request(
        app,
        "POST",
        "/guides",
        {
            "village_id": village_id,
            "full_name": "Ali Karimi",
            "bio": "Nomadic tour guide",
            "languages": ["fa", "en"],
            "specialties": ["nomadic"],
            "license_number": "LIC-42",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _create_tour(app, guide_id: str, **overrides) -> dict:
    payload = {
        "guide_id": guide_id,
        "village_id": "village-001",
        "title": "Nomadic Kermanshah Tour",
        "tour_type": "nomadic",
        "duration_hours": 8,
        "price_per_person": "500000",
        "max_participants": 10,
        "ecological_capacity": 10,
        "is_regenerative": True,
        "regenerative_activity": "Plant 10 saplings",
    }
    payload.update(overrides)
    response = await _request(app, "POST", "/tours", payload)
    assert response.status_code == 200, response.text
    return response.json()


# --- (a) happy path -------------------------------------------------------


async def test_full_lifecycle_guide_to_regenerative_completion(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")

    # 1. Guide registration — starts unverified.
    guide = await _register_guide(guest_app)
    assert guide["is_verified"] is False
    assert guide["languages"] == ["fa", "en"]
    assert guide["user_id"] == "guest-1"

    # 2. Verification is an approver action.
    response = await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    assert response.status_code == 200, response.text
    assert response.json()["is_verified"] is True

    # 3. Tour creation for the now-verified guide.
    tour = await _create_tour(guest_app, guide["id"])
    assert tour["status"] == "pending_approval"
    assert tour["slug"].startswith("nomadic-kermanshah-tour")
    assert tour["tour_type"] == "nomadic"

    # 4. Approval by the landscape manager activates the tour.
    response = await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")
    assert response.status_code == 200, response.text
    approved = response.json()
    assert approved["status"] == "active"
    assert approved["approved_by"] == "manager-1"

    # 5. Booking: 800/200/200 bps on top of 3 x 500,000.
    response = await _request(
        guest_app,
        "POST",
        "/bookings",
        {
            "tour_id": tour["id"],
            "village_id": "village-001",
            "participants_count": 3,
            "tour_date": _future_date(),
            "regenerative_commitment": "Plant 10 saplings",
        },
    )
    assert response.status_code == 200, response.text
    booking = response.json()
    assert booking["booking_number"].startswith("TR-")
    assert booking["guest_id"] == "guest-1"
    assert Decimal(booking["subtotal"]) == Decimal("1500000")
    assert Decimal(booking["platform_fee"]) == Decimal("120000")
    assert Decimal(booking["landscape_fee"]) == Decimal("30000")
    assert Decimal(booking["insurance_fee"]) == Decimal("30000")
    assert Decimal(booking["total"]) == Decimal("1680000")

    # 6. Payment confirmation.
    response = await _request(
        guest_app,
        "POST",
        f"/bookings/{booking['id']}/confirm-payment",
        {"payment_tx_hash": "tx-hash-123"},
    )
    assert response.status_code == 200, response.text
    confirmed = response.json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["payment_status"] == "paid"
    assert confirmed["blockchain_tx_hash"] == "tx-hash-123"

    # 7. Regenerative completion.
    response = await _request(guest_app, "POST", f"/bookings/{booking['id']}/complete")
    assert response.status_code == 200, response.text
    completed = response.json()
    assert completed["status"] == "completed"
    assert completed["settlement_status"] == "completed"
    assert completed["regenerative_completed"] is True

    # 8. The guest can read their own booking; the approver can too.
    response = await _request(guest_app, "GET", f"/bookings/{booking['id']}")
    assert response.status_code == 200, response.text
    response = await _request(approver_app, "GET", f"/bookings/{booking['id']}")
    assert response.status_code == 200, response.text

    # 9. Paid bookings raise the tour booking counter.
    response = await _request(guest_app, "GET", f"/tours/{tour['id']}")
    assert response.json()["total_bookings"] == 1
    assert response.json()["current_bookings"] == 3

    # 10. The guest's booking list is scoped to them, and an approver may list
    #     another guest's bookings via ?guest_id=.
    response = await _request(guest_app, "GET", "/bookings")
    assert [b["id"] for b in response.json()] == [booking["id"]]
    response = await _request(approver_app, "GET", "/bookings", params={"guest_id": "guest-1"})
    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [booking["id"]]

    # 11. The public catalogue lists the active tour only; an unapproved tour
    #     stays out of it.
    unapproved = await _create_tour(guest_app, guide["id"], title="Pending Retreat")
    response = await _request(guest_app, "GET", "/tours")
    assert response.status_code == 200, response.text
    listed = response.json()
    assert [t["id"] for t in listed] == [tour["id"]]
    response = await _request(guest_app, "GET", "/tours", params={"status": "pending_approval"})
    assert [t["id"] for t in response.json()] == [unapproved["id"]]

    # 12. Directory lookups.
    response = await _request(guest_app, "GET", "/guides")
    assert [g["id"] for g in response.json()] == [guide["id"]]
    response = await _request(guest_app, "GET", f"/guides/{guide['id']}")
    assert response.status_code == 200, response.text
    assert response.json()["full_name"] == "Ali Karimi"


async def test_unknown_entities_return_404(db_session):
    app = _build_app(db_session)
    assert (await _request(app, "GET", "/guides/nope")).status_code == 404
    assert (await _request(app, "GET", "/tours/nope")).status_code == 404
    assert (await _request(app, "GET", "/bookings/nope")).status_code == 404


async def test_tour_for_unverified_guide_is_rejected(db_session):
    guest_app = _build_app(db_session, role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _register_guide(guest_app)
    response = await _request(
        guest_app,
        "POST",
        "/tours",
        {
            "guide_id": guide["id"],
            "village_id": "village-001",
            "title": "Too Early",
            "tour_type": "nomadic",
            "duration_hours": 4,
            "price_per_person": "1000",
        },
    )
    assert response.status_code == 400, response.text
    # Once verified the very same payload is accepted.
    await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    response = await _request(
        guest_app,
        "POST",
        "/tours",
        {
            "guide_id": guide["id"],
            "village_id": "village-001",
            "title": "Just In Time",
            "tour_type": "nomadic",
            "duration_hours": 4,
            "price_per_person": "1000",
        },
    )
    assert response.status_code == 200, response.text


async def test_invalid_payload_is_rejected_with_422(db_session):
    app = _build_app(db_session)
    guide = await _register_guide(app)
    response = await _request(
        app,
        "POST",
        "/tours",
        {
            "guide_id": guide["id"],
            "village_id": "village-001",
            "title": "Free Tour",
            "tour_type": "definitely-not-a-type",
            "duration_hours": 4,
            "price_per_person": "0",
        },
    )
    assert response.status_code == 422, response.text


# --- (b) ecological capacity ---------------------------------------------


async def test_ecological_capacity_rejects_overbooking(db_session):
    guest_app = _build_app(db_session, user_id="guest-2", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")

    guide = await _register_guide(guest_app)
    await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    tour = await _create_tour(guest_app, guide["id"], ecological_capacity=5)
    await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")

    # 3 of 5 places fit.
    response = await _request(
        guest_app,
        "POST",
        "/bookings",
        {
            "tour_id": tour["id"],
            "village_id": "village-001",
            "participants_count": 3,
            "tour_date": _future_date(),
        },
    )
    assert response.status_code == 200, response.text

    # 3 more would push 6 > 5 over the ecological capacity.
    response = await _request(
        guest_app,
        "POST",
        "/bookings",
        {
            "tour_id": tour["id"],
            "village_id": "village-001",
            "participants_count": 3,
            "tour_date": _future_date(),
        },
    )
    assert response.status_code == 400, response.text

    # The rejected booking consumed no capacity.
    response = await _request(guest_app, "GET", f"/tours/{tour['id']}")
    assert response.json()["current_bookings"] == 3


async def test_booking_rejects_past_tour_date(db_session):
    guest_app = _build_app(db_session, role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _register_guide(guest_app)
    await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    tour = await _create_tour(guest_app, guide["id"])
    await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")
    response = await _request(
        guest_app,
        "POST",
        "/bookings",
        {
            "tour_id": tour["id"],
            "village_id": "village-001",
            "participants_count": 2,
            "tour_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 400, response.text


# --- (c) authorization ----------------------------------------------------


@pytest.mark.parametrize("role", ["admin", "landscape_manager"])
async def test_verify_guide_allows_admin_and_landscape_manager(db_session, role):
    app = _build_app(db_session, user_id="approver-1", role=role)
    guide = await _register_guide(app)
    response = await _request(app, "POST", f"/guides/{guide['id']}/verify")
    assert response.status_code == 200, response.text
    assert response.json()["is_verified"] is True


async def test_verify_guide_rejects_farmer_role(db_session):
    app = _build_app(db_session, user_id="farmer-9", role="farmer")
    guide = await _register_guide(app)
    response = await _request(app, "POST", f"/guides/{guide['id']}/verify")
    assert response.status_code == 403, response.text
    assert (await _request(app, "GET", f"/guides/{guide['id']}")).json()["is_verified"] is False


async def test_approve_tour_rejects_farmer_role(db_session):
    farmer_app = _build_app(db_session, user_id="farmer-9", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _register_guide(farmer_app)
    await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    tour = await _create_tour(farmer_app, guide["id"])

    response = await _request(farmer_app, "POST", f"/tours/{tour['id']}/approve")
    assert response.status_code == 403, response.text

    response = await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "active"


async def test_write_endpoints_reject_unauthenticated_callers(db_session):
    app = _build_app(db_session, authenticate=False)
    response = await _request(
        app,
        "POST",
        "/guides",
        {"village_id": "village-001", "full_name": "Anonymous"},
    )
    assert response.status_code == 401, response.text
    response = await _request(
        app,
        "POST",
        "/bookings",
        {
            "tour_id": "tour-1",
            "village_id": "village-001",
            "participants_count": 1,
            "tour_date": _future_date(),
        },
    )
    assert response.status_code == 401, response.text
    response = await _request(app, "POST", "/guides/some-guide/verify")
    assert response.status_code == 401, response.text


async def test_another_guests_booking_is_forbidden(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    other_app = _build_app(db_session, user_id="guest-2", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _register_guide(guest_app)
    await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    tour = await _create_tour(guest_app, guide["id"])
    await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")
    booking = (
        await _request(
            guest_app,
            "POST",
            "/bookings",
            {
                "tour_id": tour["id"],
                "village_id": "village-001",
                "participants_count": 2,
                "tour_date": _future_date(),
            },
        )
    ).json()

    assert (await _request(other_app, "GET", f"/bookings/{booking['id']}")).status_code == 403
    assert (await _request(guest_app, "GET", "/bookings")).json() != []
    assert (await _request(other_app, "GET", "/bookings")).json() == []
    # Listing someone else's bookings through ?guest_id= is an approver action.
    response = await _request(other_app, "GET", "/bookings", params={"guest_id": "guest-1"})
    assert response.status_code == 403
    response = await _request(approver_app, "GET", "/bookings", params={"guest_id": "guest-1"})
    assert response.status_code == 200
