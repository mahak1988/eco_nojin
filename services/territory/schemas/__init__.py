"""Territory domain schemas for Eco Nojin (Pydantic models)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TerritoryBase(BaseModel):
    """Base territory fields."""

    code: str = Field(..., min_length=1, max_length=50, description="Territory code (e.g., IR-01)")
    name: str = Field(..., min_length=1, max_length=200, description="Territory name (Persian)")
    name_en: str | None = Field(None, max_length=200, description="Territory name (English)")
    territory_type: str = Field(..., description="Type: region, county, district, village, neighborhood")
    parent_id: UUID | None = Field(None, description="Parent territory ID")
    level: int = Field(default=0, ge=0, le=4, description="Hierarchy level (0=region, 3=village)")

    # Geographic
    latitude: Decimal | None = Field(None, description="Latitude")
    longitude: Decimal | None = Field(None, description="Longitude")
    boundary_geojson: dict[str, Any] | None = Field(None, description="GeoJSON Polygon/MultiPolygon")
    center_point: dict[str, Any] | None = Field(None, description="Center point {lat, lon}")
    area_hectares: Decimal | None = Field(None, ge=0, description="Area in hectares")

    # Administrative
    population: int | None = Field(None, ge=0)
    household_count: int | None = Field(None, ge=0)
    postal_code: str | None = Field(None, max_length=20)

    # Brand
    brand_name: str | None = Field(None, max_length=200)
    brand_logo_url: str | None = Field(None, max_length=500)
    brand_slogan: str | None = Field(None, max_length=500)
    gi_registration: str | None = Field(None, max_length=100)

    # Smart contract
    smart_contract_address: str | None = Field(None, max_length=100)
    blockchain_network: str | None = Field(None, max_length=50)

    established_at: date | None = None


class TerritoryCreate(TerritoryBase):
    """Schema for creating a territory."""

    pass


class TerritoryUpdate(BaseModel):
    """Schema for updating a territory."""

    name: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    territory_type: str | None = None
    parent_id: UUID | None = None
    level: int | None = Field(None, ge=0, le=4)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    boundary_geojson: dict[str, Any] | None = None
    center_point: dict[str, Any] | None = None
    area_hectares: Decimal | None = Field(None, ge=0)
    population: int | None = Field(None, ge=0)
    household_count: int | None = Field(None, ge=0)
    postal_code: str | None = Field(None, max_length=20)
    status: str | None = Field(None, pattern="^(active|inactive|pending|archived)$")
    brand_name: str | None = Field(None, max_length=200)
    brand_logo_url: str | None = Field(None, max_length=500)
    brand_slogan: str | None = Field(None, max_length=500)
    gi_registration: str | None = Field(None, max_length=100)
    smart_contract_address: str | None = Field(None, max_length=100)
    blockchain_network: str | None = Field(None, max_length=50)
    established_at: date | None = None


class TerritoryResponse(TerritoryBase):
    """Territory response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    monthly_gmv: Decimal
    active_sellers: int
    active_tour_guides: int
    total_members: int
    created_at: datetime
    updated_at: datetime
    children: list["TerritoryResponse"] = []


class TerritoryListResponse(BaseModel):
    """Paginated territory list response."""

    items: list[TerritoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TerritorySearchRequest(BaseModel):
    """Territory search parameters."""

    q: str | None = Field(None, description="Search query (name, code)")
    territory_type: str | None = Field(None, description="Filter by type")
    parent_id: UUID | None = Field(None, description="Filter by parent")
    status: str | None = Field(None, description="Filter by status")
    region_code: str | None = Field(None, description="Filter by region code")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# Governance Schemas
class GovernanceMemberBase(BaseModel):
    """Base governance member fields."""

    territory_id: UUID
    user_id: UUID
    role: str = Field(..., description="Role in LWG")
    term_start: date | None = None
    term_end: date | None = None
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=200)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=500)


class GovernanceMemberCreate(GovernanceMemberBase):
    """Create governance member."""

    pass


