"""
Data models for standards module.

This module contains Pydantic models and dataclasses
for Standards and compliance management
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseStandards(BaseModel):
    """Base model for standards."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class StandardsCreate(BaseModel):
    """Model for creating standards."""
    pass


class StandardsRead(BaseModel):
    """Model for reading standards."""
    pass


class StandardsUpdate(BaseModel):
    """Model for updating standards."""
    pass
