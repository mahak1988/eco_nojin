"""Finance module - Financial core services for Eco Nojin."""

from __future__ import annotations

# KN-20 (fixed in P4): ``wallet_service`` does ``from services.finance import
# earning_rates`` while this ``__init__`` is still executing, so the attribute
# does not exist yet and a test module that imports finance first raises
# ImportError. Importing the leaf submodule first sets the attribute before the
# dependent module runs — the one-line ordering fix, no lazy imports needed.
from services.finance import earning_rates  # noqa: F401  (imported for its side effect)
from services.finance.ledger_service import LedgerService
from services.finance.payment_provider import (
    CODProvider,
    PaymentIntent,
    PaymentProvider,
    PaymentProviderRegistry,
    StripeProvider,
    WalletProvider,
    WebhookEvent,
    payment_registry,
)
from services.finance.reconciliation import ReconciliationService
from services.finance.wallet_service import WalletService

__all__ = [
    "CODProvider",
    "LedgerService",
    "PaymentIntent",
    "PaymentProvider",
    "PaymentProviderRegistry",
    "ReconciliationService",
    "StripeProvider",
    "WalletProvider",
    "WalletService",
    "WebhookEvent",
    "payment_registry",
]
