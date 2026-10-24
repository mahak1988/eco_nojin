"""API endpoints for Village Development Hub.

All endpoints are mounted under `/api/v1/marketplace/villages/{villageId}/...`
to reuse the existing village-scoped marketplace infrastructure.
"""
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database.hub import hub
from database.models import User
from services.api_gateway.auth import require_admin as _require_admin
from services.api_gateway.auth import require_user
from services.api_gateway.errors import safe_detail_for_status
from services.landscape.models import LandscapeVillage
from services.marketplace.hub_service import PermissionDenied
from services.marketplace.models.village_hub import (
    B2BDemand,
    EntrepreneurProfile,
    NomadicCommunity,
    VillageBrand,
    VillageCapability,
    VillageDestination,
    VillageDevelopmentGap,
    VillageEngagement,
    VillageEvent,
    VillageEventRegistration,
    VillageExperience,
    VillageFestival,
    VillageInvestment,
    VillageNeed,
    VillageOpportunity,
    VillageOpportunityInterest,
    VillageProject,
    VillageTourismService,
)
from services.marketplace.schemas.hub_schemas import (
    B2BDemandCreate,
    B2BMatchConfirm,
    BrandUpdate,
    CapabilityCreate,
    CapabilityUpdate,
    DestinationUpdate,
    EngagementCreate,
    EntrepreneurProfileUpdate,
    EventCreate,
    ExperienceCreate,
    FestivalCreate,
    InvestmentCreate,
    NeedCreate,
    NomadicCommunityApprove,
    NomadicCommunityCreate,
    NomadicCommunityUpdate,
    OpportunityCreate,
    OpportunityInterestCreate,
    OpportunityUpdate,
    ProjectCreate,
    ProjectProgressUpdate,
    TerritoryFundInvestmentCreate,
    TourismServiceCreate,
    VillageDevelopmentGapCreate,
)
from services.marketplace.service import get_hub_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/marketplace/villages",
    tags=["marketplace-village-hub"],
)


async def _get_db():
    async with hub.get_async_session() as session:
        yield session


def _require_admin(user: Annotated[User, Depends(_require_admin)]):
    return user


# ============================================================================
# Helpers
# ============================================================================


def _serialize_capability(cap: VillageCapability) -> dict:
    return {
        "id": cap.id,
        "village_id": cap.village_id,
        "category": cap.category,
        "subcategory": cap.subcategory,
        "name": cap.name,
        "name_en": cap.name_en,
        "capacity_value": float(cap.capacity_value) if cap.capacity_value else None,
        "unit": cap.unit,
        "description": cap.description,
        "is_active": cap.is_active,
        "confidence": cap.confidence,
        "source": cap.source,
        "created_at": cap.created_at.isoformat() if cap.created_at else None,
        "updated_at": cap.updated_at.isoformat() if cap.updated_at else None,
    }


def _serialize_opportunity(opp: VillageOpportunity) -> dict:
    return {
        "id": opp.id,
        "village_id": opp.village_id,
        "capability_id": opp.capability_id,
        "name": opp.name,
        "name_en": opp.name_en,
        "category": opp.category,
        "description": opp.description,
        "business_model": opp.business_model,
        "required_investment": float(opp.required_investment) if opp.required_investment else 0,
        "required_skills": opp.required_skills or [],
        "target_markets": opp.target_markets or [],
        "expected_revenue": float(opp.expected_revenue) if opp.expected_revenue else 0,
        "maturity": opp.maturity,
        "status": opp.status,
        "created_by": opp.created_by,
        "created_at": opp.created_at.isoformat() if opp.created_at else None,
        "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
    }


def _serialize_project(proj: VillageProject) -> dict:
    return {
        "id": proj.id,
        "village_id": proj.village_id,
        "opportunity_id": proj.opportunity_id,
        "name": proj.name,
        "name_en": proj.name_en,
        "description": proj.description,
        "category": proj.category,
        "status": proj.status,
        "progress_pct": proj.progress_pct,
        "investment_needed": float(proj.investment_needed) if proj.investment_needed else 0,
        "investment_secured": float(proj.investment_secured),
        "investors_count": proj.investors_count,
        "start_date": proj.start_date.isoformat() if proj.start_date else None,
        "expected_completion": proj.expected_completion.isoformat()
        if proj.expected_completion
        else None,
        "actual_completion": proj.actual_completion.isoformat() if proj.actual_completion else None,
        "team_size": proj.team_size,
        "created_by": proj.created_by,
        "created_at": proj.created_at.isoformat() if proj.created_at else None,
        "updated_at": proj.updated_at.isoformat() if proj.updated_at else None,
    }


