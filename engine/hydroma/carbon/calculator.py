"""Carbon sequestration calculator for project-level estimation.

Implements methodologies from:
- Verra VCS (Verified Carbon Standard)
- Gold Standard
- IPCC Guidelines for National Greenhouse Gas Inventories

Project types supported:
- Afforestation/Reforestation
- Soil Carbon (no-till, cover crops, compost)
- Biochar
- Agroforestry

Role: **Project-level accounting & screening** — uses IPCC Tier 1 default
sequestration rates and regional adjustment factors for rapid project
screening and economic valuation. Does NOT simulate process-based
soil carbon dynamics; uses fixed annual rates per project type.

For process-based, site-specific soil carbon dynamics with monthly
climate forcing, use:
    - engine.hydroma.simulation.runners.rothc_runner.run_rothc (canonical)
    - engine.hydroma.models.ecsi.ECSI (annual interface, delegates to above)

LIMITATIONS:
- These are regional averages for planning/estimation only.
- Actual sequestration depends on species, soil, climate, and management.
- Do NOT use these values for certified carbon credit issuance without
  project-specific measurement and third-party verification.
"""

import logging
import math
import threading
import uuid
from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


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
    verification_date: datetime | None = None
    verifier: str = ""

    # Results
    estimated_carbon_tonnes: float = 0.0
    annual_rate_tonnes: float = 0.0
    methodology: str = ""

    data_source: str = 'modelled'
    model: str = 'carbon sequestration accounting'
    computed: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


