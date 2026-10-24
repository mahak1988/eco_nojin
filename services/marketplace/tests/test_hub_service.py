"""Tests for Village Development Hub service layer.

All run on an in-memory SQLite database with the shared Base metadata.
Tests are async to match the async service layer.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.landscape.models import LandscapeGovernanceMember, LandscapeVillage
from services.marketplace.hub_service import (
    PermissionDenied,
    VillageDevelopmentHubService,
)


@pytest.fixture
async def db_session():
    """Provide an async in-memory SQLite session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def service(db_session):
    return VillageDevelopmentHubService(db_session)


@pytest.fixture
async def village_created(db_session):
    """Create a test village that services can reference."""
    v = LandscapeVillage(
        village_id="v-1",
        name="روستای تست",
        region="تهران",
        country="IR",
        is_active=True,
        active_modules=["marketplace", "tourism"],
    )
    db_session.add(v)
    await db_session.commit()


@pytest.fixture
async def service_with_village(db_session, village_created):
    return VillageDevelopmentHubService(db_session)


@pytest.fixture
async def governance_member(db_session, village_created):
    """Seed an active governance writer for ``v-1`` / ``user-1``."""
    member = LandscapeGovernanceMember(
        village_id="v-1",
        user_id="user-1",
        role="landscape_manager",
        is_active=True,
    )
    db_session.add(member)
    await db_session.commit()


# --- Capability Tests ---


@pytest.mark.asyncio
async def test_create_capability(service_with_village, governance_member, db_session):
    service = service_with_village
    cap = await service.create_capability(
        "v-1",
        {"category": "agriculture", "name": "سیب", "name_en": "Apple"},
        "user-1",
    )
    assert cap.category == "agriculture"
    assert cap.name == "سیب"
    assert cap.is_active is True

    fetched = await service.get_village_capabilities("v-1")
    assert len(fetched) == 1
    assert fetched[0].name == "سیب"


@pytest.mark.asyncio
async def test_create_capability_auto_commits(service_with_village, governance_member):
    service = service_with_village
    cap = await service.create_capability("v-1", {"category": "tourism", "name": "آبشار"}, "user-1")
    assert cap.id is not None


@pytest.mark.asyncio
async def test_capability_category_filter(service_with_village, governance_member):
    service = service_with_village
    await service.create_capability("v-1", {"category": "agriculture", "name": "سیب"}, "user-1")
    await service.create_capability(
        "v-1", {"category": "tourism", "name": "راهنمای گردشگری"}, "user-1"
    )

    ag_caps = await service.get_village_capabilities("v-1", category="agriculture")
    assert len(ag_caps) == 1
    assert ag_caps[0].name == "سیب"


@pytest.mark.asyncio
async def test_get_capabilities_invalid_village(service):
    with pytest.raises(ValueError, match="یافت نشد"):
        await service.get_village_capabilities("unknown-village")


# --- Opportunity Tests ---


@pytest.mark.asyncio
async def test_create_opportunity(service_with_village, governance_member):
    service = service_with_village
    opp = await service.create_opportunity(
        "v-1",
        {
            "name": "بسته‌بندی سیب",
            "name_en": "Apple Packaging",
            "category": "processing",
            "description": "راه‌اندازی خط بسته‌بندی با برند روستا",
            "required_investment": Decimal("5000000"),
            "expected_revenue": Decimal("15000000"),
            "maturity": "idea",
            "required_skills": ["packaging", "food_safety"],
            "target_markets": ["tehran", "isfahan"],
        },
        "user-1",
    )
    assert opp.name == "بسته‌بندی سیب"
    assert opp.status == "draft"
    assert opp.maturity == "idea"


@pytest.mark.asyncio
async def test_opportunity_invalid_village(service):
    with pytest.raises(ValueError, match="یافت نشد"):
        await service.create_opportunity("unknown-village", {"name": "x"}, "user-1")


# --- Project Tests ---


@pytest.mark.asyncio
async def test_create_and_update_project_progress(service_with_village, governance_member):
    service = service_with_village

    proj = await service.create_project(
        "v-1",
        {
            "name": "پروژه بسته‌بندی",
            "description": "راه‌اندازی خط بسته‌بندی سیب",
            "status": "in_progress",
            "investment_needed": Decimal("5000000"),
        },
        "user-1",
    )
    assert proj.progress_pct == 0
    assert proj.status == "in_progress"

    class FakeUser:
        id = "user-1"
        role = "landscape_manager"

    updated = await service.update_project_progress(proj.id, 50, FakeUser())
    assert updated.progress_pct == 50
    assert updated.status == "in_progress"

    completed = await service.update_project_progress(proj.id, 100, FakeUser())
    assert completed.progress_pct == 100
    assert completed.status == "completed"
    assert completed.actual_completion is not None


