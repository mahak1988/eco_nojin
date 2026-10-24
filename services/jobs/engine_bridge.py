"""P13 — heavy engine compute leaves the request path.

The program's rule (``PHASE_PLAN.md`` P13/P10): a request that triggers a
hydrological, erosion or simulation computation must not run it inline. The
repository already has the durable side — ``services/jobs`` (the ``compute_jobs``
table, priority queue, status transitions, cancellation, retry) and the
``services.api_gateway.eventbus`` for notification. What was missing is the
bridge: a way for a caller to say "run this engine model as a job" and have a
worker drain it.

This module is that bridge:

* :func:`submit_engine_job` records a ``ComputeJob`` with the engine request
  payload (``job_type="engine_model"``) and returns the job id — the HTTP layer
  answers ``202 Accepted`` immediately;
* :func:`run_next_engine_job` pops the highest-priority pending job, runs the
  model through the **engine gateway** (``services._gateway_facade``), records
  the result or the failure on the job, and returns;
* the worker loop is a plain ``while True: await run_next_engine_job()`` — the
  same shape the integration outbox worker uses, so it can be replaced by a
  queue transport when D-06 decides one.

Nothing here invents a second queue: the durable state is the existing
``compute_jobs`` table.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from services.jobs.models import JobPriority, JobStatus
from services.jobs.schemas import JobCreate, JobStatusUpdate
from services.jobs.service import ComputeJobService


@dataclass(frozen=True)
class EngineJobResult:
    job_id: str
    status: str
    output: dict[str, Any]
    error: str | None = None


def _job_id(job: Any):
    """The job id as the ORM expects it.

    `list_jobs` returns API responses whose `id` is a string, while the
    `compute_jobs.id` column is a Postgres UUID — binding the string back
    fails ("'str' object has no attribute 'hex'"). Coerce once, here.
    """
    value = getattr(job, "id", job)
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


async def submit_engine_job(
    service: ComputeJobService,
    *,
    model_id: str,
    inputs: dict[str, Any],
    user_id: str | None = None,
    priority: str = JobPriority.NORMAL.value,
    parameters: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> str:
    """Record a heavy engine computation and return its job id (never runs it).

    The optional ``idempotency_key`` is stored verbatim inside the job's
    ``input_data`` envelope — never inside ``inputs``, which is handed to the
    model unchanged — so a retry can be recognised by a later lookup
    (:meth:`ComputeJobService.find_active_engine_job`) without duplicating the
    computation. Callers that pass none see exactly the payload this module
    always recorded: the key is absent, not empty.
    """
    payload: dict[str, Any] = {
        "model_id": model_id,
        "inputs": inputs,
        "parameters": parameters or {},
    }
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    job = await service.create_job(
        JobCreate(
            name=f"engine:{model_id}",
            job_type="engine_model",
            priority=JobPriority(priority),
            input_data=payload,
        ),
        user_id=user_id,
    )
    return str(job.id)


async def run_next_engine_job(service: ComputeJobService) -> EngineJobResult | None:
    """Execute the next pending engine job, or return None when the queue is empty."""
    listing = await service.list_jobs(
        status=[JobStatus.PENDING, JobStatus.QUEUED],
        job_type="engine_model",
        page=1,
        page_size=50,
    )
    jobs = getattr(listing, "items", None) or []
    if not jobs:
        return None
    job = jobs[0]  # id stays an object: SQLite rejects str-bound PG UUIDs

    await service.update_job_status(
        _job_id(job), update=JobStatusUpdate(status="running")
    )
    payload = job.input_data or {}
    model_id = payload.get("model_id")

    try:
        if not model_id:
            raise ValueError("engine_model job is missing model_id")
        result = _run_model(
            model_id=model_id,
            inputs=payload.get("inputs") or {},
            parameters=payload.get("parameters") or {},
        )
    except Exception as exc:  # a failed job records the failure and stays inspectable
        await service.update_job_status(
            _job_id(job),
            update=JobStatusUpdate(status="failed", error_message=str(exc)),
        )
        return EngineJobResult(str(job.id), JobStatus.FAILED.value, {}, str(exc))

    output = {"model_id": model_id, "values": result}
    await service.update_job_status(
        _job_id(job), update=JobStatusUpdate(status="completed", output_data=output)
    )
    return EngineJobResult(str(job.id), JobStatus.COMPLETED.value, output, None)


def _run_model(*, model_id: str, inputs: dict, parameters: dict) -> dict:
    """Run one engine model through the sanctioned services boundary.

    Delegates to ``services._gateway_facade._execute_full`` — the one sanctioned
    bridge — which stamps provenance and raises ``GatewayCallError`` when the
    gateway returns a ``GatewayError`` (the gateway *returns* failure results
    rather than raising them), so a failed computation reaches the job's failed
    branch instead of being recorded as a completed job.
    """
    from services._gateway_facade import _execute_full

    result = _execute_full(
        model_id,
        inputs,
        parameters,
        source="jobs_engine_bridge",
        source_type="SERVICE_CALL",
    )
    return dict(result.values)
