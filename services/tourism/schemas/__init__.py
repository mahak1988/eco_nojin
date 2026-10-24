"""Pydantic schemas for the rural/tribal tourism HTTP surface (P2-17).

Request models validate what callers may send; response models give the
lifecycle endpoints a stable, self-documenting contract. Fee constants,
ecological-capacity rules and booking numbering stay in
``services.tourism.service`` — nothing here re-implements that logic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from services.tourism.models import TourismDifficultyLevel, TourismTourType

# --- Request models ---


class GuideCreate(BaseModel):
    """Payload for registering a tour guide (``POST /api/v1/tourism/guides``)."""

    village_id: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)
    bio: str | None = Field(default=None, max_length=2000)
    languages: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    license_number: str | None = Field(default=None, max_length=100)


class TourCreate(BaseModel):
    """Payload for creating a tour (``POST /api/v1/tourism/tours``)."""

    guide_id: str = Field(..., min_length=1, max_length=36)
    village_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=300)
    tour_type: TourismTourType
    duration_hours: int = Field(..., gt=0)
    price_per_person: Decimal = Field(..., gt=0)
    description: str | None = Field(default=None, max_length=5000)
    max_participants: int = Field(default=10, ge=1)
    min_participants: int = Field(default=2, ge=1)
    difficulty: TourismDifficultyLevel = TourismDifficultyLevel.MODERATE
    ecological_capacity: int | None = Field(default=None, ge=1)
    is_regenerative: bool = True
    regenerative_activity: str | None = Field(default=None, max_length=2000)


class BookingCreate(BaseModel):
    """Payload for booking a tour (``POST /api/v1/tourism/bookings``).

    The guest is the authenticated caller, so it is not part of the payload.
    """

    tour_id: str = Field(..., min_length=1, max_length=36)
    village_id: str = Field(..., min_length=1, max_length=100)
    participants_count: int = Field(..., ge=1)
    tour_date: datetime
    #: Optional: schedule the booking on a travel date whose remaining seats
    #: are enforced (the departure ledger), instead of the tour-level cap only.
    departure_id: str | None = Field(default=None, max_length=36)
    special_requests: str | None = Field(default=None, max_length=2000)
    regenerative_commitment: str | None = Field(default=None, max_length=2000)

    @field_validator("tour_date")
    @classmethod
    def _normalize_to_utc(cls, value: datetime) -> datetime:
        """The service compares against ``datetime.now(UTC)``.

        A naive timestamp would raise ``TypeError`` inside that comparison and
        surface as HTTP 500, so naive input is pinned to UTC here.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class PaymentConfirm(BaseModel):
    """Payload for confirming a booking payment."""

    payment_tx_hash: str = Field(..., min_length=1, max_length=100)


class BookingCancel(BaseModel):
    """Payload for cancelling a booking (``POST /api/v1/tourism/bookings/{id}/cancel``)."""

    reason: str = Field(..., min_length=1, max_length=1000)
    refund_requested: bool = Field(default=True)


# --- Response models ---


class GuideResponse(BaseModel):
    """A registered tour guide."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    village_id: str
    full_name: str
    bio: str | None = None
    languages: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    license_number: str | None = None
    is_verified: bool = False
    created_at: datetime | None = None

    @field_validator("languages", "specialties", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value):
        return [] if value is None else value


class TourResponse(BaseModel):
    """A tour in the public catalogue or awaiting approval."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    guide_id: str
    village_id: str
    title: str
    slug: str
    description: str | None = None
    # ``Tour.images`` exists on the model but was absent here, so the
    # catalogue JSON never carried it and every tour card fell back to the
    # placeholder in the UI. Same for ``currency``: the money column is
    # server-side, the unit is part of the contract.
    images: list[str] = Field(default_factory=list)
    currency: str | None = "IRR"
    tour_type: str
    duration_hours: int
    max_participants: int = 10
    min_participants: int = 2
    difficulty: str = "moderate"
    price_per_person: Decimal
    ecological_capacity: int | None = None
    current_bookings: int = 0
    total_bookings: int = 0
    status: str
    is_regenerative: bool = True
    regenerative_activity: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None

    @field_validator("images", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value):
        return [] if value is None else value


class BookingResponse(BaseModel):
    """A booking with the fee split the service computed."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_number: str
    tour_id: str
    guest_id: str
    village_id: str
    participants_count: int
    tour_date: datetime
    special_requests: str | None = None
    subtotal: Decimal
    platform_fee: Decimal
    landscape_fee: Decimal
    insurance_fee: Decimal
    total: Decimal
    status: str
    payment_status: str
    blockchain_tx_hash: str | None = None
    settlement_status: str
    regenerative_commitment: str | None = None
    regenerative_completed: bool = False
    cancel_reason: str | None = None
    refund_amount: Decimal | None = None
    refund_status: str | None = None
    created_at: datetime | None = None
