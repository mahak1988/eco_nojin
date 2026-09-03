"""Reporting SQLAlchemy models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from database.base import Base


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
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
