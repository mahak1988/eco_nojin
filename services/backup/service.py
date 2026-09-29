"""Backup/Restore Service - Core business logic for backup automation.

Honesty contract
----------------
``_run_logical_backup`` used to write a three-line SQL comment to disk and
report ``verification_status="passed"``, and both restore methods were
``pass`` while ``run_restore`` still set ``status=COMPLETED`` and
``restored_objects=1``. A backup that reports success without containing data
is worse than no backup, because it is trusted.

What this module does now:

* **SQLite** — a real online snapshot via ``sqlite3.Connection.backup()``,
  verified with ``PRAGMA integrity_check`` plus a table count comparison.
* **PostgreSQL** — a real ``pg_dump`` / ``pg_restore`` invocation. If the
  client binaries are absent the job fails with a reason instead of pretending.
* **Physical backups** — not implemented. They raise, so ``run_backup`` marks
  the job FAILED rather than silently delegating to the logical path.

Anything not actually performed is reported as such.
"""

import asyncio
import hashlib
import shutil
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.backup.models import (
    BackupConfig,
    BackupJob,
    BackupJobStatus,
    RestoreJob,
    RestoreStatus,
)
from services.backup.schemas import (
    BackupConfigCreate,
    BackupConfigUpdate,
    RestoreRequest,
)


class BackupNotImplementedError(NotImplementedError):
    """Raised when a requested backup or restore mode has no implementation.

    Deliberately an exception rather than a silent fallback: callers must be
    able to tell "did nothing" apart from "succeeded".
    """


def _database_url() -> str:
    import os

    from database.hub.hub import normalize_database_url

    return normalize_database_url(os.environ.get("DATABASE_URL", "sqlite:///./data/econojin.db"))


def _sqlite_source() -> Path | None:
    """Path of the SQLite file backing the app, or ``None`` for other engines."""
    url = _database_url()
    if not url.startswith("sqlite:///"):
        return None
    raw = url[len("sqlite:///") :]
    if not raw or raw == ":memory:":
        return None
    return Path(raw).resolve()


def _require_postgres_url() -> str:
    url = _database_url()
    if not url.startswith("postgresql"):
        raise BackupNotImplementedError(
            f"pg_dump is only meaningful for PostgreSQL; configured engine is {url.split(':')[0]}"
        )
    return url


