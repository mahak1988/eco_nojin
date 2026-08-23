from datetime import timezone
"""SQLAlchemy ORM models - Complete unified schema."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Removed JSONB import
from sqlalchemy.orm import relationship

from database.config import Base


# ============================================================================
# USER MODEL (Enhanced with KYC fields)
# ============================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Role & access
    role = Column(
        String(50), default="regular"
    )  # farmer, researcher, organization, tourist, regular

    # KYC fields for marketplace/wallet identity verification
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)

    # Profile & preferences
    language = Column(String(10), default="fa")
    avatar_url = Column(String(2000), nullable=True)  # Base64 or URL
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Legal compliance
    accept_tos = Column(Boolean, default=False)
    accept_privacy = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan")
    eco_wallet = relationship(
        "EcoWallet", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    reset_tokens = relationship(
        "PasswordResetToken", back_populates="user", cascade="all, delete-orphan"
    )


# ============================================================================
# PASSWORD RESET TOKEN
# ============================================================================
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")

    @classmethod
    def create_for_user(cls, user_id: int, hours_valid: int = 1):
        return cls(
            user_id=user_id,
            token=secrets.token_urlsafe(48),
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=hours_valid),
            used=False,
        )

    @property
    def is_valid(self) -> bool:
        return not self.used and self.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)


# ============================================================================
# FARM
# ============================================================================
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float)
    area_hectares = Column(Float, nullable=False)
    soil_type = Column(String(100))
    climate_zone = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="farms")
    soil_analyses = relationship(
        "SoilAnalysis", back_populates="farm", cascade="all, delete-orphan"
    )
    satellite_analyses = relationship(
        "SatelliteAnalysis", back_populates="farm", cascade="all, delete-orphan"
    )
    scenario_runs = relationship("ScenarioRun", back_populates="farm", cascade="all, delete-orphan")


# ============================================================================
# SOIL ANALYSIS
# ============================================================================
class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    ph = Column(Float)
    organic_matter = Column(Float)
    nitrogen = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    clay = Column(Float)
    silt = Column(Float)
    sand = Column(Float)

    texture = Column(String(50))
    ph_status = Column(String(50))
    organic_matter_rating = Column(String(50))
    health_score = Column(Float)
    recommendations = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship("Farm", back_populates="soil_analyses")


# ============================================================================
# SATELLITE ANALYSIS
# ============================================================================
class SatelliteAnalysis(Base):
    __tablename__ = "satellite_analyses"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    latitude = Column(Float)
    longitude = Column(Float)
    ndvi = Column(Float)
    evi = Column(Float)
    savi = Column(Float)
    ndwi = Column(Float)
    nbr = Column(Float)
    satellite = Column(String(50))
    data_source = Column(String(20), default="simulated", nullable=False, server_default="simulated")
    scene_id = Column(String(200))
    cloud_cover = Column(Float)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship("Farm", back_populates="satellite_analyses")


# ============================================================================
# SCENARIO RUN
# ============================================================================
class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    baseline_temp = Column(Float)
    baseline_precip = Column(Float)
    scenario = Column(String(20))
    target_year = Column(Integer)
    projected_temp = Column(Float)
    projected_precip = Column(Float)
    temp_change = Column(Float)
    precip_change_percent = Column(Float)
    drought_risk_index = Column(Float)
    impact_assessment = Column(JSON)
    recommendations = Column(JSON)
    run_at = Column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship("Farm", back_populates="scenario_runs")


# ============================================================================
# AI CONVERSATION
# ============================================================================
class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text)
    answer = Column(Text)
    language = Column(String(10))
    sources = Column(JSON)
    confidence = Column(Float)
    asked_at = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================================
# CARBON PROJECT
# ============================================================================
class CarbonProject(Base):
    __tablename__ = "carbon_projects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(100), unique=True)
    name = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    project_type = Column(String(50))
    area_hectares = Column(Float)
    status = Column(String(50), default="registered")
    credits_issued = Column(Float, default=0.0)
    registered_at = Column(DateTime, default=datetime.utcnow)
    verification_status = Column(String(50), default="unverified")
    verification_detail = Column(Text, nullable=True)
    issued_at = Column(DateTime, nullable=True)


# ============================================================================
# ECO WALLET
# ============================================================================
class EcoWallet(Base):
    __tablename__ = "eco_wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_redeemed = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)

    user = relationship("User", back_populates="eco_wallet")
    transactions = relationship(
        "EcoTransaction", back_populates="wallet", cascade="all, delete-orphan"
    )


# ============================================================================
# ECO TRANSACTION
# ============================================================================
class EcoTransaction(Base):
    __tablename__ = "eco_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True)
    wallet_id = Column(Integer, ForeignKey("eco_wallets.id", ondelete="CASCADE"))
    amount = Column(Float)
    transaction_type = Column(String(20))
    category = Column(String(100))
    description = Column(Text)
    balance_after = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    wallet = relationship("EcoWallet", back_populates="transactions")


# ============================================================================
# PRODUCT (Marketplace)
# ============================================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(Text)
    category = Column(String(100), index=True)
    price = Column(Float)
    quantity = Column(Integer, default=0)
    producer_id = Column(Integer, ForeignKey("users.id"))
    is_organic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# RECOMMENDATION CACHE
# ============================================================================
class RecommendationCache(Base):
    __tablename__ = "recommendation_cache"

    id = Column(Integer, primary_key=True, index=True)
    context_hash = Column(String(64), unique=True, index=True)
    context_type = Column(String(50))
    recommendations = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)
    hit_count = Column(Integer, default=0)


class AuditLog(Base):
    """Audit trail for admin actions (W-015)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=False)
    action = Column(String(50), nullable=False, index=True)  # e.g. user.block
    target = Column(String(255), nullable=False)              # e.g. user:42
    detail = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)



