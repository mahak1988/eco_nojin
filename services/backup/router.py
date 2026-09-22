"""Backup/Restore API Router."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.backup.service import BackupService
from services.backup.schemas import (
    BackupConfigCreate,
    BackupConfigUpdate,
    BackupConfigResponse,
    BackupJobResponse,
    RestoreRequest,
    RestoreResponse,
    BackupSummary,
)

router = APIRouter(prefix="/api/v1/backup", tags=["backup"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_backup_service(db: AsyncSession = Depends(get_db)) -> BackupService:
    return BackupService(db)


# =============================================================================
# Backup Configs
# =============================================================================


@router.post("/configs", response_model=BackupConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_config(
    data: BackupConfigCreate,
    service: BackupService = Depends(get_backup_service),
):
    """Create a new backup configuration."""
    config = await service.create_config(data)
    return BackupConfigResponse.model_validate(config)


@router.get("/configs", response_model=List[BackupConfigResponse])
async def list_backup_configs(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: BackupService = Depends(get_backup_service),
):
    """List backup configurations."""
    configs = await service.list_configs(enabled=enabled, page=page, page_size=page_size)
    return [BackupConfigResponse.model_validate(c) for c in configs]


@router.get("/configs/{config_id}", response_model=BackupConfigResponse)
async def get_backup_config(
    config_id: str,
    service: BackupService = Depends(get_backup_service),
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
    service: BackupService = Depends(get_backup_service),
):
    """Update a backup configuration."""
    config = await service.update_config(config_id, update)
    if not config:
        raise HTTPException(status_code=404, detail="Backup configuration not found")
    return BackupConfigResponse.model_validate(config)


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_config(
    config_id: str,
    service: BackupService = Depends(get_backup_service),
):
    """Delete a backup configuration."""
    success = await service.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup configuration not found")


@router.post("/configs/{config_id}/enable", response_model=BackupConfigResponse)
async def enable_backup_config(
    config_id: str,
    service: BackupService = Depends(get_backup_service),
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
    service: BackupService = Depends(get_backup_service),
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
    config_id: str = Query(..., description="Backup configuration ID"),
    backup_type: str = Query("full", description="Backup type (full, incremental, differential)"),
    triggered_by: str = Query("manual", description="Trigger source"),
    service: BackupService = Depends(get_backup_service),
):
    """Create and start a backup job."""
    job = await service.create_job(config_id, backup_type, triggered_by)
    # Start the backup in background
    import asyncio

    asyncio.create_task(service.run_backup(str(job.id)))
    return BackupJobResponse.model_validate(job)


@router.get("/jobs", response_model=List[BackupJobResponse])
async def list_backup_jobs(
    config_id: Optional[str] = Query(None, description="Filter by config ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: BackupService = Depends(get_backup_service),
):
    """List backup jobs."""
    jobs = await service.list_jobs(
        config_id=config_id, status=status, page=page, page_size=page_size
    )
    return [BackupJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/recent", response_model=List[BackupJobResponse])
async def get_recent_backup_jobs(
    limit: int = Query(10, ge=1, le=50, description="Number of recent jobs"),
    service: BackupService = Depends(get_backup_service),
):
    """Get recent backup jobs."""
    jobs = await service.get_recent_jobs(limit)
    return [BackupJobResponse.model_validate(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=BackupJobResponse)
async def get_backup_job(
    job_id: str,
    service: BackupService = Depends(get_backup_service),
):
    """Get a backup job by ID."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return BackupJobResponse.model_validate(job)


@router.post("/jobs/{job_id}/run")
async def run_backup_job(
    job_id: str,
    service: BackupService = Depends(get_backup_service),
):
    """Execute a backup job."""
    try:
        job = await service.run_backup(job_id)
        return BackupJobResponse.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/cancel", response_model=BackupJobResponse)
async def cancel_backup_job(
    job_id: str,
    service: BackupService = Depends(get_backup_service),
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
    service: BackupService = Depends(get_backup_service),
):
    """Create a restore job from a backup."""
    try:
        restore = await service.create_restore(data)
        # Start restore in background
        import asyncio

        asyncio.create_task(service.run_restore(str(restore.id)))
        return RestoreResponse.model_validate(restore)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/restore/{restore_id}", response_model=RestoreResponse)
async def get_restore(
    restore_id: str,
    service: BackupService = Depends(get_backup_service),
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
    service: BackupService = Depends(get_backup_service),
):
    """Get backup summary statistics."""
    return await service.get_job_stats()
