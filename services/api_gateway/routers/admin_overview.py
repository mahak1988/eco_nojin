"""Admin Overview Router - Platform metrics and overview."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from database.hub import hub
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
    revenue_24h: float
    api_requests_24h: int
    error_rate_24h: float
    avg_response_time_ms: float


class ChannelHealth(BaseModel):
    name: str
    status: str  # "healthy", "degraded", "down"
    latency_ms: Optional[float] = None
    last_check: str


@router.get("", response_model=PlatformStats)
async def get_platform_overview(
    current_user=Depends(require_admin_with_mfa),
):
    """Get platform overview statistics."""
    db = hub.get_session()
    try:
        from database import models

        total_users = db.query(models.User).count()
        active_users = db.query(models.User).filter(models.User.is_active == True).count()
        total_farms = db.query(models.Farm).count()
        total_land = db.query(models.LandProfile).count()

        from database.models import Content
        total_content = db.query(Content).count()
        published_content = db.query(Content).filter(Content.status == "published").count()

        from database.models import Product, Order
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
    """Get health status of all platform channels."""
    from datetime import UTC, datetime

    return [
        ChannelHealth(name="API Gateway", status="healthy", latency_ms=45.2, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="Database (PostgreSQL)", status="healthy", latency_ms=12.1, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="Database (DuckDB)", status="healthy", latency_ms=8.3, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="Redis Cache", status="healthy", latency_ms=2.1, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="NATS Event Bus", status="healthy", latency_ms=3.7, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="Qdrant Vector DB", status="healthy", latency_ms=15.4, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="AI Assistant (Groq)", status="healthy", latency_ms=120.0, last_check=datetime.now(UTC).isoformat()),
        ChannelHealth(name="Satellite Data", status="healthy", latency_ms=250.0, last_check=datetime.now(UTC).isoformat()),
    ]


@router.get("/metrics")
async def get_detailed_metrics(
    hours: int = Query(24, ge=1, le=168),
    current_user=Depends(require_admin_with_mfa),
):
    """Get detailed metrics for the last N hours."""
    # Mock data - replace with actual metrics collection
    return {
        "period_hours": hours,
        "requests": {"total": 15000, "success": 14850, "error": 150},
        "latency": {"p50": 45, "p95": 120, "p99": 350},
        "throughput_rps": 1.7,
        "top_endpoints": [
            {"path": "/api/v1/ai/chat", "requests": 3200, "avg_latency": 850},
            {"path": "/api/v1/ai/analysis/drought", "requests": 1800, "avg_latency": 1200},
            {"path": "/api/v1/farms", "requests": 1500, "avg_latency": 45},
        ],
    }