class ContentVersion(Base):
    """Snapshot of a content item at each update (Phase 6 version history)."""

    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer, ForeignKey("content_items.id", ondelete="CASCADE"), index=True
    )
    version = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentTranslation(Base):
    """AI (or manual) translations of a content item (Phase 6)."""

    __tablename__ = "content_translations"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer, ForeignKey("content_items.id", ondelete="CASCADE"), index=True
    )
    language = Column(String(10), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    source = Column(String(50), default="ai")  # ai | manual
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    """Global key/value settings (feature flags, announcements)."""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(String(1000), nullable=False, default="")
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ErrorLog(Base):
    """API errors captured by the gateway (admin error view)."""

    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    status = Column(Integer, default=500)
    message = Column(String(1000), nullable=True)
    detail = Column(String(3000), nullable=True)
    acked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ContentItem(Base):
    """Editorial content managed from the admin panel (Phase 5/6)."""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # agriculture/water/soil/carbon/climate
    language = Column(String(10), default="fa")
    status = Column(String(20), default="draft")   # draft | published | archived
    source = Column(String(200), nullable=True)     # provenance of the content
    generated_by_ai = Column(Boolean, default=False)  # Phase 6: AI-produced draft
    rag_synced = Column(Boolean, default=False)       # Phase 6: indexed into RAG store
    published_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)  # Phase 6: scheduled publishing
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MRV OBSERVATION (EM-01: three-level Measurement, Reporting, Verification)
# ============================================================================
class MRVObservation(Base):
    """A single three-level MRV observation (EM-01).

    level 1 = satellite index, level 2 = IoT sensor reading,
    level 3 = citizen field report. The QA/QC outcome is stored on the row so
    the audit trail is complete; dashboard metrics only consume ok/suspect rows.
    """

    __tablename__ = "mrv_observations"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(200), index=True, nullable=False)
    level = Column(Integer, nullable=False, index=True)  # 1 | 2 | 3
    source = Column(String(20), nullable=False, index=True)  # satellite | iot | citizen
    sensor_type = Column(String(50), nullable=True)  # iot sensor or satellite index
    category = Column(String(50), nullable=True)  # citizen report category
    value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    data_source = Column(
        String(20), nullable=False, default="real", server_default="real"
    )  # real | simulated (provenance)
    qa_status = Column(
        String(20), nullable=False, default="ok", server_default="ok"
    )  # ok | suspect | rejected
    qa_message = Column(String(500), nullable=True)
    observed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SimulationRun(Base):
    """Persisted result of one simulation-chain execution (Phase 3)."""

    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(200), nullable=False, index=True)
    scenario = Column(String(20), nullable=False)
    area_ha = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="ok")
    outputs = Column(JSON, nullable=False, default=dict)
    message = Column(Text, default="")
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================================
# NEW MODELS FOR PHASES 1, 2, 3 (LAND, SOIL, CLIMATE, WATER)
# ============================================================================
# These are the models created previously, now integrated into the main database schema.

