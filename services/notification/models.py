"""
Data models for notification module.

This module contains Pydantic models and dataclasses
for Notification service
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseNotification(BaseModel):
    """Base model for notification."""

    id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

    model_config = ConfigDict(from_attributes=True)


class NotificationCreate(BaseModel):
    """Model for creating notification."""
    pass


class NotificationRead(BaseModel):
    """Model for reading notification."""
    pass


class NotificationUpdate(BaseModel):
    """Model for updating notification."""
    pass
