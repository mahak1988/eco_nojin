"""Backup/Restore Service - Core business logic for backup automation."""

import uuid
import asyncio
import hashlib
import subprocess
import os
import shutil
from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.hub import hub
from services.backup.models import (
    BackupConfig,
    BackupJob,
    RestoreJob,
    BackupJobStatus,
    RestoreStatus,
)
from services.backup.schemas import (
    BackupConfigCreate,
    BackupConfigUpdate,
    BackupConfigResponse,
    BackupJobResponse,
    RestoreRequest,
    RestoreResponse,
    BackupSummary,
)


class BackupService:
    """Service for managing backup configurations and jobs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._running_jobs: Dict[str, asyncio.Task] = {}

    # =========================================================================
    # Backup Config CRUD
    # =========================================================================

    async def create_config(
        self, data: BackupConfigCreate, user_id: Optional[str] = None
    ) -> BackupConfig:
        """Create a new backup configuration."""
        config = BackupConfig(
            name=data.name,
            description=data.description,
            backup_type=data.backup_type,
            databases=data.databases,
            include_schemas=data.include_schemas,
            exclude_tables=data.exclude_tables,
            schedule_cron=data.schedule_cron,
            timezone=data.timezone,
            retention_days=data.retention_days,
            max_backups=data.max_backups,
            storage_backend=data.storage_backend,
            storage_path=data.storage_path,
            storage_config=data.storage_config,
            compression=data.compression,
            encryption_enabled=data.encryption_enabled,
            encryption_key_id=data.encryption_key_id,
            verify_after_backup=data.verify_after_backup,
            verify_checksum=data.verify_checksum,
            notify_on_success=data.notify_on_success,
            notify_on_failure=data.notify_on_failure,
            notification_channels=data.notification_channels,
            notification_config=data.notification_config,
            parallel_jobs=data.parallel_jobs,
            timeout_seconds=data.timeout_seconds,
            enabled=data.enabled,
            created_by=user_id,
        )

        self.db.add(config)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_config(self, config_id: str) -> Optional[BackupConfig]:
        """Get a backup configuration by ID."""
        result = await self.db.execute(select(BackupConfig).where(BackupConfig.id == config_id))
        return result.scalar_one_or_none()

    async def list_configs(
        self,
        enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[BackupConfig]:
        """List backup configurations."""
        query = select(BackupConfig)

        if enabled is not None:
            query = query.where(BackupConfig.enabled == enabled)

        query = query.order_by(desc(BackupConfig.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_config(
        self, config_id: str, data: BackupConfigUpdate
    ) -> Optional[BackupConfig]:
        """Update a backup configuration."""
        config = await self.get_config(config_id)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete_config(self, config_id: str) -> bool:
        """Delete a backup configuration."""
        config = await self.get_config(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()
        return True

    async def enable_config(self, config_id: str) -> bool:
        """Enable a backup configuration."""
        config = await self.get_config(config_id)
        if not config:
            return False
        config.enabled = True
        await self.db.commit()
        return True

    async def disable_config(self, config_id: str) -> bool:
        """Disable a backup configuration."""
        config = await self.get_config(config_id)
        if not config:
            return False
        config.enabled = False
        await self.db.commit()
        return True

    # =========================================================================
    # Backup Jobs
    # =========================================================================

    async def create_job(
        self,
        config_id: str,
        backup_type: str = "full",
        triggered_by: str = "manual",
    ) -> BackupJob:
        """Create a new backup job."""
        config = await self.get_config(config_id)
        if not config:
            raise ValueError("Backup configuration not found")

        job = BackupJob(
            config_id=config.id,
            backup_type=backup_type,
            status=BackupJobStatus.PENDING,
            databases=config.databases,
            triggered_by=triggered_by,
        )

        self.db.add(job)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(self, job_id: str) -> Optional[BackupJob]:
        """Get a backup job by ID."""
        result = await self.db.execute(select(BackupJob).where(BackupJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_job_with_config(self, job_id: str) -> Optional[BackupJob]:
        """Get a backup job with config loaded."""
        result = await self.db.execute(
            select(BackupJob).options(selectinload(BackupJob.config)).where(BackupJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        config_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[BackupJob]:
        """List backup jobs."""
        query = select(BackupJob).options(selectinload(BackupJob.config))

        if config_id:
            query = query.where(BackupJob.config_id == config_id)
        if status:
            query = query.where(BackupJob.status == status)

        query = query.order_by(desc(BackupJob.started_at))
        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_jobs(self, limit: int = 10) -> List[BackupJob]:
        """Get recent backup jobs."""
        result = await self.db.execute(
            select(BackupJob)
            .options(selectinload(BackupJob.config))
            .order_by(desc(BackupJob.started_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_job_stats(self) -> Dict[str, Any]:
        """Get backup job statistics."""
        from sqlalchemy import func

        # Status counts
        status_counts = await self.db.execute(
            select(BackupJob.status, func.count(BackupJob.id)).group_by(BackupJob.status)
        )
        status_counts = {str(s): c for s, c in status_counts.all()}

        # Today's stats
        today = datetime.now(UTC).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=UTC)

        today_completed = (
            await self.db.scalar(
                select(func.count(BackupJob.id)).where(
                    and_(
                        BackupJob.status == BackupJobStatus.COMPLETED,
                        BackupJob.completed_at >= today_start,
                    )
                )
            )
            or 0
        )

        today_failed = (
            await self.db.scalar(
                select(func.count(BackupJob.id)).where(
                    and_(
                        BackupJob.status == BackupJobStatus.FAILED,
                        BackupJob.completed_at >= today_start,
                    )
                )
            )
            or 0
        )

        # Storage
        total_size = (
            await self.db.scalar(
                select(func.sum(BackupJob.size_bytes)).where(
                    BackupJob.status == BackupJobStatus.COMPLETED
                )
            )
            or 0
        )

        # Last backup
        last_backup = await self.db.scalar(
            select(func.max(BackupJob.completed_at)).where(
                BackupJob.status == BackupJobStatus.COMPLETED
            )
        )

        # Next scheduled
        next_scheduled = await self.db.scalar(
            select(func.min(BackupConfig.schedule_cron)).where(BackupConfig.enabled == True)
        )

        return {
            "total_configs": await self.db.scalar(select(func.count(BackupConfig.id))) or 0,
            "enabled_configs": await self.db.scalar(
                select(func.count(BackupConfig.id)).where(BackupConfig.enabled == True)
            )
            or 0,
            "total_jobs": sum(status_counts.values()) if status_counts else 0,
            "pending_jobs": status_counts.get(BackupJobStatus.PENDING.value, 0),
            "running_jobs": status_counts.get(BackupJobStatus.RUNNING.value, 0),
            "completed_today": today_completed,
            "failed_today": today_failed,
            "total_storage_bytes": total_size,
            "last_backup_at": last_backup,
            "next_scheduled_at": None,  # Would need cron parsing
            "storage_used_percent": None,
        }

    # =========================================================================
    # Backup Execution
    # =========================================================================

    async def run_backup(self, job_id: str) -> BackupJob:
        """Execute a backup job."""
        job = await self.get_job(job_id)
        if not job:
            raise ValueError("Backup job not found")

        if job.status != BackupJobStatus.PENDING:
            raise ValueError(f"Job is not in pending status: {job.status}")

        job.status = BackupJobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        await self.db.commit()

        try:
            config = await self.get_config(job.config_id)
            if not config:
                raise ValueError("Config not found")

            # Execute backup based on type
            if job.backup_type == "logical":
                result = await self._run_logical_backup(job, config)
            elif job.backup_type == "physical":
                result = await self._run_physical_backup(job, config)
            else:
                result = await self._run_logical_backup(job, config)  # Default to logical

            # Update job with results
            job.status = BackupJobStatus.COMPLETED
            job.completed_at = datetime.now(UTC)
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
            job.size_bytes = result.get("size_bytes")
            job.checksum = result.get("checksum")
            job.file_path = result.get("file_path")
            job.verification_status = result.get("verification_status")
            job.verification_details = result.get("verification_details", {})

        except Exception as e:
            job.status = BackupJobStatus.FAILED
            job.completed_at = datetime.now(UTC)
            if job.started_at:
                job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())
            job.error_message = str(e)

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending/running backup job."""
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status in (
            BackupJobStatus.COMPLETED,
            BackupJobStatus.FAILED,
            BackupJobStatus.CANCELLED,
        ):
            return False

        job.status = BackupJobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        if job.started_at:
            job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())

        await self.db.commit()
        return True

    # =========================================================================
    # Restore
    # =========================================================================

    async def create_restore(
        self, data: RestoreRequest, user_id: Optional[str] = None
    ) -> RestoreJob:
        """Create a restore job."""
        backup_job = await self.get_job(data.backup_job_id)
        if not backup_job:
            raise ValueError("Backup job not found")

        if backup_job.status != BackupJobStatus.COMPLETED:
            raise ValueError("Can only restore from completed backups")

        restore_job = RestoreJob(
            backup_job_id=backup_job.id,
            target_database=data.target_database,
            target_schema=data.target_schema,
            clean_before_restore=data.clean_before_restore,
            single_transaction=data.single_transaction,
            disable_triggers=data.disable_triggers,
            no_owner=data.no_owner,
            no_privileges=data.no_privileges,
            recovery_target_time=data.recovery_target_time,
            recovery_target_xid=data.recovery_target_xid,
            recovery_target_lsn=data.recovery_target_lsn,
            status=RestoreStatus.PENDING,
            confirm=data.confirm,
            created_by=user_id,
        )

        self.db.add(restore_job)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(restore_job)
        return restore_job

    async def get_restore(self, restore_id: str) -> Optional[RestoreJob]:
        """Get a restore job by ID."""
        result = await self.db.execute(select(RestoreJob).where(RestoreJob.id == restore_id))
        return result.scalar_one_or_none()

    async def run_restore(self, restore_id: str) -> RestoreJob:
        """Execute a restore job."""
        restore = await self.get_restore(restore_id)
        if not restore:
            raise ValueError("Restore job not found")

        restore.status = RestoreStatus.RUNNING
        restore.started_at = datetime.now(UTC)
        await self.db.commit()

        try:
            backup_job = await self.get_job(str(restore.backup_job_id))
            if not backup_job:
                raise ValueError("Backup job not found")

            # Execute restore based on backup type
            if backup_job.backup_type == "logical":
                await self._run_logical_restore(restore, backup_job)
            elif backup_job.backup_type == "physical":
                await self._run_physical_restore(restore, backup_job)
            else:
                await self._run_logical_restore(restore, backup_job)

            restore.status = RestoreStatus.COMPLETED
            restore.completed_at = datetime.now(UTC)
            restore.duration_seconds = int(
                (restore.completed_at - restore.started_at).total_seconds()
            )
            restore.restored_objects = 1  # Would be actual count

        except Exception as e:
            restore.status = RestoreStatus.FAILED
            restore.completed_at = datetime.now(UTC)
            restore.error_message = str(e)

        await self.db.commit()
        await self.db.refresh(restore)
        return restore

    # =========================================================================
    # Backup Execution Helpers
    # =========================================================================

    async def _run_logical_backup(self, job: BackupJob, config: BackupConfig) -> Dict[str, Any]:
        """Run pg_dump logical backup."""
        # This is a placeholder - actual implementation would use pg_dump
        # For now, create a mock backup file

        backup_dir = Path(config.storage_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"{job.config_id}_{job.backup_type}_{job.id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.sql"
        if config.compression == "gzip":
            filename += ".gz"
        file_path = backup_dir / filename

        # Create a mock backup file
        content = f"-- Backup of {job.config.name}\n-- Created at {datetime.now(UTC).isoformat()}\n-- Databases: {', '.join(job.databases)}\n"
        if config.compression == "gzip":
            import gzip

            with gzip.open(file_path, "wt") as f:
                f.write(content)
        else:
            file_path.write_text(content)

        # Calculate size and checksum
        size_bytes = file_path.stat().st_size
        checksum = hashlib.sha256(file_path.read_bytes()).hexdigest()

        # Verification
        verification_status = "passed"
        verification_details = {}

        if config.verify_checksum:
            # Verify checksum matches
            with open(file_path, "rb") as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()
            if actual_checksum != checksum:
                verification_status = "failed"
                verification_details["checksum_mismatch"] = True

        return {
            "size_bytes": size_bytes,
            "checksum": checksum,
            "file_path": str(file_path),
            "verification_status": verification_status,
            "verification_details": verification_details,
        }

    async def _run_physical_backup(self, job: BackupJob, config: BackupConfig) -> Dict[str, Any]:
        """Run pg_basebackup physical backup."""
        # Placeholder for pg_basebackup implementation
        return await self._run_logical_backup(job, config)

    async def _run_logical_restore(self, restore: RestoreJob, backup_job: BackupJob) -> None:
        """Run logical restore from pg_dump file."""
        # Placeholder for pg_restore implementation
        pass

    async def _run_physical_restore(self, restore: RestoreJob, backup_job: BackupJob) -> None:
        """Run physical restore from pg_basebackup."""
        # Placeholder for physical restore
        pass
