"""Compute Jobs API Router."""
import logging
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import User
from services.api_gateway.auth import ADMIN_ROLES, require_user
from services.api_gateway.errors import safe_detail_for_status
from services.jobs.engine_bridge import submit_engine_job
from services.jobs.schemas import (
    EngineJobAccepted,
    EngineJobRequest,
    JobCreate,
    JobEventResponse,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
    JobStatusUpdate,
)
from services.jobs.service import ComputeJobService, job_to_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_job_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ComputeJobService:
    return ComputeJobService(db)


def _is_admin(user: User) -> bool:
    return str(getattr(user, "role", "")) in ADMIN_ROLES


async def _require_visible_job(
    service: ComputeJobService, job_id: str, user: User
):
    """A job is visible to its creator (and to admins) — nobody else.

    A foreign job answers 404 rather than 403 so the endpoint does not confirm
    which job ids exist; a job carries ``input_data``/``output_data`` and
    ``error_message`` that belong to its owner.
    """
    job = await service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    owner = str(getattr(job, "created_by", "") or "")
    if owner and owner != str(user.id) and not _is_admin(user):
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _engine_job_accepted(job: Any, model_id: str) -> EngineJobAccepted:
    """The 202 body for a job row — submitted now, or replayed from an earlier one.

    The body is read off the row rather than rebuilt from the request, so
    what the caller is told matches what the queue holds: the status is the
    state at accept time, and ``created_by`` is the id the job is really
    filed under.
    """
    return EngineJobAccepted(
        job_id=str(job.id),
        status=job.status.value,
        model_id=model_id,
        created_by=job.created_by,
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Create a new compute job (recorded under the caller)."""
    job = await service.create_job(data, user_id=str(user.id))
    return job_to_response(job)


@router.post(
    "/engine",
    response_model=EngineJobAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_engine_job_endpoint(
    data: EngineJobRequest,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """Submit a heavy engine computation as a background job (P13).

    Answers ``202 Accepted`` with the job id: the model has **not** run, and
    the body is the tracking handle rather than a result. The computation
    happens on the worker (``services/jobs/worker.py``), and its outcome is
    read from ``GET /api/v1/jobs/{job_id}`` — the same endpoint every other
    job uses, so nothing about a result is duplicated here.

    The route requires an authenticated caller, and the job is recorded
    under that caller's id (``created_by``), so a user can only ever see and
    retry their own submissions through the filters the list endpoint already
    supports.

    ``Idempotency-Key`` is honoured when the client sends one: a retry of the
    same submit while the original job is still open answers with the
    **existing** job id instead of starting a second computation. Once the
    original job reaches a terminal state the next submit is a new
    computation, which is what a retry outside the retry window means.
    """
    user_id = str(getattr(user, "id", "")) or None

    existing = await service.find_active_engine_job(
        user_id=user_id, idempotency_key=idempotency_key
    )
    if existing is not None:
        logger.info(
            "engine job %s replayed for user %s (Idempotency-Key)",
            existing.id,
            user_id,
        )
        return _engine_job_accepted(existing, data.model_id)

    job_id = await submit_engine_job(
        service,
        model_id=data.model_id,
        inputs=data.inputs,
        user_id=user_id,
        priority=data.priority,
        parameters=data.parameters,
        idempotency_key=idempotency_key,
    )
    job = await service.get_job(job_id)
    if job is None:  # pragma: no cover - the row was just committed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_detail_for_status(ValueError(), 500),
        )
    return _engine_job_accepted(job, data.model_id)


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Queue statistics. Admins see the whole queue; others see their own counts."""
    if not _is_admin(user):
        # A caller's own counts: list_jobs is already scope-filterable, and the
        # aggregate queue view (throughput, totals) is an operator's view.
        mine = await service.list_jobs(
            created_by=str(user.id), page=1, page_size=100
        )
        by_status: dict[str, int] = {}
        for entry in mine.items:
            by_status[str(entry.status)] = by_status.get(str(entry.status), 0) + 1
        return JobStatsResponse(
            total=mine.total,
            pending=by_status.get("pending", 0),
            queued=by_status.get("queued", 0),
            running=by_status.get("running", 0),
            completed=by_status.get("completed", 0),
            failed=by_status.get("failed", 0),
            cancelled=by_status.get("cancelled", 0),
            timeout=by_status.get("timeout", 0),
            avg_runtime_seconds=None,
            success_rate=None,
        )
    return await service.get_stats()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    job_type: Annotated[str | None, Query(description="Filter by job type")] = None,
    priority: Annotated[str | None, Query(description="Filter by priority")] = None,
    created_by: Annotated[str | None, Query(description="Filter by creator")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    service: Annotated[ComputeJobService, Depends(get_job_service)] = None,
    user: Annotated[User, Depends(require_user)] = None,
):
    """List compute jobs. A caller's list is scoped to their own submissions;
    only an approver may list (or filter by) another creator."""
    caller = str(user.id)
    if not _is_admin(user):
        created_by = caller
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
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Get a job by ID (the caller's own, or any for an admin)."""
    job = await _require_visible_job(service, job_id, user)
    return job_to_response(job)


@router.get("/{job_id}/events", response_model=list[JobEventResponse])
async def get_job_events(
    job_id: str,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Get all events for a job (the caller's own, or any for an admin)."""
    await _require_visible_job(service, job_id, user)
    return await service.get_job_events(job_id)


@router.get("/{job_id}/queue-position")
async def get_queue_position(
    job_id: str,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Get current queue position for a pending/queued job."""
    await _require_visible_job(service, job_id, user)

    position = await service.get_queue_position(job_id)
    if position is None:
        raise HTTPException(status_code=400, detail="Job is not in queue (not pending/queued)")
    return {"job_id": job_id, "queue_position": position}


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Update job status. Worker-driven transitions are an operator's action;
    an owner may still record their own job's terminal states."""
    job = await _require_visible_job(service, job_id, user)
    if not _is_admin(user) and str(getattr(job, "created_by", "")) != str(user.id):
        raise HTTPException(status_code=404, detail="Job not found")
    job = await service.update_job_status(job_id, update)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_response(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Cancel a pending/queued/running job (its owner, or an admin)."""
    await _require_visible_job(service, job_id, user)
    success = await service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already terminal")
    job = await service.get_job(job_id)
    return job_to_response(job)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    service: Annotated[ComputeJobService, Depends(get_job_service)],
    user: Annotated[User, Depends(require_user)],
):
    """Retry a failed/timeout/cancelled job (its owner, or an admin)."""
    await _require_visible_job(service, job_id, user)
    try:
        job = await service.retry_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job_to_response(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/stats/summary", response_model=JobStatsResponse)
async def get_job_stats_summary(
    service: Annotated[ComputeJobService, Depends(get_job_service)],
):
    """Get job queue statistics summary."""
    return await service.get_stats()
