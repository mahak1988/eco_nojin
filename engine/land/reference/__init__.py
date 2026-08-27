"""
Reference Data Module
=====================

Geographic reference data for land analysis:
- Countries, regions, cities
- Terrain classifications
- Drainage standards
"""

from .data import (
    CITIES,
    COUNTRIES,
    DRAINAGE_STANDARDS,
    REGIONS,
    TERRAIN_CLASSIFICATIONS,
    find_nearest_city,
    get_all_reference_summary,
    get_city,
    get_country,
    get_region,
    list_cities,
    list_countries,
    list_regions,
)
from .models import City, Continent, Country, DrainageStandard, Region, TerrainClassification

__all__ = [
    "CITIES",
    "COUNTRIES",
    "DRAINAGE_STANDARDS",
    "REGIONS",
    "TERRAIN_CLASSIFICATIONS",
    "City",
    "Continent",
    "Country",
    "DrainageStandard",
    "Region",
    "TerrainClassification",
    "find_nearest_city",
    "get_all_reference_summary",
    "get_city",
    "get_country",
    "get_region",
    "list_cities",
    "list_countries",
    "list_regions",
]
