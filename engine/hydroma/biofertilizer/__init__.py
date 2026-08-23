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
from .calculator import (
    NojinCalculator,
    NojinInput,
    NojinResult,
    SoilCondition,
    StrainProfile,
    StrainType,
    FormulationType,
    ApplicationMethod,
)

# Phase 1 Models
from .models import (
    NojinStrain,
    NojinFormulation,
    NojinApplicationPlan,
    NojinFieldTrial,
    NojinCalibrationRecord,
)

# Phase 2 Models (extended)
from .models import (
    NojinMaterial,
    NojinSoilType,
    NojinFormulationRecipe,
    NojinMaterialComposition,
    NojinApplicationGuide,
    NojinCostBenefit,
    NojinWaterSaving,
)

# Repositories (Phase 1 + Phase 2)
from .repositories import (
    NojinStrainRepository,
    NojinFormulationRepository,
    NojinApplicationPlanRepository,
    NojinFieldTrialRepository,
    NojinCalibrationRecordRepository,
    # Phase 2
    NojinMaterialRepository,
    NojinSoilTypeRepository,
    NojinFormulationRecipeRepository,
)

# Services (Phase 1)
from .services import NojinService
# Advanced Calculators (Phase 2)
from .advanced_calculator import (
    FormulationOptimizer,
    FormulationRequest,
    FormulationSolution,
    CostBenefitCalculator,
    CostBenefitResult,
    WaterSavingsCalculator,
    WaterSavingsResult,
    ScaleCalculator,
    ScaleResult,
)


__all__ = [
    # Calculator
    "NojinCalculator",
    "NojinInput",
    "NojinResult",
    "SoilCondition",
    "StrainProfile",
    "StrainType",
    "FormulationType",
    "ApplicationMethod",
    # Phase 1 Models
    "NojinStrain",
    "NojinFormulation",
    "NojinApplicationPlan",
    "NojinFieldTrial",
    "NojinCalibrationRecord",
    # Phase 2 Models
    "NojinMaterial",
    "NojinSoilType",
    "NojinFormulationRecipe",
    "NojinMaterialComposition",
    "NojinApplicationGuide",
    "NojinCostBenefit",
    "NojinWaterSaving",
    # Repositories
    "NojinStrainRepository",
    "NojinFormulationRepository",
    "NojinApplicationPlanRepository",
    "NojinFieldTrialRepository",
    "NojinCalibrationRecordRepository",
    # Phase 2
    "NojinMaterialRepository",
    "NojinSoilTypeRepository",
    "NojinFormulationRecipeRepository",
    # Services
    "NojinService",
    # Advanced Calculators
    "FormulationOptimizer",
    "FormulationRequest",
    "FormulationSolution",
    "CostBenefitCalculator",
    "CostBenefitResult",
    "WaterSavingsCalculator",
    "WaterSavingsResult",
    "ScaleCalculator",
    "ScaleResult",
]