def _serialize_tourism_service(svc: VillageTourismService) -> dict:
    return {
        "id": svc.id,
        "village_id": svc.village_id,
        "owner_user_id": svc.owner_user_id,
        "service_type": svc.service_type,
        "name": svc.name,
        "name_en": svc.name_en,
        "description": svc.description,
        "location": svc.location,
        "coordinates": svc.coordinates,
        "price_per_unit": float(svc.price_per_unit) if svc.price_per_unit else None,
        "capacity": svc.capacity,
        "is_organic": svc.is_organic,
        "is_regenerative": svc.is_regenerative,
        "images": svc.images or [],
        "contact_phone": svc.contact_phone,
        "contact_email": svc.contact_email,
        "is_verified": svc.is_verified,
        "status": svc.status,
        "created_at": svc.created_at.isoformat() if svc.created_at else None,
        "updated_at": svc.updated_at.isoformat() if svc.updated_at else None,
    }


def _serialize_event(evt: VillageEvent) -> dict:
    registrations_count = len(evt.registrations) if evt.registrations else 0
    return {
        "id": evt.id,
        "village_id": evt.village_id,
        "title": evt.title,
        "title_en": evt.title_en,
        "description": evt.description,
        "event_type": evt.event_type,
        "start_date": evt.start_date.isoformat() if evt.start_date else None,
        "end_date": evt.end_date.isoformat() if evt.end_date else None,
        "location": evt.location,
        "coordinates": evt.coordinates,
        "max_participants": evt.max_participants,
        "registration_fee": float(evt.registration_fee),
        "status": evt.status,
        "images": evt.images or [],
        "created_by": evt.created_by,
        "created_at": evt.created_at.isoformat() if evt.created_at else None,
        "updated_at": evt.updated_at.isoformat() if evt.updated_at else None,
        "registrations_count": registrations_count,
    }


def _serialize_need(need: VillageNeed) -> dict:
    return {
        "id": need.id,
        "village_id": need.village_id,
        "category": need.category,
        "title": need.title,
        "description": need.description,
        "priority": need.priority,
        "estimated_investment": float(need.estimated_investment)
        if need.estimated_investment
        else None,
        "is_resolved": need.is_resolved,
        "resolved_by": need.resolved_by,
        "resolved_at": need.resolved_at.isoformat() if need.resolved_at else None,
        "created_at": need.created_at.isoformat() if need.created_at else None,
        "updated_at": need.updated_at.isoformat() if need.updated_at else None,
    }


def _serialize_brand(brand: VillageBrand) -> dict:
    return {
        "id": brand.id,
        "village_id": brand.village_id,
        "story": brand.story,
        "vision": brand.vision,
        "values": brand.values or [],
        "heritage": brand.heritage,
        "certifications": brand.certifications or [],
        "media_kit_url": brand.media_kit_url,
        "brand_guidelines_url": brand.brand_guidelines_url,
        "created_at": brand.created_at.isoformat() if brand.created_at else None,
        "updated_at": brand.updated_at.isoformat() if brand.updated_at else None,
    }


def _serialize_investment(inv: VillageInvestment) -> dict:
    return {
        "id": inv.id,
        "project_id": inv.project_id,
        "investor_user_id": inv.investor_user_id,
        "amount": float(inv.amount),
        "currency": inv.currency,
        "status": inv.status,
        "notes": inv.notes,
        "confirmed_by": inv.confirmed_by,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "confirmed_at": inv.confirmed_at.isoformat() if inv.confirmed_at else None,
    }


def _serialize_entrepreneur_profile(profile: EntrepreneurProfile) -> dict:
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "village_id": profile.village_id,
        "skills": profile.skills or [],
        "interests": profile.interests or [],
        "capacity_description": profile.capacity_description,
        "experience_years": profile.experience_years,
        "is_available": profile.is_available,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _serialize_interest(interest: VillageOpportunityInterest) -> dict:
    return {
        "id": interest.id,
        "opportunity_id": interest.opportunity_id,
        "entrepreneur_id": interest.entrepreneur_id,
        "status": interest.status,
        "note": interest.note,
        "expressed_at": interest.expressed_at.isoformat() if interest.expressed_at else None,
    }


