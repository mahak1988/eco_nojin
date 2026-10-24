"""HTTP regression tests for the marketplace + commerce endpoints repaired in
waves 1-3.

Marketplace (P1-7) — exercised over an isolated in-memory engine by repointing
``database.config.SessionLocal`` (the pattern of
``services/marketplace/tests/test_payment_order_flow.py``), because the
marketplace routes open their own ``hub.get_session()``:

* ``POST /payments`` rejects an unknown order (404) and a client amount that
  differs from the order total (422), and stores the server-side total;
* a verified payment advances the order PENDING -> PAID and holds escrow;
* the dispute → settle → complete 6-step escrow lifecycle, with the
  double-release guard intact;
* the previously-``AttributeError``ing ``/vendors/{id}/products``,
  ``/vendors/{id}/orders`` and ``GET /admin/stats`` return data;
* ``PATCH /admin/products/{id}/approve`` mutates state.

Commerce (P0-3/P1-8) — exercised over a minimal app with dependency overrides:

* ``GET /orders/{id}`` reports a truthful per-line ``fulfilled_qty`` derived
  from the reservation's ``consumed_qty``;
* ``POST /orders/{id}/settle`` credits the village restoration fund
  (``LandscapeFund`` + ``LandscapeFundCredit``).
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# The payment ``verify`` path delivers a best-effort in-app notification that
# writes to ``app_notifications``; provisioning the table keeps the payment
# repair path clean (see the report note on session poisoning).
import services.notification.models_db  # noqa: F401
from database.base import Base
from database.models import (
    ComOrder,
    ComOrderItem,
    InvReservation,
)
from services.api_gateway.auth import get_current_user, require_admin, require_user
from services.api_gateway.routers.marketplace import get_async_db
from services.api_gateway.routers.marketplace import router as marketplace_router
from services.commerce.routers.commerce import get_db as commerce_get_db
from services.commerce.routers.commerce import router as commerce_router
from services.landscape.models import LandscapeFund, LandscapeFundCredit
from services.marketplace.models import (
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)
from services.marketplace.order_management import get_order_manager
from services.marketplace.product_catalog import get_catalog

pytestmark = pytest.mark.asyncio


# ===========================================================================
# Marketplace (sync engine)
# ===========================================================================


def _seed_order(session, *, total: str = "350000.00") -> MarketplaceOrder:
    order = MarketplaceOrder(
        id=str(uuid4()),
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
    session,
    *,
    status: MarketplaceProductStatus = MarketplaceProductStatus.PENDING_APPROVAL,
) -> str:
    product = MarketplaceProduct(
        seller_id="seller-1",
        name="Honey Test",
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


@pytest.fixture
def marketplace_client(monkeypatch):
    """A client whose marketplace routes hit an isolated in-memory engine.

    Every route opens its own ``hub.get_session()`` (which re-imports
    ``database.config.SessionLocal`` per call), so repointing that factory at a
    ``StaticPool`` engine makes both the routes and this fixture's seeding
    sessions observe the same rows.
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
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="buyer-1", role="farmer"
    )
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id="admin-1", role="admin"
    )
    yield app, maker
    engine.dispose()


def _payment_payload(order_id: str, amount: float) -> dict:
    return {"order_id": order_id, "payment_method": "bank", "amount": amount}


