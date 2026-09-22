"""Tests for the Tourism service — eco-tourism and rural hospitality matching."""

from __future__ import annotations


class TestTourismModels:
    def test_tourism_tour_type_enum(self):
        from services.tourism.models import TourismTourType

        assert TourismTourType.ECOTOURISM == "ecotourism"
        assert TourismTourType.AGRO == "agrotourism"
        assert TourismTourType.CULTURAL == "cultural"

    def test_tourism_difficulty_enum(self):
        from services.tourism.models import TourismDifficultyLevel

        assert TourismDifficultyLevel.EASY == "easy"
        assert TourismDifficultyLevel.CHALLENGING == "challenging"

    def test_tourism_guide_model(self):
        from services.tourism.models import TourismGuide

        guide = TourismGuide(
            user_id="user-001",
            village_id="village-001",
            full_name="Ali Karimi",
            is_verified=False,
        )
        assert guide.full_name == "Ali Karimi"
        assert guide.is_verified is False

    def test_tourism_tour_model(self):
        from services.tourism.models import (
            TourismDifficultyLevel,
            TourismTour,
            TourismTourType,
        )

        tour = TourismTour(
            guide_id="guide-001",
            village_id="village-001",
            title="Forest Hiking Tour",
            slug="forest-hiking-tour",
            tour_type=TourismTourType.ADVENTURE,
            duration_hours=4,
            max_participants=10,
            min_participants=2,
            price_per_person=5000000,
            difficulty=TourismDifficultyLevel.MODERATE,
        )
        assert tour.title == "Forest Hiking Tour"
        assert tour.tour_type == TourismTourType.ADVENTURE
        assert tour.difficulty == TourismDifficultyLevel.MODERATE

    def test_tourism_booking_model(self):
        from services.tourism.models import TourismBooking

        booking = TourismBooking(
            booking_number="BK-001",
            tour_id="tour-001",
            guest_id="guest-001",
            village_id="village-001",
            participants_count=2,
            tour_date="2026-04-01T08:00:00",
            subtotal=10000000,
            total=10000000,
            status="pending",
        )
        assert booking.participants_count == 2
        assert booking.status == "pending"


class TestTourismService:
    def test_fee_constants(self):
        from services.tourism.service import TourismService

        assert TourismService.PLATFORM_FEE_BPS == 800
        assert TourismService.LANDSCAPE_FEE_BPS == 200
        assert TourismService.INSURANCE_FEE_BPS == 200
        assert TourismService.HOST_SHARE_BPS == 8800

    def test_generate_slug(self):
        from services.tourism.service import TourismService

        service = TourismService(db=None)
        slug = service._generate_slug("Forest Hiking Tour")
        assert "forest-hiking-tour" in slug
        assert len(slug) > len("forest-hiking-tour")

    def test_generate_booking_number(self):
        from services.tourism.service import TourismService

        service = TourismService(db=None)
        number = service._generate_booking_number()
        assert number.startswith("TR-")
        assert len(number) > 10

    def test_service_initialization(self):
        from services.tourism.service import TourismService

        service = TourismService(db=None)
        assert service.db is None
        assert hasattr(service, "register_guide")
        assert hasattr(service, "create_tour")
        assert hasattr(service, "create_booking")
        assert hasattr(service, "cancel_booking")
