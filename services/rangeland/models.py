"""Rangeland ORM models (BG-014)."""

from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from database.base import Base

rangeland_usage_type_enum = PG_ENUM(
    "grazing",
    "conservation",
    "mixed",
    name="rangeland_usage_type",
    create_type=False,
)


rangeland_condition_enum = PG_ENUM(
    "good",
    "fair",
    "poor",
    name="rangeland_condition",
    create_type=False,
)


class Rangeland(Base):
    """Rangeland entity for a village (BG-014)."""

    __tablename__ = "rangelands"

    rangeland_id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    village_id = Column(String(100), nullable=False, index=True)
    governance_space_id = Column(String(36), nullable=True, index=True)
    area_ha = Column(Numeric(12, 2), nullable=False)
    vegetation_type = Column(String(100), nullable=True)
    carrying_capacity_per_ha = Column(Numeric(8, 2), nullable=True)
    usage_type = Column(String(20), nullable=False, default="grazing", index=True)
    condition = Column(String(20), nullable=False, default="fair", index=True)
    productivity_index = Column(Numeric(5, 2), nullable=True)
    management_practice = Column(String(200), nullable=True)
    notes = Column(Text(), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        Index("ix_rangeland_village", "village_id", "condition", unique=False),
    )