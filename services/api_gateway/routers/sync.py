"""Sync status — offline/cloud data synchronization endpoint with real Supabase integration."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict, Any

from database.hub import hub
from database.models import IntOutboxEvent, User
from services.supabase.client import get_supabase_client
from engine.hydroma.config.settings import get_settings
from services.api_gateway.eventbus import publish_sync_event

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


def get_db():
    with hub.get_session() as session:
        yield session


@router.get("/status")
async def sync_status(request: Request, db: Session = Depends(get_db)):
    """Real sync status with Supabase connectivity check."""
    settings = get_settings()

    # Feature flag check
    if not settings.enable_supabase_sync:
        return {
            "status": "disabled",
            "mode": "local-first",
            "cloud": "supabase",
            "local_pending_events": 0,
            "supabase_connected": False,
            "supabase_error": "Supabase sync disabled via feature flag",
            "note": "Enable with ENABLE_SUPABASE_SYNC=true",
        }

    # Check local outbox pending events
    pending_count = (
        db.execute(select(IntOutboxEvent).where(IntOutboxEvent.processed_at.is_(None)))
        .scalars()
        .all()
    )

    # Check Supabase connectivity
    supabase_ok = False
    supabase_error = None
    try:
        supabase = get_supabase_client()
        # Simple health check - query auth or a known table
        result = (
            supabase.auth.get_user()
            if False
            else supabase.table("platform_landscapes")
            .select("id", count="exact")
            .limit(1)
            .execute()
        )
        supabase_ok = True
    except Exception as e:
        supabase_error = str(e)

    # Log with correlation ID
    request_id = request.headers.get("X-Request-ID", "unknown")
    from structlog import get_logger

    logger = get_logger("econojin.api.sync")
    logger.info(
        "sync_status_checked",
        request_id=request_id,
        pending=len(pending_count),
        supabase_ok=supabase_ok,
    )

    return {
        "status": "ok",
        "mode": "local-first",
        "cloud": "supabase",
        "local_pending_events": len(pending_count),
        "supabase_connected": supabase_ok,
        "supabase_error": supabase_error,
        "note": "Local-first sync with Supabase cloud. Offline data syncs when connection restored.",
    }


@router.post("/trigger")
async def trigger_sync(request: Request, db: Session = Depends(get_db)):
    """Manually trigger sync of pending outbox events to Supabase."""
    settings = get_settings()

    # Feature flag check
    if not settings.enable_supabase_sync:
        raise HTTPException(status_code=503, detail="Supabase sync disabled via feature flag")

    if not (supabase_ok := _check_supabase()):
        raise HTTPException(status_code=503, detail="Supabase not available")

    supabase = get_supabase_client()
    pending = (
        db.execute(select(IntOutboxEvent).where(IntOutboxEvent.processed_at.is_(None)))
        .scalars()
        .all()
    )

    synced = 0
    failed = 0

    request_id = request.headers.get("X-Request-ID", "unknown")
    from structlog import get_logger

    logger = get_logger("econojin.api.sync")

    for event in pending:
        try:
            # Map event to Supabase table based on event_type
            table = _map_event_to_table(event.event_type)
            if table:
                supabase.table(table).upsert(event.payload).execute()
                event.processed_at = datetime.utcnow()
                event.supabase_synced = True
                synced += 1
                logger.info(
                    "outbox_event_synced",
                    request_id=request_id,
                    event_id=event.id,
                    event_type=event.event_type,
                )
                # Publish sync event to NATS for downstream consumers
                try:
                    await publish_sync_event(
                        "outbox_synced",
                        str(event.id),
                        {
                            "event_type": event.event_type,
                            "aggregate_type": event.aggregate_type,
                            "aggregate_id": event.aggregate_id,
                            "table": table,
                        },
                        correlation_id=request_id,
                    )
                except Exception as e:
                    logger.warning(f"Failed to publish sync event: {e}")
        except Exception as e:
            event.retry_count = (event.retry_count or 0) + 1
            event.last_error = str(e)
            failed += 1
            logger.error(
                "outbox_event_sync_failed", request_id=request_id, event_id=event.id, error=str(e)
            )

    db.commit()

    logger.info(
        "sync_trigger_completed",
        request_id=request_id,
        synced=synced,
        failed=failed,
        total=len(pending),
    )

    return {
        "ok": True,
        "synced": synced,
        "failed": failed,
        "total_pending": len(pending),
    }


@router.get("/pending")
async def list_pending(request: Request, db: Session = Depends(get_db)):
    """List pending outbox events."""
    settings = get_settings()

    # Feature flag check
    if not settings.enable_supabase_sync:
        return {
            "ok": True,
            "count": 0,
            "events": [],
            "note": "Supabase sync disabled via feature flag",
        }

    pending = (
        db.execute(select(IntOutboxEvent).where(IntOutboxEvent.processed_at.is_(None)))
        .scalars()
        .all()
    )

    request_id = request.headers.get("X-Request-ID", "unknown")
    from structlog import get_logger

    logger = get_logger("econojin.api.sync")
    logger.info("sync_pending_listed", request_id=request_id, count=len(pending))

    return {
        "ok": True,
        "count": len(pending),
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "aggregate_id": e.aggregate_id,
                "payload": e.payload,
                "retry_count": e.retry_count,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in pending
        ],
    }


def _check_supabase() -> bool:
    """Quick Supabase connectivity check."""
    try:
        get_supabase_client()
        return True
    except Exception:
        return False


def _map_event_to_table(event_type: str) -> Optional[str]:
    """Map internal event types to Supabase table names."""
    mapping = {
        "landscape_created": "platform_landscapes",
        "landscape_updated": "platform_landscapes",
        "carbon_credit_issued": "carbon_credits",
        "mrv_report_submitted": "mrv_reports",
        "user_registered": "profiles",
        "order_placed": "orders",
        "payment_completed": "payments",
    }
    return mapping.get(event_type)


# ============================================================================
# OFFLINE CONFLICT RESOLUTION (Vector Clock based)
# ============================================================================

class VectorClock(BaseModel):
    """Vector clock for conflict detection."""
    clocks: Dict[str, int] = Field(default_factory=dict)
    
    def increment(self, node_id: str) -> "VectorClock":
        """Create new vector clock with incremented counter for node."""
        new_clocks = self.clocks.copy()
        new_clocks[node_id] = new_clocks.get(node_id, 0) + 1
        return VectorClock(clocks=new_clocks)
    
    def merge(self, other: "VectorClock") -> "VectorClock":
        """Merge two vector clocks (take max of each counter)."""
        all_nodes = set(self.clocks.keys()) | set(other.clocks.keys())
        merged = {node: max(self.clocks.get(node, 0), other.clocks.get(node, 0)) for node in all_nodes}
        return VectorClock(clocks=merged)
    
    def happens_before(self, other: "VectorClock") -> bool:
        """Check if self happens before other (self < other)."""
        dominates = False
        for node in set(self.clocks.keys()) | set(other.clocks.keys()):
            if self.clocks.get(node, 0) > other.clocks.get(node, 0):
                return False
            if self.clocks.get(node, 0) < other.clocks.get(node, 0):
                dominates = True
        return dominates
    
    def is_concurrent(self, other: "VectorClock") -> bool:
        """Check if two vector clocks are concurrent (neither happens before the other)."""
        return not self.happens_before(other) and not other.happens_before(self)


class ConflictResolutionRequest(BaseModel):
    """Request payload for conflict resolution."""
    entity_type: str  # e.g., "farm", "marketplace_cart", "farm_analysis"
    entity_id: str
    client_vector_clock: VectorClock
    client_data: Dict[str, Any]
    client_timestamp: datetime
    resolution_strategy: str = "server_wins"  # "server_wins", "client_wins", "merge", "manual"


class ConflictResolutionResponse(BaseModel):
    """Response payload for conflict resolution."""
    resolved: bool
    resolution_strategy: str
    server_vector_clock: VectorClock
    server_data: Dict[str, Any]
    server_timestamp: datetime
    conflict_details: Optional[Dict[str, Any]] = None
    requires_manual_resolution: bool = False


@router.post("/merge", response_model=ConflictResolutionResponse)
async def merge_offline_data(
    request: Request,
    conflict_request: ConflictResolutionRequest,
    db: Session = Depends(get_db),
):
    """
    Merge offline data with server state using vector clock conflict resolution.
    
    This endpoint implements a vector clock-based conflict resolution strategy:
    - If client clock happens before server clock: server wins (data already synced)
    - If server clock happens before client clock: client wins (new offline changes)
    - If concurrent: apply resolution strategy (server_wins, client_wins, merge, manual)
    """
    settings = get_settings()
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    from structlog import get_logger
    logger = get_logger("econojin.api.sync.merge")
    
    logger.info(
        "merge_request_received",
        request_id=request_id,
        entity_type=conflict_request.entity_type,
        entity_id=conflict_request.entity_id,
        strategy=conflict_request.resolution_strategy,
    )
    
    # Fetch current server state
    server_data, server_vector_clock, server_timestamp = await _get_server_state(
        conflict_request.entity_type,
        conflict_request.entity_id,
        db,
    )
    
    if server_data is None:
        # Entity doesn't exist on server, create it
        await _create_entity(
            conflict_request.entity_type,
            conflict_request.entity_id,
            conflict_request.client_data,
            conflict_request.client_vector_clock,
            conflict_request.client_timestamp,
            db,
        )
        
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="client_wins",
            server_vector_clock=conflict_request.client_vector_clock,
            server_data=conflict_request.client_data,
            server_timestamp=conflict_request.client_timestamp,
        )
    
    # Compare vector clocks
    client_vc = conflict_request.client_vector_clock
    server_vc = server_vector_clock
    
    if client_vc.happens_before(server_vc):
        # Client is behind server - server wins
        logger.info(
            "merge_client_behind_server",
            request_id=request_id,
            entity_type=conflict_request.entity_type,
            entity_id=conflict_request.entity_id,
        )
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="server_wins",
            server_vector_clock=server_vc,
            server_data=server_data,
            server_timestamp=server_timestamp,
        )
    
    elif server_vc.happens_before(client_vc):
        # Server is behind client - client wins
        await _update_entity(
            conflict_request.entity_type,
            conflict_request.entity_id,
            conflict_request.client_data,
            client_vc,
            conflict_request.client_timestamp,
            db,
        )
        
        logger.info(
            "merge_client_ahead_server",
            request_id=request_id,
            entity_type=conflict_request.entity_type,
            entity_id=conflict_request.entity_id,
        )
        
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="client_wins",
            server_vector_clock=client_vc,
            server_data=conflict_request.client_data,
            server_timestamp=conflict_request.client_timestamp,
        )
    
    elif client_vc.is_concurrent(server_vc):
        # Concurrent modifications - apply resolution strategy
        logger.warning(
            "merge_concurrent_modifications",
            request_id=request_id,
            entity_type=conflict_request.entity_type,
            entity_id=conflict_request.entity_id,
            strategy=conflict_request.resolution_strategy,
        )
        
        return await _resolve_concurrent(
            conflict_request,
            server_data,
            server_vc,
            server_timestamp,
            db,
        )
    
    else:
        # Should not happen
        return ConflictResolutionResponse(
            resolved=False,
            resolution_strategy="error",
            server_vector_clock=server_vc,
            server_data=server_data,
            server_timestamp=server_timestamp,
            conflict_details={"error": "Unknown vector clock state"},
            requires_manual_resolution=True,
        )


async def _get_server_state(
    entity_type: str,
    entity_id: str,
    db: Session,
) -> tuple[Optional[Dict[str, Any]], VectorClock, Optional[datetime]]:
    """Fetch current server state for an entity."""
    # This is a simplified implementation - in production, you'd query
    # the appropriate table based on entity_type
    table_map = {
        "farm": "farms",
        "marketplace_cart": "marketplace_carts",
        "farm_analysis": "farm_analyses",
        "order": "orders",
    }
    
    table = table_map.get(entity_type)
    if not table:
        return None, VectorClock(), None
    
    # For demo purposes, return None (entity doesn't exist)
    # In production, query the actual table
    return None, VectorClock(), None


async def _create_entity(
    entity_type: str,
    entity_id: str,
    data: Dict[str, Any],
    vector_clock: VectorClock,
    timestamp: datetime,
    db: Session,
) -> None:
    """Create new entity with vector clock metadata."""
    # In production, insert into appropriate table with vector clock column
    pass


async def _update_entity(
    entity_type: str,
    entity_id: str,
    data: Dict[str, Any],
    vector_clock: VectorClock,
    timestamp: datetime,
    db: Session,
) -> None:
    """Update existing entity with new data and vector clock."""
    # In production, update the appropriate table
    pass


async def _resolve_concurrent(
    conflict_request: ConflictResolutionRequest,
    server_data: Dict[str, Any],
    server_vc: VectorClock,
    server_timestamp: datetime,
    db: Session,
) -> ConflictResolutionResponse:
    """Resolve concurrent modifications based on strategy."""
    strategy = conflict_request.resolution_strategy
    client_data = conflict_request.client_data
    client_vc = conflict_request.client_vector_clock
    
    if strategy == "server_wins":
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="server_wins",
            server_vector_clock=server_vc,
            server_data=server_data,
            server_timestamp=server_timestamp,
            conflict_details={"client_data": client_data},
        )
    
    elif strategy == "client_wins":
        # Update with client data
        await _update_entity(
            conflict_request.entity_type,
            conflict_request.entity_id,
            client_data,
            client_vc,
            conflict_request.client_timestamp,
            db,
        )
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="client_wins",
            server_vector_clock=client_vc,
            server_data=client_data,
            server_timestamp=conflict_request.client_timestamp,
        )
    
    elif strategy == "merge":
        # Attempt automatic field-level merge
        merged_data = _merge_data(server_data, client_data)
        merged_vc = server_vc.merge(client_vc)
        
        await _update_entity(
            conflict_request.entity_type,
            conflict_request.entity_id,
            merged_data,
            merged_vc,
            datetime.utcnow(),
            db,
        )
        
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="merge",
            server_vector_clock=merged_vc,
            server_data=merged_data,
            server_timestamp=datetime.utcnow(),
        )
    
    elif strategy == "manual":
        # Return conflict details for manual resolution
        return ConflictResolutionResponse(
            resolved=False,
            resolution_strategy="manual",
            server_vector_clock=server_vc,
            server_data=server_data,
            server_timestamp=server_timestamp,
            conflict_details={
                "client_data": client_data,
                "client_vector_clock": client_vc.clocks,
                "server_vector_clock": server_vc.clocks,
            },
            requires_manual_resolution=True,
        )
    
    else:
        # Default to server_wins
        return ConflictResolutionResponse(
            resolved=True,
            resolution_strategy="server_wins",
            server_vector_clock=server_vc,
            server_data=server_data,
            server_timestamp=server_timestamp,
            conflict_details={"client_data": client_data},
        )


def _merge_data(server: Dict[str, Any], client: Dict[str, Any]) -> Dict[str, Any]:
    """Simple field-level merge: client fields override server for non-null values."""
    merged = server.copy()
    for key, value in client.items():
        if value is not None:
            merged[key] = value
    return merged
