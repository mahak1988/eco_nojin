"""Support team API — named staff personas for user-facing support."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.config import get_db
from services.api_gateway.auth import get_current_user
from services.ai.support_agent import ask_support, personas_list

router = APIRouter(prefix="/api/v1/support", tags=["support"])


class SupportChatRequest(BaseModel):
    question: str
    lang: str = "fa"
    page: str | None = None


@router.get("/personas")
def support_personas() -> dict[str, Any]:
    return {"personas": personas_list()}


@router.post("/chat")
async def support_chat(
    payload: SupportChatRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    q = (payload.question or "").strip()
    if not q:
        raise HTTPException(422, "question is required")
    if len(q) > 1500:
        raise HTTPException(422, "question too long (max 1500 chars)")
    return await ask_support(db, user, payload.lang, q, payload.page)
