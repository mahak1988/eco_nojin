"""Dispute data models (SQLite-portable; Postgres UUID migration later)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text

from database.base import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=_uid)
    order_id = Column(String(36), nullable=False, index=True)
    marketplace_id = Column(String(36), index=True)
    complainant_id = Column(String(36), nullable=False)
    respondent_id = Column(String(36))

    category = Column(String(30), nullable=False)  # quality|delivery|payment|other
    description = Column(Text, nullable=False)

    status = Column(String(20), nullable=False, default="open", index=True)
    # open -> under_review -> resolved | rejected | escalated

    resolution = Column(Text)
    resolved_by = Column(String(36))
    resolved_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, onupdate=_now)

    __table_args__ = (
        Index("idx_dispute_order", "order_id"),
        Index("idx_dispute_status", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "status": self.status,
            "category": self.category,
            "description": self.description,
            "resolution": self.resolution,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DisputeEvent(Base):
    __tablename__ = "dispute_events"

    id = Column(String(36), primary_key=True, default=_uid)
    dispute_id = Column(String(36), nullable=False, index=True)
    event = Column(String(40), nullable=False)  # opened|comment|evidence|status_change|resolved
    actor = Column(String(36))
    note = Column(Text)
    created_at = Column(DateTime, default=_now)

    __table_args__ = (Index("idx_dispute_event_dispute", "dispute_id"),)
