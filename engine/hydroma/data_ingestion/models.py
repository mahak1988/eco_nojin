"""
Data models for data_ingestion module.

This module contains Pydantic models and dataclasses
for Data ingestion and preprocessing
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BaseDataIngestion(BaseModel):
    """Base model for data_ingestion."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

        from_attributes = True


class DataIngestionCreate(BaseModel):
    """Model for creating data_ingestion."""
    pass


class DataIngestionRead(BaseModel):
    """Model for reading data_ingestion."""
    pass


class DataIngestionUpdate(BaseModel):
    """Model for updating data_ingestion."""
    pass
