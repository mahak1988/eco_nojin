"""Marketplace payment + escrow ledger models (plan v2.1 — multi-gateway)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Numeric, String, Text

from database.base import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MarketplacePayment(Base):
    """A gateway payment attempt for an order.

    status flow: initiated -> redirected (zarinpal/international) | awaiting_verification (bank)
                 -> verified -> released_to_seller | refunded | failed
    escrow_status: none -> held -> released | refunded
    """

    __tablename__ = 'marketplace_payments'

    id = Column(String(36), primary_key=True, default=_uid)
    order_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)

    gateway = Column(String(20), nullable=False)  # zarinpal | bank | international
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(8), nullable=False, default='IRR')

    status = Column(String(24), nullable=False, default='initiated', index=True)
    escrow_status = Column(String(24), nullable=False, default='none')

    authority = Column(String(100), index=True)   # zarinpal authority
    ref_id = Column(String(60))                   # gateway reference
    card_pan_masked = Column(String(30))
    tracking_code = Column(String(60))            # bank transfer tracking code
    redirect_url = Column(Text)

    gateway_meta = Column(Text)                   # raw gateway response (json str), audit trail
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, onupdate=_now)

    __table_args__ = (
        Index('idx_mpay_order', 'order_id'),
        Index('idx_mpay_status', 'status'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'order_id': self.order_id, 'gateway': self.gateway,
            'amount': float(self.amount or 0), 'currency': self.currency,
            'status': self.status, 'escrow_status': self.escrow_status,
            'redirect_url': self.redirect_url, 'ref_id': self.ref_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MarketplaceEscrowEntry(Base):
    """Immutable escrow ledger: funds held after gateway verification,
    released to the seller on delivery confirmation, or refunded."""

    __tablename__ = 'marketplace_escrow_entries'

    id = Column(String(36), primary_key=True, default=_uid)
    payment_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False, index=True)
    seller_id = Column(String(36), index=True)
    marketplace_id = Column(String(36), index=True)

    entry_type = Column(String(20), nullable=False)  # hold | release | refund
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(8), nullable=False, default='IRR')
    note = Column(Text)
    actor_id = Column(String(36))
    created_at = Column(DateTime, default=_now)

    __table_args__ = (
        Index('idx_escrow_payment', 'payment_id'),
        Index('idx_escrow_order', 'order_id'),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'payment_id': self.payment_id, 'order_id': self.order_id,
            'entry_type': self.entry_type, 'amount': float(self.amount or 0),
            'currency': self.currency, 'created_at': self.created_at.isoformat() if self.created_at else None,
        }
