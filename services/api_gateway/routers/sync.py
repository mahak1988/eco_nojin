from datetime import timezone
"""Sync endpoint for offline-first mobile clients."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/sync", tags=["Offline Sync"])


class SyncItem(BaseModel):
    """A single offline action to sync."""

    client_id: str = Field(..., description="Client-generated ID")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., pattern="^(POST|PUT|DELETE)$")
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: int = Field(..., description="Unix timestamp (ms)")


class SyncBatch(BaseModel):
    """Batch of offline actions to sync."""

    device_id: str = Field(..., description="Unique device identifier")
    items: list[SyncItem] = Field(..., min_length=1, max_length=100)


class SyncResult(BaseModel):
    """Result for a single sync item."""

    client_id: str
    status: str  # success, failed, conflict
    server_id: str | None = None
    error: str | None = None


class SyncResponse(BaseModel):
    """Batch sync response."""

    device_id: str
    synced_at: str
    results: list[SyncResult]
    summary: dict[str, int]


# In-memory storage for research mode (replace with DB in production)
_sync_log: list[dict] = []


@router.post("/batch", response_model=SyncResponse)
async def sync_batch(batch: SyncBatch):
    """Process a batch of offline actions.

    This endpoint receives queued actions from offline clients,
    processes them, and returns results for each item.
    """
    results: list[SyncResult] = []

    for item in batch.items:
        try:
            # In production, route to appropriate handler based on endpoint
            # For research mode, we just log and return success
            server_id = str(uuid.uuid4())[:8]

            # Store in sync log
            _sync_log.append(
                {
                    "device_id": batch.device_id,
                    "client_id": item.client_id,
                    "endpoint": item.endpoint,
                    "method": item.method,
                    "payload": item.payload,
                    "timestamp": item.timestamp,
                    "server_id": server_id,
                    "synced_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                }
            )

            results.append(
                SyncResult(
                    client_id=item.client_id,
                    status="success",
                    server_id=server_id,
                )
            )

        except Exception as e:
            results.append(
                SyncResult(
                    client_id=item.client_id,
                    status="failed",
                    error=str(e),
                )
            )

    # Build summary
    summary = {
        "total": len(results),
        "success": sum(1 for r in results if r.status == "success"),
        "failed": sum(1 for r in results if r.status == "failed"),
        "conflict": sum(1 for r in results if r.status == "conflict"),
    }

    return SyncResponse(
        device_id=batch.device_id,
        synced_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        results=results,
        summary=summary,
    )


@router.get("/history/{device_id}")
async def get_sync_history(device_id: str, limit: int = 50):
    """Get sync history for a device."""
    device_entries = [entry for entry in _sync_log if entry["device_id"] == device_id][:limit]

    return {
        "device_id": device_id,
        "count": len(device_entries),
        "entries": device_entries,
    }


@router.get("/stats")
async def sync_stats():
    """Get sync system statistics."""
    return {
        "total_syncs": len(_sync_log),
        "unique_devices": len({e["device_id"] for e in _sync_log}),
        "last_sync": _sync_log[-1]["synced_at"] if _sync_log else None,
    }
