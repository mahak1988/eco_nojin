"""Rescued ORM result models.

These six table declarations were previously hidden in a shadowed
``database/models/`` directory, which Python could never import because it
was shadowed by ``database/models.py`. The shadowed files were removed;
their table declarations are consolidated here so the results the engine
computes are durably storable and covered by a migration.

Each model inherits the project-wide ``Base`` from ``database.base`` so
every table registers on one ``MetaData`` registry.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import cast

from sqlalchemy import (
    JSON,
    Boolean,
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
    false,
    text,
    true,
)

from database.base import Base

__all__ = [
    "Base",
    "LandProfile",
    "LandOwnership",
    "LandParcel",
    "LandTenureRight",
    "RunoffCalculationResult",
    "GroundwaterModelResult",
    "CropWaterReqResult",
    "StructureDesignResult",
    "IrrigationDesignResult",
    "CalibrationResult",
    "NojinCalibrationRecordDB",
    "User",
    "CarbonCreditState",
    "CarbonProject",
    "CarbonCredit",
    "CarbonEvent",
    "CreditAuditLog",
    "IdempotencyKey",
    "FinAccount",
    "FinJournalBatch",
    "FinJournalEntry",
    "FinIdempotencyKey",
    "EcoWallet",
    "DailyEarnings",
    "AuditEvent",
    "ComPaymentIntent",
    "ORDER_STATE_MACHINE",
    "ComOrder",
    "ComOrderItem",
    "ComSettlement",
    "InvSKU",
    "InvWarehouse",
    "InvLocation",
    "InvLot",
    "InvInventoryBalance",
    "InvStockMovement",
    "InvReservation",
    "InvStocktake",
    "InvStocktakeLine",
    "ContentItem",
    "ContentVersion",
    "ContentTranslation",
    "Farm",
    "Product",
    "AuditLog",
    "RefreshToken",
    "Setting",
    "AIConversation",
    "SoilAnalysis",
    "EcoTransaction",
    "ScenarioRun",
    "ModelRun",
    "ContactMessage",
    "NewsletterSubscriber",
    "PilotApplication",
    "ToolRegistryEntry",
    "MRVObservation",
    "IntOutboxEvent",
    "LegalText",
    "Organization",
    "OrganizationMembership",
    "LoginHistory",
    "SatelliteAnalysis",
    "IoTDevice",
    "MonitoringDataDB",
    "Notification",
    "LedgerEntry",
    "EscrowRecord",
    "EscrowState",
    "ApiKey",
    "OAuthConnection",
    "PasswordResetToken",
    "SimulationRun",
    "WorkflowRun",
    "WorkflowStatus",
    "CarbonCreditRecord",
    "CarbonRetirement",
    "EcoBalanceAccount",
    "EcoBalanceEntry",
    "OracleChallenge",
    "OracleImpactMetrics",
    "OracleImpactReport",
]

# Aggregate every service-layer model module so that all ORM tables register
# on the shared ``Base.metadata`` registry when this module is imported.
# Mirrors the discovery in ``services/conftest.py::_import_all_models`` so the
# engine's table-registration audit (``test_s12``) sees the same registry the
# application uses, without ``database/`` itself depending on services.
import contextlib  # noqa: E402
import importlib  # noqa: E402
from pathlib import Path  # noqa: E402

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _svc in sorted((_PROJECT_ROOT / "services").iterdir()):
    if not _svc.is_dir() or _svc.name.startswith((".", "_")):
        continue
    for _candidate in (_svc / "models.py", _svc / "models" / "__init__.py"):
        if _candidate.exists():
            _target = f"services.{_svc.name}.models"
            with contextlib.suppress(Exception):
                importlib.import_module(_target)
            break


class LandProfile(Base):
    """Terrain profile underlying every analysis.

    The historical ``services/models/land_models.py`` declared a second
    ``LandProfileDB`` on a twenty-column schema; the collision was removed
    and that class deleted in the same repair.
    """

    __tablename__ = "land_profiles"

    id = Column(String(36), primary_key=True)
    name = Column(String(150), nullable=False)
    geometry = Column(JSON, nullable=True)
    area_ha = Column(Numeric(12, 2), nullable=True)
    area_hectares = Column(Numeric(12, 2), nullable=True)
    elevation_min_m = Column(Float, nullable=True)
    elevation_max_m = Column(Float, nullable=True)
    slope_avg_pct = Column(Float, nullable=True)
    aspect_deg = Column(Float, nullable=True)
    soil_texture = Column(String(50), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    description = Column(String(1000), nullable=True)
    dem_source = Column(String(100), nullable=True)
    dem_resolution_m = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class RunoffCalculationResult(Base):
    """Result of a surface-runoff computation (SCS-CN or D8)."""

    __tablename__ = "runoff_calculation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    land_profile_id = Column(String(36), ForeignKey("land_profiles.id"), nullable=False)
    method = Column(String(50), nullable=False)
    rainfall_mm = Column(Numeric(10, 2), nullable=False)
    runoff_mm = Column(Numeric(10, 2), nullable=False)
    runoff_volume_m3 = Column(Numeric(14, 2), nullable=True)
    cn_number = Column(Float, nullable=True)
    peak_flow_cms = Column(Float, nullable=True)
    time_of_concentration_min = Column(Float, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class GroundwaterModelResult(Base):
    """Result of a groundwater / Theis-well computation."""

    __tablename__ = "groundwater_model_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    land_profile_id = Column(String(36), ForeignKey("land_profiles.id"), nullable=True)
    model_name = Column(String(100), nullable=False)
    drawdown_m = Column(Numeric(10, 4), nullable=False)
    hydraulic_conductivity = Column(Float, nullable=True)
    transmissivity = Column(Float, nullable=True)
    storativity = Column(Float, nullable=True)
    well_radius_m = Column(Float, nullable=True)
    pumping_rate_m3_day = Column(Numeric(14, 2), nullable=True)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CropWaterReqResult(Base):
    """Result of the FAO-56 crop-water-requirement calculation."""

    __tablename__ = "crop_water_req_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    land_profile_id = Column(String(36), ForeignKey("land_profiles.id"), nullable=False)
    crop_type = Column(String(100), nullable=False)
    et_crop_mm = Column(Numeric(10, 2), nullable=False)
    seasonal_water_mm = Column(Numeric(10, 2), nullable=False)
    kc_average = Column(Float, nullable=True)
    growing_days = Column(Integer, nullable=True)
    irrigation_requirement_mm = Column(Numeric(10, 2), nullable=True)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class StructureDesignResult(Base):
    """Result of a water-structure design computation."""

    __tablename__ = "structure_design_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    land_profile_id = Column(String(36), ForeignKey("land_profiles.id"), nullable=False)
    structure_type = Column(String(50), nullable=False)
    design_method = Column(String(50), nullable=False)
    crest_length_m = Column(Numeric(8, 2), nullable=False)
    crest_height_m = Column(Numeric(8, 2), nullable=False)
    storage_m3 = Column(Numeric(14, 2), nullable=False)
    freeboard_m = Column(Numeric(6, 2), nullable=True)
    spillway_discharge_cms = Column(Float, nullable=True)
    factor_of_safety = Column(Float, nullable=True)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class IrrigationDesignResult(Base):
    """Result of an irrigation-system design computation."""

    __tablename__ = "irrigation_design_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    land_profile_id = Column(String(36), ForeignKey("land_profiles.id"), nullable=False)
    system_type = Column(String(50), nullable=False)
    method = Column(String(50), nullable=False)
    area_ha = Column(Numeric(10, 2), nullable=False)
    discharge_lps = Column(Numeric(8, 2), nullable=False)
    emitter_spacing_m = Column(Float, nullable=True)
    operating_pressure_bar = Column(Float, nullable=True)
    total_demand_m3_day = Column(Numeric(14, 2), nullable=True)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CalibrationResult(Base):
    """Result of a model-parameter calibration run."""

    __tablename__ = "calibration_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    objective_function = Column(String(100), nullable=False)
    best_parameters = Column(JSON, nullable=False)
    rmse = Column(Float, nullable=False)
    nash_sutcliffe = Column(Float, nullable=True)
    iterations = Column(Integer, nullable=True)
    converged = Column(Integer, nullable=False, default=0)
    metadata_ = Column(JSON, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class NojinCalibrationRecordDB(Base):
    """Legacy persistence row for a biofertilizer calibration record.

    The historical ``database/models.py`` declaration carried only
    ``id``, ``user_id``, ``created_at`` and a ``user`` relationship.
    ``engine/hydroma/biofertilizer/calibration.py`` is written against
    a richer schema (``formulation_id``, ``calibration_date``,
    ``model_version``, ``parameters_updated``, ``calibration_quality_score``);
    the live table is the biofertilizer ``NojinCalibrationRecord``
    (``nojin_calibration_records``). This legacy model keeps a
    distinct table name so both register on the shared registry
    without colliding. The schema mismatch is a separate, pre-existing
    defect pinned by ``test_calibration_record_schema_does_not_match_calibration_module``.
    """

    __tablename__ = "nojin_calibration_record_db"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Service-layer ORM models
#
# The services layer (auth, carbon MRV ledger, finance
# wallet/ledger/payments, commerce idempotency middleware) imports
# these declarations from ``database.models``. They were never
# committed to the repository, so every ``from database.models import
# User`` (and the carbon / finance / commerce models) failed at
# collection time. Each schema below is reconstructed from the
# columns the corresponding service actually reads and writes.
# --------------------------------------------------------------------------- #


class User(Base):
    """Platform user account (JWT subject and village-governance actor)."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="farmer")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    two_factor_method = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    language = Column(String(10), nullable=True, default="en")
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    # SEC-02: per-account brute-force lockout (the per-IP AuthRateLimitMiddleware
    # cannot stop credential stuffing spread across IPs against one account).
    failed_login_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)


