"""P8 — the refund review flow and the incident safety brake.

Approvals are never automatic: a refund moves ``requested → approved`` only
when a reviewer acts, and ``approved → settled`` only with a finance settlement
reference. A safety-severity incident blocks new bookings on its departure until
it is resolved.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.tourism.departures import DepartureStatus, TourDeparture
from services.tourism.incidents import (
    IncidentSeverity,
    IncidentStatus,
    RefundStatus,
    TourIncident,
    TourRefund,
)
from services.tourism.models import TourismBooking


class RefundError(ValueError):
    """A forbidden refund or incident transition."""


class TourismSafetyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # refunds
    # ------------------------------------------------------------------

    async def request_refund(
        self,
        *,
        booking_id: str,
        requested_by: str,
        amount: Decimal,
        reason: str,
    ) -> TourRefund:
        booking = (
            await self.db.execute(
                select(TourismBooking).where(TourismBooking.id == booking_id)
            )
        ).scalar_one_or_none()
        if booking is None:
            raise RefundError(f"booking not found: {booking_id}")
        # A refund is a request against the guest's own booking, at most for
        # what they paid — otherwise any caller could file refunds against
        # other guests' bookings with amounts of their choosing.
        if str(booking.guest_id) != str(requested_by):
            raise RefundError("a refund can only be requested by the booking's guest")
        existing = await self.db.execute(
            select(TourRefund).where(
                TourRefund.booking_id == booking_id,
                TourRefund.status.in_(
                    [RefundStatus.REQUESTED.value, RefundStatus.APPROVED.value]
                ),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise RefundError("this booking already has an open refund request")
        if amount <= 0:
            raise RefundError("a refund amount must be positive")
        if amount > Decimal(str(booking.total)):
            raise RefundError(
                f"a refund cannot exceed the booking total ({booking.total})"
            )
        refund = TourRefund(
            booking_id=booking_id,
            requested_by=requested_by,
            amount=amount,
            currency=booking.currency or "IRR",
            reason=reason,
        )
        self.db.add(refund)
        await self.db.commit()
        return refund

    async def review_refund(
        self, refund_id: str, *, reviewer_id: str, approve: bool, note: str | None = None
    ) -> TourRefund:
        refund = await self._require_refund(refund_id)
        if refund.status != RefundStatus.REQUESTED.value:
            raise RefundError(f"the refund is {refund.status}, not requested")
        refund.status = (
            RefundStatus.APPROVED.value if approve else RefundStatus.REJECTED.value
        )
        refund.reviewed_by = reviewer_id
        refund.reviewed_at = datetime.now(UTC)
        refund.review_note = note
        await self.db.commit()
        return refund

    async def settle_refund(self, refund_id: str, *, settlement_ref: str) -> TourRefund:
        """Record the finance settlement of an approved refund.

        A booking is charged in the booking's currency (IRR). That money is
        **not** in the ECO wallet, so this method must not move ECO: doing so
        paid a rial amount out of an ECO wallet -- a currency mismatch that
        also made the platform admin's personal wallet the source of the refund
        money, and that failed outright for any refund under 10 ECO.

        Settlement books the refund against the double-entry ledger in the
        refund's currency and records the finance reference for audit
        traceability. The cash payout itself belongs to the finance plane's
        payout rail.
        """
        refund = await self._require_refund(refund_id)
        if refund.status != RefundStatus.APPROVED.value:
            raise RefundError("only an approved refund can be settled")
        if not settlement_ref:
            raise RefundError("a settled refund must name its finance settlement")

        refund.status = RefundStatus.SETTLED.value
        refund.settlement_ref = settlement_ref
        refund.settled_at = datetime.now(UTC)

        await self._post_refund_journal(refund, settlement_ref)

        await self.db.commit()
        await self.db.refresh(refund)
        return refund

    async def _post_refund_journal(self, refund: TourRefund, settlement_ref: str) -> None:
        """Book a settled refund against the double-entry ledger.

        The refund leaves the platform's cash and is an operating cost of the
        platform, in the currency the booking was charged in. The batch is
        traceable by ``reference_type="tourism_refund"`` and the refund id.
        """
        from services.finance.chart_of_accounts import (
            ECO_CASH,
            ECO_OPERATING_EXPENSE,
            ensure_account,
            get_account_spec,
        )
        from services.finance.ledger_service import LedgerService

        amount = Decimal(str(refund.amount or 0))
        if amount <= 0:
            raise RefundError("a refund must settle a positive amount")
        asset = str(refund.currency or "IRR")

        for code in (ECO_OPERATING_EXPENSE, ECO_CASH):
            spec = get_account_spec(code)
            if spec is None:
                continue
            await ensure_account(
                self.db,
                code=spec.code,
                name=spec.name,
                type=spec.type,
                asset=spec.asset,
                currency=spec.currency,
                parent_code=spec.parent_code,
                description=spec.description,
            )

        ledger = LedgerService(self.db)
        await ledger.create_journal_batch(
            reference_type="tourism_refund",
            reference_id=str(refund.id),
            description=f"Tourism refund settled via {settlement_ref}",
            created_by=refund.reviewed_by,
            entries=[
                {
                    "account_id": ECO_OPERATING_EXPENSE,
                    "entry_type": "debit",
                    "asset": asset,
                    "amount": str(amount),
                    "description": f"Refund for booking {refund.booking_id}",
                },
                {
                    "account_id": ECO_CASH,
                    "entry_type": "credit",
                    "asset": asset,
                    "amount": str(amount),
                    "description": f"Refund payout {settlement_ref}",
                },
            ],
        )

    async def cancel_refund(self, refund_id: str, *, actor_id: str) -> TourRefund:
        refund = await self._require_refund(refund_id)
        if refund.status in (RefundStatus.SETTLED.value, RefundStatus.CANCELLED.value):
            raise RefundError(f"a {refund.status} refund cannot be cancelled")
        refund.status = RefundStatus.CANCELLED.value
        refund.reviewed_by = actor_id
        await self.db.commit()
        return refund

    # ------------------------------------------------------------------
    # incidents
    # ------------------------------------------------------------------

    async def report_incident(
        self,
        *,
        departure_id: str,
        reported_by: str,
        summary: str,
        severity: str = IncidentSeverity.LOW.value,
    ) -> TourIncident:
        if severity not in {s.value for s in IncidentSeverity}:
            raise RefundError(f"unknown severity: {severity}")
        departure = await self._require_departure(departure_id)
        incident = TourIncident(
            departure_id=departure_id,
            reported_by=reported_by,
            severity=severity,
            summary=summary,
        )
        self.db.add(incident)
        await self.db.flush()
        # The safety brake: a safety-severity incident closes the departure to
        # new bookings immediately — a note would be worse than useless here.
        if incident.blocks_bookings and departure.status != DepartureStatus.CANCELLED.value:
            departure.status = DepartureStatus.CLOSED.value
        await self.db.commit()
        return incident

    async def resolve_incident(
        self, incident_id: str, *, resolver_id: str, resolution: str
    ) -> TourIncident:
        incident = await self._require_incident(incident_id)
        if incident.status == IncidentStatus.RESOLVED.value:
            raise RefundError("the incident is already resolved")
        # Read the brake flag BEFORE the status change: ``blocks_bookings`` is
        # false for a resolved incident by definition.
        was_blocking = incident.blocks_bookings
        incident.status = IncidentStatus.RESOLVED.value
        incident.resolution = resolution
        incident.resolved_at = datetime.now(UTC)
        # The brake the incident wrote is lifted with it: a departure closed by
        # a safety incident re-opens once no blocking incident remains and it
        # is not at capacity. A cancelled departure stays cancelled.
        departure = await self._require_departure(incident.departure_id)
        if (
            was_blocking
            and departure.status == DepartureStatus.CLOSED.value
            and not await self.departure_is_blocked(incident.departure_id)
            and departure.booked < departure.capacity
        ):
            departure.status = DepartureStatus.OPEN.value
        await self.db.commit()
        return incident

    async def departure_is_blocked(self, departure_id: str) -> bool:
        incidents = (
            await self.db.execute(
                select(TourIncident).where(TourIncident.departure_id == departure_id)
            )
        ).scalars()
        return any(incident.blocks_bookings for incident in incidents)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    async def _require_refund(self, refund_id: str) -> TourRefund:
        refund = (
            await self.db.execute(select(TourRefund).where(TourRefund.id == refund_id))
        ).scalar_one_or_none()
        if refund is None:
            raise RefundError(f"refund not found: {refund_id}")
        return refund

    async def _require_departure(self, departure_id: str) -> TourDeparture:
        departure = (
            await self.db.execute(
                select(TourDeparture).where(TourDeparture.id == departure_id)
            )
        ).scalar_one_or_none()
        if departure is None:
            raise RefundError(f"departure not found: {departure_id}")
        return departure

    async def _require_incident(self, incident_id: str) -> TourIncident:
        incident = (
            await self.db.execute(
                select(TourIncident).where(TourIncident.id == incident_id)
            )
        ).scalar_one_or_none()
        if incident is None:
            raise RefundError(f"incident not found: {incident_id}")
        return incident
