"""Compute Job Service - Core business logic for job queue management."""

import uuid
import heapq
import asyncio
from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any, Set
from contextlib import asynccontextmanager

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.hub import hub
from services.jobs.models import ComputeJob, JobEvent, JobStatus, JobPriority
from services.jobs.schemas import (
    JobCreate,
    JobResponse,
    JobListResponse,
    JobStatusUpdate,
    JobEventResponse,
    JobStatsResponse,
)


class ComputeJobService:
    """Service for managing compute jobs with priority queue."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory priority queue for fast scheduling
        self._queue: List[tuple[int, datetime, str]] = []  # (priority_score, created_at, job_id)
        self._queue_set: Set[str] = set()
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
        age_seconds = (datetime.now(UTC) - job.created_at).total_seconds()
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

    def _dequeue_job(self) -> Optional[str]:
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

    async def create_job(self, data: JobCreate, user_id: Optional[str] = None) -> ComputeJob:
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

        self.db.add(data)
        await self.db.flush()

        # Add to queue if not running/failed/cancelled
        if data.status in (JobStatus.PENDING, JobStatus.QUEUED):
            self._enqueue_job(data)

        await self.db.commit()
        await self.db.refresh(data)
        return data

    async def get_job(self, job_id: str) -> Optional[ComputeJob]:
        """Get a job by ID with events loaded."""
        result = await self.db.execute(
            select(ComputeJob)
            .options(selectinload(ComputeJob.events))
            .where(ComputeJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_response(self, job_id: str) -> Optional[JobResponse]:
        """Get a job by ID as response schema."""
        job = await self.get_job(job_id)
        if job:
            return JobResponse.model_validate(job)
        return None

    async def list_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        priority: Optional[str] = None,
        created_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> JobListResponse:
        """List jobs with filters and pagination."""
        query = select(ComputeJob)

        if status:
            query = query.where(ComputeJob.status == JobStatus(status))
        if job_type:
            query = query.where(ComputeJob.job_type == job_type)
        if priority:
            query = query.where(ComputeJob.priority == priority)
        if created_by:
            query = query.where(ComputeJob.created_by == created_by)

        # Total count
        from sqlalchemy import func

        count_query = select(func.count()).select_from(ComputeJob)
        if status:
            count_query = count_query.where(ComputeJob.status == status)
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
        jobs = result.scalars().all()

        items = [JobResponse.model_validate(j) for j in result.scalars().all()]

        return JobListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def update_job_status(self, job_id: str, update: JobStatusUpdate) -> Optional[ComputeJob]:
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
                job.runtime_seconds = int((datetime.now(UTC) - job.started_at).total_seconds())

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
        await self.db.refresh(data)
        return data

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
            job.runtime_seconds = int((datetime.now(UTC) - job.started_at).total_seconds())

        self.db.add(
            JobEvent(
                job_id=job.id,
                event_type="cancelled",
                message="Job cancelled by user",
            )
        )

        await self.db.commit()
        return True

    async def retry_job(self, job_id: str) -> Optional[ComputeJob]:
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

    async def get_job_events(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all events for a job."""
        result = await self.db.execute(
            select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at)
        )
        events = result.scalars().all()
        return [JobEventResponse.model_validate(e) for e in events]

    async def get_queue_position(self, job_id: str) -> Optional[int]:
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
        from sqlalchemy import case

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
