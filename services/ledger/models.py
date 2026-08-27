"""
Data models for ledger module.

This module contains Pydantic models and dataclasses
for Transaction ledger service
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseLedger(BaseModel):
    """Base model for ledger."""

    id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

    model_config = ConfigDict(from_attributes=True)


class LedgerCreate(BaseModel):
    """Model for creating ledger."""
    pass


class LedgerRead(BaseModel):
    """Model for reading ledger."""
    pass


class LedgerUpdate(BaseModel):
    """Model for updating ledger."""
    pass