@pytest.mark.asyncio
async def test_project_progress_out_of_bounds(service_with_village, governance_member):
    service = service_with_village

    proj = await service.create_project("v-1", {"name": "test"}, "user-1")

    class FakeUser:
        id = "user-1"
        role = "admin"

    with pytest.raises(ValueError, match="پیشرفت"):
        await service.update_project_progress(proj.id, 150, FakeUser())
    with pytest.raises(ValueError, match="پیشرفت"):
        await service.update_project_progress(proj.id, -10, FakeUser())


# --- Entrepreneur Tests ---


@pytest.mark.asyncio
async def test_upsert_entrepreneur_profile_create(service_with_village):
    service = service_with_village
    profile = await service.upsert_entrepreneur_profile(
        "user-1",
        {"skills": ["packaging", "food_safety"], "experience_years": 3, "village_id": "v-1"},
    )
    assert profile.user_id == "user-1"
    assert profile.skills == ["packaging", "food_safety"]
    assert profile.is_available is True


@pytest.mark.asyncio
async def test_upsert_entrepreneur_profile_update_existing(service_with_village):
    service = service_with_village
    await service.upsert_entrepreneur_profile(
        "user-1", {"skills": ["packaging"], "village_id": "v-1"}
    )
    profile = await service.upsert_entrepreneur_profile(
        "user-1", {"skills": ["packaging", "logistics"], "experience_years": 5}
    )
    assert profile.experience_years == 5
    assert len(profile.skills) == 2


@pytest.mark.asyncio
async def test_get_entrepreneur_profile_not_found(service_with_village):
    service = service_with_village
    result = await service.get_entrepreneur_profile("unknown-user")
    assert result is None


# --- Investment Tests ---


@pytest.mark.asyncio
async def test_create_investment(service_with_village, governance_member):
    service = service_with_village
    proj = await service.create_project("v-1", {"name": "test"}, "user-1")
    inv = await service.create_investment(proj.id, Decimal("1000000"), "investor-1")
    assert inv.amount == Decimal("1000000")
    assert inv.status == "pending"
    assert inv.currency == "IRR"


@pytest.mark.asyncio
async def test_create_investment_negative_amount(service_with_village, governance_member):
    service = service_with_village
    proj = await service.create_project("v-1", {"name": "test"}, "user-1")
    with pytest.raises(ValueError, match="مبلغ"):
        await service.create_investment(proj.id, Decimal("-500"), "investor-1")


@pytest.mark.asyncio
async def test_confirm_investment(service_with_village, governance_member):
    service = service_with_village
    proj = await service.create_project("v-1", {"name": "test"}, "user-1")
    inv = await service.create_investment(proj.id, Decimal("1000000"), "investor-1")
    confirmed = await service.confirm_investment(inv.id, "admin-1", "confirmed")
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_by == "admin-1"
    assert confirmed.confirmed_at is not None


@pytest.mark.asyncio
async def test_confirm_investment_not_found(service_with_village):
    service = service_with_village
    with pytest.raises(ValueError, match="یافت نشد"):
        await service.confirm_investment("nonexistent", "admin-1")


# --- Tourism Service Tests ---


@pytest.mark.asyncio
async def test_create_tourism_service(service_with_village, governance_member):
    service = service_with_village
    svc = await service.create_tourism_service(
        "v-1",
        {
            "service_type": "accommodation",
            "name": "خانه‌ مدرن",
            "name_en": "Modern House",
            "description": "اقامتگاه بوم‌گردی با منظره",
            "price_per_unit": Decimal("500000"),
            "capacity": 4,
            "contact_phone": "09120000000",
        },
        "user-1",
    )
    assert svc.service_type == "accommodation"
    assert svc.price_per_unit == Decimal("500000")
    assert svc.capacity == 4
    assert svc.is_organic is True


@pytest.mark.asyncio
async def test_get_tourism_services(service_with_village, governance_member):
    service = service_with_village
    await service.create_tourism_service(
        "v-1",
        {
            "service_type": "accommodation",
            "name": "اقامتگاه A",
            "price_per_unit": Decimal("300000"),
        },
        "user-1",
    )
    await service.create_tourism_service(
        "v-1",
        {"service_type": "tour_guide", "name": "راهنمای B", "price_per_unit": Decimal("200000")},
        "user-1",
    )
    services = await service.get_village_tourism_services("v-1")
    assert len(services) == 2


# --- Event Tests ---


@pytest.mark.asyncio
async def test_create_event_and_register(service_with_village, governance_member):
    service = service_with_village
    event = await service.create_event(
        "v-1",
        {
            "title": "جشنواره سیب",
            "title_en": "Apple Festival",
            "event_type": "festival",
            "start_date": date(2026, 10, 1),
            "end_date": date(2026, 10, 3),
            "location": "میدان روستا",
            "max_participants": 200,
            "registration_fee": Decimal("0"),
        },
        "user-1",
    )
    assert event.title == "جشنواره سیب"
    assert event.status == "draft"

    reg = await service.register_event(event.id, "user-2")
    assert reg.status == "registered"


