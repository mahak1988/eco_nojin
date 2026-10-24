"""P13/P1 — the worker that drains the engine-job queue.

``services/jobs/engine_bridge.py`` holds both halves of the contract:
``submit_engine_job`` records the request, ``run_next_engine_job`` executes
exactly one queued job. What was missing is the loop that keeps calling the
second half — a process a deployment actually runs. This module is that loop:

* :func:`run_once` drains **one** job on its own session, so a single
  iteration is what a test (or a cron tick) calls;
* :func:`run_forever` polls :func:`run_once` and sleeps between idle polls.

It deliberately invents nothing: the durable state is the existing
``compute_jobs`` table, and the only import of the engine is the sanctioned
facade inside the bridge. There is no second queue, no in-memory backlog and
no transport — when D-06 decides on a message bus, this loop is the only
thing that has to change (it calls one function).

The loop survives a failed message. A job that cannot run is recorded as
``failed`` by the bridge itself (that is what keeps it inspectable), so an
exception escaping :func:`run_once` means something *outside* the job went
wrong — a database hiccup, for instance. Dying on that would leave the queue
untouched for the lifetime of the process, so the exception is logged and the
next poll retries.
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from database.hub import hub
from services.jobs.engine_bridge import EngineJobResult, run_next_engine_job
from services.jobs.service import ComputeJobService

logger = logging.getLogger(__name__)

#: Seconds between idle polls. Five is a compromise: short enough that a
#: submitted job is picked up while its submitter is still watching the
#: status endpoint, long enough that an empty queue is not a busy loop over a
#: query that returns nothing.
DEFAULT_POLL_SECONDS = 5.0


async def run_once() -> EngineJobResult | None:
    """Drain the next pending engine job, or return ``None`` when idle.

    The session is opened per call, not per worker, so an iteration is
    self-contained: nothing is left dangling between polls, and a caller
    (a test) can invoke it without constructing a worker.
    """
    async with hub.get_async_session() as session:
        service = ComputeJobService(session)
        return await run_next_engine_job(service)


async def run_forever(
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    *,
    max_iterations: int | None = None,
    stop_event: asyncio.Event | None = None,
) -> int:
    """Poll the engine-job queue until stopped; return the jobs drained.

    ``poll_seconds`` is the idle wait between polls. ``max_iterations`` and
    ``stop_event`` exist so a caller can bound the loop instead of spawning a
    task and killing it: a test passes ``max_iterations=1``, a deployment
    passes an ``asyncio.Event`` that its shutdown handler sets. Neither
    changes what a tick does.

    A cancellation (``asyncio.CancelledError``) is *not* swallowed — it is the
    loop being told to stop, and pretending otherwise would make a shutdown
    hang until the next poll finished.
    """
    drained = 0
    iterations = 0

    while not (stop_event is not None and stop_event.is_set()):
        # Counted before the work, not after it: a poll that *fails* is still a
        # poll, and a loop whose failures are free never reaches
        # ``max_iterations`` — which is how a caller that asked the worker to
        # stop after N attempts would wait forever on a broken queue.
        iterations += 1
        try:
            result = await run_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("engine job worker: iteration failed; retrying next poll")
        else:
            if result is None:
                logger.debug("engine job worker: queue empty")
            else:
                drained += 1
                logger.info(
                    "engine job worker: job %s finished as %s",
                    result.job_id,
                    result.status,
                )

        if max_iterations is not None and iterations >= max_iterations:
            break

        if stop_event is None:
            await asyncio.sleep(poll_seconds)
            continue
        # Waiting on the event keeps shutdown immediate: setting it wakes the
        # worker instead of letting it finish its sleep first.
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=poll_seconds)
        except TimeoutError:
            pass

    return drained


def main(poll_seconds: float = DEFAULT_POLL_SECONDS) -> int:
    """Run the worker in the foreground until interrupted."""
    parser = argparse.ArgumentParser(
        prog="python -m services.jobs.worker",
        description=(
            "Drain the engine compute-job queue: run each pending "
            "engine_model job through the engine gateway and record the "
            "result on the job."
        ),
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=poll_seconds,
        help=f"seconds between polls when the queue is empty (default {poll_seconds})",
    )
    args = parser.parse_args()
    try:
        drained = asyncio.run(run_forever(args.poll_seconds))
    except KeyboardInterrupt:
        logger.info("engine job worker stopped")
        return 0
    logger.info("engine job worker stopped after draining %d job(s)", drained)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
