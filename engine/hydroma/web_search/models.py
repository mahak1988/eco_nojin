"""
Data models for web_search module.

This module contains Pydantic models and dataclasses
for Web search and information retrieval
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseWebSearch(BaseModel):
    """Base model for web_search."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class WebSearchCreate(BaseModel):
    """Model for creating web_search."""
    pass


class WebSearchRead(BaseModel):
    """Model for reading web_search."""
    pass


class WebSearchUpdate(BaseModel):
    """Model for updating web_search."""
    pass
