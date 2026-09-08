"""HyDroMa data hub — central aggregation of model runs (per user key).

Every dashboard calculator can register its result here (POST /runs).
Runs are keyed by an anonymous client key (no PII, no IP stored); runs can
be marked shared so outputs are publicly visible in the shared feed.
This implements the "single aggregation center + shared outputs" requirement
of the HyDroMa dashboard (report 64/65).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import ModelRun

logger = logging.getLogger("econojin.api.hub")

router = APIRouter(prefix="/api/v1/hub", tags=["hydroma-hub"])

MAX_JSON_CHARS = 8000
_USER_KEY_RE = __import__("re").compile(r"^[A-Za-z0-9_-]{8,64}$")


def get_db():
    with hub.get_session() as session:
        yield session


class RunCreate(BaseModel):
    user_key: str = Field(min_length=8, max_length=64)
    model_id: str = Field(min_length=2, max_length=80)
    title: str | None = Field(default=None, max_length=160)
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None

    @field_validator("user_key")
    @classmethod
    def _key_shape(cls, value: str) -> str:
        if not _USER_KEY_RE.match(value.strip()):
            raise ValueError("invalid user key")
        return value.strip()

    @field_validator("inputs", "outputs")
    @classmethod
    def _size_cap(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is not None and len(json.dumps(value)) > MAX_JSON_CHARS:
            raise ValueError("payload too large (max 8000 chars of JSON)")
        return value


class ShareUpdate(BaseModel):
    shared: bool


@router.post("/runs")
def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    record = ModelRun(
        user_key=payload.user_key,
        model_id=payload.model_id,
        title=payload.title,
        inputs=payload.inputs,
        outputs=payload.outputs,
        shared=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("hub run stored: id=%s model=%s", record.id, payload.model_id)
    return {"ok": True, "id": record.id}


@router.get("/runs")
def list_runs(
    user_key: str = Query(..., min_length=8, max_length=64),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = (
        select(ModelRun)
        .where(ModelRun.user_key == user_key)
        .order_by(ModelRun.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(statement).scalars().all()
    return {
        "ok": True,
        "count": len(rows),
        "runs": [
            {
                "id": row.id,
                "model_id": row.model_id,
                "title": row.title,
                "inputs": row.inputs,
                "outputs": row.outputs,
                "shared": row.shared,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


@router.post("/runs/{run_id}/share")
def set_shared(
    run_id: str,
    payload: ShareUpdate,
    user_key: str = Query(..., min_length=8, max_length=64),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(ModelRun).where(ModelRun.id == run_id, ModelRun.user_key == user_key)
    row = db.execute(statement).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found for this user key")
    row.shared = payload.shared
    db.commit()
    return {"ok": True, "id": row.id, "shared": row.shared}


@router.get("/shared")
def list_shared(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = (
        select(ModelRun)
        .where(ModelRun.shared.is_(True))
        .order_by(ModelRun.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(statement).scalars().all()
    return {
        "ok": True,
        "count": len(rows),
        "runs": [
            {
                "id": row.id,
                "model_id": row.model_id,
                "title": row.title,
                "outputs": row.outputs,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }
