"""P2-20: commerce domain events + notifications emit on order transitions.

Each order transition must publish exactly one ``commerce.<event>`` with the
right name and key payload fields AFTER the business commit; a failing broker
must never break the committed order; and non-emitting paths (payment failure,
idempotent replay, bus disabled) must publish nothing.
"""

from __future__ import annotations

import contextlib
from decimal import Decimal
from types import SimpleNamespace

import pytest


def _item(sku, quantity: int = 1, price: str = "100") -> dict:
    return {
        "sku_code": sku.sku_code,
        "quantity": quantity,
        "unit_price": Decimal(price),
        "warehouse_id": sku.default_warehouse_id or 1,
    }


@pytest.fixture
def events(monkeypatch):
    """Enable the event bus and record every commerce event published."""
    recorded: list[dict] = []

    async def fake_publish_event(domain, event_type, aggregate_type, aggregate_id, payload=None):
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
    monkeypatch.setattr("services.api_gateway.eventbus.publisher.publish_event", fake_publish_event)
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
    # The async service opens its own short-lived sync session for notify; keep
    # it inert so the fake above is what actually records.
    monkeypatch.setattr(
        "database.hub.hub.get_session", lambda: contextlib.nullcontext(SimpleNamespace())
    )
    return recorded


@pytest.mark.asyncio
async def test_create_order_emits_order_created(events, notifications, order_service, sku):
    order = await order_service.create_order(
        buyer_id="ev-buyer", items=[_item(sku)], shipping_address={"city": "Tehran"}
    )
    placed = [e for e in events if e["event"] == "order_created"]
    assert len(placed) == 1
    ev = placed[0]
    assert ev["domain"] == "commerce"
    assert ev["aggregate_type"] == "order"
    assert ev["aggregate_id"] == order.id
    assert ev["payload"]["order_id"] == order.id
    assert ev["payload"]["buyer_id"] == "ev-buyer"
    assert ev["payload"]["total"] == str(order.total)
    assert ev["payload"]["status"] == "reserved"
    assert any(n["user_id"] == "ev-buyer" and n["ntype"] == "order" for n in notifications)


@pytest.mark.asyncio
async def test_payment_confirmation_emits_payment_completed(
    events, notifications, order_service, sku
):
    order = await order_service.create_order(buyer_id="ev-pay", items=[_item(sku)])
    events.clear()
    notifications.clear()
    await order_service.confirm_payment(order.id, payment_confirmed=True)
    paid = [e for e in events if e["event"] == "payment_completed"]
    assert len(paid) == 1
    assert paid[0]["payload"]["order_id"] == order.id
    assert any(n["user_id"] == "ev-pay" and n["ntype"] == "payment" for n in notifications)


@pytest.mark.asyncio
async def test_payment_failure_emits_nothing(events, order_service, sku):
    order = await order_service.create_order(buyer_id="ev-fail", items=[_item(sku)])
    events.clear()
    await order_service.confirm_payment(
        order.id, payment_confirmed=False, failure_reason="declined"
    )
    assert events == []


@pytest.mark.asyncio
async def test_fulfillment_emits_shipped_then_settled(events, order_service, sku):
    order = await order_service.create_order(buyer_id="ev-fulfil", items=[_item(sku)])
    await order_service.confirm_payment(order.id, payment_confirmed=True)
    await order_service.process_order(order.id)
    await order_service.ship_order(order.id, "TRK-EV", "admin")
    await order_service.mark_delivered(order.id)
    settlement = await order_service.settle_order(order.id)

    shipped = [e for e in events if e["event"] == "order_shipped"]
    assert len(shipped) == 1
    assert shipped[0]["payload"]["tracking_code"] == "TRK-EV"

    settled = [e for e in events if e["event"] == "order_settled"]
    assert len(settled) == 1
    assert settled[0]["payload"]["order_id"] == order.id
    assert settled[0]["payload"]["settlement_id"] == settlement.id


@pytest.mark.asyncio
async def test_cancel_order_emits_order_cancelled(events, order_service, sku):
    order = await order_service.create_order(buyer_id="ev-cancel", items=[_item(sku)])
    events.clear()
    await order_service.cancel_order(order.id, reason="changed mind", cancelled_by="ev-cancel")
    cancelled = [e for e in events if e["event"] == "order_cancelled"]
    assert len(cancelled) == 1
    assert cancelled[0]["payload"]["order_id"] == order.id
    assert cancelled[0]["payload"]["reason"] == "changed mind"


@pytest.mark.asyncio
async def test_idempotent_create_order_emits_once(events, order_service, sku):
    key = "ev-idempotency-key"
    order1 = await order_service.create_order(
        buyer_id="ev-idem", items=[_item(sku)], idempotency_key=key
    )
    order2 = await order_service.create_order(
        buyer_id="ev-idem", items=[_item(sku)], idempotency_key=key
    )
    assert order1.id == order2.id
    assert len([e for e in events if e["event"] == "order_created"]) == 1


@pytest.mark.asyncio
async def test_failing_publisher_does_not_break_order(events, order_service, sku, monkeypatch):
    async def broken_publisher(*args, **kwargs):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        "services.api_gateway.eventbus.publisher.publish_event", broken_publisher
    )
    order = await order_service.create_order(buyer_id="ev-broken", items=[_item(sku)])
    # The committed row survives a broker outage.
    assert order.id is not None
    assert order.status == "reserved"
    reloaded = await order_service.get_order(order.id)
    assert reloaded is not None and reloaded.id == order.id


@pytest.mark.asyncio
async def test_no_publish_when_event_bus_disabled(monkeypatch, order_service, sku):
    calls: list[tuple] = []

    async def recording_publisher(*args, **kwargs):
        calls.append(args)

    monkeypatch.setattr(
        "engine.hydroma.config.settings.get_settings",
        lambda: SimpleNamespace(enable_event_bus=False),
    )
    monkeypatch.setattr(
        "services.api_gateway.eventbus.publisher.publish_event", recording_publisher
    )
    await order_service.create_order(buyer_id="ev-off", items=[_item(sku)])
    assert calls == []
