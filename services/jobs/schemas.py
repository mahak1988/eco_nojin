"""Pydantic schemas for Compute Jobs API."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class JobCreate(BaseModel):
    """Request to create a compute job."""
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., min_length=1, max_length=200)
    job_type: str = Field(..., min_length=1, max_length=100)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    max_runtime_seconds: int = Field(3600, ge=60, le=86400)
    max_memory_mb: int = Field(1024, ge=64, le=16384)
    max_cpu_cores: int = Field(1, ge=1, le=16)
    max_retries: int = Field(0, ge=0, le=10)
    docker_image: Optional[str] = Field(None, max_length=255)
    command: Optional[str] = Field(None, max_length=500)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    working_directory: Optional[str] = Field(None, max_length=500)
    callback_url: Optional[str] = Field(None, max_length=500)
    callback_secret: Optional[str] = Field(None, max_length=255)
    created_by: Optional[str] = Field(None, max_length=255)


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    priority_score: int
    queue_position: Optional[int]
    worker_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    runtime_seconds: Optional[int]
    retry_count: int
    progress_percent: int
    progress_message: Optional[str]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    output_artifact_urls: List[str]
    log_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobStatusUpdate(BaseModel):
    """Update job status (worker → API)."""
    model_config = ConfigDict(extra="forbid")
    
    status: Literal["running", "completed", "failed", "cancelled", "timeout"]
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    progress_message: Optional[str] = Field(None, max_length=500)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    output_artifact_urls: Optional[List[str]] = None
    log_url: Optional[str] = None
    runtime_seconds: Optional[int] = None


class JobEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    job_id: str
    event_type: str
    message: Optional[str]
    progress_percent: Optional[int]
    # API contract keeps the public key name `metadata`; the ORM attribute is
    # `event_metadata` (SQLAlchemy reserves the name `metadata`).
    event_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="event_metadata",
        serialization_alias="metadata",
    )
    created_at: datetime


class JobStatsResponse(BaseModel):
    """Job statistics summary."""
    total: int
    pending: int
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int
    timeout: int
    avg_runtime_seconds: Optional[float]
    success_rate: Optional[float]