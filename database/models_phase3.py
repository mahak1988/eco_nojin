"""Phase 3 — بازارچه نهاد models.

Import this module in database/models.py __all__ or alongside the main models
to register these tables with SQLAlchemy Base.metadata.

Tenants, Bazaars (PostGIS), Trustees (5-member), Digital Signatures (PQ),
Market Profiles (regional hub).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.base import Base

# --- helpers ---------------------------------------------------------------


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


# --- Tenant ----------------------------------------------------------------


class Tenant(Base):
    """Legal entity / organization that owns one or more bazaars (multi-tenant)."""

    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    tax_id = Column(String(50), nullable=True)
    legal_form = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    registration_number = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    bazaars = relationship("Bazaar", back_populates="tenant")
    market_profiles = relationship("MarketProfile", back_populates="tenant")

    __table_args__ = (Index("idx_tenants_slug", "slug"),)


# --- MarketProfile (§5.3 کانون منطقه‌ای) ----------------------------------


class MarketProfile(Base):
    """Regional market hub profile (کانون منطقه‌ای)."""

    __tablename__ = "market_profiles"

    id = Column(String(36), primary_key=True, default=_uuid)
    tenant_id = Column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    region_type = Column(String(50), nullable=False, server_default="local")
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    coverage_radius_m = Column(Float, nullable=True)
    bazaar_count = Column(Integer, nullable=False, server_default="0")
    store_count = Column(Integer, nullable=False, server_default="0")
    established_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    tenant = relationship("Tenant", back_populates="market_profiles")

    __table_args__ = (Index("idx_market_profile_tenant", "tenant_id"),)


# --- Bazaar (§5.2 42 bazaars, PostGIS Polygon) ------------------------------


class Bazaar(Base):
    """Bazaar institution with geographic polygon geometry (PostGIS geometry( Polygon, 4326))."""

    __tablename__ = "bazaars"

    id = Column(String(36), primary_key=True, default=_uuid)
    tenant_id = Column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    market_profile_id = Column(
        String(36), ForeignKey("market_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name = Column(String(200), nullable=False)
    slug = Column(String(300), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    bazaar_type = Column(String(50), nullable=False, server_default="rural")
    # PostGIS geometry column (PostgreSQL/PostGIS only; for SQLite use bounding_box JSON)
    geom = Column(String(50), nullable=True)  # stores SRID-aware geometry reference
    bounding_box = Column(JSON, nullable=True)  # GeoJSON Polygon fallback for SQLite dev
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_ha = Column(Float, nullable=True)
    store_count = Column(Integer, nullable=False, server_default="0")
    status = Column(String(20), nullable=False, server_default="draft")
    established_date = Column(Date, nullable=True)
    regulator_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    tenant = relationship("Tenant", back_populates="bazaars")
    market_profile = relationship("MarketProfile")
    trustees = relationship("BazaarTrustee", back_populates="bazaar", cascade="all, delete-orphan")
    signatures = relationship(
        "DigitalSignature", back_populates="bazaar", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_bazaar_tenant", "tenant_id"),
        Index("idx_bazaar_status", "status"),
        Index("idx_bazaar_tenant_status", "tenant_id", "status"),
    )


# --- BazaarTrustee (§1.2 هیئت مؤسس 5 نفره) --------------------------------


class BazaarTrustee(Base):
    """5-member founding/trustee board for each bazaar."""

    __tablename__ = "bazaar_trustees"

    id = Column(String(36), primary_key=True, default=_uuid)
    bazaar_id = Column(
        String(36), ForeignKey("bazaars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    national_id = Column(String(50), nullable=True)
    role = Column(
        String(50), nullable=False, server_default="trustee"
    )  # founder | trustee | secretary | treasurer | representative
    position = Column(Integer, nullable=False)  # 1-5 per §1.2
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    is_approved = Column(Boolean, nullable=False, server_default="0")
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    bazaar = relationship("Bazaar", back_populates="trustees")
    signatures = relationship("DigitalSignature", back_populates="trustee")

    __table_args__ = (
        Index("idx_trustee_bazaar", "bazaar_id"),
        UniqueConstraint("bazaar_id", "position", name="uq_trustee_bazaar_position"),
    )


# --- DigitalSignature (§6.2 T05 5-party PQ signature) -----------------------


class DigitalSignature(Base):
    """PQ digital signature on a bazaar establishment step (DILITHIUM2+ED25519 per test_pqcrypto.py)."""

    __tablename__ = "bazaar_signatures"

    id = Column(String(36), primary_key=True, default=_uuid)
    bazaar_id = Column(
        String(36), ForeignKey("bazaars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trustee_id = Column(
        String(36), ForeignKey("bazaar_trustees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id = Column(String(36), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)  # 1-10 per §7 wizard
    agreement_type = Column(String(50), nullable=False, server_default="establishment")
    signature_hex = Column(Text, nullable=False)  # DILITHIUM2 part
    pq_public_hex = Column(Text, nullable=False)  # Dilithium public key
    ciphertext_hex = Column(Text, nullable=True)  # KYBER512 ciphertext (hybrid KEM)
    shared_secret_hex = Column(Text, nullable=True)  # hybrid shared secret
    algorithm = Column(String(50), nullable=False, server_default="DILITHIUM2+ED25519")
    kem_algorithm = Column(String(50), nullable=True, server_default="KYBER512+X25519")
    signed_at = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, nullable=False, server_default="1")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    bazaar = relationship("Bazaar", back_populates="signatures")
    trustee = relationship("BazaarTrustee", back_populates="signatures")

    __table_args__ = (
        Index("idx_signature_bazaar", "bazaar_id"),
        UniqueConstraint("trustee_id", "step_number", name="uq_signature_trustee_step"),
    )
