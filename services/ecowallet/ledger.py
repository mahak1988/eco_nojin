"""ECO Wallet Centralized Ledger.

Phase 1: Centralized ledger (no blockchain needed).
Design: Simple, positive, no technical jargon.

Phase 4 consolidation (S-MONEY): amounts are ``Decimal`` rather than ``float``
and timestamps are timezone-aware. The wallet column in the database is
``Numeric(19, 4)``, and this module was round-tripping that precision through
binary floating point. The public methods accept ``float | Decimal | str`` and
return ``Decimal``; callers that need a float convert at the boundary.
"""

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

ZERO = Decimal("0")


def _decimal(value: float | Decimal | str | int | None) -> Decimal:
    """Coerce to Decimal. A float is routed through ``str`` so that the value
    the caller wrote is the value that is stored."""
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(str(value))


class TransactionType(Enum):
    EARN = "earn"
    REDEEM = "redeem"
    TRANSFER = "transfer"
    ADMIN = "admin"


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class EcoTransaction:
    transaction_id: str
    user_id: str
    amount: Decimal
    transaction_type: TransactionType
    description: str
    category: str
    timestamp: datetime = field(default_factory=_now)
    balance_after: Decimal = ZERO


@dataclass
class EcoWallet:
    user_id: str
    balance: Decimal = ZERO
    total_earned: Decimal = ZERO
    total_redeemed: Decimal = ZERO
    created_at: datetime = field(default_factory=_now)
    last_activity: datetime = field(default_factory=_now)
    is_active: bool = True


class EcoLedger:
    """Centralized ECO ledger (Phase 1).

    Not a cryptocurrency. Similar to airline miles or gift cards.
    No regulatory license required.
    """

    def __init__(self):
        self.wallets: dict[str, EcoWallet] = {}
        self.transactions: dict[str, list[EcoTransaction]] = {}

    def create_wallet(self, user_id: str) -> EcoWallet:
        if user_id in self.wallets:
            raise ValueError(f"Wallet already exists for user: {user_id}")
        wallet = EcoWallet(user_id=user_id)
        self.wallets[user_id] = wallet
        self.transactions[user_id] = []
        return wallet

    def get_wallet(self, user_id: str) -> EcoWallet | None:
        return self.wallets.get(user_id)

    def get_balance(self, user_id: str) -> Decimal:
        wallet = self.wallets.get(user_id)
        return wallet.balance if wallet else ZERO

    def earn(
        self, user_id: str, amount: float | Decimal, category: str, description: str
    ) -> EcoTransaction:
        wallet = self.wallets.get(user_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {user_id}")
        value = _decimal(amount)
        if value <= 0:
            raise ValueError("Amount must be positive")

        wallet.balance += value
        wallet.total_earned += value
        wallet.last_activity = _now()

        tx = EcoTransaction(
            transaction_id=str(uuid.uuid4()),
            user_id=user_id,
            amount=value,
            transaction_type=TransactionType.EARN,
            description=description,
            category=category,
            balance_after=wallet.balance,
        )
        self.transactions[user_id].append(tx)
        return tx

    def redeem(
        self, user_id: str, amount: float | Decimal, category: str, description: str
    ) -> EcoTransaction:
        wallet = self.wallets.get(user_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {user_id}")
        value = _decimal(amount)
        if value <= 0:
            raise ValueError("Amount must be positive")
        if wallet.balance < value:
            raise ValueError(f"Insufficient balance. Available: {wallet.balance}")

        wallet.balance -= value
        wallet.total_redeemed += value
        wallet.last_activity = _now()

        tx = EcoTransaction(
            transaction_id=str(uuid.uuid4()),
            user_id=user_id,
            amount=value,
            transaction_type=TransactionType.REDEEM,
            description=description,
            category=category,
            balance_after=wallet.balance,
        )
        self.transactions[user_id].append(tx)
        return tx

    def get_transaction_history(self, user_id: str, limit: int = 50) -> list[EcoTransaction]:
        transactions = self.transactions.get(user_id, [])
        return transactions[-limit:]

    def get_stats(self) -> dict:
        total_wallets = len(self.wallets)
        total_eco_in_circulation = sum((w.balance for w in self.wallets.values()), ZERO)
        total_eco_earned = sum((w.total_earned for w in self.wallets.values()), ZERO)
        total_eco_redeemed = sum((w.total_redeemed for w in self.wallets.values()), ZERO)
        active_wallets = sum(1 for w in self.wallets.values() if w.is_active)
        return {
            "total_wallets": total_wallets,
            "active_wallets": active_wallets,
            "total_eco_in_circulation": total_eco_in_circulation.quantize(Decimal("0.01")),
            "total_eco_earned": total_eco_earned.quantize(Decimal("0.01")),
            "total_eco_redeemed": total_eco_redeemed.quantize(Decimal("0.01")),
            "total_transactions": sum(len(txs) for txs in self.transactions.values()),
        }


_ledger: EcoLedger | None = None
_ledger_lock = threading.RLock()


def get_eco_ledger() -> EcoLedger:
    """Process-wide ledger singleton.

    Locked: the previous check-then-assign was unsynchronised, so two
    concurrent first callers could each build a ledger and one's balances
    would vanish.
    """
    global _ledger
    if _ledger is None:
        with _ledger_lock:
            if _ledger is None:
                _ledger = EcoLedger()
    return _ledger
