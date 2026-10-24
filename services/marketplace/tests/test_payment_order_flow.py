"""Tests for P1-7: payments wired to orders, validated amounts, and a working
marketplace escrow lifecycle.

Findings pinned here (see the P1-7 spec):
1. ``PaymentGateways.verify`` only moved the payment + escrow and left the
   linked ``MarketplaceOrder`` at ``pending`` — a paid order was
   indistinguishable from an unpaid one. It must now advance PENDING -> PAID.
2. ``POST /payments`` used to trust the client ``amount`` and never checked the
   order resolved. It must 404 on an unknown order and 422 on a total mismatch.
3. The dispute/settle/complete endpoints imported a session-less ledger
   ``EscrowService`` and always 404'd; they must operate on the marketplace
   escrow ledger (``MarketplaceEscrowEntry``) so a payment -> hold ->
   release/refund lifecycle completes, with the double-spend guard intact.
4. ``/vendors/{id}/products``, ``/vendors/{id}/orders`` and ``GET /admin/stats``
   called ``.get()`` on dataclass instances and 500'd;
   ``PATCH /admin/products/{id}/approve`` was a no-op that reported success.

The service-level tests run against a private sync engine (mirroring
``test_payments.py``). The router tests build a minimal TestClient app, override
auth, and repoint ``database.config.SessionLocal`` at an isolated engine so the
``hub.get_session()`` the routes use lands on that engine.
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

from database.base import Base
from services.api_gateway.auth import require_admin, require_user
from services.api_gateway.routers.marketplace import router as marketplace_router
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)
from services.marketplace.order_management import get_order_manager
from services.marketplace.payments_service import EscrowService, PaymentError, PaymentGateways
from services.marketplace.product_catalog import get_catalog

# --- shared seed helpers ---------------------------------------------------


def _seed_order(session, *, total: str = "350000.00") -> MarketplaceOrder:
    order = MarketplaceOrder(
        order_number=f"ORD-{uuid4().hex[:10]}",
        buyer_id="buyer-1",
        village_id="village-1",
        subtotal=Decimal(total),
        total=Decimal(total),
        status=MarketplaceOrderStatus.PENDING,
        payment_status="pending",
    )
    session.add(order)
    session.commit()
    return order


def _seed_product(
    maker,
    *,
    status: MarketplaceProductStatus = MarketplaceProductStatus.PENDING_APPROVAL,
) -> str:
    with maker() as session:
        product = MarketplaceProduct(
            seller_id="seller-1",
            name="عسل تست",
            slug=f"asal-{uuid4().hex[:8]}",
            category="food",
            price=Decimal("350000.00"),
            stock=10,
            unit="piece",
            village_id="village-1",
            status=status,
        )
        session.add(product)
        session.commit()
        return str(product.id)


# --- fixtures --------------------------------------------------------------


@pytest.fixture
def sync_session():
    """A private sync in-memory SQLite session for the service-level flow."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest_asyncio.fixture
async def router_client(monkeypatch):
    """A TestClient whose routes hit an isolated in-memory engine.

    ``hub.get_session()`` re-imports ``database.config.SessionLocal`` per call,
    so repointing it makes every route (which opens its own session or takes an
    injected ``get_db``) resolve to this engine. ``StaticPool`` keeps one
    connection so every session sees the same rows.
    """
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
    # The buyer id must match the seeded rows: the payment routes enforce
    # order ownership (``order.buyer_id`` vs the caller), so an override
    # user that no seeded row belongs to gets 403 before any amount or
    # escrow validation runs.
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id="buyer-1", role="farmer")
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1", role="admin")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, maker
    engine.dispose()


def _create_payment_payload(order_id: str, amount: float) -> dict:
    return {"order_id": order_id, "payment_method": "bank", "amount": amount}


# --- (1) verification advances the order ------------------------------------


def test_verification_advances_order_to_paid(sync_session):
    """A verified payment moves the order PENDING -> PAID (not just the payment)."""
    order = _seed_order(sync_session)
    gateways = PaymentGateways(sync_session)
    payment = gateways.create(order_id=order.id, user_id="buyer-1", gateway="bank", amount=350000.0)
    payment = gateways.verify(payment, ref_id="TRK-1")

    assert payment.status == "verified"
    reloaded = sync_session.get(MarketplaceOrder, order.id)
    assert reloaded.payment_status == "paid"
    assert reloaded.status == MarketplaceOrderStatus.PAID
    assert reloaded.paid_at is not None


