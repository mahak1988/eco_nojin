"""Public pilot-interest endpoint for the Eco Nojin website.

Anonymous POST /api/v1/pilot/apply — rate-limited by gateway middleware.
Data minimization per the privacy policy: only the fields the visitor
submits are stored (no IP, no user-agent). Consent is required.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import PilotApplication

logger = logging.getLogger("econojin.api.pilot")

router = APIRouter(prefix="/api/v1/pilot", tags=["pilot"])


def get_db():
    with hub.get_session() as session:
        yield session


class PilotApply(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    province: str = Field(min_length=2, max_length=80)
    land_hectares: float | None = Field(default=None, ge=0, le=100000)
    main_crop: str | None = Field(default=None, max_length=120)
    preferred_channel: str | None = Field(default=None, max_length=40)
    consent: bool
    locale: str | None = Field(default=None, max_length=8)

    @field_validator("name", "phone", "province")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


@router.post("/apply")
def apply_pilot(payload: PilotApply, db: Session = Depends(get_db)) -> dict[str, Any]:
    if not payload.consent:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="consent is required")

    record = PilotApplication(
        name=payload.name,
        phone=payload.phone,
        province=payload.province,
        land_hectares=payload.land_hectares,
        main_crop=payload.main_crop,
        preferred_channel=payload.preferred_channel,
        consent=payload.consent,
        locale=payload.locale,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("pilot application stored: id=%s province=%s", record.id, payload.province)
    return {"ok": True, "id": record.id}
