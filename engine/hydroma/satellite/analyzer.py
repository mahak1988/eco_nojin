"""High-level satellite analysis orchestrator.

Combines providers and processors to deliver actionable insights
for farmers, pastoralists, and ecosystem managers.

How ``FieldAnalysis.data_source`` is decided
--------------------------------------------
The label on a result is **derived from the tile that produced it**, never
asserted by this module. See :func:`_analysis_data_source` for the mapping and
the reasoning; the short version is that a tile which had bands fabricated into
it cannot yield an analysis labelled ``"measured"``.

Labels emitted here, and what each one licenses a reader to conclude:

=========  ====================================================================
``"measured"``     Every band in every index came from a downloaded observation.
``"degraded"``     Some bands were real and some were fabricated. The indices
                   are a mixture and are not a measurement. (S-HONEST: *real
                   data + a named substitute*.)
``"simulated"``    Nothing was measured -- either the provider fabricated the
                   whole tile, or it did not say where the pixels came from.
``"unavailable"``  No index was computed at all; the values are ``None``.
=========  ====================================================================
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

logger = logging.getLogger(__name__)

#: ``SatelliteTile.data_source`` value meaning "every band was a real download".
_TILE_SOURCE_REAL = "real"

#: ``SatelliteTile.data_source`` value meaning "some bands were fabricated".
_TILE_SOURCE_PARTIALLY_SYNTHETIC = "partially_synthetic"

#: ``quality_flags`` keys a provider may use to say that pixels were invented.
#: Listed rather than read one at a time so a provider that only sets
#: ``synthetic_bands`` cannot be mistaken for a provider that set nothing.
_SYNTHETIC_FLAG_KEYS = ("synthetic", "synthetic_pixels", "synthetic_bands")


@dataclass
class FieldAnalysis:
    """Complete satellite analysis for a field location."""

    lat: float | None = None
    lon: float | None = None
    analysis_date: date | None = None
    #: None means "not measured" -- no usable pixels, or no scene retrieved.
    #: It is deliberately not 0.0: zero is a real reading for every one of these
    #: indices, and interpret_ndvi(0.0) classifies as bare soil, so a zero would
    #: turn a missing observation into a confident agronomic judgement.
    ndvi: float | None = None
    evi: float | None = None
    savi: float | None = None
    ndwi: float | None = None
    nbr: float | None = None
    ndvi_class: dict | None = None
    cloud_cover: float | None = None
    data_quality: str | None = None
    recommendation: str | None = None
    #: Provenance of the ANALYSIS, not of the pixels -- see
    #: :func:`_analysis_data_source` for the mapping and the vocabulary:
    #: ``"measured"`` / ``"degraded"`` / ``"simulated"`` / ``"unavailable"``.
    #: The default is the conservative one; a caller that forgets to pass a
    #: label gets "do not treat this as a measurement" rather than the reverse.
    data_source: str = "simulated"
    quality_flags: dict[str, Any] | None = None


def _tiles_fabricated(quality_flags: dict[str, Any] | None) -> bool:
    """True if the tile says, in any of its own words, that pixels were invented.

    ``EarthSearchProvider`` sets all three of ``synthetic``,
    ``synthetic_pixels`` and ``synthetic_bands``, and they always agree. They
    are checked as alternatives rather than in sequence so that a tile which
    sets only ``synthetic_bands`` -- a stub provider, or a future provider with
    a shorter flag set -- is not read as clean. ``None`` and empty are both
    falsy, so a tile with no flags at all is *not* treated as fabricated; that
    case is handled by the unknown-source branch of :func:`_analysis_data_source`.
    """
    if not quality_flags:
        return False
    return any(bool(quality_flags.get(key)) for key in _SYNTHETIC_FLAG_KEYS)


def _analysis_data_source(tile: Any) -> str:
    """The ``FieldAnalysis.data_source`` label for an analysis of ``tile``.

    WHY THIS EXISTS
    ---------------
    ``analyze_point`` used to hard-code ``data_source="measured"`` on the
    success path. It copied ``tile.quality_flags`` onto the result, so the
    fabrication flag reached the caller while the label beside it said
    ``"measured"`` -- the truth was in the payload and the label contradicted
    it. That is the worst shape the defect can take: not a missing disclosure,
    but a disclosure attached to a contradicting claim. A reader who saw only
    ``data_source`` believed the NDVI was an observation.

    The mapping
    -----------
    ==================  ==============  =====================================
    tile provenance      label            why
    ==================  ==============  =====================================
    ``"real"``, no       ``"measured"``  Every band feeding every index was a
    fabrication flag                          downloaded observation. Indices are
                                              computed, but computed *from
                                              measurement*, which is what
                                              ``"measured"`` means here.
    ``"partially_``     ``"degraded"``   Real data plus a named substitute.
    ``synthetic"``, or                       S-HONEST defines ``degraded`` as
    a flag contradicting                       exactly this, and the
    ``"real"``                                   substitute is named in
                                              ``quality_flags["synthetic_bands"]``
                                              with ``["reason"]`` beside it. The
                                              index is not a measurement and
                                              must not be quoted as one.
    anything else      ``"simulated"``  Nothing was measured: either the
                                              provider fabricated every pixel,
                                              or it did not record where its
                                              pixels came from.
    ==================  ==============  =====================================

    WHY NOT JUST PASS ``tile.data_source`` THROUGH
    ---------------------------------------------
    The two vocabularies are not the same one. ``tile.data_source`` describes
    the *pixels* (``real`` / ``partially_synthetic`` / ``simulated``);
    ``FieldAnalysis.data_source`` describes the *analysis*, and its other two
    call sites already use ``"unavailable"`` for "nothing was computed" and
    ``"measured"`` for "computed from observation". Passing the tile's label
    through would give one field three unrelated vocabularies and would drop
    the ``"measured"`` case -- the one case where the reader most needs to be
    told the difference between an observation and a derivation of one.

    NOTE FOR A FUTURE EDIT: ``"degraded"`` is a member of the S-HONEST
    *status* vocabulary (``docs/standards/S-HONEST.md``), not of the engine's
    ``DataSource`` Literal (``engine/hydroma/provenance.py``: ``measured``,
    ``modelled``, ``simulated``, ``unavailable``). ``FieldAnalysis`` is a plain
    dataclass whose field is typed ``str``, so nothing rejects it today. If it
    is ever converted to a ``ResultProvenance`` pydantic model,
    ``"degraded"`` has to be added to that Literal in the same change or the
    partially-synthetic case becomes a ``ValidationError`` at runtime.

    CONSERVATIVE DEFAULT
    --------------------
    An unrecognised ``tile.data_source`` yields ``"simulated"``, not
    ``"measured"``. It is the safe direction to be wrong in: a caller that
    special-cases ``== "measured"`` will decline to use the number, whereas the
    opposite default hands it a fabricated index and calls it an observation.
    """
    flags = getattr(tile, "quality_flags", None)
    fabricated = _tiles_fabricated(flags)
    source = getattr(tile, "data_source", None)

    if source == _TILE_SOURCE_REAL and not fabricated:
        return "measured"
    if source == _TILE_SOURCE_PARTIALLY_SYNTHETIC or (fabricated and source == _TILE_SOURCE_REAL):
        # The second disjunct is a contradiction between the two signals -- a
        # tile claiming every band is real while flagging fabrication. Resolved
        # downward, toward "do not call this a measurement".
        return "degraded"
    return "simulated"


class SatelliteAnalyzer:
    """Orchestrates satellite data analysis."""

    def __init__(self):
        # Only the STAC provider is wired. ``NasaPowerProvider`` used to be
        # instantiated here and never read: ``analyze_point`` had no weather
        # code path at all, so ``fetch_daily`` was unreachable from this class.
        # Constructing it on every ``SatelliteAnalyzer()`` did real work --
        # ``NasaPowerProvider.__init__`` opens no socket but does read its
        # endpoint configuration -- for a capability the analyzer did not have.
        # The provider module itself is kept: it is a usable NASA POWER client
        # with its own tests, and it is the module a weather path would use.
        # Wiring it means adding a method that actually calls ``fetch_daily``,
        # which is a feature decision, not a cleanup.
        self.earth_search = EarthSearchProvider()

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
        # Fixed 2026-10-01. This was:
        #
        #     swir_band = bands.get("swir16") or bands.get("swir22") or bands["nir"]
        #
        # `or` evaluates the truth value of its left operand. A band is a numpy
        # array, so `ValueError: The truth value of an array with more than one
        # element is ambiguous` is raised the moment a SWIR band is actually
        # present — which is the normal case for real Sentinel-2 data. NBR
        # therefore computed only when *both* SWIR keys were absent, and the
        # tests avoided the path by popping those keys (see
        # `_route_around_the_swir_or_bug`), so a green suite sat on top of an
        # unreachable success path.
        #
        # Absence is tested explicitly. A missing key is None, not a falsy array —
        # the distinction is exactly what `or` throws away.
        swir_band = bands.get("swir16")
        if swir_band is None:
            swir_band = bands.get("swir22")
        if swir_band is None:
            swir_band = bands["nir"]
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

        # "measured" is not a thing this module is entitled to assert. It was
        # hard-coded here, so a tile whose NIR was filled with
        # np.random.uniform(...) reported "measured" while
        # quality_flags["synthetic"] said the opposite in the same payload.
        # The label now comes from the tile's own provenance; see
        # _analysis_data_source for the mapping and why each value was chosen.
        analysis_source = _analysis_data_source(tile)
        flags = getattr(tile, "quality_flags", None) or {}

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
            # "good" is reserved for an all-real tile. Before this change a tile
            # with five fabricated bands and 5% cloud cover reported
            # data_quality="good", which is the same contradiction as the label
            # above and one field further out. The vocabulary stays the
            # good/moderate/poor it already was -- "degraded" is not added here,
            # because nothing in this tree reads this field and widening a
            # vocabulary is not free -- but "good" is now unreachable for a
            # tile that says pixels were invented. Which bands, and why, is
            # already in quality_flags["synthetic_bands"] / ["reason"].
            data_quality=(
                ("good" if tile.cloud_cover < 10 else "moderate")
                if analysis_source == "measured"
                else "moderate"
            ),
            recommendation=recommendation,
            quality_flags=flags,
            data_source=analysis_source,
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

        ``data_source`` is accepted and deliberately not used. "unavailable" is
        the truth about *this result* whatever the tile was -- no index was
        computed, so no provenance claim about the pixels can rescue the
        numbers -- and it is the conservative direction. The tile's own label
        is still reachable: it is not discarded, only outranked by the fact
        that this analysis produced nothing.

        A NOTE ON THE UNUSED-PARAMETER SHAPE: the previous version of this
        signature took ``data_source`` and ignored it, which is a trap for the
        next reader -- the name invites the conclusion that the argument is
        load-bearing. It is recorded here rather than removed so the reasoning
        survives.
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
            # The spread order is load-bearing. It used to be
            # ``{"reason": "all_pixels_clouded", **(quality_flags or {})}``, so
            # a tile that carried its own ``reason`` -- EarthSearch sets
            # ``reason="fabricated_bands"`` -- overwrote it, and the caller
            # reading ``quality_flags["reason"] == "fabricated_bands"`` would
            # conclude the missing indices were caused by fabrication rather
            # than by cloud. The tile's flags are kept; the analysis's own
            # reason is written last and therefore wins. Nothing is lost: which
            # bands were invented is still in ``synthetic_bands`` /
            # ``synthetic_band_note``, which have no colliding key.
            quality_flags={**(quality_flags or {}), "reason": "all_pixels_clouded"},
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