@pytest.mark.asyncio
async def test_register_nonexistent_event(service_with_village):
    service = service_with_village
    with pytest.raises(ValueError, match="یافت نشد"):
        await service.register_event("nonexistent", "user-1")


@pytest.mark.asyncio
async def test_get_events_sorted(service_with_village, governance_member):
    service = service_with_village
    await service.create_event(
        "v-1", {"title": "رویداد A", "start_date": date(2026, 10, 5)}, "user-1"
    )
    await service.create_event(
        "v-1", {"title": "رویداد B", "start_date": date(2026, 10, 1)}, "user-1"
    )
    events = await service.get_village_events("v-1")
    assert events[0].title == "رویداد B"


# --- Need Tests ---


@pytest.mark.asyncio
async def test_create_and_resolve_need(service_with_village, governance_member):
    service = service_with_village
    need = await service.create_need(
        "v-1",
        {
            "category": "infrastructure",
            "title": "ساخت جاده",
            "description": "جاده دسترسی به روستا نیاز به تعمیر است",
            "priority": "high",
            "estimated_investment": Decimal("10000000"),
        },
        "user-1",
    )
    assert need.priority == "high"
    assert need.is_resolved is False

    resolved = await service.resolve_need(need.id, "council-member-1")
    assert resolved.is_resolved is True
    assert resolved.resolved_by == "council-member-1"


@pytest.mark.asyncio
async def test_list_needs_filtered_by_priority(service_with_village, governance_member):
    service = service_with_village
    await service.create_need(
        "v-1", {"category": "x", "title": "a", "priority": "low"}, "user-1"
    )
    await service.create_need(
        "v-1", {"category": "x", "title": "b", "priority": "critical"}, "user-1"
    )
    await service.create_need(
        "v-1", {"category": "x", "title": "c", "priority": "high"}, "user-1"
    )

    critical = await service.get_village_needs("v-1", priority="critical")
    assert len(critical) == 1
    assert critical[0].title == "b"


@pytest.mark.asyncio
async def test_create_need_invalid_village(service):
    with pytest.raises(ValueError, match="یافت نشد"):
        await service.create_need(
            "unknown-village", {"category": "x", "title": "y", "priority": "low"}, "user-1"
        )


# --- Brand Tests ---


@pytest.mark.asyncio
async def test_get_or_create_brand_new(service_with_village, governance_member):
    service = service_with_village
    brand = await service.get_or_create_brand(
        "v-1",
        {"story": "روستایی تاریخی", "vision": "پایداری", "values": ["eco", "community"]},
        user_id="user-1",
    )
    assert brand.story == "روستایی تاریخی"
    assert brand.values == ["eco", "community"]


@pytest.mark.asyncio
async def test_get_or_create_brand_existing(service_with_village, governance_member, db_session):
    service = service_with_village
    await service.get_or_create_brand("v-1", {"story": "اولیه"}, user_id="user-1")
    brand = await service.get_or_create_brand(
        "v-1", {"story": "به‌روز شده", "vision": "جدید"}, user_id="user-1"
    )
    assert brand.story == "به‌روز شده"
    assert brand.vision == "جدید"

    from services.marketplace.models.village_hub import VillageBrand

    result = await db_session.execute(select(VillageBrand).where(VillageBrand.village_id == "v-1"))
    brands = result.scalars().all()
    assert len(brands) == 1


# --- AI Recommendations Tests ---


@pytest.mark.asyncio
async def test_ai_recommendations_empty_village(service_with_village):
    service = service_with_village
    result = await service.ai_recommendations("v-1")
    assert result["village_id"] == "v-1"
    assert result["confidence_score"] == 0.0
    assert len(result["recommended_opportunities"]) == 0


@pytest.mark.asyncio
async def test_ai_recommendations_with_capabilities(service_with_village, governance_member):
    service = service_with_village
    await service.create_capability("v-1", {"category": "agriculture", "name": "سیب"}, "user-1")
    await service.create_capability("v-1", {"category": "agriculture", "name": "هلو"}, "user-1")
    await service.create_capability("v-1", {"category": "tourism", "name": "کمپ"}, "user-1")

    result = await service.ai_recommendations("v-1")
    assert "agriculture" in result["top_capabilities"]
    assert result["confidence_score"] > 0.0


# --- Governance Permission Tests ---


@pytest.mark.asyncio
async def test_permission_check_no_governance_member(service_with_village):
    service = service_with_village

    class FakeUser:
        id = "user-1"
        role = "farmer"

    has_access = await service._check_governance_permission("v-1", FakeUser(), write_access=True)
    assert has_access is False


