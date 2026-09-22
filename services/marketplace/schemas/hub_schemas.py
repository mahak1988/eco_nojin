"""
Pydantic schemas for Village Development Hub
=============================================

Request/response models for the village development hub endpoints.
All schemas follow the patterns from `services/auth/schemas.py`.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Base Patterns
# ============================================================================


class HubBase(BaseModel):
    model_config = {"from_attributes": True}


class TimestampMixin:
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ============================================================================
# VillageCapability
# ============================================================================


class CapabilityBase(HubBase):
    category: str = Field(..., min_length=2, max_length=50)
    subcategory: str | None = Field(None, max_length=100)
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    capacity_value: float | None = None
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=2000)
    is_active: bool = True
    confidence: str = Field(default="medium")
    source: str | None = Field(None, max_length=200)


class CapabilityCreate(CapabilityBase):
    pass


class CapabilityUpdate(HubBase):
    category: str | None = None
    subcategory: str | None = None
    name: str | None = None
    name_en: str | None = None
    capacity_value: float | None = None
    unit: str | None = None
    description: str | None = None
    is_active: bool | None = None
    confidence: str | None = None
    source: str | None = None


class CapabilityRead(CapabilityBase, TimestampMixin):
    id: str
    village_id: str


# ============================================================================
# VillageOpportunity
# ============================================================================


class OpportunityBase(HubBase):
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    category: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=3000)
    business_model: str | None = Field(None, max_length=3000)
    required_investment: Decimal | None = None
    required_skills: list[str] = Field(default_factory=list, max_length=20)
    target_markets: list[str] = Field(default_factory=list, max_length=20)
    expected_revenue: Decimal | None = None
    maturity: str = Field(default="idea")
    capability_id: str | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(HubBase):
    name: str | None = None
    name_en: str | None = None
    category: str | None = None
    description: str | None = None
    business_model: str | None = None
    required_investment: Decimal | None = None
    required_skills: list[str] | None = None
    target_markets: list[str] | None = None
    expected_revenue: Decimal | None = None
    maturity: str | None = None
    status: str | None = None
    capability_id: str | None = None


class OpportunityRead(OpportunityBase, TimestampMixin):
    id: str
    village_id: str
    status: str
    created_by: str


class OpportunityInterestCreate(HubBase):
    note: str | None = Field(None, max_length=1000)


class OpportunityInterestRead(HubBase):
    id: str
    opportunity_id: str
    entrepreneur_id: str
    status: str
    note: str | None
    expressed_at: datetime


# ============================================================================
# VillageProject
# ============================================================================


class ProjectBase(HubBase):
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=3000)
    category: str | None = Field(None, max_length=100)
    opportunity_id: str | None = None
    start_date: date | None = None
    expected_completion: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(HubBase):
    name: str | None = None
    name_en: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    opportunity_id: str | None = None
    start_date: date | None = None
    expected_completion: date | None = None


class ProjectProgressUpdate(HubBase):
    progress_pct: int = Field(..., ge=0, le=100)


class ProjectRead(ProjectBase, TimestampMixin):
    id: str
    village_id: str
    status: str
    progress_pct: int
    investment_needed: Decimal | None
    investment_secured: Decimal
    investors_count: int
    team_size: int
    created_by: str


class ProjectInvestorRead(HubBase):
    user_id: str
    amount: Decimal
    currency: str
    status: str
    invested_at: datetime


# ============================================================================
# EntrepreneurProfile
# ============================================================================


class EntrepreneurProfileBase(HubBase):
    skills: list[str] = Field(default_factory=list, max_length=30)
    interests: list[str] = Field(default_factory=list, max_length=30)
    capacity_description: str | None = Field(None, max_length=2000)
    experience_years: int | None = Field(None, ge=0, le=80)
    village_id: str | None = Field(None, max_length=100)
    is_available: bool = True


class EntrepreneurProfileCreate(EntrepreneurProfileBase):
    pass


class EntrepreneurProfileUpdate(HubBase):
    skills: list[str] | None = None
    interests: list[str] | None = None
    capacity_description: str | None = None
    experience_years: int | None = None
    village_id: str | None = None
    is_available: bool | None = None


class EntrepreneurProfileRead(EntrepreneurProfileBase, TimestampMixin):
    id: str
    user_id: str


class EntrepreneurSearchResponse(HubBase):
    profiles: list[EntrepreneurProfileRead]
    count: int


# ============================================================================
# VillageInvestment
# ============================================================================


class InvestmentCreate(HubBase):
    project_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="IRR", max_length=3)
    notes: str | None = Field(None, max_length=1000)


class InvestmentStatusUpdate(HubBase):
    status: str = Field(..., min_length=2, max_length=20)
    confirmed_by: str | None = None


class InvestmentRead(InvestmentCreate, TimestampMixin):
    id: str
    investor_user_id: str
    status: str
    confirmed_by: str | None
    confirmed_at: datetime | None


# ============================================================================
# Tourism Services
# ============================================================================


class TourismServiceCreate(HubBase):
    service_type: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    location: str | None = Field(None, max_length=200)
    coordinates: dict[str, Any] | None = None
    price_per_unit: Decimal | None = None
    capacity: int | None = Field(None, ge=0)
    is_organic: bool = True
    is_regenerative: bool = True
    images: list[str] = Field(default_factory=list)
    contact_phone: str | None = Field(None, max_length=50)
    contact_email: str | None = Field(None, max_length=200)


class TourismServiceRead(TourismServiceCreate, TimestampMixin):
    id: str
    village_id: str
    owner_user_id: str
    is_verified: bool
    status: str


# ============================================================================
# VillageEvent
# ============================================================================


class EventCreate(HubBase):
    title: str = Field(..., min_length=2, max_length=200)
    title_en: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=3000)
    event_type: str | None = Field(None, max_length=50)
    start_date: datetime
    end_date: datetime | None = None
    location: str | None = Field(None, max_length=200)
    coordinates: dict[str, Any] | None = None
    max_participants: int | None = Field(None, ge=1)
    registration_fee: Decimal = Field(default=Decimal("0.00"), ge=0)


class EventRead(EventCreate, TimestampMixin):
    id: str
    village_id: str
    created_by: str
    status: str
    images: list[str]
    registrations_count: int | None = 0


class EventRegistrationCreate(HubBase):
    pass


class EventRegistrationRead(HubBase):
    id: str
    event_id: str
    user_id: str
    status: str
    registration_fee: Decimal
    registered_at: datetime
    confirmed_at: datetime | None


# ============================================================================
# VillageNeed
# ============================================================================


class NeedCreate(HubBase):
    category: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    priority: str = Field(default="medium")
    estimated_investment: Decimal | None = None


class NeedRead(NeedCreate, TimestampMixin):
    id: str
    village_id: str
    is_resolved: bool
    resolved_by: str | None
    resolved_at: datetime | None


# ============================================================================
# VillageBrand
# ============================================================================


class BrandUpdate(HubBase):
    story: str | None = Field(None, max_length=3000)
    vision: str | None = Field(None, max_length=2000)
    values: list[str] | None = None
    heritage: str | None = Field(None, max_length=3000)
    certifications: list[str] | None = None
    media_kit_url: str | None = Field(None, max_length=500)
    brand_guidelines_url: str | None = Field(None, max_length=500)


class BrandRead(BrandUpdate, TimestampMixin):
    id: str
    village_id: str


# ============================================================================
# Village Profile & Dashboard
# ============================================================================


class VillageProfileRead(HubBase):
    village_id: str
    name: str
    name_en: str | None
    region: str
    country: str
    brand_name: str | None
    brand_logo_url: str | None
    active_modules: list[str]
    total_members: int
    active_sellers: int
    active_tour_guides: int
    monthly_gmv: Decimal
    ecological_metrics: dict[str, Any] | None
    coordinates: dict[str, Any] | None
    capabilities: list[CapabilityRead]
    opportunities_count: int
    projects_count: int
    active_projects_count: int
    total_investment_secured: Decimal


class VillageDashboardRead(HubBase):
    village_id: str
    total_capabilities: int
    total_opportunities: int
    active_projects: int
    completed_projects: int
    total_investment: Decimal
    investment_secured: Decimal
    total_entrepreneurs: int
    registered_events: int
    tourism_services_count: int
    needs_count: int
    recent_opportunities: list[OpportunityRead]
    recent_projects: list[ProjectRead]


class AIOpportunityRecommendations(HubBase):
    village_id: str
    top_capabilities: list[str]
    recommended_opportunities: list[dict[str, Any]]
    missing_needs: list[str]
    recommended_investment: Decimal
    confidence_score: float


# ============================================================================
# VillageExperience
# ============================================================================


class ExperienceCreate(HubBase):
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=3000)
    experience_type: str = Field(..., min_length=2, max_length=50)
    duration_minutes: int | None = Field(None, ge=5, le=1440)
    price_range_min: Decimal | None = None
    price_range_max: Decimal | None = None
    guide_required: bool = False
    max_participants: int | None = Field(None, ge=1)
    image_url: str | None = Field(None, max_length=500)


class ExperienceRead(ExperienceCreate, TimestampMixin):
    id: str
    village_id: str


# ============================================================================
# VillageDestination
# ============================================================================


class DestinationUpdate(HubBase):
    natural_attractions: list[str] | None = None
    cultural_attractions: list[str] | None = None
    experiences: list[str] | None = None
    accommodations: list[str] | None = None
    tagline: str | None = Field(None, max_length=500)
    hero_image_url: str | None = Field(None, max_length=500)


class DestinationRead(DestinationUpdate, TimestampMixin):
    id: str
    village_id: str


# ============================================================================
# B2B Demand
# ============================================================================


class B2BDemandCreate(HubBase):
    buyer_name: str | None = Field(None, max_length=200)
    commodity: str = Field(..., min_length=2, max_length=100)
    category: str | None = Field(None, max_length=50)
    quantity_required: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    frequency: str = Field(default="monthly", max_length=30)
    target_regions: list[str] | None = None
    min_quality_cert: str | None = Field(None, max_length=200)
    price_range: list[dict[str, Any]] | None = None


class B2BDemandRead(B2BDemandCreate, TimestampMixin):
    id: str
    buyer_id: str
    status: str
    matched_villages: list[str]
    closed_at: datetime | None = None


class B2BMatchResponse(HubBase):
    village_id: str
    village_name: str
    capability_id: str
    capability_name: str
    capacity_value: float | None
    unit: str | None
    confidence: str


# ============================================================================
# VillageEngagement
# ============================================================================


class EngagementCreate(HubBase):
    opportunity_id: str | None = None
    project_id: str | None = None
    role: str = Field(
        ..., min_length=2, max_length=30
    )  # executor|investor|supplier|trainer|marketer
    note: str | None = Field(None, max_length=2000)


class EngagementRead(EngagementCreate, TimestampMixin):
    id: str
    user_id: str
    status: str
    responded_at: datetime | None = None


class EngagementListResponse(HubBase):
    engagements: list[EngagementRead]
    count: int


# ============================================================================
# VillageDevelopmentGap
# ============================================================================


class VillageDevelopmentGapCreate(HubBase):
    gap_type: str = Field(..., min_length=2, max_length=50)
    severity: str = Field(default="medium")
    description: str | None = Field(None, max_length=3000)
    proposed_solution: str | None = Field(None, max_length=3000)
    suggested_opportunity_id: str | None = None
    ai_generated: bool = True
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)


class VillageDevelopmentGapRead(VillageDevelopmentGapCreate, TimestampMixin):
    id: str
    village_id: str


# ============================================================================
# VillageFestival
# ============================================================================


class FestivalCreate(HubBase):
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=3000)
    scope: str = Field(default="local", max_length=30)
    mode: str = Field(default="both", max_length=20)
    start_date: datetime | None = None
    end_date: datetime | None = None
    participating_villages: list[str] | None = None
    registration_link: str | None = Field(None, max_length=500)
    featured_products: list[dict[str, Any]] | None = None


class FestivalRead(FestivalCreate, TimestampMixin):
    id: str
    status: str
    created_by: str


# ============================================================================
# NomadicCommunity
# ============================================================================


class NomadicCommunityCreate(HubBase):
    name: str = Field(..., min_length=2, max_length=200)
    name_en: str | None = Field(None, max_length=200)
    region: str | None = Field(None, max_length=200)
    country: str = Field(default="IR", max_length=10)
    capacities: list[dict[str, Any]] | None = None
    tourism_experience: str | None = Field(None, max_length=5000)
    has_tented_accommodation: bool = False
    contact_person: str | None = Field(None, max_length=200)
    contact_phone: str | None = Field(None, max_length=50)


class NomadicCommunityRead(NomadicCommunityCreate, TimestampMixin):
    id: str
    is_approved: bool
    is_active: bool


# ============================================================================
# Village Dossier
# ============================================================================


class VillageDossierRead(HubBase):
    village_id: str
    name: str
    population: int | None
    natural_resources: list[str] | None
    agriculture: list[CapabilityRead]
    handicraft: list[CapabilityRead]
    tourism_services: list[TourismServiceRead]
    events: list[EventRead]
    opportunities: list[OpportunityRead]
    projects: list[ProjectRead]
    needs: list[NeedRead]
    entrepreneurs_count: int
    total_investment: Decimal
    infrastructure: list[str] | None
    vision: str | None


__all__ = [
    # Capabilities
    "CapabilityBase",
    "CapabilityCreate",
    "CapabilityUpdate",
    "CapabilityRead",
    # Opportunities
    "OpportunityBase",
    "OpportunityCreate",
    "OpportunityUpdate",
    "OpportunityRead",
    "OpportunityInterestCreate",
    "OpportunityInterestRead",
    # Projects
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectProgressUpdate",
    "ProjectRead",
    "ProjectInvestorRead",
    # Entrepreneurs
    "EntrepreneurProfileBase",
    "EntrepreneurProfileCreate",
    "EntrepreneurProfileUpdate",
    "EntrepreneurProfileRead",
    "EntrepreneurSearchResponse",
    # Investments
    "InvestmentCreate",
    "InvestmentStatusUpdate",
    "InvestmentRead",
    # Tourism
    "TourismServiceCreate",
    "TourismServiceRead",
    # Events
    "EventCreate",
    "EventRead",
    "EventRegistrationCreate",
    "EventRegistrationRead",
    # Needs
    "NeedCreate",
    "NeedRead",
    # Brand
    "BrandUpdate",
    "BrandRead",
    # Profile & Dashboard
    "VillageProfileRead",
    "VillageDashboardRead",
    "AIOpportunityRecommendations",
    # Experiences
    "ExperienceCreate",
    "ExperienceRead",
    # Destination
    "DestinationUpdate",
    "DestinationRead",
    # B2B
    "B2BDemandCreate",
    "B2BDemandRead",
    "B2BMatchResponse",
    # Engagement
    "EngagementCreate",
    "EngagementRead",
    "EngagementListResponse",
    # Gaps
    "VillageDevelopmentGapCreate",
    "VillageDevelopmentGapRead",
    # Festival
    "FestivalCreate",
    "FestivalRead",
    # Nomadic
    "NomadicCommunityCreate",
    "NomadicCommunityRead",
    # Dossier
    "VillageDossierRead",
]
