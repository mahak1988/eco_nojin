"""Simulation chain API (Phase 3): run and list simulation runs.

POST /api/v1/simulation/run  execute the RUSLE -> AquaCrop -> RothC chain
GET  /api/v1/simulation/runs  list persisted runs (filter by site)
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import SimulationRun
from engine.hydroma.simulation.contracts import ChainInputs
from engine.hydroma.simulation.orchestrator import run_chain

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


def _run_json(row: SimulationRun) -> dict:
    """Serialize one simulation run row."""
    return {
        "id": row.id,
        "site_id": row.site_id,
        "scenario": row.scenario,
        "area_ha": row.area_ha,
        "status": row.status,
        "outputs": row.outputs or {},
        "message": row.message or "",
        "executed_at": row.executed_at.isoformat() if row.executed_at else None,
    }


@router.post("/run")
def create_simulation_run(inputs: ChainInputs, db: Session = Depends(get_db)):
    """Execute the simulation chain for one site+scenario and persist it."""
    result = run_chain(inputs)
    row = SimulationRun(
        site_id=inputs.site_id,
        scenario=result.scenario,
        area_ha=inputs.area_ha,
        status=result.status,
        outputs=result.model_dump(mode="json")["outputs"],
        message=result.message,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, **result.model_dump(mode="json")}


@router.get("/runs")
def list_simulation_runs(
    site_id: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List persisted simulation runs, optionally filtered by site."""
    query = db.query(SimulationRun).order_by(SimulationRun.executed_at.desc())
    if site_id:
        query = query.filter(SimulationRun.site_id == site_id)
    rows = query.limit(limit).all()
    return {"count": len(rows), "runs": [_run_json(r) for r in rows]}


# ============================================================================
# Async chain execution with live progress (poll + SSE)
# ============================================================================

import asyncio
import json as _json

from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse

_chain_runs: dict[str, dict] = {}


def _chain_progress_cb(run_id: str):
    def cb(stage: str, pct: int) -> None:
        st = _chain_runs.setdefault(run_id, {"status": "running", "stages": [], "progress": 0})
        st["status"] = "running"
        st["progress"] = pct
        st["stage"] = stage
        if stage not in st["stages"]:
            st["stages"].append(stage)
    return cb


@router.post("/run-async")
async def create_simulation_run_async(
    inputs: ChainInputs,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Launch the chain in the background; poll /progress/{run_id} or use SSE."""
    import uuid

    run_id = f"CHAIN_{uuid.uuid4().hex[:12]}"

    def _job() -> None:
        cb = _chain_progress_cb(run_id)
        cb("queued", 1)
        try:
            result = run_chain(inputs, progress_cb=cb)
            row = SimulationRun(
                site_id=inputs.site_id,
                scenario=result.scenario,
                area_ha=inputs.area_ha,
                status=result.status,
                outputs=result.model_dump(mode="json")["outputs"],
                message=result.message,
            )
            db.add(row)
            db.commit()
            st = _chain_runs.setdefault(run_id, {})
            st.update({"status": result.status, "progress": 100, "result": result.model_dump(mode="json")})
        except Exception as exc:
            st = _chain_runs.setdefault(run_id, {})
            st.update({"status": "failed", "error": str(exc)[:300], "progress": 100})

    background_tasks.add_task(_job)
    _chain_runs[run_id] = {"status": "queued", "progress": 0, "stages": []}
    return {"run_id": run_id, "status": "queued"}


@router.get("/progress/{run_id}")
def chain_progress(run_id: str) -> dict:
    st = _chain_runs.get(run_id)
    if st is None:
        raise HTTPException(404, f"unknown run: {run_id}")
    return {"run_id": run_id, **st}


@router.get("/progress/{run_id}/stream")
async def chain_progress_stream(run_id: str) -> StreamingResponse:
    """SSE stream of chain progress until done/failed."""

    async def gen():
        while True:
            st = _chain_runs.get(run_id)
            if st is None:
                yield f"data: {_json.dumps({'error': 'unknown run'})}\n\n"
                break
            yield f"data: {_json.dumps({'run_id': run_id, 'status': st.get('status'), 'stage': st.get('stage'), 'progress': st.get('progress')})}\n\n"
            if st.get("status") in ("ok", "completed", "failed"):
                break
            await asyncio.sleep(1.5)

    return StreamingResponse(gen(), media_type="text/event-stream")