class LandProfileDB(Base):
    """
    جدول پروفایل زمین
    """
    __tablename__ = 'land_profiles'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    project_id = Column(PG_UUID(as_uuid=True), nullable=False) # احتمالاً به جدول پروژه‌ها ارجاع دارد
    location = Column(String(255), nullable=False) # مختصات نقطه به صورت 'lat,lng' یا JSON
    boundary = Column(Text) # چندضلعی به صورت GeoJSON یا WKT
    area_hectares = Column(Float)
    elevation_min = Column(Float)
    elevation_max = Column(Float)
    elevation_mean = Column(Float)
    slope_mean_degrees = Column(Float)
    aspect_dominant = Column(String(50))
    terrain_type = Column(String(100))
    drainage_pattern = Column(String(100))
    erosion_risk_level = Column(String(50))
    accessibility_score = Column(Float)
    land_capability_class = Column(String(50))
    development_constraints = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # داده‌های پیچیده به صورت JSON
    dem_source = Column(String(100))
    dem_resolution = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TerrainAnalysisDB(Base):
    """
    جدول تحلیل توپوگرافی
    """
    __tablename__ = 'terrain_analyses'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    analysis_type = Column(String(100), nullable=False)
    result_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # نتایج تحلیل
    method = Column(String(100), nullable=False)
    parameters = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # پارامترهای استفاده شده در تحلیل
    created_at = Column(DateTime, default=datetime.utcnow)


class LandCapabilityAssessmentDB(Base):
    """
    جدول ارزیابی قابلیت زمین
    """
    __tablename__ = 'land_capability_assessments'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    capability_class = Column(String(50), nullable=False)
    subclass = Column(String(50))
    limiting_factors = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # عوامل محدود کننده
    suitable_land_uses = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # کاربری‌های مناسب
    assessment_method = Column(String(100))
    confidence_level = Column(Float)
    assessed_by = Column(String(100))
    assessed_at = Column(DateTime, default=datetime.utcnow)