@pytest.mark.asyncio
async def test_permission_check_with_governance_member(service_with_village, db_session):
    service = service_with_village
    member = LandscapeGovernanceMember(
        village_id="v-1",
        user_id="user-1",
        role="council_member",
        is_active=True,
    )
    db_session.add(member)
    await db_session.commit()

    class FakeUser:
        id = "user-1"
        role = "farmer"

    has_access = await service._check_governance_permission("v-1", FakeUser(), write_access=True)
    assert has_access is True

    class FakeUser2:
        id = "user-2"
        role = "farmer"

    has_access = await service._check_governance_permission("v-1", FakeUser2(), write_access=True)
    assert has_access is False


@pytest.mark.asyncio
async def test_permission_check_read_only_role(service_with_village, db_session):
    service = service_with_village
    member = LandscapeGovernanceMember(
        village_id="v-1",
        user_id="user-1",
        role="knowledge_rep",
        is_active=True,
    )
    db_session.add(member)
    await db_session.commit()

    class FakeUser:
        id = "user-1"
        role = "farmer"

    has_write = await service._check_governance_permission("v-1", FakeUser(), write_access=True)
    assert has_write is False


# --- Interest Tests ---


@pytest.mark.asyncio
async def test_express_interest_creates_profile(service_with_village, governance_member):
    service = service_with_village
    opp = await service.create_opportunity(
        "v-1", {"name": "test opp", "category": "processing"}, "user-1"
    )
    interest = await service.express_interest(opp.id, "user-2", note="علاقه‌دارم")
    assert interest.status == "interested"
    assert interest.note == "علاقه‌دارم"


@pytest.mark.asyncio
async def test_express_interest_already_exists(service_with_village, governance_member):
    service = service_with_village
    opp = await service.create_opportunity(
        "v-1", {"name": "test opp", "category": "processing"}, "user-1"
    )
    await service.express_interest(opp.id, "user-2", note="نقدم")
    interest2 = await service.express_interest(opp.id, "user-2", note="به‌روزرسانی")
    assert interest2.note == "به‌روزرسانی"


# --- Investment Tests ---


@pytest.mark.asyncio
async def test_get_my_investments(service_with_village, governance_member):
    service = service_with_village
    proj = await service.create_project("v-1", {"name": "test"}, "user-1")
    await service.create_investment(proj.id, Decimal("500000"), "investor-1")
    await service.create_investment(proj.id, Decimal("300000"), "investor-1")

    investments = await service.get_my_investments("investor-1")
    assert len(investments) == 2


@pytest.mark.asyncio
async def test_get_project_investors(service_with_village, governance_member):
    service = service_with_village
    proj = await service.create_project("v-1", {"name": "test"}, "user-1")
    await service.create_investment(proj.id, Decimal("500000"), "investor-1")
    await service.create_investment(proj.id, Decimal("300000"), "investor-2")

    investors = await service.get_project_investors(proj.id)
    assert len(investors) == 2
    assert any(i["user_id"] == "investor-1" for i in investors)


# --- Search Opportunities Test ---


@pytest.mark.asyncio
async def test_search_opportunities_in_service(service_with_village, governance_member):
    """Test the search logic that the router endpoint uses."""
    service = service_with_village
    await service.create_opportunity("v-1", {"name": "فرصت A", "category": "processing"}, "user-1")
    await service.create_opportunity("v-1", {"category": "tourism", "name": "فرصت B"}, "user-1")

    # Verify both opportunities exist
    opps = await service.get_village_opportunities("v-1")
    assert len(opps) == 2


# --- Experience Tests ---


@pytest.mark.asyncio
async def test_create_and_list_experiences(service_with_village, governance_member):
    """Test experience creation and listing."""
    service = service_with_village
    await service.create_experience(
        "v-1",
        {
            "name": "صبحانه سنتی",
            "name_en": "Traditional Breakfast",
            "description": "دسر سنتی با نان و عسل محلی",
            "experience_type": "tasting",
            "duration_minutes": 60,
            "price_range_min": Decimal("300000"),
            "price_range_max": Decimal("500000"),
            "guide_required": False,
            "max_participants": 10,
        },
        "user-1",
    )
    exps = await service.get_village_experiences("v-1")
    assert len(exps) == 1
    assert exps[0].name == "صبحانه سنتی"
    assert exps[0].experience_type == "tasting"


@pytest.mark.asyncio
async def test_filter_experiences_by_type(service_with_village, governance_member):
    """Test filtering experiences by type."""
    service = service_with_village
    await service.create_experience("v-1", {"name": "A", "experience_type": "tasting"}, "user-1")
    await service.create_experience("v-1", {"name": "B", "experience_type": "workshop"}, "user-1")
    tasting = await service.get_village_experiences("v-1", experience_type="tasting")
    assert len(tasting) == 1
    assert tasting[0].name == "A"


# --- Destination Tests ---


