"""Tests for services.ledger.service — single-entry ledger and escrow state machine."""

from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.ledger.service import (
    ALLOWED_ASSETS,
    DEFAULT_ASSET,
    VALID_ENTRY_TYPES,
    EntryCreate,
    EscrowService,
    EscrowState,
    SingleEntryLedgerService,
)


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def ledger(db_session):
    return SingleEntryLedgerService(session=db_session)


@pytest_asyncio.fixture
async def escrow(db_session):
    return EscrowService(session=db_session)


class TestSingleEntryLedgerServiceValidation:
    def test_allowed_assets_contains_irr(self):
        assert DEFAULT_ASSET in ALLOWED_ASSETS
        assert "IRR" in ALLOWED_ASSETS

    def test_valid_entry_types(self):
        assert "debit" in VALID_ENTRY_TYPES
        assert "credit" in VALID_ENTRY_TYPES


class TestPostEntry:
    @pytest.mark.asyncio
    async def test_post_credit_entry(self, ledger):
        entry = EntryCreate(
            account_id="acct-1",
            entry_type="credit",
            amount=Decimal("100.00"),
            asset="IRR",
            description="initial credit",
        )
        record = await ledger.post_entry(entry)
        assert record["id"] is not None
        assert Decimal(record["amount"]) == Decimal("100.00")
        assert record["entry_type"] == "credit"
        assert record["asset"] == "IRR"

    @pytest.mark.asyncio
    async def test_post_debit_entry(self, ledger):
        entry = EntryCreate(
            account_id="acct-1",
            entry_type="debit",
            amount=Decimal("50.00"),
            asset="IRR",
        )
        record = await ledger.post_entry(entry)
        assert record["entry_type"] == "debit"

    @pytest.mark.asyncio
    async def test_post_entry_invalid_type_raises(self, ledger):
        entry = EntryCreate(
            account_id="acct-1",
            entry_type="invalid",
            amount=Decimal("10.00"),
        )
        with pytest.raises(ValueError, match="entry_type must be one of"):
            await ledger.post_entry(entry)

    @pytest.mark.asyncio
    async def test_post_entry_nonpositive_amount_raises(self, ledger):
        entry = EntryCreate(
            account_id="acct-1",
            entry_type="credit",
            amount=Decimal("0"),
        )
        with pytest.raises(ValueError, match="amount must be positive"):
            await ledger.post_entry(entry)

    @pytest.mark.asyncio
    async def test_post_entry_disallowed_asset_raises(self, ledger):
        entry = EntryCreate(
            account_id="acct-1",
            entry_type="credit",
            amount=Decimal("10.00"),
            asset="XYZ",
        )
        with pytest.raises(ValueError, match="asset must be one of"):
            await ledger.post_entry(entry)

    @pytest.mark.asyncio
    async def test_post_entry_missing_account_raises(self, ledger):
        entry = EntryCreate(
            account_id="",
            entry_type="credit",
            amount=Decimal("10.00"),
        )
        with pytest.raises(ValueError, match="account_id is required"):
            await ledger.post_entry(entry)


class TestGetBalance:
    @pytest.mark.asyncio
    async def test_balance_empty_account_is_zero(self, ledger):
        balance = await ledger.get_balance("acct-empty")
        assert balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_balance_credit_positive_debit_negative(self, ledger):
        await ledger.post_entry(
            EntryCreate(account_id="acct-1", entry_type="credit", amount=Decimal("100.00"))
        )
        await ledger.post_entry(
            EntryCreate(account_id="acct-1", entry_type="debit", amount=Decimal("30.00"))
        )
        balance = await ledger.get_balance("acct-1")
        assert balance == Decimal("70.00")

    @pytest.mark.asyncio
    async def test_balance_is_asset_scoped(self, ledger):
        await ledger.post_entry(
            EntryCreate(
                account_id="acct-1",
                entry_type="credit",
                amount=Decimal("100.00"),
                asset="IRR",
            )
        )
        await ledger.post_entry(
            EntryCreate(
                account_id="acct-1",
                entry_type="credit",
                amount=Decimal("50.00"),
                asset="ECO",
            )
        )
        assert await ledger.get_balance("acct-1", asset="IRR") == Decimal("100.00")
        assert await ledger.get_balance("acct-1", asset="ECO") == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, ledger):
        assert await ledger.health() == "ok"

    @pytest.mark.asyncio
    async def test_verify_chain_raises(self, ledger):
        with pytest.raises(NotImplementedError):
            await ledger.verify_chain()


class TestEscrowService:
    @pytest.mark.asyncio
    async def test_escrow_create_and_lock(self, escrow):
        record = await escrow.create(
            order_id="order-1",
            buyer_id="buyer-1",
            seller_id="seller-1",
            amount=Decimal("250000"),
        )
        assert record.state == EscrowState.CREATED.value
        assert record.amount == Decimal("250000")

        locked = await escrow.lock(order_id="order-1")
        assert locked.state == EscrowState.LOCKED.value
        assert locked.dispute_window_deadline is not None

    @pytest.mark.asyncio
    async def test_escrow_release_after_lock(self, escrow):
        await escrow.create(
            order_id="order-2",
            buyer_id="buyer-2",
            seller_id="seller-2",
            amount=Decimal("100000"),
        )
        await escrow.lock(order_id="order-2")
        released = await escrow.release(order_id="order-2")
        assert released.state == EscrowState.RELEASED.value

    @pytest.mark.asyncio
    async def test_escrow_reverse_after_lock(self, escrow):
        await escrow.create(
            order_id="order-3",
            buyer_id="buyer-3",
            seller_id="seller-3",
            amount=Decimal("75000"),
        )
        await escrow.lock(order_id="order-3")
        reversed_ = await escrow.reverse(order_id="order-3")
        assert reversed_.state == EscrowState.REVERSED.value

    @pytest.mark.asyncio
    async def test_escrow_cannot_release_twice(self, escrow):
        await escrow.create(
            order_id="order-4",
            buyer_id="buyer-4",
            seller_id="seller-4",
            amount=Decimal("50000"),
        )
        await escrow.lock(order_id="order-4")
        await escrow.release(order_id="order-4")
        with pytest.raises(ValueError, match="cannot release"):
            await escrow.release(order_id="order-4")

    @pytest.mark.asyncio
    async def test_escrow_get_state(self, escrow):
        await escrow.create(
            order_id="order-5",
            buyer_id="buyer-5",
            seller_id="seller-5",
            amount=Decimal("10000"),
        )
        state = await escrow.get_state("order-5")
        assert state is not None
        assert state.state == EscrowState.CREATED.value
