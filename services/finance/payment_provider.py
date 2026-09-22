"""Payment Provider Abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AuditEvent, ComPaymentIntent
from services.api_gateway.exceptions import EcoNojinException


@dataclass
class PaymentIntent:
    """Payment intent data."""

    id: str
    amount: Decimal
    currency: str
    status: str  # requires_action, processing, succeeded, failed, canceled
    provider: str
    provider_reference: str | None
    metadata: dict
    created_at: datetime
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    failure_reason: str | None = None


@dataclass
class WebhookEvent:
    """Normalized webhook event."""

    provider: str
    event_type: str
    provider_event_id: str
    payment_id: str
    amount: Decimal
    currency: str
    status: str
    raw_payload: dict
    received_at: datetime


class PaymentProvider(ABC):
    """Abstract base class for payment providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'stripe', 'wallet', 'bank_transfer', 'cod')."""
        pass

    @abstractmethod
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        """Create a payment intent."""
        pass

    @abstractmethod
    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        """Confirm a payment (for COD/wallet)."""
        pass

    @abstractmethod
    async def cancel_payment(self, payment_id: str, reason: str) -> PaymentIntent:
        """Cancel a payment."""
        pass

    @abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify and parse webhook payload."""
        pass

    @abstractmethod
    async def refund(self, payment_id: str, amount: Decimal, reason: str) -> PaymentIntent:
        """Process refund."""
        pass


class StripeProvider:
    """Stripe payment provider implementation."""

    provider_name = "stripe"

    def __init__(self, api_key: str, webhook_secret: str):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        # import stripe
        # stripe.api_key = api_key

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        # TODO: Implement Stripe PaymentIntent creation
        # intent = stripe.PaymentIntent.create(
        #     amount=int(amount * 100),  # Stripe uses minor units
        #     currency=currency.lower(),
        #     metadata={**metadata, "order_id": order_id},
        #     idempotency_key=idempotency_key,
        # )
        # return PaymentIntent(...)
        raise NotImplementedError("Stripe integration pending")

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        # Verify Stripe signature
        # event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
        raise NotImplementedError("Stripe webhook verification pending")


class WalletProvider:
    """Internal wallet payment provider (ECO wallet / IRR wallet)."""

    provider_name = "wallet"

    def __init__(self, wallet_service: WalletService):
        self.wallet_service = wallet_service

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        # For wallet payments, we just create a pending payment record
        # The actual deduction happens on confirmation
        return PaymentIntent(
            id=f"pay_{int(datetime.now().timestamp())}_{order_id}",
            amount=amount,
            currency=currency,
            status="requires_action",
            provider="wallet",
            provider_reference=None,
            metadata={"order_id": order_id, **metadata},
            created_at=datetime.now(UTC),
        )

    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        # Wallet payments are confirmed by deducting from wallet
        # This would be called after order confirmation
        raise NotImplementedError("Wallet confirm needs wallet service integration")

    async def verify_webhook(self, payload: bytes, signature: str):
        raise NotImplementedError("Wallet payments don't use webhooks")


class CODProvider:
    """Cash on Delivery provider."""

    provider_name = "cod"

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        return PaymentIntent(
            id=f"cod_{int(datetime.now().timestamp())}_{order_id}",
            amount=amount,
            currency=currency,
            status="pending",
            provider="cod",
            provider_reference=None,
            metadata=metadata,
            created_at=datetime.now(UTC),
        )

    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        # COD is confirmed on delivery
        raise NotImplementedError

    async def verify_webhook(self, payload: bytes, signature: str):
        raise NotImplementedError("COD doesn't use webhooks")


