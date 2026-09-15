"""Wallet Service - ECO token wallet with optimistic locking."""

from __future__ import annotations

from datetime import UTC, datetime, date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.hub import hub
from database.models import EcoWallet, FinJournalEntry, FinJournalBatch, FinAccount
from services.api_gateway.exceptions import EcoNojinException
from services.finance.ledger_service import LedgerService


class WalletService:
    """ECO token wallet with atomic operations and audit trail."""
    
    # Earning rates (synced with router)
    EARNING_RATES = {
        "tree_planting": {"eco": Decimal("50.0"), "label": "کاشت درخت"},
        "soil_health": {"eco": Decimal("30.0"), "label": "سلامت خاک"},
        "water_saving": {"eco": Decimal("25.0"), "label": "صرفه‌جویی آب"},
        "carbon_credit": {"eco": Decimal("100.0"), "label": "اعتبار کربن"},
        "education": {"eco": Decimal("10.0"), "label": "آموزش"},
        "community": {"eco": Decimal("5.0"), "label": "جامعه"},
    }
    
    REDEMPTION_RATES = {
        "consultation": {"eco": Decimal("20.0"), "label": "مشاوره متخصص"},
        "satellite_report": {"eco": Decimal("30.0"), "label": "گزارش ماهواره‌ای"},
        "marketplace_discount": {"eco": Decimal("10.0"), "label": "تخفیف بازارچه"},
    }
    
    DAILY_EARN_CAP = Decimal("200.0")
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)
    
    async def _get_or_create_wallet(self, user_id: str):
        """Get or create wallet with optimistic locking."""
        from sqlalchemy import select
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from database.models import EcoWallet
        
        # Try to get existing
        result = await self.db.execute(
            select(EcoWallet).where(EcoWallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        
        if wallet:
            return wallet
        
        # Create new wallet with upsert (PostgreSQL)
        stmt = (
            insert(EcoWallet)
            .values(
                user_id=user_id,
                balance=Decimal("0"),
                total_earned=Decimal("0"),
                total_redeemed=Decimal("0"),
                is_active=True,
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
            .returning(FinWalletAccount)
        )
        
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            # Race condition - fetch existing
            result = await self.db.execute(
                select(EcoWallet).where(EcoWallet.user_id == user_id)
            )
            wallet = result.scalar_one()
        
        return wallet
    
    async def earn(
        self,
        user_id: str,
        category: str,
        quantity: Decimal = Decimal("1"),
        idempotency_key: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> tuple[Decimal, Decimal]:
        """
        Credit ECO tokens to user wallet.
        
        Returns:
            (amount_earned, new_balance)
        """
        if category not in self.EARNING_RATES:
            raise EcoNojinException(f"Unknown earning category: {category}", code="UNKNOWN_CATEGORY")
        
        if quantity <= 0:
            raise EcoNojinException("Quantity must be positive", code="INVALID_QUANTITY")
        
        rate = self.EARNING_RATES[category]["eco"]
        amount = self.EARNING_RATES[category]["eco"] * quantity
        
        # Daily cap check
        today = date.today()
        # TODO: Check daily cap from daily_earnings table
        
        # Get wallet with optimistic locking
        wallet = await self._get_or_create_wallet(user_id)
        
        # Check daily cap (TODO: implement daily_earnings table)
        # For now, skip daily cap check
        
        # Create journal batch for earning
        batch = await self._create_earning_batch(
            user_id=user_id,
            amount=amount,
            category=category,
            reference_id=reference_id,
        )
        
        # Update wallet balance with optimistic locking
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Refresh wallet to get latest version
                from sqlalchemy import select
                result = await self.db.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
                wallet = result.scalar_one()
                
                old_balance = wallet.balance
                wallet.balance += amount
                wallet.total_earned += amount
                
                self.db.add(wallet)
                await self.db.commit()
                await self.db.refresh(wallet)
                
                return amount, wallet.balance
                
            except Exception as e:
                await self.db.rollback()
                if attempt == max_retries - 1:
                    raise EcoNojinException(
                        "Failed to update wallet after retries",
                        code="WALLET_UPDATE_FAILED"
                    )
        
        raise EcoNojinException("Failed to process earning", code="EARN_FAILED")
    
    async def _create_earning_batch(
        self,
        user_id: str,
        amount: Decimal,
        category: str,
        reference_id: Optional[str] = None,
    ):
        """Create journal batch for earning."""
        # Get or create accounts
        eco_asset_account = await self._get_or_create_account("ECO_ASSET", "ECO", "asset")
        reward_liability = await self._get_or_create_account("REWARD_LIABILITY", "ECO", "liability")
        
        entries = [
            {
                "account_id": eco_asset_account.id,
                "entry_type": "debit",
                "asset": "ECO",
                "amount": str(amount),
                "description": f"ECO earned: {category}",
            },
            {
                "account_id": reward_liability.id,
                "entry_type": "credit",
                "asset": "ECO",
                "amount": str(amount),
                "description": f"ECO liability: {category}",
            },
        ]
        
        from uuid import uuid4
        reference_id = reference_id or str(uuid4())
        
        ledger_service = LedgerService(self.db)
        batch = await self.ledger.create_journal_batch(
            reference_type="eco_earning",
            reference_id=reference_id,
            entries=entries,
            description=f"ECO earning: {category}",
        )
        return batch
    
    async def _get_or_create_account(self, code: str, asset: str, type_: str):
        """Get or create a financial account."""
        from sqlalchemy import select
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from database.models import FinAccount
        
        result = await self.db.execute(
            select(FinAccount).where(FinAccount.code == code)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            stmt = (
                insert(FinAccount)
                .values(code=code, name=code, type=type_, asset=asset, currency="ECO" if asset == "ECO" else "IRR")
                .on_conflict_do_nothing(index_elements=["code"])
                .returning(FinAccount)
            )
            result = await self.db.execute(stmt)
            account = result.scalar_one_or_none()
            if not account:
                result = await self.db.execute(
                    select(FinAccount).where(FinAccount.code == code)
                )
                account = result.scalar_one()
        
        return account
    
    async def redeem(
        self,
        user_id: str,
        category: str,
        idempotency_key: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> tuple[Decimal, Decimal]:
        """
        Redeem ECO tokens from user wallet.
        
        Returns:
            (amount_redeemed, new_balance)
        """
        if category not in self.REDEMPTION_RATES:
            raise EcoNojinException(f"Unknown redemption category: {category}", code="UNKNOWN_CATEGORY")
        
        rate = self.REDEMPTION_RATES[category]["eco"]
        amount = rate
        
        wallet = await self._get_or_create_wallet(user_id)
        
        if wallet.balance < amount:
            raise EcoNojinException(
                f"Insufficient balance ({wallet.balance:.2f} < {amount:.2f})",
                code="INSUFFICIENT_BALANCE"
            )
        
        # Create journal batch for redemption
        batch = await self._create_redemption_batch(
            user_id=user_id,
            amount=amount,
            category=category,
            reference_id=reference_id,
        )
        
        # Update wallet balance with optimistic locking
        max_retries = 3
        for attempt in range(3):
            try:
                from sqlalchemy import select
                result = await self.db.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
                wallet = result.scalar_one()
                
                if wallet.balance < amount:
                    raise EcoNojinException(
                        f"Insufficient balance ({wallet.balance:.2f} < {amount:.2f})",
                        code="INSUFFICIENT_BALANCE"
                    )
                
                wallet.balance -= amount
                wallet.total_redeemed += amount
                
                self.db.add(wallet)
                await self.db.commit()
                await self.db.refresh(wallet)
                
                return amount, wallet.balance
                
            except Exception as e:
                await self.db.rollback()
                if attempt == 2:
                    raise EcoNojinException(
                        "Failed to update wallet after retries",
                        code="WALLET_UPDATE_FAILED"
                    )
        
        raise EcoNojinException("Failed to process redemption", code="REDEEM_FAILED")
    
    async def _create_redemption_batch(
        self,
        user_id: str,
        amount: Decimal,
        category: str,
        reference_id: Optional[str] = None,
    ):
        """Create journal batch for redemption."""
        from uuid import uuid4
        
        eco_asset_account = await self._get_or_create_account("ECO_ASSET", "ECO", "asset")
        reward_liability = await self._get_or_create_account("REWARD_LIABILITY", "ECO", "liability")
        
        entries = [
            {
                "account_id": eco_asset_account.id,
                "entry_type": "credit",
                "asset": "ECO",
                "amount": str(amount),
                "description": f"ECO redeemed: {category}",
            },
            {
                "account_id": reward_liability.id,
                "entry_type": "debit",
                "asset": "ECO",
                "amount": str(amount),
                "description": f"ECO liability reduction: {category}",
            },
        ]
        
        from uuid import uuid4
        reference_id = reference_id or str(uuid4())
        
        ledger_service = LedgerService(self.db)
        batch = await self.ledger.create_journal_batch(
            reference_type="eco_redemption",
            reference_id=reference_id or str(uuid4()),
            entries=entries,
            description=f"ECO redemption: {category}",
        )
        return batch
    
    async def get_wallet_state(self, user_id: str) -> dict:
        """Get wallet state for a user."""
        wallet = await self._get_or_create_wallet(user_id)
        return {
            "user_id": user_id,
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
            "total_redeemed": wallet.total_redeemed,
            "is_active": wallet.is_active,
        }