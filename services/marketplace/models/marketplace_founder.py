"""MarketplaceFounder — بنیانگذاران بازارچه (برنامهٔ ۲.۰، فاز ۱.۱-ب)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Index, Numeric, String, UniqueConstraint

from database.base import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MarketplaceFounder(Base):
    """بنیانگذار/همبنیانگذار یک بازارچه روستایی یا عشایری."""

    __tablename__ = 'marketplace_founders'

    id = Column(String(36), primary_key=True, default=_uid)
    marketplace_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)

    role = Column(String(20), nullable=False, default='founder')  # founder|co_founder|advisor|council_member

    equity_share = Column(Numeric(5, 2), default=0)
    contribution_type = Column(String(20))  # financial|technical|land|knowledge
    contribution_amount = Column(Numeric(12, 2))

    identity_verified = Column(Boolean, default=False)
    identity_verification_date = Column(DateTime)
    verification_method = Column(String(40))  # national_id|community_verification|sbt_token

    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=_now)
    left_at = Column(DateTime)

    wallet_address = Column(String(42))

    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, onupdate=_now)

    __table_args__ = (
        Index('idx_founder_marketplace', 'marketplace_id'),
        Index('idx_founder_user', 'user_id'),
        UniqueConstraint('marketplace_id', 'user_id', name='uq_marketplace_user'),
        CheckConstraint('equity_share >= 0 AND equity_share <= 100', name='ck_equity_share'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'marketplace_id': self.marketplace_id,
            'user_id': self.user_id,
            'role': self.role,
            'equity_share': float(self.equity_share or 0),
            'contribution_type': self.contribution_type,
            'identity_verified': self.identity_verified,
            'is_active': self.is_active,
        }
