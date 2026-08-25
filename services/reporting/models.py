"""Reporting SQLAlchemy models"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from database.models import Base
import uuid

class Report(Base):
    __tablename__ = "reports"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="pending", index=True)
    parameters = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    generated_by = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    