"""P2-20: domain events + notifications for marketplace, payments and hub flows.

Seeds the minimum rows directly, then drives each transition and asserts the
publisher received the right event name and key payload fields. A broken broker
must never break the committed row, and non-emitting paths stay silent.
"""

from __future__ import annotations

import contextlib
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base
from services.marketplace.hub_service import VillageDevelopmentHubService
from services.marketplace.models import (
    Marketplace,
    MarketplaceMember,
    MarketplaceOrder,
    MarketplaceOrderStatus,
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)
from services.marketplace.models.village_hub import VillageEvent
from services.marketplace.payments_service import EscrowService, PaymentGateways
from services.marketplace.service import MarketplaceService


@pytest_asyncio.fixture
async def adb():
    """A private async in-memory session with the full Base schema."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def sdb():
    """A private sync in-memory session with the full Base schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def events(monkeypatch):
    """Enable the event bus and record every marketplace/hub event published.

    The marketplace publisher is async and is *awaited* by the async services
    but is driven inline via ``asyncio.run`` by the synchronous payments
    service, so a single async recorder covers both.
    """
    recorded: list[dict] = []

    async def fake_marketplace(event_type, aggregate_type, aggregate_id, payload=None):
        recorded.append(
            {
                "domain": "marketplace",
                "event": event_type,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "payload": payload,
            }
        )

    async def fake_event(domain, event_type, aggregate_type, aggregate_id, payload=None):
        recorded.append(
            {
                "domain": domain,
                "event": event_type,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "payload": payload,
            }
        )

    monkeypatch.setattr(
        "engine.hydroma.config.settings.get_settings",
        lambda: SimpleNamespace(enable_event_bus=True),
    )
    monkeypatch.setattr(
        "services.api_gateway.eventbus.publisher.publish_marketplace_event", fake_marketplace
    )
    monkeypatch.setattr("services.api_gateway.eventbus.publisher.publish_event", fake_event)
    return recorded


@pytest.fixture
def notifications(monkeypatch):
    """Record in-app notifications delivered for owner user ids."""
    recorded: list[dict] = []

    class FakeNotificationDbService:
        def __init__(self, db):
            self.db = db

        def notify(self, user_id, title, body="", ntype="system", link=None):
            recorded.append({"user_id": user_id, "title": title, "ntype": ntype})

    monkeypatch.setattr(
        "services.notification.db_service.NotificationDbService", FakeNotificationDbService
    )
    monkeypatch.setattr(
        "database.hub.hub.get_session", lambda: contextlib.nullcontext(SimpleNamespace())
    )
    return recorded


# --- marketplace service (async) ---------------------------------------------


@pytest.mark.asyncio
async def test_register_seller_emits_shop_created(events, notifications, adb):
    svc = MarketplaceService(adb)
    seller = await svc.register_seller(
        user_id="ev-seller", village_id="ev-village", shop_name="EV Shop"
    )
    created = [e for e in events if e["event"] == "shop_created"]
    assert len(created) == 1
    assert created[0]["aggregate_id"] == str(seller.id)
    assert created[0]["payload"]["user_id"] == "ev-seller"
    assert created[0]["payload"]["shop_name"] == "EV Shop"
    assert any(n["user_id"] == "ev-seller" for n in notifications)


@pytest.mark.asyncio
async def test_verify_seller_emits_seller_verified_and_notifies(events, notifications, adb):
    seller = MarketplaceSeller(user_id="ev-owner", village_id="ev-village", shop_name="Verify Me")
    adb.add(seller)
    await adb.commit()
    svc = MarketplaceService(adb)
    await svc.verify_seller(str(seller.id), verified_by="admin-1")
    verified = [e for e in events if e["event"] == "seller_verified"]
    assert len(verified) == 1
    assert verified[0]["aggregate_id"] == str(seller.id)
    assert verified[0]["payload"]["verified_by"] == "admin-1"
    assert any(n["user_id"] == "ev-owner" for n in notifications)


