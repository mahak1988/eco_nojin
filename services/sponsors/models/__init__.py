"""Sponsorship data model.

A sponsorship is a *service-level agreement with a named funder*, not an ad
placement. The distinction is the whole point of the design:

* the platform never serves programmatic advertising, and there is no ad
  network, no third-party SDK and no behavioural targeting anywhere in this
  model;
* every placement is contextual to a page and permanently labelled, because
  the evidence on native advertising is that transparency and conspicuous
  disclosure are the primary moderating factors;
* the value is the relationship, not the impression. A sponsor pays for a
  named, auditable role in a public restoration record.

Design constraints enforced in code, not just documented here:
* `sponsorships` carries no per-impression or per-view field, so engagement
  cannot be reported or optimised against a sponsor.
* `disclosure_required` defaults to True and activation refuses to serve
  without a disclosure string.
* the money goes to the project, not the farmer: the ecosystem fraction is a
  liability held for restoration, not revenue.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    Index,
    Numeric,
    String,
    Text,
)

from database.base import Base


class SponsorTier(StrEnum):
    #: A single page. Cheapest, lowest visibility commitment.
    PAGE = "page"
    #: A whole service area, named in its header.
    SECTION = "section"
    #: A tool, named in its footer.
    TOOL = "tool"
    #: A named region or community, acknowledged in the restoration record.
    DISTRICT = "district"
    #: Multi-site, multi-year, with a report slot.
    FOUNDING = "founding"


class SponsorshipStatus(StrEnum):
    #: Negotiating. Not visible publicly.
    PROSPECT = "prospect"
    #: Signed, not yet live.
    CONTRACTED = "contracted"
    #: Live. Eligible to appear in the slot.
    ACTIVE = "active"
    #: Paused by either side. Not served.
    SUSPENDED = "suspended"
    #: Ran to term.
    ENDED = "ended"
    #: Withdrawn. Kept as a record, because a sponsor removed for harming
    #: trust must stay visible as having existed.
    TERMINATED = "terminated"


class SlotPlacement(StrEnum):
    PUBLIC_SERVICES = "public_services"
    PUBLIC_AUDIENCES = "public_audiences"
    TOOL_FOOTER = "tool_footer"


class Sponsorship(Base):
    __tablename__ = "sponsorships"
    __table_args__ = (
        Index("idx_sponsorship_status", "status"),
        Index("idx_sponsorship_placement", "placement"),
        Index("idx_sponsorship_sponsor_name", "sponsor_name"),
        Index("idx_sponsorship_active_lookup", "status", "placement", "ends_on"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # --- Identity -------------------------------------------------------- #
    sponsor_name = Column(String(200), nullable=False, index=True)
    #: Persian name, used when the rendering locale is fa.
    sponsor_name_fa = Column(String(200), nullable=True)
    sponsor_url = Column(String(500), nullable=False)
    logo_url = Column(String(500), nullable=True)
    #: What the money funded, in one short line. A blank tagline is better
    #: than a vague one, so this is nullable rather than default "".
    tagline = Column(String(200), nullable=True)
    tagline_fa = Column(String(200), nullable=True)

    # --- Terms ------------------------------------------------------------ #
    tier = Column(SQLEnum(SponsorTier), nullable=False, default=SponsorTier.PAGE)
    status = Column(SQLEnum(SponsorshipStatus), default=SponsorshipStatus.PROSPECT, index=True)
    placement = Column(SQLEnum(SlotPlacement), nullable=False)

    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=False)

    # --- Disclosure and integrity ----------------------------------------- #
    #: A sponsor that funded the project itself, or one of its revenue lines.
    #: Both are displayed differently in the disclosure string.
    is_project_funder = Column(Boolean, default=False, index=True)
    is_revenue_source_funder = Column(Boolean, default=False)
    #: Cannot be waived. See services/sponsors/policy.py.
    #:
    #: nullable=False is load-bearing. SQLAlchemy applies a Column default on
    #: INSERT rather than on construction, so an in-memory object can read
    #: None; a null in the row would let an unlabelled slot exist through any
    #: write path that bypasses the service.
    disclosure_required = Column(
        Boolean, nullable=False, server_default="1", default=True, index=True
    )
    #: Last date the sponsor's environmental claims were re-attested, and by
    #: whom. Gates activation: see services/sponsors/service.py.
    green_claims_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    green_claims_attested_by = Column(String(120), nullable=True)

    internal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def is_live(self, today: date | None = None) -> bool:
        """Whether this sponsorship may be served in a slot right now."""
        if self.status is not SponsorshipStatus.ACTIVE:
            return False
        day = today or date.today()
        return self.starts_on <= day <= self.ends_on
