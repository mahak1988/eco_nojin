"""Quality inspection + certificate models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Index, String, Text

from database.base import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class QualityInspection(Base):
    __tablename__ = "quality_inspections"

    id = Column(String(36), primary_key=True, default=_uid)
    product_id = Column(String(36), nullable=False, index=True)
    marketplace_id = Column(String(36), index=True)
    inspector_id = Column(String(36))

    inspection_type = Column(String(30), nullable=False)  # harvest|packaging|delivery
    score = Column(Float)  # 0..100
    status = Column(String(20), nullable=False, default="pending")  # pending|passed|failed

    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, onupdate=_now)

    __table_args__ = (Index("idx_qi_product", "product_id"),)


class QualityCertificate(Base):
    __tablename__ = "quality_certificates"

    id = Column(String(36), primary_key=True, default=_uid)
    inspection_id = Column(String(36), nullable=False, index=True)
    product_id = Column(String(36), nullable=False, index=True)
    standard = Column(String(60), nullable=False)  # e.g. organic-national
    issued_at = Column(DateTime, default=_now)
    valid_until = Column(DateTime)
    issued_by = Column(String(36))