@pytest.mark.asyncio
async def test_approve_product_emits_approved_and_rejected(events, notifications, adb):
    seller = MarketplaceSeller(user_id="ev-owner", village_id="ev-village", shop_name="Prod Shop")
    adb.add(seller)
    await adb.commit()
    svc = MarketplaceService(adb)

    accepted = MarketplaceProduct(
        seller_id=str(seller.id),
        name="Accept",
        slug=f"accept-{uuid4().hex[:8]}",
        category="food",
        price=Decimal("1000"),
        village_id="ev-village",
        status=MarketplaceProductStatus.PENDING_APPROVAL,
    )
    rejected = MarketplaceProduct(
        seller_id=str(seller.id),
        name="Reject",
        slug=f"reject-{uuid4().hex[:8]}",
        category="food",
        price=Decimal("1000"),
        village_id="ev-village",
        status=MarketplaceProductStatus.PENDING_APPROVAL,
    )
    adb.add_all([accepted, rejected])
    await adb.commit()

    await svc.approve_product(str(accepted.id), approved_by="admin-1", approve=True)
    await svc.approve_product(str(rejected.id), approved_by="admin-1", approve=False)

    approved = [e for e in events if e["event"] == "product_approved"]
    denied = [e for e in events if e["event"] == "product_rejected"]
    assert [e["aggregate_id"] for e in approved] == [str(accepted.id)]
    assert [e["aggregate_id"] for e in denied] == [str(rejected.id)]
    assert approved[0]["payload"]["seller_id"] == str(seller.id)
    # notification routed to the owning user, scoped per record.
    assert any(n["user_id"] == "ev-owner" for n in notifications)


@pytest.mark.asyncio
async def test_verify_marketplace_emits_and_notifies_founders(events, notifications, adb):
    market = Marketplace(
        name="EV Market",
        slug=f"ev-market-{uuid4().hex[:8]}",
        marketplace_type="rural",
        village_id="ev-village",
    )
    adb.add(market)
    await adb.commit()
    adb.add(MarketplaceMember(marketplace_id=str(market.id), user_id="founder-1", role="founder"))
    await adb.commit()

    svc = MarketplaceService(adb)
    await svc.verify_marketplace(str(market.id), approved=True, verified_by="admin-1")
    approved = [e for e in events if e["event"] == "marketplace_approved"]
    assert len(approved) == 1
    assert approved[0]["aggregate_id"] == str(market.id)
    assert approved[0]["payload"]["verified_by"] == "admin-1"
    assert any(n["user_id"] == "founder-1" for n in notifications)


@pytest.mark.asyncio
async def test_reject_marketplace_emits_marketplace_rejected(events, adb):
    market = Marketplace(
        name="Reject Market",
        slug=f"reject-market-{uuid4().hex[:8]}",
        marketplace_type="rural",
        village_id="ev-village",
    )
    adb.add(market)
    await adb.commit()
    svc = MarketplaceService(adb)
    await svc.verify_marketplace(str(market.id), approved=False, verified_by="admin-1")
    rejected = [e for e in events if e["event"] == "marketplace_rejected"]
    assert len(rejected) == 1
    assert [e for e in events if e["event"] == "marketplace_approved"] == []


@pytest.mark.asyncio
async def test_create_order_emits_order_placed(events, notifications, adb):
    seller = MarketplaceSeller(user_id="ev-buyer-user", village_id="ev-village", shop_name="B Shop")
    adb.add(seller)
    await adb.commit()
    product = MarketplaceProduct(
        seller_id=str(seller.id),
        name="Honey",
        slug=f"honey-{uuid4().hex[:8]}",
        category="food",
        price=Decimal("350000"),
        stock=10,
        village_id="ev-village",
        status=MarketplaceProductStatus.PENDING_APPROVAL,
    )
    adb.add(product)
    await adb.commit()

    svc = MarketplaceService(adb)
    order = await svc.create_order(
        buyer_id="ev-buyer",
        items=[{"product_id": str(product.id), "quantity": 1}],
        village_id="ev-village",
        shipping_address={"city": "Tehran"},
    )
    placed = [e for e in events if e["event"] == "order_placed"]
    assert len(placed) == 1
    assert placed[0]["payload"]["order_id"] == str(order.id)
    assert placed[0]["payload"]["village_id"] == "ev-village"
    assert placed[0]["payload"]["total"] == str(order.total)
    assert placed[0]["payload"]["buyer_id"] == "ev-buyer"
    assert any(n["user_id"] == "ev-buyer" and n["ntype"] == "order" for n in notifications)


