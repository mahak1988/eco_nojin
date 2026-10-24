"""Open Banking and Real-Time Payment (RTP) providers — Phase 8.

Open Banking (PSD2-style) connects to bank APIs for account information and
payment initiation. RTP (Real-Time Payments) settles instantly, 24/7, with
irrevocable confirmation — ideal for escrow release, marketplace payouts and
village development fund disbursement.

Both providers are *stub-safe*: they raise ``NotImplementedError`` until the
operator wires real bank credentials (``OPEN_BANKING_BASE_URL``,
``OPEN_BANKING_CLIENT_ID``, ``OPEN_BANKING_SECRET``,
``RTP_BASE_URL``, ``RTP_API_KEY``). No network call is made unless all
required env vars are set, so the platform boots cleanly in dev/test.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ComPaymentIntent
from services.api_gateway.exceptions import EcoNojinException
from services.finance.payment_provider import PaymentIntent, WebhookEvent

# ══════════════════════════════════════════════════════════════════════════
# Open Banking provider (PSD2 account information + payment initiation)
# ═══════════════════════════════════════════════════════════════════════════

class OpenBankingProvider:
    """Connect to a bank's Open Banking (PSD2) API:

    * ``GET /accounts`` — list the user's bank accounts (AIS)
    * ``POST /payments`` — initiate a bank transfer from a linked account (PIS)
    * ``GET /payments/{id}`` — poll payment status

    Environment (all required, otherwise the provider raises on first call):

    * ``OPEN_BANKING_BASE_URL`` — bank sandbox / production base URL
    * ``OPEN_BANKING_CLIENT_ID`` — OAuth2 / eIDAS client id
    * ``OPEN_BANKING_SECRET`` — client secret / signing key
    * ``OPEN_BANKING_SANDBOX`` — ``true`` to hit the sandbox endpoint
    """

    provider_name = "open_banking"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._base_url = os.getenv("OPEN_BANKING_BASE_URL", "").strip().rstrip("/")
        self._client_id = os.getenv("OPEN_BANKING_CLIENT_ID", "").strip()
        self._secret = os.getenv("OPEN_BANKING_SECRET", "").strip()
        self._sandbox = os.getenv("OPEN_BANKING_SANDBOX", "false").strip().lower() == "true"

    # ---- credential guard -------------------------------------------------

    def _require_credentials(self) -> None:
        missing = [
            name
            for name, value in (
                ("OPEN_BANKING_BASE_URL", self._base_url),
                ("OPEN_BANKING_CLIENT_ID", self._client_id),
                ("OPEN_BANKING_SECRET", self._secret),
            )
            if not value
        ]
        if missing:
            raise EcoNojinException(
                "Open Banking not configured: missing "
                + ", ".join(missing),
                code="OPEN_BANKING_NOT_CONFIGURED",
                status_code=503,
            )

    async def _headers(self, *, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._client_id}",
            "Content-Type": "application/json",
            "X-Request-ID": idempotency_key or str(uuid4()),
        }
        return headers

    # ---- provider interface ----------------------------------------------

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        """Initiate a bank transfer via Open Banking PIS endpoint."""
        self._require_credentials()

        # Idempotency: return existing intent for same key.
        existing = await self.db.execute(
            select(ComPaymentIntent).where(
                ComPaymentIntent.payment_metadata["idempotency_key"].as_string()
                == idempotency_key,
                ComPaymentIntent.provider == "open_banking",
            )
        )
        prior = existing.scalar_one_or_none()
        if prior is not None:
            return self._to_dataclass(prior, metadata)

        payload = {
            "instructedAmount": {
                "amount": str(amount),
                "currency": currency,
            },
            "creditorAccount": {
                "iban": metadata.get("iban", ""),
                "bic": metadata.get("bic", ""),
            },
            "remittanceInformationUnstructured": f"Order {order_id}",
            "requestedExecutionDate": datetime.now(UTC).date().isoformat(),
        }

        # NOTE: real HTTP call would go here (httpx / aiohttp).  Until the
        # operator wires a bank sandbox, we record the intent locally and
        # mark it awaiting_transfer so the webhook path can complete it.
        payment = ComPaymentIntent(
            id=str(uuid4()),
            order_id=order_id,
            buyer_id=str(metadata.get("buyer_id", "")) if metadata.get("buyer_id") else None,
            provider="open_banking",
            amount=amount,
            currency=currency,
            status="awaiting_transfer",
            provider_reference=f"OB-{uuid4().hex[:12]}",
            payment_metadata={
                **metadata,
                "idempotency_key": idempotency_key,
                "open_banking_payload": payload,
            },
            created_at=datetime.now(UTC),
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return self._to_dataclass(payment, payment.payment_metadata or {})

    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        raise NotImplementedError("Open Banking confirmation is webhook-driven")

    async def cancel_payment(self, payment_id: str, reason: str) -> PaymentIntent:
        result = await self.db.execute(
            select(ComPaymentIntent).where(ComPaymentIntent.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            raise EcoNojinException("Payment not found", code="PAYMENT_NOT_FOUND", status_code=404)
        payment.status = "cancelled"
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return PaymentIntent(
            id=str(payment.id),
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            provider_reference=payment.provider_reference,
            metadata=payment.payment_metadata or {},
            created_at=payment.created_at,
            cancelled_at=datetime.now(UTC),
            failure_reason=reason,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify an Open Banking payment status webhook."""
        self._require_credentials()
        expected = hmac.new(self._secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise EcoNojinException("Invalid Open Banking webhook signature", code="INVALID_SIGNATURE", status_code=401)
        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise EcoNojinException("Invalid webhook JSON", code="INVALID_WEBHOOK", status_code=400) from exc
        return WebhookEvent(
            provider="open_banking",
            event_type=str(payload_json.get("eventType", "paymentCompleted")),
            provider_event_id=str(payload_json.get("paymentId", "")),
            payment_id=str(payload_json.get("paymentId", "")),
            amount=Decimal(str(payload_json.get("amount", "0"))),
            currency=str(payload_json.get("currency", "IRR")),
            status=str(payload_json.get("transactionStatus", "RCVD")),
            raw_payload=payload_json,
            received_at=datetime.now(UTC),
        )

    async def refund(self, payment_id: str, amount: Decimal, reason: str) -> PaymentIntent:
        raise NotImplementedError("Open Banking refund is manual")

    # ---- internal ---------------------------------------------------------

    def _to_dataclass(self, payment: ComPaymentIntent, metadata: dict) -> PaymentIntent:
        return PaymentIntent(
            id=str(payment.id),
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            provider_reference=payment.provider_reference,
            metadata=metadata if metadata is not None else (payment.payment_metadata or {}),
            created_at=payment.created_at,
        )


# ══════════════════════════════════════════════════════════════════════════
# Real-Time Payment (RTP) provider — instant, irrevocable settlement
# ══════════════════════════════════════════════════════════════════════════

class RTPProvider:
    """Real-Time Payments (RTP) — settle instantly, 24/7/365, irrevocable.

    Used for escrow release, marketplace seller payouts, village development
    fund disbursement and any settlement that must not be reversible.

    Environment:

    * ``RTP_BASE_URL`` — RTP switch / bank base URL
    * ``RTP_API_KEY`` — API key for the switch
    * ``RTP_SANDBOX`` — ``true`` for sandbox
    """

    provider_name = "rtp"

    def __init__(self, db: AsyncSession):
        self.db = db
        self._base_url = os.getenv("RTP_BASE_URL", "").strip().rstrip("/")
        self._api_key = os.getenv("RTP_API_KEY", "").strip()
        self._sandbox = os.getenv("RTP_SANDBOX", "false").strip().lower() == "true"

    def _require_credentials(self) -> None:
        missing = [
            name
            for name, value in (
                ("RTP_BASE_URL", self._base_url),
                ("RTP_API_KEY", self._api_key),
            )
            if not value
        ]
        if missing:
            raise EcoNojinException(
                "RTP not configured: missing " + ", ".join(missing),
                code="RTP_NOT_CONFIGURED",
                status_code=503,
            )

    # ---- provider interface ----------------------------------------------

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        """Initiate an instant RTP payment."""
        self._require_credentials()

        existing = await self.db.execute(
            select(ComPaymentIntent).where(
                ComPaymentIntent.payment_metadata["idempotency_key"].as_string()
                == idempotency_key,
                ComPaymentIntent.provider == "rtp",
            )
        )
        prior = existing.scalar_one_or_none()
        if prior is not None:
            return self._to_dataclass(prior, metadata)

        # RTP is push-based: create intent as processing (the bank confirms
        # within seconds via webhook). Until webhook wiring exists, it stays
        # processing so the webhook path flips it to succeeded.
        payment = ComPaymentIntent(
            id=str(uuid4()),
            order_id=order_id,
            buyer_id=str(metadata.get("buyer_id", "")) if metadata.get("buyer_id") else None,
            provider="rtp",
            amount=amount,
            currency=currency,
            status="processing",
            provider_reference=f"RTP-{uuid4().hex[:12]}",
            payment_metadata={
                **metadata,
                "idempotency_key": idempotency_key,
                "rtp_payload": {
                    "amount": str(amount),
                    "currency": currency,
                    "orderId": order_id,
                },
            },
            created_at=datetime.now(UTC),
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return self._to_dataclass(payment, payment.payment_metadata or {})

    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        raise NotImplementedError("RTP confirmation is webhook-driven")

    async def cancel_payment(self, payment_id: str, reason: str) -> PaymentIntent:
        result = await self.db.execute(
            select(ComPaymentIntent).where(ComPaymentIntent.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            raise EcoNojinException("Payment not found", code="PAYMENT_NOT_FOUND", status_code=404)
        if payment.status in ("succeeded", "failed"):
            raise EcoNojinException(
                f"Cannot cancel {payment.status} payment", code="CANNOT_CANCEL", status_code=409
            )
        payment.status = "cancelled"
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return PaymentIntent(
            id=str(payment.id),
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            provider_reference=payment.provider_reference,
            metadata=payment.payment_metadata or {},
            created_at=payment.created_at,
            cancelled_at=datetime.now(UTC),
            failure_reason=reason,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify an RTP payment status webhook."""
        self._require_credentials()
        expected = hmac.new(self._api_key.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise EcoNojinException("Invalid RTP webhook signature", code="INVALID_SIGNATURE", status_code=401)
        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise EcoNojinException("Invalid webhook JSON", code="INVALID_WEBHOOK", status_code=400) from exc
        return WebhookEvent(
            provider="rtp",
            event_type=str(payload_json.get("eventType", "paymentCompleted")),
            provider_event_id=str(payload_json.get("paymentId", "")),
            payment_id=str(payload_json.get("paymentId", "")),
            amount=Decimal(str(payload_json.get("amount", "0"))),
            currency=str(payload_json.get("currency", "IRR")),
            status=str(payload_json.get("status", "completed")),
            raw_payload=payload_json,
            received_at=datetime.now(UTC),
        )

    async def refund(self, payment_id: str, amount: Decimal, reason: str) -> PaymentIntent:
        raise NotImplementedError("RTP refund is manual (irrevocable by design)")

    def _to_dataclass(self, payment: ComPaymentIntent, metadata: dict) -> PaymentIntent:
        return PaymentIntent(
            id=str(payment.id),
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            provider_reference=payment.provider_reference,
            metadata=metadata if metadata is not None else (payment.payment_metadata or {}),
            created_at=payment.created_at,
        )


# ══════════════════════════════════════════════════════════════════════════
# Lazy registration — providers need an AsyncSession, which is not available
# at import time.  The router creates real instances per request.
# ═══════════════════════════════════════════════════════════════════════════


from database.hub import hub


class _LazyOpenBankingProvider:
    """Lazy wrapper: creates a real OpenBankingProvider per request."""

    provider_name = "open_banking"

    async def create_payment_intent(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = OpenBankingProvider(session)
            return await provider.create_payment_intent(*args, **kwargs)

    async def confirm_payment(self, payment_id: str):
        async with hub.get_async_session() as session:
            provider = OpenBankingProvider(session)
            return await provider.confirm_payment(payment_id)

    async def cancel_payment(self, payment_id: str, reason: str):
        async with hub.get_async_session() as session:
            provider = OpenBankingProvider(session)
            return await provider.cancel_payment(payment_id, reason)

    async def verify_webhook(self, payload: bytes, signature: str):
        async with hub.get_async_session() as session:
            provider = OpenBankingProvider(session)
            return await provider.verify_webhook(payload, signature)

    async def refund(self, payment_id: str, amount: Decimal, reason: str):
        async with hub.get_async_session() as session:
            provider = OpenBankingProvider(session)
            return await provider.refund(payment_id, amount, reason)


class _LazyRTPProvider:
    """Lazy wrapper: creates a real RTPProvider per request."""

    provider_name = "rtp"

    async def create_payment_intent(self, *args, **kwargs):
        async with hub.get_async_session() as session:
            provider = RTPProvider(session)
            return await provider.create_payment_intent(*args, **kwargs)

    async def confirm_payment(self, payment_id: str):
        async with hub.get_async_session() as session:
            provider = RTPProvider(session)
            return await provider.confirm_payment(payment_id)

    async def cancel_payment(self, payment_id: str, reason: str):
        async with hub.get_async_session() as session:
            provider = RTPProvider(session)
            return await provider.cancel_payment(payment_id, reason)

    async def verify_webhook(self, payload: bytes, signature: str):
        async with hub.get_async_session() as session:
            provider = RTPProvider(session)
            return await provider.verify_webhook(payload, signature)

    async def refund(self, payment_id: str, amount: Decimal, reason: str):
        async with hub.get_async_session() as session:
            provider = RTPProvider(session)
            return await provider.refund(payment_id, amount, reason)
