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
