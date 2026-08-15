"""
Data models for soil module.

This module contains Pydantic models and dataclasses
for Soil analysis, classification, and health assessment
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseSoil(BaseModel):
    """Base model for soil."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SoilCreate(BaseModel):
    """Model for creating soil."""
    pass


class SoilRead(BaseModel):
    """Model for reading soil."""
    pass


class SoilUpdate(BaseModel):
    """Model for updating soil."""
    pass