@pytest.mark.asyncio
async def test_get_or_create_destination(service_with_village, governance_member):
    """Test destination creation."""
    service = service_with_village
    dest = await service.get_or_create_destination(
        "v-1",
        {
            "natural_attractions": ["کوه", "آبشار"],
            "cultural_attractions": ["موسیقی محلی", "غذاهای سنتی"],
            "tagline": "روستایی زیبا",
        },
        user_id="user-1",
    )
    assert dest.village_id == "v-1"
    assert "کوه" in dest.natural_attractions
    assert "موسیقی محلی" in dest.cultural_attractions


@pytest.mark.asyncio
async def test_update_existing_destination(service_with_village, governance_member):
    """Test updating an existing destination."""
    service = service_with_village
    await service.get_or_create_destination("v-1", {"tagline": "اولین"}, user_id="user-1")
    dest = await service.get_or_create_destination(
        "v-1",
        {"tagline": "به‌روزرسانی شده", "natural_attractions": ["جنگل"]},
        user_id="user-1",
    )
    assert dest.tagline == "به‌روزرسانی شده"
    assert dest.natural_attractions == ["جنگل"]


# --- B2B Demand Tests ---


@pytest.mark.asyncio
async def test_create_b2b_demand(service_with_village):
    """Test B2B demand creation."""
    service = service_with_village
    demand = await service.create_b2b_demand(
        {
            "buyer_name": "شرکت عسل‌ساز",
            "commodity": "عسل",
            "category": "agriculture",
            "quantity_required": Decimal("5000"),
            "unit": "ton/month",
            "frequency": "monthly",
            "target_regions": ["تهران", "اصفهان"],
        },
        "buyer-1",
    )
    assert demand.commodity == "عسل"
    assert demand.quantity_required == Decimal("5000")
    assert demand.status == "open"


@pytest.mark.asyncio
async def test_match_b2b_demands(service_with_village, governance_member):
    """Test B2B demand matching with village capabilities."""
    service = service_with_village
    # Create capability
    await service.create_capability(
        "v-1",
        {"category": "agriculture", "name": "عسل", "capacity_value": 120, "unit": "ton/year"},
        "user-1",
    )
    # Create B2B demand
    await service.create_b2b_demand(
        {
            "commodity": "عسل",
            "category": "agriculture",
            "quantity_required": Decimal("5000"),
            "unit": "ton/month",
        },
        "buyer-1",
    )
    matches = await service.match_b2b_demands("v-1")
    assert len(matches) == 1
    assert matches[0]["capability_name"] == "عسل"


# --- Engagement Tests ---


@pytest.mark.asyncio
async def test_create_engagement(service_with_village, governance_member):
    """Test engagement creation."""
    service = service_with_village
    opp = await service.create_opportunity(
        "v-1",
        {"name": "test", "category": "processing"},
        "user-1",
    )
    eng = await service.create_engagement(
        {"opportunity_id": opp.id, "role": "executor", "note": "علاقه‌دارم شرکت کنم"},
        "user-2",
    )
    assert eng.role == "executor"
    assert eng.status == "pending"


@pytest.mark.asyncio
async def test_get_opportunity_team(service_with_village, governance_member, db_session):
    """Test getting accepted team members for an opportunity."""
    service = service_with_village
    opp = await service.create_opportunity(
        "v-1", {"name": "test", "category": "processing"}, "user-1"
    )
    eng1 = await service.create_engagement({"opportunity_id": opp.id, "role": "executor"}, "user-2")
    await service.create_engagement({"opportunity_id": opp.id, "role": "investor"}, "user-3")
    # Accept one
    eng1.status = "accepted"
    await db_session.commit()

    team = await service.get_opportunity_team(opp.id)
    assert len(team) == 1
    assert team[0].user_id == "user-2"


# --- Development Gap Tests ---


@pytest.mark.asyncio
async def test_create_and_list_gaps(service_with_village, governance_member):
    """Test development gap creation and listing."""
    service = service_with_village
    gap = await service.create_development_gap(
        "v-1",
        {
            "gap_type": "cold_storage",
            "severity": "red",
            "description": "نیاز به سردخانه",
            "proposed_solution": "ساخت سردخانه مشترک",
            "ai_generated": True,
            "confidence_score": 0.85,
        },
        "user-1",
    )
    assert gap.gap_type == "cold_storage"
    assert gap.severity == "red"

    gaps = await service.get_village_gaps("v-1")
    assert len(gaps) == 1
    assert gaps[0].gap_type == "cold_storage"


# --- Festival Tests ---


@pytest.mark.asyncio
async def test_get_village_festivals_empty(service_with_village):
    """Test that a village with no festivals returns empty list."""
    service = service_with_village
    festivals = await service.get_village_festivals("v-1")
    assert len(festivals) == 0


