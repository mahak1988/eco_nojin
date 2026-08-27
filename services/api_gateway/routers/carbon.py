
"""Carbon module router - scientific carbon sequestration."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import CarbonProject, User
from services.api_gateway.auth import require_user
from services.api_gateway.routers.carbon_engine import (
    STANDARDS,
    WOOD_DENSITIES,
    farquhar_photosynthesis,
    get_all_calculations,
    quantum_efficiency,
    rothc_carbon_pools,
    verify_project,
)

router = APIRouter(prefix="/api/v1/carbon", tags=["carbon"])


# ============================================================================
# Pydantic Models
# ============================================================================
class ProjectCalculateRequest(BaseModel):
    name: str = Field(min_length=3)
    area_hectares: float = Field(gt=0, le=100000)
    species: str = "tropical_moist"
    trees_per_ha: int = Field(1000, ge=100, le=10000)
    avg_diameter_cm: float = Field(20, gt=0, le=200)
    avg_height_m: float = Field(12, gt=0, le=100)
    project_years: int = Field(30, ge=5, le=100)
    latitude: float = 0.0
    longitude: float = 0.0
    soil_carbon_tha: float = 40.0
    mean_temperature_C: float = 25.0


class ProjectOut(BaseModel):
    id: int
    project_id: str
    name: str
    project_type: str
    area_hectares: float
    status: str
    credits_issued: float


# ============================================================================
# Endpoints
# ============================================================================
@router.post("/calculate")
def calculate_project(req: ProjectCalculateRequest):
    """
    Calculate carbon sequestration for a project using scientific models.

    Models used:
    - Chave et al. 2014 (biomass allometry)
    - Farquhar-von Caemmerer-Berry (photosynthesis)
    - RothC-26.3 (soil carbon)
    - FMO quantum coherence
    - Evapotranspiration cooling
    """
    return get_all_calculations(
        D_cm=req.avg_diameter_cm,
        H_m=req.avg_height_m,
        species=req.species,
        area_ha=req.area_hectares,
        trees_per_ha=req.trees_per_ha,
        project_years=req.project_years,
        soil_C_tha=req.soil_carbon_tha,
        T_C=req.mean_temperature_C,
    )


@router.post("/register")
def register_project(
    req: ProjectCalculateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    """Register a carbon project after calculation."""
    # Calculate first
    calc = get_all_calculations(
        D_cm=req.avg_diameter_cm,
        H_m=req.avg_height_m,
        species=req.species,
        area_ha=req.area_hectares,
        trees_per_ha=req.trees_per_ha,
        project_years=req.project_years,
        soil_C_tha=req.soil_carbon_tha,
        T_C=req.mean_temperature_C,
    )

    total_co2 = calc["project_summary"]["project_total"]["total_co2_tons"]
    verification = verify_project(total_co2)

    import uuid

    project_id = f"ECO-{uuid.uuid4().hex[:8].upper()}"

    project = CarbonProject(
        project_id=project_id,
        name=req.name,
        user_id=user.id,
        project_type="afforestation",
        area_hectares=req.area_hectares,
        status="registered",
        credits_issued=verification["net_credits"],
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "success": True,
        "project_id": project_id,
        "db_id": project.id,
        "credits": verification["net_credits"],
        "verification": verification,
    }


@router.get("/projects")
def list_projects(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """List user's carbon projects."""
    projects = (
        db.query(CarbonProject)
        .filter(CarbonProject.user_id == user.id)
        .order_by(CarbonProject.registered_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "project_id": p.project_id,
            "name": p.name,
            "project_type": p.project_type,
            "area_hectares": p.area_hectares,
            "status": p.status,
            "credits_issued": p.credits_issued,
            "registered_at": p.registered_at.isoformat() if p.registered_at else None,
        }
        for p in projects
    ]


@router.get("/standards")
def list_standards():
    """List available verification standards."""
    return STANDARDS


@router.get("/species")
def list_species():
    """List available tree species with wood densities."""
    return WOOD_DENSITIES


