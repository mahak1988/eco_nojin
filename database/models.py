"""SQLAlchemy ORM models - Complete unified schema."""

import secrets
from datetime import datetime, timedelta

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
            expires_at=datetime.utcnow() + timedelta(hours=hours_valid),
            used=False,
        )

    @property
    def is_valid(self) -> bool:
        return not self.used and self.expires_at > datetime.utcnow()


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
