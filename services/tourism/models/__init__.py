import uuid

"""
مدل‌های داده گردشگری روستایی و عشایری
"""

from datetime import UTC, date, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from database.base import Base


class TourismTourType(str, Enum):
    ECOTOURISM = "ecotourism"
    NOMADIC = "nomadic"
    CULTURAL = "cultural"
    AGRO = "agrotourism"
    SCIENTIFIC = "scientific"
    WELLNESS = "wellness"
    ADVENTURE = "adventure"
    CULINARY = "culinary"


class TourismDifficultyLevel(str, Enum):
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
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class TourismTour(Base):
    __tablename__ = "tourism_tours"
    __table_args__ = (
        Index("idx_tour_village", "village_id"),
        Index("idx_tour_type", "tour_type"),
        Index("idx_tour_status", "status"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guide_id = Column(String(36), ForeignKey("tourism_guides.id"), nullable=False)
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
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
