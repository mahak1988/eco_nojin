"""Admin SQLAlchemy models"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from database.models import Base
import uuid

class AuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    