"""
Data models for finance module.

This module contains Pydantic models and dataclasses
for Financial analysis and economic modeling
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BaseFinance(BaseModel):
    """Base model for finance."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class FinanceCreate(BaseModel):
    """Model for creating finance."""
    pass


class FinanceRead(BaseModel):
    """Model for reading finance."""
    pass


class FinanceUpdate(BaseModel):
    """Model for updating finance."""
    pass
