"""
Data models for erosion module.

This module contains Pydantic models and dataclasses
for Soil erosion modeling and risk assessment
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseErosion(BaseModel):
    """Base model for erosion."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class ErosionCreate(BaseModel):
    """Model for creating erosion."""
    pass


class ErosionRead(BaseModel):
    """Model for reading erosion."""
    pass


class ErosionUpdate(BaseModel):
    """Model for updating erosion."""
    pass
