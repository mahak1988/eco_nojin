"""Compute Job Service - Core business logic for job queue management."""

import heapq
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.jobs.models import ComputeJob, JobEvent, JobPriority, JobStatus
from services.jobs.schemas import (
    JobCreate,
    JobEventResponse,
    JobListResponse,
    JobResponse,
    JobStatsResponse,
    JobStatusUpdate,
)


def _as_utc(value: datetime | None) -> datetime:
    """``value`` as an aware UTC datetime, ``now`` when it is missing.

    SQLite (and any naive-column backend) hands back a naive ``created_at`` /
    ``started_at``, and subtracting that from an aware "now" raises
    ``TypeError: can't subtract offset-naive and offset-aware datetimes``.
    The completion path in :meth:`update_job_status` already guards against
    this; the age calculation and the cancel path did not, and both blew up
    on the same reloaded row.
    """
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _coerce_job_id(job_id: Any) -> Any:
    """A job id the ``UUID`` columns accept, from whatever the caller holds.

    ``compute_jobs.id`` and ``job_events.job_id`` are Postgres UUID columns,
    while the HTTP layer carries the id as the *string* the client sent.
    Binding that string fails on SQLite (``StatementError``: ``'str' object
    has no attribute 'hex'``) and is work Postgres has to do anyway, so every
    lookup normalises here first. A value that is not a UUID at all is passed
    through untouched: a malformed id must still reach the database and be
    reported as not-found rather than as a 500 raised from the Python side.
    """
    if isinstance(job_id, uuid.UUID):
        return job_id
    try:
        return uuid.UUID(str(job_id))
    except (ValueError, AttributeError, TypeError):
        return job_id


def job_to_response(job: ComputeJob) -> JobResponse:
    """Serialise a job for the API.

    The `id` column is a UUID object on every backend while the response
    schema declares `str`; `model_validate` on the ORM object fails the
    type check (this is why the list endpoint used to 500 in production and
    return nothing on SQLite). The id is coerced explicitly and the rest of
    the row is validated as-is.

    Every route that answers with a `JobResponse` must go through this. The
    list path always did; the per-job routes answered with
    ``JobResponse.model_validate(job)`` directly and therefore raised a
    ``ValidationError`` on the id (a 500) on every read.
    """
    allowed = set(JobResponse.model_fields)
    payload = {
        column.name: getattr(job, column.name)
        for column in job.__table__.columns
        if column.name in allowed
    }
    payload["id"] = str(job.id)
    return JobResponse.model_validate(payload)