@pytest.mark.asyncio
async def test_create_festival(service_with_village, governance_member):
    """Test festival creation."""
    service = service_with_village
    fest = await service.create_festival(
        {
            "name": "جشنواره ملی عسل",
            "name_en": "National Honey Festival",
            "description": "جشنواره بین‌روستایی عسل",
            "scope": "national",
            "mode": "both",
            "participating_villages": ["v-1", "v-2"],
            "registration_link": "https://example.com/register",
        },
        "user-1",
    )
    assert fest.name == "جشنواره ملی عسل"
    assert fest.scope == "national"
    assert "v-1" in fest.participating_villages

    # Now the village should see this festival
    festivals = await service.get_village_festivals("v-1")
    assert len(festivals) == 1


# --- Nomadic Community Tests ---


@pytest.mark.asyncio
async def test_get_nomadic_communities_empty(service_with_village):
    """Test that empty list is returned when no communities exist."""
    service = service_with_village
    communities = await service.get_nomadic_communities()
    assert len(communities) == 0


@pytest.mark.asyncio
async def test_create_nomadic_community(service_with_village, governance_member):
    """Test nomadic community creation."""
    service = service_with_village
    community = await service.create_nomadic_community(
        {
            "name": "عشایر گلستان",
            "name_en": "Golestan Nomads",
            "region": "گلستان",
            "country": "IR",
            "capacities": [{"type": "livestock", "value": 500, "unit": "sheep"}],
            "tourism_experience": "تجربه شب‌نشینی عشایری",
            "has_tented_accommodation": True,
            "contact_person": "علی احمدی",
            "contact_phone": "09120000000",
        },
        "user-1",
    )
    assert community.name == "عشایر گلستان"
    assert community.has_tented_accommodation is True
    assert community.is_approved is False  # Default

    # Should be visible only if approved (approved_only=True)
    found = await service.get_nomadic_communities()
    assert len(found) == 0  # Not approved

    # Should be visible if approved_only=False
    found = await service.get_nomadic_communities(approved_only=False)
    assert len(found) == 1


# --- Nomadic Approval & Lifecycle Tests (P1-10) ---


@pytest.mark.asyncio
async def test_create_nomadic_community_records_owner_and_tribal_fields(service):
    created = await service.create_nomadic_community(
        {
            "name": "عشایر لر",
            "village_id": "v-42",
            "pasture_area_ha": 1500,
            "migration_route": {"season": "summer", "origin": "شهرستان", "destination": "ییلاق"},
            "herd_size_estimate": 3000,
        },
        "creator-1",
        is_admin=True,
    )
    assert created.owner_user_id == "creator-1"
    assert created.created_by == "creator-1"
    assert created.village_id == "v-42"
    assert float(created.pasture_area_ha) == 1500
    assert created.herd_size_estimate == 3000
    assert created.migration_route["season"] == "summer"


@pytest.mark.asyncio
async def test_get_nomadic_community(service):
    created = await service.create_nomadic_community({"name": "عشایر"}, "creator-1", is_admin=True)
    fetched = await service.get_nomadic_community(created.id)
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_get_nomadic_community_not_found(service):
    with pytest.raises(ValueError, match="یافت نشد"):
        await service.get_nomadic_community("missing-id")


@pytest.mark.asyncio
async def test_approve_nomadic_community_makes_it_visible_in_approved_listing(
    service_with_village,
    governance_member,
):
    service = service_with_village
    created = await service.create_nomadic_community({"name": "عشایر شاهسون"}, "user-1")
    assert created.is_approved is False
    assert await service.get_nomadic_communities(approved_only=True) == []

    approved = await service.approve_nomadic_community(created.id, "user-1")
    assert approved.is_approved is True
    assert approved.approved_by == "user-1"
    assert approved.approved_at is not None

    visible = await service.get_nomadic_communities(approved_only=True)
    assert [c.id for c in visible] == [created.id]


@pytest.mark.asyncio
async def test_approve_nomadic_community_rejects_unauthorized(service):
    created = await service.create_nomadic_community(
        {"name": "عشایر ناشناس"}, "owner-1", is_admin=True
    )
    with pytest.raises(PermissionDenied):
        await service.approve_nomadic_community(created.id, "outsider")
    still = await service.get_nomadic_community(created.id)
    assert still.is_approved is False


@pytest.mark.asyncio
async def test_approve_nomadic_community_allows_platform_admin(service):
    created = await service.create_nomadic_community({"name": "عشایر"}, "owner-1", is_admin=True)
    approved = await service.approve_nomadic_community(created.id, "admin-actor", is_admin=True)
    assert approved.is_approved is True


@pytest.mark.asyncio
async def test_update_nomadic_community(service_with_village, governance_member):
    service = service_with_village
    created = await service.create_nomadic_community({"name": "عشایر"}, "user-1")
    updated = await service.update_nomadic_community(
        created.id, {"region": "فارس", "herd_size_estimate": 800}, "user-1"
    )
    assert updated.region == "فارس"
    assert updated.herd_size_estimate == 800


