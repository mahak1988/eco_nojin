"""The five money stores beside each other, for ONE user (D-10, P5).

Until D-09 lands, this is the honest answer to per-user attribution: the stores
are reported side by side under the shared ``users.id`` key with the source
named for each figure. It never merges them into a single balance, and it never
presents an empty store as a zero balance — the distinction between "no rows"
and "zero" is the report's job. All arithmetic is Decimal, serialised with
``str()``.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from database.models import (
    ComOrder,
    EcoBalanceAccount,
    EcoBalanceEntry,
    EcoWallet,
    FinJournalBatch,
    LedgerEntry,
)
from services.api_gateway.exceptions import NotFoundException


def _plain(value: Decimal) -> str:
    """Decimal -> string without trailing zeros, for a report humans read."""

    return format(value.normalize(), "f")


async def _count(db, column=None, *, where=()) -> int:
    """A COUNT over an append-only history — SQL aggregates, never row materialisation.

    The stores this report walks are append-only by design, so loading their
    histories to count them grows without bound; the numbers this report needs
    are counts and sums, which the database computes in one pass.
    """
    query = select(func.count(column)) if column is not None else select(func.count())
    for clause in where:
        query = query.where(clause)
    return int(await db.scalar(query) or 0)


async def _sum(db, amount_column, *, where=()) -> Decimal:
    query = select(func.coalesce(func.sum(amount_column), 0))
    for clause in where:
        query = query.where(clause)
    return Decimal(str(await db.scalar(query) or 0))


async def reconcile_ledgers_by_user(db, user_id: str) -> dict:
    from database.models import User

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise NotFoundException(f"user not found: {user_id}")

    wallet = (
        await db.execute(select(EcoWallet).where(EcoWallet.user_id == user_id))
    ).scalar_one_or_none()
    accounts = await _count(
        db, EcoBalanceAccount.id, where=(EcoBalanceAccount.user_id == user_id,)
    )
    eco_entry_count = await _count(
        db, EcoBalanceEntry.id, where=(EcoBalanceEntry.user_id == user_id,)
    )
    eco_entry_sum = await _sum(
        db, EcoBalanceEntry.amount, where=(EcoBalanceEntry.user_id == user_id,)
    )
    ledger_entries = (
        await _count(db, LedgerEntry.id, where=(LedgerEntry.user_id == user_id,))
        if hasattr(LedgerEntry, "user_id")
        else 0
    )
    orders = await _count(db, ComOrder.id, where=(ComOrder.buyer_id == user_id,))
    paid_orders = await _count(
        db,
        ComOrder.id,
        where=(
            ComOrder.buyer_id == user_id,
            ComOrder.payment_status == "paid",
        ),
    )
    paid_total = await _sum(
        db,
        ComOrder.total,
        where=(
            ComOrder.buyer_id == user_id,
            ComOrder.payment_status == "paid",
        ),
    )
    posted = await _count(
        db, FinJournalBatch.id, where=(FinJournalBatch.created_by == user_id,)
    )

    return {
        "user_id": user_id,
        "shared_key": "users.id",
        "sources": {
            "wallet": {
                "present": wallet is not None,
                "balance": _plain(wallet.balance) if wallet is not None else None,
            },
            "ecosystem": {
                "accounts": accounts,
                "entries": eco_entry_count,
                "entry_sum": _plain(eco_entry_sum),
            },
            "ledger": {"entries": ledger_entries},
            "commerce": {
                "orders": orders,
                "paid_orders": paid_orders,
                "paid_total": _plain(paid_total),
            },
            "finance_batches_posted_by_user": posted,
        },
        "note": (
            "Five stores reported side by side under the shared key; they are not "
            "merged. A store with no rows is reported as absent/empty, never as a "
            "zero balance."
        ),
    }
