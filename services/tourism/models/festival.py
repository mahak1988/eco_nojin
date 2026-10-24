"""Ecotourism festivals, editions, bookings and UNESCO intangible heritage models."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class TourismFestival(Base):
    """An ecotourism festival or celebration hosted by a village."""

    __tablename__ = "tourism_festivals"
    __table_args__ = (
        Index("idx_festival_village", "village_id"),
        Index("idx_festival_season", "season"),
        Index("idx_festival_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    village_id: Mapped[str] = mapped_column(String(100), ForeignKey("gov_community_spaces.village_id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    festival_type: Mapped[str] = mapped_column(String(50), nullable=False)  # seasonal|handicraft|culinary|religious|cultural
    season: Mapped[str] = mapped_column(String(20), nullable=False)  # spring|summer|autumn|winter
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    recurrence: Mapped[str] = mapped_column(String(20), default="annual")  # annual|biennial|one_off
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    base_ticket_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    landscape_fee_bps: Mapped[int] = mapped_column(Integer, default=200)  # 2% to landscape fund
    is_regenerative: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned|active|completed|cancelled
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    editions: Mapped[list[FestivalEdition]] = relationship(back_populates="festival", cascade="all, delete-orphan")
    bookings: Mapped[list[FestivalBooking]] = relationship(back_populates="festival", cascade="all, delete-orphan")


class FestivalEdition(Base):
    """One annual/biennial occurrence of a festival."""

    __tablename__ = "festival_editions"
    __table_args__ = (
        UniqueConstraint("festival_id", "year", name="uq_festival_edition_year"),
        Index("idx_edition_year", "year"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    festival_id: Mapped[str] = mapped_column(String(36), ForeignKey("tourism_festivals.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_available: Mapped[int] = mapped_column(Integer, nullable=False)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    landscape_fees: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    festival: Mapped[TourismFestival] = relationship(back_populates="editions")
    bookings: Mapped[list[FestivalBooking]] = relationship(back_populates="edition", cascade="all, delete-orphan")


class FestivalBooking(Base):
    """Guest reservation for a festival edition."""

    __tablename__ = "festival_bookings"
    __table_args__ = (
        Index("idx_festival_booking_guest", "guest_id"),
        Index("idx_festival_booking_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    festival_id: Mapped[str] = mapped_column(String(36), ForeignKey("tourism_festivals.id"), nullable=False, index=True)
    edition_id: Mapped[str] = mapped_column(String(36), ForeignKey("festival_editions.id"), nullable=False, index=True)
    guest_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    participants_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ticket_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    landscape_fee: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|confirmed|cancelled|completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    festival: Mapped[TourismFestival] = relationship(back_populates="bookings")
    edition: Mapped[FestivalEdition] = relationship(back_populates="bookings")


class IntangibleHeritageElement(Base):
    """UNESCO Intangible Cultural Heritage element associated with a village."""

    __tablename__ = "intangible_heritage_elements"
    __table_args__ = (
        Index("idx_ihe_village", "village_id"),
        Index("idx_ihe_domain", "domain"),
        Index("idx_ihe_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    village_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    element_name: Mapped[str] = mapped_column(String(200), nullable=False)
    element_name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # oral_traditions|performing_arts|social_practices|rituals|knowledge|craftsmanship
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    threatened_level: Mapped[str] = mapped_column(String(30), default="viable")  # viable|threatened|needs_urgent_safeguarding|inscribed
    inscription_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    safeguarding_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class UnescoIndicator(Base):
    """UNESCO assessment indicator for a village."""

    __tablename__ = "unesco_indicators"
    __table_args__ = (
        UniqueConstraint("village_id", "indicator_code", name="uq_unesco_village_indicator"),
        Index("idx_unesco_village", "village_id"),
        Index("idx_unesco_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    village_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    indicator_code: Mapped[str] = mapped_column(String(20), nullable=False)  # ICH.01, ICH.02, ...
    indicator_name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)  # oral_traditions|performing_arts|social_practices|rituals|knowledge|craftsmanship
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # inscribed|viable|threatened|needs_urgent_safeguarding
    last_assessment_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    safeguarding_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class UnescoAssessment(Base):
    """Periodic UNESCO assessment record."""

    __tablename__ = "unesco_assessments"
    __table_args__ = (
        Index("idx_assessment_village", "village_id"),
        Index("idx_assessment_indicator", "indicator_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    village_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    indicator_code: Mapped[str] = mapped_column(String(20), nullable=False)
    calificatif: Mapped[str] = mapped_column(String(30), nullable=False)  # viable|threatened|needs_urgent_safeguarding|inscribed
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_by: Mapped[str] = mapped_column(String(36), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
