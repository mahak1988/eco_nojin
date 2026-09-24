import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
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
from sqlalchemy.ext.hybrid import hybrid_property
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
    # baseline repair: auth router (register/login/me) requires these columns
    role = Column(String, default="regular")
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)

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
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

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
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

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
    description = Column(Text, nullable=True)
    dem_source = Column(String(100), nullable=True)
    dem_resolution_m = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="land_profiles")

    # تعریف صحیح __table_args__ با چندین محدودیت
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="_user_land_name_uc"),
        CheckConstraint("name != ''", name="ck_land_profile_name_not_empty"),
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


class FinJournalBatch(Base):
    """Journal batch for double-entry accounting."""

    __tablename__ = "fin_journal_batch"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    batch_date = Column(Date, nullable=False)
    reference_type = Column(String, nullable=True)  # order, payment, eco_earning, carbon_issuance
    reference_id = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    is_posted = Column(Boolean, default=False, nullable=False)


class FinJournalEntry(Base):
    """Individual journal entry within a batch."""

    __tablename__ = "fin_journal_entry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)
    entry_type = Column(String, nullable=False)  # debit | credit
    asset = Column(String, nullable=False)  # IRR, ECO, CARBON_tCO2e, USD
    amount = Column(Numeric(19, 4), nullable=False)
    description = Column(Text, nullable=True)


class FinAccount(Base):
    """Chart of accounts."""

    __tablename__ = "fin_account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # asset, liability, equity, income, expense
    asset = Column(String, nullable=True)  # IRR, ECO, CARBON_tCO2e, USD
    currency = Column(String(3), default="IRR")
    parent_id = Column(Integer, ForeignKey("fin_account.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


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
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


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
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    platform_id = Column(String(100), nullable=True)  # TTN device_id, etc.

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
    category = Column(String, default="general")
    is_secret = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


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


class AuditEvent(Base):
    """Immutable audit trail for financial and operational events."""

    __tablename__ = "audit_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    actor_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # create, update, delete, earn, redeem, pay, etc.
    resource_type = Column(
        String(50), nullable=False, index=True
    )  # wallet, order, payment, inventory, etc.
    resource_id = Column(String(100), nullable=False, index=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(64), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_audit_event_correlation", "correlation_id"),
        Index("ix_audit_event_actor_action", "actor_id", "action"),
        Index("ix_audit_event_resource", "resource_type", "resource_id"),
        Index("ix_audit_event_created", "created_at"),
    )

    def __repr__(self):
        return f"<AuditEvent id={self.id} action={self.action} resource={self.resource_type}:{self.resource_id}>"


def __repr__(self):
    return f"<AuditEvent id={self.id} action={self.action} resource={self.resource_type}:{self.resource_id}>"


class IntOutboxEvent(Base):
    """Outbox event for event-driven integration."""

    __tablename__ = "int_outbox_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aggregate_type = Column(String, nullable=False, index=True)
    aggregate_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    supabase_synced = Column(Boolean, default=False, nullable=False)
    last_error = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_int_outbox_unprocessed", "created_at", postgresql_where="processed_at IS NULL"),
    )

    def __repr__(self):
        return f"<IntOutboxEvent id={self.id} type={self.event_type} aggregate={self.aggregate_type}:{self.aggregate_id}>"


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

    __table_args__ = (Index("ix_simulationrun_site_executed", "site_id", "executed_at"),)

    def __repr__(self):
        return f"<SimulationRun id={self.id} site='{self.site_id}' status='{self.status}>"


class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    name = Column(String)
    # D2 fix: columns the farms router writes/reads (previously missing -> 500)
    owner_id = Column(String, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    elevation_m = Column(Float, nullable=True)
    area_hectares = Column(Float, nullable=True)
    soil_type = Column(String, nullable=True)
    climate_zone = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)


class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"
    id = Column(Integer, primary_key=True)
    farm_id = Column(String)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)
    __table_args__ = (Index("ix_soil_analyses_farm_analyzed", "farm_id", "analyzed_at"),)


