"""The marketplace escrow routes are closed to everyone but the order's parties.

``POST /orders/{id}/dispute``, ``POST /orders/{id}/settle`` and
``POST /orders/{id}/complete`` used to accept **any** authenticated caller, so
any account could open a dispute on, settle (release the escrowed money to the
seller) or complete an order it had no part in. The catalog-plane
``POST /orders/{id}/confirm`` had the same hole.

These tests pin the closed behaviour: a non-party gets 403, while the buyer
(the pinned contract drives the escrow lifecycle as the buyer) and an admin keep
their access.

See ``docs/project/SECTOR-TECH-DEBT-REMEDIATION-2026-10-20.md`` (FR-06a/FR-06b).
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import services.notification.models_db  # noqa: F401  (table provisioning)
from database.base import Base
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.routers.marketplace import router as marketplace_router
from services.marketplace.models import MarketplaceOrder, MarketplaceOrderStatus


@pytest_asyncio.fixture
async def escrow_app(monkeypatch):
    """A marketplace app on an isolated engine whose caller can be switched."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr("database.config.SessionLocal", maker)

    app = FastAPI()
    app.include_router(marketplace_router)

    # The acting user is switchable so one app can play buyer and stranger.
    caller = {"id": "buyer-1", "role": "farmer"}
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id=caller["id"], role=caller["role"]
    )
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id="admin-1", role="admin"
    )
    app.state.caller = caller
    app.state.maker = maker
    yield app
    engine.dispose()


def _seed_order(app, *, buyer_id: str = "buyer-1", total: str = "100.00") -> str:
    with app.state.maker() as session:
        order = MarketplaceOrder(
            id=str(uuid4()),
            order_number=f"ORD-{uuid4().hex[:10]}",
            buyer_id=buyer_id,
            village_id="village-1",
            subtotal=Decimal(total),
            total=Decimal(total),
            status=MarketplaceOrderStatus.PENDING,
            payment_status="pending",
        )
        session.add(order)
        session.commit()
        return str(order.id)


async def _hold_escrow(app, order_id: str) -> None:
    """Drive the bank-transfer rail until the escrow is held."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        created = await c.post(
            "/api/v1/marketplace/payments",
            json={"order_id": order_id, "payment_method": "bank", "amount": 100.0},
        )
        assert created.status_code == 200, created.text
        payment_id = created.json()["id"]
        await c.post(
            f"/api/v1/marketplace/payments/{payment_id}/confirm", json={"ref_id": "TRK-1"}
        )
        verified = await c.post(f"/api/v1/marketplace/payments/{payment_id}/verify-bank")
        assert verified.status_code == 200, verified.text


@pytest.mark.parametrize(
    ("route", "payload"),
    [
        ("/api/v1/marketplace/orders/{order_id}/dispute", None),
        ("/api/v1/marketplace/orders/{order_id}/settle", None),
        ("/api/v1/marketplace/orders/{order_id}/complete", None),
    ],
)
async def test_a_stranger_cannot_act_on_someone_elses_escrow(escrow_app, route, payload):
    """An authenticated user who is not a party to the order gets 403."""
    order_id = _seed_order(escrow_app, buyer_id="buyer-1")
    await _hold_escrow(escrow_app, order_id)

    escrow_app.state.caller["id"] = "stranger-9"
    escrow_app.state.caller["role"] = "farmer"

    async with AsyncClient(transport=ASGITransport(app=escrow_app), base_url="http://test") as c:
        response = await c.post(route.format(order_id=order_id), json=payload)

    assert response.status_code == 403, response.text


async def test_the_buyer_keeps_the_escrow_lifecycle(escrow_app):
    """The buyer is the party the pinned escrow contract drives."""
    order_id = _seed_order(escrow_app, buyer_id="buyer-1")
    await _hold_escrow(escrow_app, order_id)

    escrow_app.state.caller["id"] = "buyer-1"
    escrow_app.state.caller["role"] = "farmer"

    async with AsyncClient(transport=ASGITransport(app=escrow_app), base_url="http://test") as c:
        dispute = await c.post(f"/api/v1/marketplace/orders/{order_id}/dispute")
        assert dispute.status_code == 200, dispute.text

        settle = await c.post(f"/api/v1/marketplace/orders/{order_id}/settle")
        assert settle.status_code == 200, settle.text

        complete = await c.post(f"/api/v1/marketplace/orders/{order_id}/complete")
        assert complete.status_code == 200, complete.text


async def test_an_admin_may_act_on_any_escrow(escrow_app):
    """An admin is a party to every order."""
    order_id = _seed_order(escrow_app, buyer_id="buyer-1")
    await _hold_escrow(escrow_app, order_id)

    escrow_app.state.caller["id"] = "admin-1"
    escrow_app.state.caller["role"] = "admin"

    async with AsyncClient(transport=ASGITransport(app=escrow_app), base_url="http://test") as c:
        settle = await c.post(f"/api/v1/marketplace/orders/{order_id}/settle")

    assert settle.status_code == 200, settle.text


async def test_a_stranger_cannot_confirm_someone_elses_order(escrow_app):
    """The catalog-plane confirm route is closed to non-buyers too."""
    from services.marketplace.models import Product
    from services.marketplace.order_management import get_order_manager
    from services.marketplace.product_catalog import get_catalog

    catalog = get_catalog()
    catalog.add_product(
        Product(
            id="p-authz-1",
            name="Authz Honey",
            producer_id="seller-1",
            price_per_kg=10.0,
            quantity_available_kg=100.0,
            minimum_order_kg=1.0,
        )
    )

    manager = get_order_manager()
    order = manager.create_order(
        product_id="p-authz-1",
        buyer_name="buyer-1",
        quantity_kg=1,
        seller_id="seller-1",
    )
    order_id = order.id

    escrow_app.state.caller["id"] = "stranger-9"
    escrow_app.state.caller["role"] = "farmer"
    async with AsyncClient(transport=ASGITransport(app=escrow_app), base_url="http://test") as c:
        response = await c.post(f"/api/v1/marketplace/orders/{order_id}/confirm")

    assert response.status_code == 403, response.text

    # The buyer may still confirm their own order.
    escrow_app.state.caller["id"] = "buyer-1"
    async with AsyncClient(transport=ASGITransport(app=escrow_app), base_url="http://test") as c:
        own = await c.post(f"/api/v1/marketplace/orders/{order_id}/confirm")
    assert own.status_code == 200, own.text