class SoilProfileDB(Base):
    """
    جدول پروفایل خاک
    """
    __tablename__ = 'soil_profiles'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    depth_min = Column(Float, nullable=False)
    depth_max = Column(Float, nullable=False)
    texture_class = Column(String(100))
    ph = Column(Float)
    ec_dsm = Column(Float) # Electrical Conductivity (dS/m)
    cec_mmolc_kg = Column(Float) # Cation Exchange Capacity
    organic_carbon_g_kg = Column(Float)
    nitrogen_g_kg = Column(Float)
    phosphorus_g_kg = Column(Float)
    potassium_g_kg = Column(Float)
    salinity_class = Column(String(50))
    sodicity_class = Column(String(50))
    water_holding_capacity = Column(Float)
    drainage_class = Column(String(50))
    biological_condition = Column(String(100))
    source = Column(String(100))
    collected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClimateDataDB(Base):
    """
    جدول داده‌های اقلیمی
    """
    __tablename__ = 'climate_data'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    data_date = Column(DateTime, nullable=False) # تاریخ داده
    temp_max_c = Column(Float)
    temp_min_c = Column(Float)
    temp_mean_c = Column(Float)
    rainfall_mm = Column(Float)
    humidity_percent = Column(Float)
    wind_speed_m_s = Column(Float)
    radiation_mj_m2 = Column(Float)
    et0_mm = Column(Float) # Reference Evapotranspiration
    drought_index = Column(Float)
    heat_stress_index = Column(Float)
    frost_risk = Column(Float)
    climate_scenario = Column(String(100)) # e.g., SSP1-2.6
    source = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class SurfaceWaterSourceDB(Base):
    """
    جدول منابع آب سطحی
    """
    __tablename__ = 'surface_water_sources'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    source_type = Column(String(100), nullable=False) # e.g., river, lake, spring
    name = Column(String(255)) # نام منبع
    location = Column(String(255)) # مختصات 'lat,lng'
    flow_rate_m3_s = Column(Float) # دبی
    seasonal_variation = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # تغییرات فصلی
    quality_class = Column(String(50)) # کلاس کیفیت
    accessibility = Column(String(50)) # قابلیت دسترسی
    source = Column(String(100)) # منبع داده
    measured_at = Column(DateTime, default=datetime.utcnow)


class GroundwaterDataDB(Base):
    """
    جدول آب زیرزمینی
    """
    __tablename__ = 'groundwater_data'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    well_depth_m = Column(Float) # عمق چاه
    water_table_depth_m = Column(Float) # عمق سطح آب زیرزمینی
    hydraulic_conductivity_m_s = Column(Float) # هدایت هیدرولیکی
    recharge_rate_mm_yr = Column(Float) # نرخ تغذیه (میلی‌متر در سال)
    water_quality_class = Column(String(50)) # کلاس کیفیت
    abstraction_rate_m3_yr = Column(Float) # نرخ برداشت (متر مکعب در سال)
    sustainability_index = Column(Float) # شاخص پایداری
    source = Column(String(100)) # منبع داده
    measured_at = Column(DateTime, default=datetime.utcnow)


class WatershedDataDB(Base):
    """
    جدول آبخیزداری
    """
    __tablename__ = 'watershed_data'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    watershed_boundary = Column(Text) # مرز آبخیز (GeoJSON یا WKT)
    drainage_network = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # شبکه زهکشی
    runoff_coefficient = Column(Float) # ضریب رواناب
    flood_risk_level = Column(String(50)) # سطح خطر سیل
    sediment_yield_t_yr = Column(Float) # رسوب‌دهی (تن در سال)
    erosion_rate_t_ha_yr = Column(Float) # نرخ فرسایش (تن در هکتار در سال)
    recharge_rate_mm_yr = Column(Float) # نرخ تغذیه آبخیز (میلی‌متر در سال)
    groundwater_contribution = Column(Float) # مشارکت در تغذیه آب زیرزمینی
    interventions = Column(JSON) # Changed from JSONB to JSON for SQLite compatibility # مداخلات انجام شده
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# NOJIN BIOFERTILIZER MODELS
# ============================================================================
# Models for strains, formulations, applications, trials, and calibration.

