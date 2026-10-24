"""Territory domain models for Eco Nojin.

Covers villages, regions, territory hierarchy, and governance structures.
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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.base import Base


class TerritoryType(StrEnum):
    """Types of territories in the hierarchy."""

    REGION = "region"  # استان
    COUNTY = "county"  # شهرستان
    DISTRICT = "district"  # بخش
    VILLAGE = "village"  # روستا
    NEIGHBORHOOD = "neighborhood"  # محله/دهستان


class TerritoryStatus(StrEnum):
    """Status of a territory."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class Territory(Base):
    """Territory hierarchy model (region -> county -> district -> village -> neighborhood)."""

    __tablename__ = "territories"
    __table_args__ = (
        Index("idx_territory_parent", "parent_id"),
        Index("idx_territory_type", "territory_type"),
        Index("idx_territory_status", "status"),
        Index("idx_territory_code", "code"),
        UniqueConstraint("parent_id", "code", name="uq_territory_parent_code"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), nullable=False, index=True)  # e.g., "IR-01", "IR-01-02"
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    territory_type = Column(String(30), nullable=False, index=True)
    parent_id = Column(String(36), ForeignKey("territories.id"), nullable=True, index=True)
    level = Column(Integer, nullable=False, default=0)  # 0=region, 1=county, 2=district, 3=village, 4=neighborhood

    # Geographic data
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    boundary_geojson = Column(JSON, nullable=True)  # Polygon/MultiPolygon
    center_point = Column(JSON, nullable=True)  # {"lat": x, "lon": y}
    area_hectares = Column(Numeric(12, 2), nullable=True)

    # Administrative
    status = Column(String(20), default=TerritoryStatus.ACTIVE, index=True)
    population = Column(Integer, nullable=True)
    household_count = Column(Integer, nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Brand & Identity
    brand_name = Column(String(200), nullable=True)
    brand_logo_url = Column(String(500), nullable=True)
    brand_slogan = Column(String(500), nullable=True)
    gi_registration = Column(String(100), nullable=True)  # Geographical Indicator

    # Economic metrics
    monthly_gmv = Column(Numeric(18, 2), default=Decimal("0.00"))
    active_sellers = Column(Integer, default=0)
    active_tour_guides = Column(Integer, default=0)
    total_members = Column(Integer, default=0)

    # Smart contract (for blockchain integration)
    smart_contract_address = Column(String(100), nullable=True)
    blockchain_network = Column(String(50), nullable=True)

    # Timestamps
    established_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    parent = relationship("Territory", remote_side=[id], back_populates="children")
    children = relationship("Territory", back_populates="parent")
    governance_members = relationship("TerritoryGovernanceMember", back_populates="territory")
    funds = relationship("TerritoryFund", back_populates="territory")

    def __repr__(self):
        return f"<Territory id={self.id} code={self.code} name={self.name} type={self.territory_type}>"


class TerritoryGovernanceRole(StrEnum):
    """Roles in territory governance (LWG - Local Working Group)."""

    CHAIRPERSON = "chairperson"
    VICE_CHAIR = "vice_chair"
    SECRETARY = "secretary"
    TREASURER = "treasurer"
    MEMBER = "member"
    AGRICULTURE_REP = "agriculture_rep"
    TOURISM_REP = "tourism_rep"
    MARKETPLACE_REP = "marketplace_rep"
    KNOWLEDGE_REP = "knowledge_rep"
    ENVIRONMENT_REP = "environment_rep"
    YOUTH_REP = "youth_rep"
    WOMEN_REP = "women_rep"


class TerritoryGovernanceMember(Base):
    """Local Working Group (LWG) members for a territory."""

    __tablename__ = "territory_governance"
    __table_args__ = (
        Index("idx_gov_territory", "territory_id"),
        Index("idx_gov_user", "user_id"),
        Index("idx_gov_role", "role"),
        UniqueConstraint("territory_id", "user_id", "role", name="uq_gov_territory_user_role"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    territory_id = Column(String(36), ForeignKey("territories.id"), nullable=False)
    user_id = Column(String(36), nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    term_start = Column(Date, nullable=True)
    term_end = Column(Date, nullable=True)
    elected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Relationships
    territory = relationship("Territory", back_populates="governance_members")

    def __repr__(self):
        return f"<TerritoryGovernanceMember territory={self.territory_id} user={self.user_id} role={self.role}>"


class TerritoryFund(Base):
    """Financial fund for a territory (collected from marketplace fees, etc.)."""

    __tablename__ = "territory_funds"
    __table_args__ = (
        Index("idx_fund_territory", "territory_id"),
        UniqueConstraint("territory_id", name="uq_fund_territory"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    territory_id = Column(String(36), ForeignKey("territories.id"), nullable=False, index=True)
    contract_address = Column(String(100), nullable=True)
    fee_bps = Column(Integer, default=100)  # Basis points (1% = 100 bps)
    total_collected = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_distributed = Column(Numeric(18, 2), default=Decimal("0.00"))
    pending_balance = Column(Numeric(18, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="IRR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    territory = relationship("Territory", back_populates="funds")
    distributions = relationship("TerritoryFundDistribution", back_populates="fund")

    def __repr__(self):
        return f"<TerritoryFund territory={self.territory_id} balance={self.pending_balance}>"


class TerritoryFundDistribution(Base):
    """Distribution record from territory fund."""

    __tablename__ = "territory_fund_distributions"
    __table_args__ = (
        Index("idx_dist_fund", "fund_id"),
        Index("idx_dist_territory", "territory_id"),
        Index("idx_dist_status", "status"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id = Column(String(36), ForeignKey("territory_funds.id"), nullable=False, index=True)
    territory_id = Column(String(36), ForeignKey("territories.id"), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    purpose = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    recipient_user_id = Column(String(36), nullable=True)
    recipient_organization = Column(String(200), nullable=True)
    proposed_by = Column(String(36), nullable=False)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected, executed
    blockchain_tx_hash = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    fund = relationship("TerritoryFund", back_populates="distributions")

    def __repr__(self):
        return f"<TerritoryFundDistribution fund={self.fund_id} amount={self.amount} status={self.status}>"


class TerritoryBrand(Base):
    """Territory brand registration and verification."""

    __tablename__ = "territory_brands"
    __table_args__ = (
        Index("idx_brand_territory", "territory_id"),
        Index("idx_brand_status", "status"),
        UniqueConstraint("territory_id", name="uq_brand_territory"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    territory_id = Column(String(36), ForeignKey("territories.id"), nullable=False, index=True)
    brand_name = Column(String(200), nullable=False)
    brand_name_en = Column(String(200), nullable=True)
    logo_url = Column(String(500), nullable=True)
    slogan = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    story = Column(Text, nullable=True)  # Brand story/heritage

    # Verification
    status = Column(String(20), default="draft", index=True)  # draft, pending, verified, rejected
    verified_by = Column(String(36), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    gi_registration_number = Column(String(100), nullable=True)
    gi_registration_date = Column(Date, nullable=True)

    # Digital signature (PQ crypto)
    signature_hex = Column(Text, nullable=True)
    pq_public_hex = Column(Text, nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self):
        return f"<TerritoryBrand territory={self.territory_id} name={self.brand_name} status={self.status}>"