"""Payment Provider Abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import UTC, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.api_gateway.exceptions import EcoNojinException


@dataclass
class PaymentIntent:
    """Payment intent data."""
    id: str
    amount: Decimal
    currency: str
    status: str  # requires_action, processing, succeeded, failed, canceled
    provider: str
    provider_reference: Optional[str]
    metadata: dict
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    failure_reason: Optional[str] = None


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
    
    def __init__(self, wallet_service: "WalletService"):
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