class CarbonCreditState(StrEnum):
    """Lifecycle states of a carbon credit (mirrors ``CreditState``)."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class CarbonProject(Base):
    """Agroforestry carbon project under the MRV lifecycle.

    The column set is the union of what every reader and writer actually
    touches: ``services/carbon/repository.py`` creates rows with
    ``credits_issued``/``registered_at`` and orders by ``registered_at``,
    ``carbon/service.py`` filters on ``credits_issued`` via
    ``estimate_soil_parameters``'s sibling paths, and
    ``engine/hydroma/carbon/calculator.py`` reads back ``annual_rate_tonnes``
    and ``methodology`` when it hydrates a project from the repository.
    """

    __tablename__ = "carbon_projects"

    project_id = Column(String(64), primary_key=True)
    name = Column(String(200), nullable=False)
    user_id = Column(String(36), nullable=True, index=True)
    project_type = Column(String(80), default="afforestation")
    methodology = Column(String(120), default="vm0032")
    standard = Column(String(120), nullable=True)
    region = Column(String(80), nullable=True)
    duration_years = Column(Integer, nullable=True)
    verification_status = Column(String(30), default="unverified")
    field_verified = Column(Boolean, default=False)
    mrv_documents = Column(JSON, nullable=True)
    status = Column(String(30), default="DRAFT")
    verification_detail = Column(JSON, nullable=True)
    area_hectares = Column(Numeric(14, 2), nullable=True)
    estimated_carbon_tonnes = Column(Float, nullable=True)
    annual_rate_tonnes = Column(Float, nullable=True)
    credits_issued = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    registered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class CarbonCredit(Base):
    """A single issued carbon credit with its retirement accounting."""

    __tablename__ = "carbon_credits"

    credit_id = Column(String(64), primary_key=True)
    project_id = Column(String(64), nullable=False, index=True)
    serial = Column(String(64), nullable=True)
    vintage_year = Column(Integer, nullable=True)
    methodology = Column(String(120), nullable=True)
    standard = Column(String(120), nullable=True)
    data_mode = Column(String(30), nullable=True)
    mrv_documents = Column(JSON, nullable=True)
    total_amount = Column(Numeric(18, 8), nullable=False)
    retired_amount = Column(Numeric(18, 8), default=Decimal("0"))
    available_amount = Column(Numeric(18, 8), nullable=False)
    holder_id = Column(String(36), nullable=False, index=True)
    # mypy: ``Enum(...)`` takes ``*enums`` so its type parameter cannot be
    # inferred and mypy reports var-annotated; spelling the mapped type out is
    # a typing-only change and leaves the emitted DDL untouched.
    state: Column[CarbonCreditState] = Column(
        Enum(CarbonCreditState), nullable=False, default=CarbonCreditState.ACTIVE
    )
    issued_by = Column(String(120), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    frozen = Column(Boolean, default=False)
    frozen_by = Column(String(120), nullable=True)
    frozen_authority = Column(String(120), nullable=True)
    frozen_reason = Column(String(500), nullable=True)
    frozen_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=0)


class CarbonEvent(Base):
    """Append-only event sourced from the carbon MRV lifecycle."""

    __tablename__ = "carbon_events"

    event_id = Column(String(64), primary_key=True)
    aggregate_type = Column(String(30), nullable=True)
    aggregate_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=True)
    actor = Column(String(120), nullable=True)
    authority = Column(String(120), nullable=True)
    reason = Column(JSON, nullable=True)
    correlation_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CreditAuditLog(Base):
    """Immutable audit trail for carbon credit state transitions."""

    __tablename__ = "credit_audit_logs"

    event_id = Column(String(64), nullable=True)
    audit_id = Column(String(64), primary_key=True)
    credit_id = Column(String(64), nullable=False, index=True)
    project_id = Column(String(64), nullable=True)
    action = Column(String(64), nullable=True)
    actor = Column(String(120), nullable=True)
    authority = Column(String(120), nullable=True)
    reason = Column(String(500), nullable=True)
    before_state = Column(String(30), nullable=True)
    after_state = Column(String(30), nullable=True)
    delta_amount = Column(Numeric(18, 8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class IdempotencyKey(Base):
    """Generic idempotency record keyed by (key, action)."""

    __tablename__ = "idempotency_keys"

    key = Column(String(128), primary_key=True)
    action = Column(String(64), nullable=False)
    result_reference = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class FinAccount(Base):
    """Chart-of-accounts entry for the double-entry finance ledger."""

    __tablename__ = "fin_accounts"

    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(30), nullable=False)
    asset = Column(String(10), nullable=False)
    currency = Column(String(10), nullable=True)
    # ``parent_id`` is the parent row's Integer primary key held as text. There
    # is deliberately no ``ForeignKey`` here: the referenced key ``FinAccount.id``
    # is an Integer, and a foreign key between incompatible key types is
    # rejected by PostgreSQL DDL, so the hierarchy is a business key rather than
    # a referential one. ``chart_of_accounts.ensure_account`` is the only writer
    # and it always resolves ``parent_code`` to a real row id.
    parent_id = Column(String(64), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())


class FinJournalBatch(Base):
    """A posted (or draft) batch of journal entries."""

    __tablename__ = "fin_journal_batches"

    id = Column(Integer, primary_key=True)
    batch_number = Column(String(64), nullable=False)
    batch_date = Column(Date, nullable=False)
    reference_type = Column(String(64), nullable=True)
    reference_id = Column(String(64), nullable=True)
    description = Column(String(500), nullable=True)
    created_by = Column(String(36), nullable=True)
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class FinJournalEntry(Base):
    """A single debit/credit line within a journal batch."""

    __tablename__ = "fin_journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("fin_journal_batches.id"), nullable=False)
    account_id = Column(String(64), nullable=False, index=True)
    entry_type = Column(String(10), nullable=False)
    asset = Column(String(10), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class FinIdempotencyKey(Base):
    """Commerce idempotency record, unique on (user_id, key)."""

    __tablename__ = "fin_idempotency_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_fin_idempotency_user_key"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(120), nullable=False, index=True)
    key = Column(String(128), nullable=False)
    route = Column(String(255), nullable=True)
    request_hash = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    response_code = Column(Integer, nullable=True)
    response_body = Column(JSON, nullable=True)


class EcoWallet(Base):
    """ECO token wallet for a platform user."""

    __tablename__ = "eco_wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(120), nullable=False, unique=True, index=True)
    balance = Column(Numeric(18, 8), default=Decimal("0"))
    total_earned = Column(Numeric(18, 8), default=Decimal("0"))
    total_redeemed = Column(Numeric(18, 8), default=Decimal("0"))
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class DailyEarnings(Base):
    """Daily ECO earnings ledger for the wallet daily-cap check."""

    __tablename__ = "daily_earnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(120), nullable=False, index=True)
    date = Column(Date, nullable=False)
    earnings_type = Column(String(64), nullable=True)
    amount = Column(Numeric(18, 8), nullable=False)
    source = Column(String(120), nullable=True)
    status = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    processed_at = Column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    """Immutable audit event for payment and admin actions."""

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(64), nullable=True)
    actor_id = Column(String(120), nullable=True)
    action = Column(String(120), nullable=False)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ComPaymentIntent(Base):
    """Commerce payment intent persisted by the payment providers."""

    __tablename__ = "com_payment_intents"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    buyer_id = Column(String(120), nullable=True)
    provider = Column(String(64), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(32), nullable=False)
    provider_reference = Column(String(120), nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)


# --------------------------------------------------------------------------- #
# Commerce (orders, items, settlements) and Inventory (WMS) ORM models
#
# ``services.commerce.service`` and ``services.inventory.service`` import
# these declarations from ``database.models``. They were never committed
# to the repository, so every import failed at collection time. Each
# schema below is reconstructed from the columns the corresponding
# service actually reads and writes, and the raw SQL the services issue
# (``inv_stock_movements``, ``inv_inventory_balances``,
# ``inv_stocktake_lines``, ``inv_reservations``).
# --------------------------------------------------------------------------- #


#: Order lifecycle transition table. Each state maps to the set of
#: states it may advance to and the requirements a target transition
#: imposes (checked by ``OrderStateMachine.validate``). Terminal states
#: (``settled``, ``cancelled``, ``refunded``) allow no further targets.
ORDER_STATE_MACHINE: dict[str, dict[str, object]] = {
    "draft": {"allowed": {"reserved", "cancelled"}, "requires": {}},
    "reserved": {
        "allowed": {"paid", "cancelled"},
        "requires": {"paid": ["payment"]},
    },
    "paid": {"allowed": {"processing", "cancelled"}, "requires": {}},
    "processing": {
        "allowed": {"shipped", "cancelled"},
        "requires": {"shipped": ["tracking_code"]},
    },
    "shipped": {"allowed": {"delivered", "cancelled"}, "requires": {}},
    "delivered": {"allowed": {"settled", "cancelled"}, "requires": {}},
    "settled": {"allowed": set(), "requires": {}},
    "cancelled": {"allowed": set(), "requires": {}},
    "refunded": {"allowed": set(), "requires": {}},
}


class ComOrder(Base):
    """A marketplace order through the DRAFT→…→SETTLED lifecycle."""

    __tablename__ = "com_orders"
    __table_args__ = (
        # P4 / KN-03: the runtime lookup in ``commerce/service.py`` is already
        # buyer-scoped; this backstop makes the database enforce it, so two
        # requests that reuse one key under the *same* buyer collide instead
        # of creating a duplicate order. NULL keys (no idempotency supplied)
        # stay legal: SQL unique constraints treat NULLs as distinct.
        UniqueConstraint("buyer_id", "idempotency_key", name="uq_com_orders_buyer_idem"),
    )

    id = Column(String(64), primary_key=True)
    order_number = Column(String(64), unique=True, index=True)
    buyer_id = Column(String(120), nullable=False, index=True)
    seller_id = Column(String(120), nullable=True)
    status = Column(String(32), nullable=False, default="draft")
    payment_status = Column(String(32), nullable=False, default="pending")
    currency = Column(String(10), nullable=False, default="IRR")
    subtotal = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    platform_fee = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    landscape_fee = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    total = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    shipping_address = Column(JSON, nullable=True)
    idempotency_key = Column(String(128), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=0)
    tracking_code = Column(String(64), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ComOrderItem(Base):
    """A single line item of a :class:`ComOrder`."""

    __tablename__ = "com_order_items"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), ForeignKey("com_orders.id"), nullable=False, index=True)
    sku_id = Column(Integer, nullable=False)
    sku_code = Column(String(64), nullable=False)
    name = Column(String(200), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)
    unit_price = Column(Numeric(18, 8), nullable=False)
    line_total = Column(Numeric(18, 8), nullable=False)
    warehouse_id = Column(Integer, nullable=False)
    reservation_id = Column(Integer, nullable=True)
    fulfilled_qty = Column(
        Numeric(18, 8), nullable=False, default=Decimal("0"), server_default="0"
    )


class ComSettlement(Base):
    """Settlement of a delivered order: escrow release to the seller."""

    __tablename__ = "com_settlements"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), ForeignKey("com_orders.id"), nullable=False, index=True)
    seller_id = Column(String(120), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    currency = Column(String(10), nullable=False)
    commission_fee = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    landscape_fee = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    status = Column(String(32), nullable=False, default="pending")
    journal_batch_id = Column(
        Integer, ForeignKey("fin_journal_batches.id"), nullable=True
    )
    settled_at = Column(DateTime(timezone=True), nullable=True)


class InvSKU(Base):
    """A stock-keeping unit: the item identity every movement refers to."""

    __tablename__ = "inv_skus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    uom = Column(String(32), nullable=False, default="kg")
    category_id = Column(Integer, nullable=True)
    standard_cost = Column(Numeric(18, 8), nullable=True)
    default_warehouse_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    is_trackable = Column(Boolean, nullable=False, default=True, server_default=true())
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvWarehouse(Base):
    """A physical warehouse."""

    __tablename__ = "inv_warehouses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvLocation(Base):
    """A pickable/receivable location inside a warehouse."""

    __tablename__ = "inv_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(
        Integer, ForeignKey("inv_warehouses.id"), nullable=False, index=True
    )
    code = Column(String(64), nullable=False)
    location_type = Column(String(32), nullable=False, default="bin")
    is_active = Column(Boolean, nullable=False, default=True)
    is_pickable = Column(Boolean, nullable=False, default=True)
    is_receivable = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvLot(Base):
    """A physical lot/batch of one SKU, carrying the expiry FEFO picks on.

    Real lot/batch traceability the legacy Integer ``lot_id`` sentinel never
    had: one row per received batch, its ``expiry_date``, the ``unit_cost``
    the batch was received at and the running ``qty_remaining`` an FEFO
    issue decrements to zero. The three rows that can point at a lot —
    :class:`InvInventoryBalance`, :class:`InvStockMovement` and
    :class:`InvReservation` — carry the reference in their nullable
    ``lot_uuid`` column, whose NULL default means "not lot-tracked" and
    keeps the legacy
    ``(sku_id, warehouse_id, location_id, lot_id)`` sentinel path, its
    unique constraint and its moving-average valuation byte-identical.

    ``id`` is a String(36) uuid — the entity is addressed through
    ``lot_uuid``, never by an integer surrogate — and ``sku_id`` is the
    String(36) shape the uuid-addressed plane uses, holding the SKU's id as
    text so the lot table stays backfill-safe and needs no second integer
    key; :class:`InvInventoryBalance` keeps its own Integer ``sku_id``
    foreign key as the quantity authority.
    """

    __tablename__ = "inv_lots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku_id = Column(String(36), nullable=False, index=True)
    lot_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(Date, nullable=True)
    received_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    unit_cost = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    qty_received = Column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    qty_remaining = Column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    supplier_ref = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (Index("ix_inv_lots_sku_expiry", "sku_id", "expiry_date"),)


class InvInventoryBalance(Base):
    """On-hand/reserved/blocked quantities of one SKU at one place.

    ``location_id``/``lot_id`` default to ``0`` (the service's sentinel
    for "not location- or lot-specific"), so the balance a movement
    touches is always findable by the (sku, warehouse, location, lot)
    key the service queries on. The unique constraint on exactly that
    key is what makes the key a key: without it, concurrent first
    touches of the same balance (the service's ``get_or_create_balance``)
    could each insert a row and split one logical balance in two. The 0
    sentinels are NOT NULL with a server default of 0, so a plain
    unique constraint (rather than a COALESCE expression index) holds
    under the current semantics and is created by
    ``Base.metadata.create_all``. ``lot_uuid`` is the additive
    lot-tracking seam beside that legacy key: NULL means "not
    lot-tracked" and the row keeps the moving-average valuation path,
    a uuid means the row's quantity is backed by an :class:`InvLot` and
    FEFO issue/consume draws from it. It is deliberately NOT part of
    the unique constraint, so adding it cannot fork a balance row.
    """

    __tablename__ = "inv_inventory_balances"
    __table_args__ = (
        UniqueConstraint(
            "sku_id",
            "warehouse_id",
            "location_id",
            "lot_id",
            name="uq_inv_balance_sku_wh_loc_lot",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(Integer, ForeignKey("inv_skus.id"), nullable=False, index=True)
    warehouse_id = Column(
        Integer, ForeignKey("inv_warehouses.id"), nullable=False, index=True
    )
    location_id = Column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    lot_id = Column(Integer, nullable=False, default=0, server_default=text("0"))
    lot_uuid = Column(String(36), ForeignKey("inv_lots.id"), nullable=True)
    on_hand = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    reserved = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    blocked = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    in_transit = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    last_movement_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def available(self) -> Decimal:
        """Quantity free to reserve or issue: on-hand minus reserved.

        ``blocked`` is deliberately NOT subtracted. ``scrap`` removes the
        written-off quantity from ``on_hand`` *and* adds it to the
        ``blocked`` pool, so ``blocked`` is a write-off ledger outside
        ``on_hand`` — subtracting it here would double-count the scrap
        reduction. A blocked quantity returns to usable stock through
        ``StockService.unblock_stock``, which restores ``on_hand`` and
        decrements ``blocked`` symmetrically.

        ``reserved`` only counts unexpired reservations once
        ``sweep_expired_reservations`` has run for this (sku, warehouse)
        pair (the reservation sweeper runs lazily at the start of
        ``reserve_stock``, the only path where availability gates a
        write).
        """
        # mypy: ``Numeric`` subclasses ``decimal.Decimal`` *and* SQLAlchemy's
        # ``ColumnOperators``, so mypy picks the operator overload and reports
        # ColumnElement[Decimal]. Both operands are Decimals at runtime, hence
        # the cast; the arithmetic is unchanged.
        return cast("Decimal", self.on_hand - self.reserved)


class InvStockMovement(Base):
    """An immutable, append-only stock movement record."""

    __tablename__ = "inv_stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movement_type = Column(String(32), nullable=False)
    sku_id = Column(Integer, nullable=False, index=True)
    warehouse_id = Column(Integer, nullable=False)
    from_location_id = Column(Integer, nullable=True)
    to_location_id = Column(Integer, nullable=True)
    lot_id = Column(Integer, nullable=True)
    lot_uuid = Column(String(36), ForeignKey("inv_lots.id"), nullable=True)
    qty = Column(Numeric(18, 8), nullable=False)
    signed_qty = Column(Numeric(18, 8), nullable=True)
    unit_cost = Column(Numeric(18, 8), nullable=True)
    total_cost = Column(Numeric(18, 8), nullable=True)
    reference_type = Column(String(64), nullable=True)
    reference_id = Column(String(128), nullable=True)
    from_warehouse_id = Column(Integer, nullable=True)
    to_warehouse_id = Column(Integer, nullable=True)
    notes = Column(String(1000), nullable=True)
    created_by = Column(String(120), nullable=False)
    user_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvReservation(Base):
    """An atomic stock reservation with consumption tracking."""

    __tablename__ = "inv_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(Integer, nullable=False, index=True)
    warehouse_id = Column(Integer, nullable=False)
    location_id = Column(Integer, nullable=True)
    lot_id = Column(Integer, nullable=True)
    lot_uuid = Column(String(36), ForeignKey("inv_lots.id"), nullable=True)
    qty = Column(Numeric(18, 8), nullable=False)
    consumed_qty = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    status = Column(String(32), nullable=False, default="active")
    reference_type = Column(String(64), nullable=False)
    reference_id = Column(String(128), nullable=False)
    reference_line_id = Column(String(128), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InvStocktake(Base):
    """A physical stock count against system quantities."""

    __tablename__ = "inv_stocktakes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stocktake_number = Column(String(64), unique=True, nullable=False)
    warehouse_id = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="draft")
    stocktake_type = Column(String(32), nullable=False, default="full")
    created_by = Column(String(120), nullable=False)
    approved_by = Column(String(120), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)


class InvStocktakeLine(Base):
    """One counted SKU within a :class:`InvStocktake`."""

    __tablename__ = "inv_stocktake_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stocktake_id = Column(
        Integer, ForeignKey("inv_stocktakes.id"), nullable=False, index=True
    )
    sku_id = Column(Integer, nullable=False)
    warehouse_id = Column(Integer, nullable=False)
    location_id = Column(Integer, nullable=True)
    lot_id = Column(Integer, nullable=True)
    system_qty = Column(Numeric(18, 8), nullable=False)
    counted_qty = Column(Numeric(18, 8), nullable=False)
    variance_qty = Column(Numeric(18, 8), nullable=False)
    variance_value = Column(Numeric(18, 8), nullable=True)
    counted_by = Column(String(120), nullable=False)
    counted_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(32), nullable=False, default="pending")


# --------------------------------------------------------------------------- #
# Gateway / admin content plane
#
# ``services.api_gateway.content_repository``, ``routers.admin_content`` and
# ``admin.repository_overview`` import these declarations. Schema is
# reconstructed from the columns the repository reads and writes.
# --------------------------------------------------------------------------- #


class ContentItem(Base):
    """One content item in the admin content plane."""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False, index=True)
    body = Column(Text, nullable=False, default="")
    category = Column(String(80), nullable=False, default="general")
    status = Column(String(32), nullable=False, default="draft", index=True)
    language = Column(String(10), nullable=False, default="fa", index=True)
    access_level = Column(String(32), nullable=False, default="public")
    created_at = Column(String(64), nullable=True)
    updated_at = Column(String(64), nullable=True)
    published_at = Column(String(64), nullable=True)
    #: Whether the item has been handed to the RAG index. The content module
    #: (``services/content/rag_sync.py``) and the publish path
    #: (``services/content/bot_dispatch.py``) both set it, but the column was
    #: never added to the model, so every call raised ``AttributeError``.
    #: The public keyword search does not depend on it -- it filters on
    #: ``status`` -- so the search worked while the sync did not.
    #:
    #: No index: the column was added to existing tables by migration, and an
    #: ``index=True`` here makes ``create_all`` emit a CREATE INDEX for a
    #: column a pre-existing table does not have, which fails outright.
    rag_synced = Column(Boolean, nullable=False, default=False)


class ContentVersion(Base):
    """An immutable version of a :class:`ContentItem`."""

    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(
        Integer, ForeignKey("content_items.id"), nullable=False, index=True
    )
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(300), nullable=True)
    body = Column(Text, nullable=True)
    created_at = Column(String(64), nullable=True)


class ContentTranslation(Base):
    """A locale translation of a :class:`ContentItem`."""

    __tablename__ = "content_translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(
        Integer, ForeignKey("content_items.id"), nullable=False, index=True
    )
    locale = Column(String(10), nullable=False)
    title = Column(String(300), nullable=True)
    body = Column(Text, nullable=True)
    source = Column(String(32), nullable=True, default="ai")
    is_published = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("content_id", "locale", name="uq_content_translation_locale"),
    )


# --------------------------------------------------------------------------- #
# Farms, marketplace products, satellite / soil / chat analysis
#
# ``routers.farms``, ``routers.analytics``, ``routers.ai_chat``,
# ``routers.soil`` and ``admin.repository_overview`` import these.
# --------------------------------------------------------------------------- #


class Farm(Base):
    """A physical farm parcel owned by a platform user."""

    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(36), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation_m = Column(Float, nullable=True)
    area_hectares = Column(Float, nullable=True)
    soil_type = Column(String(50), nullable=True)
    climate_zone = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Product(Base):
    """A product listed in the marketplace."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    category = Column(String(80), nullable=True, index=True)
    description = Column(Text, nullable=True)
    producer_id = Column(String(120), nullable=True, index=True)
    producer_name = Column(String(200), nullable=True)
    origin_location = Column(String(200), nullable=True)
    price_per_kg = Column(Numeric(14, 2), default=Decimal("0"))
    quantity_available_kg = Column(Numeric(14, 2), default=Decimal("0"))
    minimum_order_kg = Column(Numeric(10, 2), default=Decimal("1"))
    organic_certified = Column(Boolean, default=False)
    carbon_footprint_kg_co2 = Column(Float, nullable=True)
    water_footprint_liters = Column(Float, nullable=True)
    batch_number = Column(String(120), nullable=True)
    traceability_code = Column(String(120), nullable=True, index=True)
    images = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class SoilAnalysis(Base):
    """A persisted soil analysis for one farm."""

    __tablename__ = "soil_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farm_id = Column(Integer, nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    ph = Column(Float, nullable=True)
    organic_matter = Column(Float, nullable=True)
    nitrogen = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium = Column(Float, nullable=True)
    clay = Column(Float, nullable=True)
    silt = Column(Float, nullable=True)
    sand = Column(Float, nullable=True)
    texture = Column(String(50), nullable=True)
    ph_status = Column(String(32), nullable=True)
    organic_matter_rating = Column(String(32), nullable=True)
    health_score = Column(Float, nullable=True)
    recommendations = Column(JSON, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class SatelliteAnalysis(Base):
    """A persisted satellite-index analysis for one farm."""

    __tablename__ = "satellite_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farm_id = Column(Integer, nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    ndvi = Column(Float, nullable=True)
    ndwi = Column(Float, nullable=True)
    cloud_cover = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=True)
    metadata_ = Column(JSON, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AIConversation(Base):
    """A persisted AI-chat question and answer pair."""

    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True, index=True)
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    sources = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    asked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Public website plane (contact, newsletter, pilot)
#
# ``routers.contact``, ``routers.newsletter`` and ``routers.pilot`` import
# these. Data minimization per the published privacy policy: only the
# submitted fields plus a locale tag are stored.
# --------------------------------------------------------------------------- #


class ContactMessage(Base):
    """A public contact-form submission."""

    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    role = Column(String(80), nullable=True)
    message = Column(Text, nullable=False)
    locale = Column(String(8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class NewsletterSubscriber(Base):
    """A newsletter subscription, unique per email."""

    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), nullable=False, unique=True, index=True)
    locale = Column(String(8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class PilotApplication(Base):
    """A pilot-interest application from the public website."""

    __tablename__ = "pilot_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    province = Column(String(80), nullable=False, index=True)
    land_hectares = Column(Float, nullable=True)
    main_crop = Column(String(120), nullable=True)
    preferred_channel = Column(String(40), nullable=True)
    consent = Column(Boolean, nullable=False, default=False)
    locale = Column(String(8), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Tool registry, legal texts, MRV observations
#
# ``routers.tool_registry``, ``services.legal.*`` and
# ``business_modules.iot.device_manager`` import these.
# --------------------------------------------------------------------------- #


class ToolRegistryEntry(Base):
    """One entry in the 62-tool algorithm/model registry."""

    __tablename__ = "tool_registry_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(String(32), nullable=False, unique=True, index=True)
    name_fa = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    domain = Column(String(50), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    fidelity = Column(String(20), nullable=True)
    reference = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    service_slug = Column(String(100), nullable=True)
    endpoint_path = Column(String(200), nullable=True)
    phase = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)


class LegalText(Base):
    """A versioned legal text (terms, privacy, marketplace rules)."""

    __tablename__ = "legal_texts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locale = Column(String(10), nullable=False, index=True)
    slug = Column(String(80), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="draft")
    effective_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("locale", "slug", "version", name="uq_legal_text_version"),
    )


class MRVObservation(Base):
    """One IoT/sensor observation under MRV quality control."""

    __tablename__ = "mrv_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(64), nullable=True, index=True)
    sensor_id = Column(String(64), nullable=True, index=True)
    sensor_type = Column(String(80), nullable=True)
    value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    qa_status = Column(String(32), nullable=True)
    qa_message = Column(Text, nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=True)
    data_source = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class IoTDevice(Base):
    """A provisioned IoT device in the monitoring fleet."""

    __tablename__ = "iot_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_name = Column(String(200), nullable=False)
    device_type = Column(String(32), nullable=False, default="sensor")
    sensor_types = Column(JSON, nullable=True)
    location = Column(JSON, nullable=True)
    platform_id = Column(String(120), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="provisioning")
    qr_code = Column(String(64), nullable=True, index=True)
    user_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)


class MonitoringDataDB(Base):
    """A field or mobile monitoring report persisted for a project."""

    __tablename__ = "monitoring_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(64), nullable=True, index=True)
    monitoring_type = Column(String(32), nullable=True)
    monitoring_date = Column(Date, nullable=True)
    location = Column(String(200), nullable=True)
    data_source = Column(String(200), nullable=True)
    data_quality_score = Column(Float, nullable=True)
    measurement_data = Column(JSON, nullable=True)
    quality_flags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Auth, settings and audit trail
#
# ``services.auth_legacy.*``, ``routers.auth`` and ``routers.admin_security``
# import these. Every column is one the repository reads or writes.
# --------------------------------------------------------------------------- #


class RefreshToken(Base):
    """A single refresh-token session (row per issued refresh token)."""

    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    jti = Column(String(128), nullable=False, unique=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    revoked = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class PasswordResetToken(Base):
    """A single-use password-reset (or email-change) token."""

    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    @property
    def is_valid(self) -> bool:
        """True when the token is unused and not yet expired."""
        from datetime import UTC as _UTC
        from datetime import datetime as _datetime

        if self.used:
            return False
        expires = self.expires_at
        if expires is None:
            return False
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=_UTC)
        # mypy: ``DateTime`` also carries ``ColumnOperators``, so mypy types the
        # comparison as ColumnElement[bool]; it is a real bool at runtime, and
        # ``bool()`` of a bool is that same bool.
        return bool(expires >= _datetime.now(_UTC))

    @classmethod
    def create_for_user(cls, user_id: str, hours_valid: int = 1) -> "PasswordResetToken":
        """Build a fresh, unused token for ``user_id``."""
        import secrets
        from datetime import UTC as _UTC
        from datetime import datetime as _datetime
        from datetime import timedelta as _timedelta

        return cls(
            token=secrets.token_urlsafe(48),
            user_id=user_id,
            expires_at=_datetime.now(_UTC) + _timedelta(hours=hours_valid),
            used=False,
        )


class AuditLog(Base):
    """An immutable audit-log row for auth and admin actions."""

    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(120), nullable=True, index=True)
    action = Column(String(120), nullable=True, index=True)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    ip_address = Column(String(80), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Setting(Base):
    """A key/value platform setting or user preference."""

    __tablename__ = "settings"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(200), nullable=False, index=True)
    value = Column(Text, nullable=True)
    category = Column(String(80), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class LoginHistory(Base):
    """One login attempt, successful or not."""

    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    ip_address = Column(String(80), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    failure_reason = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class OAuthConnection(Base):
    """An OAuth identity linked to a platform user."""

    __tablename__ = "oauth_connections"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    access_token_encrypted = Column(Text, nullable=True)
    connected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),
    )


class ApiKey(Base):
    """A hashed API key issued to a user."""

    __tablename__ = "api_keys"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Organizations
#
# ``services.organization.*`` imports these. The service creates the org and
# its first membership in one call; ``list_user_orgs`` joins them.
# --------------------------------------------------------------------------- #


class Organization(Base):
    """A multi-user organization."""

    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    country = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class OrganizationMembership(Base):
    """One user's membership in one :class:`Organization`."""

    __tablename__ = "organization_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=False, index=True)
    role = Column(String(32), nullable=False, default="member")
    status = Column(String(32), nullable=False, default="active")
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="uq_org_membership_user"
        ),
    )