def _serialize_event_registration(reg: VillageEventRegistration) -> dict:
    return {
        "id": reg.id,
        "event_id": reg.event_id,
        "user_id": reg.user_id,
        "status": reg.status,
        "registration_fee": float(reg.registration_fee),
        "payment_reference": reg.payment_reference,
        "created_at": reg.created_at.isoformat() if reg.created_at else None,
        "confirmed_at": reg.confirmed_at.isoformat() if reg.confirmed_at else None,
    }


async def _get_village_name(village_id: str) -> str:
    """Fetch village name — used in profile responses."""
    with hub.get_session() as session:
        v = session.get(LandscapeVillage, village_id)
    return v.name if v else village_id


# ============================================================================
# 11. Experiences
# ============================================================================


def _serialize_experience(exp: VillageExperience) -> dict:
    return {
        "id": exp.id,
        "village_id": exp.village_id,
        "name": exp.name,
        "name_en": exp.name_en,
        "description": exp.description,
        "experience_type": exp.experience_type,
        "duration_minutes": exp.duration_minutes,
        "price_range_min": float(exp.price_range_min) if exp.price_range_min else None,
        "price_range_max": float(exp.price_range_max) if exp.price_range_max else None,
        "guide_required": exp.guide_required,
        "max_participants": exp.max_participants,
        "image_url": exp.image_url,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
    }


# ============================================================================
# 12. Destination
# ============================================================================


def _serialize_destination(dest: VillageDestination) -> dict:
    return {
        "id": dest.id,
        "village_id": dest.village_id,
        "natural_attractions": dest.natural_attractions or [],
        "cultural_attractions": dest.cultural_attractions or [],
        "experiences": dest.experiences or [],
        "accommodations": dest.accommodations or [],
        "tagline": dest.tagline,
        "hero_image_url": dest.hero_image_url,
        "created_at": dest.created_at.isoformat() if dest.created_at else None,
        "updated_at": dest.updated_at.isoformat() if dest.updated_at else None,
    }


# ============================================================================
# 13. B2B Demands
# ============================================================================


def _serialize_b2b_demand(demand: B2BDemand) -> dict:
    return {
        "id": demand.id,
        "buyer_id": demand.buyer_id,
        "buyer_name": demand.buyer_name,
        "commodity": demand.commodity,
        "category": demand.category,
        "quantity_required": float(demand.quantity_required),
        "unit": demand.unit,
        "frequency": demand.frequency,
        "target_regions": demand.target_regions or [],
        "min_quality_cert": demand.min_quality_cert,
        "price_range": demand.price_range or [],
        "status": demand.status,
        "matched_villages": demand.matched_villages or [],
        "created_at": demand.created_at.isoformat() if demand.created_at else None,
        "closed_at": demand.closed_at.isoformat() if demand.closed_at else None,
    }


# ============================================================================
# 14. Village Engagement
# ============================================================================


def _serialize_engagement(eng: VillageEngagement) -> dict:
    return {
        "id": eng.id,
        "user_id": eng.user_id,
        "opportunity_id": eng.opportunity_id,
        "project_id": eng.project_id,
        "role": eng.role,
        "status": eng.status,
        "note": eng.note,
        "created_at": eng.created_at.isoformat() if eng.created_at else None,
        "responded_at": eng.responded_at.isoformat() if eng.responded_at else None,
    }


# ============================================================================
# 15. Development Gaps (AI)
# ============================================================================


def _serialize_gap(gap: VillageDevelopmentGap) -> dict:
    return {
        "id": gap.id,
        "village_id": gap.village_id,
        "gap_type": gap.gap_type,
        "severity": gap.severity,
        "description": gap.description,
        "proposed_solution": gap.proposed_solution,
        "suggested_opportunity_id": gap.suggested_opportunity_id,
        "ai_generated": gap.ai_generated,
        "confidence_score": float(gap.confidence_score) if gap.confidence_score else None,
        "created_at": gap.created_at.isoformat() if gap.created_at else None,
    }


# ============================================================================
# 16. Festivals & Exhibitions
# ============================================================================


def _serialize_festival(f: VillageFestival) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "name_en": f.name_en,
        "description": f.description,
        "scope": f.scope,
        "mode": f.mode,
        "start_date": f.start_date.isoformat() if f.start_date else None,
        "end_date": f.end_date.isoformat() if f.end_date else None,
        "participating_villages": f.participating_villages or [],
        "registration_link": f.registration_link,
        "featured_products": f.featured_products or [],
        "status": f.status,
        "created_by": f.created_by,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }


# ============================================================================
# 17. Nomadic Communities
# ============================================================================


