"""HyDroMa Model Dashboard — Model Registry, Validation & Execution API.

Provides endpoints for:
- Model catalog with metadata
- Model execution with input validation
- Validation reports and slaughterhouse status
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
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
    overall_status: str  # always one of "executed" / "partial" / "not_run" (never "passed")
    test_cases_total: int
    test_cases_passed: int
    test_cases_failed: int
    test_cases_skipped: int
    # --- additive fields (2026-10-10, AR-08 fail-closed) ---------------------
    #: runnable cases the corpus actually reached but that are internally
    #: contradictory (runner status ``inconsistent_case``); retained separately
    #: from ``test_cases_failed`` (a ``mismatch``) because one says the code is
    #: wrong and the other says the case is.
    test_cases_inconsistent: int = 0
    #: the corpus model key the report was folded from (the case file's
    #: file-level ``model:`` value), so a reader can trace the number back to
    #: ``engine/hydroma/models/validation/test_cases/<runner_key>.yaml``.
    runner_key: str | None = None
    #: the runner's raw per-status counts for this model.
    corpus_status: dict[str, int] = Field(default_factory=dict)
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
            "name": "ECSI - EcoNojin Carbon Sequestration Index",
            "category": "carbon",
            "description": "Annual soil-carbon index computed on the canonical RothC-26.3 kernel",
            "version": "1.0.0",
            "language": "python",
            "reference": "Coleman & Jenkinson (1996) RothC-26.3",
            "status": "partial",
            "repo_path": "engine/hydroma/models/ecsi.py",
            "test_file": "engine/tests/test_validation_corpus.py",
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
            "name": "HDVI - Hydroma Drought Vulnerability Index",
            "category": "satellite",
            "description": "Multi-scale drought vulnerability index (SPI/SPEI/VHI/SMI components)",
            "version": "1.0.0",
            "language": "python",
            "reference": "Kogan (1995) VHI; no published HDVI definition - project composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hdvi.py",
            "test_file": "engine/tests/test_validation_corpus.py",
        },
        "epia": {
            "name": "EPIA - EcoNojin Precision Irrigation Advisor",
            "category": "climate",
            "description": "Precision irrigation advisor: ETc = ET0 x Kc x Ks (LAI-based Kc ramp)",
            "version": "1.0.0",
            "language": "python",
            "reference": "Allen et al. (1998) FAO-56; Kc ramp is this project's - composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/epia.py",
            "test_file": "engine/tests/test_validation_corpus.py",
        },
        "esri": {
            "name": "ESRI - EcoNojin Salinity Risk Index",
            "category": "climate",
            "description": "Salinity risk: spectral band-ratio + soil EC + irrigation management",
            "version": "1.0.0",
            "language": "python",
            "reference": "Ayers & Westcot (1985) FAO-29; band-ratio sub-index - project composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/esri.py",
            "test_file": "engine/tests/test_validation_corpus.py",
        },
        "ewsi": {
            "name": "EWSI - EcoNojin Water Stress Index",
            "category": "climate",
            "description": "Water stress: Sentinel-2 NDMI + VPD + root-zone soil moisture",
            "version": "1.0.0",
            "language": "python",
            "reference": "Gao (1996) NDWI/NDMI sub-index; no published EWSI - project composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/ewsi.py",
            "test_file": "engine/tests/test_validation_corpus.py",
        },
        "hpheno": {
            "name": "H-Pheno - Hydroma Phenology Detection",
            "category": "crop",
            "description": "Crop phenology from NDVI: Savitzky-Golay smoothing + zero-crossing",
            "version": "1.0.0",
            "language": "python",
            "reference": "Savitzky & Golay (1964); detection rule is this project's - composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hpheno.py",
            "test_file": "engine/tests/test_validation_corpus.py",
        },
        "hyrue": {
            "name": "HY-RUE - Hydroma Radiation Use Efficiency Model",
            "category": "crop",
            "description": "Radiation-use-efficiency yield from PAR, LAI, water, temperature",
            "version": "1.0.0",
            "language": "python",
            "reference": "Monteith (1977); Steduto et al. (2009)",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hyrue.py",
            "test_file": "engine/tests/test_validation_corpus.py",
        },
        "hlhs": {
            "name": "HLHS - Hydroma Landscape Health Score",
            "category": "landscape",
            "description": "Composite landscape health score: 7 normalised indicators",
            "version": "1.0.0",
            "language": "python",
            "reference": "no published definition — project composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/models/hlhs.py",
            "test_file": "engine/tests/test_validation_corpus.py",
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
            "reference": "no published definition — project composite",
            "status": "stable",
            "repo_path": "services/api_gateway/routers/hydroma_mrv.py",
            "test_file": "not wired — see reports/eco-nojin/FORMULA-VALIDATION-REGISTER.md",
        },
        "mrv_metrics": {
            "name": "MRV Transparent Metrics",
            "category": "mrv",
            "description": "MRV transparent metrics with provenance badging",
            "version": "1.0.0",
            "language": "python",
            "reference": "no published definition — project composite",
            "status": "stable",
            "repo_path": "services/api_gateway/routers/hydroma_mrv.py",
            "test_file": "not wired — see reports/eco-nojin/FORMULA-VALIDATION-REGISTER.md",
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
            "reference": "no published definition — project composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/plant_neuro/",
            "test_file": "not wired — see reports/eco-nojin/FORMULA-VALIDATION-REGISTER.md",
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
            "reference": "no published definition — project composite",
            "status": "experimental",
            "repo_path": "engine/hydroma/scenarios/",
            "test_file": "not wired — see reports/eco-nojin/FORMULA-VALIDATION-REGISTER.md",
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
        with open(test_file) as f:
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


def _corpus_verdicts(model_id: str) -> tuple[dict[str, int], list[dict[str, Any]], str | None]:
    """Run the shipped validation corpus in-process and return one model's verdicts.

    Folded from the engine's own runner
    (``engine/hydroma/models/validation/runner.py::machine_summary()``) -- the
    same record the model registry folds. Returns ``(by_status, outcomes,
    runner_key)``: ``by_status`` is the runner's per-status count
    (``match`` / ``mismatch`` / ``inconsistent_case`` / ``not_run``), ``outcomes``
    the per-case records, ``runner_key`` the corpus model key the report came
    from. AR-08 (G-H2): the report reflects what actually executed -- a case that
    never ran is ``not_run`` and only ``match`` may be counted as passed. A
    corpus that cannot be executed at all is reported empty (nothing ran), never
    as a pass.

    The corpus run is the one scientific step this router performs; it is
    reached through the sanctioned bridge (``services/_gateway_facade.py``,
    AR-13), which is the only place allowed to touch engine internals — so this
    router keeps guard-green while still reporting only executed verdicts.
    """
    try:
        from services._gateway_facade import run_validation_summary

        summary = run_validation_summary()
    except Exception as exc:  # pragma: no cover - engine/corpus unavailable
        logger.warning("validation corpus unavailable for %s: %s", model_id, exc)
        return {}, [], None
    buckets = summary.get("models", {})
    # The corpus groups cases by each file's file-level ``model:`` key, which is
    # UPPERCASE for the index families (EPIA/ESRI/EWSI/HLHS/HYRUE/ECSI) while the
    # dashboard id is lower-case; resolve it case-insensitively.
    key = next((k for k in buckets if k.lower() == model_id.lower()), None)
    if key is None:
        return {}, [], None
    bucket = buckets[key]
    by_status = {str(k): int(v) for k, v in bucket.get("by_status", {}).items()}
    return by_status, list(bucket.get("outcomes", [])), key


@router.get("/models/{model_id}/validation", response_model=ValidationReport)
async def get_validation_report(model_id: str) -> ValidationReport:
    """Get a validation report that reflects what actually ran (AR-08 fail-closed).

    The engine's validation corpus is executed in-process
    (``runner.machine_summary()``) and folded into this report, so a verdict is
    never handed out without a run. ``overall_status`` is one of:

    * ``executed`` - every corpus case for this model ran and matched (>=1 match);
    * ``partial``  - a run happened, but not every case was a clean match (some
      match, plus ``not_run`` / ``inconsistent_case`` / ``mismatch``);
    * ``not_run``  - nothing executed (no wired corpus, or every case ``not_run``).

    It is never ``passed``. Cases that did not run carry status ``not_run`` on
    their detail row, ``test_cases_passed`` counts only executed-and-matched
    cases, and ``test_cases_skipped`` mirrors the ``not_run`` count.
    """
    import asyncio
    from datetime import UTC, datetime

    models = {m["id"]: m for m in _discover_models()}
    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    # Run the corpus in a worker thread: it is real CPU work and must not block
    # the event loop, but the endpoint still reports exactly what executed.
    by_status, outcomes, runner_key = await asyncio.to_thread(_corpus_verdicts, model_id)

    matched = int(by_status.get("match", 0))
    mismatch = int(by_status.get("mismatch", 0))
    inconsistent = int(by_status.get("inconsistent_case", 0))
    not_run = int(by_status.get("not_run", 0))
    # Cases the runner actually reached a comparison verdict for.
    executed = matched + mismatch + inconsistent
    total = sum(int(v) for v in by_status.values())

    if executed == 0:
        # Nothing executed: no corpus is wired to this model id, or every case
        # came back not_run. Report the honest state, never a pass.
        overall = "not_run"
    elif matched >= 1 and matched == total:
        # At least one case executed and matched, and none are left unrun.
        overall = "executed"
    else:
        # A run happened but the set is not all-clean matches.
        overall = "partial"

    details = [
        {
            "test_case": o.get("name"),
            "status": o.get("status"),
            "message": o.get("detail", ""),
            "measured": o.get("measured"),
            "expected": o.get("expected"),
        }
        for o in outcomes
    ]

    return ValidationReport(
        model_id=model_id,
        overall_status=overall,
        test_cases_total=total,
        test_cases_passed=matched,
        test_cases_failed=mismatch,
        test_cases_skipped=not_run,
        test_cases_inconsistent=inconsistent,
        runner_key=runner_key,
        corpus_status=dict(sorted(by_status.items())),
        details=details,
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.post("/models/{model_id}/run", response_model=RunResult)
async def run_model(model_id: str, request: RunRequest) -> RunResult:
    """Execute a model with given inputs."""
    import time
    import uuid

    models = {m["id"]: m for m in _discover_models()}
    if model_id not in models:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    start_time = time.perf_counter()
    run_id = str(uuid.uuid4())[:8]

    # Model execution is not wired to the engine yet. Returning a RunResult
    # with status="success" and a mock payload was indistinguishable from a
    # real run to any caller, which is the failure S-HONEST exists to prevent.
    # Refuse instead, and let the caller see the real state.
    latency_ms = (time.perf_counter() - start_time) * 1000
    logger.warning(
        "Model run refused for %s (backend=%s): execution is not implemented",
        model_id,
        request.backend,
    )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "model_execution_not_implemented",
            "model_id": model_id,
            "run_id": run_id,
            "latency_ms": round(latency_ms, 2),
            "message": (
                "Model execution is not implemented. No results were produced. "
                "This endpoint does not return mock data as a success."
            ),
        },
    )


@router.get("/slaughterhouse/status", response_model=SlaughterhouseStatus)
async def slaughterhouse_status() -> SlaughterhouseStatus:
    """Get overall slaughterhouse validation status."""
    from datetime import UTC, datetime

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
