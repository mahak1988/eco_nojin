"""Outbox pattern implementation for event-driven integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import IntOutboxEvent

logger = logging.getLogger(__name__)


class OutboxService:
    """Service for managing outbox events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_event(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
    ) -> int:
        """Add an event to the outbox within the current transaction."""
        event = IntOutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
        )
        self.db.add(event)
        await self.db.flush()
        return event.id

    async def add_event_in_transaction(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
    ) -> int:
        """Add event within an existing transaction (uses current session)."""
        event = IntOutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
        )
        self.db.add(event)
        await self.db.flush()
        return event.id


class OutboxWorker:
    """Background worker to process outbox events."""

    def __init__(
        self,
        batch_size: int = 100,
        poll_interval: float = 0.5,
        max_retries: int = 5,
    ):
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self._running = False

    async def start(self):
        """Start the worker loop."""
        self._running = True
        logger.info("Outbox worker started")
        while self._running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.error(f"Outbox worker error: {e}")
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False

    async def _process_batch(self):
        """Process a batch of unprocessed events."""
        async with hub.get_async_session() as db:
            from sqlalchemy import select

            from database.models import IntOutboxEvent

            stmt = (
                select(IntOutboxEvent)
                .where(IntOutboxEvent.processed_at.is_(None))
                .order_by(IntOutboxEvent.created_at)
                .limit(self.batch_size)
                .with_for_update(skip_locked=True)  # Skip locked rows
            )
            result = await db.execute(stmt)
            events = result.scalars().all()

            for event in events:
                try:
                    await self._process_event(db, event)
                    event.processed_at = datetime.now(UTC)
                    await db.commit()
                except Exception as e:
                    logger.error(f"Failed to process outbox event {event.id}: {e}")
                    event.retry_count += 1
                    if event.retry_count >= 5:
                        event.processed_at = datetime.now(UTC)
                    await db.commit()

    async def _process_event(self, db, event):
        """Process a single event - dispatch to handlers."""
        # Dispatch based on event type
        if event.event_type == "order.created":
            await self._handle_order_created(event)
        elif event.event_type == "payment.completed":
            await self._handle_payment_completed(event)
        elif event.event_type == "inventory.reserved":
            await self._handle_inventory_reserved(event)
        # Add more handlers as needed
        logger.info(
            f"Processed outbox event: {event.event_type} for {event.aggregate_type}:{event.aggregate_id}"
        )

    async def _handle_order_created(self, event):
        # Trigger: reservation, payment intent creation, etc.
        pass

    async def _handle_payment_completed(self, event):
        # Trigger: order confirmation, inventory issue, ledger entries
        pass

    async def _handle_inventory_reserved(self, event):
        # Trigger: order confirmation, etc.
        pass


class OutboxServiceSync:
    """Synchronous version for use in synchronous contexts."""

    def __init__(self, db):
        self.db = db

    def add_event(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
    ) -> int:
        """Add an event to the outbox within the current transaction."""
        from database.models import IntOutboxEvent

        event = IntOutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
        )
        self.db.add(event)
        self.db.flush()
        return event.id
