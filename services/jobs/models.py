"""Database models for Compute Jobs."""

import enum
import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    JSON,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from database.base import Base


class JobStatus(str, enum.Enum):
    """Job execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(str, enum.Enum):
    """Job priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ComputeJob(Base):
    """Long-running compute job tracking."""

    __tablename__ = "compute_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job identification
    name = Column(String(200), nullable=False, index=True)
    job_type = Column(
        String(100), nullable=False, index=True
    )  # e.g., "carbon_simulation", "erosion_analysis"

    # Status and priority
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.NORMAL, nullable=False, index=True)

    # Input/Output
    input_data = Column(JSON, nullable=False, default=dict)
    output_data = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    # Execution tracking
    priority_score = Column(Integer, default=0, index=True)  # Computed for queue ordering
    queue_position = Column(Integer, nullable=True)

    # Execution context
    docker_image = Column(String(255), nullable=True)
    command = Column(Text, nullable=True)
    environment_variables = Column(JSON, nullable=False, default=dict)
    working_directory = Column(String(500), nullable=True)

    # Resource limits
    max_runtime_seconds = Column(Integer, default=3600, nullable=False)
    max_memory_mb = Column(Integer, default=1024, nullable=False)
    max_cpu_cores = Column(Integer, default=1, nullable=False)

    # Execution tracking
    worker_id = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    runtime_seconds = Column(Integer, nullable=True)

    # Retry logic
    max_retries = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    retry_reason = Column(Text, nullable=True)

    # Progress tracking
    progress_percent = Column(Integer, default=0, nullable=False)
    progress_message = Column(String(500), nullable=True)

    # Output artifacts
    output_artifact_urls = Column(JSON, nullable=False, default=list)
    log_url = Column(String(500), nullable=True)

    # Callback
    callback_url = Column(String(500), nullable=True)
    callback_secret = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by = Column(String(255), nullable=True)

    # Relationships
    events = relationship(
        "JobEvent",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobEvent.created_at",
    )

    __table_args__ = (
        Index("ix_compute_job_status_priority", "status", "priority_score"),
        Index("ix_compute_job_created", "created_at"),
        Index("ix_compute_job_type_status", "job_type", "status"),
        Index("ix_compute_job_worker", "worker_id"),
    )


class JobEvent(Base):
    """Event log for job lifecycle."""

    __tablename__ = "job_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    job_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("compute_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        String(50), nullable=False, index=True
    )  # queued, started, progress, completed, failed, cancelled
    message = Column(String(500), nullable=True)
    progress_percent = Column(Integer, nullable=True)
    # NOTE: `metadata` is reserved by SQLAlchemy's Declarative API, therefore the
    # Python attribute is `event_metadata` while the DB column name stays `metadata`.
    event_metadata = Column("metadata", JSON, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    # Relationship
    job = relationship("ComputeJob", back_populates="events")

    __table_args__ = (Index("ix_job_event_job_created", "job_id", "created_at"),)
