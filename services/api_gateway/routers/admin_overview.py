"""Admin Overview Router - Platform metrics and overview.

S-STRUCT compliant: this router delegates all DB access to
``services.admin.overview_service.OverviewService``, which uses
``services.admin.repository_overview.OverviewRepository``. No direct
``db.query`` / ``db.execute`` calls remain in the router. Health probes
delegate to the service layer.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from services.admin.overview_service import OverviewService, get_overview_service
from services.api_gateway.auth import _get_async_db as get_async_db
from services.api_gateway.auth import require_admin_with_mfa

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
    revenue_24h: float | None = None
    api_requests_24h: int | None = None
    error_rate_24h: float | None = None
    avg_response_time_ms: float | None = None


class ChannelHealth(BaseModel):
    name: str
    status: str
    latency_ms: float | None = None
    last_check: str | None = None
    detail: str = ""


def _platform_stats_response(stats: dict) -> PlatformStats:
    return PlatformStats(**stats)


@router.get("", response_model=PlatformStats)
async def get_platform_overview(
    current_user: Annotated[Any, Depends(require_admin_with_mfa)],
    db: Annotated[Any, Depends(get_async_db)],
):
    """Get platform overview statistics."""
    service = get_overview_service(db)
    stats = await service.get_platform_stats()
    return _platform_stats_response(stats)


@router.get("/health", response_model=list[ChannelHealth])
async def get_channels_health(
    request: Request,
    current_user: Annotated[Any, Depends(require_admin_with_mfa)],
    service: Annotated[OverviewService, Depends(get_overview_service)],
):
    """Report whether each platform channel is reachable.

    The API Gateway channel is the process that answered this very request,
    so it reports ``status="healthy"`` with a measured response time.
    All other channels are probed by the service layer.
    """
    import time as _time
    _started = _time.perf_counter()
    _external = await service.get_channels_health()
    _elapsed_ms = (_time.perf_counter() - _started) * 1000
    results = [
        {
            "name": "API Gateway",
            "status": "healthy",
            "latency_ms": round(_elapsed_ms, 2),
            "last_check": datetime.now(UTC).isoformat(),
            "detail": "this process served the request",
        }
    ]
    results.extend(_external)
    return results


@router.get("/metrics")
async def get_detailed_metrics(
    request: Request,
    hours: Annotated[int, Query(ge=1, le=168)] = 24,
    current_user: Annotated[Any, Depends(require_admin_with_mfa)] = None,
    db: Annotated[Any, Depends(get_async_db)] = None,
):
    """Request and latency metrics for the last N hours."""
    service = get_overview_service(db)
    return await service.get_detailed_metrics(hours)
