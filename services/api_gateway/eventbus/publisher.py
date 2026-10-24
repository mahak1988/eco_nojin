"""
Event Publisher Utility for Routers
===================================
Provides high-level event publishing functions for critical domain events.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from services.api_gateway.eventbus.nats_client import get_nats_manager

logger = logging.getLogger("econojin.eventbus.publisher")


async def publish_user_event(
    event_type: str,
    user_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish user lifecycle events (registered, login, profile_updated, etc.)."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "user",
        "aggregate_id": user_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"user.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_sync_event(
    event_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish sync/outbox events for Supabase synchronization."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "sync",
        "aggregate_id": aggregate_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"sync.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_realtime_event(
    event_type: str,
    user_key: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish realtime events for SSE/WebSocket consumers."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "realtime",
        "aggregate_id": user_key,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"realtime.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_carbon_event(
    event_type: str,
    project_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish carbon project events (credit_issued, verified, retired, etc.)."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "carbon_project",
        "aggregate_id": project_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"carbon.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_mrv_event(
    event_type: str,
    report_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish MRV (Measurement/Reporting/Verification) events."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "mrv_report",
        "aggregate_id": report_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"mrv.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_marketplace_event(
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish marketplace events (order_placed, payment_completed, shop_created, etc.)."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"marketplace.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_farm_event(
    event_type: str,
    farm_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish farm/land events (created, updated, analysis_completed, etc.)."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "farm",
        "aggregate_id": farm_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"farm.{event_type}",
        event,
        correlation_id=correlation_id,
    )


async def publish_simulation_event(
    event_type: str,
    run_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Publish simulation events (started, completed, failed, etc.)."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": "simulation_run",
        "aggregate_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"simulation.{event_type}",
        event,
        correlation_id=correlation_id,
    )


# Convenience function for generic events
async def publish_event(
    domain: str,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> bool:
    """Generic event publisher for any domain."""
    manager = get_nats_manager()
    event = {
        "event_type": event_type,
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    return await manager.publish_with_retry(
        f"{domain}.{event_type}",
        event,
        correlation_id=correlation_id,
    )
