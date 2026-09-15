"""Ledger Service - Double-entry accounting for carbon credits and ECO tokens."""

from __future__ import annotations

from datetime import UTC, datetime, date
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import LedgerEntry, FinJournalBatch, FinJournalEntry, FinAccount
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
        description: Optional[str] = None,
        created_by: Optional[str] = None,
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
            raise EcoNojinException("Journal batch must have at least one entry", code="EMPTY_JOURNAL")
        
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
                raise EcoNojinException(f"Invalid entry_type: {entry['entry_type']}", code="INVALID_ENTRY_TYPE")
            
            # Validate asset
            if entry["asset"] not in ("IRR", "ECO", "CARBON_tCO2e", "USD"):
                raise EcoNojinException(f"Invalid asset: {entry['asset']}", code="INVALID_ASSET")
        
        # Validate double-entry: debits must equal credits
        if total_debit != total_credit:
            raise EcoNojinException(
                f"Journal not balanced: debits={total_debit}, credits={total_credit}",
                code="UNBALANCED_JOURNAL"
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
        as_of: Optional[datetime] = None,
    ) -> Decimal:
        """Get account balance for a specific asset."""
        query = select(func.sum(
            FinJournalEntry.amount * (1 if FinJournalEntry.entry_type == "credit" else -1)
        )).where(
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
        account_id: Optional[str] = None,
        asset: Optional[str] = None,
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