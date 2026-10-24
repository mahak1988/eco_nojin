"""Tests for the ``international`` gateway: the Stripe REST request/verify
pair, honest degradation, webhook signatures and the escrow integration.

No network: ``urllib.request.urlopen`` is replaced by a recording, scripted
stand-in that answers exactly as the provider would over the wire — including
its JSON error bodies — so the documented form body, the idempotency header
and the signature scheme are asserted from the requests the service really
builds. The escrow assertions mirror ``test_payments.py`` (bank) and
``test_payment_order_flow.py``: a verified international payment holds escrow
and advances the order through the same chain the zarinpal path takes.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from email.message import Message
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base
from services.marketplace.models import MarketplaceOrder, MarketplaceOrderStatus
from services.marketplace.models.marketplace_payment import MarketplacePayment
from services.marketplace.payments_service import (
    STRIPE_API_BASE,
    STRIPE_PAYMENT_INTENTS_PATH,
    STRIPE_WEBHOOK_TOLERANCE_SECONDS,
    EscrowService,
    PaymentError,
    PaymentGateways,
    verify_stripe_webhook_signature,
)

# Offline tests never reach Stripe: this only has to be a non-empty bearer
# token for the recording stand-in, so no provider-shaped value is committed.
STRIPE_TEST_KEY = "offline-test-bearer-token"
WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def stripe_env(monkeypatch):
    """A configured test-mode Stripe key and webhook secret in the environment."""
    monkeypatch.setenv("STRIPE_API_KEY", STRIPE_TEST_KEY)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)


class _FakeResponse:
    """The minimum ``urlopen`` context-manager surface the service uses."""

    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


class _FakeStripe:
    """A recording, scripted stand-in for ``urllib.request.urlopen``.

    ``replies`` are consumed in order: a ``dict`` is answered as a 200 JSON
    body, an ``Exception`` is raised. Every ``Request`` is kept, so a test
    asserts the exact call the service made — URL, method, headers and form
    body — without any network involvement.
    """

    def __init__(self, *replies: dict | Exception):
        self._replies: list[dict | Exception] = list(replies)
        self.requests: list[urllib.request.Request] = []

    def __call__(self, req: urllib.request.Request, timeout: float | None = None):
        self.requests.append(req)
        reply = self._replies.pop(0) if self._replies else {}
        if isinstance(reply, Exception):
            raise reply
        return _FakeResponse(reply)

    @property
    def last(self) -> urllib.request.Request:
        return self.requests[-1]


def _intent(
    payment_id: str = "pi_test_123",
    *,
    status: str = "requires_payment_method",
    currency: str = "usd",
    amount: int = 2550,
) -> dict:
    """A Stripe PaymentIntent body as the provider renders it."""
    return {
        "id": payment_id,
        "object": "payment_intent",
        "amount": amount,
        "currency": currency,
        "status": status,
        "client_secret": f"{payment_id}_secret_test",
    }


def _card_declined() -> urllib.error.HTTPError:
    """A 402 card_error, exactly as Stripe answers a declined card."""
    body = json.dumps(
        {
            "error": {
                "type": "card_error",
                "code": "card_declined",
                "message": "Your card was declined.",
            }
        }
    ).encode("utf-8")
    hdrs = Message()
    hdrs["Content-Type"] = "application/json"
    return urllib.error.HTTPError(
        f"{STRIPE_API_BASE}{STRIPE_PAYMENT_INTENTS_PATH}",
        402,
        "Payment Required",
        hdrs,
        io.BytesIO(body),
    )


def _header(req: urllib.request.Request, name: str) -> str | None:
    """Case-insensitive header lookup (urllib stores keys capitalized)."""
    return next((v for k, v in req.headers.items() if k.lower() == name.lower()), None)


def _form(req: urllib.request.Request) -> dict[str, list[str]]:
    """The request's urlencoded body, parsed (the form body is always bytes)."""
    data = req.data
    if not isinstance(data, bytes):
        return {}
    return urllib.parse.parse_qs(data.decode("utf-8"))


def _seed_order(session, *, total: str = "25.50") -> MarketplaceOrder:
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


# --- the request leg: POST /v1/payment_intents ------------------------------


