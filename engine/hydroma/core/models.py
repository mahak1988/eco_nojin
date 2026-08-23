"""SQLAlchemy ORM models for core entities."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# SoilProfile removed as it's defined in database/models.py with a more comprehensive schema.


class Plant(Base):
    """Represents plant species, seeds, and their ecological requirements."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    local_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="e.g., crop, tree, medicinal"
    )

    # Tolerances and needs are optional in initial data entry
    water_need: Mapped[str | None] = mapped_column(String(20), comment="low, medium, high")
    drought_tolerance: Mapped[str | None] = mapped_column(String(20))
    salinity_tolerance: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Material(Base):
    """Represents natural, organic, or biological materials for soil amendment."""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), comment="animal, plant, mineral, microbial")
    c_n_ratio: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Carbon to Nitrogen ratio"
    )
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)