class SatelliteAnalysis(Base):
    __tablename__ = "satellite_analyses"
    id = Column(Integer, primary_key=True)
    farm_id = Column(String)
    ndvi = Column(Float)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=True)
    __table_args__ = (Index("ix_satellite_analyses_farm_analyzed", "farm_id", "analyzed_at"),)


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)


class CarbonProject(Base):
    __tablename__ = "carbon_projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    project_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
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
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    issued_at = Column(DateTime, nullable=True)
    verification_status = Column(String(32), nullable=True, default="unverified")
    field_verified = Column(Boolean, default=False, nullable=False)
    mrv_documents = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_carbon_projects_user_status", "user_id", "status"),
        Index("ix_carbon_projects_platform_status", "platform_id", "status"),
        Index("ix_carbon_projects_lifecycle", "status", "verification_status"),
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
    __tablename__ = "nojin_application_plans"  # احتمالاً اسم جدول از خطا تشخیص داده شده
    id = Column(Integer, primary_key=True)
    land_profile_id = Column(String, ForeignKey("land_profiles.id"))  # اضافه کردن ForeignKey
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # افزودن رابطه
    land_profile = relationship("LandProfile")

    __table_args__ = (Index("ix_nojin_app_plan_profile_created", "land_profile_id", "created_at"),)


class NojinCalibrationRecordDB(Base):
    __tablename__ = "nojincalibrationrecorddb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))  # اضافه کردن ForeignKey
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")


class ModelVersionDB(Base):
    __tablename__ = "modelversiondb"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ScenarioResultDB(Base):
    __tablename__ = "scenarioresultdb"
    id = Column(Integer, primary_key=True)
    scenario_run_id = Column(Integer, ForeignKey("scenariorun.id"))  # نیاز به تعریف scenariorun اول
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    scenario_run = relationship("ScenarioRun")


class ScenarioRun(Base):
    __tablename__ = "scenariorun"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")


class DecisionRecommendationDB(Base):
    __tablename__ = "decisionrecommendationdb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")


class OptimizationResultDB(Base):
    __tablename__ = "optimizationresultdb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")


class MonitoringDataDB(Base):
    __tablename__ = "monitoringdatadb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")


class NojinFieldTrialDB(Base):
    __tablename__ = "nojinfieldtrialdb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    user = relationship("User")


class ScenarioDB(Base):
    __tablename__ = "scenariodb"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
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
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=True)
    access_token_encrypted = Column(String, nullable=True)
    refresh_token_encrypted = Column(String, nullable=True)
    connected_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    user = relationship("User", lazy="selectin")

    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider_oauth"),)


class ApiKey(Base):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_used_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", lazy="selectin")


# === Carbon MRV credit ledger (Phase 8) ==============================
# Sustainable & auditable carbon-credit issuance backed by the
# CarbonMrvMotor accounting engine. No fabricated hashes and no claim of
# endorsement by any real Validation/Verification Body (VVB): verification
# here is the honest, methodology-aligned check from
# ``services.carbon.verification`` plus the motor's data provenance.


