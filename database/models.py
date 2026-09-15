import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.base import Base


def _uuid():
    return str(uuid.uuid4())

def generate_uuid():
    """Generate a UUID string for primary keys"""
    return str(uuid.uuid4())


# --- مدل کاربر ---
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    language = Column(String, default="fa")
    platform_id = Column(String, nullable=True, index=True)
    is_email_verified = Column(Boolean, default=False)

    land_profiles = relationship("LandProfile", back_populates="user")


class OrganizationRole(str, PyEnum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationStatus(str, PyEnum):
    ACTIVE = "active"
    INVITED = "invited"
    REMOVED = "removed"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    country = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    members = relationship("OrganizationMembership", back_populates="organization")


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id = Column(String, primary_key=True, default=_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(OrganizationRole), nullable=False, default=OrganizationRole.MEMBER)
    status = Column(Enum(OrganizationStatus), nullable=False, default=OrganizationStatus.INVITED)
    joined_at = Column(DateTime, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    organization = relationship("Organization", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_org_user"),
        Index("ix_org_membership_org_status", "org_id", "status"),
        Index("ix_org_membership_user_status", "user_id", "status"),
    )


# --- مدل پروفایل زمین (اصلاح شده در مراحل قبل) ---
class LandProfile(Base):
    __tablename__ = "land_profiles"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    area_ha = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="land_profiles")

    # تعریف صحیح __table_args__ با چندین محدودیت
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='_user_land_name_uc'),
        CheckConstraint("name != ''", name='ck_land_profile_name_not_empty')
    )


# --- مدل‌های دیگر مورد نیاز ---
# ترتیب این مدل‌ها مهم است. مدل‌هایی که مورد ارجاع قرار می‌گیرند باید اول تعریف شوند.  # noqa: RUF003

class AuditLog(Base):
    """Audit trail for data changes and security events."""
    __tablename__ = "auditlog"

    id = Column(Integer, primary_key=True)
    actor_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class LedgerEntry(Base):
    """Double-entry ledger for carbon credits and ECO token movements."""
    __tablename__ = "ledgerentry"

    id = Column(Integer, primary_key=True)
    account_id = Column(String, nullable=False, index=True)
    entry_type = Column(String, nullable=False)  # debit | credit
    asset = Column(String, nullable=False)  # carbon_credit | eco_token | fiat
    amount = Column(Numeric(19, 4), nullable=False)
    reference_type = Column(String, nullable=True)
    reference_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class Notification(Base):
    """Multi-channel user notification record."""
    __tablename__ = "notification"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False)  # email | sms | in_app | telegram
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    extra_data = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending | sent | read | failed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    read_at = Column(DateTime, nullable=True)