class NojinStrainDB(Base):
    """
    جدول سویه‌های نوجین
    """
    __tablename__ = 'nojin_strains'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    strain_code = Column(String(255), unique=True, nullable=False)
    species_name = Column(String(255), nullable=False)
    strain_type = Column(String(100), nullable=False)
    function = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)
    # isolation_location = Column(Geography('POINT'), nullable=True) # Requires PostGIS
    isolation_location = Column(String(255), nullable=True) # Fallback to 'lat,lng' string
    isolation_date = Column(Date, nullable=True)
    genetic_markers = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    biosafety_level = Column(Integer, default=1)
    efficacy_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    compatibility_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    storage_conditions = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    is_proprietary = Column(Boolean, default=True)
    patent_number = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NojinFormulationDB(Base):
    """
    جدول فرمولاسیون‌های نوجین
    """
    __tablename__ = 'nojin_formulations'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    formulation_code = Column(String(255), unique=True, nullable=False)
    commercial_name = Column(String(255), nullable=False)
    # strain_ids = Column(ARRAY(PG_UUID(as_uuid=True)), ForeignKey('nojin_strains.id'), nullable=False) # ARRAY of UUIDs
    strain_ids = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Store as JSON array of UUID strings for simplicity
    carrier_material = Column(String(255), nullable=True)
    formulation_type = Column(String(100), nullable=False)
    application_method = Column(String(100), nullable=False)
    dosage_kg_ha = Column(Float, nullable=True)
    target_crops = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Store as JSON array
    target_soil_types = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Store as JSON array
    target_climates = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Store as JSON array
    efficacy_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    compatibility_notes = Column(Text, nullable=True)
    storage_conditions = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    shelf_life_days = Column(Integer, nullable=True)
    is_proprietary = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NojinApplicationPlanDB(Base):
    """
    جدول برنامه‌های کاربرد نوجین
    """
    __tablename__ = 'nojin_application_plans'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    formulation_id = Column(PG_UUID(as_uuid=True), ForeignKey('nojin_formulations.id'), nullable=False)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    crop_type = Column(String(100), nullable=False)
    application_date = Column(Date, nullable=False)
    application_method = Column(String(100), nullable=False)
    dosage_kg_ha = Column(Float, nullable=False)
    expected_yield_response = Column(Float, nullable=True)
    expected_soil_improvement = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    risk_assessment = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NojinFieldTrialDB(Base):
    """
    جدول آزمایش‌های میدانی نوجین
    """
    __tablename__ = 'nojin_field_trials'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    application_plan_id = Column(PG_UUID(as_uuid=True), ForeignKey('nojin_application_plans.id'), nullable=True)
    # trial_location = Column(Geography('POINT'), nullable=True) # Requires PostGIS
    trial_location = Column(String(255), nullable=False) # Fallback to 'lat,lng' string
    trial_date = Column(Date, nullable=False)
    crop_type = Column(String(100), nullable=False)
    plot_area_ha = Column(Float, nullable=True)
    treatment_design = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    baseline_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    post_application_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    yield_response = Column(Float, nullable=True)
    soil_improvement = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    observations = Column(Text, nullable=True)
    statistical_analysis = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)


class NojinCalibrationRecordDB(Base):
    """
    جدول کالیبراسیون نوجین
    """
    __tablename__ = 'nojin_calibration_records'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    formulation_id = Column(PG_UUID(as_uuid=True), ForeignKey('nojin_formulations.id'), nullable=False)
    calibration_date = Column(Date, nullable=False)
    calibration_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility
    model_version = Column(String(100), nullable=False)
    parameters_updated = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    validation_results = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    calibration_quality_score = Column(Float, nullable=True)
    calibrated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# ENGINEERING STRUCTURE MODELS
# ============================================================================
# Models for designing and managing engineering structures.

