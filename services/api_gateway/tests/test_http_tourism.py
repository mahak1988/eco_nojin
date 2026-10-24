"""HTTP regression tests for the rural/tribal tourism router (P2-17).

The ``services.tourism`` lifecycle (guides → verification → tours → approval
→ bookings → payment → regenerative completion) is fully implemented and is
mounted by ``services.api_gateway.main`` beside the honest status stub. These
tests pin the HTTP surface end to end over a minimal FastAPI app with in-memory
SQLite and dependency overrides for auth + DB (the pattern of
``services/tourism/tests/test_api_router.py`` and
``services/finance/tests/test_finance_router_wallet.py``):

* the full happy path, asserting the 800/200/200 bps fee split;
* ecological-capacity enforcement rejects an overbooking (400);
* verification/approval reject non-approver roles (403) and unauthenticated
  callers (401);
* the public catalogue exposes only ``active`` tours.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from services.api_gateway.auth import get_current_user
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
    requests without a token exercise the genuine 401 path. Overriding the one
    ``get_current_user`` callable is enough for ``require_user`` (its alias)
    and ``require_roles``/``_require_approver`` (which depend on it).
    """
    app = FastAPI()
    app.include_router(router)

    async def database_override():
        yield session

    app.dependency_overrides[get_db] = database_override
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


async def _verified_guide(guest_app, approver_app, village_id: str = "village-001") -> dict:
    guide = await _register_guide(guest_app, village_id)
    verified = await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    assert verified.status_code == 200, verified.text
    return verified.json()


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


async def test_guide_registration_starts_unverified(db_session):
    app = _build_app(db_session, user_id="guest-1", role="farmer")
    guide = await _register_guide(app)
    assert guide["is_verified"] is False
    assert guide["user_id"] == "guest-1"
    assert guide["languages"] == ["fa", "en"]
    assert guide["specialties"] == ["nomadic"]
    assert guide["village_id"] == "village-001"


async def test_full_lifecycle_guide_to_regenerative_completion(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")

    # 1-2. guide registration then approver verification.
    guide = await _register_guide(guest_app)
    verified = await _request(approver_app, "POST", f"/guides/{guide['id']}/verify")
    assert verified.status_code == 200, verified.text
    assert verified.json()["is_verified"] is True

    # 3-4. tour creation for the verified guide, then approval.
    tour = await _create_tour(guest_app, guide["id"])
    assert tour["status"] == "pending_approval"
    assert tour["tour_type"] == "nomadic"
    assert tour["slug"].startswith("nomadic-kermanshah-tour")
    approved = await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "active"
    assert approved.json()["approved_by"] == "manager-1"

    # 5. booking.
    booking = (
        await _request(
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
    ).json()
    assert booking["booking_number"].startswith("TR-")
    assert booking["guest_id"] == "guest-1"

    # 6. payment confirmation.
    confirmed = (
        await _request(
            guest_app,
            "POST",
            f"/bookings/{booking['id']}/confirm-payment",
            {"payment_tx_hash": "tx-hash-123"},
        )
    ).json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["payment_status"] == "paid"
    assert confirmed["blockchain_tx_hash"] == "tx-hash-123"

    # 7. regenerative completion.
    completed = (
        await _request(guest_app, "POST", f"/bookings/{booking['id']}/complete")
    ).json()
    assert completed["status"] == "completed"
    assert completed["settlement_status"] == "completed"
    assert completed["regenerative_completed"] is True

    # 8. counters advanced on the tour.
    tour_state = (await _request(guest_app, "GET", f"/tours/{tour['id']}")).json()
    assert tour_state["total_bookings"] == 1
    assert tour_state["current_bookings"] == 3


async def test_booking_fee_split_is_800_200_200_bps(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _verified_guide(guest_app, approver_app)
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
                "participants_count": 3,
                "tour_date": _future_date(),
            },
        )
    ).json()

    assert Decimal(booking["subtotal"]) == Decimal("1500000")
    assert Decimal(booking["platform_fee"]) == Decimal("120000")  # 800 bps
    assert Decimal(booking["landscape_fee"]) == Decimal("30000")  # 200 bps
    assert Decimal(booking["insurance_fee"]) == Decimal("30000")  # 200 bps
    assert Decimal(booking["total"]) == Decimal("1680000")


