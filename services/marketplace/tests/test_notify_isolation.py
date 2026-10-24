"""Pinning tests: an unavailable notification store must never break a payment.

``PaymentGateways._notify`` used to hand the caller's session to
``NotificationDbService``, which adds *and commits*. When that write failed
(``app_notifications`` missing on an isolated engine, a constraint violation)
the failed flush rolled the caller's transaction back, expired the rows it held
and left the session in ``PendingRollbackError``. The notification error was
swallowed, but the *payment object it returned was already unusable*: any
attribute access on it re-queries the dead transaction and raises, and so does
the next ``commit()`` in ``PaymentGateways.verify`` /
``EscrowService.release`` / ``refund``. A verified payment therefore became an
HTTP 500 with its escrow hold and order transition lost.

Reproduction (before the fix): ``pytest
services/marketplace/tests/test_payment_order_flow.py::test_verification_advances_order_to_paid``
failed in isolation but passed in the full suite, where another test had
provisioned ``app_notifications`` on the shared engine.

The notification now runs in its own unit of work — a fresh session from the
repo's factory (``hub.get_session()``) — so its failure is rolled back with
that session and can never touch the escrow row the caller already committed.
These tests pin that contract:

1. a missing ``app_notifications`` table still lets verification advance the
   order, return a usable payment and commit the escrow hold — and the caller's
   session keeps working for the release that follows its own notify;
2. the same holds for the refund path;
3. a ``notify`` that raises before writing anything is equally inert (the
   boundary case: it cannot poison a session it never touched);
4. when the notification store *is* available the notification is really
   delivered and committed, so the isolation is not a silent no-op.

The fixtures follow ``test_payment_order_flow.py``: a private in-memory engine
with ``StaticPool`` (one connection, so every session sees the same rows) and
``database.config.SessionLocal`` repointed at it, which is what
``hub.get_session()`` re-imports per call.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from services.marketplace.models import MarketplaceOrder, MarketplaceOrderStatus
from services.marketplace.models.marketplace_payment import (
    MarketplaceEscrowEntry,
    MarketplacePayment,
)
from services.marketplace.payments_service import EscrowService, PaymentGateways

# Registers ``app_notifications`` on the shared Base, so create_all() can
# provision it and the "store missing" fixture can drop it again.
from services.notification.models_db import AppNotification

BUYER = "buyer-1"


def _seed_order(session) -> MarketplaceOrder:
    order = MarketplaceOrder(
        order_number=f"ORD-{uuid4().hex[:10]}",
        buyer_id=BUYER,
        village_id="village-1",
        subtotal=Decimal("350000.00"),
        total=Decimal("350000.00"),
        status=MarketplaceOrderStatus.PENDING,
        payment_status="pending",
    )
    session.add(order)
    session.commit()
    return order


def _entry_types(maker, payment_id: str) -> list[str]:
    """The committed escrow entry types for a payment, on a fresh session."""
    with maker() as session:
        return sorted(
            entry.entry_type
            for entry in session.execute(
                select(MarketplaceEscrowEntry).where(
                    MarketplaceEscrowEntry.payment_id == str(payment_id)
                )
            ).scalars()
        )


@pytest.fixture
def isolated_engine(monkeypatch):
    """Build one isolated engine and repoint the repo's session factory at it.

    ``notifications=False`` drops ``app_notifications`` again after creating
    the schema, reproducing a store that was never provisioned; ``True`` keeps
    the full schema so the happy path can be asserted. Each test disposes the
    engine it built.
    """

    def _build(*, notifications: bool):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        if not notifications:
            AppNotification.__table__.drop(engine)
        maker = sessionmaker(bind=engine, expire_on_commit=False)
        monkeypatch.setattr("database.config.SessionLocal", maker)
        return engine, maker

    return _build


def test_verification_succeeds_when_the_notification_store_is_missing(isolated_engine):
    engine, maker = isolated_engine(notifications=False)
    try:
        with maker() as session:
            order = _seed_order(session)
            order_id = str(order.id)
            gateways = PaymentGateways(session)
            payment = gateways.create(
                order_id=order_id, user_id=BUYER, gateway="bank", amount=350000.0
            )
            # Pre-fix, the notify's failed commit rolled this session back and
            # expired the payment, so the next attribute access or commit — here
            # the release below, in the router the escrow/settle handlers —
            # raised PendingRollbackError and a paid order 500'd.
            payment = gateways.verify(payment, ref_id="TRK-1")
            payment_id = str(payment.id)

            assert payment.status == "verified"
            assert payment.escrow_status == "held"

            # The caller's session is still usable for its own next unit of
            # work: release() commits and then notifies in turn.
            entry = EscrowService(session).release(payment_id, actor_id="admin-1")
            assert entry.entry_type == "release"

        assert _entry_types(maker, payment_id) == ["hold", "release"]

        # The order transition really committed; a fresh session sees it.
        with maker() as check:
            reloaded = check.get(MarketplaceOrder, order_id)
            assert reloaded.status == MarketplaceOrderStatus.PAID
            assert reloaded.payment_status == "paid"
            assert reloaded.paid_at is not None
    finally:
        engine.dispose()


def test_refund_succeeds_when_the_notification_store_is_missing(isolated_engine):
    engine, maker = isolated_engine(notifications=False)
    try:
        with maker() as session:
            order = _seed_order(session)
            order_id = str(order.id)
            gateways = PaymentGateways(session)
            payment = gateways.create(
                order_id=order_id, user_id=BUYER, gateway="bank", amount=350000.0
            )
            payment = gateways.verify(payment, ref_id="TRK-2")

            assert payment.status == "verified"
            assert payment.escrow_status == "held"

            # refund() commits its ledger row and then notifies.
            entry = EscrowService(session).refund(str(payment.id), actor_id="admin-1")
            refunded = session.get(MarketplacePayment, str(payment.id))

        assert entry.entry_type == "refund"
        assert refunded.status == "refunded"
        assert refunded.escrow_status == "refunded"
        assert _entry_types(maker, str(payment.id)) == ["hold", "refund"]
    finally:
        engine.dispose()


def test_verification_survives_a_notification_that_raises(isolated_engine, monkeypatch):
    engine, maker = isolated_engine(notifications=True)
    try:

        class BrokenNotificationDbService:
            def __init__(self, db):
                self.db = db

            def notify(self, *args, **kwargs):
                raise RuntimeError("notification store unavailable")

        monkeypatch.setattr(
            "services.notification.db_service.NotificationDbService",
            BrokenNotificationDbService,
        )

        with maker() as session:
            order = _seed_order(session)
            order_id = str(order.id)
            gateways = PaymentGateways(session)
            payment = gateways.create(
                order_id=order_id, user_id=BUYER, gateway="bank", amount=350000.0
            )
            payment = gateways.verify(payment, ref_id="TRK-3")
            payment_id = str(payment.id)

            assert payment.status == "verified"
            assert payment.escrow_status == "held"

        with maker() as check:
            reloaded = check.get(MarketplaceOrder, order_id)
        assert reloaded.status == MarketplaceOrderStatus.PAID
        assert _entry_types(maker, payment_id) == ["hold"]
    finally:
        engine.dispose()


def test_notification_is_delivered_when_the_store_is_available(isolated_engine):
    """The isolation is a boundary, not a mute: the row is really committed."""
    engine, maker = isolated_engine(notifications=True)
    try:
        with maker() as session:
            order = _seed_order(session)
            gateways = PaymentGateways(session)
            payment = gateways.create(
                order_id=str(order.id), user_id=BUYER, gateway="bank", amount=350000.0
            )
            gateways.verify(payment, ref_id="TRK-4")

        # Read through the factory the notification itself used, not through
        # the caller's session: the row must survive its own unit of work.
        with maker() as check:
            rows = (
                check.execute(select(AppNotification).where(AppNotification.user_id == BUYER))
                .scalars()
                .all()
            )
        assert [(n.type, n.title) for n in rows] == [
            ("payment", "Your payment has been received.")
        ]
    finally:
        engine.dispose()
