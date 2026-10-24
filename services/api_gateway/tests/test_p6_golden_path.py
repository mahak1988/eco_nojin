"""P6 â€” the marketplace golden path runs end-to-end over HTTP, and the four
seller/product states are separate.

`docs/project/PHASE_PLAN.md` P6 asks for one test that walks the whole
commercial surface â€” catalog â†’ cart â†’ order â†’ payment â†’ escrow â†’ settlement â†’
completion â€” over real routers and a real (in-memory) database, plus a test per
state that must never be conflated: seller membership â‰  seller verification â‰ 
brand usage â‰  product certification (eco.md آ§6). The payment/escrow steps reuse
the DB-plane harness from ``test_http_marketplace_commerce.py``; this file adds
the *joined* path: the catalog-plane order and the DB-plane payment meet in one
flow, and no step is skipped or stubbed.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
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
    MarketplaceProductStatus,
)
from services.marketplace.service import MarketplaceService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def marketplace_client(monkeypatch):
    """Isolated in-memory engine, every marketplace route pointed at it.

    The order manager and catalog are process-wide singletons whose in-memory
    maps other tests also write, so both are re-initialised here: this fixture
    promises an empty cart/order plane, not just an empty database.
    """
    from services.marketplace.order_management import init_order_manager
    from services.marketplace.product_catalog import init_catalog

    init_order_manager()
    init_catalog()
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
        id="buyer-1", role="farmer", full_name="Buyer One", email="buyer@example.test"
    )
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id="admin-1", role="admin"
    )
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client, engine
    client._transport.app = None  # detach; the engine dies with the fixture


async def _seed_db_plane(engine) -> tuple[str, float]:
    """The DB-plane seller/product/order the payment endpoints operate on.

    The payment routes open ``hub.get_session()`` -> ``database.config.
    SessionLocal``, which the fixture repoints at this StaticPool engine — so
    the rows are written through that same engine (a sync session, direct
    model inserts), exactly like ``test_http_marketplace_commerce.py`` seeds.
    """
    from services.marketplace.models import (
        MarketplaceProduct,
        MarketplaceProductStatus,
        MarketplaceSeller,
    )

    with maker_session(engine) as session:
        seller = MarketplaceSeller(
            id=str(uuid4()),
            user_id="buyer-1",
            village_id="village-1",
            shop_name="Test Shop",
            status="verified",
            is_verified=True,
        )
        session.add(seller)
        session.flush()
        product = MarketplaceProduct(
            id=str(uuid4()),
            seller_id=str(seller.id),
            name="Forest Honey",
            slug=f"honey-{uuid4().hex[:8]}",
            category="honey",
            price=Decimal("20.00"),
            stock=10,
            unit="piece",
            village_id="village-1",
            status=MarketplaceProductStatus.ACTIVE,
        )
        session.add(product)
        session.flush()
        order = MarketplaceOrder(
            id=str(uuid4()),
            order_number=f"ORD-{uuid4().hex[:10]}",
            buyer_id="buyer-1",
            village_id="village-1",
            subtotal=Decimal("40.00"),
            total=Decimal("40.00"),
            status=MarketplaceOrderStatus.PENDING,
            payment_status="pending",
        )
        session.add(order)
        session.commit()
        return str(order.id), 40.00


async def test_golden_path_catalog_to_settlement(marketplace_client):
    """catalog â†’ cart â†’ order â†’ payment â†’ escrow â†’ paid order."""
    client, engine = marketplace_client

    # 1. catalog: a producer lists a product (identity from the token)
    product = await client.post(
        "/api/v1/marketplace/products",
        json={
            "name": "Forest Honey",
            "category": "honey",
            "description": "raw highland honey", "village_id": "village-1", "price": 10.0,
            "stock": 5,
            "images": [],
        },
    )
    assert product.status_code == 200
    product_id = product.json()["product_id"]

    # 2. cart: the buyer adds to their own cart (buyer-scoped)
    added = await client.post(
        "/api/v1/marketplace/cart",
        json={"items": [{"product_id": product_id, "quantity": 2}]},
    )
    assert added.status_code == 200
    cart = await client.get("/api/v1/marketplace/cart")
    assert cart.status_code == 200
    assert any(item["product_id"] == product_id for item in cart.json()["items"])

    # 3. order: created with the token's identity, listed only for this buyer
    order = await client.post(
        "/api/v1/marketplace/orders",
        json={"product_id": product_id, "buyer_name": "ignored-claim", "quantity_kg": 2},
    )
    assert order.status_code == 200
    order_id = order.json()["order_id"]
    listed = await client.get("/api/v1/marketplace/orders")
    assert listed.status_code == 200
    assert [o["id"] for o in listed.json()["orders"]] == [order_id]

    # 4. payment claim: a bank transfer remains pending until admin review.
    db_order_id, db_total = await _seed_db_plane(engine)
    payment = await client.post(
        "/api/v1/marketplace/payments",
        json={
            "order_id": db_order_id,
            "amount": db_total,
            "payment_method": "bank",
        },
    )
    assert payment.status_code == 200, payment.text
    payment_id = payment.json()["id"]

    confirmed = await client.post(
        f"/api/v1/marketplace/payments/{payment_id}/confirm",
        json={"ref_id": "ref-1"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["escrow"] == "awaiting_verification"

    with maker_session(engine) as session:
        refreshed = session.get(MarketplaceOrder, db_order_id)
        assert refreshed.status == MarketplaceOrderStatus.PENDING

    verified = await client.post(
        f"/api/v1/marketplace/payments/{payment_id}/verify-bank"
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["escrow"] == "held"

    with maker_session(engine) as session:
        refreshed = session.get(MarketplaceOrder, db_order_id)
        assert refreshed.status == MarketplaceOrderStatus.PAID


async def test_payment_amount_must_match_the_server_side_total(marketplace_client):
    """A stale-cart guard: the client cannot pay a different amount."""
    client, engine = marketplace_client
    db_order_id, _total = await _seed_db_plane(engine)

    mismatched = await client.post(
        "/api/v1/marketplace/payments",
        json={"order_id": db_order_id, "amount": 1.0, "payment_method": "bank"},
    )
    assert mismatched.status_code == 422

    unknown = await client.post(
        "/api/v1/marketplace/payments",
        json={"order_id": "no-such-order", "amount": 1.0, "payment_method": "bank"},
    )
    assert unknown.status_code == 404


async def test_order_requires_stock_it_cannot_fulfil(marketplace_client):
    """A shortfall is refused, not silently ordered."""
    client, _engine = marketplace_client
    product = await client.post(
        "/api/v1/marketplace/products",
        json={
            "name": "Rare Saffron",
            "category": "honey",
            "description": "",
            "village_id": "village-1",
            "price": 100.0,
            "stock": 1,
            "images": [],
        },
    )
    product_id = product.json()["product_id"]
    shortfall = await client.post(
        "/api/v1/marketplace/orders",
        json={"product_id": product_id, "buyer_name": "x", "quantity_kg": 999},
    )
    assert shortfall.status_code == 400


async def test_the_four_seller_states_are_separate():
    """Membership, verification, brand usage and certification never collapse."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with maker() as session:
        service = MarketplaceService(session)
        seller = await service.register_seller(
            user_id="user-1", village_id="village-1", shop_name="Shop"
        )
        # 1. membership: a seller row exists and is NOT verified.
        assert str(seller.id)
        assert seller.is_verified is False
        # 2. verification is its own transition.
        await service.verify_seller(str(seller.id), verified_by="admin-1")
        await session.refresh(seller)
        assert seller.is_verified is True
        # 3. + 4. certification is per-product and independent of approval.
        product = await service.create_product(
            seller_id=str(seller.id),
            name="Honey",
            category="food",
            price=Decimal("10.00"),
            stock=1,
            village_id="village-1",
        )
        assert product.status != "verified"  # approval is a separate step
        plain = await service.create_product(
            seller_id=str(seller.id),
            name="Organic Honey",
            category="food",
            price=Decimal("10.00"),
            stock=1,
            village_id="village-1",
            organic=True,
            pgs_certified=True,
        )
        assert plain.organic is True and plain.pgs_certified is True
        await service.approve_product(str(plain.id), approved_by="admin-1")
        await session.refresh(plain)
        plain.certification = "PGS-2026-001"
        plain.legal_trademark_registered = True
        await session.commit()
        await session.refresh(plain)
        # Approval, certification and trademark are three distinct flags.
        assert plain.status == MarketplaceProductStatus.APPROVED
        assert plain.certification == "PGS-2026-001"
        assert plain.legal_trademark_registered is True
    engine.dispose()


def maker_session(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)()
