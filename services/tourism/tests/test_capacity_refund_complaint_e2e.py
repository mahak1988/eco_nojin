"""E2E tests for tourism capacity/refund/complaint flows (B4).

These tests exercise the full lifecycle:
1. Capacity enforcement on departures (P8 scope)
2. Refund request → review → settlement
3. Complaint filing → review → resolution
4. Cross-entity interactions (booking with departure, refund on booking, complaint on booking)
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.tourism.departure_service import DepartureService
from services.tourism.departures import TourDeparture
from services.tourism.incidents import (
    ComplaintCategory,
    ComplaintStatus,
    IncidentSeverity,
    IncidentStatus,
    RefundStatus,
    TourComplaint,
    TourIncident,
)
from services.tourism.models import (
    TourismDifficultyLevel,
    TourismGuide,
    TourismTourType,
)
from services.tourism.safety_service import RefundError, TourismSafetyService
from services.tourism.service import TourismService
from services.village.models import CommunitySpace, CommunitySpaceKind, SpaceStatus


class TestTourismCapacityRefundComplaintE2E:
    """End-to-end tests for tourism capacity, refund, and complaint flows."""

    @pytest.fixture
    async def setup_tour(self, db_session: AsyncSession):
        """Create a verified guide, a tour, and a departure with capacity."""
        guide = TourismGuide(
            user_id=str(uuid4()),
            village_id="village_001",
            full_name="Test Guide",
            bio="Experienced guide",
            languages=["fa", "en"],
            specialties=["ecotourism"],
            license_number="LIC-001",
            is_verified=True,
        )
        db_session.add(guide)
        await db_session.commit()
        await db_session.refresh(guide)

        # Create admin user for refund settlement
        admin = User(
            id=str(uuid4()),
            email="admin@test.local",
            full_name="Test Admin",
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        await db_session.commit()

        # Create wallet for admin with sufficient balance
        from services.finance.wallet_service import WalletService
        wallet_service = WalletService(db_session)
        admin_wallet = await wallet_service._get_or_create_wallet(admin.id)
        admin_wallet.balance = Decimal("10000.00")
        await db_session.commit()

        # Create active CommunitySpace for the village (required for ecotourism)
        space = CommunitySpace(
            village_id="village_001",
            name="Test Community Space",
            kind=CommunitySpaceKind.VILLAGE.value,
            status=SpaceStatus.ACTIVE.value,
            region="Test Region",
            country="IR",
        )
        db_session.add(space)
        await db_session.commit()
        await db_session.refresh(space)

        # Use service to create tour (generates slug)
        service = TourismService(db_session)
        tour = await service.create_tour(
            guide_id=guide.id,
            village_id="village_001",
            title="Ecotourism Trek",
            tour_type=TourismTourType.ECOTOURISM,
            duration_hours=4,
            price_per_person=Decimal("100.00"),
            max_participants=10,
            min_participants=2,
            difficulty=TourismDifficultyLevel.MODERATE,
            ecological_capacity=10,
            is_regenerative=True,
        )
        # Activate the tour for testing
        tour.status = "active"
        db_session.add(tour)
        await db_session.commit()
        await db_session.refresh(tour)

        dep_service = DepartureService(db_session)
        departure = await dep_service.create_departure(
            tour_id=tour.id,
            departure_date=date.today() + timedelta(days=7),
            capacity=5,
            price_override=None,
            village_id="village_001",
        )
        await db_session.commit()
        await db_session.refresh(departure)

        return guide, tour, departure

    @pytest.fixture
    async def setup_booking(self, db_session: AsyncSession, setup_tour):
        guide, tour, departure = setup_tour

        guest_id = str(uuid4())
        service = TourismService(db_session)
        booking = await service.create_booking(
            tour_id=tour.id,
            guest_id=str(uuid4()),
            participants_count=3,
            tour_date=datetime.now(UTC) + timedelta(days=7),
            village_id="village_001",
            departure_id=departure.id,
            special_requests="Test booking",
            regenerative_commitment="Leave no trace",
        )
        await db_session.commit()
        await db_session.refresh(booking)

        return guide, tour, departure, booking

    async def test_capacity_enforcement_on_departure(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        assert departure.booked == 3
        assert departure.remaining() == 2

        service = TourismService(db_session)
        with pytest.raises(ValueError, match="capacity|ظرفیت|seats"):
            await service.create_booking(
                tour_id=tour.id,
                guest_id=str(uuid4()),
                participants_count=5,
                tour_date=datetime.now(UTC) + timedelta(days=7),
                village_id="village_001",
                departure_id=departure.id,
            )

    async def test_refund_request_review_settle_flow(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        safety_service = TourismSafetyService(db_session)

        refund = await safety_service.request_refund(
            booking_id=booking.id,
            requested_by=str(booking.guest_id),
            amount=Decimal("50.00"),
            reason="Schedule conflict",
        )
        assert refund.status == RefundStatus.REQUESTED.value
        assert refund.amount == Decimal("50.00")

        reviewer_id = str(uuid4())
        refund = await safety_service.review_refund(
            refund.id, reviewer_id=reviewer_id, approve=True, note="Approved"
        )
        assert refund.status == RefundStatus.APPROVED.value
        assert refund.reviewed_by == reviewer_id

        refund = await safety_service.settle_refund(
            refund.id, settlement_ref="FIN-SETTLE-12345"
        )
        assert refund.status == RefundStatus.SETTLED.value
        assert refund.settlement_ref == "FIN-SETTLE-12345"
        assert refund.settled_at is not None

    async def test_refund_rejection_flow(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        safety_service = TourismSafetyService(db_session)

        refund = await safety_service.request_refund(
            booking_id=booking.id,
            requested_by=str(booking.guest_id),
            amount=Decimal("30.00"),
            reason="Changed mind",
        )
        assert refund.status == RefundStatus.REQUESTED.value

        reviewer_id = str(uuid4())
        refund = await safety_service.review_refund(
            refund.id, reviewer_id=reviewer_id, approve=False, note="Policy violation"
        )
        assert refund.status == RefundStatus.REJECTED.value
        assert refund.review_note == "Policy violation"

        with pytest.raises(RefundError):
            await safety_service.settle_refund(refund.id, settlement_ref="FIN-123")

    async def test_complaint_filing_review_resolution(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        complaint = TourComplaint(
            booking_id=booking.id,
            tour_id=setup_booking[1].id,
            guide_id=setup_booking[0].id,
            filed_by=str(booking.guest_id),
            category=ComplaintCategory.GUIDE_BEHAVIOR.value,
            severity="high",
            status=ComplaintStatus.OPEN.value,
            summary="Guide was unprofessional and late",
        )
        db_session.add(complaint)
        await db_session.commit()
        await db_session.refresh(complaint)

        assert complaint.status == ComplaintStatus.OPEN.value
        assert complaint.category == ComplaintCategory.GUIDE_BEHAVIOR.value

        reviewer_id = str(uuid4())
        complaint.status = ComplaintStatus.INVESTIGATING.value
        complaint.assigned_to = reviewer_id
        await db_session.commit()
        await db_session.refresh(complaint)

        assert complaint.status == ComplaintStatus.INVESTIGATING.value
        assert complaint.assigned_to == reviewer_id

        complaint.status = ComplaintStatus.RESOLVED.value
        complaint.resolution = "Guide reprimanded, partial refund issued"
        complaint.resolved_at = datetime.now(UTC)
        await db_session.commit()
        await db_session.refresh(complaint)

        assert complaint.status == ComplaintStatus.RESOLVED.value
        assert complaint.resolution == "Guide reprimanded, partial refund issued"
        assert complaint.resolved_at is not None

    async def test_safety_incident_blocks_departure_bookings(self, db_session: AsyncSession, setup_booking):
        """Test that SAFETY severity incident blocks new bookings on departure."""
        guide, tour, departure, booking = setup_booking

        incident = TourIncident(
            departure_id=departure.id,
            reported_by=str(uuid4()),
            severity=IncidentSeverity.SAFETY.value,
            status=IncidentStatus.OPEN.value,
            summary="Route closed due to landslide",
        )
        db_session.add(incident)
        await db_session.commit()
        await db_session.refresh(incident)

        assert incident.blocks_bookings is True

        # Verify departure service respects the block
        dep_service = DepartureService(db_session)
        with pytest.raises(ValueError, match="blocked"):
            await dep_service.consume(
                departure_id=departure.id,
                participants=2,
            )

        # Resolve incident
        incident.status = IncidentStatus.RESOLVED.value
        incident.resolution = "Route cleared"
        incident.resolved_at = datetime.now(UTC)
        db_session.add(incident)
        await db_session.commit()
        await db_session.refresh(incident)

        assert incident.blocks_bookings is False

    async def test_no_duplicate_refund_on_same_booking(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        safety_service = TourismSafetyService(db_session)

        await safety_service.request_refund(
            booking_id=booking.id,
            requested_by=str(booking.guest_id),
            amount=Decimal("20.00"),
            reason="First request",
        )

        with pytest.raises(RefundError, match="already has an open refund"):
            await safety_service.request_refund(
                booking_id=booking.id,
                requested_by=str(booking.guest_id),
                amount=Decimal("10.00"),
                reason="Second request",
            )

    async def test_refund_cannot_exceed_booking_total(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        safety_service = TourismSafetyService(db_session)

        with pytest.raises(RefundError, match="cannot exceed the booking total"):
            await safety_service.request_refund(
                booking_id=booking.id,
                requested_by=str(booking.guest_id),
                amount=booking.total + Decimal("100.00"),
                reason="Excessive amount",
            )

    async def test_refund_only_by_booking_guest(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        safety_service = TourismSafetyService(db_session)

        other_user = str(uuid4())
        with pytest.raises(RefundError, match="only be requested by the booking's guest"):
            await safety_service.request_refund(
                booking_id=booking.id,
                requested_by=other_user,
                amount=Decimal("10.00"),
                reason="Unauthorized request",
            )

    async def test_complaint_categories_and_severities(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        categories = [
            ComplaintCategory.GUIDE_BEHAVIOR,
            ComplaintCategory.QUALITY,
            ComplaintCategory.MISREPRESENTATION,
            ComplaintCategory.BILLING,
            ComplaintCategory.SAFETY_CONCERN,
            ComplaintCategory.OTHER,
        ]

        for cat in categories:
            complaint = TourComplaint(
                booking_id=setup_booking[3].id,
                tour_id=setup_booking[1].id,
                guide_id=setup_booking[0].id,
                filed_by=str(setup_booking[3].guest_id),
                category=cat.value,
                severity="medium",
                status=ComplaintStatus.OPEN.value,
                summary=f"Complaint about {cat.value}",
            )
            db_session.add(complaint)

        await db_session.commit()

        from services.tourism.incidents import TourComplaint as TC
        complaints = await db_session.execute(
            sa.select(TC).where(TC.booking_id == setup_booking[3].id)
        )
        saved = complaints.scalars().all()
        assert len(saved) == len(categories)

        for c in saved:
            assert c.category in [cat.value for cat in [ComplaintCategory.GUIDE_BEHAVIOR, ComplaintCategory.QUALITY, ComplaintCategory.MISREPRESENTATION, ComplaintCategory.BILLING, ComplaintCategory.SAFETY_CONCERN, ComplaintCategory.OTHER]]

    async def test_complaint_status_transitions(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        complaint = TourComplaint(
            booking_id=booking.id,
            filed_by=str(booking.guest_id),
            category=ComplaintCategory.OTHER.value,
            severity="low",
            status=ComplaintStatus.OPEN.value,
            summary="Test complaint",
        )
        db_session.add(complaint)
        await db_session.commit()

        complaint.status = ComplaintStatus.INVESTIGATING.value
        await db_session.commit()
        assert complaint.status == ComplaintStatus.INVESTIGATING.value

        complaint.status = ComplaintStatus.RESOLVED.value
        complaint.resolution = "Resolved"
        await db_session.commit()
        assert complaint.status == ComplaintStatus.RESOLVED.value

        complaint2 = TourComplaint(
            booking_id=setup_booking[3].id,
            filed_by=str(uuid4()),
            category=ComplaintCategory.OTHER.value,
            severity="high",
            status=ComplaintStatus.INVESTIGATING.value,
            summary="Escalated complaint",
        )
        db_session.add(complaint2)
        await db_session.commit()

        complaint2.status = ComplaintStatus.ESCALATED.value
        await db_session.commit()
        assert complaint2.status == ComplaintStatus.ESCALATED.value

        complaint3 = TourComplaint(
            booking_id=setup_booking[3].id,
            filed_by=str(uuid4()),
            category=ComplaintCategory.OTHER.value,
            severity="low",
            status=ComplaintStatus.OPEN.value,
            summary="Rejected complaint",
        )
        db_session.add(complaint3)
        await db_session.commit()

        complaint3.status = ComplaintStatus.REJECTED.value
        await db_session.commit()
        assert complaint3.status == ComplaintStatus.REJECTED.value

    async def test_cross_entity_refund_on_departure_booking(self, db_session: AsyncSession, setup_booking):
        guide, tour, departure, booking = setup_booking

        safety_service = TourismSafetyService(db_session)
        refund = await safety_service.request_refund(
            booking_id=booking.id,
            requested_by=str(booking.guest_id),
            amount=Decimal("25.00"),
            reason="Departure cancelled by guest",
        )
        assert refund.status == RefundStatus.REQUESTED.value

        dep = await db_session.get(TourDeparture, departure.id)
        assert dep.booked >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])