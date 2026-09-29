"""
EcoWallet service — DB-backed wallet operations (Phase 8).

Replaces the old in-memory ``_wallets`` dict: balances now persist in the
``ecowallet`` table (per user, unique).

Phase 4 consolidation (S-MONEY):

* The earning-rate table moved to ``services/finance/earning_rates.py``,
  which is shared with ``services/finance/wallet_service.py``. The two tables
  held the same values under different names (``soil_health`` vs
  ``soil_restoration`` and two more), so an event emitted under one name was
  invisible to a system keyed on the other. Legacy names still resolve.
* Arithmetic is ``Decimal`` throughout. The wallet column is
  ``Numeric(19, 4)`` but the code coerced to ``float``, so every write
  round-tripped a numeric column through binary floating point.
"""

from __future__ import annotations

import threading
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import EcoWallet
from services.finance.earning_rates import EARNING_RATES, resolve_category

#: Process-wide lock. Note the limit honestly: this serialises writes only
#: within one process. It is not a cross-replica guarantee, and the read-
#: modify-write below still has no row lock.
_wallet_lock = threading.RLock()

ZERO = Decimal("0")


def _to_decimal(value: Any) -> Decimal:
    """Coerce a value coming back from a ``Numeric`` column to ``Decimal``."""
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _legacy_rates_view() -> dict[str, dict[str, Any]]:
    """Rate table in the shape the public router exposes.

    The router reads ``EARNING_RATES[cat]["eco"]``, so it cannot consume the
    flat canonical table directly. Kept as a view over it, not a second copy.
    """
    from services.finance.earning_rates import LEGACY_CATEGORY_ALIASES

    view: dict[str, dict[str, Any]] = {}
    for category, rate in EARNING_RATES.items():
        view[category] = {"eco": rate, "label": category}
    for legacy, canonical in LEGACY_CATEGORY_ALIASES.items():
        view[legacy] = {"eco": EARNING_RATES[canonical], "label": canonical}
    return view


#: Kept for import compatibility. This is a *view* of the canonical table,
#: not an independent copy.
LEGACY_EARNING_RATES = _legacy_rates_view()


def get_or_create_wallet(db: Session, user_id: int) -> EcoWallet:
    """Get an existing wallet or create a new one for the given user.

    Serialises concurrent wallet creation for the same user within this
    process. That is not a cross-replica guarantee — see ``_wallet_lock``.
    """
    with _wallet_lock:
        wallet = db.scalars(select(EcoWallet).where(EcoWallet.user_id == user_id)).first()
        if wallet is None:
            wallet = EcoWallet(user_id=user_id, balance=ZERO)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        return wallet


def earn(
    db: Session, user_id: int, category: str, quantity: float = 1.0
) -> tuple[Decimal, Decimal]:
    """Credit ECO tokens; returns ``(amount_earned, new_balance)``."""
    canonical = resolve_category(category)
    quantity_d = Decimal(str(quantity))
    if quantity_d <= 0:
        raise ValueError("quantity must be positive")

    amount = EARNING_RATES[canonical] * quantity_d

    with _wallet_lock:
        wallet = get_or_create_wallet(db, user_id)
        wallet.balance = _to_decimal(wallet.balance) + amount
        wallet.total_earned = _to_decimal(wallet.total_earned) + amount
        db.commit()
        db.refresh(wallet)
        return amount, _to_decimal(wallet.balance)


def redeem(db: Session, user_id: int, amount: float) -> tuple[Decimal, Decimal]:
    """Redeem ECO tokens; raises ``ValueError`` when the balance is short."""
    amount_d = Decimal(str(amount))
    if amount_d <= 0:
        raise ValueError("amount must be positive")

    with _wallet_lock:
        wallet = get_or_create_wallet(db, user_id)
        balance = _to_decimal(wallet.balance)
        if balance < amount_d:
            raise ValueError(f"insufficient balance ({balance:.2f} < {amount_d:.2f})")
        wallet.balance = balance - amount_d
        wallet.total_redeemed = _to_decimal(wallet.total_redeemed) + amount_d
        db.commit()
        db.refresh(wallet)
        return amount_d, _to_decimal(wallet.balance)


def wallet_state(db: Session, user_id: int) -> dict[str, Any]:
    wallet = get_or_create_wallet(db, user_id)
    return {
        "user_id": user_id,
        "balance": float(_to_decimal(wallet.balance)),
        "total_earned": float(_to_decimal(wallet.total_earned)),
        "total_redeemed": float(_to_decimal(wallet.total_redeemed)),
        "is_active": wallet.is_active,
    }
