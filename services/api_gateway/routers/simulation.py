"""Simulation chain API (Phase 3): run and list simulation runs.

POST /api/v1/simulation/run  execute the RUSLE -> AquaCrop -> RothC chain
GET  /api/v1/simulation/runs  list persisted runs (filter by site)
"""

from fastapi import APIRouter, Depends, Query
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
