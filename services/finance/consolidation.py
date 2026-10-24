"""Read-only consolidation across the five parallel money stores (P2-13).

The platform keeps five independent stores that never read one another, so no
single report describes its real financial position:

1. ``fin_journal_entries`` / ``fin_journal_batches`` — the canonical
   double-entry ledger (``services.finance.ledger_service.LedgerService``).
2. ``ledger_entries`` / ``escrow_records`` — the single-entry ledger
   (``services.ledger.service.SingleEntryLedgerService``).
3. ``marketplace_payments`` / ``marketplace_escrow_entries`` — the marketplace
   escrow ledger (``services.marketplace.models.marketplace_payment``).
4. ``ecocoin_balances`` — the blockchain EcoCoin ledger (raw SQL, no ORM model;
   see ``services.blockchain.service``).
5. ``eco_wallets`` — the ECO wallet layer (``services.finance.wallet_service``
   or ``database.models.EcoWallet``).

This module *adds* a consolidated, read-only position view over all five. It
does not merge, migrate, rewrite or delete any table: every store is queried in
isolation and reported side by side, per asset currency, and a ``gaps`` section
surfaces where the wallet layer and the REWARD_LIABILITY balance of the
canonical ledger disagree.

Each store is a different *representation* of value (double-entry
debit/credit columns, single-entry signed balances, escrow state, wallet
balances, EcoCoin balances), so their totals are reported per asset and never
summed into one number — only the reconciliation logic knows how to net them.

Cross-service imports (``services.ledger`` / ``services.marketplace`` /
``services.blockchain``) are made lazily inside the methods that need them, so
``import services.finance.consolidation`` stays free of the import cycles that
``services.finance.__init__`` (which re-exports ``LedgerService``) and the
standalone ledger app can otherwise create.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import EcoWallet, LedgerEntry
from services.finance.ledger_service import LedgerService
from services.finance.reconciliation import ReconciliationService

#: Ordered, stable list of source keys so the report shape never depends on the
#: data present. Consumers can rely on all five keys always being present.
SOURCE_KEYS: tuple[str, ...] = (
    "fin_double_entry",
    "ledger_single_entry",
    "marketplace_escrow",
    "eco_wallets",
    "ecocoin",
)


def _d(value: Any) -> Decimal:
    """Coerce a DB scalar (Decimal/int/float/str/None) to an exact Decimal.

    Raw ``text()`` queries (the EcoCoin store) come back from SQLite as int or
    float; ``None`` (an empty SUM) becomes zero. Monetary values are emitted as
    ``str`` of an exact ``Decimal``, never as a float.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _is_missing_table(exc: Exception) -> bool:
    """Whether a driver error means "this raw table was never provisioned".

    ``ecocoin_balances`` has no ORM model and no migration: in SQLite tests, and
    on a deployment where the blockchain store was never bootstrapped, the table
    is simply absent. That is an empty store, not a crash — report a zero
    position. Any other driver error (connection loss, permission) re-raises.
    """
    message = str(getattr(exc, "orig", exc)).lower()
    return "no such table" in message or "does not exist" in message


