"""
Data models for geospatial module.

This module contains Pydantic models and dataclasses
for Geospatial analysis and mapping utilities
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseGeospatial(BaseModel):
    """Base model for geospatial."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class GeospatialCreate(BaseModel):
    """Model for creating geospatial."""
    pass


class GeospatialRead(BaseModel):
    """Model for reading geospatial."""
    pass


class GeospatialUpdate(BaseModel):
    """Model for updating geospatial."""
    pass
