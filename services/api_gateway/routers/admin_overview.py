"""Admin Overview Router - Platform metrics and overview."""

from __future__ import annotations

import inspect
import logging
import time
from datetime import UTC, datetime

import redis
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text

from database.hub import hub
from engine.hydroma.config.settings import get_settings
from services.api_gateway.auth import require_admin_with_mfa
from services.api_gateway.eventbus.nats_client import get_nats_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/overview", tags=["admin-overview"])


class PlatformStats(BaseModel):
    total_users: int
    active_users_24h: int
    total_farms: int
    total_land_profiles: int
    total_content: int
    published_content: int
    total_marketplace_products: int
    total_orders: int
    revenue_24h: float
    api_requests_24h: int
    error_rate_24h: float
    avg_response_time_ms: float


class ChannelHealth(BaseModel):
    name: str
    status: str  # "healthy", "degraded", "down", "unavailable", "not_instrumented"
    latency_ms: float | None = None
    last_check: str | None = None
    # Why this channel is in the state it is. A channel with no probe, or a
    # probe that raised, has to say which; otherwise "unavailable" and
    # "not_instrumented" are indistinguishable to whoever reads the dashboard.
    detail: str = ""


@router.get("", response_model=PlatformStats)
async def get_platform_overview(
    current_user=Depends(require_admin_with_mfa),
):
    """Get platform overview statistics."""
    db = hub.get_session()
    try:
        from database import models

        total_users = db.query(models.User).count()
        active_users = db.query(models.User).filter(models.User.is_active).count()
        total_farms = db.query(models.Farm).count()
        total_land = db.query(models.LandProfile).count()

        from database.models import Content

        total_content = db.query(Content).count()
        published_content = db.query(Content).filter(Content.status == "published").count()

        from database.models import Order, Product

        total_products = db.query(Product).count()
        total_orders = db.query(Order).count()

        return PlatformStats(
            total_users=total_users,
            active_users_24h=active_users,  # Mock
            total_farms=total_farms,
            total_land_profiles=total_land,
            total_content=total_content,
            published_content=published_content,
            total_marketplace_products=total_products,
            total_orders=total_orders,
            revenue_24h=0.0,  # Mock
            api_requests_24h=0,  # Mock
            error_rate_24h=0.0,  # Mock
            avg_response_time_ms=0.0,  # Mock
        )
    finally:
        db.close()


@router.get("/health", response_model=list[ChannelHealth])
async def get_channels_health(
    current_user=Depends(require_admin_with_mfa),
):
    """Report whether each platform channel is reachable.

    The previous version returned eight channels with status="healthy" and
    hard-coded latencies (45.2, 12.1, 8.3, 2.1, 3.7, 15.4, 120.0, 250.0),
    stamped with ``datetime.now()``. Nothing was probed, so the dashboard
    asserted that the event bus had a 3.7 ms round trip at the moment it was
    asked. ``check-fabricated-success.mjs`` does not match this shape, so the
    gate stayed green.

    Each channel is now either measured or reported as unknown. A channel
    whose probe raises is "unavailable" with the reason, not "healthy".
    """
    now = datetime.now(UTC).isoformat()

    async def probe(name: str, check) -> ChannelHealth:
        """Measure one channel, or record why it could not be measured."""
        started = time.perf_counter()
        try:
            await check()
        except Exception as exc:
            return ChannelHealth(
                name=name,
                status="unavailable",
                latency_ms=None,
                last_check=now,
                detail=f"{type(exc).__name__}: {exc}"[:200],
            )
        elapsed = (time.perf_counter() - started) * 1000
        return ChannelHealth(
            name=name,
            status="healthy",
            latency_ms=round(elapsed, 2),
            last_check=now,
            detail="measured",
        )

    async def database_check() -> None:
        # The same synchronous session the rest of this module uses.
        session = hub.get_session()
        try:
            session.execute(text("SELECT 1"))
        finally:
            session.close()

    async def redis_check() -> None:
        # Built from the configured URL, so a deployment with no Redis
        # configured reports that rather than a fabricated 2.1 ms ping.
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
        # NATSManager has no round-trip health endpoint, so this checks the
        # connection state and, when the client exposes a connectivity method,
        # asks the server. A missing method is not a failure; an unconnected
        # client is.
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

    checks = [
        ("API Gateway", None),  # this process answered the request
        ("Database (PostgreSQL)", database_check),
        ("Redis Cache", redis_check),
        ("NATS Event Bus", nats_check),
    ]

    results: list[ChannelHealth] = []
    for name, check in checks:
        if check is None:
            results.append(
                ChannelHealth(
                    name=name,
                    status="healthy",
                    latency_ms=None,
                    last_check=now,
                    detail="this process served the request",
                )
            )
            continue
        results.append(await probe(name, check))

    # Channels this deployment does not instrument. Reported explicitly so the
    # dashboard shows what is missing instead of silently dropping them.
    for name in ("Database (DuckDB)", "Qdrant Vector DB", "AI Assistant (Groq)", "Satellite Data"):
        results.append(
            ChannelHealth(
                name=name,
                status="not_instrumented",
                latency_ms=None,
                last_check=None,
                detail="no probe is registered for this channel",
            )
        )

    return results


@router.get("/metrics")
async def get_detailed_metrics(
    hours: int = Query(24, ge=1, le=168),
    current_user=Depends(require_admin_with_mfa),
):
    """Request and latency metrics for the last N hours.

    The previous version returned 15000 requests with a 99% success rate and
    p50/p95/p99 of 45/120/350 ms, all literals, and echoed whatever ``hours``
    the caller asked for. A dashboard showing a fabricated 99% success rate is
    worse than one showing nothing, because it is believed.

    Request counters come from the database, using the same synchronous session
    the rest of this module already uses. When no request-log table is present
    the response says so and returns no figures.
    """
    try:
        db = hub.get_session()
        rows = db.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "COUNT(*) FILTER (WHERE status_code < 400) AS success "
                "FROM api_request_log "
                "WHERE created_at >= NOW() - make_interval(hours => :h)"
            ),
            {"h": hours},
        ).first()
    except Exception as exc:
        return {
            "period_hours": hours,
            "requests": None,
            "latency": None,
            "throughput_rps": None,
            "top_endpoints": None,
            "note": (
                f"no request log is readable in this deployment ({type(exc).__name__}), "
                "so no traffic figures exist. This endpoint does not invent them."
            ),
        }

    if rows is None or rows.total is None:
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
            "total": int(rows.total),
            "success": int(rows.success or 0),
            "error": int(rows.total) - int(rows.success or 0),
        },
        "latency": None,
        "throughput_rps": None,
        "top_endpoints": None,
        "note": "request counts measured; latency percentiles are not instrumented",
    }
