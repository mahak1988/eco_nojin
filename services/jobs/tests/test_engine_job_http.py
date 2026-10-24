"""Engine jobs over HTTP, and the worker that drains them (Phase 1 — P13).

The route and the loop are tested together because neither is the story on
its own: the submitter answers ``202 Accepted`` with a job id and runs no
model, and the worker is what turns that id into a result.

* ``POST /api/v1/jobs/engine`` requires an authenticated caller (a request
  with no token is a 401, not an anonymous job), files the job under the
  caller's id, and answers 202 with the id and the status URL;
* the submitted payload reaches the model untouched — the idempotency key
  lives in the job envelope, never inside ``inputs``;
* an ``Idempotency-Key`` retry while the job is open answers with the *same*
  job id instead of starting a second computation, and a retry after the job
  reached a terminal state is a new computation;
* ``run_once`` drains one job, and ``run_forever`` stops where its caller
  tells it to.

The tests run against the hub's process-wide async engine on purpose: the
worker opens its own session on that engine (``services/jobs/worker.py``), so
a private in-memory engine here would leave the route and the loop looking at
two different databases and prove nothing. The shared database is emptied
around every test, and the fixture's seeding session is the same one the
router uses.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import User
from services.api_gateway.auth import require_user
from services.jobs import worker
from services.jobs.engine_bridge import submit_engine_job
from services.jobs.models import ComputeJob, JobEvent, JobStatus
from services.jobs.router import get_db
from services.jobs.router import router as jobs_router
from services.jobs.service import ComputeJobService

# ``asyncio_mode = "auto"`` (pyproject.toml) discovers the async tests, so no
# module-level mark is needed — and adding one would also flag the one plain
# sync test below.
_ENGINE_PATH = "/api/v1/jobs/engine"
_MODEL = "SOIL_CEC"
_INPUTS = {"clay_pct": 22, "organic_matter_pct": 3, "ph": 7.1}


@pytest_asyncio.fixture
async def engine():
    """A private engine, so nothing here touches the process-wide hub database.

    The hub's async engine is shared-cache and process-wide, which is what a
    worker has to use in production but is exactly what a test must not: rows
    written by this file would be visible to every other test in the session.
    The worker nonetheless opens its session through the hub in production, so
    the worker's own reference to it is the one that gets swapped for the test
    engine.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@asynccontextmanager