# --------------------------------------------------------------------------- #
# Simulation, scenarios, hub runs and workflow runs
#
# ``routers.simulation``, ``routers.scenarios``, ``routers.hydroma_hub`` and
# ``services.workflow.service`` import these.
# --------------------------------------------------------------------------- #


class SimulationRun(Base):
    """One executed simulation chain (RUSLE → AquaCrop → RothC)."""

    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(64), nullable=True, index=True)
    scenario = Column(String(80), nullable=True)
    area_ha = Column(Float, nullable=True)
    status = Column(String(32), nullable=True)
    outputs = Column(JSON, nullable=True)
    message = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ScenarioRun(Base):
    """One applied IPCC SSP climate scenario."""

    __tablename__ = "scenario_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farm_id = Column(Integer, nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    baseline_temp = Column(Float, nullable=True)
    baseline_precip = Column(Float, nullable=True)
    scenario = Column(String(32), nullable=True, index=True)
    target_year = Column(Integer, nullable=True)
    projected_temp = Column(Float, nullable=True)
    projected_precip = Column(Float, nullable=True)
    temp_change = Column(Float, nullable=True)
    precip_change_percent = Column(Float, nullable=True)
    drought_risk_index = Column(Float, nullable=True)
    impact_assessment = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    run_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ModelRun(Base):
    """A dashboard calculator result stored in the central hub."""

    __tablename__ = "model_runs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_key = Column(String(64), nullable=False, index=True)
    model_id = Column(String(80), nullable=False)
    title = Column(String(160), nullable=True)
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    shared = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WorkflowStatus(StrEnum):
    """Lifecycle states of a workflow run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SUCCESS = "success"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class WorkflowRun(Base):
    """One persisted multi-stage agricultural workflow."""

    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), nullable=False, index=True)
    farmer_id = Column(String(64), nullable=True, index=True)
    field_id = Column(String(64), nullable=True)
    crop_type = Column(String(80), nullable=True)
    status = Column(String(32), nullable=True)
    stages = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


# --------------------------------------------------------------------------- #
# Integration outbox
#
# ``services.integration.outbox`` and ``outbox_worker`` import these.
# --------------------------------------------------------------------------- #


class IntOutboxEvent(Base):
    """One event in the transactional outbox awaiting NATS dispatch."""

    __tablename__ = "int_outbox_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(120), nullable=False)
    aggregate_type = Column(String(64), nullable=True)
    aggregate_id = Column(String(64), nullable=True, index=True)
    payload = Column(JSON, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    supabase_synced = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Notifications
#
# ``services.notification.main`` imports this. Multi-channel delivery
# (email / sms / in_app / telegram) is recorded per row.
# --------------------------------------------------------------------------- #


class Notification(Base):
    """One outbound notification on one channel."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(120), nullable=False, index=True)
    channel = Column(String(32), nullable=False, default="in_app")
    subject = Column(String(300), nullable=True)
    message = Column(Text, nullable=False)
    metadata_ = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class EcoTransaction(Base):
    """One ECO wallet transaction (append-only wallet ledger row)."""

    __tablename__ = "eco_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(String(120), nullable=True, index=True)
    user_id = Column(String(120), nullable=True, index=True)
    amount = Column(Numeric(18, 8), nullable=False, default=Decimal("0"))
    transaction_type = Column(String(32), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    category = Column(String(80), nullable=True)
    balance_after = Column(Numeric(18, 8), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Ledger and escrow
#
# ``services.ledger.service`` imports these. The escrow state machine is
# created → locked → released | reversed; the two exit states are terminal.
# --------------------------------------------------------------------------- #


class LedgerEntry(Base):
    """One single-entry ledger posting (credit positive, debit negative)."""

    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(120), nullable=False, index=True)
    entry_type = Column(String(10), nullable=False)
    asset = Column(String(16), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    reference_type = Column(String(64), nullable=True)
    reference_id = Column(String(64), nullable=True)
    description = Column(String(500), nullable=True)
    #: P5 / D-10: the shared attribution key across the money ledgers. NULL for
    #: historical rows — the money contract's compensation rule forbids editing
    #: them retroactively; new postings carry it so per-user attribution (and
    #: ``services/finance/cross_ledger_report.py``) works on every database.
    user_id = Column(String(120), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


#: Escrow states that allow no further target transition, as their *values*.
#: Module-level, and expressed as the enum's own ``value`` strings rather than
#: as ``EscrowState.RELEASED.value``, so it can be declared BEFORE the enum and
#: stay in sync with it without a forward reference.
_ESCROW_TERMINAL = frozenset({"released", "reversed"})


class EscrowState(StrEnum):
    """Lifecycle states of an escrow record."""

    CREATED = "created"
    LOCKED = "locked"
    RELEASED = "released"
    REVERSED = "reversed"

    def can_transition_to(self, target: "EscrowState") -> bool:
        """Whether ``self`` may advance to ``target``."""
        if self.value in _ESCROW_TERMINAL:
            return False
        if target is EscrowState.CREATED:
            return self is EscrowState.CREATED
        return {
            EscrowState.CREATED: {EscrowState.LOCKED},
            EscrowState.LOCKED: {EscrowState.RELEASED, EscrowState.REVERSED},
        }.get(self, set()).__contains__(target)


class EscrowRecord(Base):
    """Funds held for an order across the escrow lifecycle."""

    __tablename__ = "escrow_records"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(64), nullable=False, index=True)
    payment_id = Column(String(64), nullable=True)
    buyer_id = Column(String(120), nullable=True)
    seller_id = Column(String(120), nullable=True)
    amount = Column(Numeric(18, 8), nullable=False)
    asset = Column(String(16), nullable=False, default="IRR")
    state = Column(String(32), nullable=False, default=EscrowState.CREATED.value)
    dispute_window_deadline = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=True)


# --------------------------------------------------------------------------- #
# Eco-balance and carbon credits
#
# ``services.wallet.eco_balance`` and ``services.wallet.credits`` import
# these. Both are DB-constrained by design: replay protection is a unique
# constraint, not a code path.
# --------------------------------------------------------------------------- #


class EcoBalanceAccount(Base):
    """The non-transferable EcoBalance of one user."""

    __tablename__ = "eco_balance_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(120), nullable=False, index=True)
    balance = Column(Numeric(18, 6), default=Decimal("0"))
    lifetime_earned = Column(Numeric(18, 6), default=Decimal("0"))
    observation_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_activity = Column(DateTime(timezone=True), nullable=True)


class EcoBalanceEntry(Base):
    """One append-only EcoBalance credit. Retired, never deleted."""

    __tablename__ = "eco_balance_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(120), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    amount = Column(Numeric(18, 6), nullable=False)
    reason = Column(String(64), nullable=False)
    observation_id = Column(String(128), nullable=False)
    evidence_digest = Column(String(64), nullable=False)
    retired_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint(
            "user_id", "observation_id", name="uq_eco_balance_observation"
        ),
    )