class CarbonCreditState(str, PyEnum):
    """Lifecycle state of an issued carbon credit (fungible lot)."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class CarbonCredit(Base):
    """A fungible carbon-credit lot issued from a verified project.

    Double-issuance / double-counting safeguards live at two layers:
      * DB constraints: unique ``credit_id``/``serial``;
        ``retired_amount <= total_amount`` and ``available_amount >= 0``.
      * Service layer: idempotency keys, holder-ownership checks, and the
        irreversible retirement accounting in ``services.carbon.service``.
    """

    __tablename__ = "carbon_credits"

    id = Column(Integer, primary_key=True)
    credit_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"CR-{uuid.uuid4().hex}",
    )
    project_id = Column(
        String(64),
        ForeignKey("carbon_projects.project_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    serial = Column(
        String(80),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"SER-{uuid.uuid4().hex}",
    )
    vintage_year = Column(Integer, nullable=False)
    methodology = Column(String(120), nullable=True)
    standard = Column(String(120), nullable=True)
    data_mode = Column(
        String(32),
        nullable=False,
        default="modelled_estimate",
    )  # modelled_estimate | field_verified
    mrv_documents = Column(JSON, nullable=True)
    total_amount = Column(Numeric(19, 4), nullable=False)
    retired_amount = Column(Numeric(19, 4), default=Decimal("0"), nullable=False)
    available_amount = Column(Numeric(19, 4), nullable=False)
    holder_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    state = Column(
        Enum(CarbonCreditState, name="carbon_credit_state", length=16),
        nullable=False,
        default=CarbonCreditState.DRAFT,
    )
    issued_by = Column(String, nullable=True)
    issued_at = Column(DateTime, nullable=True)

    # Freeze / unfreeze bookkeeping (actor & authority recorded for audit)
    frozen = Column(Boolean, default=False, nullable=False)
    frozen_by = Column(String, nullable=True)
    frozen_authority = Column(String, nullable=True)
    frozen_reason = Column(Text, nullable=True)
    frozen_at = Column(DateTime, nullable=True)

    version = Column(Integer, nullable=False, default=1)  # optimistic concurrency
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("retired_amount >= 0", name="ck_carbon_credits_retired_non_negative"),
        CheckConstraint("available_amount >= 0", name="ck_carbon_credits_available_non_negative"),
        CheckConstraint(
            "retired_amount <= total_amount", name="ck_carbon_credits_retired_le_total"
        ),
        Index("ix_carbon_credits_project_state", "project_id", "state"),
        Index("ix_carbon_credits_holder_state", "holder_id", "state"),
    )


class CarbonEvent(Base):
    """Immutable event log for the credit/project lifecycle (event sourcing)."""

    __tablename__ = "carbon_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"EVT-{uuid.uuid4().hex}",
    )
    aggregate_type = Column(String(32), nullable=False)  # credit | project
    aggregate_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(32), nullable=False, index=True)
    actor = Column(String, nullable=True)
    authority = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    correlation_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_carbon_events_aggregate", "aggregate_type", "aggregate_id", "created_at"),
    )


class CreditAuditLog(Base):
    """Projectable, immutable audit trail for compliance queries.

    A denormalized projection of significant credit actions (issue / transfer /
    retire / freeze / unfreeze) kept for straightforward audit reads.
    """

    __tablename__ = "carbon_audit_log"

    id = Column(Integer, primary_key=True)
    event_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"EVT-{uuid.uuid4().hex}",
    )
    audit_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"AUD-{uuid.uuid4().hex}",
    )
    credit_id = Column(String(64), index=True, nullable=True)
    project_id = Column(String(64), index=True, nullable=True)
    action = Column(String(32), nullable=False)
    actor = Column(String, nullable=True)
    authority = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    before_state = Column(String(32), nullable=True)
    after_state = Column(String(32), nullable=True)
    delta_amount = Column(Numeric(19, 4), nullable=True)
    correlation_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_carbon_audit_credit", "credit_id", "created_at"),
        Index("ix_carbon_audit_project", "project_id", "created_at"),
    )


class IdempotencyKey(Base):
    """Client-supplied idempotency key for safe retries (no fabricated hash).

    The key is stored verbatim so an identical client request can never produce
    a second credit or a second retirement.
    """

    __tablename__ = "idempotency_keys"

    key = Column(String(128), primary_key=True)
    action = Column(String(32), nullable=False, index=True)
    result_reference = Column(String(128), nullable=True, index=True)
    status = Column(String(16), nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_idempotency_keys_action_status", "action", "status"),)


class RefreshToken(Base):
    """Refresh token storage for rotation tracking (H12 fix).
    Each refresh token is tracked by its JTI (JWT ID) to enable
    revocation of old tokens during rotation.
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (Index("ix_refresh_tokens_user_revoked", "user_id", "revoked"),)


