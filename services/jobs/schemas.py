"""Pydantic schemas for Compute Jobs API."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class JobCreate(BaseModel):
    """Request to create a compute job."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    job_type: str = Field(..., min_length=1, max_length=100)
    input_data: dict[str, Any] = Field(default_factory=dict)
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    max_runtime_seconds: int = Field(3600, ge=60, le=86400)
    max_memory_mb: int = Field(1024, ge=64, le=16384)
    max_cpu_cores: int = Field(1, ge=1, le=16)
    max_retries: int = Field(0, ge=0, le=10)
    docker_image: str | None = Field(None, max_length=255)
    command: str | None = Field(None, max_length=500)
    environment_variables: dict[str, str] = Field(default_factory=dict)
    working_directory: str | None = Field(None, max_length=500)
    callback_url: str | None = Field(None, max_length=500)
    callback_secret: str | None = Field(None, max_length=255)
    created_by: str | None = Field(None, max_length=255)


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    priority_score: int
    queue_position: int | None
    worker_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    runtime_seconds: int | None
    retry_count: int
    progress_percent: int
    progress_message: str | None
    output_data: dict[str, Any]
    error_message: str | None
    output_artifact_urls: list[str]
    log_url: str | None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobStatusUpdate(BaseModel):
    """Update job status (worker → API)."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["running", "completed", "failed", "cancelled", "timeout"]
    progress_percent: int | None = Field(None, ge=0, le=100)
    progress_message: str | None = Field(None, max_length=500)
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    output_artifact_urls: list[str] | None = None
    log_url: str | None = None
    runtime_seconds: int | None = None


class JobEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    event_type: str
    message: str | None
    progress_percent: int | None
    # API contract keeps the public key name `metadata`; the ORM attribute is
    # `event_metadata` (SQLAlchemy reserves the name `metadata`).
    event_metadata: dict[str, Any] = Field(
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
    avg_runtime_seconds: float | None
    success_rate: float | None
