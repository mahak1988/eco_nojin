"""Pydantic schemas for Reporting"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    SALES = "sales"
    TOURISM = "tourism"
    LANDSCAPE = "landscape"
    CARBON = "carbon"
    COMPREHENSIVE = "comprehensive"

class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportCreate(BaseModel):
    report_type: ReportType
    title: str = Field(min_length=3, max_length=255)
    parameters: dict[str, Any] | None = None
    generated_by: str | None = None

class ReportRead(BaseModel):
    id: str
    report_type: ReportType
    title: str
    status: ReportStatus
    parameters: dict[str, Any] | None
    result_data: dict[str, Any] | None
    file_path: str | None
    created_at: datetime
    completed_at: datetime | None
