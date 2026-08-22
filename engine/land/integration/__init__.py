"""
Land Integration Module
========================
Connects engine/land/ to other engine modules.
"""

from .models import (
    SoilLayer,
    DeepSoilProfile,
    SoilIntegrationResult,
    SoilTexture,
    SalinityClass,
    DrainageClass,
)

from .soil_integrator import SoilIntegrator, SOILGRIDS_LAYERS

__all__ = [
    "SoilLayer",
    "DeepSoilProfile",
    "SoilIntegrationResult",
    "SoilTexture",
    "SalinityClass",
    "DrainageClass",
    "SoilIntegrator",
    "SOILGRIDS_LAYERS",
]


# Phase 2B: Climate Integration
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
