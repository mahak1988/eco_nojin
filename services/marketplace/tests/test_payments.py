"""Tests for the multi-gateway payment service + escrow ledger (plan v2.1)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import services.marketplace.models
import services.marketplace.models.marketplace_payment  # noqa: F401
from database.base import Base
from services.marketplace.models.marketplace_payment import MarketplacePayment
from services.marketplace.payments_service import (
    EscrowService,
    PaymentError,
    PaymentGateways,
    bank_instructions,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_unknown_gateway_rejected(db_session):
    svc = PaymentGateways(db_session)
    with pytest.raises(PaymentError):
        svc.create(order_id="o-1", user_id="u-1", gateway="paypal", amount=100.0)


def test_zarinpal_unconfigured_fails_loud(db_session):
    svc = PaymentGateways(db_session)
    with pytest.raises(PaymentError):
        svc.create(order_id="o-1", user_id="u-1", gateway="zarinpal", amount=100.0)


def test_bank_flow_holds_escrow(db_session):
    svc = PaymentGateways(db_session)
    payment = svc.create(order_id="o-2", user_id="u-1", gateway="bank", amount=250000.0)
    assert payment.status == "awaiting_verification"
    with pytest.raises(PaymentError):
        svc.verify(payment)  # no tracking code
    payment = svc.verify(payment, ref_id="TRK-123456")
    assert payment.status == "verified"
    assert payment.escrow_status == "held"
    entries = EscrowService(db_session).by_order("o-2")
    assert [e.entry_type for e in entries] == ["hold"]


def test_escrow_release_then_no_double(db_session):
    svc = PaymentGateways(db_session)
    payment = svc.create(order_id="o-3", user_id="u-1", gateway="bank", amount=100.0)
    payment = svc.verify(payment, ref_id="TRK-1")
    esc = EscrowService(db_session)
    entry = esc.release(payment.id, actor_id="admin-1")
    assert entry.entry_type == "release"
    assert payment.escrow_status == "released"
    with pytest.raises(PaymentError):
        esc.release(payment.id)
    with pytest.raises(PaymentError):
        esc.refund(payment.id)


def test_bank_instructions_shape():
    info = bank_instructions()
    assert set(info.keys()) == {"card_number", "sheba", "holder"}


def test_payment_model_roundtrip(db_session):
    p = MarketplacePayment(order_id="o-9", user_id="u-9", gateway="bank", amount=50.0)
    db_session.add(p)
    db_session.commit()
    assert p.to_dict()["gateway"] == "bank"
