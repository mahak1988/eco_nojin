"""Telegram Bot FastAPI router"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub

# Compatibility: get_db via hub
async def get_db():
    async with hub.get_async_session() as session:
        yield session
from services.telegram_bot.integration_service import (
    TelegramIntegrationService,
    TelegramMessage,
    TelegramUser,
)

router = APIRouter(prefix="/telegram", tags=["Telegram"])

class WebhookPayload(BaseModel):
    message_id: int
    user_id: int
    username: str | None = None
    text: str
    village_id: str | None = None

class NotificationRequest(BaseModel):
    user_id: int
    message: str
    priority: str = "normal"

@router.post("/webhook")
async def telegram_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    service = TelegramIntegrationService(db)
    user = TelegramUser(
        user_id=payload.user_id,
        username=payload.username,
        village_id=payload.village_id,
    )
    message = TelegramMessage(
        message_id=payload.message_id,
        user=user,
        text=payload.text,
    )
    response = await service.process_message(message)
    return {"response": response}

@router.post("/notify")
async def send_notification(req: NotificationRequest, db: AsyncSession = Depends(get_db)):
    service = TelegramIntegrationService(db)
    success = await service.send_notification(req.user_id, req.message, req.priority)
    return {"success": success}

@router.get("/user-stats/{user_id}")
async def get_user_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    service = TelegramIntegrationService(db)
    return await service.get_user_stats(user_id)
