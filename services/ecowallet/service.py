"""
EcoWallet service — DB-backed wallet operations (Phase 8).

Replaces the old in-memory ``_wallets`` dict: balances now persist in the
``eco_wallets`` table (per user, unique).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from database.models import EcoWallet

# earning rates: category -> {eco, label} (kept in sync with the router)
EARNING_RATES: dict[str, dict[str, Any]] = {
    "tree_planting": {"eco": 50.0, "label": "کاشت درخت"},
    "soil_health": {"eco": 30.0, "label": "سلامت خاک"},
    "water_saving": {"eco": 25.0, "label": "صرفه‌جویی آب"},
    "carbon_credit": {"eco": 100.0, "label": "اعتبار کربن"},
    "education": {"eco": 10.0, "label": "آموزش"},
    "community": {"eco": 5.0, "label": "جامعه"},
}


def get_or_create_wallet(db: Session, user_id: int) -> EcoWallet:
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user_id).first()
    if wallet is None:
        wallet = EcoWallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def earn(db: Session, user_id: int, category: str, quantity: float = 1.0) -> tuple[float, float]:
    """Credit ECO tokens; returns (amount_earned, new_balance)."""
    if category not in EARNING_RATES:
        raise ValueError(f"unknown earning category: {category}")
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    rate = EARNING_RATES[category]["eco"]
    amount = rate * quantity
    wallet = get_or_create_wallet(db, user_id)
    wallet.balance += amount
    wallet.total_earned += amount
    db.commit()
    db.refresh(wallet)
    return amount, wallet.balance


def redeem(db: Session, user_id: int, amount: float) -> tuple[float, float]:
    """Redeem ECO tokens; raises ValueError when balance is insufficient."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    wallet = get_or_create_wallet(db, user_id)
    if wallet.balance < amount:
        raise ValueError(f"insufficient balance ({wallet.balance:.2f} < {amount:.2f})")
    wallet.balance -= amount
    wallet.total_redeemed += amount
    db.commit()
    db.refresh(wallet)
    return amount, wallet.balance


def wallet_state(db: Session, user_id: int) -> dict[str, Any]:
    wallet = get_or_create_wallet(db, user_id)
    return {
        "user_id": user_id,
        "balance": wallet.balance,
        "total_earned": wallet.total_earned,
        "total_redeemed": wallet.total_redeemed,
        "is_active": wallet.is_active,
    }
