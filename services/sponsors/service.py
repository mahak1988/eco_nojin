"""Sponsorship service.

Read path is deliberately dull: one query, one row, one JSON shape. The public
endpoint carries no user parameter of any kind, so behavioural targeting is
structurally impossible rather than merely forbidden.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.sponsors.models import (
    SlotPlacement,
    Sponsorship,
    SponsorshipStatus,
)
from services.sponsors.policy import (
    EXPIRY_GRACE_DAYS,
    PolicyViolation,
    assert_category_allowed,
    assert_placement_allowed,
    assert_platform_share_ok,
    disclosure_key,
)

logger = logging.getLogger(__name__)


class SponsorshipNotFound(LookupError):
    pass


class SponsorshipService:
    """Query and lifecycle operations for sponsorships."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ #
    # Public read
    # ------------------------------------------------------------------ #

    def get_live_slot(
        self, placement: SlotPlacement, today: date | None = None
    ) -> Sponsorship | None:
        """The one sponsorship that may be served at this placement, or None.

        Ordering is deterministic so that a duplicate never produces a
        different answer between requests.
        """
        day = today or date.today()
        stmt = (
            select(Sponsorship)
            .where(
                Sponsorship.status == SponsorshipStatus.ACTIVE,
                Sponsorship.placement == placement,
                Sponsorship.starts_on <= day,
                Sponsorship.ends_on >= day - timedelta(days=EXPIRY_GRACE_DAYS),
            )
            .order_by(Sponsorship.tier, Sponsorship.created_at)
            .limit(2)
        )
        rows = list(self.db.execute(stmt).scalars())
        if not rows:
            return None
        if len(rows) > 1:
            # More than one live sponsor at a placement breaks
            # MAX_SPONSORS_PER_PLACEMENT. Serving the first would hide it.
            logger.error(
                "Sponsorship policy violation: %d live sponsors at %s; serving "
                "none until resolved",
                len(rows),
                placement,
            )
            return None
        return rows[0]

    def list_public(self, today: date | None = None) -> list[Sponsorship]:
        """Every current sponsor, for the transparency page."""
        day = today or date.today()
        stmt = (
            select(Sponsorship)
            .where(
                Sponsorship.status.in_(
                    [SponsorshipStatus.ACTIVE, SponsorshipStatus.SUSPENDED]
                ),
                Sponsorship.starts_on <= day,
                Sponsorship.ends_on >= day,
            )
            .order_by(Sponsorship.tier, Sponsorship.created_at)
        )
        return list(self.db.execute(stmt).scalars())

    @staticmethod
    def slot_payload(sponsor: Sponsorship | None) -> dict[str, Any]:
        """Public slot shape.

        No user identifier, no referrer, no impression counter. The response is
        cacheable and identical for every reader, which is what makes targeted
        placement impossible to add later by accident.
        """
        if sponsor is None:
            return {"present": False}
        return {
            "present": True,
            "disclosure": {
                "required": True,
                "template_key": disclosure_key(sponsor.sponsor_name),
            },
            "sponsor": {
                "name": sponsor.sponsor_name,
                "name_fa": sponsor.sponsor_name_fa,
                "url": sponsor.sponsor_url,
                "logo_url": sponsor.logo_url,
                "tagline": sponsor.tagline,
                "tagline_fa": sponsor.tagline_fa,
                "tier": str(sponsor.tier),
                "is_project_funder": bool(sponsor.is_project_funder),
            },
            "expires_on": sponsor.ends_on.isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Admin lifecycle
    # ------------------------------------------------------------------ #

    def create(self, **fields: Any) -> Sponsorship:
        assert_placement_allowed(fields.get("placement_path", ""))
        assert_category_allowed(fields.get("category"))
        assert_platform_share_ok(float(fields.get("platform_share", 0.0)))

        sponsor = Sponsorship(
            sponsor_name=fields["sponsor_name"],
            sponsor_name_fa=fields.get("sponsor_name_fa"),
            sponsor_url=fields["sponsor_url"],
            logo_url=fields.get("logo_url"),
            tagline=fields.get("tagline"),
            tagline_fa=fields.get("tagline_fa"),
            tier=fields.get("tier"),
            status=SponsorshipStatus.PROSPECT,
            placement=fields["placement"],
            amount=Decimal(str(fields["amount"])),
            currency=fields.get("currency", "USD"),
            starts_on=fields["starts_on"],
            ends_on=fields["ends_on"],
            is_project_funder=bool(fields.get("is_project_funder", False)),
            is_revenue_source_funder=bool(
                fields.get("is_revenue_source_funder", False)
            ),
            disclosure_required=True,
            internal_notes=fields.get("internal_notes"),
        )
        self.db.add(sponsor)
        self.db.flush()
        return sponsor

    def activate(self, sponsor_id: str) -> Sponsorship:
        """Go live. Every gate here is a gate a moderator would want.

        The two refusals that matter most:
        * no green-claims attestation. A sponsor whose environmental claims
          have not been re-attested cannot be displayed next to our own.
        * `disclosure_required` cannot be cleared. A sponsor slot without a
          visible label is the failure mode this whole design exists to
          prevent, so it is refused rather than warned about.
        """
        sponsor = self.get(sponsor_id)
        if sponsor.disclosure_required is False:
            raise PolicyViolation(
                f"sponsorship {sponsor_id} has disclosure disabled. A slot "
                f"without a permanent label is not permitted."
            )
        if sponsor.green_claims_reviewed_at is None:
            raise PolicyViolation(
                f"sponsorship {sponsor_id} has no green-claims attestation. "
                f"Re-attest before activation; see services/sponsors/policy.py."
            )
        if sponsor.is_live():
            logger.info("Sponsorship %s is already live", sponsor_id)
            return sponsor

        clash = self.db.execute(
            select(Sponsorship.id).where(
                Sponsorship.placement == sponsor.placement,
                Sponsorship.status == SponsorshipStatus.ACTIVE,
                Sponsorship.id != sponsor.id,
            )
        ).first()
        if clash is not None:
            raise PolicyViolation(
                f"another sponsorship is already live at "
                f"{sponsor.placement}. Only one sponsor per placement."
            )

        sponsor.status = SponsorshipStatus.ACTIVE
        self.db.flush()
        logger.info("Sponsorship activated: %s (%s)", sponsor_id, sponsor.sponsor_name)
        return sponsor

    def suspend(self, sponsor_id: str, reason: str) -> Sponsorship:
        sponsor = self.get(sponsor_id)
        sponsor.status = SponsorshipStatus.SUSPENDED
        note = (sponsor.internal_notes or "").strip()
        sponsor.internal_notes = f"{note}\nsuspended: {reason}".strip()
        self.db.flush()
        return sponsor

    def terminate(self, sponsor_id: str, reason: str) -> Sponsorship:
        """Withdraw. The record is kept: a sponsor removed for harming trust
        must remain visible as having existed, and that history is published."""
        sponsor = self.get(sponsor_id)
        sponsor.status = SponsorshipStatus.TERMINATED
        note = (sponsor.internal_notes or "").strip()
        sponsor.internal_notes = f"{note}\nterminated: {reason}".strip()
        self.db.flush()
        return sponsor

    def record_green_review(self, sponsor_id: str, attested_by: str) -> Sponsorship:
        from datetime import datetime

        sponsor = self.get(sponsor_id)
        sponsor.green_claims_reviewed_at = datetime.now(UTC)
        sponsor.green_claims_attested_by = attested_by
        self.db.flush()
        return sponsor

    def get(self, sponsor_id: str) -> Sponsorship:
        sponsor = self.db.get(Sponsorship, sponsor_id)
        if sponsor is None:
            raise SponsorshipNotFound(sponsor_id)
        return sponsor