ORDER_STATE_MACHINE = {
    "draft": {
        "allowed": {"reserved", "cancelled"},
        "requires": {"reserved": {}, "cancelled": {}},
    },
    "reserved": {
        "allowed": {"paid", "cancelled"},
        "requires": {"paid": {"payment": True}, "cancelled": {}},
    },
    "paid": {
        "allowed": {"processing", "cancelled"},
        "requires": {"processing": {}, "cancelled": {}},
    },
    "processing": {
        "allowed": {"shipped", "cancelled"},
        "requires": {"shipped": {"tracking_code": True}, "cancelled": {}},
    },
    "shipped": {
        "allowed": {"delivered"},
        "requires": {"delivered": {}},
    },
    "delivered": {
        "allowed": {"settled"},
        "requires": {"settled": {}},
    },
    "settled": {"allowed": set(), "requires": {}},
    "cancelled": {"allowed": set(), "requires": {}},
}


class DailyEarnings(Base):
    """Daily earnings records for farmer payouts."""

    __tablename__ = "daily_earnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    earnings_type = Column(String(50), nullable=False)  # carbon | eco_token
    amount = Column(Numeric(19, 4), nullable=False)
    source = Column(String(100), nullable=True)  # farm, project, etc.
    reference_id = Column(String(128), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, processed, failed
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_daily_earnings_user_date_type", "user_id", "date", "earnings_type"),
        Index("ix_daily_earnings_status", "status"),
    )


class ComOrder(Base):
    """Commerce order record."""

    __tablename__ = "com_order"

    id = Column(String, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    buyer_id = Column(String, nullable=False)
    seller_id = Column(String, nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    payment_status = Column(String(20), nullable=False, default="pending")
    subtotal = Column(Numeric(18, 4), nullable=False, default=0)
    platform_fee = Column(Numeric(18, 4), nullable=False, default=0)
    landscape_fee = Column(Numeric(18, 4), nullable=False, default=0)
    total = Column(Numeric(18, 4), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="IRR")
    shipping_address = Column(JSON, nullable=True)
    tracking_code = Column(String(100), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_reason = Column(Text, nullable=True)
    idempotency_key = Column(String(64), nullable=True)
    version = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_com_order_status", "status"),
        Index("ix_com_order_buyer", "buyer_id"),
        Index("ix_com_order_seller_status", "seller_id", "status"),
        Index("ix_com_order_idempotency_key", "idempotency_key", unique=True),
    )


class ComOrderItem(Base):
    """Line items for commerce orders."""

    __tablename__ = "com_order_item"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("com_order.id", ondelete="CASCADE"), nullable=False)
    sku_id = Column(Integer, nullable=True)
    sku_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    line_total = Column(Numeric(18, 4), nullable=False)
    warehouse_id = Column(Integer, nullable=True)
    reservation_id = Column(Integer, nullable=True)
    fulfilled_qty = Column(Numeric(18, 4), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_com_order_item_order_id", "order_id"),
        Index("ix_com_order_item_sku_id", "sku_id"),
    )


class ComPaymentIntent(Base):
    """Payment intent for orders."""

    __tablename__ = "com_payment_intent"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("com_order.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(String, nullable=False)
    provider = Column(String(20), nullable=False, default="wallet")
    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="IRR")
    status = Column(String(20), nullable=False, default="requires_action")
    provider_reference = Column(String(255), nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_com_payment_order", "order_id"),
        Index("ix_com_payment_buyer", "buyer_id"),
        Index("ix_com_payment_provider", "provider"),
        Index("ix_com_payment_status", "status"),
    )


class ComSettlement(Base):
    """Order settlement record."""

    __tablename__ = "com_settlement"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("com_order.id"), nullable=False)
    seller_id = Column(String, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="IRR")
    commission_fee = Column(Numeric(18, 4), nullable=False, default=0)
    landscape_fee = Column(Numeric(18, 4), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending")
    journal_batch_id = Column(Integer, nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("ix_com_settlement_seller", "seller_id"),
        Index("ix_com_settlement_status", "status"),
    )


class InvSKU(Base):
    """Inventory SKU/product definition."""

    __tablename__ = "inv_sku"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    uom = Column(String(32), nullable=False, default="kg")
    category_id = Column(Integer, nullable=True, index=True)
    standard_cost = Column(Numeric(19, 4), nullable=True)
    default_warehouse_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )

    __table_args__ = (Index("ix_inv_sku_code_uom", "sku_code", "uom"),)


