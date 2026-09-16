"""In-app notification model (plan v2.2 — notifications wiring)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text

from database.base import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AppNotification(Base):
    """A user-scoped in-app notification (disputes, payments, orders)."""

    __tablename__ = 'app_notifications'

    id = Column(String(36), primary_key=True, default=_uid)
    user_id = Column(String(36), nullable=False, index=True)
    type = Column(String(30), nullable=False, default='info')  # dispute|payment|order|system
    title = Column(String(200), nullable=False)
    body = Column(Text)
    link = Column(String(300))
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=_now)

    __table_args__ = (Index('idx_notif_user_read', 'user_id', 'is_read'),)

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'user_id': self.user_id, 'type': self.type,
            'title': self.title, 'body': self.body, 'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
