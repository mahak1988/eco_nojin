import uuid

"""
مدل‌های داده مدیریت یکپارچه منظر (ILM)
"""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from database.models import Base


class LandscapeGovernanceRole(str, Enum):
    COUNCIL_MEMBER = "council_member"
    LANDSCAPE_MANAGER = "landscape_manager"
    MARKETPLACE_REP = "marketplace_rep"
    TOURISM_REP = "tourism_rep"
    AGRICULTURE_REP = "agriculture_rep"
    KNOWLEDGE_REP = "knowledge_rep"


class LandscapeVillage(Base):
    __tablename__ = "landscape_villages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    region = Column(String(100), nullable=False)
    country = Column(String(100), default="IR")
    coordinates = Column(JSON)
    geo_boundary = Column(JSON)
    brand_name = Column(String(200))
    brand_logo_url = Column(String(500))
    gi_registration = Column(String(100))
    is_active = Column(Boolean, default=True)
    established_at = Column(Date)
    active_modules = Column(JSON, default=list)
    total_members = Column(Integer, default=0)
    active_sellers = Column(Integer, default=0)
    active_tour_guides = Column(Integer, default=0)
    monthly_gmv = Column(Numeric(18, 2), default=Decimal("0.00"))
    ecological_metrics_data = Column(JSON, default=dict)
    smart_contract_address = Column(String(100))
    blockchain_network = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class LandscapeGovernanceMember(Base):
    __tablename__ = "landscape_governance"
    __table_args__ = (
        Index("idx_gov_village", "village_id"),
        Index("idx_gov_role", "role"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    term_start = Column(Date)
    term_end = Column(Date)
    elected_at = Column(DateTime, default=lambda: datetime.now(UTC))
    phone = Column(String(20))
    email = Column(String(200))


class LandscapeFund(Base):
    __tablename__ = "landscape_funds"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_id = Column(String(100), unique=True, nullable=False, index=True)
    contract_address = Column(String(100))
    fee_bps = Column(Integer, default=100)
    total_collected = Column(Numeric(18, 2), default=Decimal("0.00"))
    total_distributed = Column(Numeric(18, 2), default=Decimal("0.00"))
    pending_balance = Column(Numeric(18, 2), default=Decimal("0.00"))
    currency = Column(String(3), default="IRR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class LandscapeFundDistribution(Base):
    __tablename__ = "landscape_fund_distributions"
    __table_args__ = (
        Index("idx_dist_fund", "fund_id"),
        Index("idx_dist_village", "village_id"),
    )
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id = Column(String(36), nullable=False, index=True)
    village_id = Column(String(100), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    purpose = Column(String(200), nullable=False)
    description = Column(Text)
    recipient_user_id = Column(String(36))
    recipient_organization = Column(String(200))
    proposed_by = Column(String(36), nullable=False)
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending", index=True)
    blockchain_tx_hash = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    executed_at = Column(DateTime, nullable=True)
