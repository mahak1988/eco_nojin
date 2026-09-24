"""Tests for Finance/Wallet Services"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.finance.wallet_service import LedgerService, WalletService


class TestWalletService:
    """Tests for WalletService"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_db):
        return WalletService(mock_db)

    @pytest.mark.asyncio
    async def test_earn_tokens(self, service):
        """Test earning ECO tokens"""
        # Mock database operations
        service._get_or_create_wallet = AsyncMock(
            return_value=MagicMock(
                balance=Decimal("0"),
                total_earned=Decimal("0"),
                last_activity=datetime.now(UTC),
            )
        )
        service._create_earning_batch = AsyncMock()
        service.db.execute = AsyncMock()
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        # Mock daily earnings check
        service.db.execute.return_value.scalar.return_value = Decimal("0")

        amount, _balance = await service.earn("user_123", "tree_planting", Decimal("1"))
        assert amount == Decimal("50.0")

    @pytest.mark.asyncio
    async def test_earn_daily_cap(self, service):
        """Test daily earning cap enforcement"""
        service._get_or_create_wallet = AsyncMock()
        service.db.execute = AsyncMock()
        service.db.execute.return_value.scalar.return_value = Decimal("180")

        with pytest.raises(ValueError, match="Daily earning cap"):
            await service.earn("user_123", "tree_planting", Decimal("1"))

    @pytest.mark.asyncio
    async def test_redeem_tokens(self, service):
        """Test redeeming tokens"""
        service._get_or_create_wallet = AsyncMock(
            return_value=MagicMock(
                balance=Decimal("100"),
                total_redeemed=Decimal("0"),
            )
        )
        service._create_redemption_batch = AsyncMock()
        service.db.execute = AsyncMock()
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()

        amount, _balance = await service.redeem("user_123", "consultation")
        assert amount == Decimal("20.0")

    @pytest.mark.asyncio
    async def test_redeem_insufficient_balance(self, service):
        """Test redeem with insufficient balance"""
        service._get_or_create_wallet = AsyncMock(
            return_value=MagicMock(
                balance=Decimal("10"),
            )
        )

        with pytest.raises(ValueError, match="Insufficient balance"):
            await service.redeem("user_123", "consultation")

    @pytest.mark.asyncio
    async def test_transfer(self, service):
        """Test transferring tokens between users"""
        from_wallet = MagicMock(balance=Decimal("100"), last_activity=datetime.now(UTC))
        to_wallet = MagicMock(balance=Decimal("0"), last_activity=datetime.now(UTC))

        service._get_or_create_wallet = AsyncMock(side_effect=[from_wallet, to_wallet])
        service._create_transfer_batch = AsyncMock()
        service.db.execute = AsyncMock()
        service.db.commit = AsyncMock()

        result = await service.transfer("user_1", "user_2", Decimal("50"))
        assert result is True

    @pytest.mark.asyncio
    async def test_transfer_insufficient(self, service):
        """Test transfer with insufficient balance"""
        from_wallet = MagicMock(balance=Decimal("10"))

        service._get_or_create_wallet = AsyncMock(return_value=from_wallet)

        with pytest.raises(ValueError, match="Insufficient balance"):
            await service.transfer("user_1", "user_2", Decimal("50"))

    @pytest.mark.asyncio
    async def test_get_wallet_state(self, service):
        """Test getting wallet state"""
        service._get_or_create_wallet = AsyncMock(
            return_value=MagicMock(
                balance=Decimal("100"),
                total_earned=Decimal("200"),
                total_redeemed=Decimal("50"),
                is_active=True,
            )
        )

        state = await service.get_wallet_state("user_123")
        assert state["balance"] == Decimal("100")
        assert state["total_earned"] == Decimal("200")

    @pytest.mark.asyncio
    async def test_transfer_minimum_amount(self, service):
        """Test minimum transfer amount"""
        with pytest.raises(ValueError, match="Minimum transfer"):
            await service.transfer("user_1", "user_2", Decimal("5"))


class TestLedgerService:
    """Tests for LedgerService"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return LedgerService(mock_db)

    @pytest.mark.asyncio
    async def test_create_journal_batch(self, service):
        """Test creating journal batch"""
        service.db.add = MagicMock()
        service.db.flush = AsyncMock()
        service.db.commit = AsyncMock()

        entries = [
            {
                "account_id": 1,
                "entry_type": "debit",
                "asset": "ECO",
                "amount": "100",
                "description": "Test",
            },
            {
                "account_id": 2,
                "entry_type": "credit",
                "asset": "ECO",
                "amount": "100",
                "description": "Test",
            },
        ]

        batch = await service.create_journal_batch(
            reference_type="test",
            reference_id="test-123",
            entries=entries,
            description="Test batch",
            created_by="user_123",
        )

        assert batch is not None

    @pytest.mark.asyncio
    async def test_get_account_balance(self, service):
        """Test getting account balance"""
        service.db.execute = AsyncMock()
        service.db.execute.return_value.scalar.side_effect = [Decimal("1000"), Decimal("400")]

        balance = await service.get_account_balance(1)
        assert balance == Decimal("600")
