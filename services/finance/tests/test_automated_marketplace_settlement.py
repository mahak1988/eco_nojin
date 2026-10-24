"""Tests for AutomatedMarketplaceSettlementService — Phase 10+.5."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from database.models import (
    AuditEvent,
    ComOrder,
    ComSettlement,
    FinJournalBatch,
    IntOutboxEvent,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.automated_marketplace_settlement import (
    AutomatedMarketplaceSettlementService,
    SettlementBatch,
)

pytestmark = pytest.mark.asyncio


async def _make_order(
    db_session,
    order_id: str = "ORD-001",
    seller_id: str = "seller-1",
    buyer_id: str = "buyer-1",
    total: Decimal = Decimal("1000.00"),
    currency: str = "IRR",
    status: str = "delivered",
    payment_status: str = "succeeded",
):
    """Insert a ComOrder row directly and commit."""
    order = ComOrder(
        id=order_id,
        order_number=order_id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        status=status,
        payment_status=payment_status,
        currency=currency,
        subtotal=str(total),
        total=str(total),
    )
    db_session.add(order)
    await db_session.commit()
    return order


class TestFeeComputation:
    """Tests for fee computation logic (pure, no DB)."""

    def test_compute_fees_800_200_200(self):
        """800/200/200 bps split on a 1000 IRR order."""
        seller_amount, platform_fee, landscape_fee, developer_fee = (
            AutomatedMarketplaceSettlementService._compute_fees(
                Decimal("1000"), 800, 200
            )
        )
        assert platform_fee == Decimal("80.00000000")
        assert landscape_fee == Decimal("20.00000000")
        assert developer_fee == Decimal("20.00000000")
        assert seller_amount == Decimal("880.00000000")

    def test_compute_fees_balanced(self):
        """Fees + seller_amount == total."""
        total = Decimal("1234.5678")
        seller, platform, landscape, developer = (
            AutomatedMarketplaceSettlementService._compute_fees(total, 800, 200)
        )
        assert seller + platform + landscape + developer == total.quantize(Decimal("0.00000001"))


class TestEligibleOrders:
    """Tests for find_eligible_orders."""

    async def test_finds_delivered_paid_orders(self, db_session):
        """Delivered + paid orders with no settlement are eligible."""
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="ORD-001", status="delivered", payment_status="succeeded")
        await _make_order(db_session, order_id="ORD-002", status="shipped", payment_status="succeeded")
        await _make_order(db_session, order_id="ORD-003", status="draft", payment_status="succeeded")
        await _make_order(db_session, order_id="ORD-004", status="delivered", payment_status="pending")

        eligible = await service.find_eligible_orders(limit=50)
        ids = {o.id for o in eligible}
        assert "ORD-001" in ids
        assert "ORD-002" in ids
        assert "ORD-003" not in ids
        assert "ORD-004" not in ids

    async def test_excludes_already_settled(self, db_session):
        """Orders with an existing ComSettlement are not returned."""
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="ORD-005")

        settlement = ComSettlement(
            id="SETTLE-005",
            order_id="ORD-005",
            seller_id="seller-1",
            amount=Decimal("100"),
            currency="IRR",
            commission_fee=Decimal("10"),
            landscape_fee=Decimal("2"),
            status="posted",
        )
        db_session.add(settlement)
        await db_session.commit()

        eligible = await service.find_eligible_orders(limit=50)
        assert "ORD-005" not in {o.id for o in eligible}


class TestSettleOrder:
    """Tests for settle_order."""

    async def test_settle_simulation_mode(self, db_session, monkeypatch):
        """Settling without CBDC_ENDPOINT_URL operates in simulation mode."""
        monkeypatch.delenv("CBDC_ENDPOINT_URL", raising=False)
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="ORD-SIM", total=Decimal("1000"))

        result = await service.settle_order("ORD-SIM")

        assert result.status == "posted"
        assert result.seller_amount == Decimal("880.00000000")
        assert result.platform_fee == Decimal("80.00000000")
        assert result.landscape_fee == Decimal("20.00000000")
        assert result.cbdc_transaction_id.startswith("SIM-")
        assert result.journal_batch_id is not None

        # Verify settlement row exists
        settlement_result = await db_session.execute(
            select(ComSettlement).where(ComSettlement.order_id == "ORD-SIM")
        )
        settlement = settlement_result.scalar_one()
        assert settlement.status == "posted"
        assert settlement.journal_batch_id == result.journal_batch_id

        # Verify audit event
        audit_result = await db_session.execute(
            select(AuditEvent).where(AuditEvent.resource_id == "ORD-SIM")
        )
        audit = audit_result.scalar_one()
        assert audit.action == "order_settled"

        # Verify journal batch exists
        batch_result = await db_session.execute(
            select(FinJournalBatch).where(FinJournalBatch.id == result.journal_batch_id)
        )
        batch = batch_result.scalar_one()
        assert batch is not None

    async def test_settle_idempotent(self, db_session, monkeypatch):
        """A second settle_order call returns the prior settlement."""
        monkeypatch.delenv("CBDC_ENDPOINT_URL", raising=False)
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="ORD-IDEM", total=Decimal("500"))

        first = await service.settle_order("ORD-IDEM")
        second = await service.settle_order("ORD-IDEM")

        assert second.status == "posted"
        assert second.seller_amount == first.seller_amount
        assert second.platform_fee == first.platform_fee
        assert second.journal_batch_id == first.journal_batch_id

    async def test_settle_order_creates_outbox_event(self, db_session, monkeypatch):
        """Settlement creates an IntOutboxEvent for SSE streaming."""
        monkeypatch.delenv("CBDC_ENDPOINT_URL", raising=False)
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="ORD-SSE", total=Decimal("200"))

        await service.settle_order("ORD-SSE")

        outbox_result = await db_session.execute(
            select(IntOutboxEvent).where(IntOutboxEvent.event_type == "settlement_completed")
        )
        outbox = outbox_result.scalars().all()
        assert len(outbox) == 1
        assert outbox[0].aggregate_id == "SETTLE-ORD-SSE"
        assert outbox[0].payload is not None

    async def test_settle_order_not_found(self, db_session, monkeypatch):
        """Settling a non-existent order raises ORDER_NOT_FOUND."""
        monkeypatch.delenv("CBDC_ENDPOINT_URL", raising=False)
        service = AutomatedMarketplaceSettlementService(db_session)
        with pytest.raises(EcoNojinException) as exc_info:
            await service.settle_order("NON-EXISTENT")
        assert exc_info.value.code == "ORDER_NOT_FOUND"

    async def test_settle_with_cbdc_endpoint(self, db_session, monkeypatch):
        """When CBDC_ENDPOINT_URL is set, the CBDC transfer runs normally."""
        monkeypatch.setenv("CBDC_ENDPOINT_URL", "https://cbdc.test")
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="ORD-CBDC", total=Decimal("1000"))

        result = await service.settle_order("ORD-CBDC")

        assert result.status == "posted"
        assert result.cbdc_transaction_id.startswith("CBDC-")


class TestSettleBatch:
    """Tests for settle_batch."""

    async def test_settle_batch_multiple_orders(self, db_session, monkeypatch):
        """Batch settlement processes multiple orders."""
        monkeypatch.delenv("CBDC_ENDPOINT_URL", raising=False)
        service = AutomatedMarketplaceSettlementService(db_session)
        await _make_order(db_session, order_id="BATCH-1", total=Decimal("1000"))
        await _make_order(db_session, order_id="BATCH-2", total=Decimal("2000"))
        await _make_order(db_session, order_id="BATCH-3", total=Decimal("500"))

        batch: SettlementBatch = await service.settle_batch(limit=50)

        assert len(batch.settled) == 3
        assert len(batch.errors) == 0
        assert all(r.status == "posted" for r in batch.settled)

    async def test_settle_batch_no_eligible(self, db_session, monkeypatch):
        """Empty batch when no orders are eligible."""
        monkeypatch.delenv("CBDC_ENDPOINT_URL", raising=False)
        service = AutomatedMarketplaceSettlementService(db_session)
        batch = await service.settle_batch(limit=50)
        assert len(batch.settled) == 0
        assert len(batch.errors) == 0
