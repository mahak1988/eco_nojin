"""
Water Signature API Router
===========================================

Water signature summary for the F0 dashboard.

Endpoints:
    - GET /api/v1/water-signature/summary - water signature summary

Backend Gap: no ``WaterSignature`` domain model exists anywhere under
``services/`` or ``engine/`` (grep 2026-10-07: zero hits). This route
answers an explicit ``status=no_data`` envelope naming the gap instead of
fabricating rainfall, area or quality figures — masterprumpt.md بند ۸۰ wants
the unavailable state visible and بند ۷۸ forbids a fake backend.

Author: Eco Nojin Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/water-signature", tags=["water"])

#: The registry row that tracks the missing domain model.
GAP_ID = "BG-027"


@router.get("/summary", summary="Get water signature summary")
async def get_water_signature_summary(
    region: str | None = Query(
        None, description="Filter by region (province, city, village)"
    ),
):
    """
    Water signature summary — NOT YET BACKED BY A DOMAIN MODEL (BG-027).

    Returns an explicit ``no_data`` envelope naming the gap. It never invents
    rainfall, area or water-quality numbers; when the domain model lands this
    handler is the single place that changes.
    """
    logger.info("water-signature/summary served as no_data (region=%s)", region)
    return {
        "status": "no_data",
        "reason": f"water signature domain model not implemented ({GAP_ID})",
        "data": {},
        "timestamp": datetime.now(UTC).isoformat(),
    }
