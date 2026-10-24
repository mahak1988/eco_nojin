"""Shared fixtures and helpers for the frontend contract tests.

The gateway's HTTP surface is the React client's contract: ``frontend/`` calls
it from ``src/services/*.ts``, and every field name, envelope and error body
below is typed there. Two test files use this module because the contract is
one product: the marketplace/tourism flows live in
``test_frontend_contract.py`` and the account/security surface in
``test_frontend_contract_account.py``.
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

os.environ.setdefault("SECRET_KEY", "test-secret-key")
# The contract suite registers dozens of probe users through the real API.
# The operational rate limiter is orthogonal to the contract: leaving it on
# makes every registration past five sleep a whole refill window (30s each),
# which turned a 60-second suite into a six-minute one. Raising the ceiling
# for this process keeps the *limiter's existence* tested elsewhere
# (test_rate_limit_scope.py) while this file tests the field contract.
os.environ.setdefault("HYDROMA_AUTH_RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from database.config import SessionLocal
from services.marketplace.models import MarketplaceProduct, MarketplaceSeller
from services.tourism.models import TourismTour


@pytest.fixture(scope="module")
def client():
    from services.api_gateway.main import app

    with TestClient(app) as c:
        c.get("/health")  # materialise the lazily-built middleware stack
        yield c


@pytest.fixture()
def anonymous_client():
    """A cookie-free client, for asserting the anonymous contract."""
    from services.api_gateway.main import app

    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str, full_name: str = "Buyer One") -> dict:
    last = None
    for _attempt in range(14):  # 5 registrations / 60s: wait the window out
        last = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": full_name,
                "password": "Passw0rd!23",
                "role": "regular",
                "language": "fa",
                "accept_tos": True,
                "accept_privacy": True,
            },
        )
        if last.status_code == 429:
            time.sleep(30)
            continue
        break
    assert last.status_code == 200, last.text
    body = last.json()
    # AuthPage wraps the session as {"user": {...}} and reads the role for
    # its post-register navigation: a user that registers and cannot reach
    # the science workspace is a dead end, not a policy.
    assert body["user"]["role"] == "regular"
    return body


def _csrf(client: TestClient) -> str:
    return client.cookies.get("econojin_csrf") or ""


def _write_headers(client: TestClient, key: str | None = None) -> dict:
    headers = {"x-csrf-token": _csrf(client)}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def _seed_tour() -> str:
    tour_id = f"tour-{uuid4().hex[:8]}"
    with SessionLocal() as session:
        session.add(
            TourismTour(
                id=tour_id,
                guide_id=f"guide-{uuid4().hex[:6]}",
                village_id="v-1",
                title="Tour contract probe",
                slug=f"tour-contract-{tour_id}",
                description="Seeded by the contract test",
                images=["/images/tour.jpg"],
                tour_type="ecotourism",
                duration_hours=4,
                price_per_person=Decimal("250000"),
                # The public catalogue only serves active tours.
                status="active",
                is_regenerative=True,
            )
        )
        session.commit()
    return tour_id


def _seed_approved_product(client: TestClient, name: str, price: int) -> str | None:
    """Create a listing and approve it, so the test owns a buyable product.

    The 24-item catalogue falls back to the non-orderable demo rows when no
    persisted product is approved, and those rows are not addressable by the
    cart, detail or item routes — they live only in the in-memory demo
    catalogue. A test that needs an orderable product must seed its own.
    """
    listing = client.post(
        "/api/v1/marketplace/checkout/products",
        headers=_write_headers(client),
        json={
            "name": name,
            "category": "food",
            "price": price,
            "village_id": "v-1",
            "description": f"seeded by {name}",
            "stock": 25,
        },
    )
    if listing.status_code != 200:
        return None
    product_id = listing.json()["product_id"]
    with SessionLocal() as session:
        product = session.get(MarketplaceProduct, product_id)
        if product is None:
            return None
        seller = session.get(MarketplaceSeller, product.seller_id)
        assert seller is not None
        seller.is_verified = True
        seller.status = "active"
        product.status = "active"
        session.commit()
    return product_id


def _promote_latest_contract_user() -> str | None:
    """Give the most recently registered probe user the admin role."""
    from database import models as db_models

    with SessionLocal() as session:
        actor = (
            session.query(db_models.User)
            .filter(db_models.User.email.like("contract-%"))
            .order_by(db_models.User.created_at.desc())
            .first()
        )
        if actor is None:
            return None
        actor.role = "admin"
        session.commit()
        return actor.email


def _login_as_admin(client: TestClient) -> str:
    """Register a fresh probe user, promote it, and sign in as admin."""
    _register(client, f"contract-{uuid4().hex[:8]}@example.com")
    email = _promote_latest_contract_user()
    assert email is not None, "the probe user must exist on the shared database"
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Passw0rd!23"},
    )
    assert login.status_code == 200, login.text
    return email


__all__ = [
    "anonymous_client",
    "client",
    "date",
    "timedelta",
    "_login_as_admin",
    "_promote_latest_contract_user",
    "_register",
    "_seed_approved_product",
    "_seed_tour",
    "_write_headers",
]
