"""
مدل‌های داده مرکز توسعه روستا (Village Development Hub)
=======================================================

ماژول‌های جدید برای توسعهٔ اقتصادی، فرهنگی و گردشگیری روستا:
1. VillageCapability — ظرفیت‌های اقتصادی/گردشگیری روستا
2. VillageOpportunity — فرصت‌های سرمایه‌گذاری و کارآفرینی
3. VillageProject — پروژه‌های در حال اجرا با پیگیری پیشرفت
4. EntrepreneurProfile — پروفایل مهارت‌ها و علاقه‌های کارآفرینان
5. VillageInvestment — درخواست‌های سرمایه و سرمایه‌گذاری
6. VillageTourismService — سرویس‌های گردشگيری (اقامتگاه، تور، راهنمای گردشگری)
7. VillageEvent — رویدادهای فرهنگی و گردشگيری
8. VillageNeed — نیازهای شناسایی شده روستا
9. VillageBrand — برند روستا (تاریخچه، داستان، ارزش‌ها)
10. VillageOpportunityInterest — ابراز علاقه کارآفرین به فرصت
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database.base import Base

# ============================================================================
# Enums
# ============================================================================


class CapabilityCategory(StrEnum):
    """دسته‌های ظرفیت‌های اقتصادی روستا."""

    AGRICULTURE = "agriculture"
    PROCESSING = "processing"
    HANDICRAFT = "handicraft"
    TOURISM = "tourism"
    CULTURE = "culture"
    LIVESTOCK = "livestock"
    FORESTRY = "forestry"
    ENERGY = "energy"


class OpportunityCategory(StrEnum):
    """دسته‌های فرصت‌های توسعه."""

    PROCESSING = "processing"
    BRANDING = "branding"
    TOURISM = "tourism"
    HANDICRAFT = "handicraft"
    MARKETING = "marketing"
    COOPERATIVE = "cooperative"
    DIGITAL = "digital"
    ENERGY = "energy"
    WATER = "water"
    TRANSPORT = "transport"


class OpportunityMaturity(StrEnum):
    """سطوح بالغیت فرصت توسعه."""

    IDEA = "idea"
    PROTOTYPE = "prototype"
    VALIDATION = "validation"
    GROWTH = "growth"
    SCALE = "scale"


class OpportunityStatus(StrEnum):
    """وضعیت یک فرصت توسعه."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    SCALING = "scaling"
    ARCHIVED = "archived"


class ProjectStatus(StrEnum):
    """وضعیت پروژهٔ توسعه."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class InvestmentStatus(StrEnum):
    """وضعیت درخواست سرمایه‌گذاری."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    FUNDED = "funded"


class TourismServiceType(StrEnum):
    """انواع سرویس‌های گردشگيری."""

    ACCOMMODATION = "accommodation"
    TOUR_GUIDE = "tour_guide"
    ACTIVITY = "activity"
    TRANSPORT = "transport"
    FOOD = "food"


class EventStatus(StrEnum):
    """وضعیت رویداد."""

    DRAFT = "draft"
    PUBLISHED = "published"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NeedPriority(StrEnum):
    """اولویت نیازهای روستا."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(StrEnum):
    """سطح اطمینان داده."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# VillageCapability
# ============================================================================