def test_unverified_payment_leaves_order_pending(sync_session):
    """Creating a payment alone must not advance the order."""
    order = _seed_order(sync_session)
    gateways = PaymentGateways(sync_session)
    gateways.create(order_id=order.id, user_id="buyer-1", gateway="bank", amount=350000.0)

    reloaded = sync_session.get(MarketplaceOrder, order.id)
    assert reloaded.status == MarketplaceOrderStatus.PENDING
    assert reloaded.payment_status == "pending"


def test_advance_is_guarded_to_pending(sync_session):
    """An order already beyond PENDING is never rewound by verification."""
    order = _seed_order(sync_session, total="100.00")
    order.status = MarketplaceOrderStatus.PROCESSING
    order.payment_status = "paid"
    sync_session.commit()

    gateways = PaymentGateways(sync_session)
    payment = gateways.create(order_id=order.id, user_id="buyer-1", gateway="bank", amount=100.0)
    payment = gateways.verify(payment, ref_id="TRK-2")

    reloaded = sync_session.get(MarketplaceOrder, order.id)
    assert reloaded.status == MarketplaceOrderStatus.PROCESSING


# --- (3) escrow lifecycle + double-spend guard (service level) ---------------


def test_escrow_hold_then_release_with_double_spend_guard(sync_session):
    """hold -> release completes, and a second release/refund is refused."""
    order = _seed_order(sync_session, total="100.00")
    gateways = PaymentGateways(sync_session)
    payment = gateways.create(order_id=order.id, user_id="buyer-1", gateway="bank", amount=100.0)
    payment = gateways.verify(payment, ref_id="TRK-3")
    assert payment.escrow_status == "held"

    escrow = EscrowService(sync_session)
    entry = escrow.release(payment.id, actor_id="admin-1")
    assert entry.entry_type == "release"
    assert payment.escrow_status == "released"

    with pytest.raises(PaymentError):
        escrow.release(payment.id)
    with pytest.raises(PaymentError):
        escrow.refund(payment.id)


# --- (2) POST /payments amount validation -----------------------------------