class ComputeJobService:
    """Service for managing compute jobs with priority queue."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory priority queue for fast scheduling
        self._queue: list[tuple[int, datetime, str]] = []  # (priority_score, created_at, job_id)
        self._queue_set: set[str] = set()
        self._initialized = False

    def _calculate_priority_score(self, job: ComputeJob) -> int:
        """Calculate composite priority score for queue ordering.

        Higher score = higher priority (processed first).
        """
        priority_weights = {
            "critical": 10000,
            "high": 1000,
            "normal": 100,
            "low": 10,
        }
        base = priority_weights.get(job.priority.value, 100)
        # Age bonus (older jobs get slight priority boost)
        age_seconds = (datetime.now(UTC) - _as_utc(job.created_at)).total_seconds()
        age_bonus = min(int(age_seconds / 3600), 100)  # Max 100 points for age
        return base * 100 + age_bonus - job.retry_count * 10

    async def _rebuild_queue(self):
        """Rebuild priority queue from database."""
        self._queue.clear()
        self._queue_set.clear()

        result = await self.db.execute(
            select(ComputeJob)
            .where(ComputeJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED]))
            .order_by(desc(ComputeJob.priority_score), ComputeJob.created_at)
        )
        jobs = result.scalars().all()

        for job in jobs:
            score = self._calculate_priority_score(job)
            job.priority_score = score
            heapq.heappush(self._queue, (-score, job.created_at, str(job.id)))
            self._queue_set.add(str(job.id))

        self._initialized = True

    def _enqueue_job(self, job: ComputeJob):
        """Add job to priority queue."""
        score = self._calculate_priority_score(job)
        job.priority_score = score
        heapq.heappush(self._queue, (-score, job.created_at, str(job.id)))
        self._queue_set.add(str(job.id))

    def _dequeue_job(self) -> str | None:
        """Remove and return highest priority job ID."""
        while self._queue:
            _, _, job_id = heapq.heappop(self._queue)
            if job_id in self._queue_set:
                self._queue_set.remove(job_id)
                return job_id
        return None

    # =========================================================================
    # Job CRUD
    # =========================================================================

    async def create_job(self, data: JobCreate, user_id: str | None = None) -> ComputeJob:
        """Create a new compute job."""
        # Calculate priority score
        priority_enum = JobPriority(data.priority)
        job = ComputeJob(
            name=data.name,
            job_type=data.job_type,
            input_data=data.input_data,
            priority=priority_enum,
            max_runtime_seconds=data.max_runtime_seconds,
            max_memory_mb=data.max_memory_mb,
            max_cpu_cores=data.max_cpu_cores,
            max_retries=data.max_retries,
            docker_image=data.docker_image,
            command=data.command,
            environment_variables=data.environment_variables,
            working_directory=data.working_directory,
            callback_url=data.callback_url,
            callback_secret=data.callback_secret,
            created_by=data.created_by or user_id,
        )

        # P13: this used to `self.db.add(data)` — the *schema* object, not the
        # model — so every create raised ``UnmappedInstanceError``. The
        # engine-bridge tests caught it; the model is what gets persisted.
        self.db.add(job)
        await self.db.flush()

        # Add to queue if not running/failed/cancelled
        if job.status in (JobStatus.PENDING, JobStatus.QUEUED):
            self._enqueue_job(job)

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(self, job_id: str) -> ComputeJob | None:
        """Get a job by ID with events loaded."""
        result = await self.db.execute(
            select(ComputeJob)
            .options(selectinload(ComputeJob.events))
            .where(ComputeJob.id == _coerce_job_id(job_id))
        )
        return result.scalar_one_or_none()

    async def get_job_response(self, job_id: str) -> JobResponse | None:
        """Get a job by ID as response schema."""
        job = await self.get_job(job_id)
        if job:
            return job_to_response(job)
        return None

    async def list_jobs(
        self,
        status: str | list[str] | tuple[str, ...] | None = None,
        job_type: str | None = None,
        priority: str | None = None,
        created_by: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> JobListResponse:
        """List jobs with filters and pagination.

        ``status`` accepts one status or several (the queue itself treats
        ``PENDING`` and ``QUEUED`` as equally drainable — see
        ``_rebuild_queue`` — so a drain must be able to ask for both).
        """
        statuses: list[str] | None = None
        if status:
            statuses = [status] if isinstance(status, str) else list(status)
        query = select(ComputeJob)

        if statuses:
            query = query.where(ComputeJob.status.in_(statuses))
        if job_type:
            query = query.where(ComputeJob.job_type == job_type)
        if priority:
            query = query.where(ComputeJob.priority == priority)
        if created_by:
            query = query.where(ComputeJob.created_by == created_by)

        # Total count
        from sqlalchemy import func

        count_query = select(func.count()).select_from(ComputeJob)
        if statuses:
            count_query = count_query.where(ComputeJob.status.in_(statuses))
        if job_type:
            count_query = count_query.where(ComputeJob.job_type == job_type)
        if priority:
            count_query = count_query.where(ComputeJob.priority == priority)
        if created_by:
            count_query = count_query.where(ComputeJob.created_by == created_by)

        total = (
            await self.db.scalar(
                select(func.count()).select_from(
                    select(1)
                    .where(ComputeJob.id == ComputeJob.id)
                    .where(ComputeJob.id.isnot(None))
                    .subquery()
                )
            )
            or 0
        )

        # Simpler count
        total_result = await self.db.execute(select(func.count(ComputeJob.id)))
        total = total_result.scalar() or 0

        # Pagination
        query = query.order_by(desc(ComputeJob.priority_score), ComputeJob.created_at)
        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)

        items = [job_to_response(j) for j in result.scalars().all()]

        return JobListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def update_job_status(self, job_id: str, update: JobStatusUpdate) -> ComputeJob | None:
        """Update job status (called by workers)."""
        job = await self.get_job(job_id)
        if not job:
            return None

        old_status = job.status
        new_status = JobStatus(update.status)
        job.status = new_status

        if update.progress_percent is not None:
            job.progress_percent = update.progress_percent
        if update.progress_message is not None:
            job.progress_message = update.progress_message
        if update.output_data is not None:
            job.output_data = update.output_data
        if update.error_message is not None:
            job.error_message = update.error_message
        if update.output_artifact_urls is not None:
            job.output_artifact_urls = update.output_artifact_urls
        if update.log_url is not None:
            job.log_url = update.log_url
        if update.runtime_seconds is not None:
            job.runtime_seconds = update.runtime_seconds

        # Handle status transitions
        if new_status == JobStatus.RUNNING and old_status in (JobStatus.PENDING, JobStatus.QUEUED):
            job.started_at = datetime.now(UTC)
        elif new_status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        ):
            job.completed_at = datetime.now(UTC)
            if job.started_at:
                # SQLite (and any naive-column backend) hands back a naive
                # ``started_at``; subtracting it from an aware "now" raises
                # "can't subtract offset-naive and offset-aware datetimes" and
                # every completion used to fail on that line.
                runtime = datetime.now(UTC) - _as_utc(job.started_at)
                job.runtime_seconds = int(runtime.total_seconds())

        # Add event (single insert: the previous code created it twice)
        self.db.add(
            JobEvent(
                job_id=job.id,
                event_type=new_status.value,
                message=f"Status changed to {new_status.value}",
                progress_percent=update.progress_percent,
                event_metadata={"old_status": old_status.value, "new_status": new_status.value},
            )
        )

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending/queued/running job."""
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.TIMEOUT,
        ):
            return False  # Already terminal

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        if job.started_at:
            job.runtime_seconds = int(
                (datetime.now(UTC) - _as_utc(job.started_at)).total_seconds()
            )

        self.db.add(
            JobEvent(
                job_id=job.id,
                event_type="cancelled",
                message="Job cancelled by user",
            )
        )

        await self.db.commit()
        return True

    async def retry_job(self, job_id: str) -> ComputeJob | None:
        """Retry a failed/timeout/cancelled job."""
        job = await self.get_job(job_id)
        if not job:
            return None

        if job.status not in (JobStatus.FAILED, JobStatus.TIMEOUT, JobStatus.CANCELLED):
            return None  # Can only retry terminal failed states

        if job.retry_count >= job.max_retries:
            raise ValueError(f"Max retries ({job.max_retries}) exceeded")

        # Reset for retry
        job.status = JobStatus.PENDING
        job.retry_count += 1
        job.last_retry_at = datetime.now(UTC)
        job.retry_reason = "Manual retry"
        job.error_message = None
        job.progress_percent = 0
        job.progress_message = None
        job.started_at = None
        job.completed_at = None
        job.runtime_seconds = None
        job.output_data = {}
        job.error_message = None
        job.output_artifact_urls = []
        job.log_url = None

        self.db.add(
            JobEvent(
                job_id=job.id,
                event_type="retry",
                message=f"Retry #{job.retry_count}",
            )
        )

        # Re-queue
        self._enqueue_job(job)

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def find_active_engine_job(
        self, *, user_id: str | None, idempotency_key: str
    ) -> ComputeJob | None:
        """This caller's still-open engine job for one idempotency key.

        Deduplication for the ``Idempotency-Key`` contract: a client that
        retries an engine submit (a flaky network, not a new intent) finds its
        previous job instead of starting a second computation for the same
        model request.

        Returns ``None`` when there is nothing to dedupe against — no
        authenticated caller, or every earlier job for the key already reached
        a terminal state. A retry *after* a completion is a new computation,
        not a replay, and must not be answered with the old job.

        The key is matched in Python rather than in SQL: the envelope is a
        generic ``JSON`` column, and a JSON path expression is spelled
        differently on SQLite (``json_extract``) and PostgreSQL (``->``). The
        query stays bounded to the most recent open jobs of the same caller
        and type, so this is a small in-memory scan rather than a table scan.
        """
        if not idempotency_key or not user_id:
            return None

        result = await self.db.execute(
            select(ComputeJob)
            .where(
                ComputeJob.job_type == "engine_model",
                ComputeJob.created_by == user_id,
                ComputeJob.status.in_(
                    (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING)
                ),
            )
            .order_by(desc(ComputeJob.created_at))
            .limit(50)
        )
        for job in result.scalars().all():
            if (job.input_data or {}).get("idempotency_key") == idempotency_key:
                return job
        return None

    async def get_job_events(self, job_id: str) -> list[dict[str, Any]]:
        """Get all events for a job."""
        result = await self.db.execute(
            select(JobEvent)
            .where(JobEvent.job_id == _coerce_job_id(job_id))
            .order_by(JobEvent.created_at)
        )
        events = result.scalars().all()
        return [JobEventResponse.model_validate(e) for e in events]

    async def get_queue_position(self, job_id: str) -> int | None:
        """Get current queue position for a pending/queued job."""
        job = await self.get_job(job_id)
        if not job or job.status not in (JobStatus.PENDING, JobStatus.QUEUED):
            return None

        # Count jobs with higher priority or same priority but earlier
        result = await self.db.execute(
            select(func.count(ComputeJob.id)).where(
                and_(
                    ComputeJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED]),
                    or_(
                        ComputeJob.priority_score > job.priority_score,
                        and_(
                            ComputeJob.priority_score == job.priority_score,
                            ComputeJob.created_at < job.created_at,
                        ),
                    ),
                )
            )
        )
        return (result.scalar() or 0) + 1

    async def get_stats(self) -> JobStatsResponse:
        """Get job queue statistics."""

        # Count by status
        status_counts = await self.db.execute(
            select(ComputeJob.status, func.count(ComputeJob.id)).group_by(ComputeJob.status)
        )
        counts = {str(status): count for status, count in status_counts.all()}

        # Average runtime for completed jobs
        avg_runtime_result = await self.db.execute(
            select(func.avg(ComputeJob.runtime_seconds)).where(
                and_(
                    ComputeJob.status == JobStatus.COMPLETED,
                    ComputeJob.runtime_seconds.isnot(None),
                )
            )
        )
        avg_runtime = avg_runtime_result.scalar()

        # Success rate
        total_terminal = sum(
            counts.get(s.value, 0)
            for s in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT]
        )
        completed = counts.get(JobStatus.COMPLETED.value, 0)
        success_rate = completed / total_terminal if total_terminal > 0 else None

        return JobStatsResponse(
            total=sum(counts.values()),
            pending=counts.get(JobStatus.PENDING.value, 0),
            queued=counts.get(JobStatus.QUEUED.value, 0),
            running=counts.get(JobStatus.RUNNING.value, 0),
            completed=counts.get(JobStatus.COMPLETED.value, 0),
            failed=counts.get(JobStatus.FAILED.value, 0),
            cancelled=counts.get(JobStatus.CANCELLED.value, 0),
            timeout=counts.get(JobStatus.TIMEOUT.value, 0),
            avg_runtime_seconds=avg_runtime,
            success_rate=round(success_rate * 100, 2) if success_rate else None,
        )
