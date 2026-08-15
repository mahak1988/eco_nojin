"""
Data models for groundwater module.

This module contains Pydantic models and dataclasses
for Groundwater modeling and aquifer analysis
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseGroundwater(BaseModel):
    """Base model for groundwater."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class GroundwaterCreate(BaseModel):
    """Model for creating groundwater."""
    pass


class GroundwaterRead(BaseModel):
    """Model for reading groundwater."""
    pass


class GroundwaterUpdate(BaseModel):
    """Model for updating groundwater."""
    pass