class BankTransferProvider(PaymentProvider):
    """Bank transfer (علی‌حساب) payment provider.

    Creates an ``awaiting_transfer`` payment intent persisted as a
    ``ComPaymentIntent`` row and verifies the transfer against the recorded
    amount.  Supports full, partial and already-verified transitions and writes
    an immutable ``AuditEvent`` on verification.
    """

    provider_name = "bank_transfer"

    def __init__(self, db: AsyncSession):
        self.db = db

    def _bank_account(self) -> str:
        import os

        return (
            os.getenv("BANK_TRANSFER_SHEBA", "").strip()
            or os.getenv("BANK_TRANSFER_CARD_NUMBER", "").strip()
            or "IR00000000000000000000000000"
        )

    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        order_id: str,
        metadata: dict,
        idempotency_key: str,
    ) -> PaymentIntent:
        # Idempotency: return the existing intent for the same key.
        existing = await self.db.execute(
            select(ComPaymentIntent).where(
                ComPaymentIntent.payment_metadata["idempotency_key"].as_string() == idempotency_key,
                ComPaymentIntent.provider == "bank_transfer",
            )
        )
        prior = existing.scalar_one_or_none()
        if prior is not None:
            return self._to_dataclass(prior, metadata)

        provider_reference = f"BT-{uuid4().hex[:12]}"
        reference_number = provider_reference
        enriched_metadata = {
            **metadata,
            "bank_account": self._bank_account(),
            "reference_number": reference_number,
            "idempotency_key": idempotency_key,
        }

        payment = ComPaymentIntent(
            id=str(uuid4()),
            order_id=order_id,
            buyer_id=str(metadata.get("buyer_id", "")) if metadata.get("buyer_id") else None,
            provider="bank_transfer",
            amount=amount,
            currency=currency,
            status="awaiting_transfer",
            provider_reference=provider_reference,
            payment_metadata=enriched_metadata,
            created_at=datetime.now(UTC),
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return self._to_dataclass(payment, enriched_metadata)

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

    async def verify_transfer(
        self,
        payment_id,
        transferred_amount: Decimal,
        verified_by: str,
        description: str | None = None,
    ) -> PaymentIntent | None:
        # ``payment_id`` may arrive as int or str.
        try:
            pk = int(payment_id)
        except (TypeError, ValueError):
            pk = None

        result = await self.db.execute(
            select(ComPaymentIntent).where(ComPaymentIntent.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment is None and pk is not None:
            result = await self.db.execute(
                select(ComPaymentIntent).where(ComPaymentIntent.id == pk)
            )
            payment = result.scalar_one_or_none()
        if payment is None:
            return None

        if transferred_amount < 0:
            raise EcoNojinException("Transfer amount cannot be negative", code="INVALID_AMOUNT")

        # Already fully verified — a second verification is not allowed.
        if payment.status == "succeeded":
            raise EcoNojinException("Transfer already verified", code="ALREADY_VERIFIED")

        if transferred_amount == payment.amount:
            payment.status = "succeeded"
            confirmed = True
            failure_reason = None
        elif transferred_amount < payment.amount:
            payment.status = "partial"
            failure_reason = f"Partial payment: {transferred_amount} of {payment.amount} received"
            confirmed = False
        else:
            payment.status = "succeeded"
            failure_reason = None
            confirmed = True

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # Immutable audit trail for the verification.
        self.db.add(
            AuditEvent(
                correlation_id=str(payment.id),
                actor_id=str(verified_by),
                action="bank_transfer_verify",
                resource_type="payment",
                resource_id=str(payment.id),
                before_state={"status": "awaiting_transfer"},
                after_state={
                    "status": payment.status,
                    "transferred_amount": str(transferred_amount),
                    "verified_by": str(verified_by),
                    "description": description,
                },
                created_at=datetime.now(UTC),
            )
        )
        await self.db.commit()

        return PaymentIntent(
            id=str(payment.id),
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            provider_reference=payment.provider_reference,
            metadata=payment.payment_metadata or {},
            created_at=payment.created_at,
            confirmed_at=datetime.now(UTC) if confirmed else None,
            failure_reason=failure_reason,
        )

    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        raise NotImplementedError("Bank transfer confirmation is manual")

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
        raise NotImplementedError("Bank transfer does not use webhooks")

    async def refund(self, payment_id: str, amount: Decimal, reason: str) -> PaymentIntent:
        raise NotImplementedError("Bank transfer refund is manual")


# Provider Registry
class PaymentProviderRegistry:
    """Registry for payment providers."""

    def __init__(self):
        self._providers: dict[str, PaymentProvider] = {}

    def register(self, provider: PaymentProvider):
        self._providers[provider.provider_name] = provider

    def get(self, provider_name: str) -> PaymentProvider:
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown payment provider: {provider_name}")
        return provider

    def get_all(self) -> list[PaymentProvider]:
        return list(self._providers.values())


# Global registry instance
payment_registry = PaymentProviderRegistry()
