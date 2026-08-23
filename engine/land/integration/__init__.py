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
        SoilProfile,
        SoilLayer,
        DeepSoilProfile,
        SoilIntegrator,
    )
    __all__.extend([
        "SoilProfile",
        "SoilLayer",
        "DeepSoilProfile",
        "SoilIntegrator",
    ])
except ImportError:
    pass  # Soil modules not available

# ============================================================
# Phase 2B: Climate Integration
# ============================================================
try:
    from .climate_models import (
        ClimateProfile,
        ClimateIntegrationResult,
        MonthlyClimate,
        KoppenClimate,
        AridityClass,
        KOPPEN_DESCRIPTIONS,
    )
    from .climate_integrator import ClimateIntegrator
    __all__.extend([
        "ClimateProfile",
        "ClimateIntegrationResult",
        "MonthlyClimate",
        "KoppenClimate",
        "AridityClass",
        "KOPPEN_DESCRIPTIONS",
        "ClimateIntegrator",
    ])
except ImportError:
    pass  # Climate modules not available

# ============================================================
# Phase 2C: Comprehensive Analysis
# ============================================================
try:
    from .comprehensive_analyzer import (
        SoilSummary,
        ClimateSummary,
        TerrainSummary,
        CropSuitability,
        ComprehensiveLandAnalysis,
        LandUseCategory,
        CropType,
        ComprehensiveLandAnalyzer,
    )
    __all__.extend([
        "SoilSummary",
        "ClimateSummary",
        "TerrainSummary",
        "CropSuitability",
        "ComprehensiveLandAnalysis",
        "LandUseCategory",
        "CropType",
        "ComprehensiveLandAnalyzer",
    ])
except ImportError:
    pass  # Comprehensive modules not available

# ============================================================
# Phase 2D: Scientific Motors Hub
# ============================================================
try:
    from .motors_hub import (
        MotorStatus,
        MotorResult,
        UnifiedLandAnalysis,
        ScientificMotorsHub,
    )
    __all__.extend([
        "MotorStatus",
        "MotorResult",
        "UnifiedLandAnalysis",
        "ScientificMotorsHub",
    ])
except ImportError:
    pass  # Motors hub not available

# ============================================================
# Phase 3: Water Integration (adapters to existing modules)
# ============================================================
try:
    from .water_adapter import (
        WaterBalanceInput,
        WaterBalanceResult,
        RunoffInput,
        RunoffResult,
        GroundwaterInput,
        GroundwaterResult,
        UnifiedWaterAnalysis,
        WaterBalanceIntegrator,
        WatershedIntegrator,
        GroundwaterIntegrator,
        UnifiedWaterAnalyzer,
    )
    __all__.extend([
        "WaterBalanceInput",
        "WaterBalanceResult",
        "RunoffInput",
        "RunoffResult",
        "GroundwaterInput",
        "GroundwaterResult",
        "UnifiedWaterAnalysis",
        "WaterBalanceIntegrator",
        "WatershedIntegrator",
        "GroundwaterIntegrator",
        "UnifiedWaterAnalyzer",
    ])
except ImportError:
    pass  # Water modules not available
