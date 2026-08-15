"""Carbon module router - scientific carbon sequestration."""

from fastapi import APIRouter, Depends
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
