"""Public contact endpoint for the Eco Nojin website (public-site phase).

Anonymous POST /api/v1/contact — rate-limited by the gateway middleware.
Storage policy follows the published privacy policy (data minimization):
only the fields the visitor submits plus a locale tag are stored; no IP and
no user-agent are persisted. A hidden honeypot field silently drops bot
submissions.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import ContactMessage

logger = logging.getLogger("econojin.api.contact")

router = APIRouter(prefix="/api/v1/contact", tags=["contact"])

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_db():
    with hub.get_session() as session:
        yield session


class ContactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    role: str | None = Field(default=None, max_length=80)
    message: str = Field(min_length=10, max_length=4000)
    locale: str | None = Field(default=None, max_length=8)
    # Honeypot: real users never fill this; bots do. Handled silently.
    website: str | None = Field(default=None, max_length=200)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, value: str) -> str:
        if not _EMAIL_RE.match(value.strip()):
            raise ValueError("invalid email address")
        return value.strip().lower()

    @field_validator("name", "message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


@router.post("")
def submit_contact(payload: ContactCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    if payload.website:
        # Silently accept so bots learn nothing; nothing is stored.
        logger.info("contact honeypot triggered — submission dropped")
        return {"ok": True}

    record = ContactMessage(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        message=payload.message,
        locale=payload.locale,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("contact message stored: id=%s role=%s", record.id, payload.role)
    return {"ok": True, "id": record.id}
