"""Tests for finance module — double-entry ledger, wallet, reconciliation."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@qa.econojin-test.com"


@pytest.fixture
async def fresh_wallet_service(db_session):
    from services.finance.wallet_service import WalletService

    return WalletService(db_session)


@pytest.fixture
async def fresh_ledger_service(db_session):
    from services.finance.ledger_service import LedgerService

    return LedgerService(db_session)


@pytest.fixture
async def fresh_stock_service(db_session):
    from services.inventory.service import StockService

    return StockService(db_session)


@pytest.fixture
async def fresh_order_service(db_session):
    from services.commerce.service import OrderService

    return OrderService(db_session)


class TestLedgerService:
    """Tests for double-entry ledger validation."""

    async def test_create_balanced_batch(self, fresh_ledger_service, db_session):
        # Create test accounts
        eco_asset = FinAccount(
            code="ECO_TEST_ASSET", name="ECO Asset", type="asset", asset="ECO", currency="ECO"
        )
        revenue = FinAccount(
            code="ECO_TEST_REV", name="Revenue", type="income", asset="ECO", currency="ECO"
        )
        db_session.add_all([eco_asset, revenue])
        await db_session.commit()
        await db_session.refresh(eco_asset)
        await db_session.refresh(revenue)

        batch = await fresh_ledger_service.create_journal_batch(
            reference_type="test",
            reference_id=str(uuid.uuid4()),
            entries=[
                {
                    "account_id": str(eco_asset.id),
                    "entry_type": "debit",
                    "asset": "ECO",
                    "amount": "100",
                },
                {
                    "account_id": str(revenue.id),
                    "entry_type": "credit",
                    "asset": "ECO",
                    "amount": "100",
                },
            ],
        )
        assert batch.is_posted is False

    async def test_unbalanced_batch_raises(self, fresh_ledger_service, db_session):
        from services.api_gateway.exceptions import EcoNojinException

        eco_asset = FinAccount(
            code="ECO_UNBAL", name="ECO Asset", type="asset", asset="ECO", currency="ECO"
        )
        db_session.add(eco_asset)
        await db_session.commit()
        await db_session.refresh(eco_asset)

        with pytest.raises(EcoNojinException) as exc_info:
            await fresh_ledger_service.create_journal_batch(
                reference_type="test",
                reference_id=str(uuid.uuid4()),
                entries=[
                    {
                        "account_id": str(eco_asset.id),
                        "entry_type": "debit",
                        "asset": "ECO",
                        "amount": "100",
                    },
                    {
                        "account_id": str(eco_asset.id),
                        "entry_type": "credit",
                        "asset": "ECO",
                        "amount": "99",
                    },
                ],
            )
        assert exc_info.value.code == "UNBALANCED_JOURNAL"

    async def test_get_account_balance(self, fresh_ledger_service, db_session):

        account = FinAccount(
            code="ECO_BAL_TEST", name="Test", type="asset", asset="ECO", currency="ECO"
        )
        offset = FinAccount(
            code="ECO_BAL_OFFSET", name="Offset", type="income", asset="ECO", currency="ECO"
        )
        db_session.add_all([account, offset])
        await db_session.commit()
        await db_session.refresh(account)
        await db_session.refresh(offset)

        await fresh_ledger_service.create_journal_batch(
            reference_type="test",
            reference_id=str(uuid.uuid4()),
            entries=[
                {
                    "account_id": str(account.id),
                    "entry_type": "credit",
                    "asset": "ECO",
                    "amount": "100",
                },
                {
                    "account_id": str(account.id),
                    "entry_type": "debit",
                    "asset": "ECO",
                    "amount": "30",
                },
                {
                    "account_id": str(offset.id),
                    "entry_type": "debit",
                    "asset": "ECO",
                    "amount": "70",
                },
            ],
        )
        balance = await fresh_ledger_service.get_account_balance(str(account.id), "ECO")
        assert balance == Decimal("70")

    async def test_post_batch(self, fresh_ledger_service, db_session):

        account = FinAccount(
            code="ECO_POST_TEST", name="Test", type="asset", asset="ECO", currency="ECO"
        )
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        batch = await fresh_ledger_service.create_journal_batch(
            reference_type="test",
            reference_id=str(uuid.uuid4()),
            entries=[
                {
                    "account_id": str(account.id),
                    "entry_type": "debit",
                    "asset": "ECO",
                    "amount": "50",
                },
                {
                    "account_id": str(account.id),
                    "entry_type": "credit",
                    "asset": "ECO",
                    "amount": "50",
                },
            ],
        )
        posted = await fresh_ledger_service.post_journal_batch(batch.id)
        assert posted.is_posted is True
        assert posted.posted_at is not None


class TestWalletService:
    """Tests for wallet with idempotency and daily cap."""

    async def test_get_or_create_wallet(self, fresh_wallet_service, db_session):
        wallet = await fresh_wallet_service._get_or_create_wallet("test-user-1")
        assert wallet.user_id == "test-user-1"
        assert wallet.balance == Decimal("0")

    async def test_earn_tokens(self, fresh_wallet_service, db_session):
        amount, balance = await fresh_wallet_service.earn(
            user_id="test-user-2",
            category="tree_planting",
            quantity=Decimal("1"),
        )
        assert amount == Decimal("50.0")
        assert balance == Decimal("50.0")

    async def test_earn_with_quantity(self, fresh_wallet_service, db_session):
        amount, balance = await fresh_wallet_service.earn(
            user_id="test-user-3",
            category="education",
            quantity=Decimal("2"),
        )
        assert amount == Decimal("20.0")
        assert balance == Decimal("20.0")

    async def test_redeem_tokens(self, fresh_wallet_service, db_session):
        await fresh_wallet_service.earn(
            user_id="test-user-4", category="community", quantity=Decimal("10")
        )
        amount, balance = await fresh_wallet_service.redeem(
            user_id="test-user-4", category="consultation"
        )
        assert amount == Decimal("20.0")
        assert balance == Decimal("30.0")

    async def test_redeem_insufficient_balance(self, fresh_wallet_service, db_session):
        with pytest.raises(EcoNojinException) as exc_info:
            await fresh_wallet_service.redeem(user_id="test-user-5", category="consultation")
        assert "INSUFFICIENT_BALANCE" in exc_info.value.code

    async def test_daily_cap_enforced(self, fresh_wallet_service, db_session):
        from services.api_gateway.exceptions import EcoNojinException

        with pytest.raises(EcoNojinException) as exc_info:
            await fresh_wallet_service.earn(
                user_id="test-user-6",
                category="tree_planting",
                quantity=Decimal("10"),  # 10 * 50 = 500 > 200 cap
            )
        assert "DAILY_CAP_EXCEEDED" in exc_info.value.code

    async def test_unknown_category_rejected(self, fresh_wallet_service, db_session):
        with pytest.raises(EcoNojinException) as exc_info:
            await fresh_wallet_service.earn(user_id="test-user-7", category="unknown")
        assert "UNKNOWN_CATEGORY" in exc_info.value.code

    async def test_journal_entries_created_on_earn(self, fresh_wallet_service, db_session):
        await fresh_wallet_service.earn(user_id="test-user-8", category="tree_planting")
        result = await db_session.execute(
            select(FinJournalEntry).where(FinJournalEntry.asset == "ECO")
        )
        entries = result.scalars().all()
        assert len(entries) == 2  # one debit, one credit
        types = {e.entry_type for e in entries}
        assert types == {"debit", "credit"}


class TestReconciliation:
    """Tests for financial reconciliation."""

    async def test_wallet_ledger_reconciliation_ok(self, fresh_wallet_service, db_session):
        await fresh_wallet_service.earn(
            user_id="test-user-9", category="community", quantity=Decimal("1")
        )
        recon = ReconciliationService(db_session)
        result = await recon.reconcile_wallet_ledger()
        assert result["overall_ok"] is True
        assert result["discrepancies_count"] == 0

    async def test_full_reconciliation_returns_all_checks(self, db_session):
        recon = ReconciliationService(db_session)
        result = await recon.run_full_reconciliation()
        assert "checks" in result
        assert "wallet_ledger" in result["checks"]
        assert "orders_payments" in result["checks"]
        assert "inventory" in result["checks"]
        assert "overall_ok" in result


class TestBankTransferProvider:
    """Tests for BankTransferProvider."""

    async def test_provider_name(self, db_session):
        provider = BankTransferProvider(db_session)
        assert provider.provider_name == "bank_transfer"

    async def test_create_payment_intent(self, db_session):
        from services.finance.wallet_service import WalletService

        wallet_service = WalletService(db_session)
        provider = BankTransferProvider(db_session)

        intent = await provider.create_payment_intent(
            amount=Decimal("1000.00"),
            currency="IRR",
            order_id="test-order-1",
            metadata={"buyer_id": "user-1"},
            idempotency_key="bt-test-1",
        )
        assert intent.amount == Decimal("1000.00")
        assert intent.currency == "IRR"
        assert intent.status == "awaiting_transfer"
        assert intent.provider == "bank_transfer"
        assert intent.provider_reference is not None
        assert intent.provider_reference.startswith("BT-")
        assert "bank_account" in intent.metadata
        assert "reference_number" in intent.metadata

    async def test_create_payment_intent_persisted(self, db_session):
        provider = BankTransferProvider(db_session)

        intent = await provider.create_payment_intent(
            amount=Decimal("500.00"),
            currency="IRR",
            order_id="test-order-2",
            metadata={"buyer_id": "user-2"},
            idempotency_key="bt-test-2",
        )

        result = await db_session.execute(
            select(ComPaymentIntent).where(ComPaymentIntent.id == intent.id)
        )
        payment = result.scalar_one_or_none()
        assert payment is not None
        assert payment.status == "awaiting_transfer"
        assert payment.provider == "bank_transfer"
        assert payment.provider_reference is not None

    async def test_verify_transfer_success(self, db_session):
        provider = BankTransferProvider(db_session)

        intent = await provider.create_payment_intent(
            amount=Decimal("1000.00"),
            currency="IRR",
            order_id="test-order-3",
            metadata={"buyer_id": "user-3"},
            idempotency_key="bt-test-3",
        )

        verified = await provider.verify_transfer(
            payment_id=intent.id,
            transferred_amount=Decimal("1000.00"),
            verified_by="admin-1",
            description="Full transfer verified",
        )
        assert verified is not None
        assert verified.status == "succeeded"
        assert verified.confirmed_at is not None

        result = await db_session.execute(
            select(AuditEvent).where(AuditEvent.correlation_id == intent.id)
        )
        audit = result.scalar_one_or_none()
        assert audit is not None
        assert audit.action == "bank_transfer_verify"
        assert audit.actor_id == "admin-1"

    async def test_verify_transfer_partial(self, db_session):
        provider = BankTransferProvider(db_session)

        intent = await provider.create_payment_intent(
            amount=Decimal("1000.00"),
            currency="IRR",
            order_id="test-order-4",
            metadata={"buyer_id": "user-4"},
            idempotency_key="bt-test-4",
        )

        verified = await provider.verify_transfer(
            payment_id=intent.id,
            transferred_amount=Decimal("600.00"),
            verified_by="admin-2",
        )
        assert verified is not None
        assert verified.status == "partial"
        assert "Partial payment" in (verified.failure_reason or "")

    async def test_verify_transfer_negative_amount_raises(self, db_session):
        provider = BankTransferProvider(db_session)

        intent = await provider.create_payment_intent(
            amount=Decimal("1000.00"),
            currency="IRR",
            order_id="test-order-5",
            metadata={"buyer_id": "user-5"},
            idempotency_key="bt-test-5",
        )

        with pytest.raises(EcoNojinException) as exc_info:
            await provider.verify_transfer(
                payment_id=intent.id,
                transferred_amount=Decimal("-100"),
                verified_by="admin-3",
            )
        assert exc_info.value.code == "INVALID_AMOUNT"

    async def test_verify_transfer_already_verified(self, db_session):
        provider = BankTransferProvider(db_session)

        intent = await provider.create_payment_intent(
            amount=Decimal("1000.00"),
            currency="IRR",
            order_id="test-order-6",
            metadata={"buyer_id": "user-6"},
            idempotency_key="bt-test-6",
        )
        await provider.verify_transfer(
            payment_id=intent.id,
            transferred_amount=Decimal("1000.00"),
            verified_by="admin-4",
        )

        with pytest.raises(EcoNojinException) as exc_info:
            await provider.verify_transfer(
                payment_id=intent.id,
                transferred_amount=Decimal("1000.00"),
                verified_by="admin-4",
            )
        assert exc_info.value.code == "ALREADY_VERIFIED"

    async def test_verify_transfer_missing_payment(self, db_session):
        provider = BankTransferProvider(db_session)

        result = await provider.verify_transfer(
            payment_id="nonexistent-payment",
            transferred_amount=Decimal("1000.00"),
            verified_by="admin-5",
        )
        assert result is None


# ---------------------------------------------------------------------------
# Imports needed by tests
# ---------------------------------------------------------------------------

from database.models import AuditEvent, ComPaymentIntent, FinAccount, FinJournalEntry
from services.api_gateway.exceptions import EcoNojinException
from services.finance.payment_provider import BankTransferProvider
from services.finance.reconciliation import ReconciliationService
