"""
Data models for ecotourism module.

This module contains Pydantic models and dataclasses
for Ecotourism planning and management
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseEcotourism(BaseModel):
    """Base model for ecotourism."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class EcotourismCreate(BaseModel):
    """Model for creating ecotourism."""
    pass


class EcotourismRead(BaseModel):
    """Model for reading ecotourism."""
    pass


class EcotourismUpdate(BaseModel):
    """Model for updating ecotourism."""
    pass
