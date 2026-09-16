"""Outbox worker — polls IntOutboxEvent and dispatches events exactly-once.

Uses PostgreSQL ``FOR UPDATE SKIP LOCKED`` to claim events atomically.
After successful dispatch, marks the event as processed. On failure,
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

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 1
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2  # exponential backoff
BATCH_SIZE = 100


class OutboxWorker:
    """Polling outbox worker for exactly-once event delivery."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def poll_once(self, limit: int = BATCH_SIZE) -> int:
        """Poll for unprocessed events, claim them atomically, and dispatch.

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
                logger.error("Outbox: failed to dispatch event %d (%s): %s", event.id, event.event_type, exc)
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
        """Dispatch a single outbox event to the appropriate handler.

        The payload contains:
          - aggregate_type / aggregate_id for tracing
          - event_type to determine the handler
          - payload with event-specific data
        """
        payload = event.payload or {}
        event_type = event.event_type

        # Dispatch based on event type
        if event_type.startswith("wallet."):
            await self._dispatch_wallet_event(payload)
        elif event_type.startswith("order."):
            await self._dispatch_order_event(payload)
        elif event_type.startswith("payment."):
            await self._dispatch_payment_event(payload)
        elif event_type.startswith("inventory."):
            await self._dispatch_inventory_event(payload)
        elif event_type.startswith("ledger."):
            await self._dispatch_ledger_event(payload)
        else:
            logger.warning("Outbox: unknown event type: %s", event_type)

    async def _dispatch_wallet_event(self, payload: dict) -> None:
        """Handle wallet-related events (earn, redeem, transfer)."""
        handler = payload.get("handler", "noop")
        if handler == "noop":
            return  # no external system to notify
        logger.info("Outbox: wallet event dispatched (handler=%s)", handler)

    async def _dispatch_order_event(self, payload: dict) -> None:
        """Handle order lifecycle events."""
        handler = payload.get("handler", "noop")
        if handler == "noop":
            return
        logger.info("Outbox: order event dispatched (handler=%s)", handler)

    async def _dispatch_payment_event(self, payload: dict) -> None:
        """Handle payment events (create, confirm, refund)."""
        handler = payload.get("handler", "noop")
        if handler == "noop":
            return
        logger.info("Outbox: payment event dispatched (handler=%s)", handler)

    async def _dispatch_inventory_event(self, payload: dict) -> None:
        """Handle inventory events (receipt, issue, transfer, stocktake)."""
        handler = payload.get("handler", "noop")
        if handler == "noop":
            return
        logger.info("Outbox: inventory event dispatched (handler=%s)", handler)

    async def _dispatch_ledger_event(self, payload: dict) -> None:
        """Handle ledger events (batch posted, batch reversed)."""
        handler = payload.get("handler", "noop")
        if handler == "noop":
            return
        logger.info("Outbox: ledger event dispatched (handler=%s)", handler)

    async def cleanup_expired(self, older_than_hours: int = 24) -> int:
        """Delete processed events older than the given threshold."""
        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
        result = await self.db.execute(
            text("DELETE FROM int_outbox_event WHERE processed_at IS NOT NULL AND processed_at < :cutoff"),
            {"cutoff": cutoff},
        )
        await self.db.commit()
        return result.rowcount

    async def run_forever(self, poll_interval: float = POLL_INTERVAL_SECONDS) -> None:
        """Run the outbox worker continuously."""
        logger.info("Outbox worker started (poll interval=%.1fs)", poll_interval)
        while True:
            try:
                async with hub.get_async_session() as db:
                    worker = OutboxWorker(db)
                    processed = await worker.poll_once()
                    if processed:
                        logger.info("Outbox: processed %d events", processed)
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
    worker = OutboxWorker(None)
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
