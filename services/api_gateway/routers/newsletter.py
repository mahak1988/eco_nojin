"""Public newsletter subscription endpoint (no marketing trackers; the
newsletter is the project's own updates channel). Duplicate emails are
handled gracefully: the endpoint answers ok with already=True.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import NewsletterSubscriber

logger = logging.getLogger("econojin.api.newsletter")

router = APIRouter(prefix="/api/v1/newsletter", tags=["newsletter"])

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_db():
    with hub.get_session() as session:
        yield session


class NewsletterSubscribe(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    locale: str | None = Field(default=None, max_length=8)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, value: str) -> str:
        if not _EMAIL_RE.match(value.strip()):
            raise ValueError("invalid email address")
        return value.strip().lower()


@router.post("/subscribe")
def subscribe(payload: NewsletterSubscribe, db: Session = Depends(get_db)) -> dict[str, Any]:
    record = NewsletterSubscriber(email=payload.email, locale=payload.locale)
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        logger.info("newsletter duplicate subscription: %s", payload.email)
        return {"ok": True, "already": True}
    logger.info("newsletter subscriber stored: id=%s", record.id)
    return {"ok": True, "already": False}
