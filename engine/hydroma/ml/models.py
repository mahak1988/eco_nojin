"""
Data models for ml module.

This module contains Pydantic models and dataclasses
for Machine learning models for prediction
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseML(BaseModel):
    """Base model for ml."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class MLCreate(BaseModel):
    """Model for creating ml."""
    pass


class MLRead(BaseModel):
    """Model for reading ml."""
    pass


class MLUpdate(BaseModel):
    """Model for updating ml."""
    pass
