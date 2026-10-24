"""Quality assurance service — inspection lifecycle + certificates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import QualityCertificate, QualityInspection

PASS_THRESHOLD = 80.0
CERTIFICATE_MIN_SCORE = 85.0


class QualityService:
    def __init__(self, db: Session):
        self.db = db

    def create_inspection(
        self,
        product_id: str,
        inspection_type: str,
        marketplace_id: str | None = None,
        inspector_id: str | None = None,
    ) -> QualityInspection:
        if inspection_type not in ("harvest", "packaging", "delivery"):
            raise ValueError(f"unknown inspection type: {inspection_type}")
        insp = QualityInspection(
            product_id=product_id,
            inspection_type=inspection_type,
            marketplace_id=marketplace_id,
            inspector_id=inspector_id,
        )
        self.db.add(insp)
        self.db.commit()
        self.db.refresh(insp)
        return insp

    def record_result(
        self,
        inspection_id: str,
        score: float,
        notes: str | None = None,
        inspector_id: str | None = None,
    ) -> dict[str, Any]:
        if not (0.0 <= score <= 100.0):
            raise ValueError("score must be in [0, 100]")
        insp = self.db.get(QualityInspection, inspection_id)
        if insp is None:
            raise LookupError(f"inspection not found: {inspection_id}")
        insp.score = score
        insp.status = "passed" if score >= PASS_THRESHOLD else "failed"
        insp.notes = notes
        insp.inspector_id = inspector_id or insp.inspector_id
        self.db.commit()

        certificate = None
        if insp.status == "passed" and score >= CERTIFICATE_MIN_SCORE:
            cert = QualityCertificate(
                inspection_id=insp.id,
                product_id=insp.product_id,
                standard="econojin-quality",
                issued_by=insp.inspector_id,
                valid_until=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=365),
            )
            self.db.add(cert)
            self.db.commit()
            certificate = cert.id
        return {"inspection": insp, "certificate_id": certificate}

    def get(self, inspection_id: str) -> QualityInspection:
        insp = self.db.get(QualityInspection, inspection_id)
        if insp is None:
            raise LookupError(f"inspection not found: {inspection_id}")
        return insp

    def list(self, product_id: str | None = None, limit: int = 50) -> list[QualityInspection]:
        stmt = select(QualityInspection).order_by(QualityInspection.created_at.desc()).limit(limit)
        if product_id:
            stmt = (
                select(QualityInspection)
                .where(QualityInspection.product_id == product_id)
                .limit(limit)
            )
        return list(self.db.execute(stmt).scalars().all())
