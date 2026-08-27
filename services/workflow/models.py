"""
Data models for workflow module.

This module contains Pydantic models and dataclasses
for Workflow management service
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseWorkflow(BaseModel):
    """Base model for workflow."""

    id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict()

    model_config = ConfigDict(from_attributes=True)


class WorkflowCreate(BaseModel):
    """Model for creating workflow."""
    pass


class WorkflowRead(BaseModel):
    """Model for reading workflow."""
    pass


class WorkflowUpdate(BaseModel):
    """Model for updating workflow."""
    pass
