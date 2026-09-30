"""High-level satellite analysis orchestrator.

Combines providers and processors to deliver actionable insights
for farmers, pastoralists, and ecosystem managers.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import numpy as np

from .processors.indices import (
    calculate_evi,
    calculate_nbr,
    calculate_ndvi,
    calculate_ndwi,
    calculate_savi,
    interpret_ndvi,
)
from .providers.earth_search import EarthSearchProvider
from .providers.nasa_power import NasaPowerProvider

logger = logging.getLogger(__name__)


@dataclass
class FieldAnalysis:
    """Complete satellite analysis for a field location."""

    lat: float | None = None
    lon: float | None = None
    analysis_date: date = None
    #: None means "not measured" -- no usable pixels, or no scene retrieved.
    #: It is deliberately not 0.0: zero is a real reading for every one of these
    #: indices, and interpret_ndvi(0.0) classifies as bare soil, so a zero would
    #: turn a missing observation into a confident agronomic judgement.
    ndvi: float | None = None
    evi: float | None = None
    savi: float | None = None
    ndwi: float | None = None
    nbr: float | None = None
    ndvi_class: dict = None
    cloud_cover: float | None = None
    data_quality: str | None = None
    recommendation: str | None = None
    data_source: str = "simulated"
    quality_flags: dict[str, Any] | None = None


class SatelliteAnalyzer:
    """Orchestrates satellite data analysis."""

    def __init__(self):
        self.earth_search = EarthSearchProvider()
        self.nasa_power = NasaPowerProvider()

    def analyze_point(
        self,
        lat: float,
        lon: float,
        analysis_date: date | None = None,
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
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
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
        swir_band = bands.get("swir16") or bands.get("swir22") or bands["nir"]
        nbr_arr = calculate_nbr(bands["nir"], swir_band)

        # Aggregate to the median of valid pixels. Cloud-masked pixels are NaN and
        # are excluded by nanmedian; the index functions used to convert those NaNs
        # to 0.0, so a cloudy scene was averaged in as bare soil and produced a
        # recommendation to plant drought-resistant species.
        with np.errstate(invalid="ignore"):
            ndvi = float(np.nanmedian(ndvi_arr))
            evi = float(np.nanmedian(evi_arr))
            savi = float(np.nanmedian(savi_arr))
            ndwi = float(np.nanmedian(ndwi_arr))
            nbr = float(np.nanmedian(nbr_arr))

        # An entirely cloudy scene leaves nothing to aggregate. Report it as
        # unusable rather than emitting NaN into the interpretation, where
        # every comparison against NaN is False and the first branch always wins.
        if not all(np.isfinite(v) for v in (ndvi, evi, savi, ndwi, nbr)):
            logger.warning("no valid (unclouded) pixels in the tile for %s, %s", lat, lon)
            return self._all_clouded_analysis(
                lat,
                lon,
                analysis_date,
                tile.cloud_cover,
                tile.data_source,
                getattr(tile, "quality_flags", None),
            )

        # Interpret results
        interpretation = interpret_ndvi(ndvi)
        recommendation = self._generate_recommendation(
            ndvi=ndvi, ndwi=ndwi, savi=savi, veg_class=interpretation["class"]
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
            quality_flags=getattr(tile, "quality_flags", None),
            # Real Sentinel-2 pixels were retrieved and the indices above were
            # computed from them. The previous hard-coded "modelled" was the
            # opposite error: a measurement was presented as a simulation,
            # which tells a reader to discount a number that is fine.
            data_source="measured",
        )

    def _all_clouded_analysis(
        self,
        lat: float,
        lon: float,
        analysis_date: date,
        cloud_cover: float,
        data_source: str,
        quality_flags: dict | None,
    ) -> FieldAnalysis:
        """Every pixel was cloud or invalid, so no index could be computed.

        The values are ``None``, not 0.0. A zero here is not a neutral answer:
        ``interpret_ndvi(0.0)`` classifies as bare soil, and the recommendation
        path would then advise planting. ``None`` says "not measured".
        """
        return FieldAnalysis(
            lat=lat,
            lon=lon,
            analysis_date=analysis_date,
            ndvi=None,
            evi=None,
            savi=None,
            ndwi=None,
            nbr=None,
            ndvi_class={
                "class": "unknown",
                "description": "No unclouded pixels available in any retrieved scene",
            },
            cloud_cover=cloud_cover,
            data_quality="poor",
            recommendation=(
                "Every retrieved scene was fully clouded, so vegetation indices could "
                "not be computed. Please try again on a clearer day or provide manual "
                "field observations."
            ),
            quality_flags={"reason": "all_pixels_clouded", **(quality_flags or {})},
            # No index was computed: every retrieved scene was fully clouded
            # and the values above are None. Labelling this "modelled" claimed
            # a simulation ran.
            data_source="unavailable",
        )

    def _fallback_analysis(self, lat: float, lon: float, analysis_date: date) -> FieldAnalysis:
        """Provide fallback analysis when satellite data is unavailable.

        The index values are ``None``, not 0.0. Zero is a real, meaningful reading
        for every one of these indices, and ``interpret_ndvi(0.0)`` returns
        "bare_soil", so a zero here previously produced an authoritative-sounding
        agronomic recommendation about dead ground for a request that had no
        satellite data at all. ``None`` is the honest answer.
        """
        return FieldAnalysis(
            lat=lat,
            lon=lon,
            analysis_date=analysis_date,
            ndvi=None,
            evi=None,
            savi=None,
            ndwi=None,
            nbr=None,
            ndvi_class={"class": "unknown", "description": "No satellite data available"},
            cloud_cover=100.0,
            data_quality="poor",
            recommendation="Satellite data temporarily unavailable. Please try again later or provide manual field observations.",
            quality_flags={"reason": "no_tiles"},
            # No tile was retrieved and no index was computed. Every value above
            # is None, which is an absence, not a simulation result.
            data_source="unavailable",
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
            recommendations.append("Conditions appear stable. Continue regular monitoring.")

        return " | ".join(recommendations)


# Singleton
_analyzer: SatelliteAnalyzer | None = None


def get_analyzer() -> SatelliteAnalyzer:
    """Get or create singleton analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SatelliteAnalyzer()
    return _analyzer
