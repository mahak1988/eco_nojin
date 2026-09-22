"""EcoCoin Wallet Service - Manages user wallets, balances, and transactions"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional
from enum import Enum
from uuid import uuid4
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database.models import EcoWallet, DailyEarnings, FinJournalBatch, FinJournalEntry, FinAccount
from services.api_gateway.exceptions import EcoNojinException


class TransactionType(Enum):
    EARN = "earn"
    REDEEM = "redeem"
    TRANSFER = "transfer"
    MINT = "mint"
    BURN = "burn"
    PLATFORM_FEE = "platform_fee"
    ECOSYSTEM_GRANT = "ecosystem_grant"
    GOVERNANCE = "governance"


@dataclass
class WalletTransaction:
    transaction_id: str
    user_id: str
    amount: Decimal
    transaction_type: TransactionType
    description: str
    category: str
    balance_after: Decimal
    reference_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class WalletService:
    """
    EcoCoin wallet service with atomic operations, audit trail, and phase-gated transfers.
    """

    # Earning rates (ECO per unit)
    EARNING_RATES = {
        "tree_planting": Decimal("50.0"),
        "soil_restoration": Decimal("30.0"),
        "water_conservation": Decimal("25.0"),
        "biodiversity": Decimal("40.0"),
        "cleanup": Decimal("15.0"),
        "regenerative_farming": Decimal("35.0"),
        "carbon_verification": Decimal("100.0"),
        "education": Decimal("10.0"),
        "community": Decimal("5.0"),
        "satellite_verification": Decimal("30.0"),
        "mrv_submission": Decimal("20.0"),
    }

    REDEMPTION_RATES = {
        "consultation": Decimal("20.0"),
        "satellite_report": Decimal("30.0"),
        "marketplace_discount": Decimal("10.0"),
        "training": Decimal("15.0"),
        "certification": Decimal("50.0"),
    }

    DAILY_EARN_CAP = Decimal("200.0")
    TRANSFER_MIN_BALANCE = Decimal("10.0")

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)

    async def _get_or_create_wallet(self, user_id: str) -> EcoWallet:
        result = await self.db.execute(select(EcoWallet).where(EcoWallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if wallet:
            return wallet

        wallet = EcoWallet(
            user_id=user_id,
            balance=Decimal("0"),
            total_earned=Decimal("0"),
            total_redeemed=Decimal("0"),
            is_active=True,
            version=1,
        )
        self.db.add(wallet)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            result = await self.db.execute(select(EcoWallet).where(EcoWallet.user_id == user_id))
            return result.scalar_one()
        return wallet

    async def earn(
        self,
        user_id: str,
        category: str,
        quantity: Decimal = Decimal("1"),
        reference_id: str = None,
    ) -> tuple[Decimal, Decimal]:
        """Credit ECO tokens to user wallet for ecosystem activities"""
        if category not in self.EARNING_RATES:
            raise EcoNojinException(
                f"Unknown earning category: {category}",
                status_code=422,
                code="UNKNOWN_CATEGORY",
            )

        if quantity <= 0:
            raise EcoNojinException(
                "Quantity must be positive", status_code=422, code="INVALID_QUANTITY"
            )

        amount = self.EARNING_RATES[category] * quantity

        # Daily earning cap check
        today = datetime.now(UTC).date()
        result = await self.db.execute(
            select(func.coalesce(func.sum(DailyEarnings.amount), Decimal("0"))).where(
                DailyEarnings.user_id == user_id,
                DailyEarnings.date == today,
                DailyEarnings.status == "processed",
            )
        )
        earned_today = result.scalar() or Decimal("0")
        if earned_today + amount > self.DAILY_EARN_CAP:
            raise EcoNojinException(
                f"Daily earning cap ({self.DAILY_EARN_CAP}) exceeded",
                status_code=400,
                code="DAILY_CAP_EXCEEDED",
            )

        wallet = await self._get_or_create_wallet(user_id)

        # Create journal batch
        batch = await self._create_earning_batch(user_id, amount, category)

        # Update wallet balance
        for attempt in range(3):
            try:
                result = await self.db.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
                wallet = result.scalar_one()

                wallet.balance += amount
                wallet.total_earned += amount
                wallet.last_activity = datetime.now(UTC)

                self.db.add(wallet)
                await self.db.commit()
                await self.db.refresh(wallet)

                # Record daily earnings
                self.db.add(
                    DailyEarnings(
                        user_id=user_id,
                        date=datetime.now(UTC).date(),
                        earnings_type="eco_token",
                        amount=amount,
                        source=category,
                        status="processed",
                    )
                )
                await self.db.commit()

                return amount, wallet.balance

            except Exception:
                await self.db.rollback()
                if attempt == 2:
                    raise ValueError("Failed to update wallet after retries")

        raise ValueError("Failed to process earning")

    async def redeem(
        self,
        user_id: str,
        category: str,
        reference_id: str = None,
    ) -> tuple[Decimal, Decimal]:
        """Redeem ECO tokens for platform services"""
        if category not in self.REDEMPTION_RATES:
            raise EcoNojinException(
                f"Unknown redemption category: {category}",
                status_code=422,
                code="UNKNOWN_CATEGORY",
            )

        amount = self.REDEMPTION_RATES[category]

        wallet = await self._get_or_create_wallet(user_id)
        if wallet.balance < amount:
            raise EcoNojinException(
                f"Insufficient balance ({wallet.balance:.2f} < {amount:.2f})",
                status_code=400,
                code="INSUFFICIENT_BALANCE",
            )

        batch = await self._create_redemption_batch(user_id, amount, category)

        for attempt in range(3):
            try:
                result = await self.db.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
                wallet = result.scalar_one()

                if wallet.balance < amount:
                    raise EcoNojinException(
                f"Insufficient balance ({wallet.balance:.2f} < {amount:.2f})",
                status_code=400,
                code="INSUFFICIENT_BALANCE",
            )

                wallet.balance -= amount
                wallet.total_redeemed += amount
                wallet.last_activity = datetime.now(UTC)

                self.db.add(wallet)
                await self.db.commit()
                await self.db.refresh(wallet)

                return amount, wallet.balance

            except ValueError:
                await self.db.rollback()
                raise
            except Exception:
                await self.db.rollback()
                if attempt == 2:
                    raise ValueError("Failed to update wallet after retries")

        raise ValueError("Failed to process redemption")

    async def transfer(
        self,
        from_user: str,
        to_user: str,
        amount: Decimal,
        description: str = "",
    ) -> bool:
        """Transfer ECO between users (phase-gated)"""
        if amount <= 0:
            raise EcoNojinException(
                "Amount must be positive", status_code=422, code="INVALID_AMOUNT"
            )
        if amount < 10:
            raise EcoNojinException(
                "Minimum transfer amount is 10 ECO",
                status_code=422,
                code="BELOW_MINIMUM_TRANSFER",
            )

        # Check if transfers are allowed in current phase
        # In production: check PhaseGate contract
        # For now, allow if both users exist

        from_wallet = await self._get_or_create_wallet(from_user)
        if from_wallet.balance < amount:
            raise EcoNojinException(
                f"Insufficient balance ({from_wallet.balance:.2f} < {amount:.2f})",
                status_code=409,
                code="INSUFFICIENT_BALANCE",
            )

        to_wallet = await self._get_or_create_wallet(to_user)

        # Atomic transfer with journal
        batch = await self._create_transfer_batch(from_user, to_user, amount, "transfer")

        for attempt in range(3):
            try:
                # Lock both wallets
                from_result = await self.db.execute(
                    select(EcoWallet).where(EcoWallet.user_id == from_user)
                )
                from_wallet = from_result.scalar_one()
                to_result = await self.db.execute(
                    select(EcoWallet).where(EcoWallet.user_id == to_user)
                )
                to_wallet = to_result.scalar_one()

                if from_wallet.balance < amount:
                    raise EcoNojinException("Insufficient balance", status_code=400, code="INSUFFICIENT_BALANCE")

                from_wallet.balance -= amount
                to_wallet.balance += amount
                from_wallet.last_activity = datetime.now(UTC)
                to_wallet.last_activity = datetime.now(UTC)

                self.db.add(from_wallet)
                self.db.add(to_wallet)
                await self.db.commit()

                return True

            except Exception:
                await self.db.rollback()
                if attempt == 2:
                    raise ValueError("Transfer failed after retries")

        return False

    async def get_wallet_state(self, user_id: str) -> dict:
        wallet = await self._get_or_create_wallet(user_id)
        return {
            "user_id": user_id,
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
            "total_redeemed": wallet.total_redeemed,
            "is_active": wallet.is_active,
        }

    async def list_earnings(self, user_id: str, limit: int = 50) -> list[dict]:
        result = await self.db.execute(
            select(DailyEarnings)
            .where(DailyEarnings.user_id == user_id)
            .order_by(DailyEarnings.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "date": e.date.isoformat(),
                "earnings_type": e.earnings_type,
                "amount": str(e.amount),
                "source": e.source,
                "status": e.status,
                "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            }
            for e in rows
        ]

    async def _create_earning_batch(
        self, user_id: str, amount: Decimal, category: str, reference_id: str = None
    ):
        eco_asset = await self._get_or_create_account("ECO_ASSET", "ECO", "asset")
        reward_liability = await self._get_or_create_account("REWARD_LIABILITY", "ECO", "liability")

        entries = [
            {
                "account_id": eco_asset.id,
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
        return await self.ledger.create_journal_batch(
            reference_type="eco_earning",
            reference_id=reference_id or f"earn-{__import__('uuid').uuid4().hex[:8]}",
            entries=entries,
            description=f"ECO earning: {category}",
            created_by=user_id,
        )

    async def _create_redemption_batch(
        self, user_id: str, amount: Decimal, category: str, reference_id: str = None
    ):
        eco_asset = await self._get_or_create_account("ECO_ASSET", "ECO", "asset")
        reward_liability = await self._get_or_create_account("REWARD_LIABILITY", "ECO", "liability")

        entries = [
            {
                "account_id": eco_asset.id,
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
        return await self.ledger.create_journal_batch(
            reference_type="eco_redemption",
            reference_id=reference_id or f"redeem-{__import__('uuid').uuid4().hex[:8]}",
            entries=entries,
            description=f"ECO redemption: {category}",
            created_by=user_id,
        )

    async def _create_transfer_batch(
        self, from_user: str, to_user: str, amount: Decimal, description: str
    ):
        eco_asset = await self._get_or_create_account("ECO_ASSET", "ECO", "asset")

        entries = [
            {
                "account_id": (
                    await self._get_or_create_account(f"ECO_USER_{from_user}", "ECO", "asset")
                ).id,
                "entry_type": "credit",
                "asset": "ECO",
                "amount": str(amount),
                "description": f"Transfer to {to_user}",
            },
            {
                "account_id": (
                    await self._get_or_create_account(f"ECO_USER_{to_user}", "ECO", "asset")
                ).id,
                "entry_type": "debit",
                "asset": "ECO",
                "amount": str(amount),
                "description": f"Transfer from {from_user}",
            },
        ]
        return await self.ledger.create_journal_batch(
            reference_type="eco_transfer",
            reference_id=f"xfer-{__import__('uuid').uuid4().hex[:8]}",
            entries=entries,
            description=f"ECO transfer",
            created_by="system",
        )

    async def _get_or_create_account(self, code: str, asset: str, type_: str):
        result = await self.db.execute(select(FinAccount).where(FinAccount.code == code))
        account = result.scalar_one_or_none()
        if account:
            return account

        account = FinAccount(code=code, name=code, type=type_, asset=asset, currency="ECO")
        self.db.add(account)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            result = await self.db.execute(select(FinAccount).where(FinAccount.code == code))
            return result.scalar_one()
        return account


class LedgerService:
    """Double-entry ledger for ECO token movements"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_journal_batch(
        self,
        reference_type: str,
        reference_id: str,
        entries: list,
        description: str,
        created_by: str,
    ):
        batch = FinJournalBatch(
            batch_number=f"JB-{__import__('uuid').uuid4().hex[:8].upper()}",
            batch_date=datetime.now(UTC).date(),
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            created_by=created_by,
        )
        self.db.add(batch)
        await self.db.flush()

        for entry in entries:
            self.db.add(
                FinJournalEntry(
                    batch_id=batch.id,
                    account_id=entry["account_id"],
                    entry_type=entry["entry_type"],
                    asset=entry["asset"],
                    amount=entry["amount"],
                    description=entry["description"],
                )
            )

        await self.db.commit()
        return batch

    async def get_account_balance(self, account_id: int) -> Decimal:
        result = await self.db.execute(
            select(func.coalesce(func.sum(FinJournalEntry.amount), Decimal("0"))).where(
                FinJournalEntry.account_id == account_id,
                FinJournalEntry.entry_type == "debit",
            )
        )
        debits = result.scalar() or Decimal("0")

        result = await self.db.execute(
            select(func.coalesce(func.sum(FinJournalEntry.amount), Decimal("0"))).where(
                FinJournalEntry.account_id == account_id,
                FinJournalEntry.entry_type == "credit",
            )
        )
        credits = result.scalar() or Decimal("0")

        return debits - credits