@pytest.mark.asyncio
async def test_payment_rejects_unknown_order(router_client):
    client, _ = router_client
    resp = await client.post(
        "/api/v1/marketplace/payments",
        json=_create_payment_payload("does-not-exist", 350000.0),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_payment_rejects_amount_mismatch(router_client):
    client, maker = router_client
    with maker() as session:
        order_id = str(_seed_order(session).id)

    resp = await client.post(
        "/api/v1/marketplace/payments",
        json=_create_payment_payload(order_id, 1.0),
    )
    assert resp.status_code == 422
    assert "does not match order" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_payment_uses_server_side_total(router_client):
    client, maker = router_client
    with maker() as session:
        order_id = str(_seed_order(session).id)

    resp = await client.post(
        "/api/v1/marketplace/payments",
        json=_create_payment_payload(order_id, 350000.0),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["amount"] == 350000.0
    assert body["order_id"] == order_id
    assert body["status"] == "awaiting_verification"
    assert "bank_instructions" in body


# --- (3) full escrow lifecycle through the router ---------------------------


@pytest.mark.asyncio
async def test_dispute_settle_complete_lifecycle_via_router(router_client):
    """The marketplace escrow ledger completes the 6-step money flow, and a
    second settle is refused by the double-spend guard."""
    client, maker = router_client
    with maker() as session:
        order_id = str(_seed_order(session).id)

    create = await client.post(
        "/api/v1/marketplace/payments",
        json=_create_payment_payload(order_id, 350000.0),
    )
    assert create.status_code == 200, create.text
    payment_id = create.json()["id"]

    confirm = await client.post(
        f"/api/v1/marketplace/payments/{payment_id}/confirm", json={"ref_id": "TRK-1"}
    )
    assert confirm.status_code == 200, confirm.text
    # A bank transfer is only a *claim* until an admin verifies it: the
    # buyer's tracking code moves the payment to awaiting_verification and
    # holds no escrow yet.
    assert confirm.json()["escrow"] == "awaiting_verification"

    verified = await client.post(f"/api/v1/marketplace/payments/{payment_id}/verify-bank")
    assert verified.status_code == 200, verified.text
    assert verified.json()["escrow"] == "held"
    with maker() as session:
        assert session.get(MarketplaceOrder, order_id).status == MarketplaceOrderStatus.PAID

    dispute = await client.post(f"/api/v1/marketplace/orders/{order_id}/dispute")
    assert dispute.status_code == 200, dispute.text
    assert dispute.json()["status"] == "dispute_window_open"

    settle = await client.post(f"/api/v1/marketplace/orders/{order_id}/settle")
    assert settle.status_code == 200, settle.text
    assert settle.json()["status"] == "settled_released"

    complete = await client.post(f"/api/v1/marketplace/orders/{order_id}/complete")
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"
    assert complete.json()["amount"]["source"] == "ledger:escrow_release"

    again = await client.post(f"/api/v1/marketplace/orders/{order_id}/settle")
    assert again.status_code == 400


@pytest.mark.asyncio
async def test_escrow_lifecycle_unknown_order_is_404(router_client):
    client, _ = router_client
    assert (await client.post("/api/v1/marketplace/orders/nope/dispute")).status_code == 404
    assert (await client.post("/api/v1/marketplace/orders/nope/settle")).status_code == 404
    assert (await client.post("/api/v1/marketplace/orders/nope/complete")).status_code == 404


# --- (4) the three previously-crashing endpoints + admin approve ------------


@pytest.mark.asyncio
async def test_vendor_products_endpoint_returns_data(router_client):
    """Regression for ``p.get(...)`` on dataclass ``Product`` instances."""
    client, _ = router_client
    producer = get_catalog().list_producers()[0]

    resp = await client.get(f"/api/v1/marketplace/vendors/{producer.id}/products")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["vendor_id"] == producer.id
    for product in body["products"]:
        assert product["producer_id"] == producer.id


@pytest.mark.asyncio
async def test_vendor_orders_endpoint_returns_data(router_client):
    """Regression for ``o.get(...)`` on dataclass ``Order`` instances.

    The seller-orders route hides other sellers' orders: a non-admin caller
    must own the vendor row. The demo-catalogue order lives in the in-memory
    order manager, so the owning ``MarketplaceSeller`` is seeded under the
    demo producer's id to let the route reach the order it must return.
    """
    client, maker = router_client
    product = get_catalog().list_products()[0]
    with maker() as session:
        session.add(
            MarketplaceSeller(
                id=product.producer_id,
                user_id="buyer-1",
                village_id="village-1",
                shop_name="Demo producer",
                status="active",
                is_verified=True,
            )
        )
        session.commit()
    order = get_order_manager().create_order(
        product_id=product.id,
        buyer_name="buyer-1",
        quantity_kg=product.minimum_order_kg,
        seller_id=product.producer_id,
    )

    resp = await client.get(f"/api/v1/marketplace/vendors/{order.seller_id}/orders")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert order.id in {o["id"] for o in body["orders"]}
    assert body["count"] >= 1
    match = next(o for o in body["orders"] if o["id"] == order.id)
    assert match["status"] == "pending"


@pytest.mark.asyncio
async def test_admin_stats_endpoint_returns_data(router_client):
    """Regression for ``p.get("organic_certified")`` on dataclass instances."""
    client, _ = router_client
    resp = await client.get("/api/v1/marketplace/admin/stats")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_products"] >= 1
    assert body["total_producers"] >= 1
    assert isinstance(body["organic_products"], int)
    assert "orders" in body


@pytest.mark.asyncio
async def test_admin_approve_product_mutates_state(router_client):
    """The no-op approve now writes the product's approval status."""
    client, maker = router_client
    product_id = _seed_product(maker, status=MarketplaceProductStatus.PENDING_APPROVAL)

    resp = await client.patch(f"/api/v1/marketplace/admin/products/{product_id}/approve")
    assert resp.status_code == 200, resp.text
    assert resp.json()["approved"] is True
    assert resp.json()["status"] == "approved"

    with maker() as session:
        row = session.get(MarketplaceProduct, product_id)
        assert row.status == MarketplaceProductStatus.APPROVED
        assert row.approved_by == "admin-1"
        assert row.approved_at is not None


@pytest.mark.asyncio
async def test_admin_reject_product_mutates_state(router_client):
    client, maker = router_client
    product_id = _seed_product(maker, status=MarketplaceProductStatus.DRAFT)

    resp = await client.patch(
        f"/api/v1/marketplace/admin/products/{product_id}/approve", params={"approve": False}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["approved"] is False

    with maker() as session:
        row = session.get(MarketplaceProduct, product_id)
        assert row.status == MarketplaceProductStatus.REJECTED
        assert row.approved_by is None


@pytest.mark.asyncio
async def test_admin_approve_unknown_product_is_404(router_client):
    client, _ = router_client
    resp = await client.patch("/api/v1/marketplace/admin/products/nope/approve")
    assert resp.status_code == 404
