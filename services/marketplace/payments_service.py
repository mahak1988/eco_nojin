"""Multi-gateway payment service with smart-escrow hold/release (plan v2.1).

Gateways
--------
- ``zarinpal``      : real ZarinPal v4 REST (request/verify); requires
  ``ZARINPAL_MERCHANT_ID``; ``ZARINPAL_SANDBOX=1`` switches to sandbox host.
- ``bank``          : direct bank transfer (کارت به کارت) — returns the
  configured account instructions and waits for the buyer's tracking code.
- ``international`` : external checkout link via ``INTL_PAYMENT_CHECKOUT_URL``
  (Stripe/PayPal payment page) — honest error when unconfigured.

Escrow
------
After gateway verification the amount is recorded as an immutale ``hold``
ledger entry; it is ``release``-d when the buyer confirms delivery (or an
admin releases it) and ``refund``-ed on cancellation. This mirrors the
on-chain EscrowWithDispute contract for fiat rails.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models.marketplace_payment import MarketplaceEscrowEntry, MarketplacePayment

VALID_GATEWAYS = ("zarinpal", "bank", "international")

ZARINPAL_PAY_URL = "https://payment.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_SANDBOX_PAY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_SANDBOX_VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_START_PAY = "https://payment.zarinpal.com/pg/StartPay/"
ZARINPAL_SANDBOX_START_PAY = "https://sandbox.zarinpal.com/pg/StartPay/"


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
        else:  # international
            link = os.getenv("INTL_PAYMENT_CHECKOUT_URL", "").strip()
            if not link:
                raise PaymentError(
                    "درگاه بینالمللی پیکربندی نشده است (INTL_PAYMENT_CHECKOUT_URL خالی است)"
                )
            payment.redirect_url = f"{link}?amount={amount}&order={order_id}"
            payment.status = "redirected"

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
        # international: confirmed manually by the operator (documented flow)

        payment.status = "verified"
        self.db.commit()
        EscrowService(self.db).hold(payment)
        return payment


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