class CarbonCreditRecord(Base):
    """One issued carbon credit; its class follows its evidence."""

    __tablename__ = "carbon_credit_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    holder_id = Column(String(120), nullable=False, index=True)
    project_ref = Column(String(128), nullable=False, index=True)
    tonnes_co2e = Column(Numeric(18, 8), nullable=False)
    serial_number = Column(String(128), nullable=True)
    credit_class = Column(String(32), nullable=False)
    standard_code = Column(String(64), nullable=True)
    attestation_ref = Column(String(300), nullable=True)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    state = Column(
        Enum(CarbonCreditState), nullable=False, default=CarbonCreditState.ACTIVE
    )


class CarbonRetirement(Base):
    """One retirement of a carbon credit. Double retirement is impossible."""

    __tablename__ = "carbon_retirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    credit_id = Column(
        Integer, ForeignKey("carbon_credit_records.id"), nullable=False, index=True
    )
    sequence = Column(Integer, nullable=False)
    retired_by = Column(String(120), nullable=False)
    payload_digest = Column(String(64), nullable=False)
    chain_tx_hash = Column(String(128), nullable=True)
    retired_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        # The guarantee that a credit can only ever be retired once. The
        # service also refuses a second retirement, but this constraint is
        # what makes the guarantee hold if the service check is ever removed
        # or bypassed. Without it the same tonne could be retired twice and
        # counted twice.
        UniqueConstraint("credit_id", name="uq_carbon_retirement_credit"),
    )


