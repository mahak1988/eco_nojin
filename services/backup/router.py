"""Backup/Restore API Router."""
import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.auth import require_admin
from services.api_gateway.errors import safe_detail_for_status
from services.backup.schemas import (
    BackupConfigCreate,
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupJobResponse,
    BackupSummary,
    RestoreRequest,
    RestoreResponse,
)
from services.backup.service import BackupService

# SEC-06: every route on this router is admin-only. The endpoints can write an
# arbitrary path (backup storage), overwrite the live database (restore) and
# read database artifacts — mounting this router without an authorization
# dependency would turn one ``include_router`` call into an unauthenticated
# arbitrary-file-write primitive. The dependency is declared on the router so
# a new endpoint can never forget it; ``tests/test_backup_router_is_gated.py``
# fails if any route loses it (or if the router is ever mounted without it).
router = APIRouter(
    prefix="/api/v1/backup",
    tags=["backup"],
    dependencies=[Depends(require_admin)],
)

# The event loop only holds a weak reference to a running task, so a task
# that is never referenced can be garbage-collected mid-flight. Keep the
# strong references here and drop them once each task finishes.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_backup_service(db: Annotated[AsyncSession, Depends(get_db)]) -> BackupService:
    return BackupService(db)


# =============================================================================
# Backup Configs
# =============================================================================


@router.post("/configs", response_model=BackupConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_config(
    data: BackupConfigCreate,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Create a new backup configuration."""
    config = await service.create_config(data)
    return BackupConfigResponse.model_validate(config)


@router.get("/configs", response_model=list[BackupConfigResponse])
async def list_backup_configs(
    enabled: Annotated[bool | None, Query(description="Filter by enabled status")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    service: Annotated[BackupService, Depends(get_backup_service)] = None,
):
    """List backup configurations."""
    configs = await service.list_configs(enabled=enabled, page=page, page_size=page_size)
    return [BackupConfigResponse.model_validate(c) for c in configs]


@router.get("/configs/{config_id}", response_model=BackupConfigResponse)
async def get_backup_config(
    config_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Get a backup configuration by ID."""
    config = await service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Backup configuration not found")
    return BackupConfigResponse.model_validate(config)


@router.patch("/configs/{config_id}", response_model=BackupConfigResponse)
async def update_backup_config(
    config_id: str,
    update: BackupConfigUpdate,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Update a backup configuration."""
    config = await service.update_config(config_id, update)
    if not config:
        raise HTTPException(status_code=404, detail="Backup configuration not found")
    return BackupConfigResponse.model_validate(config)


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_config(
    config_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Delete a backup configuration."""
    success = await service.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup configuration not found")


@router.post("/configs/{config_id}/enable", response_model=BackupConfigResponse)
async def enable_backup_config(
    config_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Enable a backup configuration."""
    success = await service.enable_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup configuration not found")
    config = await service.get_config(config_id)
    return BackupConfigResponse.model_validate(config)


@router.post("/configs/{config_id}/disable", response_model=BackupConfigResponse)
async def disable_backup_config(
    config_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Disable a backup configuration."""
    success = await service.disable_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup configuration not found")
    config = await service.get_config(config_id)
    return BackupConfigResponse.model_validate(config)


# =============================================================================
# Backup Jobs
# =============================================================================


@router.post("/jobs", response_model=BackupJobResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_job(
    config_id: Annotated[str, Query(description="Backup configuration ID")],
    backup_type: Annotated[
    str, Query(description="Backup type (full, incremental, differential)")
] = "full",
    triggered_by: Annotated[str, Query(description="Trigger source")] = "manual",
    service: Annotated[BackupService, Depends(get_backup_service)] = None,
):
    """Create and start a backup job."""
    job = await service.create_job(config_id, backup_type, triggered_by)
    # Start the backup in background
    _spawn(service.run_backup(str(job.id)))
    return BackupJobResponse.model_validate(job)


@router.get("/jobs", response_model=list[BackupJobResponse])
async def list_backup_jobs(
    config_id: Annotated[str | None, Query(description="Filter by config ID")] = None,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    service: Annotated[BackupService, Depends(get_backup_service)] = None,
):
    """List backup jobs."""
    jobs = await service.list_jobs(
        config_id=config_id, status=status, page=page, page_size=page_size
    )
    return [BackupJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/recent", response_model=list[BackupJobResponse])
async def get_recent_backup_jobs(
    limit: Annotated[int, Query(ge=1, le=50, description="Number of recent jobs")] = 10,
    service: Annotated[BackupService, Depends(get_backup_service)] = None,
):
    """Get recent backup jobs."""
    jobs = await service.get_recent_jobs(limit)
    return [BackupJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=BackupJobResponse)
async def get_backup_job(
    job_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Get a backup job by ID."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return BackupJobResponse.model_validate(job)


@router.post("/jobs/{job_id}/run")
async def run_backup_job(
    job_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Execute a backup job."""
    try:
        job = await service.run_backup(job_id)
        return BackupJobResponse.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/jobs/{job_id}/cancel", response_model=BackupJobResponse)
async def cancel_backup_job(
    job_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Cancel a pending/running backup job."""
    success = await service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already terminal")
    job = await service.get_job(job_id)
    return BackupJobResponse.model_validate(job)


# =============================================================================
# Restore
# =============================================================================


@router.post("/restore", response_model=RestoreResponse, status_code=status.HTTP_201_CREATED)
async def create_restore(
    data: RestoreRequest,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Create a restore job from a backup.

    SEC-06: restore copies bytes over a live database, so it runs only with an
    explicit ``confirm: true`` in the request body (the schema default is
    False). The router is admin-only via its router-level dependency.
    """
    if not data.confirm:
        raise HTTPException(
            status_code=400,
            detail="confirmation required: set confirm=true to restore over a live database",
        )
    try:
        restore = await service.create_restore(data)
        # Start restore in background
        _spawn(service.run_restore(str(restore.id)))
        return RestoreResponse.model_validate(restore)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/restore/{restore_id}", response_model=RestoreResponse)
async def get_restore(
    restore_id: str,
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Get a restore job by ID."""
    restore = await service.get_restore(restore_id)
    if not restore:
        raise HTTPException(status_code=404, detail="Restore job not found")
    return RestoreResponse.model_validate(restore)


# =============================================================================
# Summary
# =============================================================================


@router.get("/summary", response_model=BackupSummary)
async def get_backup_summary(
    service: Annotated[BackupService, Depends(get_backup_service)],
):
    """Get backup summary statistics."""
    return await service.get_job_stats()
