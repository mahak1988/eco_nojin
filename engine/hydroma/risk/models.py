"""
Data models for risk module.

This module contains Pydantic models and dataclasses
for Risk assessment and management
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseRisk(BaseModel):
    """Base model for risk."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class RiskCreate(BaseModel):
    """Model for creating risk."""
    pass


class RiskRead(BaseModel):
    """Model for reading risk."""
    pass


class RiskUpdate(BaseModel):
    """Model for updating risk."""
    pass