class VillageCapability(Base):
    """ظرفیت اقتصادی/گردشگيری یا فرهنگی یک روستا.

    مثال: "تولید سیب در منطقهٔ شمالی"، "جاذبهٔ طبیعی آبشار"
    """

    __tablename__ = "village_capabilities"
    __table_args__ = (
        Index("idx_cap_village", "village_id"),
        Index("idx_cap_category", "category"),
        Index("idx_cap_active", "is_active"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    category = Column(String(50), nullable=False)
    subcategory = Column(String(100))
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    capacity_value = Column(Numeric(12, 2), nullable=True)
    unit = Column(String(50))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    confidence = Column(String(20), default="medium")
    source = Column(String(200))

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    opportunities = relationship(
        "VillageOpportunity", back_populates="capability", cascade="all, delete-orphan"
    )


# ============================================================================
# VillageOpportunity
# ============================================================================


class VillageOpportunity(Base):
    """فرصت توسعهٔ یک روستا — یک ایدهٔ کسب‌وکار قابل اجرا.

    مثال: "راه‌اندازی خط بسته‌بندی سیب"، "ایجاد اکوکمپینی برای گردشگيری"
    """

    __tablename__ = "village_opportunities"
    __table_args__ = (
        Index("idx_opp_village", "village_id"),
        Index("idx_opp_category", "category"),
        Index("idx_opp_status", "status"),
        Index("idx_opp_capability", "capability_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    capability_id = Column(
        String(36), ForeignKey("village_capabilities.id"), nullable=True, index=True
    )
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    category = Column(String(100), nullable=False)
    description = Column(Text)
    business_model = Column(Text)
    required_investment = Column(Numeric(18, 2))
    required_skills = Column(JSON, default=list)
    target_markets = Column(JSON, default=list)
    expected_revenue = Column(Numeric(18, 2))
    maturity = Column(String(30), default="idea")
    status = Column(String(20), default="draft")
    created_by = Column(String(36), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    capability = relationship("VillageCapability", back_populates="opportunities")
    projects = relationship(
        "VillageProject", back_populates="opportunity", cascade="all, delete-orphan"
    )
    interests = relationship(
        "VillageOpportunityInterest", back_populates="opportunity", cascade="all, delete-orphan"
    )


# ============================================================================
# VillageProject
# ============================================================================


class VillageProject(Base):
    """پروژهٔ توسعه در حال اجرا در یک روستا.

    یک پروژه معمولاً از یک فرصت ناشی می‌شود ولی نیازی ندارد.
    """

    __tablename__ = "village_projects"
    __table_args__ = (
        Index("idx_proj_village", "village_id"),
        Index("idx_proj_status", "status"),
        Index("idx_proj_opportunity", "opportunity_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    opportunity_id = Column(
        String(36), ForeignKey("village_opportunities.id"), nullable=True, index=True
    )
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    description = Column(Text)
    category = Column(String(100))
    status = Column(String(20), default="planned")
    progress_pct = Column(Integer, default=0)
    investment_needed = Column(Numeric(18, 2))
    investment_secured = Column(Numeric(18, 2), default=Decimal("0.00"))
    investors_count = Column(Integer, default=0)

    start_date = Column(Date)
    expected_completion = Column(Date)
    actual_completion = Column(Date)
    team_size = Column(Integer, default=0)

    created_by = Column(String(36), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    opportunity = relationship("VillageOpportunity", back_populates="projects")
    investments = relationship(
        "VillageInvestment", back_populates="project", cascade="all, delete-orphan"
    )


# ============================================================================
# EntrepreneurProfile
# ============================================================================


class EntrepreneurProfile(Base):
    """پروفایل کارآفرین — مهارت‌ها، علاقه‌ها و ظرفیت.

    ارتباط 1:1 با User — هر کاربر می‌تواند یک پروفایل کارآفرین داشته باشد.
    """

    __tablename__ = "entrepreneur_profiles"
    __table_args__ = (
        Index("idx_entrepreneur_user", "user_id"),
        Index("idx_entrepreneur_village", "village_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    village_id = Column(String(100), nullable=True, index=True)

    skills = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    capacity_description = Column(Text)
    experience_years = Column(Integer)
    is_available = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    interests_in_opportunities = relationship(
        "VillageOpportunityInterest", back_populates="entrepreneur", cascade="all, delete-orphan"
    )


# ============================================================================
# VillageInvestment
# ============================================================================


class VillageInvestment(Base):
    """ثبت سرمایه‌گذاری یا درخواست سرمایه در یک پروژه.

    استفاده برای سرمایه‌گذاری افراد یا تخصیص از صندوق منظر.
    """

    __tablename__ = "village_investments"
    __table_args__ = (
        Index("idx_inv_project", "project_id"),
        Index("idx_inv_investor", "investor_user_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("village_projects.id"), nullable=False, index=True)
    investor_user_id = Column(String(36), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="IRR")
    status = Column(String(20), default="pending")
    notes = Column(Text)
    confirmed_by = Column(String(36), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("VillageProject", back_populates="investments")


# ============================================================================
# VillageTourismService
# ============================================================================


class VillageTourismService(Base):
    """سرویس گردشگيری روستا: اقامتگاه، تور، فعالیت، حمل‌ونقل، غذا.

    یکپارچه با tourism_guides موجود — در صورتی که راهنمای تأیید شده باشد،
    می‌تواند سرویس گردشگيری ثبت کند.
    """

    __tablename__ = "village_tourism_services"
    __table_args__ = (
        Index("idx_tour_svc_village", "village_id"),
        Index("idx_tour_svc_type", "service_type"),
        Index("idx_tour_svc_owner", "owner_user_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    owner_user_id = Column(String(36), nullable=False, index=True)
    service_type = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    description = Column(Text)
    location = Column(String(200))
    coordinates = Column(JSON)
    price_per_unit = Column(Numeric(12, 2), nullable=True)
    capacity = Column(Integer)
    is_organic = Column(Boolean, default=True)
    is_regenerative = Column(Boolean, default=True)
    images = Column(JSON, default=list)
    contact_phone = Column(String(50))
    contact_email = Column(String(200))
    is_verified = Column(Boolean, default=False)
    status = Column(String(20), default="pending")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ============================================================================
# VillageEvent
# ============================================================================


class VillageEvent(Base):
    """رویداد فرهنگی یا گردشگيری یک روستا.

    مثال: بازار محلی، جشنوارهٔ سیب، کارگاه دستی
    """

    __tablename__ = "village_events"
    __table_args__ = (
        Index("idx_event_village", "village_id"),
        Index("idx_event_start", "start_date"),
        Index("idx_event_status", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    title_en = Column(String(200))
    description = Column(Text)
    event_type = Column(String(50))
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    location = Column(String(200))
    coordinates = Column(JSON)
    max_participants = Column(Integer)
    registration_fee = Column(Numeric(12, 2), default=Decimal("0.00"))
    status = Column(String(20), default="draft")
    images = Column(JSON, default=list)
    created_by = Column(String(36), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    registrations = relationship(
        "VillageEventRegistration", back_populates="event", cascade="all, delete-orphan"
    )


# ============================================================================
# VillageEventRegistration
# ============================================================================


class VillageEventRegistration(Base):
    """ثبت‌نام شرکت‌کننده در یک رویداد."""

    __tablename__ = "village_event_registrations"
    __table_args__ = (
        Index("idx_event_reg_event", "event_id"),
        Index("idx_event_reg_user", "user_id"),
        Index("idx_event_reg_status", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("village_events.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), default="registered")
    registration_fee = Column(Numeric(12, 2), default=Decimal("0.00"))
    payment_reference = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    event = relationship("VillageEvent", back_populates="registrations")


# ============================================================================
# VillageNeed
# ============================================================================


class VillageNeed(Base):
    """نیازهای توسعهٔ شناسایی شده برای یک روستا.

    این نیازها می‌توانند از تحلیل داده‌ها یا پرسش‌نامه‌های محلی استخراج شوند.
    """

    __tablename__ = "village_needs"
    __table_args__ = (
        Index("idx_need_village", "village_id"),
        Index("idx_need_priority", "priority"),
        Index("idx_need_category", "category"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    category = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default="medium")
    estimated_investment = Column(Numeric(18, 2), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ============================================================================
# VillageBrand
# ============================================================================


class VillageBrand(Base):
    """یکپذار برند روستا — تاریخچه، داستان، ارزش‌ها.

    این جدول به‌صورت اختیاری بر `LandscapeVillage` موجود متصل می‌شود
    و اطلاعات غنی برندسازی را نگهداری می‌کند.
    """

    __tablename__ = "village_brands"
    __table_args__ = (Index("idx_brand_village", "village_id"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, unique=True, index=True)

    story = Column(Text)
    vision = Column(Text)
    values = Column(JSON, default=list)
    heritage = Column(Text)
    certifications = Column(JSON, default=list)
    media_kit_url = Column(String(500))
    brand_guidelines_url = Column(String(500))

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ============================================================================
# VillageOpportunityInterest
# ============================================================================


class VillageOpportunityInterest(Base):
    """علاقه یک کارآفرین به یک فرصت توسعه.

    این جدول رابطهٔ many-to-many بین EntrepreneurProfile و VillageOpportunity
    را با وضعیت ابراز علاقه و یادداشت‌ها نگهداری می‌کند.
    """

    __tablename__ = "village_opportunity_interests"
    __table_args__ = (
        Index("idx_interest_opp", "opportunity_id"),
        Index("idx_interest_entrepreneur", "entrepreneur_id"),
        Index("idx_interest_status", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(
        String(36), ForeignKey("village_opportunities.id"), nullable=False, index=True
    )
    entrepreneur_id = Column(
        String(36), ForeignKey("entrepreneur_profiles.id"), nullable=False, index=True
    )

    status = Column(String(20), default="interested")
    note = Column(Text, nullable=True)
    expressed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    opportunity = relationship("VillageOpportunity", back_populates="interests")
    entrepreneur = relationship("EntrepreneurProfile", back_populates="interests_in_opportunities")


# ============================================================================
# VillageExperience — تجربه‌های گردشگری قابل رزرو
# ============================================================================


class ExperienceType(StrEnum):
    """انواع تجربه‌های گردشگری."""

    ACCOMMODATION = "accommodation"
    WORKSHOP = "workshop"
    TASTING = "tasting"
    TOUR = "tour"
    ACTIVITY = "activity"


class VillageExperience(Base):
    """تجربهٔ گردشگری قابل رزرو در یک روستا.

    مثال: «صبحانه سنتی در خانه روستایی»، «آموزش گلیم‌بافی»، «برداشت زعفران»
    """

    __tablename__ = "village_experiences"
    __table_args__ = (
        Index("idx_exp_village", "village_id"),
        Index("idx_exp_type", "experience_type"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    description = Column(Text)
    experience_type = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    price_range_min = Column(Numeric(12, 2), nullable=True)
    price_range_max = Column(Numeric(12, 2), nullable=True)
    guide_required = Column(Boolean, default=False)
    max_participants = Column(Integer, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ============================================================================
# VillageDestination — صفحهٔ مقصد گردشگری روستا
# ============================================================================


class VillageDestination(Base):
    """صفحهٔ مقصد گردشگری یک روستا — ترکیبی از طبیعت، فرهنگ، و تجربه.

    روستا فقط محل تولید نیست، بلکه **محصول** است.
    """

    __tablename__ = "village_destinations"
    __table_args__ = (Index("idx_dest_village", "village_id"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, unique=True, index=True)

    # طبیعت
    natural_attractions = Column(JSON, default=list)  # کوه، رودخانه، آبشار، جنگل، ...
    # فرهنگ
    cultural_attractions = Column(JSON, default=list)  # موسیقی، غذا، معماری، آیین‌ها
    # تجربه
    experiences = Column(JSON, default=list)  # لیست تجربه‌های قابل رزرو
    # امکانات
    accommodations = Column(JSON, default=list)  # لیست اقامتگاه‌ها
    # برند
    tagline = Column(String(500), nullable=True)  # شعار گردشگری
    hero_image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ============================================================================
# B2BDemand — درخواست‌های خرید B2B از کارخانه‌ها/زنجیره‌های خرید
# ============================================================================


class B2BDemand(Base):
    """درخواست خرید B2B از شرکت‌های بزرگ یا فروشگاه‌های زنجیره‌ای.

    مثال: «ماهانه ۵ تن عسل نیاز دارم» یا «۲۰۰۰ مترمربع گلیم می‌خرم».
    این بازار B2B بزرگتر از فروش مستقیم به مصرف‌کننده است.
    """

    __tablename__ = "b2b_demands"
    __table_args__ = (
        Index("idx_b2b_buyer", "buyer_id"),
        Index("idx_b2b_commodity", "commodity"),
        Index("idx_b2b_status", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    buyer_id = Column(String(36), nullable=False, index=True)  # شناسه شرکت خریدار
    buyer_name = Column(String(200), nullable=True)
    commodity = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    quantity_required = Column(Numeric(18, 2), nullable=False)
    unit = Column(String(50), nullable=False)  # ton/month, sqm, etc.
    frequency = Column(String(30), default="monthly")  # monthly|quarterly|one_time
    target_regions = Column(JSON, default=list)
    min_quality_cert = Column(String(200), nullable=True)
    price_range = Column(JSON, default=list)  # [{min, max, currency}]
    status = Column(String(20), default="open")  # open|matched|closed
    matched_villages = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    closed_at = Column(DateTime(timezone=True), nullable=True)


# ============================================================================
# NomadicCommunity — جامعه عشایری
# ============================================================================


class NomadicCommunity(Base):
    """یک جامعه عشایری با مدل متفاوت از روستاهای ثابت.

    شامل ظرفیت‌های دامداری، لبنیات، صنایع دستی، گیاهان دارویی،
    و تجربهٔ «زندگی عشایری» برای گردشگر.
    """

    __tablename__ = "nomadic_communities"
    __table_args__ = (Index("idx_nomadic_region", "region"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    region = Column(String(200), nullable=True)
    country = Column(String(10), default="IR")

    # ظرفیت‌ها
    capacities = Column(JSON, default=list)  # [{type: "livestock", value: ..., unit: ...}]

    # تجربه گردشگری عشایری
    tourism_experience = Column(Text, nullable=True)
    has_tented_accommodation = Column(Boolean, default=False)

    # اطلاعات تماس
    contact_person = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # وضعیت
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# ============================================================================
# VillageEngagement — ماشین‌بازی ظرفیت ↔ کارآفرین
# ============================================================================


class EngagementRole(StrEnum):
    """نقش افراد در گره‌گیری ظرفیت با کارآفرین."""

    EXECUTOR = "executor"  # من می‌خواهم اجرا کنم
    INVESTOR = "investor"  # سرمایه‌گذار هستم
    SUPPLIER = "supplier"  # تجهیزات مواد اولیه دارم
    TRAINER = "trainer"  # دانش فنی دارم
    MARKETER = "marketer"  # بازار فروش دارم


class VillageEngagement(Base):
    """رابطهٔ many-to-many بین کاربر و فرصت/پروژه با نقش.

    این جدول تبدیل اکو نوژین به «شبکهٔ اتصال ظرفیت روستا به منابع مورد
    نیاز توسعهٔ آن» می‌کند.
    """

    __tablename__ = "village_engagements"
    __table_args__ = (
        Index("idx_eng_user", "user_id"),
        Index("idx_eng_opportunity", "opportunity_id"),
        Index("idx_eng_project", "project_id"),
        Index("idx_eng_role", "role"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    opportunity_id = Column(
        String(36), ForeignKey("village_opportunities.id"), nullable=True, index=True
    )
    project_id = Column(String(36), ForeignKey("village_projects.id"), nullable=True, index=True)
    role = Column(String(30), nullable=False)  # executor|investor|supplier|trainer|marketer
    status = Column(String(20), default="pending")  # pending|accepted|rejected
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    responded_at = Column(DateTime(timezone=True), nullable=True)


# ============================================================================
# VillageDevelopmentGap — شکاف‌های توسعه (خروجی تحلیل AI)
# ============================================================================


class VillageDevelopmentGap(Base):
    """یک شکاف توسعهٔ شناسایی شده توسط هوش مصنوعی.

    مثال: «روستا ظرفیت تولید ۵۰ تن گیاه دارویی دارد اما کارگاه فرآوری ندارد».
    """

    __tablename__ = "village_development_gaps"
    __table_args__ = (
        Index("idx_gap_village", "village_id"),
        Index("idx_gap_type", "gap_type"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)
    gap_type = Column(
        String(50), nullable=False
    )  # cold_storage|packaging|branding|processing|tourism|accommodation
    severity = Column(String(20))  # red|yellow|green
    description = Column(Text, nullable=True)
    proposed_solution = Column(Text, nullable=True)
    suggested_opportunity_id = Column(
        String(36), ForeignKey("village_opportunities.id"), nullable=True
    )
    ai_generated = Column(Boolean, default=True)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# ============================================================================
# VillageFestival — جشنواره‌ها و نمایشگاه‌ها
# ============================================================================


class FestivalScope(StrEnum):
    """مقیاس جشنواره."""

    LOCAL = "local"
    INTER_VILLAGE = "inter_village"
    NATIONAL = "national"


class FestivalMode(StrEnum):
    """حالت برگزاری (دیجیتال/فیزیکی/تمرکب)."""

    DIGITAL = "digital"
    PHYSICAL = "physical"
    BOTH = "both"


class VillageFestival(Base):
    """جشنواره یا نمایشگاه بین‌روستایی یا ملی.

    مثال: «جشنواره ملی عسل روستایی» با شرکت چنارستان، گلستان، کوهستان، ...
    """

    __tablename__ = "village_festivals"
    __table_args__ = (Index("idx_fest_scope", "scope"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    scope = Column(String(30), default="local")  # local|inter_village|national
    mode = Column(String(20), default="both")  # digital|physical|both

    # زمان‌بندی
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # شرکت‌کننده‌ها (لیست village_id)
    participating_villages = Column(JSON, default=list)

    # تنظیمات
    registration_link = Column(String(500), nullable=True)
    featured_products = Column(JSON, default=list)

    status = Column(String(20), default="planning")  # planning|active|completed|cancelled
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


__all__ = [
    "B2BDemand",
    # Enums
    "CapabilityCategory",
    "ConfidenceLevel",
    "EngagementRole",
    "EntrepreneurProfile",
    "EventStatus",
    "ExperienceType",
    "FestivalMode",
    "FestivalScope",
    "InvestmentStatus",
    "NeedPriority",
    "NomadicCommunity",
    "OpportunityCategory",
    "OpportunityMaturity",
    "OpportunityStatus",
    "ProjectStatus",
    "TourismServiceType",
    "VillageBrand",
    # Models
    "VillageCapability",
    "VillageDestination",
    "VillageDevelopmentGap",
    "VillageEngagement",
    "VillageEvent",
    "VillageEventRegistration",
    "VillageExperience",
    "VillageFestival",
    "VillageInvestment",
    "VillageNeed",
    "VillageOpportunity",
    "VillageOpportunityInterest",
    "VillageProject",
    "VillageTourismService",
]
