"""
Data models for plants module.

This module contains Pydantic models and dataclasses
for Plant database and species information
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BasePlants(BaseModel):
    """Base model for plants."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PlantsCreate(BaseModel):
    """Model for creating plants."""
    pass


class PlantsRead(BaseModel):
    """Model for reading plants."""
    pass


class PlantsUpdate(BaseModel):
    """Model for updating plants."""
    pass