async def test_completing_an_unpaid_booking_is_rejected(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _verified_guide(guest_app, approver_app)
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
    assert booking["id"]

    # The service only completes a confirmed (paid) booking.
    response = await _request(guest_app, "POST", f"/bookings/{booking['id']}/complete")
    assert response.status_code == 400, response.text


async def test_unknown_entities_return_404(db_session):
    app = _build_app(db_session)
    assert (await _request(app, "GET", "/guides/nope")).status_code == 404
    assert (await _request(app, "GET", "/tours/nope")).status_code == 404
    assert (await _request(app, "GET", "/bookings/nope")).status_code == 404


async def test_tour_for_unverified_guide_is_rejected(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
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


async def test_invalid_tour_payload_is_rejected_with_422(db_session):
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
    guide = await _verified_guide(guest_app, approver_app)
    tour = await _create_tour(guest_app, guide["id"], ecological_capacity=5)
    await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")

    accepted = await _request(
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
    assert accepted.status_code == 200, accepted.text

    # 3 more would push 6 > 5 over the ecological capacity.
    overbooked = await _request(
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
    assert overbooked.status_code == 400, overbooked.text

    # The rejected booking consumed no capacity.
    tour_state = (await _request(guest_app, "GET", f"/tours/{tour['id']}")).json()
    assert tour_state["current_bookings"] == 3


async def test_booking_rejects_past_tour_date(db_session):
    guest_app = _build_app(db_session, user_id="guest-2", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _verified_guide(guest_app, approver_app)
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


async def test_verify_guide_rejects_non_approver_role(db_session):
    app = _build_app(db_session, user_id="farmer-9", role="farmer")
    guide = await _register_guide(app)
    response = await _request(app, "POST", f"/guides/{guide['id']}/verify")
    assert response.status_code == 403, response.text
    # The guide stays unverified.
    assert (await _request(app, "GET", f"/guides/{guide['id']}")).json()["is_verified"] is False


async def test_approve_tour_rejects_non_approver_role(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _verified_guide(guest_app, approver_app)
    tour = await _create_tour(guest_app, guide["id"])

    assert (
        await _request(guest_app, "POST", f"/tours/{tour['id']}/approve")
    ).status_code == 403

    approved = await _request(approver_app, "POST", f"/tours/{tour['id']}/approve")
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "active"


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
    assert (
        await _request(app, "POST", "/guides/some-guide/verify")
    ).status_code == 401


async def test_another_guests_booking_is_forbidden(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    other_app = _build_app(db_session, user_id="guest-2", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _verified_guide(guest_app, approver_app)
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

    # A different guest cannot read someone else's booking.
    assert (
        await _request(other_app, "GET", f"/bookings/{booking['id']}")
    ).status_code == 403
    # Each guest only sees their own list.
    assert [b["id"] for b in (await _request(guest_app, "GET", "/bookings")).json()] == [
        booking["id"]
    ]
    assert (await _request(other_app, "GET", "/bookings")).json() == []
    # Listing via ?guest_id= is an approver-only action.
    assert (
        await _request(other_app, "GET", "/bookings", params={"guest_id": "guest-1"})
    ).status_code == 403
    assert (
        await _request(approver_app, "GET", "/bookings", params={"guest_id": "guest-1"})
    ).status_code == 200


async def test_public_catalogue_shows_only_active_tours(db_session):
    guest_app = _build_app(db_session, user_id="guest-1", role="farmer")
    approver_app = _build_app(db_session, user_id="manager-1", role="landscape_manager")
    guide = await _verified_guide(guest_app, approver_app)
    active = await _create_tour(guest_app, guide["id"])
    await _request(approver_app, "POST", f"/tours/{active['id']}/approve")
    pending = await _create_tour(guest_app, guide["id"], title="Pending Retreat")

    default_listing = (await _request(guest_app, "GET", "/tours")).json()
    assert [t["id"] for t in default_listing] == [active["id"]]
    pending_listing = (
        await _request(guest_app, "GET", "/tours", params={"status": "pending_approval"})
    ).json()
    assert [t["id"] for t in pending_listing] == [pending["id"]]
