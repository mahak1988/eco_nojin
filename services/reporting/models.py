"""
Data models for reporting module.

This module contains Pydantic models and dataclasses
for Report generation service
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseReporting(BaseModel):
    """Base model for reporting."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ReportingCreate(BaseModel):
    """Model for creating reporting."""
    pass


class ReportingRead(BaseModel):
    """Model for reading reporting."""
    pass


class ReportingUpdate(BaseModel):
    """Model for updating reporting."""
    pass