class TestMarketplacePayments:
    async def test_unknown_order_is_404(self, marketplace_client):
        app, _ = marketplace_client
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload("no-such-order", 350000.0)
            )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Order not found"

    async def test_amount_mismatch_is_422(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session).id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 1.0)
            )
        assert resp.status_code == 422
        assert "does not match order" in resp.json()["detail"]

    async def test_stores_server_side_total(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session, total="350000.00").id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["amount"] == 350000.0
        assert body["order_id"] == order_id
        assert body["status"] == "awaiting_verification"
        assert "bank_instructions" in body

    async def test_cannot_create_payment_for_another_buyers_order(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session).id)
        app.dependency_overrides[require_user] = lambda: SimpleNamespace(
            id="different-buyer", role="farmer"
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
        assert resp.status_code == 403


class TestMarketplaceOrderAdvancement:
    async def test_admin_payment_queue_only_lists_claimed_pending_bank_transfers(
        self, marketplace_client
    ):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session).id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
            assert create.status_code == 200, create.text
            payment_id = create.json()["id"]

            empty = await c.get("/api/v1/marketplace/admin/payments/pending")
            assert empty.status_code == 200, empty.text
            assert empty.json()["payments"] == []

            claim = await c.post(
                f"/api/v1/marketplace/payments/{payment_id}/confirm",
                json={"ref_id": "TRANSFER-QUEUE-123"},
            )
            assert claim.status_code == 200, claim.text

            retry = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
            assert retry.status_code == 200, retry.text
            assert retry.json()["id"] == payment_id
            assert retry.json()["tracking_code"] == "TRANSFER-QUEUE-123"

            pending = await c.get("/api/v1/marketplace/admin/payments/pending")
            assert pending.status_code == 200, pending.text
            assert pending.json()["count"] == 1
            assert pending.json()["payments"][0]["tracking_code"] == "TRANSFER-QUEUE-123"
            assert pending.json()["payments"][0]["order_id"] == order_id

            app.dependency_overrides.pop(require_admin)
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                id="user-1", role="farmer"
            )
            forbidden = await c.get("/api/v1/marketplace/admin/payments/pending")
            assert forbidden.status_code == 403

    async def test_admin_cannot_verify_bank_payment_without_submitted_claim(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session).id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
            assert create.status_code == 200, create.text
            verify = await c.post(
                f"/api/v1/marketplace/payments/{create.json()['id']}/verify-bank"
            )
        assert verify.status_code == 409

    async def test_payment_owner_only_can_submit_bank_transfer_claim(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session).id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
            assert create.status_code == 200, create.text
            payment_id = create.json()["id"]

            app.dependency_overrides[require_user] = lambda: SimpleNamespace(
                id="different-buyer", role="farmer"
            )
            confirm = await c.post(
                f"/api/v1/marketplace/payments/{payment_id}/confirm",
                json={"ref_id": "TRK-1"},
            )
        assert confirm.status_code == 403

    async def test_bank_claim_waits_for_admin_verification(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            order_id = str(_seed_order(session).id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 350000.0)
            )
            assert create.status_code == 200, create.text
            payment_id = create.json()["id"]
            confirm = await c.post(
                f"/api/v1/marketplace/payments/{payment_id}/confirm", json={"ref_id": "TRK-1"}
            )
            assert confirm.status_code == 200, confirm.text
            assert confirm.json()["escrow"] == "awaiting_verification"
            assert confirm.json()["payment"]["status"] == "awaiting_verification"
            verify = await c.post(
                f"/api/v1/marketplace/payments/{payment_id}/verify-bank"
            )
            assert verify.status_code == 200, verify.text
            assert verify.json()["escrow"] == "held"
        with maker() as session:
            order = session.get(MarketplaceOrder, order_id)
            assert order.payment_status == "paid"
            assert order.status == MarketplaceOrderStatus.PAID
            assert order.paid_at is not None


