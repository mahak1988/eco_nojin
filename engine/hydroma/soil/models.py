"""
Data models for soil module.

This module contains Pydantic models and dataclasses
for Soil analysis, classification, and health assessment
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseSoil(BaseModel):
    """Base model for soil."""

    id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

    model_config = ConfigDict(from_attributes=True)


class SoilCreate(BaseModel):
    """Model for creating soil."""
    pass


class SoilRead(BaseModel):
    """Model for reading soil."""
    pass


class SoilUpdate(BaseModel):
    """Model for updating soil."""
    pass
