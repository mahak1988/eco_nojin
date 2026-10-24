"""Multi-gateway payment service with smart-escrow hold/release (plan v2.1).

Gateways
--------
- ``zarinpal``      : real ZarinPal v4 REST (request/verify); requires
  ``ZARINPAL_MERCHANT_ID``; ``ZARINPAL_SANDBOX=1`` switches to sandbox host.
- ``bank``          : direct bank transfer (کارت به کارت) — returns the
  configured account instructions and waits for the buyer's tracking code.
- ``international`` : real Stripe REST PaymentIntent (request/verify) plus
  webhook signature verification; requires ``STRIPE_API_KEY`` (and
  ``STRIPE_WEBHOOK_SECRET`` for webhook verification) — honest error when
  unconfigured. The test sandbox is chosen by the key itself (``sk_test_``),
  not by a different host.

Escrow
------
After gateway verification the amount is recorded as an immutale ``hold``
ledger entry; it is ``release``-d when the buyer confirms delivery (or an
admin releases it) and ``refund``-ed on cancellation. This mirrors the
on-chain EscrowWithDispute contract for fiat rails.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import inspect
import json
import logging
import os
import time
import urllib.request
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode

from sqlalchemy import select
from sqlalchemy.orm import Session

from services._contracts.money import ALLOWED_ASSETS, Asset, Money, MoneyError, dec

from .models import MarketplaceOrder, MarketplaceOrderStatus
from .models.marketplace_payment import MarketplaceEscrowEntry, MarketplacePayment

logger = logging.getLogger(__name__)


async def _drive_publish(awaitable: Any) -> None:
    """Await an async publisher coroutine, swallowing any broker failure."""
    try:
        await awaitable
    except Exception as exc:  # noqa: BLE001 - broker failure must not propagate
        logger.warning("marketplace event publish failed: %s", exc)


def _emit_marketplace_event(
    event_type: str, aggregate_type: str, aggregate_id: str, payload: dict
) -> None:
    """Publish a marketplace domain event best-effort from synchronous code.

    These escrow/gateway methods run inside async route handlers (and inside
    ``PaymentGateways.verify``), so a running loop is usually present: the
    publish is scheduled on that loop — the one that owns the NATS connection —
    rather than blocking the caller. With no running loop (sync callers and
    tests) it is driven inline. Gated on ``enable_event_bus`` and fully
    failure-isolated, so a broker outage never breaks the committed escrow row.
    """
    try:
        from engine.hydroma.config.settings import get_settings

        if not get_settings().enable_event_bus:
            return
        from services.api_gateway.eventbus.publisher import publish_marketplace_event

        outcome = publish_marketplace_event(event_type, aggregate_type, aggregate_id, payload)
        if not inspect.isawaitable(outcome):
            return  # already resolved (e.g. a synchronous test double)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(_drive_publish(outcome))
        else:
            asyncio.run(_drive_publish(outcome))
    except Exception as exc:  # noqa: BLE001 - broker failure must not propagate
        logger.warning("marketplace event %r not published: %s", event_type, exc)


def _notify(
    db: Session,
    user_id: str,
    title: str,
    body: str = "",
    ntype: str = "system",
    link: str | None = None,
) -> None:
    """Deliver one owner-scoped in-app notification (best-effort, failure-isolated).

    ``NotificationDbService`` adds *and commits*, so its write must never run on
    the caller's session: a failing INSERT (``app_notifications`` missing, a
    constraint violation) rolls that session's transaction back and leaves it in
    ``PendingRollbackError``, so the next ``PaymentGateways.verify`` /
    ``EscrowService.release`` / ``refund`` commit raised and turned an
    already-verified payment into an HTTP 500. The notification therefore runs
    in its own unit of work — a fresh short-lived session taken from the repo's
    factory (``hub.get_session()``, which re-imports
    ``database.config.SessionLocal`` per call, so a repointed factory is
    honoured) — and its failure is rolled back with *that* session, never with
    the escrow row the caller already committed.

    ``db`` is kept for call-site symmetry only; handing it to
    ``NotificationDbService`` is exactly the session poisoning fixed here.
    Imported lazily to keep the notification module out of the import path.
    """
    try:
        from database.hub import hub
        from services.notification.db_service import NotificationDbService

        with hub.get_session() as session:
            NotificationDbService(session).notify(
                user_id, title, body=body, ntype=ntype, link=link
            )
    except Exception as exc:  # noqa: BLE001 - notification failure must not propagate
        logger.warning("notification to %s not delivered: %s", user_id, exc)

VALID_GATEWAYS = ("zarinpal", "bank", "international")

ZARINPAL_PAY_URL = "https://payment.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_SANDBOX_PAY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_SANDBOX_VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_START_PAY = "https://payment.zarinpal.com/pg/StartPay/"
ZARINPAL_SANDBOX_START_PAY = "https://sandbox.zarinpal.com/pg/StartPay/"

#: Stripe REST — the hosted-payment provider behind the ``international``
#: gateway. Test and live modes share one host: the mode is carried by the
#: key itself (``sk_test_…`` vs ``sk_live_…``), so no sandbox URL exists.
STRIPE_API_BASE = "https://api.stripe.com/v1"
STRIPE_PAYMENT_INTENTS_PATH = "/payment_intents"

#: Webhook freshness window in seconds — Stripe's documented default is five
#: minutes. A signature on an older timestamp is a replay, not a payment.
STRIPE_WEBHOOK_TOLERANCE_SECONDS = 300

#: Booked assets that are not ISO 4217 currencies: the platform token (ECO)
#: and the carbon quantity (CARBON_tCO2e). A card network settles neither.
_NON_FIAT_ASSETS = frozenset({Asset.ECO.value, Asset.CARBON.value})

#: ISO 4217 codes the international rail may settle — the fiat members of the
#: S-MONEY contract's ``ALLOWED_ASSETS`` (the marketplace is IRR-first).
INTL_CURRENCIES = frozenset(ALLOWED_ASSETS) - _NON_FIAT_ASSETS

#: ISO 4217 minor-unit exponent per settleable currency. Stripe takes an
#: integer in the smallest unit — cents for USD, a zero-decimal rial for IRR.
_INTL_MINOR_UNIT_EXPONENT: dict[str, int] = {"IRR": 0, "USD": 2}


class PaymentError(ValueError):
    """Raised for honest, user-facing payment configuration/flow errors."""


def _http_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


# -- international (Stripe REST) --------------------------------------------


def _require_intl_currency(currency: str) -> str:
    """Normalise and validate an international settlement currency, or raise.

    The marketplace is IRR-first, so an empty code defaults to ``IRR``. The
    international rail then takes any ISO 4217 code the S-MONEY contract
    books — the fiat members of ``ALLOWED_ASSETS`` — and refuses the platform
    token and the carbon quantity, which no card network settles.
    """
    code = str(currency or "").strip().upper() or Asset.IRR.value
    if code not in INTL_CURRENCIES:
        raise PaymentError(
            f"international payments settle in {sorted(INTL_CURRENCIES)}, got {code!r}"
        )
    return code


def _stripe_minor_units(amount: Decimal, currency: str) -> int:
    """Scale a ``Money`` amount to Stripe's integer smallest-unit amount."""
    exponent = _INTL_MINOR_UNIT_EXPONENT.get(currency)
    if exponent is None:
        raise PaymentError(f"no Stripe minor unit configured for {currency!r}")
    quantum = Decimal(1).scaleb(-exponent)
    return int((amount / quantum).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _stripe_api_key() -> str:
    """The configured Stripe secret key, or an honest typed error.

    Mirrors the zarinpal branch: an unconfigured gateway is an operator
    error that must be named, never a silent fallback to a fabricated id.
    """
    key = os.getenv("STRIPE_API_KEY", "").strip()
    if not key:
        raise PaymentError("درگاه بینالمللی پیکربندی نشده است (STRIPE_API_KEY خالی است)")
    return key


def _stripe_error_detail(exc: HTTPError) -> str:
    """The provider's own error text, or the HTTP status when there is none."""
    try:
        parsed = json.loads(exc.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - an unreadable body still earns a message
        return f"HTTP {exc.code}"
    if not isinstance(parsed, dict):
        return f"HTTP {exc.code}"
    error = parsed.get("error")
    if isinstance(error, dict):
        detail = error.get("message") or error.get("code") or error.get("type")
        if detail:
            return str(detail)
    return str(parsed)


def _stripe_request(
    method: str,
    path: str,
    form: dict[str, Any] | None = None,
    *,
    idempotency_key: str = "",
) -> dict[str, Any]:
    """One authenticated Stripe REST call, or an honest ``PaymentError``.

    Stripe speaks form-encoded bodies (not JSON) and answers a refusal with a
    JSON error body under a non-2xx status — a 402 ``card_declined`` is a
    declined card, so it surfaces as a typed error and is never read as a
    success. The ``Idempotency-Key`` header rides along on the request leg so
    a retried submission replays the same intent instead of charging twice.
    """
    body = urlencode(form).encode("utf-8") if form is not None else None
    headers = {"Authorization": f"Bearer {_stripe_api_key()}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(
        f"{STRIPE_API_BASE}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise PaymentError(
            f"درگاه بینالمللی درخواست را رد کرد (HTTP {exc.code}): {_stripe_error_detail(exc)}"
        ) from exc
    except urllib.error.URLError as exc:
        raise PaymentError(f"international gateway unreachable: {exc.reason}") from exc
    return payload


def verify_stripe_webhook_signature(
    payload: bytes | str,
    signature_header: str,
    *,
    secret: str | None = None,
    tolerance: int = STRIPE_WEBHOOK_TOLERANCE_SECONDS,
) -> bool:
    """Constant-time verification of a Stripe ``Stripe-Signature`` header.

    The documented scheme: the header carries ``t=<unix timestamp>`` and one
    or more ``v1=<hex digest>`` entries; the signed value is
    ``"{timestamp}.{raw payload}"`` under HMAC-SHA256 with the endpoint's
    ``STRIPE_WEBHOOK_SECRET``. A digest match inside the tolerance window
    accepts the event; a tampered body, a stale (replayed) timestamp, or a
    missing or malformed header is rejected with ``False``.

    An unset ``secret`` raises instead of returning ``False``: verifying
    under an empty secret would "accept" a signature anyone can recompute,
    which is the one failure this function must never have.

    ``payload`` must be the **raw** request body — re-serialising parsed JSON
    reorders keys and whitespace and breaks the digest.
    """
    if secret is None:
        secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise PaymentError(
            "درگاه بینالمللی پیکربندی نشده است (STRIPE_WEBHOOK_SECRET خالی است)"
        )
    entries: dict[str, list[str]] = {}
    for item in (signature_header or "").split(","):
        name, _, value = item.partition("=")
        entries.setdefault(name.strip(), []).append(value.strip())
    timestamps = entries.get("t") or []
    signatures = entries.get("v1") or []
    if len(timestamps) != 1 or not signatures:
        return False
    try:
        timestamp = int(timestamps[0])
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp) > tolerance:
        return False
    body = payload.encode("utf-8") if isinstance(payload, str) else payload
    signed = f"{timestamp}.".encode() + body
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return any(
        hmac.compare_digest(candidate.encode("utf-8", errors="replace"), expected.encode("ascii"))
        for candidate in signatures
    )


class PaymentGateways:
    """Creates and verifies gateway payments."""

    def __init__(self, db: Session, base_url: str = ""):
        self.db = db
        self.base_url = base_url.rstrip("/")

    # -- creation -----------------------------------------------------------

    def create(
        self,
        order_id: str,
        user_id: str,
        gateway: str,
        amount: float,
        currency: str = "IRR",
        description: str = "",
        callback_path: str = "/api/v1/marketplace/payments/zarinpal/callback",
    ) -> MarketplacePayment:
        if gateway not in VALID_GATEWAYS:
            raise PaymentError(f"unknown gateway: {gateway}")
        if amount <= 0:
            raise PaymentError("amount must be positive")

        payment = MarketplacePayment(
            order_id=order_id, user_id=user_id, gateway=gateway, amount=amount
        )
        if gateway == "zarinpal":
            data = self._zarinpal_request(amount, description, callback_path)
            payment.authority = data["authority"]
            payment.redirect_url = data["redirect_url"]
            payment.status = "redirected"
            payment.gateway_meta = json.dumps(data["raw"], ensure_ascii=False)[:2000]
        elif gateway == "bank":
            payment.status = "awaiting_verification"
            payment.redirect_url = None
        else:  # international — Stripe PaymentIntent (the request leg)
            code = _require_intl_currency(currency)
            data = self.create_international_payment(
                amount,
                code,
                idempotency_key=f"order:{order_id}",
                metadata={
                    "order_id": str(order_id),
                    "user_id": str(user_id),
                    "description": (description or "")[:255],
                },
            )
            payment.authority = data["payment_id"]
            payment.currency = code
            payment.redirect_url = None  # the client confirms via client_secret
            payment.status = "redirected"
            payment.gateway_meta = json.dumps(
                {
                    "payment_id": data["payment_id"],
                    "client_secret": data["client_secret"],
                    "status": data["status"],
                    "currency": code,
                    "amount": str(amount),
                },
                ensure_ascii=False,
            )[:2000]

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def _zarinpal_request(
        self, amount: float, description: str, callback_path: str
    ) -> dict[str, Any]:
        merchant = os.getenv("ZARINPAL_MERCHANT_ID", "").strip()
        if not merchant:
            raise PaymentError("درگاه زرینپال پیکربندی نشده است (ZARINPAL_MERCHANT_ID خالی است)")
        sandbox = os.getenv("ZARINPAL_SANDBOX", "0").strip() in ("1", "true", "yes")
        pay_url = ZARINPAL_SANDBOX_PAY_URL if sandbox else ZARINPAL_PAY_URL
        callback = f"{self.base_url}{callback_path}"
        raw = _http_json(
            pay_url,
            {
                "merchant_id": merchant,
                "amount": int(amount),  # zarinpal expects Tomans as int
                "callback_url": callback,
                "description": description[:255] or "Eco Nojin marketplace order",
            },
        )
        body = raw.get("data") or {}
        if raw.get("errors") or not body.get("authority"):
            raise PaymentError(f"زرینپال درخواست پرداخت را رد کرد: {raw.get('errors') or raw}")
        authority = body["authority"]
        start = ZARINPAL_SANDBOX_START_PAY if sandbox else ZARINPAL_START_PAY
        return {"authority": authority, "redirect_url": f"{start}{authority}", "raw": raw}

    def create_international_payment(
        self,
        amount: float,
        currency: str = "IRR",
        *,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create the Stripe PaymentIntent — the international request leg.

        POSTs ``/v1/payment_intents`` under the caller's idempotency key, so
        a retried submission replays the same intent instead of charging
        twice, and returns the gateway's own shape: the ``pi_...``
        ``payment_id``, the ``client_secret`` the payer's Stripe element
        confirms the payment with, and the provider ``status`` (``raw``
        carries the full answer for the ``gateway_meta`` audit trail). A
        missing ``STRIPE_API_KEY`` and a provider refusal are both honest
        ``PaymentError``s — no payment id is ever invented here.
        """
        code = _require_intl_currency(currency)
        try:
            money = Money(amount=dec(str(amount)), asset=code)
        except MoneyError as exc:
            raise PaymentError(str(exc)) from exc
        form: dict[str, Any] = {
            "amount": _stripe_minor_units(money.amount, code),
            "currency": code.lower(),  # Stripe takes the ISO 4217 code lower-case
            "automatic_payment_methods[enabled]": "true",
        }
        for name, value in (metadata or {}).items():
            form[f"metadata[{name}]"] = str(value)
        raw = _stripe_request(
            "POST", STRIPE_PAYMENT_INTENTS_PATH, form, idempotency_key=idempotency_key
        )
        payment_id = str(raw.get("id") or "")
        if not payment_id:
            raise PaymentError(f"درگاه بینالمللی شناسه پرداخت دریافت نکرد: {raw}")
        return {
            "payment_id": payment_id,
            "client_secret": str(raw.get("client_secret") or ""),
            "status": str(raw.get("status") or ""),
            "raw": raw,
        }

    def verify_international_payment(self, payment_id: str) -> dict[str, Any]:
        """Retrieve the Stripe PaymentIntent — the international verify leg.

        GETs ``/v1/payment_intents/{id}`` and parses the answer into the same
        gateway shape as the request leg, so the caller compares ``status``
        against ``succeeded`` itself. An unknown, failed or still-pending
        intent reports exactly what Stripe says — nothing is fabricated.
        """
        intent_id = str(payment_id or "").strip()
        if not intent_id:
            raise PaymentError("شناسه پرداخت بینالمللی الزامی است")
        raw = _stripe_request(
            "GET", f"{STRIPE_PAYMENT_INTENTS_PATH}/{quote(intent_id, safe='')}"
        )
        if not raw.get("id"):
            raise PaymentError(f"درگاه بینالمللی پرداخت {intent_id} را پیدا نکرد: {raw}")
        return {
            "payment_id": str(raw["id"]),
            "client_secret": str(raw.get("client_secret") or ""),
            "status": str(raw.get("status") or ""),
            "raw": raw,
        }

    # -- verification -------------------------------------------------------

    def verify(
        self, payment: MarketplacePayment, ref_id: str | None = None, card_pan: str | None = None
    ) -> MarketplacePayment:
        """Verify a payment with its gateway and move funds into escrow hold."""
        if payment.status in ("verified", "released_to_seller", "refunded"):
            raise PaymentError("payment already finalized")
        if payment.gateway == "zarinpal":
            merchant = os.getenv("ZARINPAL_MERCHANT_ID", "").strip()
            if not merchant:
                raise PaymentError("درگاه زرینپال پیکربندی نشده است")
            sandbox = os.getenv("ZARINPAL_SANDBOX", "0").strip() in ("1", "true", "yes")
            verify_url = ZARINPAL_SANDBOX_VERIFY_URL if sandbox else ZARINPAL_VERIFY_URL
            raw = _http_json(
                verify_url,
                {
                    "merchant_id": merchant,
                    "amount": int(payment.amount),
                    "authority": payment.authority,
                },
            )
            body = raw.get("data") or {}
            code = body.get("code") or raw.get("code")
            if code not in (100, 101):
                payment.status = "failed"
                payment.gateway_meta = json.dumps(raw, ensure_ascii=False)[:2000]
                self.db.commit()
                raise PaymentError(f"تأیید زرینپال ناموفق بود (code={code})")
            payment.ref_id = str(body.get("ref_id") or ref_id or "")
            payment.card_pan_masked = str(body.get("card_pan") or card_pan or "")
        elif payment.gateway == "bank":
            if not (ref_id or "").strip():
                raise PaymentError("شماره پیگیری انتقال بانکی الزامی است")
            payment.tracking_code = ref_id
            payment.ref_id = ref_id
        elif payment.gateway == "international":
            intent_id = str(payment.authority or "").strip()
            if not intent_id:
                raise PaymentError("پرداخت بینالمللی شناسه Stripe ندارد")
            data = self.verify_international_payment(intent_id)
            if data["status"] != "succeeded":
                payment.status = "failed"
                payment.gateway_meta = json.dumps(data["raw"], ensure_ascii=False)[:2000]
                self.db.commit()
                raise PaymentError(
                    f"تأیید درگاه بینالمللی ناموفق بود (status={data['status']})"
                )
            payment.ref_id = data["payment_id"]

        payment.status = "verified"
        self.db.commit()
        EscrowService(self.db).hold(payment)
        self._advance_order_for_payment(payment)

        _emit_marketplace_event(
            "payment_completed",
            "payment",
            str(payment.id),
            {
                "order_id": str(payment.order_id),
                "payment_id": str(payment.id),
                "amount": float(payment.amount),
                "gateway": str(payment.gateway),
            },
        )
        _notify(self.db, str(payment.user_id), "Your payment has been received.", ntype="payment")
        return payment

    def _advance_order_for_payment(self, payment: MarketplacePayment) -> None:
        """Advance the linked order's state once its funds are verified.

        Verification used to only move the payment and its escrow hold; the
        order itself stayed ``pending`` with ``payment_status="pending"``, so a
        paid order was indistinguishable from an unpaid one and could never be
        shipped. ``MarketplaceService.confirm_payment`` performs the same
        PENDING -> PAID transition but is async and reachable by no endpoint, so
        the sync gateway path applies it here on the same committed session.

        The only legal transition out of a freshly placed order is PENDING ->
        PAID, so that is the only one applied, and only when the order is still
        pending (a re-verify never rewinds an already-shipped order).
        """
        order = self.db.get(MarketplaceOrder, payment.order_id)
        if order is None or order.status != MarketplaceOrderStatus.PENDING:
            return
        order.payment_status = "paid"
        order.status = MarketplaceOrderStatus.PAID
        order.paid_at = datetime.now(UTC)
        self.db.commit()


class EscrowService:
    """Escrow ledger: hold on verified payment, release on delivery confirm."""

    def __init__(self, db: Session):
        self.db = db

    def hold(
        self,
        payment: MarketplacePayment,
        seller_id: str | None = None,
        marketplace_id: str | None = None,
        actor_id: str | None = None,
    ) -> MarketplaceEscrowEntry:
        if payment.escrow_status != "none":
            raise PaymentError("escrow already opened for this payment")
        entry = MarketplaceEscrowEntry(
            payment_id=payment.id,
            order_id=payment.order_id,
            entry_type="hold",
            amount=payment.amount,
            currency=payment.currency,
            seller_id=seller_id,
            marketplace_id=marketplace_id,
            actor_id=actor_id,
            note="funds held after gateway verification",
        )
        self.db.add(entry)
        payment.escrow_status = "held"
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def release(
        self,
        payment_id: str,
        actor_id: str | None = None,
        note: str = "released on delivery confirmation",
    ) -> MarketplaceEscrowEntry:
        payment = self.db.get(MarketplacePayment, payment_id)
        if payment is None:
            raise LookupError(f"payment not found: {payment_id}")
        if payment.escrow_status != "held":
            raise PaymentError(f"escrow is not held (status={payment.escrow_status})")
        entry = MarketplaceEscrowEntry(
            payment_id=payment.id,
            order_id=payment.order_id,
            entry_type="release",
            amount=payment.amount,
            currency=payment.currency,
            actor_id=actor_id,
            note=note,
        )
        self.db.add(entry)
        payment.escrow_status = "released"
        payment.status = "released_to_seller"
        self.db.commit()
        self.db.refresh(entry)

        _emit_marketplace_event(
            "settlement_posted",
            "order",
            str(payment.order_id),
            {
                "order_id": str(payment.order_id),
                "payment_id": str(payment.id),
                "escrow_id": str(entry.id),
                "amount": float(entry.amount),
                "actor_id": "" if actor_id is None else str(actor_id),
            },
        )
        _notify(
            self.db,
            str(payment.user_id),
            "Funds for your order have been released to the seller.",
            ntype="payment",
        )
        return entry

    def refund(
        self, payment_id: str, actor_id: str | None = None, note: str = "refunded to buyer"
    ) -> MarketplaceEscrowEntry:
        payment = self.db.get(MarketplacePayment, payment_id)
        if payment is None:
            raise LookupError(f"payment not found: {payment_id}")
        if payment.escrow_status != "held":
            raise PaymentError(f"escrow is not held (status={payment.escrow_status})")
        entry = MarketplaceEscrowEntry(
            payment_id=payment.id,
            order_id=payment.order_id,
            entry_type="refund",
            amount=payment.amount,
            currency=payment.currency,
            actor_id=actor_id,
            note=note,
        )
        self.db.add(entry)
        payment.escrow_status = "refunded"
        payment.status = "refunded"
        self.db.commit()
        self.db.refresh(entry)

        _emit_marketplace_event(
            "payment_refunded",
            "order",
            str(payment.order_id),
            {
                "order_id": str(payment.order_id),
                "payment_id": str(payment.id),
                "amount": float(entry.amount),
                "actor_id": "" if actor_id is None else str(actor_id),
            },
        )
        _notify(self.db, str(payment.user_id), "Your payment has been refunded.", ntype="payment")
        return entry

    def by_order(self, order_id: str) -> list[MarketplaceEscrowEntry]:
        stmt = select(MarketplaceEscrowEntry).where(MarketplaceEscrowEntry.order_id == order_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_payment(self, payment_id: str) -> MarketplacePayment:
        p = self.db.get(MarketplacePayment, payment_id)
        if p is None:
            raise LookupError(f"payment not found: {payment_id}")
        return p


def bank_instructions() -> dict[str, str]:
    """Static bank transfer instructions from env (کارت به کارت)."""
    return {
        "card_number": os.getenv("BANK_TRANSFER_CARD_NUMBER", "").strip(),
        "sheba": os.getenv("BANK_TRANSFER_SHEBA", "").strip(),
        "holder": os.getenv("BANK_TRANSFER_HOLDER", "").strip(),
    }
