"""Real-time events via Server-Sent Events (SSE) for live dashboard updates."""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import AsyncGenerator
import asyncio
import json
import logging

from database.hub import hub
from database.models import ModelRun, IntOutboxEvent
from engine.hydroma.config.settings import get_settings

logger = logging.getLogger("econojin.api.realtime")

router = APIRouter(prefix="/api/v1/realtime", tags=["realtime"])


def get_db():
    with hub.get_session() as session:
        yield session


async def event_generator(
    request: Request,
    db: Session,
    user_key: str,
    event_types: list[str],
    interval: float = 2.0,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for subscribed event types."""
    last_model_run_id = 0
    last_outbox_count = 0
    request_id = request.headers.get("X-Request-ID", "unknown")

    try:
        while True:
            if await request.is_disconnected():
                logger.info(
                    "SSE client disconnected",
                    extra={"request_id": request_id, "user_key": user_key},
                )
                break

            events = []

            # Check for new model runs (if subscribed)
            if "model_runs" in event_types:
                new_runs = (
                    db.execute(
                        select(ModelRun)
                        .where(ModelRun.user_key == user_key)
                        .where(ModelRun.id > last_model_run_id)
                        .order_by(ModelRun.id.desc())
                        .limit(10)
                    )
                    .scalars()
                    .all()
                )

                if new_runs:
                    last_model_run_id = new_runs[0].id
                    for run in new_runs:
                        events.append(
                            {
                                "type": "model_run",
                                "data": {
                                    "id": run.id,
                                    "model_id": run.model_id,
                                    "title": run.title,
                                    "shared": run.shared,
                                    "created_at": run.created_at.isoformat()
                                    if run.created_at
                                    else None,
                                },
                            }
                        )

            # Check for sync status changes (if subscribed)
            if "sync_status" in event_types:
                pending_count = len(
                    db.execute(select(IntOutboxEvent).where(IntOutboxEvent.processed_at.is_(None)))
                    .scalars()
                    .all()
                )

                if pending_count != last_outbox_count:
                    last_outbox_count = pending_count
                    events.append({"type": "sync_status", "data": {"pending_count": pending_count}})

            # Send events if any
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"

            # Heartbeat to keep connection alive
            yield ": heartbeat\n\n"

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info("SSE stream cancelled", extra={"request_id": request_id, "user_key": user_key})
    except Exception as e:
        logger.error(
            "SSE error", extra={"request_id": request_id, "user_key": user_key, "error": str(e)}
        )
        yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"


@router.get("/stream")
async def sse_stream(
    request: Request,
    user_key: str = None,
    events: str = "model_runs,sync_status",
    interval: float = 2.0,
    db: Session = Depends(get_db),
):
    """SSE endpoint for real-time updates.

    Query params:
    - user_key: Anonymous user key (required for production, auto-generated for dev)
    - events: Comma-separated list of event types (model_runs, sync_status)
    - interval: Polling interval in seconds (default 2.0)
    """
    settings = get_settings()

    # Feature flag check
    if not settings.enable_realtime_sse:
        raise HTTPException(status_code=503, detail="Realtime SSE disabled via feature flag")

    # Generate user_key if not provided (for development)
    if not user_key:
        import uuid
        user_key = f"dev-{uuid.uuid4().hex[:16]}"
        logger.info("Auto-generated user_key for development", extra={"user_key": user_key})

    # Validate user_key format (skip for auto-generated dev keys)
    if not user_key.startswith("dev-"):
        import re
        if not re.match(r"^[A-Za-z0-9_-]{8,64}$", user_key):
            raise HTTPException(status_code=400, detail="Invalid user key format")

    event_list = [e.strip() for e in events.split(",")]
    valid_events = {"model_runs", "sync_status"}
    event_list = [e for e in event_list if e in valid_events]

    if not event_list:
        event_list = ["model_runs", "sync_status"]

    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.info(
        "SSE stream started",
        extra={"request_id": request_id, "user_key": user_key, "events": event_list},
    )

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable nginx buffering
    }

    return StreamingResponse(
        event_generator(request, db, user_key, event_list, interval),
        headers=headers,
        media_type="text/event-stream",
    )


@router.get("/health")
async def realtime_health():
    """Health check for realtime endpoint."""
    settings = get_settings()
    return {
        "status": "ok" if settings.enable_realtime_sse else "disabled",
        "service": "realtime-sse",
        "enabled": settings.enable_realtime_sse,
    }
