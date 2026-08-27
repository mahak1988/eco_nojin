"""Admin SQLAlchemy models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from database.models import Base


class AuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