class InvWarehouse(Base):
    """Inventory warehouse location."""

    __tablename__ = "inv_warehouses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )


class InvLocation(Base):
    """Inventory location within warehouse (bin/shelf)."""

    __tablename__ = "inv_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("inv_warehouses.id"), nullable=False, index=True)
    code = Column(String(64), nullable=False)
    location_type = Column(String(32), nullable=False, default="bin")
    is_active = Column(Boolean, default=True)
    is_pickable = Column(Boolean, default=True)
    is_receivable = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (Index("ix_inv_location_warehouse_code", "warehouse_id", "code", unique=True),)


class InvReservation(Base):
    """Stock reservation for order fulfillment."""

    __tablename__ = "inv_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(Integer, ForeignKey("inv_sku.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inv_warehouses.id"), nullable=False)
    location_id = Column(Integer, nullable=True, index=True)
    lot_id = Column(Integer, nullable=True, index=True)
    qty = Column(Numeric(19, 4), nullable=False)
    consumed_qty = Column(Numeric(19, 4), nullable=False, default=0)
    reserved_for = Column(String(64), nullable=True)  # order_id, etc.
    reference_type = Column(String(32), nullable=False)  # order, etc.
    reference_id = Column(String(128), nullable=False)
    reference_line_id = Column(String(128), nullable=True)
    status = Column(
        String(20), nullable=False, default="active", index=True
    )  # active, consumed, released
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_inv_reservation_sku_status", "sku_id", "status"),
        Index("ix_inv_reservation_reference", "reference_type", "reference_id"),
    )


class InvStockMovement(Base):
    """Stock movement record (receipt, issue, transfer, etc.)."""

    __tablename__ = "inv_stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(Integer, ForeignKey("inv_sku.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inv_warehouses.id"), nullable=False, index=True)
    movement_type = Column(
        String(32), nullable=False, index=True
    )  # receipt, issue, transfer, adjustment, return, scrap
    qty = Column(Numeric(19, 4), nullable=False)
    from_location_id = Column(Integer, nullable=True, index=True)
    to_location_id = Column(Integer, nullable=True, index=True)
    from_warehouse_id = Column(Integer, nullable=True, index=True)
    to_warehouse_id = Column(Integer, nullable=True, index=True)
    lot_id = Column(Integer, nullable=True, index=True)
    unit_cost = Column(Numeric(19, 4), nullable=True)
    total_cost = Column(Numeric(19, 4), nullable=True)
    reference_type = Column(String(32), nullable=True)  # order, stocktake, adjustment
    reference_id = Column(String(128), nullable=True)
    reason = Column(String(200), nullable=True)
    created_by = Column(String, nullable=False)
    location_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index(
            "ix_inv_stock_movements_sku_warehouse_type", "sku_id", "warehouse_id", "movement_type"
        ),
    )