def test_create_builds_the_documented_form_body_and_idempotency_header(
    db_session, stripe_env, monkeypatch
):
    stripe = _FakeStripe(_intent())
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    svc = PaymentGateways(db_session)
    result = svc.create_international_payment(
        25.50,
        "USD",
        idempotency_key="order:o-1:attempt:1",
        metadata={"order_id": "o-1", "user_id": "u-1"},
    )

    req = stripe.last
    assert req.full_url == f"{STRIPE_API_BASE}{STRIPE_PAYMENT_INTENTS_PATH}"
    assert req.get_method() == "POST"
    assert _header(req, "Authorization") == f"Bearer {STRIPE_TEST_KEY}"
    assert _header(req, "Idempotency-Key") == "order:o-1:attempt:1"
    assert _header(req, "Content-Type") == "application/x-www-form-urlencoded"

    body = _form(req)
    assert body["amount"] == ["2550"]  # cents — Stripe's minor unit, not dollars
    assert body["currency"] == ["usd"]  # Stripe takes the ISO 4217 code lower-case
    assert body["automatic_payment_methods[enabled]"] == ["true"]
    assert body["metadata[order_id]"] == ["o-1"]
    assert body["metadata[user_id]"] == ["u-1"]

    # The gateway's own shape, straight from the provider's answer.
    assert result["payment_id"] == "pi_test_123"
    assert result["client_secret"] == "pi_test_123_secret_test"
    assert result["status"] == "requires_payment_method"
    assert result["raw"]["id"] == "pi_test_123"


def test_verify_parses_the_provider_response(db_session, stripe_env, monkeypatch):
    stripe = _FakeStripe(_intent("pi_test_abc", status="succeeded"))
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    svc = PaymentGateways(db_session)
    result = svc.verify_international_payment("pi_test_abc")

    req = stripe.last
    assert req.full_url == f"{STRIPE_API_BASE}{STRIPE_PAYMENT_INTENTS_PATH}/pi_test_abc"
    assert req.get_method() == "GET"
    assert not req.data  # a retrieve carries no body
    assert _header(req, "Authorization") == f"Bearer {STRIPE_TEST_KEY}"
    assert not req.has_header("Idempotency-key")

    assert result["payment_id"] == "pi_test_abc"
    assert result["status"] == "succeeded"
    assert result["client_secret"] == "pi_test_abc_secret_test"
    assert result["raw"]["amount"] == 2550


def test_a_provider_answer_without_an_id_is_refused(db_session, stripe_env, monkeypatch):
    """No id in the answer means no payment id comes back — none is invented."""
    stripe = _FakeStripe({"object": "payment_intent", "status": "succeeded"})
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    svc = PaymentGateways(db_session)
    with pytest.raises(PaymentError):
        svc.create_international_payment(25.50, "USD", idempotency_key="k")

    stripe = _FakeStripe({"object": "payment_intent", "status": "succeeded"})
    monkeypatch.setattr(urllib.request, "urlopen", stripe)
    with pytest.raises(PaymentError):
        svc.verify_international_payment("pi_gone")


# --- currency: the S-MONEY contract meets Stripe's minor units ---------------


def test_usd_is_charged_in_cents_and_irr_as_rials(db_session, stripe_env, monkeypatch):
    svc = PaymentGateways(db_session)

    usd = _FakeStripe(_intent(amount=2550, currency="usd"))
    monkeypatch.setattr(urllib.request, "urlopen", usd)
    svc.create_international_payment(25.50, "USD", idempotency_key="k")
    assert _form(usd.last)["amount"] == ["2550"]

    irr = _FakeStripe(_intent(amount=350000, currency="irr"))
    monkeypatch.setattr(urllib.request, "urlopen", irr)
    svc.create_international_payment(350000.0, "IRR", idempotency_key="k")
    body = _form(irr.last)
    assert body["amount"] == ["350000"]  # IRR is zero-decimal at Stripe
    assert body["currency"] == ["irr"]


def test_the_marketplace_default_currency_is_irr(db_session, stripe_env, monkeypatch):
    stripe = _FakeStripe(_intent(amount=350000, currency="irr"))
    monkeypatch.setattr(urllib.request, "urlopen", stripe)
    PaymentGateways(db_session).create_international_payment(350000.0, idempotency_key="k")
    assert _form(stripe.last)["currency"] == ["irr"]


def test_a_currency_the_platform_does_not_book_is_refused(
    db_session, stripe_env, monkeypatch
):
    stripe = _FakeStripe()
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    with pytest.raises(PaymentError, match="EUR"):
        PaymentGateways(db_session).create_international_payment(
            10.0, "eur", idempotency_key="k"
        )
    assert stripe.requests == []  # refused before any provider call


def test_booked_assets_that_are_not_currencies_are_refused(
    db_session, stripe_env, monkeypatch
):
    """ECO (the platform token) and CARBON_tCO2e (a quantity) settle nowhere."""
    stripe = _FakeStripe()
    monkeypatch.setattr(urllib.request, "urlopen", stripe)
    svc = PaymentGateways(db_session)

    with pytest.raises(PaymentError, match="ECO"):
        svc.create_international_payment(10.0, "ECO", idempotency_key="k")
    with pytest.raises(PaymentError, match="CARBON"):
        svc.create_international_payment(10.0, "CARBON_tCO2e", idempotency_key="k")
    assert stripe.requests == []


