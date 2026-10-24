"""
Nature API Router
===========================================

Ecosystem catalog for the F0 dashboard and business pages.

Endpoints:
    - GET /api/v1/nature/ecosystems - ecosystem catalog

Backend Gap: there is no ecosystem/biodiversity *catalogue* domain model
anywhere under ``services/`` or ``engine/``. The nearest module,
``services/ecosystem/service.py``, is the EcoCoin restoration-activity domain
(activities, evidence, trust scores) — not a catalogue of ecosystems, areas or
biodiversity scores — so the 2026-10-07 "zero hits" finding still holds for
what this route serves. This route therefore answers an explicit
``status=no_data`` envelope that names the gap (``reason`` carries the BG id)
instead of fabricating rows — masterprumpt.md بند ۸۰ (Frontend Consumption
Rule) wants the unavailable state visible, and بند ۷۸ forbids a fake backend.

Author: Eco Nojin Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nature", tags=["nature"])

#: The registry row that tracks the missing domain model.
GAP_ID = "BG-027"


@router.get("/ecosystems", summary="List ecosystems")
async def list_ecosystems(
    limit: int = Query(50, ge=1, le=200, description="Maximum ecosystems to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Ecosystem catalog — NOT YET BACKED BY A DOMAIN MODEL (BG-027).

    Returns an explicit ``no_data`` envelope naming the gap. It never invents
    ecosystems, areas or biodiversity scores; when the domain model lands this
    handler is the single place that changes.
    """
    logger.info("nature/ecosystems served as no_data (limit=%s, offset=%s)", limit, offset)
    return {
        "status": "no_data",
        "reason": f"ecosystem domain model not implemented ({GAP_ID})",
        "total": 0,
        "items": [],
        "timestamp": datetime.now(UTC).isoformat(),
    }