class ConsolidatedPositionService:
    """Read-only consolidated position over the five independent money stores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def position(self, as_of: date | None = None) -> dict:
        """Build the consolidated position as of ``as_of`` (defaults to now).

        Args:
            as_of: Optional cutoff date. Applied to the double-entry trial
                balance (its native ``batch_date`` cutoff); the other stores
                have no comparable point-in-time semantics and report their
                current totals.

        Returns:
            ``{"as_of", "generated_at", "sources", "gaps", "overall"}`` — see the
            per-source methods for the aggregation semantics.
        """
        as_of_iso = as_of.isoformat() if as_of else None
        generated_at = datetime.now(UTC).isoformat()

        # The raw-table EcoCoin query runs last: it is the only read that can
        # find its table absent, and running it after every ORM read (and the
        # reconciliation) keeps that from disturbing the rest of the report.
        gaps = await self._gaps(as_of)
        sources = {
            "fin_double_entry": await self._double_entry(as_of, as_of_iso),
            "ledger_single_entry": await self._single_entry(as_of_iso),
            "marketplace_escrow": await self._marketplace(as_of_iso),
            "eco_wallets": await self._wallets(as_of_iso),
            "ecocoin": await self._ecocoin(as_of_iso),
        }
        return {
            "as_of": as_of_iso,
            "generated_at": generated_at,
            "sources": sources,
            "gaps": gaps,
            "overall": self._overall(sources, as_of_iso, generated_at, gaps),
        }

    # ------------------------------------------------------------------ #
    # Per-source aggregation
    # ------------------------------------------------------------------ #

    async def _double_entry(self, as_of: date | None, as_of_iso: str | None) -> dict:
        """POSTED double-entry balances, per account, grouped by asset.

        Reuses ``LedgerService.trial_balance`` verbatim (posted batches only),
        and rolls each asset's accounts up into gross debit/credit totals.
        """
        report = await LedgerService(self.db).trial_balance(as_of=as_of)
        rows = report["rows"]
        assets: dict[str, dict] = {}
        for row in rows:
            bucket = assets.setdefault(
                row["asset"],
                {"accounts": [], "_debits": Decimal("0"), "_credits": Decimal("0")},
            )
            bucket["accounts"].append(
                {
                    "account_id": row["account_id"],
                    "debit_balance": row["debit_balance"],
                    "credit_balance": row["credit_balance"],
                }
            )
            bucket["_debits"] += Decimal(row["total_debits"])
            bucket["_credits"] += Decimal(row["total_credits"])
        for bucket in assets.values():
            bucket["total_debits"] = str(bucket.pop("_debits"))
            bucket["total_credits"] = str(bucket.pop("_credits"))
        return {
            "name": "Double-entry journal (fin_journal_entries / fin_journal_batches, posted only)",
            "row_count": len(rows),
            "as_of": as_of_iso,
            "assets": assets,
        }

    async def _single_entry(self, as_of_iso: str | None) -> dict:
        """Signed single-entry balances (credit positive, debit negative) per asset."""
        signed = case(
            (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
            else_=-LedgerEntry.amount,
        )
        result = await self.db.execute(
            select(
                LedgerEntry.asset,
                func.coalesce(func.sum(signed), Decimal("0")).label("total"),
                func.count().label("n"),
            ).group_by(LedgerEntry.asset)
        )
        assets: dict[str, dict] = {}
        row_count = 0
        for asset, total, n in result:
            row_count += int(n)
            assets[str(asset)] = {"total": str(_d(total))}
        return {
            "name": "Single-entry ledger (ledger_entries, credit-positive)",
            "row_count": row_count,
            "as_of": as_of_iso,
            "assets": assets,
        }

    async def _marketplace(self, as_of_iso: str | None) -> dict:
        """Marketplace escrow amounts by state (hold/release/refund) per asset."""
        from services.marketplace.models.marketplace_payment import (
            MarketplaceEscrowEntry,
        )

        result = await self.db.execute(
            select(
                MarketplaceEscrowEntry.currency,
                MarketplaceEscrowEntry.entry_type,
                func.coalesce(func.sum(MarketplaceEscrowEntry.amount), Decimal("0")),
                func.count(),
            ).group_by(MarketplaceEscrowEntry.currency, MarketplaceEscrowEntry.entry_type)
        )
        assets: dict[str, dict] = {}
        row_count = 0
        for currency, entry_type, total, n in result:
            row_count += int(n)
            bucket = assets.setdefault(
                str(currency), {"total": Decimal("0"), "by_state": {}}
            )
            amount = _d(total)
            bucket["total"] += amount
            bucket["by_state"][str(entry_type)] = str(amount)
        for bucket in assets.values():
            bucket["total"] = str(bucket["total"])
        return {
            "name": "Marketplace escrow (marketplace_escrow_entries by state)",
            "row_count": row_count,
            "as_of": as_of_iso,
            "assets": assets,
        }

    async def _wallets(self, as_of_iso: str | None) -> dict:
        """Sum of ``eco_wallets.balance`` (plus cumulative earned/redeemed)."""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(EcoWallet.balance), Decimal("0")),
                func.coalesce(func.sum(EcoWallet.total_earned), Decimal("0")),
                func.coalesce(func.sum(EcoWallet.total_redeemed), Decimal("0")),
                func.count(),
            )
        )
        balance, earned, redeemed, count = result.first()
        return {
            "name": "ECO wallets (eco_wallets.balance)",
            "row_count": int(count),
            "as_of": as_of_iso,
            "assets": {
                "ECO": {
                    "total": str(_d(balance)),
                    "total_earned": str(_d(earned)),
                    "total_redeemed": str(_d(redeemed)),
                }
            },
        }

    async def _ecocoin(self, as_of_iso: str | None) -> dict:
        """EcoCoin balances from the raw ``ecocoin_balances`` table via text() SQL.

        The table has no ORM model, so it is queried with ``text()``. A missing
        table is an empty store and reports a zero position rather than raising.
        """
        empty_source: dict = {
            "name": "Blockchain EcoCoin (ecocoin_balances, raw SQL)",
            "row_count": 0,
            "as_of": as_of_iso,
            "assets": {"ECO": {"total": "0", "total_earned": "0", "total_spent": "0"}},
            "available": False,
        }
        query = text(
            "SELECT COALESCE(SUM(balance), 0) AS balance, "
            "COALESCE(SUM(total_earned), 0) AS total_earned, "
            "COALESCE(SUM(total_spent), 0) AS total_spent, "
            "COUNT(*) AS n "
            "FROM ecocoin_balances"
        )
        try:
            result = await self.db.execute(query)
            row = result.first()
        except (OperationalError, ProgrammingError) as exc:
            if not _is_missing_table(exc):
                raise
            return empty_source
        return {
            "name": "Blockchain EcoCoin (ecocoin_balances, raw SQL)",
            "row_count": int(row.n) if row else 0,
            "as_of": as_of_iso,
            "assets": {
                "ECO": {
                    "total": str(_d(row.balance)) if row else "0",
                    "total_earned": str(_d(row.total_earned)) if row else "0",
                    "total_spent": str(_d(row.total_spent)) if row else "0",
                }
            },
            "available": True,
        }

    # ------------------------------------------------------------------ #
    # Gaps + overall roll-up
    # ------------------------------------------------------------------ #

    async def _gaps(self, as_of: date | None) -> dict:
        """Reconciliation gap between wallets and the canonical REWARD_LIABILITY.

        Reuses ``services.finance.reconciliation.ReconciliationService`` read-only
        (that file is not edited here). The other parallel stores are reported
        side by side and are not mutually netted.
        """
        cutoff: datetime | None = None
        if as_of is not None:
            cutoff = datetime(as_of.year, as_of.month, as_of.day, tzinfo=UTC)
        wallet_ledger = await ReconciliationService(self.db).reconcile_wallet_ledger(
            as_of=cutoff
        )
        return {
            "wallet_vs_reward_liability": wallet_ledger,
            "note": (
                "Wallets (eco_wallets) are reconciled against the REWARD_LIABILITY "
                "balance of the canonical double-entry ledger by reusing "
                "services/finance/reconciliation.py. The other parallel stores are "
                "reported side by side and are not netted against each other."
            ),
        }

    def _overall(
        self, sources: dict, as_of_iso: str | None, generated_at: str, gaps: dict
    ) -> dict:
        assets: set[str] = set()
        for source in sources.values():
            assets.update(source["assets"].keys())
        recon = gaps.get("wallet_vs_reward_liability", {})
        return {
            "as_of": as_of_iso,
            "generated_at": generated_at,
            "source_count": len(SOURCE_KEYS),
            "sources": list(SOURCE_KEYS),
            "assets": sorted(assets),
            "non_empty_sources": [
                key for key in SOURCE_KEYS if sources[key]["row_count"] > 0
            ],
            "gaps": {
                "overall_ok": recon.get("overall_ok", True),
                "discrepancies_count": recon.get("discrepancies_count", 0),
            },
            "note": (
                "Parallel stores are reported side by side per asset and are never "
                "summed into one figure: double-entry debits/credits, single-entry "
                "signed balances, marketplace escrow, wallet balances and EcoCoin are "
                "independent representations that reconcile only through the gaps view."
            ),
        }
