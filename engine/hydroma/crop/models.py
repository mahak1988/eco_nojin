"""
Data models for crop module.

This module contains Pydantic models and dataclasses
for Crop growth modeling and yield prediction
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseCrop(BaseModel):
    """Base model for crop."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class CropCreate(BaseModel):
    """Model for creating crop."""
    pass


class CropRead(BaseModel):
    """Model for reading crop."""
    pass


class CropUpdate(BaseModel):
    """Model for updating crop."""
    pass