def _serialize_nomadic(community: NomadicCommunity) -> dict:
    return {
        "id": community.id,
        "village_id": community.village_id,
        "owner_user_id": community.owner_user_id,
        "created_by": community.created_by,
        "name": community.name,
        "name_en": community.name_en,
        "region": community.region,
        "country": community.country,
        "capacities": community.capacities or [],
        "pasture_area_ha": float(community.pasture_area_ha)
        if community.pasture_area_ha
        else None,
        "migration_route": community.migration_route,
        "herd_size_estimate": community.herd_size_estimate,
        "tourism_experience": community.tourism_experience,
        "has_tented_accommodation": community.has_tented_accommodation,
        "contact_person": community.contact_person,
        "contact_phone": community.contact_phone,
        "is_approved": community.is_approved,
        "is_active": community.is_active,
        "approved_by": community.approved_by,
        "approved_at": community.approved_at.isoformat() if community.approved_at else None,
        "created_at": community.created_at.isoformat() if community.created_at else None,
        "updated_at": community.updated_at.isoformat() if community.updated_at else None,
    }

# ==========================================================================
# Global (non-village-scoped) routes - registered FIRST so their literal
# paths are matched before the parameterized village routes below.
# ==========================================================================


@router.post("/opportunities/{opportunity_id}/interest", response_model=dict)
async def express_interest(
    opportunity_id: str,
    payload: OpportunityInterestCreate | None = None,
    user: Annotated[User, Depends(require_user)] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """یک کارآفرین علاقه خود را به یک فرصت اعلام می‌کند."""
    service = get_hub_service(db)
    try:
        note = payload.note if payload else None
        interest = await service.express_interest(opportunity_id, user.id, note)
        return _serialize_interest(interest)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/opportunities", response_model=list)
async def search_opportunities(
    q: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    village_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    user: Annotated[User, Depends(require_user)] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """جستجو در تمام فرصت‌های توسعهٔ همه روستاها."""
    service = get_hub_service(db)
    opps = await service.search_opportunities(q=q, category=category, village_id=village_id, limit=limit)
    return [_serialize_opportunity(o) for o in opps]


# ============================================================================
# 5. Entrepreneurs
# ============================================================================


@router.get("/entrepreneurs/me", response_model=dict)
async def get_my_entrepreneur_profile(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """دریافت پروفایل کارآفرین جاری."""
    service = get_hub_service(db)
    profile = await service.get_entrepreneur_profile(user.id)
    if not profile:
        return {"exists": False}
    return _serialize_entrepreneur_profile(profile)


@router.put("/entrepreneurs/me", response_model=dict)
async def upsert_my_entrepreneur_profile(
    payload: EntrepreneurProfileUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ایجاد یا بروزرسانی پروفایل کارآفرین جاری."""
    service = get_hub_service(db)
    profile = await service.upsert_entrepreneur_profile(
        user.id, payload.model_dump(exclude_unset=True)
    )
    return _serialize_entrepreneur_profile(profile)


@router.get("/entrepreneurs", response_model=dict)
async def search_entrepreneurs(
    q: Annotated[str | None, Query()] = None,
    village_id: Annotated[str | None, Query()] = None,
    skills: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """جستجوی کارآفرینان بر اساس مهارت یا روستا."""
    service = get_hub_service(db)
    profiles = await service.search_entrepreneurs(skills=skills, village_id=village_id)
    if q:
        profiles = [p for p in profiles if q.lower() in (p.capacity_description or "").lower()]
    return {
        "profiles": [_serialize_entrepreneur_profile(p) for p in profiles],
        "count": len(profiles),
    }


# ============================================================================
# 6. Investments
# ============================================================================


@router.post("/investments", response_model=dict)
async def create_investment(
    payload: InvestmentCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت سرمایه‌گذاری در یک پروژه."""
    service = get_hub_service(db)
    try:
        inv = await service.create_investment(
            payload.project_id,
            payload.amount,
            user.id,
            payload.notes,
        )
        return _serialize_investment(inv)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/investments", response_model=list)
async def get_my_investments(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """دریافت سرمایه‌گذاری‌های فعلی کاربر."""
    service = get_hub_service(db)
    investments = await service.get_my_investments(user.id)
    return [_serialize_investment(i) for i in investments]


@router.post("/investments/from-territory-fund", response_model=dict)
async def invest_from_territory_fund(
    payload: TerritoryFundInvestmentCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """تخصیص از صندوق قلمرو به یک پروژه روستا."""
    service = get_hub_service(db)
    try:
        inv = await service.invest_from_territory_fund(
            territory_id=payload.territory_id,
            territory_fund_id=payload.territory_fund_id,
            project_id=payload.project_id,
            amount=payload.amount,
            notes=payload.notes,
        )
        return {
            "id": inv.id,
            "project_id": inv.project_id,
            "amount": str(inv.amount),
            "currency": inv.currency,
            "status": inv.status,
            "territory_id": inv.territory_id,
            "territory_fund_id": inv.territory_fund_id,
            "confirmed_at": inv.confirmed_at.isoformat() if inv.confirmed_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/events/{event_id}/register", response_model=dict)
async def register_for_event(
    event_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت‌نام کاربر در یک رویداد."""
    service = get_hub_service(db)
    try:
        reg = await service.register_event(event_id, user.id)
        return _serialize_event_registration(reg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/b2b/demands", response_model=dict)
async def create_b2b_demand(
    payload: B2BDemandCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت درخواست خرید B2B از یک شرکت/فروشگاه."""
    service = get_hub_service(db)
    return _serialize_b2b_demand(
        await service.create_b2b_demand(payload.model_dump(exclude_unset=True), user.id)
    )


@router.get("/b2b/demands/my", response_model=list)
async def get_my_b2b_demands(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """دریافت درخواست‌های B2B ثبت‌شده توسط کاربر."""
    service = get_hub_service(db)
    demands = await service.get_b2b_demands_for_buyer(user.id)
    return [_serialize_b2b_demand(d) for d in demands]


@router.get("/b2b/matches/{village_id}", response_model=list)
async def get_b2b_matches(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """یافتن درخواست‌های B2B مناسب یک روستا."""
    service = get_hub_service(db)
    try:
        return await service.match_b2b_demands(village_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/b2b/matches/confirm", response_model=dict)
async def confirm_b2b_match(
    payload: B2BMatchConfirm,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """تأیید نهایی تطبیق درخواست B2B با فرصت روستا."""
    service = get_hub_service(db)
    try:
        return await service.confirm_b2b_match(
            demand_id=payload.demand_id,
            opportunity_id=payload.opportunity_id,
            confirmed_by=str(user.id),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/engagements", response_model=dict)
async def create_engagement(
    payload: EngagementCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت علاقه یا شرکت در یک فرصت/پروژه."""
    service = get_hub_service(db)
    eng = await service.create_engagement(payload.model_dump(exclude_unset=True), user.id)
    return _serialize_engagement(eng)


@router.get("/opportunities/{opportunity_id}/team", response_model=list)
async def get_opportunity_team(opportunity_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت لیست تیم یک فرصت (تیم قبول‌شده‌ها)."""
    service = get_hub_service(db)
    team = await service.get_opportunity_team(opportunity_id)
    return [_serialize_engagement(e) for e in team]


@router.get("/projects/{project_id}/engaged", response_model=list)
async def get_project_engagements(project_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت لیست مشارکت‌کنندگان در یک پروژه."""
    service = get_hub_service(db)
    engagements = await service.get_project_engagements(project_id)
    return [_serialize_engagement(e) for e in engagements]


@router.post("/festivals", response_model=dict)
async def create_festival(
    payload: FestivalCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ایجاد جشنواره یا نمایشگاه."""
    service = get_hub_service(db)
    fest = await service.create_festival(payload.model_dump(exclude_unset=True), user.id)
    return _serialize_festival(fest)


@router.get("/nomadic-communities", response_model=list)
async def list_nomadic_communities(
    approved_only: Annotated[bool, Query()] = True, db: Annotated[Any, Depends(_get_db)] = None
):
    """لیست جوامع عشایری."""
    service = get_hub_service(db)
    communities = await service.get_nomadic_communities(approved_only)
    return [_serialize_nomadic(c) for c in communities]


@router.post("/nomadic-communities", response_model=dict)
async def create_nomadic_community(
    payload: NomadicCommunityCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت یک جامعهٔ عشایری تازه (نیازمند تأیید برای نمایش عمومی)."""
    service = get_hub_service(db)
    try:
        community = await service.create_nomadic_community(
            payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_nomadic(community)
    except ValueError as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDenied) else 400,
            detail=safe_detail_for_status(e, 403),
        ) from e


@router.get("/nomadic-communities/{community_id}", response_model=dict)
async def get_nomadic_community(
    community_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """جزئیات یک جامعهٔ عشایری."""
    service = get_hub_service(db)
    try:
        community = await service.get_nomadic_community(community_id)
        return _serialize_nomadic(community)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.patch("/nomadic-communities/{community_id}/approve", response_model=dict)
async def approve_nomadic_community(
    community_id: str,
    payload: NomadicCommunityApprove | None = None,
    user: Annotated[User, Depends(require_user)] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """تأیید یک جامعهٔ عشایری — ادمین پلتفرم یا عضو حکمرانی فعال."""
    service = get_hub_service(db)
    try:
        community = await service.approve_nomadic_community(community_id, user.id)
        return _serialize_nomadic(community)
    except ValueError as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDenied) else 404,
            detail=safe_detail_for_status(e, 403),
        ) from e


@router.put("/nomadic-communities/{community_id}", response_model=dict)
async def update_nomadic_community(
    community_id: str,
    payload: NomadicCommunityUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """بروزرسانی یک جامعهٔ عشایری — مالک یا حکمرانی/ادمین."""
    service = get_hub_service(db)
    try:
        community = await service.update_nomadic_community(
            community_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_nomadic(community)
    except ValueError as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDenied) else 404,
            detail=safe_detail_for_status(e, 403),
        ) from e


@router.delete(
    "/nomadic-communities/{community_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_nomadic_community(
    community_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """حذف یک جامعهٔ عشایری — مالک یا حکمرانی/ادمین."""
    service = get_hub_service(db)
    try:
        await service.delete_nomadic_community(community_id, user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=403 if isinstance(e, PermissionDenied) else 404,
            detail=safe_detail_for_status(e, 403),
        ) from e

# ==========================================================================
# Village-scoped routes (village-id parameterized) - registered LAST.
# Starlette matches routes in registration order, so these must follow every
# literal path above; previously the first route here shadowed the four globals.
# ==========================================================================


# ============================================================================
# 1. Village Profile & Dashboard
# ============================================================================


@router.get("/{village_id}", response_model=dict)
async def get_village_profile(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت پروفایل کامل روستا با تمام ماژول‌ها."""
    service = get_hub_service(db)
    try:
        profile = await service.get_village_profile(village_id)
        profile["name"] = await _get_village_name(village_id)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/{village_id}/dashboard", response_model=dict)
async def get_village_dashboard(
    village_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """دریافت داشبورد توسعهٔ روستا."""
    service = get_hub_service(db)
    try:
        return await service.get_village_dashboard(village_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


# ============================================================================
# 2. Capabilities
# ============================================================================


@router.get("/{village_id}/capabilities", response_model=list)
async def list_capabilities(
    village_id: str,
    category: Annotated[str | None, Query()] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """لیست ظرفیت‌های اقتصادی/گردشگيری روستا — دسترسی عمومی (directory lookup)."""
    service = get_hub_service(db)
    try:
        caps = await service.get_village_capabilities(village_id, category)
        return [_serialize_capability(c) for c in caps]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/capabilities", response_model=dict)
async def create_capability(
    village_id: str,
    payload: CapabilityCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ایجاد یا بروزرسانی یک ظرفیت روستا."""
    service = get_hub_service(db)
    try:
        cap = await service.create_capability(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_capability(cap)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/{village_id}/capabilities/{capability_id}", response_model=dict)
async def get_capability(
    village_id: str, capability_id: str, user: Annotated[User, Depends(require_user)]
):
    """جزئیات یک ظرفیت."""
    with hub.get_session() as session:
        cap = session.get(VillageCapability, capability_id)
    if not cap or cap.village_id != village_id:
        raise HTTPException(status_code=404, detail="ظرفیت یافت نشد")
    return _serialize_capability(cap)


@router.put("/{village_id}/capabilities/{capability_id}", response_model=dict)
async def update_capability(
    village_id: str,
    capability_id: str,
    payload: CapabilityUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """بروزرسانی ظرفیت — نیاز به دسترسی حکمرانی."""
    service = get_hub_service(db)
    try:
        cap = await service.update_capability(
            capability_id, payload.model_dump(exclude_unset=True), user
        )
        return _serialize_capability(cap)
    except ValueError as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionDenied) else 404, detail=safe_detail_for_status(e, 403)) from e


@router.delete("/{village_id}/capabilities/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_capability(
    village_id: str,
    capability_id: str,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """حذف ظرفیت."""
    service = get_hub_service(db)
    try:
        await service.delete_capability(capability_id, user)
    except ValueError as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionDenied) else 404, detail=safe_detail_for_status(e, 403)) from e


# ============================================================================
# 3. Opportunities
# ============================================================================


@router.get("/{village_id}/opportunities", response_model=list)
async def list_opportunities(
    village_id: str,
    maturity: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    user: Annotated[User, Depends(require_user)] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """لیست فرصت‌های توسعهٔ روستا."""
    service = get_hub_service(db)
    try:
        opps = await service.get_village_opportunities(village_id, maturity, status)
        return [_serialize_opportunity(o) for o in opps]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/opportunities", response_model=dict)
async def create_opportunity(
    village_id: str,
    payload: OpportunityCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ایجاد فرصت توسعه جدید."""
    service = get_hub_service(db)
    try:
        opp = await service.create_opportunity(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_opportunity(opp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/{village_id}/opportunities/{opportunity_id}", response_model=dict)
async def get_opportunity(
    village_id: str,
    opportunity_id: str,
    user: Annotated[User, Depends(require_user)],
):
    """جزئیات یک فرصت."""
    with hub.get_session() as session:
        opp = session.get(VillageOpportunity, opportunity_id)
    if not opp or opp.village_id != village_id:
        raise HTTPException(status_code=404, detail="فرصت یافت نشد")
    result = _serialize_opportunity(opp)
    result["interests_count"] = len(opp.interests) if opp.interests else 0
    return result


@router.put("/{village_id}/opportunities/{opportunity_id}", response_model=dict)
async def update_opportunity(
    village_id: str,
    opportunity_id: str,
    payload: OpportunityUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """بروزرسانی فرصت توسعه."""
    service = get_hub_service(db)
    try:
        opp = await service.update_opportunity(
            opportunity_id, payload.model_dump(exclude_unset=True), user
        )
        return _serialize_opportunity(opp)
    except ValueError as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionDenied) else 404, detail=safe_detail_for_status(e, 403)) from e


# ============================================================================
# 4. Projects
# ============================================================================


@router.get("/{village_id}/projects", response_model=list)
async def list_projects(
    village_id: str,
    status: Annotated[str | None, Query()] = None,
    user: Annotated[User, Depends(require_user)] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """لیست پروژه‌های در حال اجرا در روستا."""
    service = get_hub_service(db)
    try:
        projects = await service.get_village_projects(village_id, status)
        return [_serialize_project(p) for p in projects]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/projects", response_model=dict)
async def create_project(
    village_id: str,
    payload: ProjectCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ایجاد یا بروزرسانی یک پروژه توسعه."""
    service = get_hub_service(db)
    try:
        proj = await service.create_project(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_project(proj)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.put("/{village_id}/projects/{project_id}/progress", response_model=dict)
async def update_project_progress(
    village_id: str,
    project_id: str,
    payload: ProjectProgressUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """بروزرسانی درصد پیشرفت یک پروژه."""
    service = get_hub_service(db)
    try:
        proj = await service.update_project_progress(project_id, payload.progress_pct, user)
        return _serialize_project(proj)
    except ValueError as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionDenied) else 404, detail=safe_detail_for_status(e, 403)) from e


@router.get("/{village_id}/projects/{project_id}/investors", response_model=list)
async def get_project_investors(
    village_id: str,
    project_id: str,
    db: Annotated[Any, Depends(_get_db)],
):
    """دریافت لیست سرمایه‌گذاران یک پروژه."""
    service = get_hub_service(db)
    try:
        return await service.get_project_investors(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


# ============================================================================
# 7. Tourism Services
# ============================================================================


@router.get("/{village_id}/tourism", response_model=list)
async def list_tourism_services(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """لیست سرویس‌های گردشگيری روستا."""
    service = get_hub_service(db)
    try:
        services = await service.get_village_tourism_services(village_id)
        return [_serialize_tourism_service(s) for s in services]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/tourism", response_model=dict)
async def create_tourism_service(
    village_id: str,
    payload: TourismServiceCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت سرویس گردشگيری جدید."""
    service = get_hub_service(db)
    try:
        svc = await service.create_tourism_service(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_tourism_service(svc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# ============================================================================
# 8. Events
# ============================================================================


@router.get("/{village_id}/events", response_model=list)
async def list_events(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """لیست رویدادهای فرهنگی و گردشگيری روستا."""
    service = get_hub_service(db)
    try:
        events = await service.get_village_events(village_id)
        return [_serialize_event(e) for e in events]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/events", response_model=dict)
async def create_event(
    village_id: str,
    payload: EventCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ایجاد رویداد جدید برای روستا."""
    service = get_hub_service(db)
    try:
        evt = await service.create_event(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_event(evt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# ============================================================================
# 9. Needs
# ============================================================================


@router.get("/{village_id}/needs", response_model=list)
async def list_needs(
    village_id: str,
    priority: Annotated[str | None, Query(alias="priority")] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """لیست نیازهای شناسایی شدهٔ روستا."""
    service = get_hub_service(db)
    try:
        needs = await service.get_village_needs(village_id, priority)
        return [_serialize_need(n) for n in needs]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/needs", response_model=dict)
async def create_need(
    village_id: str,
    payload: NeedCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت نیاز جدید برای روستا."""
    service = get_hub_service(db)
    try:
        need = await service.create_need(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_need(need)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# ============================================================================
# 10. Brand
# ============================================================================


@router.get("/{village_id}/brand", response_model=dict)
async def get_brand(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت اطلاعات برند روستا."""
    service = get_hub_service(db)
    try:
        brand = await service.get_or_create_brand(village_id)
        return _serialize_brand(brand)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.put("/{village_id}/brand", response_model=dict)
async def update_brand(
    village_id: str,
    payload: BrandUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """بروزرسانی برند روستا."""
    service = get_hub_service(db)
    try:
        brand = await service.get_or_create_brand(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_brand(brand)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


# ============================================================================
# AI Recommendations & Search
# ============================================================================


@router.post("/{village_id}/ai-recommendations", response_model=dict)
async def get_ai_recommendations(
    village_id: str,
    actor: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """تحلیل هوشمند ظرفیت روستا و پیشنهاد فرور."""
    service = get_hub_service(db)
    try:
        return await service.ai_recommendations(village_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/{village_id}/experiences", response_model=list)
async def list_experiences(
    village_id: str,
    experience_type: Annotated[str | None, Query()] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """لیست تجربیات گردشگيری روستا."""
    service = get_hub_service(db)
    try:
        exps = await service.get_village_experiences(village_id, experience_type)
        return [_serialize_experience(e) for e in exps]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.post("/{village_id}/experiences", response_model=dict)
async def create_experience(
    village_id: str,
    payload: ExperienceCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت یک تجربهٔ گردشگيری جدید."""
    service = get_hub_service(db)
    try:
        exp = await service.create_experience(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_experience(exp)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/{village_id}/destination", response_model=dict)
async def get_destination(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت صفحهٔ مقصد گردشگری روستا."""
    service = get_hub_service(db)
    try:
        dest = await service.get_or_create_destination(village_id)
        return _serialize_destination(dest)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.put("/{village_id}/destination", response_model=dict)
async def update_destination(
    village_id: str,
    payload: DestinationUpdate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """بروزرسانی صفحهٔ مقصد گردشگری روستا."""
    service = get_hub_service(db)
    try:
        dest = await service.get_or_create_destination(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_destination(dest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/{village_id}/gaps", response_model=dict)
async def create_development_gap(
    village_id: str,
    payload: VillageDevelopmentGapCreate,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Any, Depends(_get_db)],
):
    """ثبت یک شکاف توسعه برای روستا."""
    service = get_hub_service(db)
    try:
        gap = await service.create_development_gap(
            village_id, payload.model_dump(exclude_unset=True), user.id
        )
        return _serialize_gap(gap)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/{village_id}/gaps", response_model=list)
async def list_gaps(
    village_id: str,
    gap_type: Annotated[str | None, Query()] = None,
    db: Annotated[Any, Depends(_get_db)] = None,
):
    """دریافت شکاف‌های توسعهٔ روستا."""
    service = get_hub_service(db)
    try:
        gaps = await service.get_village_gaps(village_id, gap_type)
        return [_serialize_gap(g) for g in gaps]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/{village_id}/festivals", response_model=list)
async def get_village_festivals(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت جشنواره‌های مرتبط با روستا."""
    service = get_hub_service(db)
    try:
        festivals = await service.get_village_festivals(village_id)
        return [_serialize_festival(f) for f in festivals]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


# ============================================================================
# 18. Dossier (پرونده توسعه روستا)
# ============================================================================


@router.get("/{village_id}/dossier", response_model=dict)
async def get_village_dossier(village_id: str, db: Annotated[Any, Depends(_get_db)]):
    """دریافت پروندهٔ توسعهٔ کامل روستا."""
    service = get_hub_service(db)
    try:
        return await service.get_village_dossier(village_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e
