"""Public sponsorship endpoints.

Design rule for this router: **no endpoint accepts a user identifier, a
visitor id, a referrer, or any behavioural input.** The slot response is
identical for every reader on a given day, which is what makes contextual
placement structurally impossible to convert into targeted placement later.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from services.sponsors.models import SlotPlacement
from services.sponsors.service import SponsorshipService

router = APIRouter(prefix="/api/v1/sponsors", tags=["Sponsors"])

#: Slot content changes only when a sponsorship is activated, suspended or
#: expires, so a short shared cache is safe and keeps the platform's
#: infrastructure cost down.
CACHE_CONTROL = "public, max-age=900"


def _get_db():
    from database.hub import hub

    with hub.get_session() as session:
        yield session


@router.get("/slot")
async def get_slot(
    placement: SlotPlacement = Query(SlotPlacement.PUBLIC_SERVICES),
):
    """The single sponsor permitted at this placement, or a negative answer.

    `present: false` with no surrounding markup is the expected state most of
    the time. The frontend must render nothing at all in that case, not an
    empty frame.
    """
    from database.hub import hub

    with hub.get_session() as session:
        sponsor = SponsorshipService(session).get_live_slot(placement)
        payload = SponsorshipService.slot_payload(sponsor)

    return JSONResponse(
        content=payload,
        headers={
            "Cache-Control": CACHE_CONTROL,
            # A slot must never be personalised, and this says so at the
            # protocol level so a future change has to be deliberate.
            "Vary": "Accept-Language",
        },
    )


@router.get("")
async def list_sponsors():
    """Full transparency list.

    The platform's claim is that sponsorship is disclosed, so the list is
    public and includes terminations with their reason. A sponsor that was
    removed for harming trust has no incentive to be quiet about it, which is
    the point.
    """
    from database.hub import hub

    with hub.get_session() as session:
        rows = SponsorshipService(session).list_public()
        payload = {
            "sponsors": [
                {
                    "name": s.sponsor_name,
                    "name_fa": s.sponsor_name_fa,
                    "url": s.sponsor_url,
                    "tagline": s.tagline,
                    "tagline_fa": s.tagline_fa,
                    "tier": str(s.tier),
                    "status": str(s.status),
                    "is_project_funder": bool(s.is_project_funder),
                    "is_revenue_source_funder": bool(s.is_revenue_source_funder),
                    "starts_on": s.starts_on.isoformat(),
                    "ends_on": s.ends_on.isoformat(),
                    "green_claims_reviewed_at": (
                        s.green_claims_reviewed_at.isoformat()
                        if s.green_claims_reviewed_at
                        else None
                    ),
                }
                for s in rows
            ],
            "policy": {
                "no_programmatic_advertising": True,
                "no_third_party_ad_sdk": True,
                "no_behavioural_targeting": True,
                "disclosure_is_permanent": True,
                "restricted_surfaces": [
                    "agronomic recommendation",
                    "checkout and settlement",
                    "low-bandwidth channels",
                ],
            },
        }

    return JSONResponse(content=payload, headers={"Cache-Control": CACHE_CONTROL})
