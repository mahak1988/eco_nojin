from datetime import timezone
"""ECO Wallet Centralized Ledger.

Phase 1: Centralized ledger (no blockchain needed).
Design: Simple, positive, no technical jargon.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TransactionType(Enum):
    EARN = "earn"
    REDEEM = "redeem"
    TRANSFER = "transfer"
    ADMIN = "admin"


@dataclass
class EcoTransaction:
    transaction_id: str
    user_id: str
    amount: float
    transaction_type: TransactionType
    description: str
    category: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    balance_after: float = 0.0


@dataclass
class EcoWallet:
    user_id: str
    balance: float = 0.0
    total_earned: float = 0.0
    total_redeemed: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
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

    def get_balance(self, user_id: str) -> float:
        wallet = self.wallets.get(user_id)
        return wallet.balance if wallet else 0.0

    def earn(self, user_id: str, amount: float, category: str, description: str) -> EcoTransaction:
        wallet = self.wallets.get(user_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {user_id}")
        if amount <= 0:
            raise ValueError("Amount must be positive")

        wallet.balance += amount
        wallet.total_earned += amount
        wallet.last_activity = datetime.now(timezone.utc).replace(tzinfo=None)

        tx = EcoTransaction(
            transaction_id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.EARN,
            description=description,
            category=category,
            balance_after=wallet.balance,
        )
        self.transactions[user_id].append(tx)
        return tx

    def redeem(
        self, user_id: str, amount: float, category: str, description: str
    ) -> EcoTransaction:
        wallet = self.wallets.get(user_id)
        if not wallet:
            raise ValueError(f"Wallet not found: {user_id}")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if wallet.balance < amount:
            raise ValueError(f"Insufficient balance. Available: {wallet.balance}")

        wallet.balance -= amount
        wallet.total_redeemed += amount
        wallet.last_activity = datetime.now(timezone.utc).replace(tzinfo=None)

        tx = EcoTransaction(
            transaction_id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
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
        total_eco_in_circulation = sum(w.balance for w in self.wallets.values())
        total_eco_earned = sum(w.total_earned for w in self.wallets.values())
        total_eco_redeemed = sum(w.total_redeemed for w in self.wallets.values())
        active_wallets = sum(1 for w in self.wallets.values() if w.is_active)
        return {
            "total_wallets": total_wallets,
            "active_wallets": active_wallets,
            "total_eco_in_circulation": round(total_eco_in_circulation, 2),
            "total_eco_earned": round(total_eco_earned, 2),
            "total_eco_redeemed": round(total_eco_redeemed, 2),
            "total_transactions": sum(len(txs) for txs in self.transactions.values()),
        }


_ledger: EcoLedger | None = None


def get_eco_ledger() -> EcoLedger:
    global _ledger
    if _ledger is None:
        _ledger = EcoLedger()
    return _ledger
