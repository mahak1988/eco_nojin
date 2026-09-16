"""Quality API — POST /api/v1/quality/inspections ..."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from services.api_gateway.auth import require_user
from services.quality_assurance.service import QualityService

router = APIRouter(prefix='/api/v1/quality', tags=['quality'])


def get_db():
    with hub.get_session() as session:
        yield session


class InspectionCreate(BaseModel):
    product_id: str = Field(min_length=1)
    inspection_type: str
    marketplace_id: str | None = None


class InspectionResult(BaseModel):
    score: float
    notes: str | None = None


@router.post('/inspections')
def create_inspection(payload: InspectionCreate, db: Session = Depends(get_db),
                      user=Depends(require_user)) -> dict[str, Any]:
    try:
        insp = QualityService(db).create_inspection(**payload.model_dump())
        return {'ok': True, 'id': insp.id, 'status': insp.status}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/inspections/{inspection_id}/result')
def record_result(inspection_id: str, payload: InspectionResult,
                  db: Session = Depends(get_db), user=Depends(require_user)) -> dict[str, Any]:
    try:
        out = QualityService(db).record_result(inspection_id, payload.score, payload.notes)
        insp = out['inspection']
        return {'ok': True, 'status': insp.status, 'score': insp.score,
                'certificate_id': out['certificate_id']}
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/inspections')
def list_inspections(product_id: str | None = None, limit: int = 50,
                     db: Session = Depends(get_db)) -> dict[str, Any]:
    items = QualityService(db).list(product_id=product_id, limit=limit)
    return {'count': len(items),
            'inspections': [{'id': i.id, 'product_id': i.product_id, 'status': i.status,
                             'score': i.score} for i in items]}
