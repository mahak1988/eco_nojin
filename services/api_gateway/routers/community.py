"""
Community API Router
===========================================

Community participation data for the F0 dashboard and business pages.

Endpoints:
    - GET /api/v1/community/participants - event participation counts
    - GET /api/v1/community/people       - public entrepreneur profiles

Data sources (existing tables, no new schema):
    - ``village_events`` / ``village_event_registrations`` (participants)
    - ``entrepreneur_profiles``                            (people)

Authorization: public read, mirroring the already-public
``GET /api/v1/marketplace/villages/entrepreneurs`` surface in ``village_hub.py``.
No user ids or personal data are exposed: ``people`` answers with the public
profile columns only (skills, village, availability, experience).

Honesty (S-HONEST / masterprumpt.md بند ۸۰): a failed query is logged and
re-raised — never swallowed into an empty collection. An empty store answers
``status=no_data`` with measured zeros, not a success claim.

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
from services.marketplace.models.village_hub import (
    EntrepreneurProfile,
    VillageEvent,
    VillageEventRegistration,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/community", tags=["community"])


async def _get_db():
    async with hub.get_async_session() as session:
        yield session


@router.get("/participants", summary="Community participation counts")
async def list_participants(
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum event rows to return")] = 50,
    db: Annotated[AsyncSession, Depends(_get_db)] = None,
):
    """
    Participation counts from real event registrations (cross-village).

    Returns aggregate counts plus a per-event breakdown. No user identifiers
    are exposed — participation is reported as counts only.
    """
    try:
        total = (
            await db.execute(select(func.count(VillageEventRegistration.id)))
        ).scalar_one()
        confirmed = (
            await db.execute(
                select(func.count(VillageEventRegistration.id)).where(
                    VillageEventRegistration.status == "confirmed"
                )
            )
        ).scalar_one()
        rows = (
            await db.execute(
                select(
                    VillageEvent.id,
                    VillageEvent.title,
                    func.count(VillageEventRegistration.id),
                )
                .join(
                    VillageEventRegistration,
                    VillageEventRegistration.event_id == VillageEvent.id,
                )
                .group_by(VillageEvent.id, VillageEvent.title)
                .order_by(func.count(VillageEventRegistration.id).desc())
                .limit(limit)
            )
        ).all()
    except Exception:
        logger.exception("community/participants query failed")
        raise

    status_value = "ok" if total else "no_data"
    return {
        "status": status_value,
        "data": {
            "total_registrations": int(total),
            "confirmed": int(confirmed),
            "pending": int(total - confirmed),
            "by_event": [
                {"event_id": row[0], "title": row[1], "registrations": int(row[2])}
                for row in rows
            ],
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/people", summary="Public community profiles")
async def list_people(
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum profiles to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    db: Annotated[AsyncSession, Depends(_get_db)] = None,
):
    """
    Public community profiles (entrepreneur profiles — human capital data).

    Only the publicly-shaped columns are exposed; ``user_id`` and contact data
    stay behind the authenticated ``/entrepreneurs/me`` route in village_hub.
    """
    try:
        total = (
            await db.execute(select(func.count(EntrepreneurProfile.id)))
        ).scalar_one()
        rows = (
            await db.execute(
                select(EntrepreneurProfile)
                .order_by(EntrepreneurProfile.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
    except Exception:
        logger.exception("community/people query failed")
        raise

    items = [
        {
            "id": profile.id,
            "village_id": profile.village_id,
            "skills": list(profile.skills or []),
            "experience_years": profile.experience_years,
            "is_available": bool(profile.is_available),
            "joined_at": profile.created_at.isoformat() if profile.created_at else None,
        }
        for profile in rows
    ]
    status_value = "ok" if items else "no_data"
    return {
        "status": status_value,
        "total": int(total),
        "items": items,
        "timestamp": datetime.now(UTC).isoformat(),
    }
