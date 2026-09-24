"""
Nojin Biofertilizer Module
===========================
Complete system for biofertilizer application optimization.

Components:
- calculator: Scientific computation engine
- models: 12 SQLAlchemy models (Phase 1 + Phase 2)
- repositories: CRUD operations
- services: Business logic with cross-phase integration
"""

# Core calculator (Phase 1)
# Advanced Calculators (Phase 2)
from .advanced_calculator import (
    CostBenefitCalculator,
    CostBenefitResult,
    FormulationOptimizer,
    FormulationRequest,
    FormulationSolution,
    ScaleCalculator,
    ScaleResult,
    WaterSavingsCalculator,
    WaterSavingsResult,
)
from .calculator import (
    ApplicationMethod,
    FormulationType,
    NojinCalculator,
    NojinInput,
    NojinResult,
    SoilCondition,
    StrainProfile,
    StrainType,
)

# Phase 1 Models
# Phase 2 Models (extended)
from .models import (
    NojinApplicationGuide,
    NojinApplicationPlan,
    NojinCalibrationRecord,
    NojinCostBenefit,
    NojinFieldTrial,
    NojinFormulation,
    NojinFormulationRecipe,
    NojinMaterial,
    NojinMaterialComposition,
    NojinSoilType,
    NojinStrain,
    NojinWaterSaving,
)

# Repositories (Phase 1 + Phase 2)
from .repositories import (
    NojinApplicationPlanRepository,
    NojinCalibrationRecordRepository,
    NojinFieldTrialRepository,
    NojinFormulationRecipeRepository,
    NojinFormulationRepository,
    # Phase 2
    NojinMaterialRepository,
    NojinSoilTypeRepository,
    NojinStrainRepository,
)

# Services (Phase 1)
from .services import NojinService

__all__ = [
    "ApplicationMethod",
    "CostBenefitCalculator",
    "CostBenefitResult",
    # Advanced Calculators
    "FormulationOptimizer",
    "FormulationRequest",
    "FormulationSolution",
    "FormulationType",
    "NojinApplicationGuide",
    "NojinApplicationPlan",
    "NojinApplicationPlanRepository",
    # Calculator
    "NojinCalculator",
    "NojinCalibrationRecord",
    "NojinCalibrationRecordRepository",
    "NojinCostBenefit",
    "NojinFieldTrial",
    "NojinFieldTrialRepository",
    "NojinFormulation",
    "NojinFormulationRecipe",
    "NojinFormulationRecipeRepository",
    "NojinFormulationRepository",
    "NojinInput",
    # Phase 2 Models
    "NojinMaterial",
    "NojinMaterialComposition",
    # Phase 2
    "NojinMaterialRepository",
    "NojinResult",
    # Services
    "NojinService",
    "NojinSoilType",
    "NojinSoilTypeRepository",
    # Phase 1 Models
    "NojinStrain",
    # Repositories
    "NojinStrainRepository",
    "NojinWaterSaving",
    "ScaleCalculator",
    "ScaleResult",
    "SoilCondition",
    "StrainProfile",
    "StrainType",
    "WaterSavingsCalculator",
    "WaterSavingsResult",
]
