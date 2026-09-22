"""Logistics API — /api/v1/logistics/shipments ..."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from services.api_gateway.auth import require_user
from services.logistics.service import LogisticsService

router = APIRouter(prefix="/api/v1/logistics", tags=["logistics"])


def get_db():
    with hub.get_session() as session:
        yield session


class ShipmentCreate(BaseModel):
    order_id: str = Field(min_length=1)
    carrier: str = "post"
    origin: str = ""
    destination: str = ""


class StatusUpdate(BaseModel):
    status: str
    actor: str = ""
    note: str | None = None


@router.post("/shipments")
def create_shipment(
    payload: ShipmentCreate, db: Session = Depends(get_db), user=Depends(require_user)
) -> dict[str, Any]:
    try:
        sh = LogisticsService(db).create(**payload.model_dump())
        return {"ok": True, "id": sh.id, "status": sh.status}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        sh = LogisticsService(db).get(shipment_id)
        return {
            "shipment": {
                "id": sh.id,
                "order_id": sh.order_id,
                "status": sh.status,
                "carrier": sh.carrier,
                "tracking_code": sh.tracking_code,
            }
        }
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/shipments/{shipment_id}/status")
def update_status(
    shipment_id: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_user),
) -> dict[str, Any]:
    try:
        sh = LogisticsService(db).update_status(
            shipment_id, payload.status, payload.actor, payload.note
        )
        return {"ok": True, "id": sh.id, "status": sh.status}
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
