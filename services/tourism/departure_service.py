"""P8 — departures are additive: the tour plane is untouched.

Before this module a tour could not be scheduled, so per-departure capacity,
cancellation and (later) refunds had nothing to attach to. The booking flow
keeps working exactly as before for tours without departures; when a departure
is given, the booking consumes the departure's capacity instead of the tour's.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.tourism.departures import DepartureStatus, TourDeparture
from services.tourism.incidents import TourIncident
from services.tourism.models import TourismTour


class DepartureError(ValueError):
    """A forbidden departure transition."""


class DepartureService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_departure(
        self,
        *,
        tour_id: str,
        departure_date: date,
        capacity: int | None = None,
        price_override: Decimal | None = None,
        village_id: str | None = None,
    ) -> TourDeparture:
        tour = (
            await self.db.execute(select(TourismTour).where(TourismTour.id == tour_id))
        ).scalar_one_or_none()
        if tour is None:
            raise DepartureError(f"tour not found: {tour_id}")
        if departure_date <= datetime.now(UTC).date():
            raise DepartureError("a departure must be in the future")

        effective = capacity or tour.ecological_capacity or tour.max_participants
        if tour.ecological_capacity and effective > tour.ecological_capacity:
            raise DepartureError(
                f"departure capacity {effective} exceeds the tour's ecological "
                f"capacity {tour.ecological_capacity}"
            )
        if effective <= 0:
            raise DepartureError("a departure needs a positive capacity")

        existing = await self.db.execute(
            select(TourDeparture).where(
                TourDeparture.tour_id == tour_id,
                TourDeparture.departure_date == departure_date,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise DepartureError("this tour already departs on that date")

        departure = TourDeparture(
            tour_id=tour_id,
            departure_date=departure_date,
            capacity=effective,
            price_override=price_override,
            village_id=village_id,
        )
        self.db.add(departure)
        await self.db.commit()
        return departure

    async def close(self, departure_id: str) -> TourDeparture:
        departure = await self._require(departure_id)
        if departure.status == DepartureStatus.CANCELLED.value:
            raise DepartureError("a cancelled departure cannot be closed")
        departure.status = DepartureStatus.CLOSED.value
        await self.db.commit()
        return departure

    async def cancel(self, departure_id: str, *, reason: str) -> TourDeparture:
        departure = await self._require(departure_id)
        if departure.status == DepartureStatus.CANCELLED.value:
            return departure
        departure.status = DepartureStatus.CANCELLED.value
        # The reason is carried on the record so the cancellation is auditable;
        # refunds are the 9-entity decision's follow-up and do NOT happen here.
        departure.cancelled_reason = reason
        await self.db.commit()
        return departure

    async def consume(self, departure_id: str, participants: int) -> TourDeparture:
        """Reserve seats; refuse when the departure is full or not open.

        The seat rule itself lives on the model (``TourDeparture.take_seats``),
        shared with the booking path, so the two services cannot disagree
        about what "full" means.
        """
        departure = await self._require(departure_id)

        # Check for safety incidents that block bookings
        incident = await self._get_blocking_incident(departure.id)
        if incident:
            raise DepartureError(
                f"departure blocked by safety incident {incident.id}: {incident.summary}"
            )

        try:
            departure.take_seats(participants)
        except ValueError as exc:
            raise DepartureError(str(exc)) from exc
        await self.db.commit()
        return departure

    async def _get_blocking_incident(self, departure_id: str):
        """Return the first open SAFETY-severity incident for a departure, if any."""
        result = await self.db.execute(
            select(TourIncident).where(
                TourIncident.departure_id == departure_id,
                TourIncident.severity == "safety",
                TourIncident.status.in_(["open", "investigating"]),
            )
        )
        return result.scalar_one_or_none()

    async def _require(self, departure_id: str) -> TourDeparture:
        departure = (
            await self.db.execute(
                select(TourDeparture).where(TourDeparture.id == departure_id)
            )
        ).scalar_one_or_none()
        if departure is None:
            raise DepartureError(f"departure not found: {departure_id}")
        return departure
