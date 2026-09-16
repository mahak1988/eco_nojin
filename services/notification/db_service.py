"""DB-backed in-app notifications (v2.2). Create/list/mark-read."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models_db import AppNotification

VALID_TYPES = ('dispute', 'payment', 'order', 'system')


class NotificationDbService:
    def __init__(self, db: Session):
        self.db = db

    def notify(self, user_id: str, title: str, body: str = '', ntype: str = 'system',
               link: str | None = None) -> AppNotification:
        if ntype not in VALID_TYPES:
            raise ValueError(f'unknown notification type: {ntype}')
        if not user_id:
            raise ValueError('user_id is required')
        n = AppNotification(user_id=user_id, title=title[:200], body=body,
                            type=ntype, link=link)
        self.db.add(n)
        self.db.commit()
        self.db.refresh(n)
        return n

    def list_for(self, user_id: str, unread_only: bool = False, limit: int = 50) -> list[AppNotification]:
        stmt = select(AppNotification).where(AppNotification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(AppNotification.is_read.is_(False))
        stmt = stmt.order_by(AppNotification.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def mark_read(self, notification_id: str, user_id: str) -> AppNotification:
        n = self.db.get(AppNotification, notification_id)
        if n is None or n.user_id != user_id:
            raise LookupError(f'notification not found: {notification_id}')
        n.is_read = True
        self.db.commit()
        self.db.refresh(n)
        return n
