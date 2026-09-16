"""Dispute resolution service — lifecycle: open → under_review → resolved/rejected/escalated."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Dispute, DisputeEvent


class DisputeService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order_id: str, complainant_id: str, category: str,
               description: str, respondent_id: str | None = None,
               marketplace_id: str | None = None) -> Dispute:
        if category not in ('quality', 'delivery', 'payment', 'other'):
            raise ValueError(f'unknown category: {category}')
        dispute = Dispute(
            order_id=order_id, complainant_id=complainant_id, respondent_id=respondent_id,
            marketplace_id=marketplace_id, category=category, description=description,
        )
        self.db.add(dispute)
        self.db.commit()
        self.db.refresh(dispute)
        self.db.add(DisputeEvent(dispute_id=dispute.id, event='opened', actor=complainant_id,
                                 note=description[:200]))
        self.db.commit()
        return dispute

    def get(self, dispute_id: str) -> Dispute:
        d = self.db.get(Dispute, dispute_id)
        if d is None:
            raise LookupError(f'dispute not found: {dispute_id}')
        return d

    def list(self, status: str | None = None, limit: int = 50) -> list[Dispute]:
        stmt = select(Dispute).order_by(Dispute.created_at.desc()).limit(limit)
        if status:
            stmt = select(Dispute).where(Dispute.status == status).order_by(Dispute.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def add_event(self, dispute_id: str, event: str, actor: str, note: str | None = None) -> DisputeEvent:
        d = self.get(dispute_id)
        if d.status in ('resolved', 'rejected'):
            raise ValueError('dispute is closed')
        ev = DisputeEvent(dispute_id=dispute_id, event=event, actor=actor, note=note)
        self.db.add(ev)
        if d.status == 'open' and event in ('comment', 'evidence'):
            d.status = 'under_review'
        self.db.commit()
        return ev

    def resolve(self, dispute_id: str, resolved_by: str, resolution: str,
                outcome: str = 'resolved') -> Dispute:
        if outcome not in ('resolved', 'rejected'):
            raise ValueError(f'invalid outcome: {outcome}')
        d = self.get(dispute_id)
        if d.status in ('resolved', 'rejected'):
            raise ValueError('dispute already closed')
        d.status = outcome
        d.resolution = resolution
        d.resolved_by = resolved_by
        d.resolved_at = d.updated_at
        self.db.add(DisputeEvent(dispute_id=d.id, event='resolved', actor=resolved_by, note=resolution[:200]))
        self.db.commit()
        return d

    def escalate(self, dispute_id: str, actor: str) -> Dispute:
        d = self.get(dispute_id)
        if d.status in ('resolved', 'rejected'):
            raise ValueError('dispute already closed')
        d.status = 'escalated'
        self.db.add(DisputeEvent(dispute_id=d.id, event='escalated', actor=actor))
        self.db.commit()
        return d

    def events(self, dispute_id: str) -> list[DisputeEvent]:
        stmt = select(DisputeEvent).where(DisputeEvent.dispute_id == dispute_id).order_by(DisputeEvent.created_at)
        return list(self.db.execute(stmt).scalars().all())
