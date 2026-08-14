"""Carbon sequestration calculator for various project types.

Implements methodologies from:
- Verra VCS (Verified Carbon Standard)
- Gold Standard
- IPCC Guidelines for National Greenhouse Gas Inventories

Project types supported:
- Afforestation/Reforestation
- Soil Carbon (no-till, cover crops, compost)
- Biochar
- Agroforestry
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
import uuid
from datetime import datetime


class CarbonProjectType(Enum):
    """Types of carbon sequestration projects."""
    AFFORESTATION = "afforestation"
    REFORESTATION = "reforestation"
    SOIL_CARBON_NO_TILL = "soil_carbon_no_till"
    SOIL_CARBON_COVER_CROP = "soil_carbon_cover_crop"
    SOIL_CARBON_COMPOST = "soil_carbon_compost"
    BIOCHAR = "biochar"
    AGROFORESTRY = "agroforestry"
    GRASSLAND_RESTORATION = "grassland_restoration"


@dataclass
class CarbonProject:
    """A carbon sequestration project."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    project_type: CarbonProjectType = CarbonProjectType.AFFORESTATION
    area_ha: float = 0.0
    duration_years: int = 10
    location: str = ""
    lat: float = 0.0
    lon: float = 0.0
    
    # Verification
    status: str = "draft"  # draft, submitted, verified, certified
    verification_date: Optional[datetime] = None
    verifier: str = ""
    
    # Results
    estimated_carbon_tonnes: float = 0.0
    annual_rate_tonnes: float = 0.0
    methodology: str = ""
    
    created_at: datetime = field(default_factory=datetime.utcnow)


# Carbon sequestration rates (tonnes CO2/ha/year) by project type
# Based on IPCC AR6 and peer-reviewed literature
SEQUESTRATION_RATES: Dict[CarbonProjectType, Dict[str, float]] = {
    CarbonProjectType.AFFORESTATION: {
        "rate": 8.0,       # tonnes CO2/ha/year (tropical/temperate average)
        "min": 4.0,
        "max": 15.0,
        "permanence_years": 100,
    },
    CarbonProjectType.REFORESTATION: {
        "rate": 6.0,
        "min": 3.0,
        "max": 12.0,
        "permanence_years": 80,
    },
    CarbonProjectType.SOIL_CARBON_NO_TILL: {
        "rate": 0.8,       # Lower rate but more certain
        "min": 0.3,
        "max": 1.5,
        "permanence_years": 25,
    },
    CarbonProjectType.SOIL_CARBON_COVER_CROP: {
        "rate": 0.5,
        "min": 0.2,
        "max": 1.0,
        "permanence_years": 20,
    },
    CarbonProjectType.SOIL_CARBON_COMPOST: {
        "rate": 1.2,
        "min": 0.5,
        "max": 2.0,
        "permanence_years": 30,
    },
    CarbonProjectType.BIOCHAR: {
        "rate": 3.0,       # One-time application
        "min": 2.0,
        "max": 5.0,
        "permanence_years": 500,  # Biochar is very stable
    },
    CarbonProjectType.AGROFORESTRY: {
        "rate": 4.5,
        "min": 2.0,
        "max": 8.0,
        "permanence_years": 50,
    },
    CarbonProjectType.GRASSLAND_RESTORATION: {
        "rate": 1.5,
        "min": 0.5,
        "max": 3.0,
        "permanence_years": 40,
    },
}

# Market prices (USD/tonne CO2) by standard
CARBON_PRICES: Dict[str, float] = {
    "verra_vcs": 12.0,
    "gold_standard": 18.0,
    "plan_vivo": 15.0,
    "voluntary_market": 10.0,
}


def calculate_carbon_sequestration(
    project_type: CarbonProjectType,
    area_ha: float,
    duration_years: int = 10,
    region: str = "temperate",
) -> dict:
    """Calculate carbon sequestration for a project.
    
    Args:
        project_type: Type of carbon project
        area_ha: Project area in hectares
        duration_years: Project duration in years
        region: Climate region (tropical, temperate, arid)
    
    Returns:
        Sequestration estimates and economic value
    """
    rates = SEQUESTRATION_RATES.get(project_type)
    if not rates:
        raise ValueError(f"Unknown project type: {project_type}")
    
    # Regional adjustment factor
    region_factors = {
        "tropical": 1.3,   # Higher growth rates
        "temperate": 1.0,  # Baseline
        "arid": 0.6,       # Lower growth rates
    }
    factor = region_factors.get(region, 1.0)
    
    # Adjusted annual rate
    annual_rate = rates["rate"] * factor
    min_rate = rates["min"] * factor
    max_rate = rates["max"] * factor
    
    # For biochar, sequestration is one-time (not annual)
    if project_type == CarbonProjectType.BIOCHAR:
        total_carbon = annual_rate * area_ha
        annual_rate = total_carbon / duration_years  # Amortized
    else:
        total_carbon = annual_rate * area_ha * duration_years
    
    # Apply discount for uncertainty (conservative approach)
    discount_factor = 0.85  # 15% discount for uncertainty
    
    estimated_carbon = total_carbon * discount_factor
    
    # Economic value
    price_per_tonne = CARBON_PRICES["voluntary_market"]
    estimated_revenue = estimated_carbon * price_per_tonne
    annual_revenue = annual_rate * area_ha * price_per_tonne * discount_factor
    
    return {
        "project_type": project_type.value,
        "area_ha": area_ha,
        "duration_years": duration_years,
        "region": region,
        "annual_rate_tonnes": round(annual_rate * area_ha, 2),
        "total_carbon_tonnes": round(estimated_carbon, 2),
        "total_carbon_min": round(min_rate * area_ha * duration_years * discount_factor, 2),
        "total_carbon_max": round(max_rate * area_ha * duration_years * discount_factor, 2),
        "permanence_years": rates["permanence_years"],
        "estimated_revenue_usd": round(estimated_revenue, 0),
        "annual_revenue_usd": round(annual_revenue, 0),
        "price_per_tonne_usd": price_per_tonne,
        "methodology": f"IPCC AR6 {project_type.value} methodology",
        "confidence": "medium",
    }


def compare_project_types(area_ha: float = 100, duration_years: int = 10) -> dict:
    """Compare all carbon project types for given parameters.
    
    Returns ranking by total carbon and revenue.
    """
    results = []
    
    for project_type in CarbonProjectType:
        try:
            result = calculate_carbon_sequestration(
                project_type=project_type,
                area_ha=area_ha,
                duration_years=duration_years,
            )
            results.append(result)
        except Exception:
            continue
    
    # Sort by total carbon (descending)
    ranked = sorted(results, key=lambda x: x["total_carbon_tonnes"], reverse=True)
    
    return {
        "ranking": [r["project_type"] for r in ranked],
        "details": results,
        "best_carbon": ranked[0]["project_type"] if ranked else None,
        "best_revenue": max(results, key=lambda x: x["estimated_revenue_usd"])["project_type"] if results else None,
    }


# Project registry (in-memory for research mode)
_projects: Dict[str, CarbonProject] = {}


def register_project(project: CarbonProject) -> str:
    """Register a new carbon project."""
    _projects[project.id] = project
    return project.id


def get_project(project_id: str) -> Optional[CarbonProject]:
    """Get project by ID."""
    return _projects.get(project_id)


def list_projects(status: Optional[str] = None) -> list:
    """List all projects with optional status filter."""
    projects = list(_projects.values())
    if status:
        projects = [p for p in projects if p.status == status]
    return projects
