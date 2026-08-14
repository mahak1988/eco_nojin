"""API endpoints for Carbon Credit system."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

from engine.hydroma.carbon.calculator import (
    CarbonProjectType, CarbonProject,
    calculate_carbon_sequestration, compare_project_types,
    register_project, get_project, list_projects,
    SEQUESTRATION_RATES, CARBON_PRICES
)

router = APIRouter(prefix="/api/v1/carbon", tags=["Carbon Credits"])


# --- Request Models ---

class CarbonCalculationRequest(BaseModel):
    project_type: str = Field(..., description="Project type")
    area_ha: float = Field(..., gt=0, le=100000)
    duration_years: int = Field(10, ge=1, le=100)
    region: str = Field("temperate", description="tropical, temperate, or arid")


class ProjectRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    project_type: str
    area_ha: float = Field(..., gt=0)
    duration_years: int = Field(10, ge=1, le=100)
    location: str = ""
    lat: float = 0.0
    lon: float = 0.0


# --- Endpoints ---

@router.get("/project-types")
def list_project_types():
    """List all available carbon project types with rates."""
    return {
        "project_types": [
            {
                "type": pt.value,
                "annual_rate_tonnes_ha": rates["rate"],
                "min_rate": rates["min"],
                "max_rate": rates["max"],
                "permanence_years": rates["permanence_years"],
            }
            for pt, rates in SEQUESTRATION_RATES.items()
        ],
        "count": len(SEQUESTRATION_RATES),
    }


@router.get("/prices")
def get_carbon_prices():
    """Get current carbon credit prices by standard."""
    return {
        "prices_usd_per_tonne": CARBON_PRICES,
        "last_updated": "2025-01-01",
        "market": "voluntary",
    }


@router.post("/calculate")
def calculate_carbon(payload: CarbonCalculationRequest):
    """Calculate carbon sequestration for a project."""
    try:
        project_type = CarbonProjectType(payload.project_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown project type: {payload.project_type}. "
                   f"Available: {[pt.value for pt in CarbonProjectType]}"
        )
    
    return calculate_carbon_sequestration(
        project_type=project_type,
        area_ha=payload.area_ha,
        duration_years=payload.duration_years,
        region=payload.region,
    )


@router.post("/compare")
def compare_carbon_projects(payload: CarbonCalculationRequest):
    """Compare all carbon project types for given parameters."""
    return compare_project_types(
        area_ha=payload.area_ha,
        duration_years=payload.duration_years,
    )


@router.post("/projects")
def register_carbon_project(payload: ProjectRegistrationRequest):
    """Register a new carbon project."""
    try:
        project_type = CarbonProjectType(payload.project_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown project type: {payload.project_type}"
        )
    
    project = CarbonProject(
        name=payload.name,
        project_type=project_type,
        area_ha=payload.area_ha,
        duration_years=payload.duration_years,
        location=payload.location,
        lat=payload.lat,
        lon=payload.lon,
    )
    
    # Calculate estimates
    calc = calculate_carbon_sequestration(
        project_type=project_type,
        area_ha=payload.area_ha,
        duration_years=payload.duration_years,
    )
    
    project.estimated_carbon_tonnes = calc["total_carbon_tonnes"]
    project.annual_rate_tonnes = calc["annual_rate_tonnes"]
    project.methodology = calc["methodology"]
    project.status = "submitted"
    
    project_id = register_project(project)
    
    return {
        "project_id": project_id,
        "name": project.name,
        "status": project.status,
        "estimated_carbon_tonnes": project.estimated_carbon_tonnes,
        "annual_rate_tonnes": project.annual_rate_tonnes,
        "methodology": project.methodology,
    }


@router.get("/projects")
def list_carbon_projects(status: Optional[str] = None):
    """List all registered carbon projects."""
    projects = list_projects(status)
    
    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "project_type": p.project_type.value,
                "area_ha": p.area_ha,
                "status": p.status,
                "estimated_carbon_tonnes": p.estimated_carbon_tonnes,
            }
            for p in projects
        ],
        "count": len(projects),
    }


@router.get("/projects/{project_id}")
def get_carbon_project(project_id: str):
    """Get carbon project details."""
    project = get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "name": project.name,
        "project_type": project.project_type.value,
        "area_ha": project.area_ha,
        "duration_years": project.duration_years,
        "location": project.location,
        "status": project.status,
        "estimated_carbon_tonnes": project.estimated_carbon_tonnes,
        "annual_rate_tonnes": project.annual_rate_tonnes,
        "methodology": project.methodology,
        "created_at": project.created_at.isoformat(),
    }


@router.post("/projects/{project_id}/verify")
def verify_carbon_project(project_id: str, verifier: str = "Eco Nojin Internal"):
    """Submit project for verification."""
    project = get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != "submitted":
        raise HTTPException(
            status_code=400,
            detail=f"Project cannot be verified from status: {project.status}"
        )
    
    # Simplified verification for research mode
    project.status = "verified"
    project.verifier = verifier
    project.verification_date = datetime.now(timezone.utc)
    
    return {
        "project_id": project_id,
        "status": project.status,
        "verifier": project.verifier,
        "verification_date": project.verification_date.isoformat(),
    }