class InvInventoryBalance(Base):
    """Current inventory balance per SKU/warehouse/location/lot."""

    __tablename__ = "inv_inventory_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(Integer, ForeignKey("inv_sku.id"), nullable=False, index=True)
    warehouse_id = Column(
        Integer, ForeignKey("inv_warehouses.id"), nullable=False, default=1, index=True
    )
    location_id = Column(Integer, nullable=False, default=0, index=True)
    lot_id = Column(Integer, nullable=False, default=0, index=True)
    on_hand = Column(Numeric(19, 4), nullable=False, default=0)
    reserved = Column(Numeric(19, 4), nullable=False, default=0)
    blocked = Column(Numeric(19, 4), nullable=False, default=0)
    in_transit = Column(Numeric(19, 4), nullable=False, default=0)
    fifo_cost = Column(Numeric(19, 4), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_inv_balance_sku_wh_loc_lot",
            "sku_id",
            "warehouse_id",
            "location_id",
            "lot_id",
            unique=True,
        ),
    )

    @hybrid_property
    def available(self) -> Decimal:
        """Available stock = on_hand - reserved - blocked."""
        from decimal import Decimal

        on_hand_val = self.on_hand or Decimal("0")
        reserved_val = self.reserved or Decimal("0")
        blocked_val = self.blocked or Decimal("0")
        return on_hand_val - reserved_val - blocked_val


class InvStocktake(Base):
    """Physical inventory stocktake."""

    __tablename__ = "inv_stocktakes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stocktake_number = Column(String(50), unique=True, nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inv_warehouses.id"), nullable=False, index=True)
    stocktake_type = Column(String(32), nullable=False, default="full")  # full, cycle, partial
    status = Column(String(32), nullable=False, default="draft", index=True)
    created_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (Index("ix_inv_stocktake_warehouse_status", "warehouse_id", "status"),)


class InvStocktakeLine(Base):
    """Stocktake line items."""

    __tablename__ = "inv_stocktake_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stocktake_id = Column(Integer, ForeignKey("inv_stocktakes.id"), nullable=False, index=True)
    sku_id = Column(Integer, ForeignKey("inv_sku.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inv_warehouses.id"), nullable=False, index=True)
    location_id = Column(Integer, nullable=True, index=True)
    lot_id = Column(Integer, nullable=True, index=True)
    system_qty = Column(Numeric(19, 4), nullable=True)
    counted_qty = Column(Numeric(19, 4), nullable=False)
    variance_qty = Column(Numeric(19, 4), nullable=False, default=0)
    variance_value = Column(Numeric(19, 4), nullable=True)
    counted_by = Column(String, nullable=True)
    counted_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        String(32), nullable=False, default="pending", index=True
    )  # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (Index("ix_inv_stocktake_line_stocktake_sku", "stocktake_id", "sku_id"),)


class InvValuationMethod(str, PyEnum):
    """Inventory valuation method."""

    FIFO = "fifo"
    WEIGHTED_AVG = "weighted_avg"
    STANDARD = "standard"


class InvValuationMethod(str, PyEnum):
    """Inventory valuation method."""

    FIFO = "fifo"
    WEIGHTED_AVG = "weighted_avg"
    STANDARD = "standard"


class ToolRegistryEntry(Base):
    """Tool registry mapping 62 tools/services to their implementations (Phase 2 prerequisite)."""

    __tablename__ = "tool_registry"

    id = Column(String, primary_key=True, default=_uuid)
    tool_id = Column(String(32), nullable=False, unique=True, index=True)  # H01-H25, M01-M22, etc.
    name_fa = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    domain = Column(
        String(50), nullable=False, index=True
    )  # climate, water, soil, carbon, crop, seed, modeling
    category = Column(String(50), nullable=False)  # algorithm, model, dataset, service
    fidelity = Column(String(20), nullable=True)  # official, simplified, experimental
    reference = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    service_slug = Column(
        String(100), nullable=True
    )  # e.g., "models/et0_hargreaves", "science/citations"
    endpoint_path = Column(String(200), nullable=True)  # e.g., "/api/v1/models/et0_hargreaves/run"
    phase = Column(Integer, nullable=True)  # 1-5 per innovation_registry.json phases
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_tool_registry_domain_category", "domain", "category"),
        Index("ix_tool_registry_service_slug", "service_slug"),
    )


