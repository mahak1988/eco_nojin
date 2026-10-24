import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)

from database.base import Base

"""
مدل‌های داده گردشگری روستایی و عشایری
"""

class TourismTourType(StrEnum):
    ECOTOURISM = "ecotourism"
    NOMADIC = "nomadic"
    CULTURAL = "cultural"
    AGRO = "agrotourism"
    SCIENTIFIC = "scientific"
    WELLNESS = "wellness"
    ADVENTURE = "adventure"
    CULINARY = "culinary"


class TourismDifficultyLevel(StrEnum):
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


class TourismGuide(Base):
    __tablename__ = "tourism_guides"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    village_id = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    bio = Column(Text)
    languages = Column(JSON, default=list)
    specialties = Column(JSON, default=list)
    license_number = Column(String(100))
    is_verified = Column(Boolean, default=False)
    insurance_provider = Column(String(200))
    insurance_policy_number = Column(String(100))
    insurance_expiry = Column(Date, nullable=True)
    total_tours = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class TourismTour(Base):
    __tablename__ = "tourism_tours"
    __table_args__ = (
        Index("idx_tour_village", "village_id"),
        Index("idx_tour_type", "tour_type"),
        Index("idx_tour_status", "status"),
        Index("idx_tour_nomadic", "nomadic_community_id"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guide_id = Column(String(36), ForeignKey("tourism_guides.id"), nullable=False)
    nomadic_community_id = Column(String(36), nullable=True, index=True)
    village_id = Column(String(100), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    description = Column(Text)
    tour_type = Column(SQLEnum(TourismTourType), nullable=False, index=True)
    duration_hours = Column(Integer, nullable=False)
    max_participants = Column(Integer, default=10)
    min_participants = Column(Integer, default=2)
    difficulty = Column(SQLEnum(TourismDifficultyLevel), default=TourismDifficultyLevel.MODERATE)
    price_per_person = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="IRR")
    includes = Column(JSON, default=list)
    excludes = Column(JSON, default=list)
    itinerary = Column(JSON, default=list)
    meeting_point = Column(JSON)
    images = Column(JSON, default=list)
    safety_equipment = Column(JSON, default=list)
    ecological_capacity = Column(Integer)
    current_bookings = Column(Integer, default=0)
    status = Column(String(20), default="pending_approval", index=True)
    is_regenerative = Column(Boolean, default=True)
    regenerative_activity = Column(Text)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    total_bookings = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class TourismBooking(Base):
    __tablename__ = "tourism_bookings"
    __table_args__ = (
        Index("idx_booking_tour", "tour_id"),
        Index("idx_booking_guest", "guest_id"),
        Index("idx_booking_status", "status"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_number = Column(String(50), unique=True, nullable=False, index=True)
    tour_id = Column(String(36), ForeignKey("tourism_tours.id"), nullable=False)
    guest_id = Column(String(36), nullable=False, index=True)
    village_id = Column(String(100), nullable=False, index=True)
    participants_count = Column(Integer, nullable=False)
    tour_date = Column(DateTime, nullable=False)
    special_requests = Column(Text, nullable=True)
    subtotal = Column(Numeric(15, 2), nullable=False)
    platform_fee = Column(Numeric(15, 2), default=Decimal("0.00"))
    landscape_fee = Column(Numeric(15, 2), default=Decimal("0.00"))
    insurance_fee = Column(Numeric(15, 2), default=Decimal("0.00"))
    total = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="IRR")
    status = Column(String(20), default="pending", index=True)
    payment_status = Column(String(20), default="pending")
    insurance_provider = Column(String(200))
    insurance_policy_number = Column(String(100))
    blockchain_tx_hash = Column(String(100))
    settlement_status = Column(String(20), default="pending")
    regenerative_commitment = Column(Text)
    regenerative_completed = Column(Boolean, default=False)
    cancel_reason = Column(Text)
    refund_amount = Column(Numeric(15, 2), default=Decimal("0.00"))
    refund_status = Column(String(20), default="none")  # none|pending|processed|failed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class TourismFestival(Base):
    """An ecotourism festival or celebration hosted by a village."""

    __tablename__ = "tourism_festivals"
    __table_args__ = (
        Index("idx_festival_village", "village_id"),
        Index("idx_festival_season", "season"),
        Index("idx_festival_status", "status"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), ForeignKey("gov_community_spaces.village_id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    festival_type = Column(String(50), nullable=False)  # seasonal|handicraft|culinary|religious|cultural
    season = Column(String(20), nullable=False)  # spring|summer|autumn|winter
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    recurrence = Column(String(20), default="annual")  # annual|biennial|one_off
    capacity = Column(Integer, nullable=False)
    base_ticket_price = Column(Numeric(12, 2), nullable=False)
    landscape_fee_bps = Column(Integer, default=200)  # 2% to landscape fund
    is_regenerative = Column(Boolean, default=False)
    status = Column(String(20), default="planned")  # planned|active|completed|cancelled
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class FestivalEdition(Base):
    """One annual/biennial occurrence of a festival."""

    __tablename__ = "festival_editions"
    __table_args__ = (
        UniqueConstraint("festival_id", "year", name="uq_festival_edition_year"),
        Index("idx_edition_year", "year"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    festival_id = Column(String(36), ForeignKey("tourism_festivals.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    total_seats = Column(Integer, nullable=False)
    seats_available = Column(Integer, nullable=False)
    total_revenue = Column(Numeric(14, 2), default=Decimal("0"))
    landscape_fees = Column(Numeric(14, 2), default=Decimal("0"))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class FestivalBooking(Base):
    """Guest reservation for a festival edition."""

    __tablename__ = "festival_bookings"
    __table_args__ = (
        Index("idx_festival_booking_guest", "guest_id"),
        Index("idx_festival_booking_status", "status"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    festival_id = Column(String(36), ForeignKey("tourism_festivals.id"), nullable=False, index=True)
    edition_id = Column(String(36), ForeignKey("festival_editions.id"), nullable=False, index=True)
    guest_id = Column(String(36), nullable=False, index=True)
    participants_count = Column(Integer, nullable=False)
    ticket_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(14, 2), nullable=False)
    platform_fee = Column(Numeric(14, 2), default=Decimal("0"))
    landscape_fee = Column(Numeric(14, 2), default=Decimal("0"))
    total = Column(Numeric(14, 2), nullable=False)
    status = Column(String(20), default="pending")  # pending|confirmed|cancelled|completed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class IntangibleHeritageElement(Base):
    """UNESCO Intangible Cultural Heritage element associated with a village."""

    __tablename__ = "intangible_heritage_elements"
    __table_args__ = (
        Index("idx_ihe_village", "village_id"),
        Index("idx_ihe_domain", "domain"),
        Index("idx_ihe_status", "threatened_level"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)
    element_name = Column(String(200), nullable=False)
    element_name_en = Column(String(200), nullable=True)
    domain = Column(String(50), nullable=False)  # oral_traditions|performing_arts|social_practices|rituals|knowledge|craftsmanship
    description = Column(Text, nullable=True)
    threatened_level = Column(String(30), default="viable")  # viable|threatened|needs_urgent_safeguarding|inscribed
    inscription_year = Column(Integer, nullable=True)
    safeguarding_plan = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class UnescoIndicator(Base):
    """UNESCO assessment indicator for a village."""

    __tablename__ = "unesco_indicators"
    __table_args__ = (
        UniqueConstraint("village_id", "indicator_code", name="uq_unesco_village_indicator"),
        Index("idx_unesco_village", "village_id"),
        Index("idx_unesco_status", "status"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)
    indicator_code = Column(String(20), nullable=False)  # ICH.01, ICH.02, ...
    indicator_name = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=False)  # oral_traditions|performing_arts|social_practices|rituals|knowledge|craftsmanship
    status = Column(String(30), nullable=False)  # inscribed|viable|threatened|needs_urgent_safeguarding
    last_assessment_at = Column(DateTime, nullable=True)
    justification = Column(Text, nullable=True)
    safeguarding_plan = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class UnescoAssessment(Base):
    """Periodic UNESCO assessment record."""

    __tablename__ = "unesco_assessments"
    __table_args__ = (
        Index("idx_assessment_village", "village_id"),
        Index("idx_assessment_indicator", "indicator_code"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)
    indicator_code = Column(String(20), nullable=False)
    calificatif = Column(String(30), nullable=False)  # viable|threatened|needs_urgent_safeguarding|inscribed
    justification = Column(Text, nullable=True)
    assessed_by = Column(String(36), nullable=False)
    assessed_at = Column(DateTime, default=lambda: datetime.now(UTC))