# Carbon sequestration rates (tonnes CO2/ha/year) by project type
# Based on IPCC AR6 and peer-reviewed literature
#
# LIMITATIONS:
# - These are regional averages for planning/estimation only.
# - Actual sequestration depends on species, soil, climate, and management.
# - Do NOT use these values for certified carbon credit issuance without
#   project-specific measurement and third-party verification.
SEQUESTRATION_RATES: dict[CarbonProjectType, dict[str, float]] = {
    CarbonProjectType.AFFORESTATION: {
        "rate": 8.0,  # tonnes CO2/ha/year (tropical/temperate average)
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
        "rate": 0.8,  # Lower rate but more certain
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
        "rate": 3.0,  # One-time application
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
#
# LIMITATIONS — read before using these numbers:
# - These are *illustrative planning defaults*, not market quotations. They
#   carry no as-of date, no source citation, and no variance range.
# - The observed market has moved sharply and in both directions. As of the
#   World Bank Pink Sheet release of 2 September 2026: DAP 793.50 USD/t,
#   urea 390.00 USD/t, Fertilizers index 146.4 (2010=100). Voluntary carbon
#   average reported prices were ~6.34 USD/t for 2024, with the MSCI Carbon
#   Credit Price Index averaging ~3.5 USD/t in 2025 — far below every value
#   below. Do not present these defaults as achievable prices.
# - Nothing here is a VVB determination, a clearing price, or a valuation.
#   Using them in a monetised "impact" figure produces a number with no
#   evidentiary basis, which is the exact failure mode the EU Empowering
#   Consumers Directive ((EU) 2024/825, applicable from 27 September 2026)
#   prohibits. See reports/HYDROMA_NOJIN_CONSULTING_FRAMEWORK_FA.md §0.2.
# - Prefer passing a caller-supplied price table (see EconomyRequest.prices)
#   over relying on these defaults.
CARBON_PRICES: dict[str, float] = {
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

    Raises:
        ValueError: If the project type, region, area or duration is not
            admissible. None of them is defaulted: an unrecognised region
            priced as temperate is a silent 23 % error in the headline figure,
            and a negative area turns a sink into a source.
    """
    rates = SEQUESTRATION_RATES.get(project_type)
    if not rates:
        raise ValueError(f"Unknown project type: {project_type}")

    if area_ha < 0:
        raise ValueError(
            f"area_ha must not be negative, got {area_ha!r}: a negative area "
            f"reports the site as a carbon source"
        )
    if duration_years <= 0:
        raise ValueError(
            f"duration_years must be positive, got {duration_years!r}: a "
            f"non-positive credit period has no defensible total"
        )

    # Regional adjustment factor
    region_factors = {
        "tropical": 1.3,  # Higher growth rates
        "temperate": 1.0,  # Baseline
        "arid": 0.6,  # Lower growth rates
    }
    if region not in region_factors:
        raise ValueError(f"Unknown region: {region!r}; use one of {sorted(region_factors)}")
    factor = region_factors[region]

    # Apply discount for uncertainty (conservative approach)
    discount_factor = 0.85  # 15% discount for uncertainty

    # Biochar is a one-time application, so its lifetime total and its reported
    # band are per-hectare one-off quantities; only the annual figure is
    # amortised over the credit period. Every other type accumulates per year,
    # so total and band both carry duration_years and the annual figure does not.
    if project_type == CarbonProjectType.BIOCHAR:
        total_carbon = rates["rate"] * factor * area_ha
        band_min = rates["min"] * factor * area_ha
        band_max = rates["max"] * factor * area_ha
    else:
        total_carbon = rates["rate"] * factor * area_ha * duration_years
        band_min = rates["min"] * factor * area_ha * duration_years
        band_max = rates["max"] * factor * area_ha * duration_years

    estimated_carbon = total_carbon * discount_factor
    # The annual figure is the reported total spread over the credit period, so
    # it carries the same uncertainty discount and the same basis as the total.
    annual_total = estimated_carbon / duration_years

    # Economic value
    price_per_tonne = CARBON_PRICES["voluntary_market"]
    estimated_revenue = estimated_carbon * price_per_tonne
    annual_revenue = annual_total * price_per_tonne

    return {
        "project_type": project_type.value,
        "area_ha": area_ha,
        "duration_years": duration_years,
        "region": region,
        "annual_rate_tonnes": round(annual_total, 2),
        "total_carbon_tonnes": round(estimated_carbon, 2),
        "total_carbon_min": round(band_min * discount_factor, 2),
        "total_carbon_max": round(band_max * discount_factor, 2),
        "permanence_years": rates["permanence_years"],
        "estimated_revenue_usd": round(estimated_revenue, 0),
        "annual_revenue_usd": round(annual_revenue, 0),
        "price_per_tonne_usd": price_per_tonne,
        "methodology": f"IPCC AR6 {project_type.value} methodology",
        "confidence": "medium",
    }


def _ranking_value(result: dict) -> float:
    """Sort key for a comparison entry; a type that failed has nothing to rank on."""
    value = result["total_carbon_tonnes"]
    return -math.inf if value is None else value


def compare_project_types(area_ha: float = 100, duration_years: int = 10) -> dict:
    """Compare all carbon project types for given parameters.

    Returns ranking by total carbon and revenue. A project type that cannot be
    evaluated keeps its place in ``ranking`` with a null carbon total and is
    named in ``failures``: a comparison that silently dropped the type the
    caller was about to choose is worse than one that raises.
    """
    results = []
    failures = []

    for project_type in CarbonProjectType:
        try:
            result = calculate_carbon_sequestration(
                project_type=project_type,
                area_ha=area_ha,
                duration_years=duration_years,
            )
        except Exception as exc:
            logger.error(
                "carbon project type failed comparison",
                extra={"project_type": project_type.value, "error": str(exc)},
            )
            result = {
                "project_type": project_type.value,
                "total_carbon_tonnes": None,
                "estimated_revenue_usd": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
            failures.append(result)
        results.append(result)

    # Sort by total carbon (descending), failures last
    ranked = sorted(results, key=_ranking_value, reverse=True)
    scored = [r for r in ranked if r["total_carbon_tonnes"] is not None]

    return {
        "ranking": [r["project_type"] for r in ranked],
        "details": results,
        "failures": failures,
        "best_carbon": scored[0]["project_type"] if scored else None,
        "best_revenue": max(scored, key=lambda x: x["estimated_revenue_usd"])["project_type"]
        if scored
        else None,
    }


class _ScopedProjectStore(MutableMapping[str, CarbonProject]):
    """In-memory project store scoped to the calling thread.

    A module-level dict is one store for every thread and every request a worker
    thread serves, so a multi-tenant gateway cannot keep tenants apart and
    concurrent registrations observe each other half-written. This store keeps
    one mapping per thread. It is a scratchpad rather than a register: anything
    that must outlive the process belongs in a repository set with
    :func:`set_repository`.
    """

    def __init__(self) -> None:
        self._local = threading.local()

    @property
    def _store(self) -> dict[str, CarbonProject]:
        store = getattr(self._local, "store", None)
        if store is None:
            store = {}
            self._local.store = store
        return store

    def __getitem__(self, project_id: str) -> CarbonProject:
        return self._store[project_id]

    def __setitem__(self, project_id: str, project: CarbonProject) -> None:
        self._store[project_id] = project

    def __delitem__(self, project_id: str) -> None:
        del self._store[project_id]

    def __iter__(self) -> Iterator[str]:
        return iter(dict(self._store))

    def __len__(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()


# Project registry. When a repository is configured it is the only source of
# truth: its errors propagate to the caller, because a write that falls back to
# process memory returns an id for a row that was never stored. The in-memory
# store is per-thread (see _ScopedProjectStore) and exists for single-process
# screening only.
_projects: MutableMapping[str, CarbonProject] = _ScopedProjectStore()
_repository = None


def set_repository(repository) -> None:
    """Set the carbon project repository for DB-backed persistence."""
    global _repository
    _repository = repository


def register_project(project: CarbonProject) -> str:
    """Register a new carbon project.

    Returns the durable identifier the registry assigned. A repository failure
    raises; it is never reported as a successful in-memory registration.
    """
    if _repository is not None:
        db_project = _repository.create_project(
            project_id=project.id,
            name=project.name,
            project_type=project.project_type.value,
            area_ha=project.area_ha,
            status=project.status,
            estimated_carbon_tonnes=project.estimated_carbon_tonnes,
            annual_rate_tonnes=project.annual_rate_tonnes,
            methodology=project.methodology,
        )
        return str(db_project.id)
    _projects[project.id] = project
    return project.id


def get_project(project_id: str) -> CarbonProject | None:
    """Get project by ID. Returns None only when the registry has no such project."""
    if _repository is None:
        return _projects.get(project_id)
    db_project = _repository.get_project(project_id)
    if db_project is None:
        return None
    return CarbonProject(
        id=db_project.project_id,
        name=db_project.name,
        project_type=CarbonProjectType(db_project.project_type or "afforestation"),
        area_ha=db_project.area_hectares or 0.0,
        status=db_project.status or "draft",
        estimated_carbon_tonnes=db_project.estimated_carbon_tonnes or 0.0,
        annual_rate_tonnes=db_project.annual_rate_tonnes or 0.0,
        methodology=db_project.methodology or "",
        created_at=db_project.created_at or datetime.utcnow(),
    )


def list_projects(status: str | None = None) -> list:
    """List all projects with optional status filter."""
    if _repository is not None:
        return [
            CarbonProject(
                id=p.project_id,
                name=p.name,
                project_type=CarbonProjectType(p.project_type or "afforestation"),
                area_ha=p.area_hectares or 0.0,
                status=p.status or "draft",
                estimated_carbon_tonnes=p.estimated_carbon_tonnes or 0.0,
                annual_rate_tonnes=p.annual_rate_tonnes or 0.0,
                methodology=p.methodology or "",
                created_at=p.created_at or datetime.utcnow(),
            )
            for p in _repository.list_projects(status=status)
        ]
    projects = list(_projects.values())
    if status:
        projects = [p for p in projects if p.status == status]
    return projects
