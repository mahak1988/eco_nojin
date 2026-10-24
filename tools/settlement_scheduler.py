"""Automated settlement scheduler — runs settle_batch on a fixed interval.

Started as a background_process worker. Each tick opens a fresh hub session,
runs the settlement pipeline, logs the result, and commits.  Failures are
caught and logged — a single bad order must never kill the loop.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import UTC, datetime

logger = logging.getLogger("econojin.settlement-scheduler")

INTERVAL_SECONDS = 60

# Bootstrap PYTHONPATH so the service can import from the repo root.
import os

sys.path.insert(0, os.environ.get("PYTHONPATH", ""))
os.environ.setdefault("SECRET_KEY", "test-secret-key")


async def _tick() -> dict:
    """One settlement pass: open session, run batch, return summary."""
    from database.hub import hub
    from services.finance.automated_marketplace_settlement import (
        AutomatedMarketplaceSettlementService,
    )

    async with hub.get_async_session() as db:
        service = AutomatedMarketplaceSettlementService(db)
        batch = await service.settle_batch(limit=100)
        return {
            "settled": len(batch.settled),
            "errors": len(batch.errors),
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def _loop() -> None:
    """Run the settlement tick forever, every INTERVAL_SECONDS."""
    while True:
        try:
            result = await _tick()
            logger.info(
                "settlement tick: %d settled, %d errors",
                result["settled"],
                result["errors"],
            )
        except Exception as exc:
            logger.error("settlement tick failed: %s", exc, exc_info=True)

        await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("Starting automated settlement scheduler (interval=%ds)", INTERVAL_SECONDS)
    try:
        asyncio.run(_loop())
    except KeyboardInterrupt:
        logger.info("Settlement scheduler shutting down")
