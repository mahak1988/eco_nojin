"""Reconciliation service for financial integrity."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    EcoWallet,
    FinJournalBatch,
    FinJournalEntry,
)


class ReconciliationService:
    """Service for financial reconciliation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def reconcile_wallet_ledger(self, as_of: datetime | None = None) -> dict:
        """
        Reconcile wallet balances with ledger entries.

        Returns:
            Dict with reconciliation results
        """
        if not as_of:
            as_of = datetime.now(UTC)

        # Get all wallet balances
        from sqlalchemy import select

        result = await self.db.execute(select(EcoWallet))
        wallets = result.scalars().all()

        discrepancies = []

        for wallet in wallets:
            # Calculate ledger balance
            ledger_balance = await self._get_ledger_balance(wallet.user_id, "ECO")

            if wallet.balance != ledger_balance:
                discrepancies.append(
                    {
                        "user_id": wallet.user_id,
                        "wallet_balance": float(wallet.balance),
                        "ledger_balance": float(ledger_balance),
                        "difference": float(wallet.balance - ledger_balance),
                    }
                )

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_wallets": len(wallets),
            "discrepancies_count": len(discrepancies),
            "discrepancies": discrepancies,
            "overall_ok": len(discrepancies) == 0,
        }

    async def _get_ledger_balance(self, user_id: str, asset: str) -> Decimal:
        """Calculate ledger balance for user/asset from REWARD_LIABILITY account.

        The wallet balance represents ECO tokens owned by the user, which corresponds
        to the platform's REWARD_LIABILITY account (credits = platform owes user).
        """
        from sqlalchemy import case

        from database.models import FinAccount

        result = await self.db.execute(
            select(
                func.sum(
                    FinJournalEntry.amount
                    * case((FinJournalEntry.entry_type == "credit", 1), else_=-1)
                )
            )
            .select_from(FinJournalEntry)
            .join(FinJournalBatch, FinJournalEntry.batch_id == FinJournalBatch.id)
            .join(FinAccount, FinJournalEntry.account_id == FinAccount.id)
            .where(
                FinJournalBatch.created_by == user_id,
                FinAccount.code == "REWARD_LIABILITY",
                FinJournalEntry.asset == asset,
            )
        )
        return result.scalar() or Decimal("0")

    async def reconcile_orders_payments(self) -> dict:
        """Reconcile orders with payments."""
        # TODO: Implement when FinOrder and FinPayment models are available
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_orders_checked": 0,
            "discrepancies_count": 0,
            "discrepancies": [],
            "note": "Skipped - FinOrder and FinPayment models not yet implemented",
        }

    async def reconcile_inventory(self) -> dict:
        """Reconcile inventory balances with stock movements."""
        # TODO: Implement when InvInventoryBalance and InvStockMovement models are available
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "total_balances_checked": 0,
            "discrepancies_count": 0,
            "discrepancies": [],
            "note": "Skipped - InvInventoryBalance and InvStockMovement models not yet implemented",
        }

    async def run_full_reconciliation(self) -> dict:
        """Run all reconciliation checks."""
        wallet_result = await self.reconcile_wallet_ledger()
        orders_result = await self.reconcile_orders_payments()
        inventory_result = await self.reconcile_inventory()

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "checks": {
                "wallet_ledger": wallet_result,
                "orders_payments": orders_result,
                "inventory": inventory_result,
            },
            "overall_ok": (
                wallet_result.get("overall_ok", False)
                and orders_result.get("discrepancies_count", 0) == 0
                and inventory_result.get("discrepancies_count", 0) == 0
            ),
        }