def test_a_sub_contract_precision_amount_is_refused(db_session, stripe_env, monkeypatch):
    """The S-MONEY contract caps money at 4 decimals; Stripe scales to cents."""
    stripe = _FakeStripe()
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    with pytest.raises(PaymentError, match="decimal places"):
        PaymentGateways(db_session).create_international_payment(
            10.12345, "USD", idempotency_key="k"
        )
    assert stripe.requests == []


# --- honest degradation ------------------------------------------------------


def test_a_missing_api_key_fails_loud_without_any_provider_call(db_session, monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    stripe = _FakeStripe()
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    svc = PaymentGateways(db_session)
    with pytest.raises(PaymentError, match="STRIPE_API_KEY"):
        svc.create_international_payment(25.50, "USD", idempotency_key="k")
    with pytest.raises(PaymentError, match="STRIPE_API_KEY"):
        svc.verify_international_payment("pi_test_123")

    # Honest degradation: no fabricated payment id, no provider call at all.
    assert stripe.requests == []


def test_a_declined_card_surfaces_as_a_typed_error(db_session, stripe_env, monkeypatch):
    stripe = _FakeStripe(_card_declined())
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    with pytest.raises(PaymentError, match="declined"):
        PaymentGateways(db_session).create_international_payment(
            25.50, "USD", idempotency_key="k"
        )


def test_an_unreachable_provider_is_a_typed_error(db_session, stripe_env, monkeypatch):
    stripe = _FakeStripe(urllib.error.URLError("connection refused"))
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    with pytest.raises(PaymentError, match="unreachable"):
        PaymentGateways(db_session).create_international_payment(
            25.50, "USD", idempotency_key="k"
        )


# --- webhook signature: the documented Stripe scheme -------------------------


def _sign(secret: str, timestamp: int, payload: bytes) -> str:
    """A ``Stripe-Signature`` header built the documented way."""
    digest = hmac.new(
        secret.encode("utf-8"), f"{timestamp}.".encode() + payload, hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_a_valid_signature_is_accepted():
    payload = json.dumps(
        {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test_123"}}}
    ).encode("utf-8")
    header = _sign(WEBHOOK_SECRET, int(time.time()), payload)
    assert verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is True


def test_a_tampered_payload_is_rejected():
    payload = b'{"type":"payment_intent.succeeded"}'
    header = _sign(WEBHOOK_SECRET, int(time.time()), payload)
    tampered = b'{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_evil"}}}'
    assert verify_stripe_webhook_signature(tampered, header, secret=WEBHOOK_SECRET) is False


def test_a_stale_timestamp_is_rejected():
    payload = b'{"type":"payment_intent.succeeded"}'
    stale = int(time.time()) - STRIPE_WEBHOOK_TOLERANCE_SECONDS - 60
    header = _sign(WEBHOOK_SECRET, stale, payload)
    assert verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is False

    # The same payload freshly signed still passes: it was the age of the
    # signature, not the digest, that was rejected.
    fresh = _sign(WEBHOOK_SECRET, int(time.time()), payload)
    assert verify_stripe_webhook_signature(payload, fresh, secret=WEBHOOK_SECRET) is True


def test_a_future_timestamp_outside_the_tolerance_is_rejected():
    payload = b'{"type":"ping"}'
    ahead = int(time.time()) + STRIPE_WEBHOOK_TOLERANCE_SECONDS + 60
    header = _sign(WEBHOOK_SECRET, ahead, payload)
    assert verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is False


def test_a_signature_from_the_wrong_secret_is_rejected():
    payload = b'{"type":"ping"}'
    header = _sign("whsec_someone_else", int(time.time()), payload)
    assert verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is False


def test_a_malformed_header_is_rejected():
    payload = b'{"type":"ping"}'
    for header in ("", "v1=deadbeef", "t=notanumber,v1=deadbeef", "t=1"):
        assert (
            verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is False
        ), header


def test_a_second_v1_entry_does_not_defeat_verification():
    """Stripe may send several digests; any matching ``v1`` entry accepts."""
    payload = b'{"type":"ping"}'
    timestamp = int(time.time())
    digest = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    header = f"t={timestamp},v1={'0' * 64},v1={digest}"
    assert verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is True


def test_a_str_payload_is_signed_over_its_utf8_bytes():
    payload = '{"type":"ping","note":"€"}'
    encoded = payload.encode("utf-8")
    header = _sign(WEBHOOK_SECRET, int(time.time()), encoded)
    assert verify_stripe_webhook_signature(payload, header, secret=WEBHOOK_SECRET) is True


def test_the_secret_defaults_to_the_environment(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_from_env")
    payload = b'{"type":"ping"}'
    header = _sign("whsec_from_env", int(time.time()), payload)
    assert verify_stripe_webhook_signature(payload, header) is True


def test_an_unconfigured_webhook_secret_fails_loud(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    with pytest.raises(PaymentError, match="STRIPE_WEBHOOK_SECRET"):
        verify_stripe_webhook_signature(b'{"type":"ping"}', "t=1,v1=abc")


# --- escrow integration: the same chain the other rails take ----------------


def test_a_successful_international_payment_holds_escrow_like_the_other_rails(
    db_session, stripe_env, monkeypatch
):
    """create -> verify -> hold, the same chain the zarinpal/bank paths take."""
    stripe = _FakeStripe(_intent("pi_ok"), _intent("pi_ok", status="succeeded"))
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    order = _seed_order(db_session)
    svc = PaymentGateways(db_session)
    payment = svc.create(
        order_id=str(order.id),
        user_id="buyer-1",
        gateway="international",
        amount=25.50,
        currency="USD",
    )

    assert payment.status == "redirected"
    assert payment.authority == "pi_ok"
    assert payment.currency == "USD"  # the settlement code lands on the row
    # The idempotency key is order-scoped, so a retry cannot double-charge.
    assert _header(stripe.last, "Idempotency-Key") == f"order:{order.id}"

    payment = svc.verify(payment)
    assert payment.status == "verified"
    assert payment.escrow_status == "held"
    assert payment.ref_id == "pi_ok"

    entries = EscrowService(db_session).by_order(str(order.id))
    assert [e.entry_type for e in entries] == ["hold"]
    assert entries[0].currency == "USD"  # the escrow ledger carries the same code

    reloaded = db_session.get(MarketplaceOrder, str(order.id))
    assert reloaded.status == MarketplaceOrderStatus.PAID
    assert reloaded.payment_status == "paid"


def test_international_escrow_releases_after_delivery_confirmation(
    db_session, stripe_env, monkeypatch
):
    """The full lifecycle: hold -> release, with the double-spend guard."""
    stripe = _FakeStripe(_intent("pi_life"), _intent("pi_life", status="succeeded"))
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    order = _seed_order(db_session)
    svc = PaymentGateways(db_session)
    payment = svc.create(
        order_id=str(order.id),
        user_id="buyer-1",
        gateway="international",
        amount=25.50,
        currency="USD",
    )
    payment = svc.verify(payment)

    escrow = EscrowService(db_session)
    entry = escrow.release(str(payment.id), actor_id="admin-1")
    assert entry.entry_type == "release"
    assert payment.escrow_status == "released"
    with pytest.raises(PaymentError):
        escrow.release(str(payment.id))
    with pytest.raises(PaymentError):
        escrow.refund(str(payment.id))


def test_a_non_succeeded_intent_never_holds_escrow(db_session, stripe_env, monkeypatch):
    """The hold is the money movement: an unpaid intent must not move it."""
    stripe = _FakeStripe(
        _intent("pi_unpaid"),
        _intent("pi_unpaid", status="requires_payment_method"),
    )
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    order = _seed_order(db_session)
    svc = PaymentGateways(db_session)
    payment = svc.create(
        order_id=str(order.id),
        user_id="buyer-1",
        gateway="international",
        amount=25.50,
        currency="USD",
    )
    with pytest.raises(PaymentError, match="requires_payment_method"):
        svc.verify(payment)

    assert payment.status == "failed"
    assert payment.escrow_status == "none"
    assert EscrowService(db_session).by_order(str(order.id)) == []

    reloaded = db_session.get(MarketplaceOrder, str(order.id))
    assert reloaded.status == MarketplaceOrderStatus.PENDING  # never advanced


def test_verify_refuses_a_payment_without_a_stripe_id(db_session, stripe_env, monkeypatch):
    """A payment row whose create never ran carries no id to verify."""
    stripe = _FakeStripe()
    monkeypatch.setattr(urllib.request, "urlopen", stripe)

    payment = MarketplacePayment(
        order_id="o-1", user_id="buyer-1", gateway="international", amount=25.50
    )
    db_session.add(payment)
    db_session.commit()

    with pytest.raises(PaymentError, match="Stripe"):
        PaymentGateways(db_session).verify(payment)
    assert stripe.requests == []