class EngineeringStructureDB(Base):
    """
    جدول سازه‌های مهندسی
    """
    __tablename__ = 'engineering_structures'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    structure_type = Column(String(100), nullable=False) # e.g., 'drain', 'channel', 'weir', 'dam', 'culvert', 'checkdam'
    structure_name = Column(String(255), nullable=True)
    # location = Column(Geography('POINT'), nullable=True) # Requires PostGIS
    location = Column(String(255), nullable=True) # Fallback to 'lat,lng' string
    design_parameters = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # All inputs for the design calculation
    design_calculation = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Results from the design engine
    material_specifications = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Materials and quantities
    construction_cost = Column(Float, nullable=True) # Estimated cost
    maintenance_cost_annual = Column(Float, nullable=True) # Annual maintenance cost
    lifespan_years = Column(Integer, nullable=True) # Expected lifespan
    safety_factor = Column(Float, nullable=True) # Design safety factor
    design_standard = Column(String(100), nullable=True) # e.g., 'ACI', 'ASCE'
    status = Column(String(50), default='planned') # 'planned', 'designed', 'approved', 'constructed', 'operational', 'decommissioned'
    constructed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InnovativeStructureDB(Base):
    """
    جدول طراحی‌های نوآورانه
    """
    __tablename__ = 'innovative_structures'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    structure_id = Column(PG_UUID(as_uuid=True), ForeignKey('engineering_structures.id'), nullable=True) # Links to a standard structure if applicable
    innovation_type = Column(String(100), nullable=False) # e.g., 'bioengineered_channel', 'permeable_checkdam'
    design_concept = Column(Text, nullable=False) # Description of the innovative idea
    technical_specifications = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Detailed tech specs
    energy_dissipation_design = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Specific design aspects
    groundwater_recharge_design = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Specific design aspects
    flood_control_design = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Specific design aspects
    pilot_test_results = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Results from small-scale tests
    patent_status = Column(String(100), nullable=True) # e.g., 'pending', 'granted', 'open_source'
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# ECONOMIC & FINANCIAL MODELS
# ============================================================================
# Models for economic analysis, costing, revenue, and financial tracking.

class EconomicAnalysisDB(Base):
    """
    جدول تحلیل اقتصادی پروژه
    """
    __tablename__ = 'economic_analyses'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False) # Assumes a 'projects' table exists
    project_id = Column(String(255), nullable=False) # Fallback if no specific project table
    analysis_type = Column(String(100), nullable=False) # e.g., 'feasibility', 'ex-post_evaluation'
    base_year = Column(Integer, nullable=False)
    projection_years = Column(Integer, nullable=False)
    discount_rate = Column(Float, nullable=False)
    inflation_rate = Column(Float, nullable=True)
    currency = Column(String(10), default='IRR')
    npv = Column(Float, nullable=True)
    irr = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    payback_period_years = Column(Float, nullable=True)
    cash_flow_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Stores yearly cash flows
    sensitivity_analysis = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    risk_assessment = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    assumptions = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectCostDB(Base):
    """
    جدول هزینه‌های پروژه
    """
    __tablename__ = 'project_costs'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    project_id = Column(String(255), nullable=False)
    cost_category = Column(String(100), nullable=False) # e.g., 'capital', 'operational', 'maintenance'
    cost_type = Column(String(100), nullable=False) # e.g., 'labor', 'materials', 'equipment_rental'
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='IRR')
    cost_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    # associated_structure_id = Column(PG_UUID(as_uuid=True), ForeignKey('engineering_structures.id'), nullable=True)
    associated_structure_id = Column(String(255), nullable=True) # Fallback
    # associated_crop_id = Column(PG_UUID(as_uuid=True), nullable=True) # Could link to a crop plan table
    associated_crop_id = Column(String(255), nullable=True) # Fallback
    # associated_biofertilizer_id = Column(PG_UUID(as_uuid=True), ForeignKey('nojin_formulations.id'), nullable=True)
    associated_biofertilizer_id = Column(String(255), nullable=True) # Fallback
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectRevenueDB(Base):
    """
    جدول درآمدهای پروژه
    """
    __tablename__ = 'project_revenues'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    project_id = Column(String(255), nullable=False)
    revenue_category = Column(String(100), nullable=False) # e.g., 'agricultural_sales', 'carbon_credits', 'ecosystem_services'
    revenue_type = Column(String(100), nullable=False) # e.g., 'produce_sale', 'certified_emission_reduction'
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='IRR')
    revenue_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    associated_yield = Column(Float, nullable=True) # Tonnes sold
    associated_carbon_credit = Column(Float, nullable=True) # Tonnes CO2e credited
    created_at = Column(DateTime, default=datetime.utcnow)


