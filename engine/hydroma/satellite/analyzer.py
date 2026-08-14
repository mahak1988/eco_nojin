"""High-level satellite analysis orchestrator.

Combines providers and processors to deliver actionable insights
for farmers, pastoralists, and ecosystem managers.
"""
from datetime import date, timedelta
from dataclasses import dataclass
from typing import Optional
import numpy as np

from .providers.earth_search import EarthSearchProvider
from .providers.nasa_power import NasaPowerProvider
from .processors.indices import (
    calculate_ndvi, calculate_evi, calculate_savi,
    calculate_ndwi, calculate_nbr, interpret_ndvi
)


@dataclass
class FieldAnalysis:
    """Complete satellite analysis for a field location."""
    lat: float
    lon: float
    analysis_date: date
    ndvi: float
    evi: float
    savi: float
    ndwi: float
    nbr: float
    ndvi_class: dict
    cloud_cover: float
    data_quality: str  # "good", "moderate", "poor"
    recommendation: str


class SatelliteAnalyzer:
    """Orchestrates satellite data analysis."""
    
    def __init__(self):
        self.earth_search = EarthSearchProvider()
        self.nasa_power = NasaPowerProvider()
    
    def analyze_point(
        self,
        lat: float,
        lon: float,
        analysis_date: Optional[date] = None,
    ) -> FieldAnalysis:
        """Perform comprehensive satellite analysis for a geographic point.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            analysis_date: Target date (defaults to 7 days ago for data availability)
            
        Returns:
            Complete FieldAnalysis with indices and recommendations
        """
        if analysis_date is None:
            analysis_date = date.today() - timedelta(days=7)
        
        start_date = analysis_date - timedelta(days=14)
        end_date = analysis_date
        
        # Fetch Sentinel-2 imagery
        tiles = self.earth_search.search(
            lat=lat, lon=lon,
            start_date=start_date, end_date=end_date,
            max_cloud_cover=30.0,
            limit=5,
        )
        
        if not tiles:
            return self._fallback_analysis(lat, lon, analysis_date)
        
        # Get best tile (lowest cloud cover)
        best_tile_id = tiles[0].get("id", "unknown")
        tile = self.earth_search.fetch_tile(best_tile_id)
        
        if tile is None:
            return self._fallback_analysis(lat, lon, analysis_date)
        
        # Calculate vegetation indices
        bands = tile.bands
        ndvi_arr = calculate_ndvi(bands["red"], bands["nir"])
        evi_arr = calculate_evi(bands["red"], bands["nir"], bands["blue"])
        savi_arr = calculate_savi(bands["red"], bands["nir"])
        ndwi_arr = calculate_ndwi(bands["green"], bands["nir"])
        nbr_arr = calculate_nbr(bands["nir"], bands.get("swir16", bands["nir"]))
        
        # Aggregate to single values (median of valid pixels)
        ndvi = float(np.nanmedian(ndvi_arr))
        evi = float(np.nanmedian(evi_arr))
        savi = float(np.nanmedian(savi_arr))
        ndwi = float(np.nanmedian(ndwi_arr))
        nbr = float(np.nanmedian(nbr_arr))
        
        # Interpret results
        interpretation = interpret_ndvi(ndvi)
        recommendation = self._generate_recommendation(
            ndvi=ndvi, ndwi=ndwi, savi=savi,
            veg_class=interpretation["class"]
        )
        
        return FieldAnalysis(
            lat=lat,
            lon=lon,
            analysis_date=analysis_date,
            ndvi=round(ndvi, 3),
            evi=round(evi, 3),
            savi=round(savi, 3),
            ndwi=round(ndwi, 3),
            nbr=round(nbr, 3),
            ndvi_class=interpretation,
            cloud_cover=tile.cloud_cover,
            data_quality="good" if tile.cloud_cover < 10 else "moderate",
            recommendation=recommendation,
        )
    
    def _fallback_analysis(self, lat: float, lon: float, analysis_date: date) -> FieldAnalysis:
        """Provide fallback analysis when satellite data unavailable."""
        return FieldAnalysis(
            lat=lat,
            lon=lon,
            analysis_date=analysis_date,
            ndvi=0.0,
            evi=0.0,
            savi=0.0,
            ndwi=0.0,
            nbr=0.0,
            ndvi_class={"class": "unknown", "description": "No satellite data available"},
            cloud_cover=100.0,
            data_quality="poor",
            recommendation="Satellite data temporarily unavailable. Please try again later or provide manual field observations.",
        )
    
    def _generate_recommendation(
        self,
        ndvi: float,
        ndwi: float,
        savi: float,
        veg_class: str,
    ) -> str:
        """Generate actionable recommendation based on indices."""
        recommendations = []
        
        # Vegetation health
        if ndvi < 0.2:
            recommendations.append(
                "Vegetation cover is sparse. Consider planting drought-resistant "
                "species (millet, sorghum) and applying compost to improve soil fertility."
            )
        elif ndvi < 0.4:
            recommendations.append(
                "Moderate vegetation detected. Maintain current practices and consider "
                "supplemental irrigation during dry periods."
            )
        elif ndvi > 0.6:
            recommendations.append(
                "Excellent vegetation health. Continue current management and monitor "
                "for pest pressure in dense canopies."
            )
        
        # Water stress
        if ndwi < -0.2:
            recommendations.append(
                "Low moisture content detected. Prioritize irrigation and apply mulch "
                "to reduce evaporation."
            )
        elif ndwi > 0.2:
            recommendations.append(
                "Good water availability. Monitor for waterlogging in low-lying areas."
            )
        
        # Soil exposure
        if savi < 0.3 and veg_class == "sparse":
            recommendations.append(
                "Soil is exposed to erosion. Implement cover cropping or construct "
                "contour bunds to protect topsoil."
            )
        
        if not recommendations:
            recommendations.append(
                "Conditions appear stable. Continue regular monitoring."
            )
        
        return " | ".join(recommendations)


# Singleton
_analyzer: Optional[SatelliteAnalyzer] = None


def get_analyzer() -> SatelliteAnalyzer:
    """Get or create singleton analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SatelliteAnalyzer()
    return _analyzer