async def test_persistent_catalog_to_bank_payment_claim_and_admin_verification(
    monkeypatch, tmp_path
):
    db_file = tmp_path / "checkout.sqlite"
    sync_engine = create_engine(URL.create("sqlite", database=str(db_file)))
    Base.metadata.create_all(sync_engine)
    sync_maker = sessionmaker(bind=sync_engine, expire_on_commit=False)
    monkeypatch.setattr("database.config.SessionLocal", sync_maker)
    async_engine = create_async_engine(
        URL.create("sqlite+aiosqlite", database=str(db_file))
    )
    async_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    monkeypatch.setenv("BANK_TRANSFER_CARD_NUMBER", "1111222233334444")
    monkeypatch.setenv("BANK_TRANSFER_SHEBA", "IR000000000000000000000000")
    monkeypatch.setenv("BANK_TRANSFER_HOLDER", "Test Marketplace")

    with sync_maker() as session:
        seller = MarketplaceSeller(
            user_id="seller-user",
            village_id="village-1",
            shop_name="Approved Shop",
            status="active",
            is_verified=True,
        )
        session.add(seller)
        session.flush()
        product = MarketplaceProduct(
            seller_id=seller.id,
            name="Verified honey",
            slug=f"verified-honey-{uuid4().hex[:8]}",
            category="honey",
            price=Decimal("250000.00"),
            stock=8,
            unit="kg",
            village_id="village-1",
            status=MarketplaceProductStatus.ACTIVE,
        )
        session.add(product)
        session.commit()
        product_id = str(product.id)

    async def async_db_override():
        async with async_maker() as session:
            yield session

    app = FastAPI()
    app.include_router(marketplace_router)
    app.dependency_overrides[get_async_db] = async_db_override
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="buyer-1", role="farmer"
    )
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id="admin-1", role="admin"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        catalogue = await client.get("/api/v1/marketplace/products")
        assert catalogue.status_code == 200, catalogue.text
        listed_product = next(p for p in catalogue.json()["products"] if p["id"] == product_id)
        assert listed_product["orderable"] is True

        order_response = await client.post(
            "/api/v1/marketplace/checkout/orders",
            json={
                "product_id": product_id,
                "quantity": 2,
                "shipping_address": "12 Garden Road, Village One",
            },
        )
        assert order_response.status_code == 200, order_response.text
        order = order_response.json()
        assert order["subtotal"] == "500000.00"
        assert order["total"] == "520000.00"

        payment_response = await client.post(
            "/api/v1/marketplace/payments",
            json={
                "order_id": order["order_id"],
                "amount": float(order["total"]),
                "payment_method": "bank",
            },
        )
        assert payment_response.status_code == 200, payment_response.text
        payment = payment_response.json()
        assert payment["bank_instructions"]["card_number"] == "1111222233334444"

        claim = await client.post(
            f"/api/v1/marketplace/payments/{payment['id']}/confirm",
            json={"ref_id": "TRANSFER-123"},
        )
        assert claim.status_code == 200, claim.text
        assert claim.json()["escrow"] == "awaiting_verification"
        with sync_maker() as session:
            saved_order = session.get(MarketplaceOrder, order["order_id"])
            assert saved_order.payment_status == "pending"

        verified = await client.post(
            f"/api/v1/marketplace/payments/{payment['id']}/verify-bank"
        )
        assert verified.status_code == 200, verified.text
        assert verified.json()["escrow"] == "held"

        history = await client.get("/api/v1/marketplace/orders")
        saved = next(row for row in history.json()["orders"] if row["id"] == order["order_id"])
        assert saved["payment"]["status"] == "verified"
        assert saved["currency"] == "IRR"

    await async_engine.dispose()
    sync_engine.dispose()


