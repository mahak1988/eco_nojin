"""P8 — tour departures: dates and per-departure capacity (the additive step).

``docs/project/TOURISM-ENTITY-MODEL-DECISION.md`` recommends the additive path:
the 3-entity model keeps working, and departures make *dates* expressible —
a tour without departures cannot be scheduled, and no per-departure capacity or
refund flow can be tested against a real instance. Incidents and refunds remain
the 9-entity decision's follow-up.

A departure never exceeds the tour's ecological capacity: the smaller of the two
wins, so a per-departure cap can only be tighter than the tour's own limit.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from database.base import Base


class DepartureStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TourDeparture(Base):
    """One dated instance of a tour, with its own capacity."""

    __tablename__ = "tourism_departures"
    __table_args__ = (
        UniqueConstraint("tour_id", "departure_date", name="uq_departure_tour_date"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tour_id = Column(String(36), ForeignKey("tourism_tours.id"), nullable=False, index=True)
    departure_date = Column(Date, nullable=False, index=True)
    #: The effective cap: the smaller of the departure's own capacity and the
    #: tour's ecological capacity. Never larger than the tour's limit.
    capacity = Column(Integer, nullable=False)
    booked = Column(Integer, nullable=False, default=0)
    price_override = Column(Numeric(12, 2), nullable=True)
    status = Column(String(20), nullable=False, default=DepartureStatus.OPEN.value)
    village_id = Column(String(100), nullable=True)
    #: Why the departure was cancelled — the only audit trail of the reason;
    #: NULL while the departure is open or closed-but-running.
    cancelled_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def remaining(self) -> int:
        return max(self.capacity - self.booked, 0)

    def take_seats(self, count: int) -> None:
        """Consume ``count`` seats; close the departure when it fills up.

        The one seat rule for a departure — shared by ``TourismService``
        (booking) and ``DepartureService`` — so a departure's ledger and its
        open/closed state cannot drift between the two services.
        """
        if self.status != DepartureStatus.OPEN.value:
            raise ValueError(
                f"departure is {self.status} (برگزاری {self.status} است)"
            )
        if count > self.remaining():
            raise ValueError(
                f"departure has {self.remaining()} seats left, {count} requested "
                f"(ظرفیت این برگزاری تکمیل است. فقط {self.remaining()} نفر باقی مانده)"
            )
        self.booked += count
        if self.booked >= self.capacity:
            self.status = DepartureStatus.CLOSED.value

    def release_seats(self, count: int, *, may_reopen: bool = True) -> None:
        """Free ``count`` seats; re-open a departure closed only by fullness.

        ``may_reopen`` is False while a safety incident still blocks the
        departure: the seats come back, but the brake stays on.
        """
        if self.status == DepartureStatus.CANCELLED.value:
            return
        self.booked = max(0, self.booked - count)
        if (
            may_reopen
            and self.status == DepartureStatus.CLOSED.value
            and self.booked < self.capacity
        ):
            self.status = DepartureStatus.OPEN.value
