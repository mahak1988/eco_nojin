"""
Land Integration Layer
=======================
Connects engine/land/ to scientific modules:
- Soil (Phase 2A)
- Climate (Phase 2B)
- Water (Phase 3)

Architecture:
- Adapters (not duplicates) to existing modules
- Graceful degradation when modules unavailable
- Standard result formats
"""

from __future__ import annotations

__all__ = []

# ============================================================
# Phase 2A: Soil Integration
# ============================================================
try:
    from .soil_integrator import (
        DeepSoilProfile,
        SoilIntegrator,
        SoilLayer,
        SoilProfile,
    )
    __all__.extend([
        "DeepSoilProfile",
        "SoilIntegrator",
        "SoilLayer",
        "SoilProfile",
    ])
except ImportError:
    pass  # Soil modules not available

# ============================================================
# Phase 2B: Climate Integration
# ============================================================
try:
    from .climate_integrator import ClimateIntegrator
    from .climate_models import (
        KOPPEN_DESCRIPTIONS,
        AridityClass,
        ClimateIntegrationResult,
        ClimateProfile,
        KoppenClimate,
        MonthlyClimate,
    )
    __all__.extend([
        "KOPPEN_DESCRIPTIONS",
        "AridityClass",
        "ClimateIntegrationResult",
        "ClimateIntegrator",
        "ClimateProfile",
        "KoppenClimate",
        "MonthlyClimate",
    ])
except ImportError:
    pass  # Climate modules not available

# ============================================================
# Phase 2C: Comprehensive Analysis
# ============================================================
try:
    from .comprehensive_analyzer import (
        ClimateSummary,
        ComprehensiveLandAnalysis,
        ComprehensiveLandAnalyzer,
        CropSuitability,
        CropType,
        LandUseCategory,
        SoilSummary,
        TerrainSummary,
    )
    __all__.extend([
        "ClimateSummary",
        "ComprehensiveLandAnalysis",
        "ComprehensiveLandAnalyzer",
        "CropSuitability",
        "CropType",
        "LandUseCategory",
        "SoilSummary",
        "TerrainSummary",
    ])
except ImportError:
    pass  # Comprehensive modules not available

# ============================================================
# Phase 2D: Scientific Motors Hub
# ============================================================
try:
    from .motors_hub import (
        MotorResult,
        MotorStatus,
        ScientificMotorsHub,
        UnifiedLandAnalysis,
    )
    __all__.extend([
        "MotorResult",
        "MotorStatus",
        "ScientificMotorsHub",
        "UnifiedLandAnalysis",
    ])
except ImportError:
    pass  # Motors hub not available

# ============================================================
# Phase 3: Water Integration (adapters to existing modules)
# ============================================================
try:
    from .water_adapter import (
        GroundwaterInput,
        GroundwaterIntegrator,
        GroundwaterResult,
        RunoffInput,
        RunoffResult,
        UnifiedWaterAnalysis,
        UnifiedWaterAnalyzer,
        WaterBalanceInput,
        WaterBalanceIntegrator,
        WaterBalanceResult,
        WatershedIntegrator,
    )
    __all__.extend([
        "GroundwaterInput",
        "GroundwaterIntegrator",
        "GroundwaterResult",
        "RunoffInput",
        "RunoffResult",
        "UnifiedWaterAnalysis",
        "UnifiedWaterAnalyzer",
        "WaterBalanceInput",
        "WaterBalanceIntegrator",
        "WaterBalanceResult",
        "WatershedIntegrator",
    ])
except ImportError:
    pass  # Water modules not available