class EcoWallet(Base):
    __tablename__ = "ecowallet"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    balance = Column(Numeric(19, 4), default=0.0)
    total_earned = Column(Numeric(19, 4), default=0.0)
    total_redeemed = Column(Numeric(19, 4), default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    token = Column(String)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    @property
    def is_valid(self) -> bool:
        """True when the token has not been used and has not expired.
        Handles both timezone-aware and naive datetimes (SQLite stores
        datetimes as naive strings)."""
        if self.used:
            return False
        if self.expires_at is None:
            return False
        now = datetime.now(UTC)
        expires = self.expires_at
        # If the stored datetime is naive, compare against naive now.
        if expires.tzinfo is None:
            now = now.replace(tzinfo=None)
        return now < expires

    @classmethod
    def create_for_user(cls, user_id: str, hours_valid: int = 1) -> "PasswordResetToken":
        """Create a new reset token valid for `hours_valid` hours."""
        return cls(
            user_id=user_id,
            token=str(uuid.uuid4()),
            expires_at=datetime.now(UTC) + timedelta(hours=hours_valid),
            used=False,
        )

class TopographyAnalysisResult(Base):
    __tablename__ = "topography_analysis_results"
    id = Column(Integer, primary_key=True)
    profile_id = Column(String)
    data = Column(String)

class IoTDevice(Base):
    __tablename__ = "iot_devices"

    id = Column(String, primary_key=True, default=_uuid)
    device_name = Column(String(200), nullable=False)
    device_type = Column(String(50), nullable=False, index=True)  # sensor, gateway, actuator
    sensor_types = Column(JSON, nullable=False, default=list)  # ["soil_moisture", "temp", "ec"]
    location = Column(JSON, nullable=True)  # {"lat": 35.6892, "lon": 51.3890, "address": "..."}
    status = Column(String(20), default="active", index=True)  # active, inactive, error
    firmware_version = Column(String(50), nullable=True)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    platform_id = Column(String(100), nullable=True, index=True)  # TTN device_id, etc.

    __table_args__ = (
        Index("ix_iot_device_status_type", "status", "device_type"),
        Index("ix_iot_device_platform", "platform_id"),
    )

    def __repr__(self):
        return f"<IoTDevice id={self.id} name={self.device_name} type={self.device_type} status={self.status}>"


class MRVObservation(Base):
    __tablename__ = "mrvobservation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(200), nullable=False, index=True)
    level = Column(Integer, nullable=False)  # 1=satellite, 2=iot, 3=citizen
    source = Column(String(50), nullable=False)  # satellite, iot, citizen
    sensor_type = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    data_source = Column(String(20), nullable=False)  # real, simulated, no_data
    qa_status = Column(String(20), nullable=False)  # ok, suspect, rejected
    qa_message = Column(Text, nullable=True)
    observed_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_mrv_obs_site_level", "site_id", "level"),
        Index("ix_mrv_obs_site_sensor_time", "site_id", "sensor_type", "observed_at"),
        Index("ix_mrv_obs_qa_status", "qa_status"),
    )

    def __repr__(self):
        return f"<MRVObservation id={self.id} site={self.site_id} sensor={self.sensor_type} qa={self.qa_status}>"


class Setting(Base):
    """System-wide settings storage (key-value pairs)"""
    __tablename__ = "settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String, nullable=True)
    category = Column(String, default='general')
    is_secret = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class FinIdempotencyKey(Base):
    """Idempotency key storage for financial operations."""
    __tablename__ = "fin_idempotency_key"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False)
    route = Column(String, nullable=False)
    request_hash = Column(String(64), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, completed, failed
    response_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_fin_idempotency_user_key", "user_id", "key", unique=True),
        Index("ix_fin_idempotency_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<FinIdempotencyKey user_id={self.user_id} key={self.key} status={self.status}>"

class ErrorLog(Base):
    __tablename__ = "errorlog"
    id = Column(Integer, primary_key=True)
    path = Column(String(500))
    method = Column(String(10))
    status = Column(Integer)
    message = Column(Text)
    acked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class SimulationRun(Base):
    """Persisted result of a HyDroMa simulation chain run (RUSLE > AquaCrop > RothC)."""
    __tablename__ = "simulationrun"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(64), index=True)
    scenario = Column(String(120), default="baseline")
    area_ha = Column(Float)
    status = Column(String(32), default="completed")
    outputs = Column(JSON)
    message = Column(Text)
    executed_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    __table_args__ = (
        Index("ix_simulationrun_site_executed", "site_id", "executed_at"),
    )

    def __repr__(self):
        return f"<SimulationRun id={self.id} site='{self.site_id}' status='{self.status}>"

class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    name = Column(String)

class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"
    id = Column(Integer, primary_key=True)
    farm_id = Column(String)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)
    __table_args__ = (
        Index("ix_soil_analyses_farm_analyzed", "farm_id", "analyzed_at"),
    )


class SatelliteAnalysis(Base):
    __tablename__ = "satellite_analyses"
    id = Column(Integer, primary_key=True)
    farm_id = Column(String)
    ndvi = Column(Float)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)
    __table_args__ = (
        Index("ix_satellite_analyses_farm_analyzed", "farm_id", "analyzed_at"),
    )

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)

class CarbonProject(Base):
    __tablename__ = "carbon_projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    project_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    platform_id = Column(String, nullable=True, index=True)
    project_type = Column(String(80), nullable=True)
    area_hectares = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="draft")
    credits_issued = Column(Float, nullable=True)
    registered_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)
    verification_detail = Column(Text, nullable=True)
    estimated_carbon_tonnes = Column(Float, nullable=True)
    annual_rate_tonnes = Column(Float, nullable=True)
    methodology = Column(String(120), nullable=True)
    region = Column(String(80), nullable=True)
    duration_years = Column(Integer, nullable=True)
    price_per_tonne_usd = Column(Float, nullable=True)
    estimated_revenue_usd = Column(Float, nullable=True)
    confidence = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_carbon_projects_user_status", "user_id", "status"),
        Index("ix_carbon_projects_platform_status", "platform_id", "status"),
    )

