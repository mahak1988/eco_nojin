"""
Land Intelligence Engine - Complete Module
==========================================

Version: 1.5.0

Modules:
- models: Pydantic V2 data structures
- dem_processor: DEM loading and processing
- slope_aspect: 7-class USDA slope analysis, TWI, TPI, landforms
- terrain_analysis: Advanced terrain analysis
- drainage: Strahler ordering, Horton ratios, Kirpich Tc
- capability: USDA Land Capability Classification
- reference: Geographic reference data (countries, regions, cities)
"""

from .models import (
    LandProfile,
    TerrainAnalysis,
    CapabilityAssessment,
    DrainageAnalysis,
    SlopeAspectResult,
    CurvatureResult,
    TerrainIndices,
    StreamOrder,
    TerrainType,
    SlopeClass,
    DrainagePattern,
    DrainageDensityClass,
    ErosionRisk,
    LandCapabilityClass,
    LandformType,
)

from .dem_processor import DEMProcessor
from .slope_aspect import SlopeAspectCalculator
from .terrain_analysis import TerrainAnalyzer
from .drainage import DrainageAnalyzer
from .capability import CapabilityAssessor

from .reference import (
    Country, Region, City, Continent,
    TerrainClassification, DrainageStandard,
    COUNTRIES, REGIONS, CITIES,
    TERRAIN_CLASSIFICATIONS, DRAINAGE_STANDARDS,
    get_country, get_region, get_city,
    list_countries, list_regions, list_cities,
    find_nearest_city, get_all_reference_summary,
)

__all__ = [
    # Models
    "LandProfile", "TerrainAnalysis", "CapabilityAssessment",
    "DrainageAnalysis", "SlopeAspectResult", "CurvatureResult",
    "TerrainIndices", "StreamOrder",
    # Enums
    "TerrainType", "SlopeClass", "DrainagePattern",
    "DrainageDensityClass", "ErosionRisk", "LandCapabilityClass",
    "LandformType",
    # Processors
    "DEMProcessor", "SlopeAspectCalculator", "TerrainAnalyzer",
    "DrainageAnalyzer", "CapabilityAssessor",
    # Reference models
    "Country", "Region", "City", "Continent",
    "TerrainClassification", "DrainageStandard",
    # Reference data
    "COUNTRIES", "REGIONS", "CITIES",
    "TERRAIN_CLASSIFICATIONS", "DRAINAGE_STANDARDS",
    # Reference functions
    "get_country", "get_region", "get_city",
    "list_countries", "list_regions", "list_cities",
    "find_nearest_city", "get_all_reference_summary",
]

__version__ = "1.5.0"
