"""Shipment models."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Index, String, Text

from database.base import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Shipment(Base):
    __tablename__ = 'shipments'

    id = Column(String(36), primary_key=True, default=_uid)
    order_id = Column(String(36), nullable=False, index=True)
    carrier = Column(String(60))  # post|tipax|local_courier|pickup
    tracking_code = Column(String(60), index=True)

    status = Column(String(20), nullable=False, default='pending')  # pending|picked_up|in_transit|delivered|failed
    origin = Column(String(200))
    destination = Column(String(200))
    note = Column(Text)

    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, onupdate=_now)

    __table_args__ = (Index('idx_shipment_order', 'order_id'),)


class ShipmentEvent(Base):
    __tablename__ = 'shipment_events'

    id = Column(String(36), primary_key=True, default=_uid)
    shipment_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    actor = Column(String(36))
    note = Column(Text)
    created_at = Column(DateTime, default=_now)