@pytest.mark.asyncio
async def test_payment_ship_complete_transitions(events, notifications, adb):
    svc = MarketplaceService(adb)

    def _seed_order(
        *, payment_status: str = "pending", status=MarketplaceOrderStatus.PENDING
    ) -> MarketplaceOrder:
        order = MarketplaceOrder(
            order_number=f"ORD-{uuid4().hex[:10]}",
            buyer_id="ev-buyer",
            village_id="ev-village",
            subtotal=Decimal("350000"),
            total=Decimal("350000"),
            status=status,
            payment_status=payment_status,
        )
        adb.add(order)
        return order

    paid_order = _seed_order()
    await adb.commit()
    confirmed = await svc.confirm_payment(str(paid_order.id), payment_tx_hash="0xTX")
    paid = [e for e in events if e["event"] == "payment_completed"]
    assert len(paid) == 1
    assert paid[0]["payload"]["order_id"] == str(paid_order.id)
    assert paid[0]["payload"]["total"] == str(confirmed.total)
    assert any(n["user_id"] == "ev-buyer" and n["ntype"] == "payment" for n in notifications)

    ship_order = _seed_order(payment_status="paid", status=MarketplaceOrderStatus.PAID)
    await adb.commit()
    await svc.ship_order(str(ship_order.id), tracking_code="TRK-EV")
    shipped = [e for e in events if e["event"] == "order_shipped"]
    assert len(shipped) == 1
    assert shipped[0]["payload"]["tracking_code"] == "TRK-EV"

    done_order = _seed_order(payment_status="paid", status=MarketplaceOrderStatus.SHIPPED)
    await adb.commit()
    await svc.complete_order(str(done_order.id))
    completed = [e for e in events if e["event"] == "order_completed"]
    assert len(completed) == 1
    assert completed[0]["aggregate_id"] == str(done_order.id)


@pytest.mark.asyncio
async def test_failing_marketplace_publisher_keeps_business(events, adb, monkeypatch):
    async def broken_publisher(*args, **kwargs):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        "services.api_gateway.eventbus.publisher.publish_marketplace_event", broken_publisher
    )
    svc = MarketplaceService(adb)
    seller = await svc.register_seller(
        user_id="ev-broken", village_id="ev-village", shop_name="Broken Shop"
    )
    assert seller.id is not None
    reloaded = await adb.get(MarketplaceSeller, str(seller.id))
    assert reloaded is not None


# --- payments service (sync) --------------------------------------------------


def _seed_payment(sdb, *, total: float = 350000.0) -> MarketplaceOrder:
    order = MarketplaceOrder(
        order_number=f"ORD-{uuid4().hex[:10]}",
        buyer_id="buyer-1",
        village_id="village-1",
        subtotal=Decimal(str(total)),
        total=Decimal(str(total)),
        status=MarketplaceOrderStatus.PENDING,
        payment_status="pending",
    )
    sdb.add(order)
    sdb.commit()
    return order


def test_verify_payment_emits_payment_completed(events, notifications, sdb):
    order = _seed_payment(sdb)
    gateways = PaymentGateways(sdb)
    payment = gateways.create(
        order_id=str(order.id), user_id="buyer-1", gateway="bank", amount=350000.0
    )
    gateways.verify(payment, ref_id="TRK-EV")

    paid = [e for e in events if e["event"] == "payment_completed"]
    assert len(paid) == 1
    assert paid[0]["payload"]["payment_id"] == str(payment.id)
    assert paid[0]["payload"]["order_id"] == str(order.id)
    assert any(n["user_id"] == "buyer-1" and n["ntype"] == "payment" for n in notifications)


def test_release_emits_settlement_posted(events, notifications, sdb):
    order = _seed_payment(sdb)
    gateways = PaymentGateways(sdb)
    payment = gateways.create(
        order_id=str(order.id), user_id="buyer-1", gateway="bank", amount=350000.0
    )
    gateways.verify(payment, ref_id="TRK-EV")
    events.clear()
    notifications.clear()

    EscrowService(sdb).release(str(payment.id), actor_id="admin-1")
    settled = [e for e in events if e["event"] == "settlement_posted"]
    assert len(settled) == 1
    assert settled[0]["aggregate_id"] == str(order.id)
    assert settled[0]["payload"]["payment_id"] == str(payment.id)
    assert any(n["user_id"] == "buyer-1" and n["ntype"] == "payment" for n in notifications)