@router.post("/photosynthesis")
def calc_photosynthesis(
    PAR_umol: float = 1500,
    T_leaf_C: float = 25.0,
    CO2_ppm: float = 420.0,
    Vcmax25: float = 80.0,
):
    """Calculate photosynthesis using Farquhar model."""
    return farquhar_photosynthesis(PAR_umol, T_leaf_C, CO2_ppm, Vcmax25)


@router.get("/quantum")
def calc_quantum(T_C: float = 25.0):
    """Calculate quantum coherence efficiency in FMO complex."""
    return quantum_efficiency(T_C)


@router.post("/soil-carbon")
def calc_soil_carbon(
    initial_C_tha: float = 40.0,
    annual_input_tha: float = 3.0,
    clay_pct: float = 30.0,
    temperature_C: float = 15.0,
    rainfall_mm: float = 500.0,
    years: int = 50,
):
    """Simulate soil carbon using RothC-26.3 model."""
    return rothc_carbon_pools(
        initial_C_tha, annual_input_tha, 1.44, clay_pct, temperature_C, rainfall_mm, years
    )


# ============================================================================
# Phase 8 — methodology verification + credit issuance (VM0042-aligned)
# ============================================================================


class VerifyRequest(BaseModel):
    baseline_activity: str = Field(..., description="pre-project land use")
    has_financing: bool = False
    would_happen_without_project: bool = False
    activity_displacement: bool = False
    market_leakage: bool = False
    commitment_years: int = Field(30, ge=1, le=100)
    risk_flag: bool = False


def _get_owned_project(db: Session, project_id: int, user: User):
    project = db.query(CarbonProject).filter(CarbonProject.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="not your project")
    return project


@router.post("/projects/{project_id}/verify")
def verify_project_methodology(
    project_id: int,
    req: VerifyRequest,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Run honest VM0042-style methodology checks (baseline/additionality/
    leakage/permanence). Never rubber-stamps: failed checks are returned."""
    from services.carbon.verification import run_verification

    project = _get_owned_project(db, project_id, user)
    result = run_verification(
        baseline_activity=req.baseline_activity,
        has_financing=req.has_financing,
        would_happen_without_project=req.would_happen_without_project,
        activity_displacement=req.activity_displacement,
        market_leakage=req.market_leakage,
        commitment_years=req.commitment_years,
        risk_flag=req.risk_flag,
    )
    project.verification_detail = json.dumps(result, ensure_ascii=False)
    project.verification_status = "verified" if result["passed"] else "failed"
    db.commit()
    return {"project_id": project.project_id, "verification": result}


@router.post("/projects/{project_id}/issue")
def issue_credits(
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Issue carbon credits for a VERIFIED project and credit the wallet."""
    from services.ecowallet.service import earn as wallet_earn

    project = _get_owned_project(db, project_id, user)
    if project.verification_status != "verified":
        raise HTTPException(
            status_code=400,
            detail=f"project not verified (status={project.verification_status}); "
            "run POST /projects/{id}/verify first",
        )
    credits = project.credits_issued or 0.0
    if credits <= 0:
        raise HTTPException(status_code=400, detail="no credits to issue")
    amount, balance = wallet_earn(db, user.id, "carbon_credit", quantity=credits)
    project.status = "issued"
    project.issued_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return {
        "project_id": project.project_id,
        "credits_issued": credits,
        "wallet_eco_earned": amount,
        "wallet_balance": balance,
        "issued_at": project.issued_at.isoformat(),
    }


@router.get("/projects/{project_id}/oracle-report")
def oracle_report(
    project_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """VerificationOracle certificate for an owned project."""
    from services.carbon.oracle import build_oracle_report

    project = _get_owned_project(db, project_id, user)
    return build_oracle_report(project)


@router.get("/wallet")
def carbon_wallet(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """DB-backed ECO wallet state (persists across restarts)."""
    from services.ecowallet.service import wallet_state

    return wallet_state(db, user.id)

