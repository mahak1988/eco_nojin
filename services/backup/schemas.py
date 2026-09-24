"""Schemas for Backup/Restore Service."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BackupType(StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    LOGICAL = "logical"  # pg_dump style
    PHYSICAL = "physical"  # pg_basebackup style


class BackupStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BackupConfigCreate(BaseModel):
    """Request to create a backup configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)

    # Backup type and scope
    backup_type: Literal["full", "incremental", "differential", "logical", "physical"] = "full"
    databases: list[str] = Field(
        default_factory=list, description="Database names to backup (empty = all)"
    )
    include_schemas: list[str] = Field(
        default_factory=list, description="Specific schemas to include"
    )
    exclude_tables: list[str] = Field(default_factory=list, description="Tables to exclude")

    # Schedule
    schedule_cron: str = Field("0 2 * * *", description="Cron expression for schedule (UTC)")
    timezone: str = Field("UTC", description="Timezone for schedule")

    # Retention
    retention_days: int = Field(30, ge=1, le=3650, description="Retention period in days")
    max_backups: int = Field(100, ge=1, le=1000, description="Maximum backups to keep")

    # Storage
    storage_backend: Literal["local", "s3", "gcs", "azure"] = "local"
    storage_path: str = Field("./backups", description="Local path or S3 bucket path")
    storage_config: dict[str, Any] = Field(
        default_factory=dict, description="Backend-specific config"
    )

    # Compression & Encryption
    compression: Literal["none", "gzip", "zstd", "lz4"] = "gzip"
    encryption_enabled: bool = False
    encryption_key_id: str | None = Field(None, max_length=255)

    # Verification
    verify_after_backup: bool = True
    verify_checksum: bool = True

    # Notifications
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_channels: list[str] = Field(default_factory=list)
    notification_config: dict[str, Any] = Field(default_factory=dict)

    # Advanced
    parallel_jobs: int = Field(1, ge=1, le=8, description="Parallel backup jobs")
    timeout_seconds: int = Field(3600, ge=60, description="Backup timeout")

    enabled: bool = True


class BackupConfigUpdate(BaseModel):
    """Request to update a backup configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    backup_type: Literal["full", "incremental", "differential", "logical", "physical"] | None = None
    databases: list[str] | None = None
    include_schemas: list[str] | None = None
    exclude_tables: list[str] | None = None
    schedule_cron: str | None = None
    timezone: str | None = None
    retention_days: int | None = Field(None, ge=1, le=3650)
    max_backups: int | None = Field(None, ge=1, le=1000)
    storage_backend: Literal["local", "s3", "gcs", "azure"] | None = None
    storage_path: str | None = None
    storage_config: dict[str, Any] | None = None
    compression: Literal["none", "gzip", "zstd", "lz4"] | None = None
    encryption_enabled: bool | None = None
    encryption_key_id: str | None = None
    verify_after_backup: bool | None = None
    verify_checksum: bool | None = None
    notify_on_success: bool | None = None
    notify_on_failure: bool | None = None
    notification_channels: list[str] | None = None
    notification_config: dict[str, Any] | None = None
    parallel_jobs: int | None = Field(None, ge=1, le=8)
    timeout_seconds: int | None = Field(None, ge=60)
    enabled: bool | None = None


class BackupConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    backup_type: str
    databases: list[str]
    schedule_cron: str
    timezone: str
    retention_days: int
    max_backups: int
    storage_backend: str
    storage_path: str
    compression: str
    encryption_enabled: bool
    verify_after_backup: bool
    verify_checksum: bool
    notify_on_success: bool
    notify_on_failure: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime


class BackupJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BackupJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    config_id: str
    config_name: str
    backup_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None
    size_bytes: int | None
    checksum: str | None
    file_path: str | None
    error_message: str | None
    databases: list[str]
    verification_status: str | None
    created_at: datetime


class RestoreRequest(BaseModel):
    """Request to restore from a backup."""

    model_config = ConfigDict(extra="forbid")

    backup_job_id: str = Field(..., description="Backup job to restore from")
    target_database: str = Field(
        ..., min_length=1, max_length=100, description="Target database name"
    )
    target_schema: str | None = Field(None, max_length=100, description="Target schema (optional)")

    # Restore options
    clean_before_restore: bool = Field(False, description="Drop existing objects before restore")
    single_transaction: bool = Field(True, description="Run restore in single transaction")
    disable_triggers: bool = Field(False, description="Disable triggers during restore")
    no_owner: bool = Field(False, description="Skip setting object ownership")
    no_privileges: bool = Field(False, description="Skip privilege restoration")

    # Point-in-time recovery (for physical backups)
    recovery_target_time: datetime | None = None
    recovery_target_xid: str | None = None
    recovery_target_lsn: str | None = None

    # Safety
    confirm: bool = Field(True, description="Confirmation required")


class RestoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    backup_job_id: str
    target_database: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None
    restored_objects: int
    error_message: str | None
    created_at: datetime


class BackupSummary(BaseModel):
    """Backup summary statistics."""

    total_configs: int
    enabled_configs: int
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_today: int
    failed_today: int
    total_storage_bytes: int
    last_backup_at: datetime | None
    next_scheduled_at: datetime | None
    storage_used_percent: float | None
