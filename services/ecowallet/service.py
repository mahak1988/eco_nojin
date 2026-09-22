"""
EcoWallet service — DB-backed wallet operations (Phase 8).

Replaces the old in-memory ``_wallets`` dict: balances now persist in the
``ecowallet`` table (per user, unique).
"""

from __future__ import annotations

import threading
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import EcoWallet

_wallet_lock = threading.RLock()

# earning rates: category -> {eco, label} (kept in sync with the router)
EARNING_RATES: dict[str, dict[str, Any]] = {
    "tree_planting": {"eco": 50.0, "label": "کاشت درخت"},
    "soil_health": {"eco": 30.0, "label": "سلامت خاک"},
    "water_saving": {"eco": 25.0, "label": "صرفه‌جویی آب"},
    "carbon_credit": {"eco": 100.0, "label": "اعتبار کربن"},
    "education": {"eco": 10.0, "label": "آموزش"},
    "community": {"eco": 5.0, "label": "جامعه"},
}


def _to_float(value: Any) -> float:
    """Coerce Decimal / None to float for arithmetic in wallet operations."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(value)


def get_or_create_wallet(db: Session, user_id: int) -> EcoWallet:
    """Get an existing wallet or create a new one for the given user.

    Uses a process-wide lock to serialise concurrent wallet creation for the
    same user, preventing double-insert race conditions.
    """
    with _wallet_lock:
        wallet = db.scalars(select(EcoWallet).where(EcoWallet.user_id == user_id)).first()
        if wallet is None:
            wallet = EcoWallet(user_id=user_id, balance=0.0)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        return wallet


def earn(db: Session, user_id: int, category: str, quantity: float = 1.0) -> tuple[float, float]:
    """Credit ECO tokens; returns (amount_earned, new_balance).

    Uses an internal lock to serialise concurrent writes to the same wallet,
    preventing lost-update race conditions.
    """
    if category not in EARNING_RATES:
        raise ValueError(f"unknown earning category: {category}")
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    rate = EARNING_RATES[category]["eco"]
    amount = rate * quantity

    with _wallet_lock:
        wallet = get_or_create_wallet(db, user_id)
        wallet.balance = _to_float(wallet.balance) + amount
        wallet.total_earned = _to_float(wallet.total_earned) + amount
        db.commit()
        db.refresh(wallet)
        return amount, _to_float(wallet.balance)


def redeem(db: Session, user_id: int, amount: float) -> tuple[float, float]:
    """Redeem ECO tokens; raises ValueError when balance is insufficient.

    Uses an internal lock to serialise concurrent writes to the same wallet,
    preventing overdraft race conditions.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    with _wallet_lock:
        wallet = get_or_create_wallet(db, user_id)
        balance = _to_float(wallet.balance)
        if balance < amount:
            raise ValueError(f"insufficient balance ({balance:.2f} < {amount:.2f})")
        wallet.balance = balance - amount
        wallet.total_redeemed = _to_float(wallet.total_redeemed) + amount
        db.commit()
        db.refresh(wallet)
        return amount, _to_float(wallet.balance)


def wallet_state(db: Session, user_id: int) -> dict[str, Any]:
    wallet = get_or_create_wallet(db, user_id)
    return {
        "user_id": user_id,
        "balance": _to_float(wallet.balance),
        "total_earned": _to_float(wallet.total_earned),
        "total_redeemed": _to_float(wallet.total_redeemed),
        "is_active": wallet.is_active,
    }