@pytest.mark.asyncio
async def test_update_nomadic_community_owner_can_update_own_record(service):
    created = await service.create_nomadic_community(
        {"name": "عشایر باشکیر"}, "owner-9", is_admin=True
    )
    updated = await service.update_nomadic_community(
        created.id, {"herd_size_estimate": 1200}, "owner-9"
    )
    assert updated.herd_size_estimate == 1200


@pytest.mark.asyncio
async def test_update_nomadic_community_non_owner_cannot_update(service):
    created = await service.create_nomadic_community(
        {"name": "عشایر قشقایی"}, "owner-1", is_admin=True
    )
    with pytest.raises(PermissionDenied):
        await service.update_nomadic_community(created.id, {"herd_size_estimate": 5}, "outsider")


@pytest.mark.asyncio
async def test_delete_nomadic_community(service_with_village, governance_member):
    service = service_with_village
    created = await service.create_nomadic_community({"name": "عشایر"}, "user-1")
    await service.delete_nomadic_community(created.id, "user-1")
    listed = await service.get_nomadic_communities(approved_only=False)
    assert all(c.id != created.id for c in listed)
    with pytest.raises(ValueError):
        await service.get_nomadic_community(created.id)


@pytest.mark.asyncio
async def test_delete_nomadic_community_non_owner_cannot_delete(service):
    created = await service.create_nomadic_community({"name": "عشایر"}, "owner-1", is_admin=True)
    with pytest.raises(PermissionDenied):
        await service.delete_nomadic_community(created.id, "outsider")


def test_nomadic_lifecycle_routes_are_registered_and_precede_village_routes():
    """The four new nomadic lifecycle routes are registered as literal paths and
    placed before the /{village_id} family, so none is shadowed."""
    from services.api_gateway.routers import village_hub as vh

    prefix = vh.router.prefix
    routes = [r for r in vh.router.routes if hasattr(r, "path") and r.path.startswith(prefix)]

    def _find(method: str, path: str):
        for route in routes:
            if route.path == path and method in getattr(route, "methods", set()):
                return route
        return None

    by_id_path = f"{prefix}/nomadic-communities/{{community_id}}"
    approve_path = f"{prefix}/nomadic-communities/{{community_id}}/approve"

    approve = _find("PATCH", approve_path)
    assert approve is not None and approve.endpoint.__name__ == "approve_nomadic_community"
    get_one = _find("GET", by_id_path)
    assert get_one is not None and get_one.endpoint.__name__ == "get_nomadic_community"
    put_one = _find("PUT", by_id_path)
    assert put_one is not None and put_one.endpoint.__name__ == "update_nomadic_community"
    del_one = _find("DELETE", by_id_path)
    assert del_one is not None and del_one.endpoint.__name__ == "delete_nomadic_community"

    suffixes = [r.path[len(prefix):] for r in routes]
    first_param = min(i for i, s in enumerate(suffixes) if s.startswith("/{"))
    for route in (approve, get_one, put_one, del_one):
        position = routes.index(route)
        assert position < first_param, f"{route.path} registered after a /{{village_id}} route"


# --- Dossier Tests ---


@pytest.mark.asyncio
async def test_get_village_dossier(service_with_village, governance_member):
    """Test village dossier retrieval."""
    service = service_with_village
    # Create some data
    await service.create_capability("v-1", {"category": "agriculture", "name": "سیب"}, "user-1")
    await service.create_opportunity(
        "v-1", {"name": "فرآوری سیب", "category": "processing"}, "user-1"
    )
    await service.create_project("v-1", {"name": "پروژه سیب", "status": "in_progress"}, "user-1")
    await service.create_need(
        "v-1",
        {"category": "infrastructure", "title": "سردخانه", "priority": "critical"},
        "user-1",
    )

    dossier = await service.get_village_dossier("v-1")
    assert dossier["village_id"] == "v-1"
    assert len(dossier["agriculture"]) == 1
    assert len(dossier["opportunities"]) == 1
    assert len(dossier["projects"]) == 1
    assert len(dossier["needs"]) == 1
    assert dossier["entrepreneurs_count"] == 0
    # The village row must be read through the SAME session the fixture
    # seeded (S17 D-26/T-04): before the fix the service opened a second data
    # path through the global hub, so these came back None/0 here while the
    # combined engine+services run failed outright.
    assert dossier["name"] == "روستای تست"
    assert dossier["population"] == 0


# --- Governance Permission Tests (additional) ---


@pytest.mark.asyncio
async def test_permission_check_write_role(service_with_village, db_session):
    """Test that council_member can write but knowledge_rep cannot."""
    service = service_with_village
    # Add council_member
    member_council = LandscapeGovernanceMember(
        village_id="v-1",
        user_id="user-council",
        role="council_member",
        is_active=True,
    )
    member_knowledge = LandscapeGovernanceMember(
        village_id="v-1",
        user_id="user-knowledge",
        role="knowledge_rep",
        is_active=True,
    )
    db_session.add_all([member_council, member_knowledge])
    await db_session.commit()

    class FakeCouncilUser:
        id = "user-council"
        role = "farmer"

    class FakeKnowledgeUser:
        id = "user-knowledge"
        role = "farmer"

    # Council member can write
    has_access = await service._check_governance_permission(
        "v-1", FakeCouncilUser(), write_access=True
    )
    assert has_access is True

    # Knowledge rep cannot write
    has_access = await service._check_governance_permission(
        "v-1", FakeKnowledgeUser(), write_access=True
    )
    assert has_access is False


