"""Compute Jobs API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.jobs.schemas import (
    JobCreate,
    JobEventResponse,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
    JobStatusUpdate,
)
from services.jobs.service import ComputeJobService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_job_service(db: AsyncSession = Depends(get_db)) -> ComputeJobService:
    return ComputeJobService(db)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    service: ComputeJobService = Depends(get_job_service),
):
    """Create a new compute job."""
    job = await service.create_job(data)
    return JobResponse.model_validate(job)


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Get job queue statistics."""
    return await service.get_stats()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: str | None = Query(None, description="Filter by status"),
    job_type: str | None = Query(None, description="Filter by job type"),
    priority: str | None = Query(None, description="Filter by priority"),
    created_by: str | None = Query(None, description="Filter by creator"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """List compute jobs with filtering and pagination."""
    return await service.list_jobs(
        status=status,
        job_type=job_type,
        priority=priority,
        created_by=created_by,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Get a compute job by ID."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.get("/{job_id}/events", response_model=list[JobEventResponse])
async def get_job_events(
    job_id: str,
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Get all events for a job."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return await service.get_job_events(job_id)


@router.get("/{job_id}/queue-position")
async def get_queue_position(
    job_id: str,
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Get current queue position for a pending/queued job."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    position = await service.get_queue_position(job_id)
    if position is None:
        raise HTTPException(status_code=400, detail="Job is not in queue (not pending/queued)")
    return {"job_id": job_id, "queue_position": position}


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Update job status (called by workers)."""
    job = await service.update_job_status(job_id, update)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Cancel a pending/queued/running job."""
    success = await service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already terminal")
    job = await service.get_job(job_id)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Retry a failed/timeout/cancelled job."""
    try:
        job = await service.retry_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobResponse.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/summary", response_model=JobStatsResponse)
async def get_job_stats_summary(
    service: ComputeJobService = Depends(get_compute_job_service),
):
    """Get job queue statistics summary."""
    return await service.get_stats()
