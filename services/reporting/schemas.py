"""Pydantic schemas for Reporting"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

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
    parameters: Optional[Dict[str, Any]] = None
    generated_by: Optional[str] = None

class ReportRead(BaseModel):
    id: str
    report_type: ReportType
    title: str
    status: ReportStatus
    parameters: Optional[Dict[str, Any]]
    result_data: Optional[Dict[str, Any]]
    file_path: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    