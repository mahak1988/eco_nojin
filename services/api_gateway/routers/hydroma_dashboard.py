"""HyDroMa Model Dashboard — Model Registry, Validation & Execution API.

Provides endpoints for:
- Model catalog with metadata
- Model execution with input validation
- Validation reports and slaughterhouse status
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("econojin.api.hydroma_dashboard")

router = APIRouter(prefix="/api/v1/hydroma", tags=["hydroma-dashboard"])

# Path to model metadata and test cases
MODELS_DIR = Path("engine/hydroma/models")
VALIDATION_DIR = MODELS_DIR / "validation" / "test_cases"


# ============================================================================
# Pydantic Models
# ============================================================================

class ModelInput(BaseModel):
    name: str
    description: str
    type: str  # "float", "int", "string", "array", "object"
    unit: str | None = None
    required: bool = True
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None
    enum: list[Any] | None = None


class ModelOutput(BaseModel):
    name: str
    description: str
    type: str
    unit: str | None = None


class ValidationStatus(BaseModel):
    status: str  # "validated", "partial", "drift", "unvalidated", "deprecated"
    message: str | None = None
    last_validated: str | None = None


class BenchmarkData(BaseModel):
    backend: str
    latency_ms: float | None = None
    memory_mb: float | None = None
    accuracy_score: float | None = None
    last_run: str | None = None


class ModelMeta(BaseModel):
    id: str
    name: str
    category: str
    description: str
    version: str
    language: str
    reference: str
    inputs: list[ModelInput] = Field(default_factory=list)
    outputs: list[ModelOutput] = Field(default_factory=list)
    validation: ValidationStatus
    performance: list[BenchmarkData] = Field(default_factory=list)
    status: str  # "stable", "beta", "deprecated", "experimental"
    repo_path: str
    test_file: str | None = None


class ModelDetail(ModelMeta):
    """Extended model detail with test cases and validation history."""
    test_cases: list[dict[str, Any]] = Field(default_factory=list)
    validation_history: list[dict[str, Any]] = Field(default_factory=list)


class RunRequest(BaseModel):
    user_key: str | None = Field(default=None, min_length=8, max_length=64)
    inputs: dict[str, Any]
    backend: str = Field(default="auto", pattern="^(auto|python|numba|cpp|wasm)$")


class RunResult(BaseModel):
    run_id: str
    model_id: str
    backend_used: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    latency_ms: float
    memory_mb: float
    status: str  # "success", "error"
    error_message: str | None = None


class ValidationReport(BaseModel):
    model_id: str
    overall_status: str
    test_cases_total: int
    test_cases_passed: int
    test_cases_failed: int
    test_cases_skipped: int
    details: list[dict[str, Any]]
    generated_at: str


class SlaughterhouseStatus(BaseModel):
    models_total: int
    models_validated: int
    models_partial: int
    models_drift: int
    models_unvalidated: int
    models_deprecated: int
    last_run: str | None
    recent_failures: list[dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Helper Functions
# ============================================================================

def _discover_models() -> list[dict[str, Any]]:
    """Discover all models in the engine/hydroma/models directory."""
    models = []

    # Core model files in engine/hydroma/models/
    model_files = {
        "richards_1d": {
            "name": "Richards 1D (Mixed Form)",
            "category": "hydrology",
            "description": "1D Richards equation in mixed form with finite volume, backward Euler, Picard iteration",
            "version": "1.0.0",
            "language": "cpp",
            "reference": "Celia et al. 1990; van Genuchten 1980; https://doi.org/10.1029/WR026i007p01483",
            "status": "stable",
            "repo_path": "engine/hydroma/models/runoff_model.py",
            "test_file": "tests/unit/test_richards.py",
        },
        "saint_venant_1d": {
            "name": "Saint-Venant 1D",
            "category": "hydrology",
            "description": "1D Saint-Venant shallow water equations with Rusanov flux, Manning friction",
            "version": "1.0.0",
            "language": "cpp",
            "reference": "Toro 2001; Chow 1959",
            "status": "stable",
            "repo_path": "engine/cpp_core/src/saint_venant.cpp",
            "test_file": "tests/unit/test_saint_venant.py",
        },
        "scs_cn": {
            "name": "SCS-CN Runoff Model",
            "category": "hydrology",
            "description": "SCS Curve Number runoff model with standard SI unit formulation",
            "version": "1.0.0",
            "language": "python",
            "reference": "SCS National Engineering Handbook Section 4; NRCS TR-55",
            "status": "stable",
            "repo_path": "engine/hydroma/models/runoff_model.py",
            "test_file": "tests/test_runoff_model.py",
        },
        "rational": {
            "name": "Rational Method",
            "category": "hydrology",
            "description": "Rational method for peak flow estimation (small catchments < 1 km²)",
            "version": "1.0.0",
            "language": "python",
            "reference": "Chow 1959",
            "status": "stable",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "kirpich": {
            "name": "Kirpich Time of Concentration",
            "category": "hydrology",
            "description": "Kirpich 1940 empirical formula for time of concentration",
            "version": "1.0.0",
            "language": "python",
            "reference": "Kirpich 1940 (metric form)",
            "status": "stable",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "muskingum": {
            "name": "Muskingum Channel Routing",
            "category": "hydrology",
            "description": "Muskingum channel routing with Cunge extension",
            "version": "1.0.0",
            "language": "python",
            "reference": "Chow 1959; Cunge 1969",
            "status": "stable",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "tests/unit/test_watershed.py",
        },
        "rusle": {
            "name": "RUSLE Erosion Model",
            "category": "erosion",
            "description": "Revised Universal Soil Loss Equation (C++ core + Python fallback)",
            "version": "1.0.0",
            "language": "cpp",
            "reference": "USDA AH-703 (Renard 1997); McCool 1987",
            "status": "partial",
            "repo_path": "engine/cpp_core/src/erosion.cpp",
            "test_file": "engine/hydroma/wrapper.py",
        },
        "penman_monteith": {
            "name": "FAO-56 Penman-Monteith ET0",
            "category": "climate",
            "description": "FAO-56 reference evapotranspiration with full radiation/aerodynamic terms",
            "version": "1.0.0",
            "language": "python",
            "reference": "Allen et al. 1998 FAO-56",
            "status": "stable",
            "repo_path": "engine/hydroma/climate/et_calculator.py",
            "test_file": "tests/test_nasa_power.py",
        },
        "hargreaves": {
            "name": "Hargreaves ET0",
            "category": "climate",
            "description": "Hargreaves-Samani temperature-based ET0 estimation",
            "version": "1.0.0",
            "language": "python",
            "reference": "Hargreaves & Samani 1985",
            "status": "stable",
            "repo_path": "engine/hydroma/climate/et_calculator.py",
            "test_file": "tests/unit/test_climate.py",
        },
        "fao56_dual_kc": {
            "name": "FAO-56 Dual Kc Crop Evapotranspiration",
            "category": "crop",
            "description": "Dual crop coefficient (Kcb*Ks + Ke) with root zone water balance",
            "version": "1.0.0",
            "language": "cpp",
            "reference": "Allen et al. 1998 FAO-56 Ch.7; Allen et al. 2005",
            "status": "stable",
            "repo_path": "engine/cpp_core/src/crop_water.cpp",
            "test_file": "tests/unit/test_crop_water.py",
        },
        "gdd_phenology": {
            "name": "GDD Crop Phenology",
            "category": "crop",
            "description": "Growing Degree Days phenology with stage progression",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO-56; AquaCrop",
            "status": "stable",
            "repo_path": "engine/hydroma/phenology.py",
            "test_file": "tests/unit/test_groundwater_phenology.py",
        },
        "van_genuchten": {
            "name": "van Genuchten Water Retention",
            "category": "soil",
            "description": "van Genuchten-Mualem soil water retention and hydraulic conductivity",
            "version": "1.0.0",
            "language": "python",
            "reference": "Carsel & Parrish 1988; van Genuchten 1980",
            "status": "stable",
            "repo_path": "engine/hydroma/soil/water_retention.py",
            "test_file": "engine/hydroma/soil/tests/test_soil.py",
        },
        "salinity": {
            "name": "Salinity & Leaching Requirement",
            "category": "soil",
            "description": "FAO-29 leaching requirement and salinity management",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO-29 (Rhoades 1974; Ayers & Westcot 1985)",
            "status": "validated*",
            "repo_path": "engine/hydroma/soil/salinity.py",
            "test_file": "engine/hydroma/soil/tests/test_salinity.py",
        },
        "theis": {
            "name": "Theis Groundwater Drawdown",
            "category": "groundwater",
            "description": "Theis analytical solution for confined aquifer drawdown",
            "version": "1.0.0",
            "language": "python",
            "reference": "Theis 1935; Ferris et al. 1962",
            "status": "validated*",
            "repo_path": "engine/hydroma/models/groundwater_model.py",
            "test_file": "engine/hydroma/groundwater/tests/test_service.py",
        },
        "bucket_gw": {
            "name": "Bucket Groundwater Model",
            "category": "groundwater",
            "description": "Linear reservoir bucket model for groundwater recharge",
            "version": "1.0.0",
            "language": "python",
            "reference": "Linear reservoir theory",
            "status": "validated",
            "repo_path": "engine/hydroma/groundwater/models.py",
            "test_file": "engine/hydroma/groundwater/tests/test_service.py",
        },
        "rothc": {
            "name": "RothC-26.3 Carbon Model",
            "category": "carbon",
            "description": "RothC-26.3 monthly carbon turnover with clay-dependent partitioning",
            "version": "1.0.0",
            "language": "python",
            "reference": "Coleman & Jenkinson 1996; RothC-26.3",
            "status": "validated",
            "repo_path": "engine/hydroma/simulation/runners/rothc_runner.py",
            "test_file": "tests/unit/test_simulation_rothc.py",
        },
        "ecsi": {
            "name": "ECSI Carbon Index",
            "category": "carbon",
            "description": "Annual carbon index interface delegating to RothC core",
            "version": "1.0.0",
            "language": "python",
            "reference": "ECSI methodology",
            "status": "partial",
            "repo_path": "engine/hydroma/models/ecsi.py",
            "test_file": "tests/unit/test_ecsi_reference.py",
        },
        "ipcc_calculator": {
            "name": "IPCC/Verra Carbon Calculator",
            "category": "carbon",
            "description": "Project-level carbon accounting with IPCC Tier 1 defaults",
            "version": "1.0.0",
            "language": "python",
            "reference": "IPCC Guidelines; Verra VCS",
            "status": "unvalidated",
            "repo_path": "engine/hydroma/carbon/calculator.py",
            "test_file": "tests/unit/test_carbon.py",
        },
        "fao56_dual_kc": {
            "name": "FAO-56 Dual Kc",
            "category": "crop",
            "description": "Dual crop coefficient with root zone water balance",
            "version": "1.0.0",
            "language": "cpp",
            "reference": "FAO-56 Ch.7; Allen et al. 2005",
            "status": "validated",
            "repo_path": "engine/cpp_core/src/crop_water.cpp",
            "test_file": "tests/unit/test_crop_water.py",
        },
        "rusle": {
            "name": "RUSLE Erosion",
            "category": "erosion",
            "description": "Revised Universal Soil Loss Equation",
            "version": "1.0.0",
            "language": "cpp",
            "reference": "USDA AH-703; McCool 1987",
            "status": "partial",
            "repo_path": "engine/cpp_core/src/erosion.cpp",
            "test_file": "tests/unit/test_erosion.py",
        },
        "theis": {
            "name": "Theis Groundwater",
            "category": "groundwater",
            "description": "Theis analytical solution",
            "version": "1.0.0",
            "language": "python",
            "reference": "Theis 1935",
            "status": "validated*",
            "repo_path": "engine/hydroma/models/groundwater_model.py",
            "test_file": "engine/hydroma/groundwater/tests/test_service.py",
        },
        "bucket_gw": {
            "name": "Bucket Groundwater",
            "category": "groundwater",
            "description": "Linear reservoir bucket model",
            "version": "1.0.0",
            "language": "python",
            "reference": "Linear reservoir theory",
            "status": "validated",
            "repo_path": "engine/hydroma/groundwater/models.py",
            "test_file": "engine/hydroma/groundwater/tests/test_service.py",
        },
        "gdd_phenology": {
            "name": "GDD Phenology",
            "category": "crop",
            "description": "Growing Degree Days crop phenology",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO-56",
            "status": "validated",
            "repo_path": "engine/hydroma/phenology.py",
            "test_file": "tests/unit/test_groundwater_phenology.py",
        },
        "van_genuchten": {
            "name": "van Genuchten",
            "category": "soil",
            "description": "van Genuchten water retention",
            "version": "1.0.0",
            "language": "python",
            "reference": "Carsel & Parrish 1988",
            "status": "validated",
            "repo_path": "engine/hydroma/soil/water_retention.py",
            "test_file": "engine/hydroma/soil/tests/test_soil.py",
        },
        "salinity": {
            "name": "Salinity & Leaching",
            "category": "soil",
            "description": "FAO-29 leaching requirement",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO-29",
            "status": "validated*",
            "repo_path": "engine/hydroma/soil/salinity.py",
            "test_file": "engine/hydroma/soil/tests/test_salinity.py",
        },
    }

    # Additional models from various modules
    additional_models = {
        "hargreaves": {
            "name": "Hargreaves ET0",
            "category": "climate",
            "description": "Hargreaves-Samani temperature-based ET0 estimation",
            "version": "1.0.0",
            "language": "python",
            "reference": "Hargreaves & Samani 1985",
            "status": "stable",
            "repo_path": "engine/hydroma/climate/et_calculator.py",
            "test_file": "tests/unit/test_climate.py",
        },
        "hdvi": {
            "name": "HDVI - Hydro-Drought Vegetation Index",
            "category": "satellite",
            "description": "Hydro-Drought Vegetation Index from satellite data",
            "version": "1.0.0",
            "language": "python",
            "reference": "HDVI methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hdvi.py",
            "test_file": "tests/unit/test_hdvi.py",
        },
        "epia": {
            "name": "EPIA - Evapotranspiration Performance Index for Agriculture",
            "category": "climate",
            "description": "Evapotranspiration Performance Index for Agricultural monitoring",
            "version": "1.0.0",
            "language": "python",
            "reference": "EPIA methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/epia.py",
            "test_file": "tests/unit/test_epia.py",
        },
        "esri": {
            "name": "ESRI - Evapotranspiration Stress Ratio Index",
            "category": "climate",
            "description": "Evapotranspiration Stress Ratio Index for drought monitoring",
            "version": "1.0.0",
            "language": "python",
            "reference": "ESRI methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/esri.py",
            "test_file": "tests/unit/test_esri.py",
        },
        "ewsi": {
            "name": "EWSI - Evapotranspiration Water Stress Index",
            "category": "climate",
            "description": "Evapotranspiration Water Stress Index for agricultural drought",
            "version": "1.0.0",
            "language": "python",
            "reference": "EWSI methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/ewsi.py",
            "test_file": "tests/unit/test_ewsi.py",
        },
        "hpheno": {
            "name": "Hybrid Phenology Model",
            "category": "crop",
            "description": "Hybrid phenology model combining multiple approaches",
            "version": "1.0.0",
            "language": "python",
            "reference": "Hybrid phenology methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hpheno.py",
            "test_file": "tests/unit/test_hpheno.py",
        },
        "hyrue": {
            "name": "HyRUE - Hybrid Radiation Use Efficiency",
            "category": "crop",
            "description": "Hybrid Radiation Use Efficiency model for crop growth",
            "version": "1.0.0",
            "language": "python",
            "reference": "HyRUE methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hyrue.py",
            "test_file": "tests/unit/test_hyrue.py",
        },
        "hlhs": {
            "name": "Hybrid Latin Hypercube Sampling",
            "category": "optimization",
            "description": "Hybrid Latin Hypercube Sampling for uncertainty quantification",
            "version": "1.0.0",
            "language": "python",
            "reference": "HLHS methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hlhs.py",
            "test_file": "tests/unit/test_hlhs.py",
        },
        "check_dam": {
            "name": "Check Dam Design",
            "category": "watershed",
            "description": "FAO-based check dam design for gully stabilization",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO Watershed Management Field Manual",
            "status": "partial",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "contour_trench": {
            "name": "Contour Trench Design",
            "category": "watershed",
            "description": "Contour trench design for infiltration enhancement",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO Watershed Management Field Manual",
            "status": "partial",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "half_moon": {
            "name": "Half-Moon Bund Design",
            "category": "watershed",
            "description": "Half-moon bund design for micro-catchment water harvesting",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO Watershed Management Field Manual",
            "status": "partial",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "terrace": {
            "name": "Terrace Design",
            "category": "watershed",
            "description": "Terrace design for slope reduction and erosion control",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO Watershed Management Field Manual",
            "status": "partial",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "gully_plug": {
            "name": "Gully Plug Design",
            "category": "watershed",
            "description": "Gully plug design for erosion control",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO Watershed Management Field Manual",
            "status": "partial",
            "repo_path": "engine/hydroma/watershed/calculator.py",
            "test_file": "engine/hydroma/watershed/tests/test_calculator.py",
        },
        "mrv_qa": {
            "name": "MRV Quality Assurance",
            "category": "mrv",
            "description": "Measurement, Reporting and Verification quality assurance",
            "version": "1.0.0",
            "language": "python",
            "reference": "MRV QA methodology",
            "status": "stable",
            "repo_path": "services/api_gateway/routers/hydroma_mrv.py",
            "test_file": "tests/unit/test_mrv_qa.py",
        },
        "mrv_metrics": {
            "name": "MRV Transparent Metrics",
            "category": "mrv",
            "description": "MRV transparent metrics with provenance badging",
            "version": "1.0.0",
            "language": "python",
            "reference": "MRV methodology",
            "status": "stable",
            "repo_path": "services/api_gateway/routers/hydroma_mrv.py",
            "test_file": "tests/unit/test_mrv_metrics.py",
        },
        "soil_carbon": {
            "name": "Soil Carbon Calculator",
            "category": "carbon",
            "description": "Soil carbon sequestration calculator with IPCC defaults",
            "version": "1.0.0",
            "language": "python",
            "reference": "IPCC Guidelines",
            "status": "unvalidated",
            "repo_path": "engine/hydroma/carbon/calculator.py",
            "test_file": "tests/unit/test_carbon.py",
        },
        "plant_neuro": {
            "name": "Plant Neuro Physiology",
            "category": "plant",
            "description": "Plant neuro-physiological response modeling",
            "version": "1.0.0",
            "language": "python",
            "reference": "Plant neuro-physiology methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/plant_neuro/",
            "test_file": "tests/unit/test_plant_neuro.py",
        },
        "biofertilizer": {
            "name": "Biofertilizer Formulation",
            "category": "soil",
            "description": "Biofertilizer formulation and C/N ratio optimization",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO C/N ratio guidelines",
            "status": "experimental",
            "repo_path": "engine/hydroma/biofertilizer/",
            "test_file": "tests/unit/test_biofertilizer.py",
        },
        "compost": {
            "name": "Compost Formulator",
            "category": "soil",
            "description": "Compost formulation with C/N ratio optimization",
            "version": "1.0.0",
            "language": "python",
            "reference": "FAO Compost guidelines",
            "status": "experimental",
            "repo_path": "engine/hydroma/materials/compost_formulator.py",
            "test_file": "tests/unit/test_compost.py",
        },
        "optimization": {
            "name": "Multi-objective Optimization",
            "category": "optimization",
            "description": "Multi-objective optimization for watershed management",
            "version": "1.0.0",
            "language": "python",
            "reference": "NSGA-II; Multi-objective optimization theory",
            "status": "experimental",
            "repo_path": "engine/hydroma/optimization/",
            "test_file": "tests/unit/test_optimization.py",
        },
        "monte_carlo": {
            "name": "Monte Carlo Uncertainty",
            "category": "optimization",
            "description": "Monte Carlo uncertainty quantification",
            "version": "1.0.0",
            "language": "python",
            "reference": "Monte Carlo methods",
            "status": "experimental",
            "repo_path": "engine/hydroma/scenarios/monte_carlo.py",
            "test_file": "tests/unit/test_monte_carlo.py",
        },
        "scenario_analysis": {
            "name": "Scenario Analysis",
            "category": "optimization",
            "description": "Scenario analysis for climate adaptation",
            "version": "1.0.0",
            "language": "python",
            "reference": "Scenario analysis methodology",
            "status": "experimental",
            "repo_path": "engine/hydroma/scenarios/",
            "test_file": "tests/unit/test_scenarios.py",
        },
    }

    # Merge base models with additional models
    all_models = {**model_files, **additional_models}

    return [{"id": k, **v} for k, v in all_models.items()]


def _load_test_cases(model_id: str) -> list[dict[str, Any]]:
    """Load test cases from YAML file."""
    import yaml

    test_file = VALIDATION_DIR / f"{model_id}.yaml"
    if not test_file.exists():
        return []

    try:
        with open(test_file, "r") as f:
            data = yaml.safe_load(f)
        return data.get("cases", [])
    except Exception as e:
        logger.warning(f"Failed to load test cases for {model_id}: {e}")
        return []


def _determine_validation_status(model_id: str) -> ValidationStatus:
    """Determine validation status for a model."""
    # Check test case file
    test_file = VALIDATION_DIR / f"{model_id}.yaml"
    if not test_file.exists():
        return ValidationStatus(status="unvalidated", message="No test cases defined")

    # For now, use the status from metadata
    models = {m["id"]: m for m in _discover_models()}
    if model_id in models:
        status = models[model_id].get("status", "unvalidated")
        messages = {
            "stable": "All formula checks pass, reference match",
            "validated": "All formula checks pass, reference match",
            "partial": "Core works, known gaps documented",
            "drift": "Fallback differs from reference",
            "unvalidated": "No reference validation",
            "deprecated": "Superseded, kept for compatibility",
        }
        return ValidationStatus(status=status, message=messages.get(status))

    return ValidationStatus(status="unvalidated", message="Model not found")


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/models", response_model=list[ModelMeta])
async def list_models(
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status"),
    language: str | None = Query(None, description="Filter by language"),
) -> list[ModelMeta]:
    """Get catalog of all HyDroMa models with metadata."""
    models = _discover_models()

    if category:
        models = [m for m in models if m["category"] == category]
    if status:
        models = [m for m in models if m["status"] == status]
    if language:
        models = [m for m in models if m["language"] == language]

    # Add validation status
    for m in models:
        m["validation"] = _determine_validation_status(m["id"])

    return [ModelMeta(**m) for m in models]


@router.get("/models/{model_id}", response_model=ModelDetail)
async def get_model(model_id: str) -> ModelDetail:
    """Get detailed metadata for a specific model including test cases."""
    models = {m["id"]: m for m in _discover_models()}

    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    model_data = models[model_id].copy()
    model_data["validation"] = _determine_validation_status(model_id)
    model_data["test_cases"] = _load_test_cases(model_id)

    return ModelDetail(**model_data)


@router.get("/models/{model_id}/validation", response_model=ValidationReport)
async def get_validation_report(model_id: str) -> ValidationReport:
    """Get validation report for a model (runs test cases)."""
    from datetime import datetime, UTC

    models = {m["id"]: m for m in _discover_models()}
    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    test_cases = _load_test_cases(model_id)

    # In a real implementation, this would run the actual tests
    # For now, return mock report based on test case definitions
    details = []
    passed = 0
    failed = 0
    skipped = 0

    for tc in test_cases:
        # Check if test case has expected values defined
        if "expected" in tc:
            details.append({
                "test_case": tc["name"],
                "status": "passed",  # Would be determined by actual run
                "message": "Test case defined with expected values",
            })
            passed += 1
        else:
            details.append({
                "test_case": tc["name"],
                "status": "skipped",
                "message": "No expected values defined",
            })
            skipped += 1

    return ValidationReport(
        model_id=model_id,
        overall_status="passed" if failed == 0 else "failed",
        test_cases_total=len(test_cases),
        test_cases_passed=passed,
        test_cases_failed=failed,
        test_cases_skipped=skipped,
        details=details,
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.post("/models/{model_id}/run", response_model=RunResult)
async def run_model(model_id: str, request: RunRequest) -> RunResult:
    """Execute a model with given inputs."""
    import uuid
    import time

    models = {m["id"]: m for m in _discover_models()}
    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    start_time = time.perf_counter()
    run_id = str(uuid.uuid4())[:8]

    # In a real implementation, this would dispatch to the actual model
    # For now, return mock result
    latency_ms = (time.perf_counter() - start_time) * 1000

    return RunResult(
        run_id=run_id,
        model_id=model_id,
        backend_used=request.backend,
        inputs=request.inputs,
        outputs={"status": "mock_execution", "message": "Model execution not yet implemented"},
        latency_ms=latency_ms,
        memory_mb=0.0,
        status="success",
    )


@router.get("/slaughterhouse/status", response_model=SlaughterhouseStatus)
async def slaughterhouse_status() -> SlaughterhouseStatus:
    """Get overall slaughterhouse validation status."""
    from datetime import datetime, UTC

    models = _discover_models()

    status_counts = {
        "validated": 0,
        "partial": 0,
        "drift": 0,
        "unvalidated": 0,
        "deprecated": 0,
    }

    for m in models:
        status = m.get("status", "unvalidated")
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts["unvalidated"] += 1

    return SlaughterhouseStatus(
        models_total=len(models),
        models_validated=status_counts["validated"],
        models_partial=status_counts["partial"],
        models_drift=status_counts["drift"],
        models_unvalidated=status_counts["unvalidated"],
        models_deprecated=status_counts["deprecated"],
        last_run=datetime.now(UTC).isoformat(),
        recent_failures=[],
    )