class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class EcoTransaction(Base):
    __tablename__ = "ecotransaction"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    amount = Column(Numeric(19, 4))
    transaction_type = Column(String)  # earn | redeem | transfer
    category = Column(String)
    reference_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

class CalibrationRecordDB(Base):
    __tablename__ = "calibrationrecorddb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    # Add other relevant fields

# --- مدل‌های Placeholder با رابطه ---
# توجه کنید که مدل‌هایی که از land_profiles یا users ارجاع می‌دهند، بعد از آن‌ها تعریف می‌شوند.  # noqa: RUF003

class NojinApplicationPlanDB(Base):
    __tablename__ = "nojin_application_plans" # احتمالاً اسم جدول از خطا تشخیص داده شده
    id = Column(Integer, primary_key=True)
    land_profile_id = Column(String, ForeignKey('land_profiles.id')) # اضافه کردن ForeignKey
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # افزودن رابطه
    land_profile = relationship("LandProfile")

    __table_args__ = (
        Index("ix_nojin_app_plan_profile_created", "land_profile_id", "created_at"),
    )

class NojinCalibrationRecordDB(Base):
    __tablename__ = "nojincalibrationrecorddb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id')) # اضافه کردن ForeignKey
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

class ModelVersionDB(Base):
    __tablename__ = "modelversiondb"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

class ScenarioResultDB(Base):
    __tablename__ = "scenarioresultdb"
    id = Column(Integer, primary_key=True)
    scenario_run_id = Column(Integer, ForeignKey('scenariorun.id')) # نیاز به تعریف scenariorun اول
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    scenario_run = relationship("ScenarioRun")

class ScenarioRun(Base):
    __tablename__ = "scenariorun"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

class DecisionRecommendationDB(Base):
    __tablename__ = "decisionrecommendationdb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

class OptimizationResultDB(Base):
    __tablename__ = "optimizationresultdb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

class MonitoringDataDB(Base):
    __tablename__ = "monitoringdatadb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

class NojinFieldTrialDB(Base):
    __tablename__ = "nojinfieldtrialdb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

class ScenarioDB(Base):
    __tablename__ = "scenariodb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")

# Add other models similarly...
# --- Public website contact messages (public site phase) ---
class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    role = Column(String(80), nullable=True)
    message = Column(Text, nullable=False)
    locale = Column(String(8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
# --- Pilot applications (public site phase) ---
class PilotApplication(Base):
    __tablename__ = "pilot_applications"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    province = Column(String(80), nullable=False)
    land_hectares = Column(Float, nullable=True)
    main_crop = Column(String(120), nullable=True)
    preferred_channel = Column(String(40), nullable=True)
    consent = Column(Boolean, nullable=False, default=False)
    locale = Column(String(8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


# --- Newsletter subscribers (public site phase) ---
class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String(200), nullable=False, unique=True, index=True)
    locale = Column(String(8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
# --- HyDroMa data hub: per-user model runs (public dashboard aggregation) ---
class ModelRun(Base):
    __tablename__ = "hydroma_model_runs"

    id = Column(String, primary_key=True, default=_uuid)
    user_key = Column(String(64), nullable=False, index=True)
    model_id = Column(String(80), nullable=False, index=True)
    title = Column(String(160), nullable=True)
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    shared = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_model_run_user_model_created", "user_key", "model_id", "created_at"),
    )


class OAuthConnection(Base):
    """OAuth provider connection for a user (Google, GitHub, Microsoft, etc.)"""
    __tablename__ = "oauth_connections"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=True)
    access_token_encrypted = Column(String, nullable=True)
    refresh_token_encrypted = Column(String, nullable=True)
    connected_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uq_user_provider_oauth'),
    )


class ApiKey(Base):
    """API key for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_used_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", lazy="selectin")
