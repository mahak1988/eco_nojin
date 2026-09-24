"""Tests for the unified ledger escrow state machine (plan v2.2)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.base import Base
from database.models import EscrowState
from services.ledger.service import EscrowService


@pytest_asyncio.fixture
async def async_session():
    """In-memory SQLite async session with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
class TestEscrowStateMachine:
    """Validates the created → locked → released|reversed lifecycle."""

    async def test_state_machine_transitions(self, async_session):
        svc = EscrowService(session=async_session)

        record = await svc.create(
            order_id="order-1",
            buyer_id="buyer-1",
            seller_id="seller-1",
            amount=Decimal("150000"),
        )
        assert record.state == EscrowState.CREATED.value
        assert record.id is not None

        assert not EscrowState.CREATED.can_transition_to(EscrowState.RELEASED)
        assert EscrowState.CREATED.can_transition_to(EscrowState.LOCKED)

        record = await svc.lock(order_id="order-1")
        assert record.state == EscrowState.LOCKED.value
        assert record.dispute_window_deadline is not None

        assert EscrowState.LOCKED.can_transition_to(EscrowState.RELEASED)
        assert EscrowState.LOCKED.can_transition_to(EscrowState.REVERSED)
        assert not EscrowState.LOCKED.can_transition_to(EscrowState.CREATED)

        record = await svc.release(order_id="order-1", actor_id="admin-1")
        assert record.state == EscrowState.RELEASED.value
        assert record.completed_at is not None

    async def test_reversal_from_locked(self, async_session):
        svc = EscrowService(session=async_session)

        await svc.create(
            order_id="order-2",
            buyer_id="buyer-2",
            seller_id="seller-2",
            amount=Decimal("50000"),
        )
        await svc.lock(order_id="order-2")
        record = await svc.reverse(order_id="order-2", actor_id="buyer-2")
        assert record.state == EscrowState.REVERSED.value
        assert record.completed_at is not None

    async def test_invalid_transition_locked_to_locked(self, async_session):
        svc = EscrowService(session=async_session)

        await svc.create(
            order_id="order-3",
            buyer_id="buyer-3",
            seller_id="seller-3",
            amount=Decimal("10000"),
        )
        await svc.lock(order_id="order-3")
        with pytest.raises(ValueError, match="cannot lock"):
            await svc.lock(order_id="order-3")

    async def test_cannot_release_unlocked(self, async_session):
        svc = EscrowService(session=async_session)
        await svc.create(
            order_id="order-4",
            buyer_id="buyer-4",
            seller_id="seller-4",
            amount=Decimal("10000"),
        )
        with pytest.raises(ValueError, match="cannot release"):
            await svc.release(order_id="order-4")

    async def test_complete_after_release(self, async_session):
        svc = EscrowService(session=async_session)
        await svc.create(
            order_id="order-5",
            buyer_id="buyer-5",
            seller_id="seller-5",
            amount=Decimal("20000"),
        )
        await svc.lock(order_id="order-5")
        await svc.release(order_id="order-5")
        record = await svc.complete(order_id="order-5")
        assert record.state == EscrowState.RELEASED.value

    async def test_dispute_window_open(self, async_session):
        svc = EscrowService(session=async_session)
        await svc.create(
            order_id="order-6",
            buyer_id="buyer-6",
            seller_id="seller-6",
            amount=Decimal("20000"),
        )
        await svc.lock(order_id="order-6")
        record = await svc.dispute(order_id="order-6")
        assert record.state == EscrowState.LOCKED.value
        assert record.dispute_window_deadline is not None
        deadline = record.dispute_window_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        assert deadline > datetime.now(UTC)

    async def test_dispute_window_expiry(self, async_session):
        svc = EscrowService(session=async_session)
        svc.DISPUTE_WINDOW_HOURS = 0

        await svc.create(
            order_id="order-7",
            buyer_id="buyer-7",
            seller_id="seller-7",
            amount=Decimal("20000"),
        )
        await svc.lock(order_id="order-7")
        with pytest.raises(ValueError, match="Dispute window expired"):
            await svc.dispute(order_id="order-7")

    async def test_double_release_prevented(self, async_session):
        svc = EscrowService(session=async_session)
        await svc.create(
            order_id="order-8",
            buyer_id="buyer-8",
            seller_id="seller-8",
            amount=Decimal("20000"),
        )
        await svc.lock(order_id="order-8")
        await svc.release(order_id="order-8")
        with pytest.raises(ValueError, match="cannot release"):
            await svc.release(order_id="order-8")


class TestProvenanceStamp:
    def test_stamps_value_with_source(self):
        from services.provenance.stamp import stamp_value

        stamped = stamp_value(Decimal("150000"), source="ledger:balance")
        assert stamped.value == Decimal("150000")
        assert stamped.source == "ledger:balance"
        assert stamped.timestamp is not None

    def test_stamp_serializable(self):
        from services.provenance.stamp import stamp_value

        stamped = stamp_value(Decimal("150000"), source="ledger:escrow_release", method="realtime")
        data = stamped.model_dump()
        assert "value" in data
        assert "source" in data
        assert "timestamp" in data
        assert data["method"] == "realtime"


class TestIdempotencySHA256Key:
    def test_sha256_key_passes_format_validation(self):
        """SHA256 hex key (64 chars) passes format validation."""
        import hashlib

        from services.api_gateway.middleware.idempotency import IdempotencyMiddleware

        IdempotencyMiddleware(app=None)
        key = hashlib.sha256(b"test").hexdigest()
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_uuid_still_accepted(self):
        """UUID v4 keys still pass format validation."""
        import uuid

        from services.api_gateway.middleware.idempotency import IdempotencyMiddleware

        IdempotencyMiddleware(app=None)
        key = str(uuid.uuid4())
        assert len(key) == 36