class LegalText(Base):
    """Versioned legal texts per locale (terms, privacy, cookies, e-commerce rules, buy-sell rules)."""

    __tablename__ = "legal_texts"

    id = Column(String, primary_key=True, default=_uuid)
    locale = Column(String(8), nullable=False, index=True)
    slug = Column(
        String(64), nullable=False, index=True
    )  # terms, privacy, cookies, ecommerce_rules, buy_sell_rules
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft")  # draft, published, archived
    effective_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("locale", "slug", "version", name="uq_legal_text_locale_slug_version"),
        Index("ix_legal_text_locale_slug_status", "locale", "slug", "status"),
    )


class ContentItem(Base):
    """Editorial content items for the knowledge hub / editorial platform."""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general", index=True)
    language = Column(String(8), nullable=False, default="fa", index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft, published, archived
    source = Column(String(50), nullable=True)  # ai-generated, manual, imported
    generated_by_ai = Column(Boolean, default=False, nullable=False)
    rag_synced = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    versions = relationship("ContentVersion", back_populates="content", order_by="ContentVersion.version.desc()")
    translations = relationship("ContentTranslation", back_populates="content")

    __table_args__ = (
        Index("ix_content_item_status_language", "status", "language"),
        Index("ix_content_item_category_status", "category", "status"),
    )


class ContentVersion(Base):
    """Version history for content items (snapshot before each update)."""

    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    content = relationship("ContentItem", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("content_id", "version", name="uq_content_version"),
        Index("ix_content_version_content_id_version", "content_id", "version"),
    )


class ContentTranslation(Base):
    """Translations of content items into different languages."""

    __tablename__ = "content_translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True)
    locale = Column(String(8), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    source = Column(String(20), nullable=True, default="manual")  # manual, ai
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    content = relationship("ContentItem", back_populates="translations")

    __table_args__ = (
        UniqueConstraint("content_id", "locale", name="uq_content_translation_locale"),
        Index("ix_content_translation_content_locale", "content_id", "locale"),
    )


class EscrowState(str, PyEnum):
    """Escrow state machine states."""

    CREATED = "created"
    LOCKED = "locked"
    RELEASED = "released"
    REVERSED = "reversed"
    COMPLETED = "completed"

    def can_transition_to(self, to_state: "EscrowState") -> bool:
        """Check if state transition is valid from this state."""
        valid_transitions = {
            EscrowState.CREATED: {EscrowState.LOCKED},
            EscrowState.LOCKED: {EscrowState.RELEASED, EscrowState.REVERSED},
            EscrowState.RELEASED: {EscrowState.COMPLETED},
            EscrowState.REVERSED: {EscrowState.COMPLETED},
        }
        return to_state in valid_transitions.get(self, set())

    @classmethod
    def can_transition_from(cls, from_state: "EscrowState", to_state: "EscrowState") -> bool:
        """Check if state transition is valid from a given state."""
        valid_transitions = {
            EscrowState.CREATED: {EscrowState.LOCKED},
            EscrowState.LOCKED: {EscrowState.RELEASED, EscrowState.REVERSED},
            EscrowState.RELEASED: {EscrowState.COMPLETED},
            EscrowState.REVERSED: {EscrowState.COMPLETED},
        }
        return to_state in valid_transitions.get(from_state, set())


class EscrowRecord(Base):
    """Escrow record for marketplace order payments."""

    __tablename__ = "escrow_records"

    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, nullable=False, index=True, unique=True)
    payment_id = Column(String, nullable=True, index=True)
    buyer_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    asset = Column(String(16), nullable=False, default="IRT")
    state = Column(String(20), nullable=False, default=EscrowState.CREATED.value)
    dispute_window_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])

    __table_args__ = (
        Index("ix_escrow_record_state", "state"),
        Index("ix_escrow_record_buyer", "buyer_id"),
        Index("ix_escrow_record_seller", "seller_id"),
    )