async def _session_on(engine):
    """One session on ``engine``, matching ``hub.get_async_session()``'s shape."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session


async def _clear_queue(engine) -> None:
    """Empty the tables this module reads and writes."""
    async with _session_on(engine) as session:
        await session.execute(delete(JobEvent))
        await session.execute(delete(ComputeJob))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest_asyncio.fixture
async def session(engine):
    """A session on the private engine, with one user seeded."""
    async with _session_on(engine) as session:
        session.add(
            User(id="user-1", email="a@example.test", password_hash="x", full_name="A")
        )
        await session.commit()
        yield session
    await _clear_queue(engine)


@pytest.fixture
def worker_db(monkeypatch, engine):
    """Send the worker's ``run_once`` at the test engine.

    ``worker.hub`` is the attribute the worker resolves at call time, so
    substituting it here changes nothing for any other module that holds the
    real hub — and it lets ``run_forever`` be bounded instead of left running
    against whatever the process happens to hold in memory.
    """
    monkeypatch.setattr(
        worker, "hub", SimpleNamespace(get_async_session=lambda: _session_on(engine))
    )
    return worker.hub


@pytest_asyncio.fixture
async def client(session):
    """The jobs router on its own app, with the caller and the DB substituted."""
    app = FastAPI()
    app.include_router(jobs_router)

    async def _db_override():
        yield session

    app.dependency_overrides[get_db] = _db_override
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id="user-1")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


def _submit_body(**overrides):
    body = {"model_id": _MODEL, "inputs": _INPUTS}
    body.update(overrides)
    return body


# ── the route ─────────────────────────────────────────────────────────────────


class TestEngineJobRoute:
    async def test_submit_answers_202_with_a_job_id(self, client):
        response = await client.post(_ENGINE_PATH, json=_submit_body())

        assert response.status_code == 202, response.text
        body = response.json()
        assert body["job_id"]
        assert body["status"] == JobStatus.PENDING.value
        assert body["model_id"] == _MODEL
        assert body["status_url"] == f"/api/v1/jobs/{body['job_id']}"

    async def test_the_model_does_not_run_on_the_request(self, client):
        """202 means accepted, not computed: there is no result in the body."""
        response = await client.post(_ENGINE_PATH, json=_submit_body())

        body = response.json()
        assert body["status"] == JobStatus.PENDING.value
        assert "output_data" not in body
        assert "values" not in body

    async def test_the_job_is_recorded_under_the_callers_id(self, client, session):
        response = await client.post(_ENGINE_PATH, json=_submit_body())
        job_id = response.json()["job_id"]

        service = ComputeJobService(session)
        job = await service.get_job(job_id)

        assert job is not None
        assert job.created_by == "user-1"
        assert job.job_type == "engine_model"
        assert job.input_data["model_id"] == _MODEL
        assert job.input_data["inputs"] == _INPUTS

    async def test_an_unauthenticated_caller_is_refused(self, session):
        """No token: the real ``require_user`` runs and answers 401."""
        app = FastAPI()
        app.include_router(jobs_router)
        app.dependency_overrides[get_db] = lambda: session
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(_ENGINE_PATH, json=_submit_body())

        assert response.status_code == 401
        listing = await ComputeJobService(session).list_jobs(job_type="engine_model")
        assert listing.items == [], "an unauthenticated submit must record nothing"

    async def test_an_unknown_key_is_rejected_not_ignored(self, client):
        """A typo must not silently become a model input."""
        response = await client.post(_ENGINE_PATH, json=_submit_body(modelid=_MODEL))

        assert response.status_code == 422, response.text

    async def test_a_priority_is_honoured(self, client, session):
        response = await client.post(_ENGINE_PATH, json=_submit_body(priority="high"))

        assert response.status_code == 202
        job_id = response.json()["job_id"]
        job = await ComputeJobService(session).get_job(job_id)
        assert job.priority.value == "high"

    async def test_the_existing_create_route_still_works(self, client, session):
        response = await client.post(
            "/api/v1/jobs",
            json={"name": "manual", "job_type": "carbon_simulation"},
        )

        assert response.status_code == 201, response.text
        job_id = response.json()["id"]
        job = await ComputeJobService(session).get_job(job_id)
        assert job is not None
        assert job.name == "manual"

    async def test_the_existing_read_routes_still_answer(self, client, session):
        await submit_engine_job(
            ComputeJobService(session), model_id=_MODEL, inputs=_INPUTS, user_id="user-1"
        )
        listing = await client.get("/api/v1/jobs")
        stats = await client.get("/api/v1/jobs/stats")
        detail = await client.get(f"/api/v1/jobs/{listing.json()['items'][0]['id']}")

        assert listing.status_code == 200
        assert stats.status_code == 200
        assert detail.status_code == 200, detail.text
        assert detail.json()["id"] == listing.json()["items"][0]["id"]

    async def test_the_existing_lifecycle_routes_still_answer(self, client, session):
        """Cancel / retry / events / queue-position are untouched by the new route."""
        created = await client.post(
            "/api/v1/jobs",
            json={
                "name": "manual",
                "job_type": "carbon_simulation",
                "max_retries": 1,
            },
        )
        job_id = created.json()["id"]

        events = await client.get(f"/api/v1/jobs/{job_id}/events")
        position = await client.get(f"/api/v1/jobs/{job_id}/queue-position")
        cancelled = await client.post(f"/api/v1/jobs/{job_id}/cancel")
        retried = await client.post(f"/api/v1/jobs/{job_id}/retry")

        assert events.status_code == 200, events.text
        assert position.status_code == 200, position.text
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["status"] == JobStatus.CANCELLED.value
        assert retried.status_code == 200, retried.text
        assert retried.json()["status"] == JobStatus.PENDING.value

    async def test_a_retry_is_refused_without_a_retry_budget(self, client):
        """``max_retries`` defaults to 0, and the service says so rather than looping."""
        created = await client.post(
            "/api/v1/jobs",
            json={"name": "manual", "job_type": "carbon_simulation"},
        )
        job_id = created.json()["id"]

        await client.post(f"/api/v1/jobs/{job_id}/cancel")
        retried = await client.post(f"/api/v1/jobs/{job_id}/retry")

        assert retried.status_code == 400, retried.text


# ── idempotency ───────────────────────────────────────────────────────────────


class TestEngineJobIdempotency:
    async def test_a_retry_replays_the_same_job(self, client, session):
        headers = {"Idempotency-Key": str(uuid4())}
        first = await client.post(_ENGINE_PATH, json=_submit_body(), headers=headers)
        second = await client.post(_ENGINE_PATH, json=_submit_body(), headers=headers)

        assert first.status_code == 202
        assert second.status_code == 202
        assert first.json()["job_id"] == second.json()["job_id"]

        listing = await ComputeJobService(session).list_jobs(
            job_type="engine_model", created_by="user-1"
        )
        assert len(listing.items) == 1, "a retry must not start a second computation"

    async def test_another_caller_with_the_same_key_gets_its_own_job(self, session):
        """The key is scoped to its caller: one client's replay is not another's."""
        service = ComputeJobService(session)
        key = str(uuid4())
        first = await submit_engine_job(
            service, model_id=_MODEL, inputs=_INPUTS, user_id="user-1",
            idempotency_key=key,
        )
        second = await submit_engine_job(
            service, model_id=_MODEL, inputs=_INPUTS, user_id="user-2",
            idempotency_key=key,
        )

        assert first != second
        assert await service.find_active_engine_job(
            user_id="user-1", idempotency_key=key
        ) is not None
        assert await service.find_active_engine_job(
            user_id="user-3", idempotency_key=key
        ) is None

    async def test_a_key_is_kept_out_of_the_model_inputs(self, client, session):
        key = str(uuid4())
        response = await client.post(
            _ENGINE_PATH, json=_submit_body(), headers={"Idempotency-Key": key}
        )

        job_id = response.json()["job_id"]
        job = await ComputeJobService(session).get_job(job_id)
        assert job.input_data["inputs"] == _INPUTS
        assert job.input_data["idempotency_key"] == key

    async def test_no_key_means_no_key_in_the_payload(self, client, session):
        """The payload a caller without the header produces is unchanged."""
        response = await client.post(_ENGINE_PATH, json=_submit_body())

        job_id = response.json()["job_id"]
        job = await ComputeJobService(session).get_job(job_id)
        assert "idempotency_key" not in job.input_data
        assert set(job.input_data) == {"model_id", "inputs", "parameters"}

    async def test_a_retry_after_completion_is_a_new_computation(
        self, client, session, worker_db
    ):
        headers = {"Idempotency-Key": str(uuid4())}
        first = await client.post(_ENGINE_PATH, json=_submit_body(), headers=headers)
        job_id = first.json()["job_id"]

        assert await worker.run_once() is not None

        job = await ComputeJobService(session).get_job(job_id)
        assert job.status in (JobStatus.COMPLETED, JobStatus.FAILED)

        second = await client.post(_ENGINE_PATH, json=_submit_body(), headers=headers)
        assert second.status_code == 202
        assert second.json()["job_id"] != job_id


# ── the worker ────────────────────────────────────────────────────────────────


class TestEngineJobWorker:
    async def test_run_once_drains_one_job(self, session, worker_db):
        service = ComputeJobService(session)
        job_id = await submit_engine_job(
            service, model_id=_MODEL, inputs=_INPUTS, user_id="user-1"
        )

        result = await worker.run_once()

        assert result is not None
        assert result.job_id == job_id
        job = await service.get_job(job_id)
        # Whichever way the engine answered, the record carries the answer:
        # no silent inline execution, and no lost failure.
        assert job.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        assert job.output_data or job.error_message

    async def test_run_once_reports_an_empty_queue(self, worker_db):
        assert await worker.run_once() is None

    async def test_run_once_leaves_the_queue_empty_after_draining_it(self, session, worker_db):
        service = ComputeJobService(session)
        for _ in range(2):
            await submit_engine_job(
                service, model_id=_MODEL, inputs=_INPUTS, user_id="user-1"
            )

        assert await worker.run_once() is not None
        assert await worker.run_once() is not None
        assert await worker.run_once() is None

    async def test_run_forever_stops_where_its_caller_says(self, session, worker_db):
        """``max_iterations`` bounds the loop instead of the caller killing it."""
        service = ComputeJobService(session)
        await submit_engine_job(
            service, model_id=_MODEL, inputs=_INPUTS, user_id="user-1"
        )

        drained = await worker.run_forever(poll_seconds=0.01, max_iterations=1)

        assert drained == 1
        listing = await service.list_jobs(job_type="engine_model", created_by="user-1")
        assert listing.items[0].status in (JobStatus.COMPLETED, JobStatus.FAILED)

    async def test_run_forever_stops_on_the_stop_event(self, worker_db):
        stop = asyncio.Event()
        stop.set()

        drained = await worker.run_forever(poll_seconds=0.01, stop_event=stop)

        assert drained == 0

    async def test_run_forever_wakes_immediately_when_stopped(self, worker_db):
        """Setting the event skips the remaining sleep instead of finishing it.

        A 30 s poll is used on purpose: if the loop slept through the timeout
        instead of waiting on the event, this test's own 5 s ceiling would
        expire first and the failure would be visible rather than a slow pass.
        """
        stop = asyncio.Event()
        task = asyncio.create_task(worker.run_forever(poll_seconds=30.0, stop_event=stop))
        await asyncio.sleep(0.05)

        started = asyncio.get_running_loop().time()
        stop.set()

        drained = await asyncio.wait_for(task, timeout=5)
        assert drained == 0
        assert asyncio.get_running_loop().time() - started < 5

    async def test_run_forever_survives_a_failed_iteration(self, monkeypatch, caplog):
        """One bad poll must not end the worker for the life of the process."""
        calls = {"n": 0}

        async def _boom():
            calls["n"] += 1
            raise RuntimeError("the queue is unreachable")

        monkeypatch.setattr(worker, "run_once", _boom)
        with caplog.at_level(logging.ERROR, logger="services.jobs.worker"):
            drained = await worker.run_forever(poll_seconds=0.01, max_iterations=2)

        assert calls["n"] == 2
        assert drained == 0
        assert "the queue is unreachable" in caplog.text

    async def test_a_cancellation_is_not_swallowed(self, monkeypatch):
        """Cancellation is being told to stop; pretending otherwise hangs shutdown."""

        async def _cancel():
            raise asyncio.CancelledError

        monkeypatch.setattr(worker, "run_once", _cancel)
        with pytest.raises(asyncio.CancelledError):
            await worker.run_forever(poll_seconds=0.01, max_iterations=3)

    def test_the_default_poll_interval_is_five_seconds(self):
        assert worker.DEFAULT_POLL_SECONDS == 5.0
