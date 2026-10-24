"""Tests for the outbox pattern (event-driven integration)."""

import pytest

from services.integration.outbox import OutboxService, OutboxWorker


class TestOutboxService:
    """Tests for OutboxService (requires database)."""

    @pytest.fixture
    def service(self, db_session):
        return OutboxService(db_session)

    async def test_service_instantiation(self, service):
        assert service is not None
        assert hasattr(service, 'add_event')

    async def test_add_event_creates_a_pending_event(self, service):
        """An event must be written inside the caller's transaction."""
        event_id = await service.add_event(
            aggregate_type="order",
            aggregate_id="order-1",
            event_type="order.created",
            payload={"total": "100.00"},
        )
        assert event_id is not None

        from sqlalchemy import select

        from database.models import IntOutboxEvent

        result = await service.db.execute(
            select(IntOutboxEvent).where(IntOutboxEvent.id == event_id)
        )
        event = result.scalar_one()
        assert event.aggregate_type == "order"
        assert event.aggregate_id == "order-1"
        assert event.event_type == "order.created"
        assert event.payload["total"] == "100.00"

    async def test_new_events_are_unprocessed(self, service):
        await service.add_event(
            aggregate_type="order",
            aggregate_id="order-2",
            event_type="order.created",
            payload={},
        )

        from sqlalchemy import select

        from database.models import IntOutboxEvent

        result = await service.db.execute(select(IntOutboxEvent))
        events = result.scalars().all()
        assert events
        assert all(event.processed_at is None for event in events)

    async def test_events_are_ordered_by_creation(self, service):
        for i in range(3):
            await service.add_event(
                aggregate_type="order",
                aggregate_id=f"order-{i}",
                event_type="order.created",
                payload={"n": i},
            )

        from sqlalchemy import select

        from database.models import IntOutboxEvent

        result = await service.db.execute(
            select(IntOutboxEvent).order_by(IntOutboxEvent.created_at)
        )
        events = result.scalars().all()
        assert [e.aggregate_id for e in events] == ["order-0", "order-1", "order-2"]


class TestOutboxWorker:
    """Tests for the OutboxWorker loop control."""

    def test_worker_defaults(self):
        worker = OutboxWorker()
        assert worker.batch_size == 100
        assert worker.poll_interval == 0.5
        assert worker.max_retries == 5
        assert worker._running is False

    def test_worker_accepts_configuration(self):
        worker = OutboxWorker(batch_size=10, poll_interval=0.1, max_retries=2)
        assert worker.batch_size == 10
        assert worker.poll_interval == 0.1
        assert worker.max_retries == 2

    def test_stop_clears_the_running_flag(self):
        worker = OutboxWorker()
        worker._running = True
        worker.stop()
        assert worker._running is False
