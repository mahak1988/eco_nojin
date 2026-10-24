"""Service for admin overview metrics — business logic layer.

S-STRUCT compliant: all DB and external service probes live here.
The router only calls this service with no direct Session or query access.
"""

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from engine.hydroma.config.settings import get_settings
from services.admin.repository_overview import OverviewRepository
from services.api_gateway.eventbus.nats_client import get_nats_manager

logger = logging.getLogger(__name__)


class OverviewService:
    """Orchestrates platform overview statistics from the repository."""

    def __init__(self, db: AsyncSession):
        self.repo = OverviewRepository(db)

    async def get_platform_stats(self) -> dict:
        """Return platform statistics with honest null for uninstrumented metrics."""
        counts = await self.repo.count_platform_stats()
        return {
            "total_users": counts["total_users"],
            "active_users_24h": counts["active_users"],
            "total_farms": counts["total_farms"],
            "total_land_profiles": counts["total_land_profiles"],
            "total_content": counts["total_content"],
            "published_content": counts["published_content"],
            "total_marketplace_products": counts["total_marketplace_products"],
            "total_orders": counts["total_orders"],
            "revenue_24h": None,
            "api_requests_24h": None,
            "error_rate_24h": None,
            "avg_response_time_ms": None,
        }

    async def get_detailed_metrics(self, hours: int) -> dict:
        """Return request/latency metrics for the last N hours, or null if unavailable."""
        total = await self.repo.count_requests_24h(hours)
        success = await self.repo.count_successful_requests_24h(hours)

        if total is None or success is None:
            return {
                "period_hours": hours,
                "requests": None,
                "latency": None,
                "throughput_rps": None,
                "top_endpoints": None,
                "note": (
                    "no request log is readable in this deployment, "
                    "so no traffic figures exist. This endpoint does not invent them."
                ),
            }

        if total == 0:
            return {
                "period_hours": hours,
                "requests": None,
                "latency": None,
                "throughput_rps": None,
                "top_endpoints": None,
                "note": (
                    "the request log is empty for this window, so there is nothing to "
                    "report. Zero requests is a measurement, not a missing one."
                ),
            }

        return {
            "period_hours": hours,
            "requests": {
                "total": int(total),
                "success": int(success or 0),
                "error": int(total) - int(success or 0),
            },
            "latency": None,
            "throughput_rps": None,
            "top_endpoints": None,
            "note": "request counts measured; latency percentiles are not instrumented",
        }

    async def get_channels_health(self) -> list[dict[str, Any]]:
        """Probe each platform channel and report status."""
        now = datetime.now(UTC).isoformat()

        async def probe(name: str, check: Callable) -> dict[str, Any]:
            started = time.perf_counter()
            try:
                await check()
            except Exception as exc:
                return {
                    "name": name,
                    "status": "unavailable",
                    "latency_ms": None,
                    "last_check": now,
                    "detail": f"{type(exc).__name__}: {exc}"[:200],
                }
            elapsed = (time.perf_counter() - started) * 1000
            return {
                "name": name,
                "status": "healthy",
                "latency_ms": round(elapsed, 2),
                "last_check": now,
                "detail": "measured",
            }

        async def database_check() -> None:
            session = hub.get_session()
            try:
                session.execute(text("SELECT 1"))
            finally:
                session.close()

        async def redis_check() -> None:
            url = get_settings().redis_url
            if not url:
                raise RuntimeError("redis_url is not configured in this deployment")
            client = redis.Redis.from_url(url, socket_connect_timeout=2)
            try:
                if not await client.ping():
                    raise RuntimeError("Redis did not answer PING")
            finally:
                await client.aclose()

        async def nats_check() -> None:
            manager = get_nats_manager()
            if manager is None or not manager.is_connected:
                raise RuntimeError("the NATS client is not connected")
            checker = getattr(manager, "is_healthy", None)
            if callable(checker):
                result = checker()
                if inspect.isawaitable(result):
                    result = await result
                if not result:
                    raise RuntimeError("NATS reported itself unhealthy")

        checks: list[tuple[str, Callable | None]] = [
            ("API Gateway", None),
            ("Database (PostgreSQL)", database_check),
            ("Redis Cache", redis_check),
            ("NATS Event Bus", nats_check),
        ]

        results: list[dict[str, Any]] = []
        for name, check in checks:
            if check is None:
                results.append({
                    "name": name,
                    "status": "healthy",
                    "latency_ms": None,
                    "last_check": now,
                    "detail": "this process served the request",
                })
                continue
            results.append(await probe(name, check))

        for name in ("Database (DuckDB)", "Qdrant Vector DB", "AI Assistant (Groq)", "Satellite Data"):
            results.append({
                "name": name,
                "status": "not_instrumented",
                "latency_ms": None,
                "last_check": None,
                "detail": "no probe is registered for this channel",
            })

        return results


def get_overview_service(db=None) -> OverviewService:
    """Factory for dependency injection."""
    return OverviewService(db)
