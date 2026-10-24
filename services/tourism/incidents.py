"""P8 — refunds, incidents, and complaints: the follow-up entities the proposal named.

``docs/project/TOURISM-ENTITY-MODEL-DECISION.md`` recommended departures first and
refunds/incidents as the follow-up. This module is that follow-up:

* a **refund** is a request against a booking that moves through review and,
  when approved, is *settled* through the existing escrow refund path — the
  money never moves here, only the record and the settlement reference;
* an **incident** is a report against a departure (weather, injury, route
  closure) with a severity, and it can *block* further bookings on that
  departure until it is resolved — a safety brake, not a note;
* a **complaint** is a customer-service issue against a tour/guide/booking
  (misrepresentation, guide behavior, quality, billing dispute) that follows
  a review/resolution workflow but does not block operations.

None of these entities can be created twice against the same target for the
same open case, and none is silently auto-approved.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)

from database.base import Base


class RefundStatus(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SAFETY = "safety"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class ComplaintCategory(StrEnum):
    """Category of a tourism complaint."""
    GUIDE_BEHAVIOR = "guide_behavior"
    QUALITY = "quality"
    MISREPRESENTATION = "misrepresentation"
    BILLING = "billing"
    SAFETY_CONCERN = "safety_concern"
    OTHER = "other"


class ComplaintStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class TourRefund(Base):
    """A refund request against one booking. The money moves in finance."""

    __tablename__ = "tourism_refunds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booking_id = Column(
        String(36), ForeignKey("tourism_bookings.id"), nullable=False, index=True
    )
    requested_by = Column(String(36), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="IRR")
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default=RefundStatus.REQUESTED.value, index=True)
    reviewed_by = Column(String(36), nullable=True)
    review_note = Column(Text, nullable=True)
    #: The settlement reference once the money actually moved (finance/escrow).
    settlement_ref = Column(String(120), nullable=True)
    requested_at = Column(DateTime, default=lambda: datetime.now(UTC))
    reviewed_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)


class TourIncident(Base):
    """An incident on a departure; a safety incident blocks new bookings."""

    __tablename__ = "tourism_incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    departure_id = Column(
        String(36), ForeignKey("tourism_departures.id"), nullable=False, index=True
    )
    reported_by = Column(String(36), nullable=False)
    severity = Column(String(20), nullable=False, default=IncidentSeverity.LOW.value)
    status = Column(String(20), nullable=False, default=IncidentStatus.OPEN.value, index=True)
    summary = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    reported_at = Column(DateTime, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True)

    @property
    def blocks_bookings(self) -> bool:
        return self.severity == IncidentSeverity.SAFETY.value and (
            self.status != IncidentStatus.RESOLVED.value
        )


class TourComplaint(Base):
    """A customer-service complaint against a tour/guide/booking.

    Unlike incidents (safety), complaints are service-quality issues:
    guide behavior, quality, misrepresentation, billing, etc.
    They follow a review/resolution workflow but do not block operations.
    """

    __tablename__ = "tourism_complaints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booking_id = Column(
        String(36), ForeignKey("tourism_bookings.id"), nullable=False, index=True
    )
    guide_id = Column(
        String(36), ForeignKey("tourism_guides.id"), nullable=True, index=True
    )
    tour_id = Column(
        String(36), ForeignKey("tourism_tours.id"), nullable=True, index=True
    )
    filed_by = Column(String(36), nullable=False)  # guest who filed
    category = Column(String(30), nullable=False, default=ComplaintCategory.OTHER.value)
    severity = Column(String(20), nullable=False, default="medium")  # low/medium/high
    status = Column(String(20), nullable=False, default=ComplaintStatus.OPEN.value, index=True)
    summary = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    assigned_to = Column(String(36), nullable=True)  # reviewer/approver
    filed_at = Column(DateTime, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True)