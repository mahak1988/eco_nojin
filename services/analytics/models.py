"""Analytics SQLAlchemy models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Index, String

from database.models import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_type = Column(String(50), nullable=False)
    village_id = Column(String(50), nullable=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_analytics_snapshots_lookup", "snapshot_type", "village_id"),
    )
