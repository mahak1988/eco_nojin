"""
Culture API Router
===========================================

Cultural events for the F0 dashboard and business pages.

Endpoints:
    - GET /api/v1/culture/events - cultural events (cross-village)

Data source (existing table, no new schema): ``village_events`` — the same
store ``village_hub.py`` writes through ``POST
/api/v1/marketplace/villages/{village_id}/events``.

Honesty (S-HONEST / masterprumpt.md بند ۸۰): a failed query is logged and
re-raised — never swallowed into an empty collection. An empty store answers
``status=no_data``, not a success claim.

Author: Eco Nojin Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.marketplace.models.village_hub import VillageEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/culture", tags=["culture"])


async def _get_db():
    async with hub.get_async_session() as session:
        yield session


@router.get("/events", summary="List cultural events")
async def list_events(
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum events to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    db: Annotated[AsyncSession, Depends(_get_db)] = None,
):
    """
    Cultural events across villages, newest start date first.

    Returns the public event columns only (no creator, no payment data).
    """
    try:
        total = (await db.execute(select(func.count(VillageEvent.id)))).scalar_one()
        rows = (
            await db.execute(
                select(VillageEvent)
                .order_by(VillageEvent.start_date.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
    except Exception:
        logger.exception("culture/events query failed")
        raise

    items = [
        {
            "id": event.id,
            "village_id": event.village_id,
            "title": event.title,
            "title_en": event.title_en,
            "event_type": event.event_type,
            "start_date": event.start_date.isoformat() if event.start_date else None,
            "end_date": event.end_date.isoformat() if event.end_date else None,
            "location": event.location,
            "status": event.status,
            "max_participants": event.max_participants,
        }
        for event in rows
    ]
    status_value = "ok" if items else "no_data"
    return {
        "status": status_value,
        "total": int(total),
        "items": items,
        "timestamp": datetime.now(UTC).isoformat(),
    }
