"""P13 — heavy compute leaves the request path and stays inspectable.

Note: ``compute_jobs.id`` is a Postgres ``UUID`` column, so SQLite rejects
str-bound ids; the tests pass ``uuid.UUID`` objects, as Postgres deployments
bind them.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import User
from services.jobs.engine_bridge import run_next_engine_job, submit_engine_job
from services.jobs.models import JobStatus
from services.jobs.schemas import JobCreate
from services.jobs.service import ComputeJobService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(User(id="user-1", email="a@example.test", password_hash="x", full_name="A"))
        await session.commit()
        yield session
    await engine.dispose()


async def test_submit_returns_without_running_the_model(session):
    service = ComputeJobService(session)
    job_id = await submit_engine_job(
        service,
        model_id="SOIL_CEC",
        inputs={"clay_pct": 22, "organic_matter_pct": 3, "ph": 7.1},
        user_id="user-1",
    )
    job = await service.get_job(uuid.UUID(job_id))
    assert job is not None
    assert job.status == JobStatus.PENDING
    assert job.input_data["model_id"] == "SOIL_CEC"


async def test_the_worker_runs_the_next_job_and_records_the_result(session):
    service = ComputeJobService(session)
    job_id = await submit_engine_job(
        service,
        model_id="SOIL_CEC",
        inputs={"clay_pct": 22, "organic_matter_pct": 3, "ph": 7.1},
        user_id="user-1",
    )
    result = await run_next_engine_job(service)
    assert result is not None
    assert result.job_id == job_id
    job = await service.get_job(uuid.UUID(job_id))
    assert job.status in (JobStatus.COMPLETED, JobStatus.FAILED)
    # whichever way the engine answered, the record carries the answer — no
    # silent inline execution and no lost failure
    assert job.output_data or job.error_message


async def test_a_gateway_error_marks_the_job_failed(session):
    """A GatewayError must not be laundered into a completed job."""
    service = ComputeJobService(session)
    job_id = await submit_engine_job(
        service,
        model_id="NOPE_NOT_A_MODEL",
        inputs={},
        user_id="user-1",
    )
    result = await run_next_engine_job(service)
    assert result is not None
    assert result.status == JobStatus.FAILED
    job = await service.get_job(uuid.UUID(job_id))
    assert job.status == JobStatus.FAILED
    assert job.error_message
    # no result may be recorded on a failed job — an empty output, not a
    # swallowed GatewayError string presented as the answer
    assert not job.output_data


async def test_non_engine_jobs_are_not_drained(session):
    """The worker only drains ``engine_model`` jobs."""
    service = ComputeJobService(session)
    await service.create_job(
        JobCreate(
            name="generic", job_type="carbon_simulation", input_data={}
        ),
        user_id="user-1",
    )
    assert await run_next_engine_job(service) is None


async def test_a_queued_engine_job_is_drained(session):
    """The queue treats PENDING and QUEUED as equally drainable.

    ``JobStatusUpdate`` refuses a direct transition to ``queued`` (only the
    queue maintenance writes it), so the test seeds the status on the model —
    exactly the state a producer outside this service leaves behind.
    """
    from services.jobs.models import ComputeJob

    service = ComputeJobService(session)
    job_id = await submit_engine_job(
        service,
        model_id="CANON-004",
        inputs={"precipitation": 25, "curve_number": 75},
        user_id="user-1",
    )
    job = await session.get(ComputeJob, uuid.UUID(job_id))
    job.status = JobStatus.QUEUED  # the service holds the enum on the model
    await session.commit()

    result = await run_next_engine_job(service)
    assert result is not None
    job = await service.get_job(uuid.UUID(job_id))
    assert job.status in (JobStatus.COMPLETED, JobStatus.FAILED)


async def test_an_empty_queue_returns_none(session):
    service = ComputeJobService(session)
    assert await run_next_engine_job(service) is None
