"""Bots FastAPI router"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.bots.unified_service import (
    BotMessage,
    BotPlatform,
    MessageType,
    UnifiedBotService,
)


# Compatibility: get_db via hub
async def get_db():
    async with hub.get_async_session() as session:
        yield session


router = APIRouter(prefix="/bots", tags=["Bots"])


class SendMessageRequest(BaseModel):
    platform: str
    chat_id: str
    content: str
    message_type: str = "text"


class BroadcastRequest(BaseModel):
    chat_id: str
    content: str
    platforms: list[str] | None = None


class AdviceRequest(BaseModel):
    question: str
    village_id: str | None = None


@router.post("/send")
async def send_message(req: SendMessageRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    service = UnifiedBotService(db)
    message = BotMessage(
        platform=BotPlatform(req.platform),
        chat_id=req.chat_id,
        message_type=MessageType(req.message_type),
        content=req.content,
    )
    result = await service.send_message(message)
    return {"success": result.success, "error": result.error}


@router.post("/broadcast")
async def broadcast(req: BroadcastRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    service = UnifiedBotService(db)
    message = BotMessage(
        platform=BotPlatform.TELEGRAM,  # placeholder
        chat_id=req.chat_id,
        message_type=MessageType.TEXT,
        content=req.content,
    )
    platforms = [BotPlatform(p) for p in req.platforms] if req.platforms else None
    results = await service.broadcast(message, platforms)
    return {p.value: {"success": r.success, "error": r.error} for p, r in results.items()}


@router.post("/advice")
async def get_advice(req: AdviceRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    service = UnifiedBotService(db)
    advice = await service.get_advice(req.question, req.village_id)
    return {"advice": advice}
