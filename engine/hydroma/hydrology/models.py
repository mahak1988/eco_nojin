"""
Data models for hydrology module.

This module contains Pydantic models and dataclasses
for Hydrological calculations and water balance modeling
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseHydrology(BaseModel):
    """Base model for hydrology."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class HydrologyCreate(BaseModel):
    """Model for creating hydrology."""
    pass


class HydrologyRead(BaseModel):
    """Model for reading hydrology."""
    pass


class HydrologyUpdate(BaseModel):
    """Model for updating hydrology."""
    pass