class GovernanceMemberUpdate(BaseModel):
    """Update governance member."""

    role: str | None = None
    is_active: bool | None = None
    term_start: date | None = None
    term_end: date | None = None
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=200)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=500)


class GovernanceMemberResponse(GovernanceMemberBase):
    """Governance member response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    elected_at: datetime
    created_at: datetime


# Fund Schemas
class TerritoryFundBase(BaseModel):
    """Base territory fund fields."""

    territory_id: UUID
    fee_bps: int = Field(default=100, ge=0, le=10000)
    currency: str = Field(default="IRR", max_length=3)


class TerritoryFundCreate(TerritoryFundBase):
    """Create territory fund."""

    contract_address: str | None = Field(None, max_length=100)


class TerritoryFundUpdate(BaseModel):
    """Update territory fund."""

    fee_bps: int | None = Field(None, ge=0, le=10000)
    contract_address: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class TerritoryFundResponse(TerritoryFundBase):
    """Territory fund response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contract_address: str | None
    total_collected: Decimal
    total_distributed: Decimal
    pending_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TerritoryFundDistributionBase(BaseModel):
    """Base fund distribution fields."""

    fund_id: UUID
    territory_id: UUID
    amount: Decimal = Field(..., gt=0)
    purpose: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    recipient_user_id: UUID | None = None
    recipient_organization: str | None = Field(None, max_length=200)
    proposed_by: UUID


class TerritoryFundDistributionCreate(TerritoryFundDistributionBase):
    """Create fund distribution."""

    pass


class TerritoryFundDistributionUpdate(BaseModel):
    """Update fund distribution."""

    approved_by: UUID | None = None
    status: str | None = Field(None, pattern="^(pending|approved|rejected|executed)$")
    blockchain_tx_hash: str | None = Field(None, max_length=100)


class TerritoryFundDistributionResponse(TerritoryFundDistributionBase):
    """Fund distribution response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    approved_by: UUID | None
    approved_at: datetime | None
    status: str
    blockchain_tx_hash: str | None
    created_at: datetime
    executed_at: datetime | None


# Brand Schemas
class TerritoryBrandBase(BaseModel):
    """Base territory brand fields."""

    territory_id: UUID
    brand_name: str = Field(..., min_length=1, max_length=200)
    brand_name_en: str | None = Field(None, max_length=200)
    logo_url: str | None = Field(None, max_length=500)
    slogan: str | None = Field(None, max_length=500)
    description: str | None = None
    story: str | None = None


class TerritoryBrandCreate(TerritoryBrandBase):
    """Create territory brand."""

    pass


class TerritoryBrandUpdate(BaseModel):
    """Update territory brand."""

    brand_name: str | None = Field(None, min_length=1, max_length=200)
    brand_name_en: str | None = Field(None, max_length=200)
    logo_url: str | None = Field(None, max_length=500)
    slogan: str | None = Field(None, max_length=500)
    description: str | None = None
    story: str | None = None
    status: str | None = Field(None, pattern="^(draft|pending|verified|rejected)$")
    verified_by: UUID | None = None
    gi_registration_number: str | None = Field(None, max_length=100)
    gi_registration_date: date | None = None
    signature_hex: str | None = None
    pq_public_hex: str | None = None


class TerritoryBrandResponse(TerritoryBrandBase):
    """Territory brand response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    verified_by: UUID | None
    verified_at: datetime | None
    verification_notes: str | None
    gi_registration_number: str | None
    gi_registration_date: date | None
    signature_hex: str | None
    pq_public_hex: str | None
    signed_at: datetime | None
    created_at: datetime
    updated_at: datetime


# Hierarchy schemas
class TerritoryTreeNode(BaseModel):
    """Territory tree node for hierarchical display."""

    id: UUID
    code: str
    name: str
    name_en: str | None
    territory_type: str
    level: int
    children: list["TerritoryTreeNode"] = []


class TerritoryStatsResponse(BaseModel):
    """Territory statistics."""

    total_territories: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    total_population: int | None
    total_area_hectares: Decimal | None
    total_gmv: Decimal