class ProfitDistributionDB(Base):
    """
    جدول تقسیم سود
    """
    __tablename__ = 'profit_distributions'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    project_id = Column(String(255), nullable=False)
    distribution_period = Column(String(50), nullable=False) # e.g., 'monthly', 'quarterly', 'yearly'
    total_profit = Column(Float, nullable=False)
    distribution_ratio = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"farmer": 0.6, "investor": 0.3, "community": 0.1}
    distribution_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"farmer_amount": X, "investor_amount": Y, ...}
    smart_contract_address = Column(String(255), nullable=True) # If using blockchain
    smart_contract_status = Column(String(50), nullable=True) # e.g., 'pending', 'executed', 'failed'
    distributed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# MONITORING & CALIBRATION MODELS
# ============================================================================
# Models for storing monitoring data, calibration records, and model versions.

class MonitoringDataDB(Base):
    """
    جدول داده‌های پایش
    """
    __tablename__ = 'monitoring_data'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    project_id = Column(String(255), nullable=False) # Fallback if no specific project table
    monitoring_type = Column(String(50), nullable=False) # e.g., 'satellite', 'field', 'mobile'
    monitoring_date = Column(Date, nullable=False)
    # location = Column(Geography('POINT'), nullable=True) # Requires PostGIS
    location = Column(String(255), nullable=True) # Fallback to 'lat,lng' string
    data_source = Column(String(255), nullable=True) # e.g., 'Sentinel-2', 'sensor_001', 'user_002'
    data_quality_score = Column(Float, nullable=True) # e.g., 0.0 (bad) to 1.0 (excellent)
    measurement_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Stores the raw or processed measurements
    quality_flags = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Stores flags like 'cloud_cover_high', 'sensor_error'
    created_at = Column(DateTime, default=datetime.utcnow)


class CalibrationRecordDB(Base):
    """
    جدول رکوردهای کالیبراسیون
    """
    __tablename__ = 'calibration_records'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    model_name = Column(String(100), nullable=False) # e.g., 'soil_nutrient_model', 'crop_yield_model'
    model_version = Column(String(50), nullable=False) # e.g., '1.0.0', '1.1.0-calibrated'
    calibration_date = Column(Date, nullable=False)
    calibration_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Summary of data used for calibration
    parameters_before = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Parameters before calibration
    parameters_after = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Parameters after calibration
    calibration_metrics = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Metrics like RMSE, NSE
    calibration_quality_score = Column(Float, nullable=True) # Overall score of calibration quality
    validation_results = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Results from validation step
    calibrated_by = Column(String(255), nullable=True) # User or system that performed calibration
    approved_by = Column(String(255), nullable=True) # User who approved the calibration
    approved_at = Column(DateTime, nullable=True) # When it was approved
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelVersionDB(Base):
    """
    جدول نسخه‌های مدل
    """
    __tablename__ = 'model_versions'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    model_name = Column(String(100), nullable=False)
    version_number = Column(String(50), nullable=False) # e.g., '1.0.0', '1.0.0-cal-20241027'
    version_type = Column(String(50), nullable=False) # e.g., 'major', 'minor', 'patch', 'calibrated'
    release_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False) # What changed in this version
    parameters = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Full set of model parameters for this version
    performance_metrics = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Performance on benchmark datasets
    # calibration_record_id = Column(PG_UUID(as_uuid=True), ForeignKey('calibration_records.id'), nullable=True)
    calibration_record_id = Column(String(255), nullable=True) # Fallback if no specific cal record table
    is_current = Column(Boolean, default=False) # Flag to indicate the active version
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# SCENARIO, OPTIMIZATION & DECISION SUPPORT MODELS
# ============================================================================
# Models for storing scenarios, their results, optimization outcomes, and recommendations.

