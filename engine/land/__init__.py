"""
Land Intelligence Engine - Complete Module
==========================================

Version: 1.6.0

Modules:
- models: Pydantic V2 data structures
- dem_processor: DEM loading and processing
- slope_aspect: Slope/aspect analysis with TWI, TPI
- terrain_analysis: Advanced terrain analysis
- drainage: Strahler ordering, Horton ratios
- capability: USDA Land Capability Classification
- erosion_risk: Erosion risk estimation
- surface_water_analysis: Surface water analysis
- reference: Geographic reference data (countries, regions, cities)
"""

__version__ = "1.6.0"

# ═══════════════════════════════════════════════════════════════════
# Models and Enums
# ═══════════════════════════════════════════════════════════════════
from .capability import CapabilityAssessor

# ═══════════════════════════════════════════════════════════════════
# Processors and Analyzers
# ═══════════════════════════════════════════════════════════════════
from .dem_processor import DEMProcessor
from .drainage import DrainageAnalyzer
from .erosion_risk import estimate_erosion_risk
from .models import (
    CapabilityAssessment,
    CurvatureResult,
    DrainageAnalysis,
    DrainageDensityClass,
    DrainagePattern,
    ErosionRisk,
    LandCapabilityClass,
    LandformType,
    LandProfile,
    SlopeAspectResult,
    SlopeClass,
    StreamOrder,
    TerrainAnalysis,
    TerrainIndices,
    TerrainType,
)
from .slope_aspect import SlopeAspectAnalyzer
from .surface_water_analysis import SurfaceWaterAnalyzer
from .terrain_analysis import TerrainAnalyzer

# ═══════════════════════════════════════════════════════════════════
# Reference Data (optional)
# ═══════════════════════════════════════════════════════════════════
try:
    from .reference import (
        CITIES,
        COUNTRIES,
        DRAINAGE_STANDARDS,
        REGIONS,
        TERRAIN_CLASSIFICATIONS,
        City,
        Continent,
        Country,
        DrainageStandard,
        Region,
        TerrainClassification,
        find_nearest_city,
        get_all_reference_summary,
        get_city,
        get_country,
        get_region,
        list_cities,
        list_countries,
        list_regions,
    )

    _REFERENCE_AVAILABLE = True
except ImportError:
    _REFERENCE_AVAILABLE = False
    # Provide None values if reference is not available. These names are
    # classes, callables and containers when the optional .reference module
    # imports, and its absence is a supported deployment; the fallback type
    # genuinely varies, so the degradation is marked rather than restructured.
    Country = Region = City = Continent = None  # type: ignore[assignment,misc]
    TerrainClassification = DrainageStandard = None  # type: ignore[assignment,misc]
    COUNTRIES = REGIONS = CITIES = {}  # type: ignore[assignment]
    TERRAIN_CLASSIFICATIONS = DRAINAGE_STANDARDS = {}  # type: ignore[assignment]
    get_country = get_region = get_city = None  # type: ignore[assignment]
    list_countries = list_regions = list_cities = None  # type: ignore[assignment]
    find_nearest_city = get_all_reference_summary = None  # type: ignore[assignment]

# ═══════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════
__all__ = [
    "CITIES",
    "COUNTRIES",
    "DRAINAGE_STANDARDS",
    "REGIONS",
    "TERRAIN_CLASSIFICATIONS",
    "CapabilityAssessment",
    "CapabilityAssessor",
    "City",
    "Continent",
    # Reference (when available)
    "Country",
    "CurvatureResult",
    # Processors
    "DEMProcessor",
    "DrainageAnalysis",
    "DrainageAnalyzer",
    "DrainageDensityClass",
    "DrainagePattern",
    "DrainageStandard",
    "ErosionRisk",
    "LandCapabilityClass",
    # Models
    "LandProfile",
    "LandformType",
    "Region",
    "SlopeAspectAnalyzer",
    "SlopeAspectResult",
    "SlopeClass",
    "StreamOrder",
    "SurfaceWaterAnalyzer",
    "TerrainAnalysis",
    "TerrainAnalyzer",
    "TerrainClassification",
    "TerrainIndices",
    # Enums
    "TerrainType",
    "estimate_erosion_risk",
    "find_nearest_city",
    "get_all_reference_summary",
    "get_city",
    "get_country",
    "get_region",
    "list_cities",
    "list_countries",
    "list_regions",
]
