"""Climate scenarios router - IPCC SSP + database."""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import ScenarioRun
from services.api_gateway.errors import safe_error_detail


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session



router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


class ScenarioRequest(BaseModel):
    baseline_temp: float = Field(20.0, description="Baseline annual mean temp (C)")
    baseline_precip: float = Field(400.0, description="Baseline annual precipitation (mm)")
    scenario: str = Field("ssp245", description="ssp126/ssp245/ssp370/ssp585")
    year: int = Field(2050, ge=2025, le=2100)
    farm_id: int | None = None
    user_id: int | None = None


@router.post("/apply")
def apply_scenario(req: ScenarioRequest, db: Annotated[Session, Depends(get_db)]):
    """Apply IPCC SSP climate scenario."""
    from services._gateway_facade import apply_scenario as _apply_scenario

    result = _apply_scenario(req.scenario, {"baseline_temp": req.baseline_temp, "baseline_precip": req.baseline_precip, "year": req.year})

    # Save to database
    if req.farm_id and req.user_id:
        try:
            record = ScenarioRun(
                farm_id=req.farm_id,
                user_id=req.user_id,
                baseline_temp=req.baseline_temp,
                baseline_precip=req.baseline_precip,
                scenario=req.scenario,
                target_year=req.year,
                projected_temp=result.get("projected_temperature"),
                projected_precip=result.get("projected_precipitation"),
                temp_change=result.get("temperature_change"),
                precip_change_percent=result.get("precipitation_change_percent"),
                drought_risk_index=result.get("drought_risk_index"),
                impact_assessment=result.get("impact_assessment"),
                recommendations=result.get("recommendations"),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            result["saved_id"] = record.id
        except Exception as e:
            db.rollback()
            result["save_warning"] = safe_error_detail(e)

    return result


@router.get("/compare/{farm_id}")
def compare_scenarios(farm_id: int, db: Annotated[Session, Depends(get_db)]):
    """Compare all scenarios for a farm."""
    runs = (
        db.query(ScenarioRun)
        .filter(ScenarioRun.farm_id == farm_id)
        .order_by(ScenarioRun.run_at.desc())
        .all()
    )
    return {
        "farm_id": farm_id,
        "count": len(runs),
        "scenarios": [
            {
                "id": r.id,
                "scenario": r.scenario,
                "year": r.target_year,
                "temp_change": r.temp_change,
                "precip_change": r.precip_change_percent,
                "drought_risk": r.drought_risk_index,
                "run_at": r.run_at.isoformat() if r.run_at else None,
            }
            for r in runs
        ],
    }
