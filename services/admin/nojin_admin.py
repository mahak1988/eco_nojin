"""
Nojin Admin Dashboard - FastAPI Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

router = APIRouter(prefix="/admin/nojin", tags=["Admin"])

class ProjectStatus(BaseModel):
    project_id: str
    name: str
    area_ha: float
    soil_type: str
    status: str
    start_date: date
    carbon_sequestered_t: float
    credits_issued: int
    credits_pending: int

class MaterialInventory(BaseModel):
    material_code: str
    name: str
    stock_tons: float
    monthly_consumption_tons: float
    months_of_stock: float
    reorder_point_tons: float
    status: str

class SystemHealth(BaseModel):
    total_projects: int
    active_projects: int
    total_area_ha: float
    total_carbon_tons: float
    total_credits_issued: int
    revenue_usd: float
    database_status: str
    api_status: str
    satellite_status: str

@router.get("/dashboard/overview", response_model=SystemHealth)
async def get_dashboard_overview():
    return SystemHealth(
        total_projects=127, active_projects=98, total_area_ha=15240.5,
        total_carbon_tons=45720.8, total_credits_issued=38500,
        revenue_usd=962500.0, database_status="healthy",
        api_status="healthy", satellite_status="operational"
    )

@router.get("/projects", response_model=List[ProjectStatus])
async def list_projects(status_filter: Optional[str] = None, limit: int = 50):
    projects = [
        ProjectStatus(
            project_id="PRJ-001", name="Khuzestan Restoration", area_ha=250.0,
            soil_type="Saline", status="active", start_date=date(2026, 1, 15),
            carbon_sequestered_t=1250.5, credits_issued=1100, credits_pending=150
        ),
        ProjectStatus(
            project_id="PRJ-002", name="Yazd Desert Project", area_ha=500.0,
            soil_type="Desert Sandy", status="active", start_date=date(2026, 2, 1),
            carbon_sequestered_t=2850.0, credits_issued=2500, credits_pending=350
        ),
    ]
    if status_filter:
        projects = [p for p in projects if p.status == status_filter]
    return projects[:limit]

@router.get("/inventory", response_model=List[MaterialInventory])
async def get_material_inventory():
    return [
        MaterialInventory(
            material_code="MIN-011", name="Zeolite", stock_tons=500.0,
            monthly_consumption_tons=50.0, months_of_stock=10.0,
            reorder_point_tons=100.0, status="ok"
        ),
        MaterialInventory(
            material_code="ANM-027", name="Sheep Manure", stock_tons=80.0,
            monthly_consumption_tons=60.0, months_of_stock=1.3,
            reorder_point_tons=120.0, status="critical"
        ),
    ]

@router.post("/projects/{project_id}/verify")
async def verify_project(project_id: str):
    return {
        "project_id": project_id, "status": "submitted_for_verification",
        "verification_body": "Verra", "expected_completion": "2026-11-30"
    }

@router.post("/credits/issue")
async def issue_credits(project_id: str, amount_tons: float):
    return {
        "project_id": project_id, "credits_issued": amount_tons,
        "Integer_numbers": [f"NOJIN-2026-{i:06d}" for i in range(1, int(amount_tons) + 1)],
        "registry": "Verra"
    }

@router.get("/reports/monthly/{year}/{month}")
async def get_monthly_report(year: int, month: int):
    return {
        "period": f"{year}-{month:02d}", "projects_active": 98,
        "new_projects": 12, "area_treated_ha": 1250.5,
        "carbon_sequestered_t": 3750.8, "credits_issued": 3200,
        "revenue_usd": 80000.0, "water_saved_m3": 2500000
    }

__all__ = ["router"]
