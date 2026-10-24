"""Ledger Service - Double-entry accounting for carbon credits and ECO tokens."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import FinAccount, FinJournalBatch, FinJournalEntry
from services.api_gateway.exceptions import EcoNojinException


class LedgerService:
    """Double-entry ledger service with full validation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_journal_batch(
        self,
        reference_type: str,
        reference_id: str,
        entries: list[dict],
        description: str | None = None,
        created_by: str | None = None,
    ):
        """
        Create a balanced journal batch with multiple entries.

        Args:
            reference_type: 'order', 'payment', 'eco_earning', 'carbon_issuance', etc.
            reference_id: UUID of the referenced entity
            entries: List of {account_id, entry_type, asset, amount, description}
            description: Batch description
            created_by: User ID who created the batch

        Returns:
            Created FinJournalBatch

        Raises:
            EcoNojinException: If batch is not balanced
        """
        # Validate entries
        if not entries:
            raise EcoNojinException(
                "Journal batch must have at least one entry", code="EMPTY_JOURNAL"
            )

        # Calculate totals
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for entry in entries:
            amount = Decimal(str(entry["amount"]))
            if amount <= 0:
                raise EcoNojinException(f"Amount must be positive: {amount}", code="INVALID_AMOUNT")

            if entry["entry_type"] == "debit":
                total_debit += amount
            elif entry["entry_type"] == "credit":
                total_credit += amount
            else:
                raise EcoNojinException(
                    f"Invalid entry_type: {entry['entry_type']}", code="INVALID_ENTRY_TYPE"
                )

            # Validate asset
            if entry["asset"] not in ("IRR", "ECO", "CARBON_tCO2e", "USD"):
                raise EcoNojinException(f"Invalid asset: {entry['asset']}", code="INVALID_ASSET")

        # Validate double-entry: debits must equal credits
        if total_debit != total_credit:
            raise EcoNojinException(
                f"Journal not balanced: debits={total_debit}, credits={total_credit}",
                code="UNBALANCED_JOURNAL",
            )

        # Create batch
        batch = FinJournalBatch(
            batch_number=f"JB-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}",
            batch_date=date.today(),
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            created_by=created_by,
        )
        self.db.add(batch)
        await self.db.flush()

        # Create entries
        for entry in entries:
            amount = Decimal(str(entry["amount"]))
            entry_obj = FinJournalEntry(
                batch_id=batch.id,
                account_id=entry["account_id"],
                entry_type=entry["entry_type"],
                asset=entry["asset"],
                amount=Decimal(str(entry["amount"])),
                description=entry.get("description"),
            )
            self.db.add(entry_obj)

        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def get_account_balance(
        self,
        account_id: str,
        asset: str = "ECO",
        as_of: datetime | None = None,
    ) -> Decimal:
        """Get account balance for a specific asset.

        Sign convention (unchanged, now computed in SQL): ``credit`` is positive
        and ``debit`` is negative. The previous implementation multiplied by a
        Python-level ``1 if <SQL expression> else -1`` which always evaluated to
        ``1`` and silently returned debit+credit for every account.
        """
        signed_amount = case(
            (FinJournalEntry.entry_type == "credit", FinJournalEntry.amount),
            else_=-FinJournalEntry.amount,
        )
        query = select(func.sum(signed_amount)).where(
            FinJournalEntry.account_id == account_id,
            FinJournalEntry.asset == asset,
        )

        if as_of:
            query = query.where(FinJournalEntry.created_at <= as_of)

        result = await self.db.execute(query)
        balance = result.scalar() or Decimal("0")
        return balance

    async def list_entries(
        self,
        account_id: str | None = None,
        asset: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """List ledger entries with optional filters."""
        query = select(FinJournalEntry).order_by(FinJournalEntry.created_at.desc())

        if account_id:
            query = query.where(FinJournalEntry.account_id == account_id)
        if asset:
            query = query.where(FinJournalEntry.asset == asset)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def trial_balance(
        self,
        as_of: date | None = None,
        asset: str | None = None,
    ) -> dict:
        """تراز آزمایشی حسابداری (ترازنامه آزمایشی حساب‌ها).

        Audited columns: فقط اسناد posted، گروه‌بندی بر اساس (حساب، دارایی).
        هر کل شامل مبلغ بدهکار/بستانکار و پرچم صریح ``balanced`` است؛
        عدم توازن گزارش می‌شود و هرگز پنهان نمی‌شود.

        Args:
            as_of: Optional as-of date (cutoff) for the report.
            asset: Optional asset filter.

        Returns:
            ``{"rows": [...], "totals": [...]}``
        """
        query = (
            select(
                FinJournalEntry.account_id,
                FinJournalEntry.asset,
                func.sum(
                    case(
                        (FinJournalEntry.entry_type == "debit", FinJournalEntry.amount),
                        else_=Decimal("0"),
                    )
                ).label("debit"),
                func.sum(
                    case(
                        (FinJournalEntry.entry_type == "credit", FinJournalEntry.amount),
                        else_=Decimal("0"),
                    )
                ).label("credit"),
            )
            .join(FinJournalBatch, FinJournalEntry.batch_id == FinJournalBatch.id)
            .where(FinJournalBatch.is_posted.is_(True))
            .group_by(FinJournalEntry.account_id, FinJournalEntry.asset)
            .order_by(FinJournalEntry.account_id, FinJournalEntry.asset)
        )
        if as_of is not None:
            query = query.where(FinJournalBatch.batch_date <= as_of)
        if asset is not None:
            query = query.where(FinJournalEntry.asset == asset)

        result = await self.db.execute(query)
        quant = Decimal("0.0001")
        rows = []
        for row in result:
            signed = (row.debit - row.credit).quantize(quant)
            rows.append(
                {
                    "account_id": row.account_id,
                    "asset": row.asset,
                    "debit_balance": str(signed if signed > 0 else Decimal("0").quantize(quant)),
                    "credit_balance": str(-signed if signed < 0 else Decimal("0").quantize(quant)),
                    "total_debits": str(row.debit),
                    "total_credits": str(row.credit),
                }
            )
        totals: dict[str, dict] = {}
        for row in rows:
            acc = totals.setdefault(
                row["asset"], {"asset": row["asset"], "debit": Decimal("0"), "credit": Decimal("0")}
            )
            acc["debit"] += Decimal(row["total_debits"])
            acc["credit"] += Decimal(row["total_credits"])
        total_list = [
            {
                "asset": asset_name,
                "debit": str(values["debit"].quantize(Decimal("0.0001"))),
                "credit": str(values["credit"].quantize(Decimal("0.0001"))),
                "balanced": values["debit"] == values["credit"],
            }
            for asset_name, values in totals.items()
        ]
        return {"rows": rows, "totals": total_list}

    async def profit_and_loss(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        asset: str | None = None,
    ) -> dict:
        """گزارش سود و زیان (درآمد و هزینه) بر پایه اسناد posted.

        Audited columns: فقط اسناد posted؛ بازه تاریخ روی ``batch_date`` اعمال
        می‌شود. مانده طبیعی درآمد = بستانکار − بدهکار و مانده طبیعی هزینه =
        بدهکار − بستانکار. حساب‌های ترازنامه‌ای (asset/liability/equity) در این
        گزارش نمی‌آیند و حساب‌های نامشخص در ``unclassified`` گزارش می‌شوند تا
        هرگز پنهان نشوند.

        Returns:
            ``{"income": [...], "expense": [...], "unclassified": [...],
            "totals": [{"asset", "income", "expense", "net", "profitable"}]}``
        """
        query = (
            select(
                FinJournalEntry.account_id,
                FinJournalEntry.asset,
                func.sum(
                    case(
                        (FinJournalEntry.entry_type == "debit", FinJournalEntry.amount),
                        else_=Decimal("0"),
                    )
                ).label("debit"),
                func.sum(
                    case(
                        (FinJournalEntry.entry_type == "credit", FinJournalEntry.amount),
                        else_=Decimal("0"),
                    )
                ).label("credit"),
            )
            .join(FinJournalBatch, FinJournalEntry.batch_id == FinJournalBatch.id)
            .where(FinJournalBatch.is_posted.is_(True))
            .group_by(FinJournalEntry.account_id, FinJournalEntry.asset)
            .order_by(FinJournalEntry.account_id, FinJournalEntry.asset)
        )
        if from_date is not None:
            query = query.where(FinJournalBatch.batch_date >= from_date)
        if to_date is not None:
            query = query.where(FinJournalBatch.batch_date <= to_date)
        if asset is not None:
            query = query.where(FinJournalEntry.asset == asset)

        result = await self.db.execute(query)
        aggregated = result.all()

        # Chart of accounts lookup keyed by both numeric id and code because
        # legacy entries reference the account either way.
        accounts_result = await self.db.execute(select(FinAccount))
        accounts: dict[str, FinAccount] = {}
        for account in accounts_result.scalars().all():
            accounts[str(account.id)] = account
            accounts.setdefault(account.code, account)

        quant = Decimal("0.0001")
        income: list[dict] = []
        expense: list[dict] = []
        unclassified: list[dict] = []
        for row in aggregated:
            account = accounts.get(str(row.account_id))
            signed = (row.credit - row.debit).quantize(quant)
            entry = {
                "account_id": row.account_id,
                "account_code": account.code if account else None,
                "account_name": account.name if account else None,
                "asset": row.asset,
                "amount": str(signed if signed > 0 else Decimal("0").quantize(quant)),
            }
            if account is None:
                unclassified.append({**entry, "reason": "account_not_found"})
            elif account.type == "income":
                income.append(entry)
            elif account.type == "expense":
                expense.append(
                    {
                        **entry,
                        "amount": str((-signed) if signed < 0 else Decimal("0").quantize(quant)),
                    }
                )
            # Balance-sheet accounts are intentionally excluded from P&L.

        totals_map: dict[str, dict] = {}
        for row in income:
            bucket = totals_map.setdefault(
                row["asset"],
                {"asset": row["asset"], "income": Decimal("0"), "expense": Decimal("0")},
            )
            bucket["income"] += Decimal(row["amount"])
        for row in expense:
            bucket = totals_map.setdefault(
                row["asset"],
                {"asset": row["asset"], "income": Decimal("0"), "expense": Decimal("0")},
            )
            bucket["expense"] += Decimal(row["amount"])
        totals = []
        for asset_name, values in totals_map.items():
            net = (values["income"] - values["expense"]).quantize(quant)
            totals.append(
                {
                    "asset": asset_name,
                    "income": str(values["income"].quantize(quant)),
                    "expense": str(values["expense"].quantize(quant)),
                    "net": str(net),
                    "profitable": net >= 0,
                }
            )

        return {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "asset": asset,
            "income": income,
            "expense": expense,
            "unclassified": unclassified,
            "totals": totals,
        }

    async def post_journal_batch(self, batch_id: str):
        """Post a draft journal batch (mark as posted)."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(FinJournalBatch).where(FinJournalBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if not batch:
            raise EcoNojinException("Batch not found", code="BATCH_NOT_FOUND")

        if batch.is_posted:
            raise EcoNojinException("Batch already posted", code="ALREADY_POSTED")

        batch.is_posted = True
        batch.posted_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(batch)
        return batch
