"""Database models for Backup/Restore Service."""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from database.base import Base


class BackupType(enum.StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    LOGICAL = "logical"
    PHYSICAL = "physical"


class BackupJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class RestoreStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupConfig(Base):
    """Backup configuration."""

    __tablename__ = "backup_configs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Backup type and scope
    backup_type = Column(String(20), default="full", nullable=False)
    databases = Column(JSON, nullable=False, default=list)
    include_schemas = Column(JSON, nullable=False, default=list)
    exclude_tables = Column(JSON, nullable=False, default=list)

    # Schedule
    schedule_cron = Column(String(100), default="0 2 * * *", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Retention
    retention_days = Column(Integer, default=30, nullable=False)
    max_backups = Column(Integer, default=100, nullable=False)

    # Storage
    storage_backend = Column(String(20), default="local", nullable=False)
    storage_path = Column(String(500), default="./backups", nullable=False)
    storage_config = Column(JSON, nullable=False, default=dict)

    # Compression & Encryption
    compression = Column(String(20), default="gzip", nullable=False)
    encryption_enabled = Column(Boolean, default=False, nullable=False)
    encryption_key_id = Column(String(255), nullable=True)

    # Verification
    verify_after_backup = Column(Boolean, default=True, nullable=False)
    verify_checksum = Column(Boolean, default=True, nullable=False)

    # Notifications
    notify_on_success = Column(Boolean, default=False, nullable=False)
    notify_on_failure = Column(Boolean, default=True, nullable=False)
    notification_channels = Column(JSON, nullable=False, default=list)
    notification_config = Column(JSON, nullable=False, default=dict)

    # Advanced
    parallel_jobs = Column(Integer, default=1, nullable=False)
    timeout_seconds = Column(Integer, default=3600, nullable=False)

    # State
    enabled = Column(Boolean, default=True, nullable=False, index=True)

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
    jobs = relationship("BackupJob", back_populates="config", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_backup_config_enabled", "enabled"),
        Index("ix_backup_config_schedule", "enabled", "schedule_cron"),
    )


class BackupJob(Base):
    """Backup job execution record."""

    __tablename__ = "backup_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    config_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backup_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job identification
    backup_type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)

    # Output
    size_bytes = Column(BigInteger, nullable=True)
    checksum = Column(String(128), nullable=True)  # SHA256
    file_path = Column(String(500), nullable=True)

    # Databases backed up
    databases = Column(JSON, nullable=False, default=list)

    # Verification
    verification_status = Column(String(20), nullable=True)  # passed, failed, skipped
    verification_details = Column(JSON, nullable=False, default=dict)

    # Error
    error_message = Column(Text, nullable=True)

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
    triggered_by = Column(String(255), nullable=True)  # manual, scheduled, api

    # Relationships
    config = relationship("BackupConfig", back_populates="jobs")

    __table_args__ = (
        Index("ix_backup_job_config_status", "config_id", "status"),
        Index("ix_backup_job_started", "started_at"),
    )


class RestoreJob(Base):
    """Restore job record."""

    __tablename__ = "restore_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    backup_job_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backup_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Target
    target_database = Column(String(100), nullable=False)
    target_schema = Column(String(100), nullable=True)

    # Options
    clean_before_restore = Column(Boolean, default=False)
    single_transaction = Column(Boolean, default=True)
    disable_triggers = Column(Boolean, default=False)
    no_owner = Column(Boolean, default=False)
    no_privileges = Column(Boolean, default=False)

    # Point-in-time recovery
    recovery_target_time = Column(DateTime(timezone=True), nullable=True)
    recovery_target_xid = Column(String(100), nullable=True)
    recovery_target_lsn = Column(String(100), nullable=True)

    # Status
    status = Column(String(20), default="pending", nullable=False, index=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Results
    restored_objects = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Safety
    confirm = Column(Boolean, default=True)

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

    __table_args__ = (
        Index("ix_restore_job_backup", "backup_job_id"),
        Index("ix_restore_job_status", "status"),
    )
