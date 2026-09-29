"""Standalone NATS JetStream worker entry point.

Now backed by ``services.api_gateway.eventbus``, the single stack chosen in the
phase 4 S-EVENT consolidation. ``services/event_bus/`` held a second, parallel
implementation whose subject mapping differed from the gateway's, so the same
logical event could land on two different subjects depending on which one
published it.
"""

from __future__ import annotations

import asyncio
import logging

from services.api_gateway.eventbus.worker import EventWorker

logger = logging.getLogger(__name__)


async def run_event_worker(settings: object | None = None, **kwargs: object) -> None:
    """Run the configured event worker until interrupted."""
    worker = EventWorker.from_settings(settings)
    await worker.run(**kwargs)


def main() -> int:
    """CLI entry point for ``python -m services.workers.event_worker``."""
    try:
        asyncio.run(run_event_worker())
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
