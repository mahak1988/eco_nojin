"""Auth SQLAlchemy models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database.base import Base


class AuthUser(Base):
    __tablename__ = "auth_users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC),
                       onupdate=lambda: datetime.now(UTC))

class RefreshToken(Base):
    __tablename__ = "auth_refresh_tokens"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
