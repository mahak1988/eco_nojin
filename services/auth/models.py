"""
Data models for auth module.

This module contains Pydantic models and dataclasses
for Authentication and authorization service
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseAuth(BaseModel):
    """Base model for auth."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class AuthCreate(BaseModel):
    """Model for creating auth."""
    pass


class AuthRead(BaseModel):
    """Model for reading auth."""
    pass


class AuthUpdate(BaseModel):
    """Model for updating auth."""
    pass
