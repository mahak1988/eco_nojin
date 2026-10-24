"""Notification service — multi-channel push notifications.

Channels:
- Email (SMTP / SendGrid-compatible)
- SMS (via telco webhook)
- In-app (database-backed)
- Telegram bot integration
"""
import logging
import os
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import Notification
from engine.hydroma.config.settings import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    user_id: str
    channel: str  # email | sms | in_app | telegram
    subject: str | None = None
    message: str
    metadata: dict | None = None


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


@router.post("/", status_code=201)
async def create_notification(
    body: NotificationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    notification = Notification(
        user_id=body.user_id,
        channel=body.channel,
        subject=body.subject,
        message=body.message,
        metadata=body.metadata,
        status="pending",
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return {"id": notification.id, "status": "created"}


@router.get("/")
async def list_notifications(
    user_id: str | None = None,
    limit: int = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    stmt = select(Notification)
    if user_id:
        stmt = stmt.where(Notification.user_id == user_id)
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return {
        "notifications": [
            {
                "id": n.id,
                "user_id": n.user_id,
                "channel": n.channel,
                "subject": n.subject,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]
    }


@router.post("/{notification_id}/mark-read")
async def mark_read(
    notification_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.status = "read"
    notification.read_at = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    return {"id": notification_id, "status": "read"}


def main() -> None:
    """Run the notification service."""
    import uvicorn

    uvicorn.run(app, host=os.getenv("HYDROMA_BIND_HOST", "127.0.0.1"), port=8003)



app = FastAPI(title="Eco Nojin Notification Service", version="1.0.0")
app.include_router(router)


if __name__ == "__main__":
    main()