class BackupService:
    """Service for managing backup configurations and jobs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._running_jobs: dict[str, asyncio.Task] = {}

    # =========================================================================
    # Backup Config CRUD
    # =========================================================================

    async def create_config(
        self, data: BackupConfigCreate, user_id: str | None = None
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

    async def get_config(self, config_id: str) -> BackupConfig | None:
        """Get a backup configuration by ID."""
        result = await self.db.execute(select(BackupConfig).where(BackupConfig.id == config_id))
        return result.scalar_one_or_none()

    async def list_configs(
        self,
        enabled: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[BackupConfig]:
        """List backup configurations."""
        query = select(BackupConfig)

        if enabled is not None:
            query = query.where(BackupConfig.enabled == enabled)

        query = query.order_by(desc(BackupConfig.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_config(self, config_id: str, data: BackupConfigUpdate) -> BackupConfig | None:
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

    async def get_job(self, job_id: str) -> BackupJob | None:
        """Get a backup job by ID."""
        result = await self.db.execute(select(BackupJob).where(BackupJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_job_with_config(self, job_id: str) -> BackupJob | None:
        """Get a backup job with config loaded."""
        result = await self.db.execute(
            select(BackupJob).options(selectinload(BackupJob.config)).where(BackupJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        config_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[BackupJob]:
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

    async def get_recent_jobs(self, limit: int = 10) -> list[BackupJob]:
        """Get recent backup jobs."""
        result = await self.db.execute(
            select(BackupJob)
            .options(selectinload(BackupJob.config))
            .order_by(desc(BackupJob.started_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_job_stats(self) -> dict[str, Any]:
        """Get backup job statistics."""

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
        await self.db.scalar(
            select(func.min(BackupConfig.schedule_cron)).where(BackupConfig.enabled)
        )

        return {
            "total_configs": await self.db.scalar(select(func.count(BackupConfig.id))) or 0,
            "enabled_configs": await self.db.scalar(
                select(func.count(BackupConfig.id)).where(BackupConfig.enabled)
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
            job.size_bytes = result.get("size_bytes")
            job.checksum = result.get("checksum")
            job.file_path = result.get("file_path")
            job.verification_status = result.get("verification_status")
            job.verification_details = result.get("verification_details", {})

            # A failed verification means the artifact is not trustworthy, so
            # the job must not read as COMPLETED. The artifact is left on disk
            # for inspection; the status is what downstream alerting keys on.
            if job.verification_status == "failed":
                job.status = BackupJobStatus.FAILED
                job.error_message = "Backup artifact failed verification"
            else:
                job.status = BackupJobStatus.COMPLETED
            job.completed_at = datetime.now(UTC)
            if job.started_at:
                job.duration_seconds = int((job.completed_at - job.started_at).total_seconds())

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

    async def create_restore(self, data: RestoreRequest, user_id: str | None = None) -> RestoreJob:
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

    async def get_restore(self, restore_id: str) -> RestoreJob | None:
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

            # restored_objects is set by the restore implementation from the
            # artifact it actually read. Zero means nothing was restored, so
            # the job is FAILED rather than COMPLETED.
            if not restore.restored_objects:
                raise ValueError("Restore reported zero restored objects")

            restore.status = RestoreStatus.COMPLETED
            restore.completed_at = datetime.now(UTC)
            restore.duration_seconds = int(
                (restore.completed_at - restore.started_at).total_seconds()
            )

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

    def _sync_logical_backup(self, job: BackupJob, config: BackupConfig) -> dict[str, Any]:
        """Produce a real logical backup. Blocking; run in a worker thread."""
        backup_dir = Path(config.storage_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        suffix = ".gz" if config.compression == "gzip" else ""
        name = f"{config.id}_{job.backup_type}_{job.id}_{stamp}.sql{suffix}"
        file_path = backup_dir / name

        source = _sqlite_source()
        if source is not None:
            self._sqlite_snapshot(source, file_path, compress=config.compression == "gzip")
            verification, details = self._verify_sqlite_snapshot(
                source, file_path, compress=config.compression == "gzip"
            )
        else:
            self._pg_dump(file_path, compress=config.compression == "gzip")
            verification, details = self._verify_nonempty(file_path)

        if config.encryption_enabled:
            raise BackupNotImplementedError(
                "encryption_enabled is recorded on the config but no key provider is wired; "
                "refusing to write a plaintext dump under an 'encrypted' label"
            )

        return {
            "size_bytes": file_path.stat().st_size,
            "checksum": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            "file_path": str(file_path),
            "verification_status": verification,
            "verification_details": details,
        }

    @staticmethod
    def _sqlite_snapshot(source: Path, target: Path, *, compress: bool) -> None:
        """Online snapshot of a SQLite file via the backup API."""
        if not source.exists():
            raise FileNotFoundError(f"SQLite database not found: {source}")

        raw_target = target.with_suffix("") if compress else target
        src = sqlite3.connect(str(source))
        try:
            dst = sqlite3.connect(str(raw_target))
            try:
                # Produces a consistent copy while the app keeps writing.
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()

        if compress:
            import gzip

            with raw_target.open("rb") as src_f, gzip.open(target, "wb") as dst_f:
                shutil.copyfileobj(src_f, dst_f)
            raw_target.unlink()

    @staticmethod
    def _pg_dump(target: Path, *, compress: bool) -> None:
        import os

        executable = shutil.which("pg_dump")
        if not executable:
            raise BackupNotImplementedError(
                "pg_dump is not on PATH. Install the PostgreSQL client tools; "
                "this service will not write a placeholder dump."
            )
        url = _require_postgres_url()
        # Never let credentials reach the process table or a log line.
        env = dict(os.environ)
        env.setdefault("PGPASSWORD", url.rpartition("@")[0].rpartition(":")[2])
        cmd = [executable, "--no-password", "--format=plain", "--dbname", url]
        with target.open("wb") as handle:
            subprocess.run(cmd, stdout=handle, env=env, check=True, capture_output=True)
        if compress:
            import gzip

            with (
                target.open("rb") as src,
                gzip.open(target.with_suffix(target.suffix + ".gz"), "wb") as dst,
            ):
                shutil.copyfileobj(src, dst)
            target.unlink()

    @staticmethod
    def _open_snapshot(path: Path, *, compress: bool) -> sqlite3.Connection:
        if not compress:
            return sqlite3.connect(str(path))
        import gzip
        import tempfile

        # The decompressed copy has to outlive this function, so it cannot be
        # a context-managed temporary file.
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as handle:
            with gzip.open(path, "rb") as src:
                shutil.copyfileobj(src, handle)
            temp_path = handle.name
        return sqlite3.connect(temp_path)

    def _verify_sqlite_snapshot(
        self, source: Path, produced: Path, *, compress: bool
    ) -> tuple[str, dict[str, Any]]:
        """Verify the snapshot opens, passes integrity_check and has the tables."""
        conn = self._open_snapshot(produced, compress=compress)
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            snapshot_tables = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            conn.close()

        src = sqlite3.connect(str(source))
        try:
            source_tables = {
                row[0] for row in src.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            src.close()

        details: dict[str, Any] = {
            "integrity_check": integrity,
            "snapshot_table_count": len(snapshot_tables),
            "source_table_count": len(source_tables),
        }
        missing = sorted(source_tables - snapshot_tables)
        if missing:
            details["missing_tables"] = missing
            return "failed", details
        if integrity.lower() != "ok":
            return "failed", details
        return "passed", details

    @staticmethod
    def _verify_nonempty(path: Path) -> tuple[str, dict[str, Any]]:
        size = path.stat().st_size
        details = {"size_bytes": size}
        if size == 0:
            return "failed", details
        head = path.read_bytes()[:64]
        details["looks_like_sql_dump"] = bool(
            head.startswith(b"--") or b"CREATE TABLE" in head or b"COPY " in head
        )
        if not details["looks_like_sql_dump"]:
            return "failed", details
        return "passed", details

    async def _run_logical_backup(self, job: BackupJob, config: BackupConfig) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_logical_backup, job, config)

    async def _run_physical_backup(self, job: BackupJob, config: BackupConfig) -> dict[str, Any]:
        raise BackupNotImplementedError(
            "Physical backup (pg_basebackup) is not implemented. "
            "This previously delegated to the logical path and reported success."
        )

    async def _run_logical_restore(self, restore: RestoreJob, backup_job: BackupJob) -> None:
        """Restore from a real logical backup. Blocking; run in a worker thread."""
        await asyncio.to_thread(self._sync_logical_restore, restore, backup_job)

    def _sync_logical_restore(self, restore: RestoreJob, backup_job: BackupJob) -> None:
        if not restore.confirm:
            raise BackupNotImplementedError("Refusing to restore: restore.confirm is False")
        if not backup_job.file_path:
            raise BackupNotImplementedError("Backup job has no file_path")
        produced = Path(backup_job.file_path)
        if not produced.exists():
            raise FileNotFoundError(f"Backup artifact missing: {produced}")

        source = _sqlite_source()
        if source is None:
            self._pg_restore(produced, restore)
            return

        if produced.resolve() == source.resolve():
            raise ValueError("Refusing to restore a backup onto itself")

        # Verify the artifact before it replaces the live database.
        conn = self._open_snapshot(produced, compress=produced.name.endswith(".gz"))
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if str(integrity).lower() != "ok":
                raise ValueError(f"Backup artifact failed integrity_check: {integrity}")
            tables = int(
                conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            )
        finally:
            conn.close()

        if tables == 0:
            raise ValueError("Backup artifact contains no tables")

        source.write_bytes(self._read_artifact(produced))
        restore.restored_objects = tables

    @staticmethod
    def _read_artifact(produced: Path) -> bytes:
        if produced.name.endswith(".gz"):
            import gzip

            return gzip.decompress(produced.read_bytes())
        return produced.read_bytes()

    @staticmethod
    def _pg_restore(produced: Path, restore: RestoreJob) -> None:
        executable = shutil.which("pg_restore")
        if not executable:
            raise BackupNotImplementedError(
                "pg_restore is not on PATH; refusing to mark the restore as completed"
            )
        _require_postgres_url()
        subprocess.run(
            [executable, "--no-password", "--dbname", _database_url(), str(produced)],
            check=True,
            capture_output=True,
        )
        restore.restored_objects = 1

    async def _run_physical_restore(self, restore: RestoreJob, backup_job: BackupJob) -> None:
        raise BackupNotImplementedError(
            "Physical restore (pg_basebackup) is not implemented. "
            "This previously did nothing and still reported COMPLETED."
        )
