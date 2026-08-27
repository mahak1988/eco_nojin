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
    # Provide None values if reference is not available
    Country = Region = City = Continent = None
    TerrainClassification = DrainageStandard = None
    COUNTRIES = REGIONS = CITIES = {}
    TERRAIN_CLASSIFICATIONS = DRAINAGE_STANDARDS = {}
    get_country = get_region = get_city = None
    list_countries = list_regions = list_cities = None
    find_nearest_city = get_all_reference_summary = None

# ═══════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════
__all__ = [
    # Models
    "LandProfile",
    "TerrainAnalysis",
    "CapabilityAssessment",
    "DrainageAnalysis",
    "SlopeAspectResult",
    "CurvatureResult",
    "TerrainIndices",
    "StreamOrder",

    # Enums
    "TerrainType",
    "SlopeClass",
    "DrainagePattern",
    "DrainageDensityClass",
    "ErosionRisk",
    "LandCapabilityClass",
    "LandformType",

    # Processors
    "DEMProcessor",
    "SlopeAspectAnalyzer",
    "TerrainAnalyzer",
    "DrainageAnalyzer",
    "CapabilityAssessor",
    "estimate_erosion_risk",
    "SurfaceWaterAnalyzer",

    # Reference (when available)
    "Country",
    "Region",
    "City",
    "Continent",
    "TerrainClassification",
    "DrainageStandard",
    "COUNTRIES",
    "REGIONS",
    "CITIES",
    "TERRAIN_CLASSIFICATIONS",
    "DRAINAGE_STANDARDS",
    "get_country",
    "get_region",
    "get_city",
    "list_countries",
    "list_regions",
    "list_cities",
    "find_nearest_city",
    "get_all_reference_summary",
]
