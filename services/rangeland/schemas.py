from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RangelandUsageType(StrEnum):
    grazing = "grazing"
    conservation = "conservation"
    mixed = "mixed"


class RangelandCondition(StrEnum):
    good = "good"
    fair = "fair"
    poor = "poor"


class RangelandBase(BaseModel):
    name: str = Field(..., max_length=200)
    village_id: str = Field(..., max_length=100, description="FK to landscape_villages.village_id")
    area_ha: Decimal = Field(..., ge=0, decimal_places=2, max_digits=12)
    vegetation_type: str | None = Field(None, max_length=100)
    carrying_capacity_per_ha: Decimal | None = Field(None, ge=0, decimal_places=2, max_digits=8)
    usage_type: RangelandUsageType = Field(default=RangelandUsageType.grazing)
    condition: RangelandCondition = Field(default=RangelandCondition.fair)
    productivity_index: Decimal | None = Field(None, ge=0, decimal_places=2, max_digits=5)
    management_practice: str | None = Field(None, max_length=200)
    notes: str | None = None


class RangelandCreate(RangelandBase):
    rangeland_id: str = Field(..., max_length=100, description="External rangeland identifier (unique)")


class RangelandUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    area_ha: Decimal | None = Field(None, ge=0, decimal_places=2, max_digits=12)
    vegetation_type: str | None = Field(None, max_length=100)
    carrying_capacity_per_ha: Decimal | None = Field(None, ge=0, decimal_places=2, max_digits=8)
    usage_type: RangelandUsageType | None = None
    condition: RangelandCondition | None = None
    productivity_index: Decimal | None = Field(None, ge=0, decimal_places=2, max_digits=5)
    management_practice: str | None = Field(None, max_length=200)
    notes: str | None = None


class RangelandOut(RangelandBase):
    id: UUID = Field(default_factory=uuid4)
    rangeland_id: str
    status: str = "ok"
    reason: str | None = None
    provenance: dict[str, Any] = Field(
        default_factory=lambda: {
            "source": "measured",
            "engine": "services/rangeland/service.py",
            "synthetic": False,
        }
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RangelandStats(BaseModel):
    village_id: str
    count: int
    total_area_ha: Decimal
    avg_productivity_index: float | None = None
    condition_distribution: dict[str, int] = Field(default_factory=dict)
    usage_type_distribution: dict[str, int] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(
        default_factory=lambda: {
            "source": "derived",
            "engine": "services/rangeland/service.py",
            "synthetic": False,
        }
    )
