"""Standalone NATS JetStream worker entry point."""

from __future__ import annotations

import asyncio

from services.event_bus.worker import EventWorker


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
