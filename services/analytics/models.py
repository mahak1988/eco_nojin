"""Analytics SQLAlchemy models"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Index
from database.models import Base
import uuid

class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_type = Column(String(50), nullable=False)
    village_id = Column(String(50), nullable=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("ix_analytics_snapshots_lookup", "snapshot_type", "village_id"),
    )
    