"""مدیریت یکپارچه منظر - schemas"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LandscapeVillageOut(BaseModel):
    id: UUID
    village_id: str
    name: str
    region: str
    country: str | None = None
    coordinates: dict | None = None
    geo_boundary: dict | None = None
    brand_name: str | None = None
    brand_logo_url: str | None = None
    gi_registration: str | None = None
    is_active: bool = True
    established_at: datetime | None = None
    active_modules: list = Field(default_factory=list)
    total_members: int = 0
    active_sellers: int = 0
    active_tour_guides: int = 0
    monthly_gmv: Decimal = Field(default=Decimal("0.00"))
    ecological_metrics_data: dict = Field(default_factory=dict)
    smart_contract_address: str | None = None
    blockchain_network: str | None = None
    verification_status: str = "pending"
    representative_status: str = "none"
    workflow_status: str = "published"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    status: str = "ok"
    reason: str | None = None
    provenance: dict[str, Any] = Field(
        default_factory=lambda: {
            "source": "measured",
            "engine": "services/landscape/service.py",
            "synthetic": False,
        }
    )

    model_config = ConfigDict(from_attributes=True)


class LandscapeGovernanceMemberOut(BaseModel):
    id: UUID
    village_id: str
    user_id: str
    role: str
    is_active: bool = True
    term_start: datetime | None = None
    term_end: datetime | None = None
    elected_at: datetime | None = None
    phone: str | None = None
    email: str | None = None

    status: str = "ok"
    reason: str | None = None
    provenance: dict[str, Any] = Field(
        default_factory=lambda: {
            "source": "measured",
            "engine": "services/landscape/service.py",
            "synthetic": False,
        }
    )

    model_config = ConfigDict(from_attributes=True)


class LandscapeFundOut(BaseModel):
    id: UUID
    village_id: str
    contract_address: str | None = None
    fee_bps: int = 100
    total_collected: Decimal = Field(default=Decimal("0.00"))
    total_distributed: Decimal = Field(default=Decimal("0.00"))
    pending_balance: Decimal = Field(default=Decimal("0.00"))
    currency: str = "IRR"
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LandscapeFundDistributionOut(BaseModel):
    id: UUID
    fund_id: UUID
    village_id: str
    amount: Decimal
    purpose: str
    description: str | None = None
    recipient_user_id: str | None = None
    recipient_organization: str | None = None
    proposed_by: UUID
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    status: str = "pending"
    blockchain_tx_hash: str | None = None
    created_at: datetime | None = None
    executed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)