def test_refund_emits_payment_refunded(events, notifications, sdb):
    order = _seed_payment(sdb)
    gateways = PaymentGateways(sdb)
    payment = gateways.create(
        order_id=str(order.id), user_id="buyer-1", gateway="bank", amount=350000.0
    )
    gateways.verify(payment, ref_id="TRK-EV")
    events.clear()
    notifications.clear()

    EscrowService(sdb).refund(str(payment.id), actor_id="admin-1")
    refunded = [e for e in events if e["event"] == "payment_refunded"]
    assert len(refunded) == 1
    assert refunded[0]["aggregate_id"] == str(order.id)
    assert any(n["user_id"] == "buyer-1" for n in notifications)


def test_failing_payment_publisher_keeps_business(events, sdb, monkeypatch):
    def broken_publisher(*args, **kwargs):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        "services.api_gateway.eventbus.publisher.publish_marketplace_event", broken_publisher
    )
    order = _seed_payment(sdb)
    gateways = PaymentGateways(sdb)
    payment = gateways.create(
        order_id=str(order.id), user_id="buyer-1", gateway="bank", amount=350000.0
    )
    # Broker outage must not prevent the payment from verifying / the escrow hold.
    gateways.verify(payment, ref_id="TRK-EV")
    reloaded = sdb.get(MarketplaceOrder, str(order.id))
    assert reloaded.payment_status == "paid"


# --- village hub service (async) ----------------------------------------------


@pytest.mark.asyncio
async def test_nomadic_community_created_and_approved(events, notifications, adb):
    svc = VillageDevelopmentHubService(adb)
    community = await svc.create_nomadic_community(
        {"name": "EV Nomads", "village_id": "ev-village"}, "owner-1", is_admin=True
    )
    created = [e for e in events if e["event"] == "nomadic_community_created"]
    assert len(created) == 1
    assert created[0]["aggregate_id"] == str(community.id)
    assert created[0]["payload"]["owner_user_id"] == "owner-1"

    events.clear()
    notifications.clear()
    await svc.approve_nomadic_community(str(community.id), "admin-actor", is_admin=True)
    approved = [e for e in events if e["event"] == "nomadic_community_approved"]
    assert len(approved) == 1
    assert approved[0]["payload"]["approved_by"] == "admin-actor"
    assert any(n["user_id"] == "owner-1" for n in notifications)


@pytest.mark.asyncio
async def test_event_registration_emits_event_registration_created(events, notifications, adb):
    event = VillageEvent(
        village_id="ev-village",
        title="EV Festival",
        start_date=date(2026, 10, 1),
        created_by="host-1",
    )
    adb.add(event)
    await adb.commit()

    svc = VillageDevelopmentHubService(adb)
    events.clear()
    registration = await svc.register_event(str(event.id), "attendee-1")
    emitted = [e for e in events if e["event"] == "event_registration_created"]
    assert len(emitted) == 1
    assert emitted[0]["aggregate_id"] == str(registration.id)
    assert emitted[0]["payload"]["event_id"] == str(event.id)
    assert emitted[0]["payload"]["user_id"] == "attendee-1"
    assert any(n["user_id"] == "attendee-1" for n in notifications)


@pytest.mark.asyncio
async def test_b2b_demand_created_emits(events, notifications, adb):
    svc = VillageDevelopmentHubService(adb)
    demand = await svc.create_b2b_demand(
        {
            "buyer_name": "EV Buyer",
            "commodity": "honey",
            "quantity_required": Decimal("5000"),
            "unit": "ton/month",
        },
        "buyer-1",
    )
    emitted = [e for e in events if e["event"] == "b2b_demand_created"]
    assert len(emitted) == 1
    assert emitted[0]["aggregate_id"] == str(demand.id)
    assert emitted[0]["payload"]["buyer_id"] == "buyer-1"
    assert emitted[0]["payload"]["commodity"] == "honey"
    assert any(n["user_id"] == "buyer-1" for n in notifications)


@pytest.mark.asyncio
async def test_no_hub_event_on_read_paths(events, adb):
    svc = VillageDevelopmentHubService(adb)
    await svc.get_nomadic_communities()
    assert events == []