class TestMarketplaceEscrowLifecycle:
    async def _held_payment(self, app, maker):
        with maker() as session:
            order_id = str(_seed_order(session, total="100.00").id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create = await c.post(
                "/api/v1/marketplace/payments", json=_payment_payload(order_id, 100.0)
            )
            payment_id = create.json()["id"]
            await c.post(
                f"/api/v1/marketplace/payments/{payment_id}/confirm", json={"ref_id": "TRK-1"}
            )
            verified = await c.post(
                f"/api/v1/marketplace/payments/{payment_id}/verify-bank"
            )
            assert verified.status_code == 200, verified.text
        return order_id, payment_id

    async def test_dispute_settle_complete_lifecycle(self, marketplace_client):
        app, maker = marketplace_client
        order_id, payment_id = await self._held_payment(app, maker)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            dispute = await c.post(f"/api/v1/marketplace/orders/{order_id}/dispute")
            assert dispute.status_code == 200, dispute.text
            assert dispute.json()["status"] == "dispute_window_open"

            settle = await c.post(f"/api/v1/marketplace/orders/{order_id}/settle")
            assert settle.status_code == 200, settle.text
            assert settle.json()["status"] == "settled_released"

            complete = await c.post(f"/api/v1/marketplace/orders/{order_id}/complete")
            assert complete.status_code == 200, complete.text
            assert complete.json()["status"] == "completed"
            assert complete.json()["amount"]["source"] == "ledger:escrow_release"

            # Double-release refused.
            again = await c.post(f"/api/v1/marketplace/orders/{order_id}/settle")
            assert again.status_code == 400

    async def test_unknown_order_lifecycle_is_404(self, marketplace_client):
        app, _ = marketplace_client
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            assert (await c.post("/api/v1/marketplace/orders/nope/dispute")).status_code == 404
            assert (await c.post("/api/v1/marketplace/orders/nope/settle")).status_code == 404
            assert (await c.post("/api/v1/marketplace/orders/nope/complete")).status_code == 404

    async def test_admin_escrow_release_then_double_release_refused(self, marketplace_client):
        app, maker = marketplace_client
        _order_id, payment_id = await self._held_payment(app, maker)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            first = await c.post(f"/api/v1/marketplace/payments/{payment_id}/escrow/release")
            assert first.status_code == 200, first.text
            assert first.json()["entry"]["entry_type"] == "release"
            second = await c.post(f"/api/v1/marketplace/payments/{payment_id}/escrow/release")
            assert second.status_code == 400

    async def test_admin_escrow_refund_after_hold(self, marketplace_client):
        app, maker = marketplace_client
        _order_id, payment_id = await self._held_payment(app, maker)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            refund = await c.post(f"/api/v1/marketplace/payments/{payment_id}/escrow/refund")
            assert refund.status_code == 200, refund.text
            assert refund.json()["entry"]["entry_type"] == "refund"


class TestMarketplaceVendorAndAdmin:
    async def test_vendor_products_endpoint_returns_data(self, marketplace_client):
        app, _ = marketplace_client
        producer = get_catalog().list_producers()[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(f"/api/v1/marketplace/vendors/{producer.id}/products")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["vendor_id"] == producer.id
        assert len(body["products"]) >= 1
        assert all(p["producer_id"] == producer.id for p in body["products"])

    async def test_vendor_orders_endpoint_returns_data(self, marketplace_client):
        app, maker = marketplace_client
        product = get_catalog().list_products()[0]
        order = get_order_manager().create_order(
            product_id=product.id,
            buyer_name="buyer-1",
            quantity_kg=product.minimum_order_kg,
            seller_id=product.producer_id,
        )
        with maker() as session:
            session.add(
                MarketplaceSeller(
                    id=order.seller_id,
                    user_id="buyer-1",
                    village_id="village-1",
                    shop_name="Owner shop",
                )
            )
            session.commit()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(f"/api/v1/marketplace/vendors/{order.seller_id}/orders")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert order.id in {o["id"] for o in body["orders"]}
        assert body["count"] >= 1

    async def test_vendor_orders_are_hidden_from_non_owners(self, marketplace_client):
        app, maker = marketplace_client
        product = get_catalog().list_products()[0]
        order = get_order_manager().create_order(
            product_id=product.id,
            buyer_name="buyer-2",
            quantity_kg=product.minimum_order_kg,
            seller_id=product.producer_id,
        )
        with maker() as session:
            session.add(
                MarketplaceSeller(
                    id=order.seller_id,
                    user_id="seller-owner",
                    village_id="village-1",
                    shop_name="Private shop",
                )
            )
            session.commit()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/marketplace/vendors/{order.seller_id}/orders"
            )
        assert response.status_code == 404

    async def test_admin_stats_endpoint_returns_data(self, marketplace_client):
        app, _ = marketplace_client
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/api/v1/marketplace/admin/stats")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_products"] >= 1
        assert body["total_producers"] >= 1
        assert isinstance(body["organic_products"], int)
        assert "orders" in body

    async def test_admin_approve_product_mutates_state(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            product_id = _seed_product(session, status=MarketplaceProductStatus.PENDING_APPROVAL)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.patch(f"/api/v1/marketplace/admin/products/{product_id}/approve")
        assert resp.status_code == 200, resp.text
        assert resp.json()["approved"] is True
        assert resp.json()["status"] == "approved"
        with maker() as session:
            row = session.get(MarketplaceProduct, product_id)
            assert row.status == MarketplaceProductStatus.APPROVED
            assert row.approved_by == "admin-1"
            assert row.approved_at is not None

    async def test_admin_reject_product_mutates_state(self, marketplace_client):
        app, maker = marketplace_client
        with maker() as session:
            product_id = _seed_product(session, status=MarketplaceProductStatus.DRAFT)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.patch(
                f"/api/v1/marketplace/admin/products/{product_id}/approve",
                params={"approve": False},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["approved"] is False
        with maker() as session:
            row = session.get(MarketplaceProduct, product_id)
            assert row.status == MarketplaceProductStatus.REJECTED
            assert row.approved_by is None

    async def test_admin_approve_unknown_product_is_404(self, marketplace_client):
        app, _ = marketplace_client
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.patch("/api/v1/marketplace/admin/products/nope/approve")
        assert resp.status_code == 404


# ===========================================================================
# Commerce (async engine)
# ===========================================================================

@pytest_asyncio.fixture
async def commerce_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        app = FastAPI()
        app.include_router(commerce_router)

        async def database_override():
            yield session

        app.dependency_overrides[commerce_get_db] = database_override
        app.dependency_overrides[require_user] = lambda: SimpleNamespace(
            id="buyer-1", role="farmer"
        )
        app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
            id="admin-1", role="admin"
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, session
    await engine.dispose()


async def _seed_com_order(session, *, consumed_qty: str, status: str = "processing") -> str:
    order = ComOrder(
        id="com-order-1",
        order_number="ORD-COM-1",
        buyer_id="buyer-1",
        seller_id="seller-1",
        status=status,
        payment_status="paid",
        currency="IRR",
        subtotal=Decimal("10.00"),
        platform_fee=Decimal("0.30"),
        landscape_fee=Decimal("0.10"),
        total=Decimal("10.40"),
        shipping_address={"village_id": "village-com"},
        version=1,
    )
    session.add(order)
    await session.flush()
    session.add(
        ComOrderItem(
            id="line-1",
            order_id="com-order-1",
            sku_id=1,
            sku_code="SKU-1",
            name="Product",
            quantity=Decimal("5"),
            unit_price=Decimal("2.00"),
            line_total=Decimal("10.00"),
            warehouse_id=1,
            reservation_id=42,
        )
    )
    session.add(
        InvReservation(
            id=42,
            sku_id=1,
            warehouse_id=1,
            qty=Decimal("5"),
            consumed_qty=Decimal(consumed_qty),
            status="active",
            reference_type="order",
            reference_id="com-order-1",
            created_by="buyer-1",
        )
    )
    await session.commit()
    return order.id


class TestCommerceOrderFulfilledQty:
    async def test_fulfilled_qty_reflects_consumed_reservation(self, commerce_client):
        client, session = commerce_client
        await _seed_com_order(session, consumed_qty="3.5")
        resp = await client.get("/api/v1/commerce/orders/com-order-1")
        assert resp.status_code == 200, resp.text
        line = resp.json()["items"][0]
        assert Decimal(line["fulfilled_qty"]) == Decimal("3.5")
        assert Decimal(line["fulfilled_qty"]) <= Decimal(line["quantity"])

    async def test_line_without_consumption_reports_zero(self, commerce_client):
        client, session = commerce_client
        await _seed_com_order(session, consumed_qty="0")
        resp = await client.get("/api/v1/commerce/orders/com-order-1")
        assert Decimal(resp.json()["items"][0]["fulfilled_qty"]) == Decimal("0")

    async def test_unknown_order_is_404(self, commerce_client):
        client, _ = commerce_client
        resp = await client.get("/api/v1/commerce/orders/missing")
        assert resp.status_code == 404


class TestCommerceSettlementFundCredit:
    async def _delivered_order(self, session, village_id: str = "village-com") -> str:
        order = ComOrder(
            id="com-settle-1",
            order_number="ORD-COM-SETTLE",
            buyer_id="buyer-1",
            seller_id="seller-1",
            status="delivered",
            payment_status="paid",
            currency="IRR",
            subtotal=Decimal("100.00"),
            platform_fee=Decimal("3.00"),
            landscape_fee=Decimal("1.00"),
            total=Decimal("104.00"),
            shipping_address={"village_id": village_id},
            version=1,
        )
        session.add(order)
        await session.commit()
        return order.id

    async def test_settle_credits_village_fund(self, commerce_client):
        client, session = commerce_client
        await self._delivered_order(session)
        resp = await client.post("/api/v1/commerce/orders/com-settle-1/settle")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "paid"
        assert body["journal_batch_id"] is not None

        fund = (
            await session.execute(
                select(LandscapeFund).where(LandscapeFund.village_id == "village-com")
            )
        ).scalar_one()
        assert Decimal(str(fund.total_collected)) == Decimal("1.00")
        assert Decimal(str(fund.pending_balance)) == Decimal("1.00")

        credits = (
            await session.execute(
                select(LandscapeFundCredit).where(
                    LandscapeFundCredit.order_id == "com-settle-1"
                )
            )
        ).scalars().all()
        assert len(credits) == 1
        assert Decimal(str(credits[0].amount)) == Decimal("1.00")
        assert credits[0].village_id == "village-com"

    async def test_settle_requires_delivered_status(self, commerce_client):
        client, session = commerce_client
        # Not yet delivered — settle is refused by the state machine.
        await _seed_com_order(session, consumed_qty="0", status="processing")
        resp = await client.post("/api/v1/commerce/orders/com-order-1/settle")
        assert resp.status_code == 400, resp.text

    async def test_settle_unknown_order_is_404(self, commerce_client):
        client, _ = commerce_client
        resp = await client.post("/api/v1/commerce/orders/missing/settle")
        assert resp.status_code == 404