# --------------------------------------------------------------------------- #
# Oracle challenge plane
#
# ``services.oracle.router`` imports these. An impact report opens a
# challenge window; a challenge is resolved to upheld / rejected.
# --------------------------------------------------------------------------- #


class OracleImpactReport(Base):
    """A submitted impact report with an open challenge window."""

    __tablename__ = "oracle_impact_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(64), nullable=False, unique=True, index=True)
    activity_id = Column(String(128), nullable=False, index=True)
    reporter = Column(String(200), nullable=True)
    data_type = Column(String(80), nullable=True)
    confidence = Column(Float, nullable=True)
    impact_hash = Column(String(64), nullable=True)
    evidence_commitment = Column(String(300), nullable=True)
    methodology_version = Column(String(32), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    challenged = Column(Boolean, nullable=False, default=False)
    challenge_deadline = Column(DateTime(timezone=True), nullable=True)


class OracleChallenge(Base):
    """A challenge raised against an :class:`OracleImpactReport`."""

    __tablename__ = "oracle_challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    challenge_id = Column(String(64), nullable=False, unique=True, index=True)
    activity_id = Column(String(128), nullable=False, index=True)
    challenger = Column(String(200), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    upheld = Column(Boolean, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class OracleImpactMetrics(Base):
    """Finalized impact metrics for one activity."""

    __tablename__ = "oracle_impact_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(String(128), nullable=False, index=True)
    confidence = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)
    trust_multiplier = Column(Float, nullable=True)
    survival_factor = Column(Float, nullable=True)
    scarcity_factor = Column(Float, nullable=True)
    challenge_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


# --------------------------------------------------------------------------- #
# Land registry (cadastral ownership and tenure) — P2-16
#
# ``services.land.registry.LandRegistryService`` owns these tables. A
# parcel is the cadastral unit (unique deed number, GeoJSON boundary);
# ownership records carry effective-dated shares that may be verified
# by a registrar; tenure rights model short-of-ownership use (grazing,
# seasonal corridors) held by a user or a nomadic community, with a
# pending / active / expired / revoked lifecycle. The tables are new, so
# the later Alembic wave creates them whole; constant defaults also get
# a server_default to match the file's additive-column convention.
# --------------------------------------------------------------------------- #


class LandParcel(Base):
    """A cadastral parcel: the registry's unit of land.

    ``id`` is the parcel identifier the registry contracts call
    ``parcel_id``; ownership and tenure rows reference it. The GeoJSON
    boundary is stored as JSON here; a later wave can move it to a
    PostGIS geometry column without changing the service API.
    """

    __tablename__ = "land_parcels"
    __table_args__ = (
        Index("ix_land_parcel_village", "village_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deed_no = Column(String(64), unique=True, nullable=False, index=True)
    village_id = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    area_ha = Column(Numeric(12, 2), nullable=False)
    boundary = Column(JSON, nullable=True)
    land_use = Column(
        String(32), nullable=False, default="agricultural", server_default=text("agricultural")
    )
    capability_class = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(UTC)
    )


class LandOwnership(Base):
    """One owner's effective-dated share of a parcel.

    History is kept rather than overwritten: a transfer closes the
    current record (sets ``effective_to``) and opens a successor row, so
    the chain of title stays queryable. The unique constraint allows one
    row per (parcel, owner, effective_from); ``LandRegistryService``
    additionally enforces that the active shares of a parcel never
    exceed 100%.
    """

    __tablename__ = "land_ownerships"
    __table_args__ = (
        Index("ix_land_ownership_parcel", "parcel_id"),
        Index("ix_land_ownership_owner", "owner_user_id"),
        UniqueConstraint(
            "parcel_id",
            "owner_user_id",
            "effective_from",
            name="uq_land_ownership_parcel_owner_from",
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parcel_id = Column(String(36), ForeignKey("land_parcels.id"), nullable=False, index=True)
    owner_user_id = Column(String(120), nullable=False, index=True)
    ownership_type = Column(
        String(32), nullable=False, default="individual", server_default=text("individual")
    )
    share_pct = Column(Numeric(5, 2), nullable=False)
    effective_from = Column(Date, nullable=False, default=date.today)
    effective_to = Column(Date, nullable=True)
    evidence_ref = Column(String(255), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, server_default=false())
    verified_by = Column(String(120), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LandTenureRight(Base):
    """A use right over a parcel: grazing or a seasonal migration corridor.

    A communal holder references the nomadic community by
    ``community_id`` (``nomadic_communities`` lives in
    ``services.marketplace``); an individual holder references
    ``holder_user_id``. ``season_start``/``season_end`` are month numbers
    (1-12) and may wrap across the year end (11 to 3 for a winter
    window). Overlap detection in the service considers the rights that
    are still pending or active.
    """

    __tablename__ = "land_tenure_rights"
    __table_args__ = (
        Index("ix_land_tenure_parcel", "parcel_id"),
        Index("ix_land_tenure_holder", "holder_user_id"),
        Index("ix_land_tenure_community", "community_id"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    right_type = Column(
        String(32), nullable=False, default="grazing", server_default=text("grazing")
    )
    parcel_id = Column(String(36), ForeignKey("land_parcels.id"), nullable=False, index=True)
    holder_type = Column(
        String(16), nullable=False, default="user", server_default=text("user")
    )
    holder_user_id = Column(String(120), nullable=True, index=True)
    community_id = Column(String(36), nullable=True, index=True)
    season_start = Column(Integer, nullable=False)
    season_end = Column(Integer, nullable=False)
    granted_by = Column(String(120), nullable=False)
    status = Column(
        String(20), nullable=False, default="pending", server_default=text("pending")
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    activated_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