# --- Governance Permission Tests on Create Paths (P1-11) ---


@pytest.mark.asyncio
async def test_create_capability_rejects_non_governance_user(service_with_village):
    """Anyone authenticated (the router only requires require_user) is not enough."""
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_capability(
            "v-1", {"category": "agriculture", "name": "سیب"}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_capability_allows_governance_writer(service_with_village, governance_member):
    """A governance writer of that village may create."""
    service = service_with_village
    cap = await service.create_capability(
        "v-1", {"category": "agriculture", "name": "سیب"}, "user-1"
    )
    assert cap.village_id == "v-1"


@pytest.mark.asyncio
async def test_create_capability_is_admin_param_allows_platform_admin(service_with_village):
    """The previously-ignored is_admin flag now grants the platform-admin override."""
    service = service_with_village
    cap = await service.create_capability(
        "v-1", {"category": "agriculture", "name": "سیب"}, "platform-admin", is_admin=True
    )
    assert cap.village_id == "v-1"


@pytest.mark.asyncio
async def test_create_opportunity_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_opportunity("v-1", {"name": "فرصت A"}, "outsider")


@pytest.mark.asyncio
async def test_create_project_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_project("v-1", {"name": "پروژه"}, "outsider")


@pytest.mark.asyncio
async def test_create_tourism_service_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_tourism_service(
            "v-1", {"name": "اقامتگاه", "service_type": "accommodation"}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_event_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_event(
            "v-1", {"title": "جشنواره", "start_date": date(2026, 10, 1)}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_experience_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_experience(
            "v-1", {"name": "چشیدن عسل", "experience_type": "tasting"}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_need_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_need(
            "v-1", {"category": "x", "title": "a", "priority": "low"}, "outsider"
        )


@pytest.mark.asyncio
async def test_get_or_create_brand_write_rejects_non_governance_user(service_with_village):
    """Only the WRITE leg of brand upsert is gated; the read leg stays open."""
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.get_or_create_brand("v-1", {"story": "محدود"}, "outsider")


@pytest.mark.asyncio
async def test_get_or_create_brand_anonymous_read_still_allowed(service_with_village):
    """No governance member is required to only read the brand."""
    service = service_with_village
    brand = await service.get_or_create_brand("v-1")
    assert brand.village_id == "v-1"


@pytest.mark.asyncio
async def test_get_or_create_destination_write_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.get_or_create_destination("v-1", {"tagline": "محدود"}, "outsider")


@pytest.mark.asyncio
async def test_create_development_gap_rejects_non_governance_user(service_with_village):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_development_gap(
            "v-1", {"gap_type": "cold_storage", "severity": "red"}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_festival_rejects_non_governance_user(service_with_village):
    """A festival tied to a village needs governance on one of its villages."""
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_festival(
            {"name": "جشنواره", "participating_villages": ["v-1"]}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_festival_rejects_full_outsider_when_village_has_no_governance(
    service_with_village,
):
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_festival(
            {"name": "جشنواره", "participating_villages": ["other-village"]}, "outsider"
        )


@pytest.mark.asyncio
async def test_create_nomadic_community_rejects_non_governance_user(service_with_village):
    """A landscape-level write: any governance member (or admin) may author it."""
    service = service_with_village
    with pytest.raises(PermissionDenied):
        await service.create_nomadic_community({"name": "عشایر ناشناس"}, "outsider")


@pytest.mark.asyncio
async def test_read_paths_remain_open_without_governance(service_with_village):
    """README/read endpoints must not regress: no membership railroads reads."""
    service = service_with_village
    caps = await service.get_village_capabilities("v-1")
    assert caps == []
    opps = await service.get_village_opportunities("v-1")
    assert opps == []
    dashboard = await service.get_village_dashboard("v-1")
    assert dashboard["village_id"] == "v-1"


@pytest.mark.asyncio
async def test_lifecycle_write_paths_still_governed(service_with_village):
    """Regression guard: update/delete/progress keep the original mechanism."""
    service = service_with_village
    cap = await service.create_capability(
        "v-1", {"category": "agriculture", "name": "سیب"}, "user-1", is_admin=True
    )

    class FakeOutsider:
        id = "outsider"
        role = "farmer"

    with pytest.raises(PermissionDenied):
        await service.update_capability(cap.id, {"name": "دستکاری"}, FakeOutsider())
    with pytest.raises(PermissionDenied):
        await service.delete_capability(cap.id, FakeOutsider())
