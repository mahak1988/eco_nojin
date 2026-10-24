"""Response models for the village_hub router.

Added 2026-10-04. All 49 village_hub routes declared ``response_model=dict`` or
``list``, which renders into ``{"type":"object"}`` with no properties -- so the
shape was unknown to every generated client. This is the single largest untyped
surface left: 48 of the 60 untyped routes in the gateway.

The field sets here were extracted from the ``_serialize_*`` helpers' dict
literals by AST (``scripts``-style measurement, not hand transcription), because
a response_model that omits a key makes FastAPI **drop it from the response**.
Silent field loss is worse than an untyped route, so the models are
``extra="allow"`` and the shape is asserted against the serialisers in
``tests/unit/test_village_hub_schemas.py``.

``extra="allow"`` is the deliberate trade. A closed model here would either drop
fields or start 500ing the moment a column is added to a SQLAlchemy model and
the serialiser starts emitting it. An open model keeps the response identical
and still documents every field a client can rely on.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _VillageModel(BaseModel):
    """Base for the serialised village entities.

    ``extra="allow"`` throughout: see the module docstring. ``populate_by_name``
    is not needed because every serialiser emits the field name verbatim.
    """

    model_config = ConfigDict(extra="allow")


class CapabilityOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    category: str | None = None
    subcategory: str | None = None
    name: str
    name_en: str | None = None
    capacity_value: Any = Field(
        default=None, description="Serialised through _money(), so it is a string."
    )
    unit: str | None = None
    description: str | None = None
    is_active: bool | None = None
    confidence: str | None = None
    source: str | None = None
    created_at: str | None = Field(default=None, description="ISO 8601.")
    updated_at: str | None = Field(default=None, description="ISO 8601.")


class OpportunityOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    capability_id: Any = None
    name: str
    name_en: str | None = None
    category: str | None = None
    description: str | None = None
    business_model: str | None = None
    required_investment: Any = None
    required_skills: list[str] = Field(default_factory=list)
    target_markets: list[str] = Field(default_factory=list)
    expected_revenue: Any = None
    maturity: str | None = None
    status: str | None = None
    created_by: Any = None
    created_at: str | None = None
    updated_at: str | None = None


class ProjectOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    opportunity_id: Any = None
    name: str
    name_en: str | None = None
    description: str | None = None
    category: str | None = None
    status: str | None = None
    progress_pct: Any = None
    investment_needed: Any = None
    investment_secured: Any = None
    investors_count: int | None = None
    start_date: Any = None
    expected_completion: Any = None
    actual_completion: Any = None
    team_size: int | None = None
    created_by: Any = None
    created_at: str | None = None
    updated_at: str | None = None


class TourismServiceOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    owner_user_id: Any = None
    service_type: str | None = None
    name: str
    name_en: str | None = None
    description: str | None = None
    location: str | None = None
    coordinates: Any = None
    price_per_unit: Any = None
    capacity: int | None = None
    is_organic: bool | None = None
    is_regenerative: bool | None = None
    images: list[str] = Field(default_factory=list)
    contact_phone: str | None = None
    contact_email: str | None = None
    is_verified: bool | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EventOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    title: str
    title_en: str | None = None
    description: str | None = None
    event_type: str | None = None
    start_date: Any = None
    end_date: Any = None
    location: str | None = None
    coordinates: Any = None
    max_participants: int | None = None
    registration_fee: Any = None
    status: str | None = None
    images: list[str] = Field(default_factory=list)
    created_by: Any = None
    created_at: str | None = None
    updated_at: str | None = None
    registrations_count: int | None = None


class NeedOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    category: str | None = None
    title: str
    description: str | None = None
    priority: str | None = None
    estimated_investment: Any = None
    is_resolved: bool | None = None
    resolved_by: Any = None
    resolved_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BrandOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    story: str | None = None
    vision: str | None = None
    values: list[str] = Field(default_factory=list)
    heritage: str | None = None
    certifications: list[str] = Field(default_factory=list)
    media_kit_url: str | None = None
    brand_guidelines_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class InvestmentOut(_VillageModel):
    id: Any = None
    project_id: Any = None
    investor_user_id: Any = None
    amount: Any = None
    currency: str | None = None
    status: str | None = None
    notes: str | None = None
    confirmed_by: Any = None
    created_at: str | None = None
    confirmed_at: str | None = None


class EntrepreneurProfileOut(_VillageModel):
    id: Any = None
    user_id: Any = None
    village_id: Any = None
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    capacity_description: str | None = None
    experience_years: Any = None
    is_available: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class InterestOut(_VillageModel):
    id: Any = None
    opportunity_id: Any = None
    entrepreneur_id: Any = None
    status: str | None = None
    note: str | None = None
    expressed_at: str | None = None


class EventRegistrationOut(_VillageModel):
    id: Any = None
    event_id: Any = None
    user_id: Any = None
    status: str | None = None
    registration_fee: Any = None
    payment_reference: str | None = None
    created_at: str | None = None
    confirmed_at: str | None = None


class ExperienceOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    name: str
    name_en: str | None = None
    description: str | None = None
    experience_type: str | None = None
    duration_minutes: int | None = None
    price_range_min: Any = None
    price_range_max: Any = None
    guide_required: bool | None = None
    max_participants: int | None = None
    image_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DestinationOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    natural_attractions: list[Any] = Field(default_factory=list)
    cultural_attractions: list[Any] = Field(default_factory=list)
    experiences: list[Any] = Field(default_factory=list)
    accommodations: list[Any] = Field(default_factory=list)
    tagline: str | None = None
    hero_image_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class B2BDemandOut(_VillageModel):
    id: Any = None
    buyer_id: Any = None
    buyer_name: str | None = None
    commodity: str | None = None
    category: str | None = None
    quantity_required: Any = None
    unit: str | None = None
    frequency: str | None = None
    target_regions: list[str] = Field(default_factory=list)
    min_quality_cert: str | None = None
    price_range: Any = None
    status: str | None = None
    matched_villages: list[Any] = Field(default_factory=list)
    created_at: str | None = None
    closed_at: str | None = None


class EngagementOut(_VillageModel):
    id: Any = None
    user_id: Any = None
    opportunity_id: Any = None
    project_id: Any = None
    role: str | None = None
    status: str | None = None
    note: str | None = None
    created_at: str | None = None
    responded_at: str | None = None


class GapOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    gap_type: str | None = None
    severity: str | None = None
    description: str | None = None
    proposed_solution: str | None = None
    suggested_opportunity_id: Any = None
    ai_generated: bool | None = None
    confidence_score: Any = None
    created_at: str | None = None


class FestivalOut(_VillageModel):
    id: Any = None
    name: str
    name_en: str | None = None
    description: str | None = None
    scope: str | None = None
    mode: str | None = None
    start_date: Any = None
    end_date: Any = None
    participating_villages: list[Any] = Field(default_factory=list)
    registration_link: str | None = None
    featured_products: list[Any] = Field(default_factory=list)
    status: str | None = None
    created_by: Any = None
    created_at: str | None = None
    updated_at: str | None = None


class NomadicOut(_VillageModel):
    id: Any = None
    village_id: Any = None
    owner_user_id: Any = None
    created_by: Any = None
    name: str
    name_en: str | None = None
    region: str | None = None
    country: str | None = None
    capacities: list[Any] = Field(default_factory=list)
    pasture_area_ha: Any = None
    migration_route: Any = None
    herd_size_estimate: int | None = None
    tourism_experience: str | None = None
    has_tented_accommodation: bool | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    is_approved: bool | None = None
    is_active: bool | None = None
    approved_by: Any = None
    approved_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ExistsOut(BaseModel):
    """The ``{"exists": bool}`` shape returned by several probes."""

    model_config = ConfigDict(extra="allow")

    exists: bool


# ---------------------------------------------------------------------------
# Aggregates. These five routes delegate to services/marketplace/hub_service.py,
# so their shapes were read from that file rather than from the router:
#   get_village_dashboard   hub_service.py:195   13 keys
#   get_village_profile     hub_service.py:140   13 keys
#   get_village_dossier     hub_service.py:1235  12 keys
#   get_project_investors   hub_service.py:570   5 keys, list
#   match_b2b_demands       hub_service.py:1060  9 keys, list
#   ai_recommendations      hub_service.py:946   see below
# ---------------------------------------------------------------------------


class VillageDashboardOut(BaseModel):
    """get_village_dashboard. `recent_*` are serialised opportunity/project dicts."""

    model_config = ConfigDict(extra="allow")

    village_id: Any = None
    total_capabilities: int | None = None
    total_opportunities: int | None = None
    active_projects: int | None = None
    completed_projects: int | None = None
    total_investment: Any = None
    investment_secured: Any = None
    total_entrepreneurs: int | None = None
    registered_events: int | None = None
    tourism_services_count: int | None = None
    needs_count: int | None = None
    recent_opportunities: list[Any] = Field(default_factory=list)
    recent_projects: list[Any] = Field(default_factory=list)


class VillageProfileOut(BaseModel):
    """get_village_profile. `active_modules` and the counts come from the hub."""

    model_config = ConfigDict(extra="allow")

    village_id: Any = None
    name: str | None = None
    region: str | None = None
    brand_name: str | None = None
    active_modules: list[Any] = Field(default_factory=list)
    total_members: int | None = None
    monthly_gmv: Any = None
    capabilities: list[Any] = Field(default_factory=list)
    opportunities_count: int | None = None
    projects_count: int | None = None
    active_projects_count: int | None = None
    total_investment_secured: Any = None
    total_entrepreneurs: int | None = None


class VillageDossierOut(BaseModel):
    """get_village_dossier -- the printable village summary."""

    model_config = ConfigDict(extra="allow")

    village_id: Any = None
    name: str | None = None
    population: Any = None
    agriculture: Any = None
    handicraft: Any = None
    tourism_services: Any = None
    events: Any = None
    opportunities: Any = None
    projects: Any = None
    needs: Any = None
    entrepreneurs_count: int | None = None
    total_investment: Any = None


class ProjectInvestorOut(BaseModel):
    """One entry of get_project_investors (hub_service.py:570).

    Note this is *not* InvestmentOut: the service returns a trimmed dict with
    `invested_at` rather than `created_at` and no `id`. Two shapes for one
    entity, which is why both models exist.
    """

    model_config = ConfigDict(extra="allow")

    user_id: Any = None
    amount: Any = None
    currency: str | None = None
    status: str | None = None
    invested_at: str | None = None


class B2BMatchOut(BaseModel):
    """One entry of match_b2b_demands (hub_service.py:1060): a demand joined to a
    matching local capability. `quantity_required` and `capacity_value` both go
    through _money()."""

    model_config = ConfigDict(extra="allow")

    demand_id: Any = None
    buyer_name: str | None = None
    commodity: str | None = None
    quantity_required: Any = None
    unit: str | None = None
    frequency: str | None = None
    capability_id: Any = None
    capability_name: str | None = None
    capacity_value: Any = None
    unit_cap: str | None = None
    confidence: str | None = None


class AIRecommendationOut(BaseModel):
    """One entry of ai_recommendations' `recommendations` list."""

    model_config = ConfigDict(extra="allow")

    capability_id: Any = None
    score: Any = None
    rationale: str | None = None


class AIRecommendationsOut(BaseModel):
    """ai_recommendations (hub_service.py:946).

    The router's own docstring records that the underlying implementation is a
    stub, and this route is session-guarded precisely because `missing_needs`
    exposes a village's unresolved community-submitted needs for any village id.
    That is why `missing_needs` is typed explicitly rather than left to
    extra="allow": a client needs to know the field is populated from real
    community submissions and is not a recommendation.
    """

    model_config = ConfigDict(extra="allow")

    village_id: Any = None
    recommendations: list[AIRecommendationOut] = Field(default_factory=list)
    missing_needs: list[str] = Field(
        default_factory=list,
        description="Titles of the village's unresolved needs. NOT a recommendation.",
    )
