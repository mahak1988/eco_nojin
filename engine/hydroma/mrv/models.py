"""
Data models for mrv module.

This module contains Pydantic models and dataclasses
for Measurement, Reporting, and Verification for carbon credits
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class BaseMRV(BaseModel):
    """Base model for mrv."""
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(from_attributes=True)


class MRVCreate(BaseModel):
    """Model for creating mrv."""
    pass


class MRVRead(BaseModel):
    """Model for reading mrv."""
    pass


class MRVUpdate(BaseModel):
    """Model for updating mrv."""
    pass
