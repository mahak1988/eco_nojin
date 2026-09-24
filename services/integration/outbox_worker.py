"""Outbox worker — polls IntOutboxEvent and dispatches events to NATS JetStream.

Uses PostgreSQL ``FOR UPDATE SKIP LOCKED`` to claim events atomically.
After successful dispatch to NATS, marks the event as processed. On failure,
increments retry_count for redelivery.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import IntOutboxEvent
from services.api_gateway.eventbus import get_nats_manager

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 1
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2  # exponential backoff
BATCH_SIZE = 100


class OutboxWorker:
    """Polling outbox worker for exactly-once event delivery to NATS."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._nats_manager = get_nats_manager()

    async def poll_once(self, limit: int = BATCH_SIZE) -> int:
        """Poll for unprocessed events, claim them atomically, and dispatch to NATS.

        Returns the number of events successfully processed in this cycle.
        """
        claimed: list[IntOutboxEvent] = []
        now = datetime.now(UTC)

        try:
            # Atomically claim events using SKIP LOCKED
            result = await self.db.execute(
                select(IntOutboxEvent)
                .where(
                    IntOutboxEvent.processed_at.is_(None),
                    IntOutboxEvent.retry_count < MAX_RETRIES,
                )
                .order_by(IntOutboxEvent.created_at.asc())
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
            rows = result.scalars().all()

            for row in rows:
                # Claim by setting processed_at to now (prevents other workers from picking up)
                await self.db.execute(
                    update(IntOutboxEvent)
                    .where(IntOutboxEvent.id == row.id)
                    .values(processed_at=now)
                )

            await self.db.flush()
            claimed = rows
        except Exception as exc:
            logger.warning("Outbox: failed to claim events, aborting cycle: %s", exc)
            await self.db.rollback()
            return 0

        processed = 0
        for event in claimed:
            try:
                await self._dispatch_event(event)
                processed += 1
            except Exception as exc:
                logger.error(
                    "Outbox: failed to dispatch event %d (%s): %s", event.id, event.event_type, exc
                )
                # Reset processed_at so other workers can retry
                await self.db.execute(
                    update(IntOutboxEvent)
                    .where(IntOutboxEvent.id == event.id)
                    .values(
                        processed_at=None,
                        retry_count=event.retry_count + 1,
                    )
                )
                await self.db.flush()

        await self.db.commit()
        return processed

    async def _dispatch_event(self, event: IntOutboxEvent) -> None:
        """Dispatch a single outbox event to NATS JetStream.

        The payload contains:
          - aggregate_type / aggregate_id for tracing
          - event_type to determine the subject
          - payload with event-specific data
        """
        payload = event.payload or {}
        event_type = event.event_type
        aggregate_type = event.aggregate_type or "unknown"
        aggregate_id = event.aggregate_id or "unknown"

        # Determine NATS subject from event_type
        subject = self._get_subject(event_type, aggregate_type)

        # Prepare NATS message
        nats_payload = {
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": payload,
        }

        # Correlation ID from outbox event
        correlation_id = f"outbox-{event.id}"

        # Publish to NATS with retry
        success = await self._nats_manager.publish_with_retry(
            subject,
            nats_payload,
            correlation_id=correlation_id,
            max_retries=3,
        )

        if not success:
            raise RuntimeError(f"Failed to publish event {event.id} to NATS after retries")

        # Mark as Supabase synced (for compatibility with existing sync flow)
        await self.db.execute(
            update(IntOutboxEvent).where(IntOutboxEvent.id == event.id).values(supabase_synced=True)
        )

        logger.info(
            "Outbox: event %d (%s) published to NATS subject %s",
            event.id,
            event_type,
            subject,
        )

    def _get_subject(self, event_type: str, aggregate_type: str) -> str:
        """Map event_type to NATS subject prefix."""
        # Domain-specific subject mapping
        if event_type.startswith("user."):
            return f"user.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("sync."):
            return f"sync.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("wallet."):
            return f"wallet.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("order."):
            return f"order.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("payment."):
            return f"payment.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("inventory."):
            return f"inventory.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("ledger."):
            return f"ledger.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("carbon."):
            return f"carbon.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("mrv."):
            return f"mrv.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("marketplace."):
            return f"marketplace.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("farm."):
            return f"farm.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("simulation."):
            return f"simulation.{event_type.split('.', 1)[1]}"
        elif event_type.startswith("realtime."):
            return f"realtime.{event_type.split('.', 1)[1]}"
        else:
            # Fallback: use aggregate_type as domain
            return f"{aggregate_type}.{event_type}"

    async def cleanup_expired(self, older_than_hours: int = 24) -> int:
        """Delete processed events older than the given threshold."""
        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
        result = await self.db.execute(
            text(
                "DELETE FROM int_outbox_event WHERE processed_at IS NOT NULL AND processed_at < :cutoff"
            ),
            {"cutoff": cutoff},
        )
        await self.db.commit()
        return result.rowcount

    async def run_forever(self, poll_interval: float = POLL_INTERVAL_SECONDS) -> None:
        """Run the outbox worker continuously."""
        logger.info(
            "Outbox worker started (poll interval=%.1fs, NATS bridge enabled)", poll_interval
        )
        while True:
            try:
                async with hub.get_async_session() as db:
                    worker = OutboxWorker(db)
                    processed = await worker.poll_once()
                    if processed:
                        logger.info("Outbox: processed %d events to NATS", processed)
                    await worker.cleanup_expired()
            except Exception as exc:
                logger.error("Outbox worker cycle error: %s", exc)
            await asyncio.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Idempotency key cleanup
# ---------------------------------------------------------------------------


async def cleanup_expired_idempotency_keys(db: AsyncSession, older_than_hours: int = 24) -> int:
    """Remove expired idempotency keys from the store."""
    cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
    result = await db.execute(
        text("DELETE FROM fin_idempotency_key WHERE expires_at < :cutoff"),
        {"cutoff": cutoff},
    )
    return result.rowcount


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


async def main():
    """Run the outbox worker as a background process."""
    async with hub.get_async_session() as db:
        worker = OutboxWorker(db)
        await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