class ScenarioDB(Base):
    """
    جدول سناریوها
    """
    __tablename__ = 'scenarios'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    project_id = Column(String(255), nullable=False) # Fallback if no specific project table
    scenario_name = Column(String(255), nullable=False)
    scenario_type = Column(String(100), nullable=False) # e.g., 'climate_change', 'crop_management'
    # baseline_scenario_id = Column(PG_UUID(as_uuid=True), ForeignKey('scenarios.id'), nullable=True)
    baseline_scenario_id = Column(String(255), nullable=True) # Fallback
    description = Column(Text, nullable=True)
    assumptions = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"co2_concentration_ppm": 450}
    parameters = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"temp_change_degC": 2.0}
    expected_outcomes = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"yield_change_percent": 5.0}
    status = Column(String(50), default='draft') # e.g., 'draft', 'running', 'completed'
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScenarioResultDB(Base):
    """
    جدول نتایج سناریو
    """
    __tablename__ = 'scenario_results'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    scenario_id = Column(PG_UUID(as_uuid=True), ForeignKey('scenarios.id'), nullable=False)
    result_type = Column(String(100), nullable=False) # e.g., 'simulation_output', 'economic_analysis', 'full_analysis'
    result_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Stores the complex output dictionary
    uncertainty_data = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., confidence intervals, MC variance
    confidence_level = Column(Float, nullable=True) # e.g., 0.95
    created_at = Column(DateTime, default=datetime.utcnow)


class OptimizationResultDB(Base):
    """
    جدول نتایج بهینه‌سازی
    """
    __tablename__ = 'optimization_results'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    scenario_id = Column(PG_UUID(as_uuid=True), ForeignKey('scenarios.id'), nullable=False)
    optimization_type = Column(String(100), nullable=False) # e.g., 'crop_mix', 'fertilizer_rate'
    objective_function = Column(String(500), nullable=False) # e.g., '{"yield": 0.4, "profit": 0.4, "risk": 0.2}'
    constraints = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"max_area_ha": 100, "min_profit_irr": 5000000}
    optimal_solution = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"crop_a_ha": 60, "crop_b_ha": 40}
    sensitivity_analysis = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Sensitivity of solution to parameters
    pareto_front = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Points on the Pareto frontier
    convergence_metrics = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # Info from the optimizer
    computation_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DecisionRecommendationDB(Base):
    """
    جدول توصیه‌های تصمیمیار
    """
    __tablename__ = 'decision_recommendations'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    # project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    project_id = Column(String(255), nullable=False) # Fallback if no specific project table
    recommendation_type = Column(String(100), nullable=False) # e.g., 'crop_selection', 'infrastructure_investment'
    recommendation_data = Column(JSON, nullable=False) # Changed from JSONB to JSON for SQLite compatibility # Full details of the recommendation
    confidence_level = Column(Float, nullable=False) # e.g., 0.85
    risk_level = Column(String(50), nullable=False) # e.g., 'low', 'medium', 'high'
    economic_impact = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"NPV_irr": 5000000, "IRR_fraction": 0.12}
    environmental_impact = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"co2_reduction_tonnes": 100}
    social_impact = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"jobs_created": 2.5}
    implementation_timeline = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"start": "2024-06-01", "end": "2024-10-30"}
    monitoring_plan = Column(JSON, nullable=True) # Changed from JSONB to JSON for SQLite compatibility # e.g., {"checkpoints": [...], "kpis": [...]}
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    implemented_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# TOPOGRAPHY ANALYSIS RESULT MODEL
# ============================================================================
class TopographyAnalysisResult(Base):
    __tablename__ = "topography_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(255), nullable=False)  # Unique identifier for the site
    dem_path = Column(String(1000), nullable=False)  # Path to the input DEM file
    analysis_types = Column(JSON, nullable=False)  # Serialized list of analysis types performed
    slope_map_path = Column(String(1000), nullable=True)  # Path to the output slope map
    aspect_map_path = Column(String(1000), nullable=True)  # Path to the output aspect map
    curvature_map_path = Column(String(1000), nullable=True)  # Path to the output curvature map
    flow_direction_map_path = Column(String(1000), nullable=True)  # Path to the output flow direction map
    flow_accumulation_map_path = Column(String(1000), nullable=True)  # Path to the output flow accumulation map
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp of record creation