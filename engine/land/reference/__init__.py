"""
Reference Data Module
=====================

Geographic reference data for land analysis:
- Countries, regions, cities
- Terrain classifications
- Drainage standards
"""

from .models import (
    Country, Region, City, Continent,
    TerrainClassification, DrainageStandard
)

from .data import (
    COUNTRIES, REGIONS, CITIES,
    TERRAIN_CLASSIFICATIONS, DRAINAGE_STANDARDS,
    get_country, get_region, get_city,
    list_countries, list_regions, list_cities,
    find_nearest_city, get_all_reference_summary
)

__all__ = [
    "Country", "Region", "City", "Continent",
    "TerrainClassification", "DrainageStandard",
    "COUNTRIES", "REGIONS", "CITIES",
    "TERRAIN_CLASSIFICATIONS", "DRAINAGE_STANDARDS",
    "get_country", "get_region", "get_city",
    "list_countries", "list_regions", "list_cities",
    "find_nearest_city", "get_all_reference_summary",
]
