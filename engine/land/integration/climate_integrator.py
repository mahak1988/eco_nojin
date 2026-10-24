"""
Climate Integrator
===================
Connects engine/land/ to climate modules.
Uses existing modules:
- engine/hydroma/climate/et_calculator.py
- engine/hydroma/models/global_watchdog/koppen.py
- services/satellite/open_meteo.py
"""

import logging
import math
import time
from datetime import datetime
from typing import Any, cast

import numpy as np

from engine.hydroma.provenance import DataSource

from .climate_models import (
    KOPPEN_DESCRIPTIONS,
    AridityClass,
    ClimateIntegrationResult,
    ClimateProfile,
    KoppenClimate,
    MonthlyClimate,
)

logger = logging.getLogger(__name__)

# Day of year at the middle of each month, used to evaluate extraterrestrial
# radiation on a monthly basis. FAO-56 eq. 21 is defined per day.
_MID_MONTH_DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]

# Synthetic climate data for fallback (based on latitude bands)
# Each entry: (t_min_jan, t_max_jan, t_min_jul, t_max_jul, annual_precip)
LATITUDE_CLIMATE_BANDS: dict[str, dict[str, Any]] = {
    "tropical": {
        "lat_range": (-23.5, 23.5),
        "t_min_jan": 22.0,
        "t_max_jan": 32.0,
        "t_min_jul": 22.0,
        "t_max_jul": 32.0,
        "annual_precip": 2000.0,
        "koppen": KoppenClimate.Aw,
    },
    "subtropical_arid": {
        "lat_range": (23.5, 35.0),
        "t_min_jan": 5.0,
        "t_max_jan": 18.0,
        "t_min_jul": 22.0,
        "t_max_jul": 42.0,
        "annual_precip": 150.0,
        "koppen": KoppenClimate.BWh,
    },
    "subtropical_arid_south": {
        "lat_range": (-35.0, -23.5),
        "t_min_jan": 22.0,
        "t_max_jan": 42.0,
        "t_min_jul": 5.0,
        "t_max_jul": 18.0,
        "annual_precip": 150.0,
        "koppen": KoppenClimate.BWh,
    },
    "temperate": {
        "lat_range": (35.0, 50.0),
        "t_min_jan": -2.0,
        "t_max_jan": 8.0,
        "t_min_jul": 15.0,
        "t_max_jul": 28.0,
        "annual_precip": 700.0,
        "koppen": KoppenClimate.Cfb,
    },
    "temperate_south": {
        "lat_range": (-50.0, -35.0),
        "t_min_jan": 15.0,
        "t_max_jan": 28.0,
        "t_min_jul": -2.0,
        "t_max_jul": 8.0,
        "annual_precip": 700.0,
        "koppen": KoppenClimate.Cfb,
    },
    "continental": {
        "lat_range": (50.0, 66.5),
        "t_min_jan": -15.0,
        "t_max_jan": -5.0,
        "t_min_jul": 12.0,
        "t_max_jul": 24.0,
        "annual_precip": 500.0,
        "koppen": KoppenClimate.Dfb,
    },
    "continental_south": {
        "lat_range": (-66.5, -50.0),
        "t_min_jan": 12.0,
        "t_max_jan": 24.0,
        "t_min_jul": -15.0,
        "t_max_jul": -5.0,
        "annual_precip": 500.0,
        "koppen": KoppenClimate.Dfb,
    },
    "polar": {
        "lat_range": (66.5, 90.0),
        "t_min_jan": -30.0,
        "t_max_jan": -15.0,
        "t_min_jul": 0.0,
        "t_max_jul": 8.0,
        "annual_precip": 250.0,
        "koppen": KoppenClimate.ET,
    },
    "polar_south": {
        "lat_range": (-90.0, -66.5),
        "t_min_jan": 0.0,
        "t_max_jan": 8.0,
        "t_min_jul": -30.0,
        "t_max_jul": -15.0,
        "annual_precip": 250.0,
        "koppen": KoppenClimate.ET,
    },
}


class ClimateIntegrator:
    """
    Integrates climate data with land profiles.

    Connects to:
    - engine/hydroma/climate/et_calculator.py (ET0)
    - engine/hydroma/models/global_watchdog/koppen.py (KGCv5)
    - services/satellite/open_meteo.py (climate data)
    """

    def __init__(self):
        """Initialize integrator with climate modules."""
        self._et_calculator = None
        self._koppen_classifier = None
        self._load_climate_modules()

    def _load_climate_modules(self):
        """Resolve the canonical climate modules this integrator delegates to.

        Eager, not lazy: it runs from ``__init__``. The callables it binds are
        the only copy of FAO-56 eq. 52 and eq. 21 in this module --
        ``calculate_et0_hargreaves_monthly`` and
        ``_extraterrestrial_radiation_monthly`` both call through here rather
        than re-deriving the formulas.
        """
        # Load ET calculator
        try:
            from engine.hydroma.climate.et_calculator import (
                calc_et0_hargreaves,
                calc_extraterrestrial_radiation,
            )

            self._et_calculator = {
                "hargreaves": calc_et0_hargreaves,
                "radiation": calc_extraterrestrial_radiation,
            }
            logger.info("ET calculator loaded")
        except ImportError as e:
            logger.warning(f"Could not load ET calculator: {e}")

        # Load Köppen classifier
        try:
            from engine.hydroma.models.global_watchdog.koppen import KGCv5

            self._koppen_classifier = KGCv5()
            logger.info("KGCv5 Köppen classifier loaded")
        except ImportError as e:
            logger.warning(f"Could not load KGCv5: {e}")

    def get_latitude_band(self, lat: float) -> dict[str, Any]:
        """Get climate band for a given latitude."""
        for name, band in LATITUDE_CLIMATE_BANDS.items():
            low, high = band["lat_range"]
            if low <= lat < high:
                return {"name": name, **band}
        # Default to temperate if not found
        return {"name": "temperate", **LATITUDE_CLIMATE_BANDS["temperate"]}

    def generate_synthetic_monthly_climate(self, lat: float, lon: float) -> list[MonthlyClimate]:
        """
        Generate synthetic monthly climate data based on latitude.

        This is the L0 fallback when real data is not available.
        """
        band = self.get_latitude_band(lat)

        # Determine hemisphere
        is_northern = lat >= 0

        # Interpolate monthly temperatures using cosine function
        # T(month) = T_mean + (T_jul - T_jan)/2 * cos(2π(month - 7)/12)
        # for northern hemisphere (warmest in July)
        t_jan_mean = (band["t_min_jan"] + band["t_max_jan"]) / 2
        t_jul_mean = (band["t_min_jul"] + band["t_max_jul"]) / 2
        t_annual_mean = (t_jan_mean + t_jul_mean) / 2
        t_amplitude = abs(t_jul_mean - t_jan_mean) / 2

        # Precipitation distribution (simple sinusoidal with peak in warm season for temperate)
        annual_precip = band["annual_precip"]

        monthly = []
        for month in range(1, 13):
            # Temperature: cosine curve
            phase = (month - 7) * 2 * math.pi / 12  # Peak in July (month 7)
            if not is_northern:
                phase = (month - 1) * 2 * math.pi / 12  # Peak in January for south

            t_mean = t_annual_mean + t_amplitude * math.cos(phase)

            # Add some daily range
            daily_range = 8.0 + 2.0 * math.cos(phase)  # Varies seasonally
            t_min = t_mean - daily_range / 2
            t_max = t_mean + daily_range / 2

            # Precipitation: peak in warm season for temperate, wet season varies
            # Simplified: more in summer for temperate, winter for Mediterranean
            precip_phase = phase + math.pi  # Opposite phase for precip
            monthly_frac = (1 + 0.5 * math.cos(precip_phase)) / 12
            precip_mm = annual_precip * monthly_frac

            monthly.append(
                MonthlyClimate(
                    month=month,
                    t_min_c=round(t_min, 1),
                    t_max_c=round(t_max, 1),
                    t_mean_c=round(t_mean, 1),
                    precipitation_mm=round(max(0, precip_mm), 1),
                    # This path has no ET0, so et0_mm stays None; passed
                    # explicitly because mypy cannot see the Field default.
                    et0_mm=None,
                )
            )

        return monthly

    def calculate_et0_hargreaves_monthly(
        self, monthly: list[MonthlyClimate], lat: float
    ) -> list[MonthlyClimate]:
        """
        Calculate monthly ET0 using the Hargreaves-Samani method.

        Delegates to the canonical implementation in
        ``engine/hydroma/climate/et_calculator.py``, which returns mm/day;
        the monthly total is that daily rate times the length of the month.

        What this used to do
        --------------------
        This method carried its own copy of FAO-56 eq. 52:

            et0 = 0.0023 * ra * (Tmean + 17.8) * sqrt(Tmax - Tmin)

        with ``ra`` taken from ``_extraterrestrial_radiation_monthly``, which
        returns MJ/m²/day. Eq. 52 requires Ra in **equivalent evaporation
        (mm/day)**, which is Ra * 0.408 (FAO-56 eq. 40). That conversion was
        missing here, so every value this method produced was overstated by
        1/0.408 = 2.45x. The exponent this copy carried was ``math.sqrt``, i.e.
        0.50, which is the published form of FAO-56 eq. 52 (0.5); the core it
        now delegates to once carried an unjustified 0.48, corrected in S17
        (see ``climate.et_calculator._hargreaves_core``).

        It was worse than one wrong copy. ``_load_climate_modules`` imported
        ``calc_et0_hargreaves`` and stored it in ``self._et_calculator``, and
        then *both* branches of this method ignored it: the branch taken when
        the import succeeded inlined the same wrong formula, and the branch
        taken when it failed inlined it too -- minus the multiplication by
        days in month, so the two branches disagreed with each other by
        roughly 30x. The consolidation the docstring claimed had not
        happened.

        There is no fallback formula any more. Without the canonical module
        there is no ET0, so ``et0_mm`` stays None and the caller sees an
        absent value rather than a wrong one; ``build_climate_profile``
        already treats a missing annual ET0 as "not computed" rather than as
        a humid climate.

        The 0.1 degC diurnal-range floor this method applied is preserved via
        the canonical function's ``dtr_floor`` argument, which is the
        supported way to keep that behaviour without a second implementation.
        """
        if not self._et_calculator:
            logger.warning(
                "ET0 not computed: the canonical FAO-56 calculator is unavailable, "
                "so et0_mm is left unset. An absent ET0 is not an ET0 of zero."
            )
            return monthly

        hargreaves = self._et_calculator["hargreaves"]
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        for m in monthly:
            ra_mj = self._extraterrestrial_radiation_monthly(m.month, lat)
            try:
                et0_daily = hargreaves(
                    t_min=m.t_min_c,
                    t_max=m.t_max_c,
                    t_mean=m.t_mean_c,
                    ra_mj=ra_mj,
                    dtr_floor=0.1,
                )
            except Exception as e:
                # One bad month must not discard the other eleven.
                logger.warning("ET0 calculation failed for month %s: %s", m.month, e)
                continue
            m.et0_mm = round(max(0.0, et0_daily * days_in_month[m.month - 1]), 1)

        return monthly

    def _extraterrestrial_radiation_monthly(self, month: int, lat: float) -> float:
        """
        Extraterrestrial radiation at the middle of ``month``, in MJ/m²/day.

        A thin wrapper over the canonical FAO-56 eq. 21 implementation in
        ``engine/hydroma/climate/et_calculator.py``. This used to be a second
        copy of eq. 21; it is retained only because callers ask for radiation
        on a *monthly* basis rather than by day of year. The canonical function
        additionally clamps a negative Ra to zero, which the copy did not.
        """
        if self._et_calculator:
            radiation = self._et_calculator["radiation"]
        else:
            from engine.hydroma.climate.et_calculator import (
                calc_extraterrestrial_radiation as radiation,
            )

        ra_monthly: float = radiation(lat, _MID_MONTH_DOY[month - 1])
        return ra_monthly

    def classify_koppen(
        self, monthly: list[MonthlyClimate], lat: float
    ) -> tuple[KoppenClimate | None, str | None]:
        """
        Classify climate using Köppen-Geiger system.

        Uses KGCv5 from engine/hydroma/models/global_watchdog/koppen.py
        """
        if self._koppen_classifier is None:
            # Fallback: use latitude band
            band = self.get_latitude_band(lat)
            return band.get("koppen"), "synthetic"

        try:
            # KGCv5.classify takes exactly three 12-element arrays --
            # (t_min, t_max, precipitation) -- and returns a dict carrying
            # "code", "description" and "group". This call passed four
            # arguments and then parsed the result as if it were a tuple, so
            # the TypeError was raised on every single call, caught by the
            # ``except Exception`` below, and every classification silently
            # degraded to the latitude-band fallback. The canonical Köppen
            # implementation was never once reached.
            t_min = np.array([m.t_min_c for m in monthly], dtype=float)
            t_max = np.array([m.t_max_c for m in monthly], dtype=float)
            precip = np.array([m.precipitation_mm for m in monthly], dtype=float)

            result = self._koppen_classifier.classify(t_min, t_max, precip)

            # Parse the documented dict result.
            if isinstance(result, dict):
                koppen_code = result.get("code")
            elif isinstance(result, tuple):
                koppen_code = result[0] if result else None
            elif hasattr(result, "code"):
                koppen_code = result.code
            else:
                koppen_code = str(result)

            if not koppen_code:
                raise ValueError(f"KGCv5.classify returned no code: {result!r}")

            # Map to enum
            try:
                koppen_enum = KoppenClimate(koppen_code)
                description = KOPPEN_DESCRIPTIONS.get(koppen_enum, koppen_code)
                return koppen_enum, description
            except ValueError:
                logger.warning(f"Unknown Köppen code: {koppen_code}")
                return None, koppen_code

        except Exception as e:
            logger.warning(f"Köppen classification failed: {e}")
            band = self.get_latitude_band(lat)
            return band.get("koppen"), "synthetic (fallback)"

    def calculate_aridity_index(
        self, annual_precip_mm: float, annual_et0_mm: float
    ) -> tuple[float, AridityClass]:
        """
        Calculate UNEP Aridity Index = P / PET.

        Reference: UNEP (1992) "World Atlas of Desertification"

        Missing ET0 is not a humid climate. The previous version returned
        ``(1.0, AridityClass.HUMID)`` when ``annual_et0_mm <= 0``, so an absent
        reference evapotranspiration was reported as the wettest possible
        classification. For an arid-country platform that inverts the
        conclusion from "unknown" into "not arid", and any irrigation advice
        derived from it would err in the dangerous direction.

        A site with no ET0 has no aridity index. The index is returned as NaN
        so the "not computed" state is explicit, and the class says UNKNOWN.
        """
        if annual_et0_mm is None or annual_et0_mm <= 0:
            logger.warning(
                "Aridity index not computed: annual_et0_mm is %r. Absence of ET0 "
                "is not evidence of a humid climate.",
                annual_et0_mm,
            )
            return float("nan"), AridityClass.UNKNOWN

        if annual_precip_mm is None or annual_precip_mm < 0:
            logger.warning("Aridity index not computed: annual_precip_mm is %r", annual_precip_mm)
            return float("nan"), AridityClass.UNKNOWN

        ai = annual_precip_mm / annual_et0_mm
        ai = min(ai, 2.0)  # Cap for safety

        if ai < 0.05:
            return ai, AridityClass.HYPER_ARID
        elif ai < 0.20:
            return ai, AridityClass.ARID
        elif ai < 0.50:
            return ai, AridityClass.SEMI_ARID
        elif ai < 0.65:
            return ai, AridityClass.DRY_SUBHUMID
        else:
            return ai, AridityClass.HUMID

    def calculate_growing_season(self, monthly: list[MonthlyClimate]) -> tuple[int, int]:
        """
        Calculate growing season length and frost-free days.

        Growing season: months with T_mean > 5°C (suitable for most crops)
        Frost-free days: days where T_min > 0°C

        Returns:
            (growing_season_days, frost_free_days)
        """
        growing_days = 0
        frost_free_days = 0
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        for m in monthly:
            days = days_in_month[m.month - 1]

            # Growing season: T_mean > 5°C
            if m.t_mean_c > 5.0:
                growing_days += days

            # Frost-free: T_min > 0°C
            if m.t_min_c > 0.0:
                frost_free_days += days
            elif m.t_min_c > -5.0:
                # Partial month (estimate fraction without frost)
                frost_fraction = (m.t_min_c + 5.0) / 10.0  # Rough estimate
                frost_free_days += int(days * frost_fraction)

        return growing_days, frost_free_days

    def build_climate_profile(
        self, lat: float, lon: float, elevation_m: float | None = None
    ) -> ClimateProfile:
        """
        Build complete climate profile for a location.

        Priority:
        1. Try Open-Meteo (real data)
        2. Fall back to synthetic data

        Returns:
            ClimateProfile with all derived metrics
        """
        data_source = "synthetic"

        # Try to fetch from Open-Meteo
        real_data = self._fetch_open_meteo(lat, lon)
        if real_data:
            monthly = real_data
            data_source = "open_meteo"
        else:
            monthly = self.generate_synthetic_monthly_climate(lat, lon)

        # Calculate ET0
        monthly = self.calculate_et0_hargreaves_monthly(monthly, lat)

        # Köppen classification
        koppen, koppen_description = self.classify_koppen(monthly, lat)

        # Annual aggregates
        annual_precip = sum(m.precipitation_mm for m in monthly)
        annual_et0 = sum(m.et0_mm for m in monthly if m.et0_mm is not None)
        annual_t_mean = sum(m.t_mean_c for m in monthly) / 12

        # Aridity index
        aridity_index, aridity_class = self.calculate_aridity_index(annual_precip, annual_et0)

        # Growing season
        growing_season_days, frost_free_days = self.calculate_growing_season(monthly)

        # Köppen group (first letter)
        koppen_group = koppen.value[0] if koppen else None

        return ClimateProfile(
            lat=lat,
            lon=lon,
            elevation_m=elevation_m,
            koppen=koppen,
            koppen_description=koppen_description,
            koppen_group=koppen_group,
            annual_precip_mm=round(annual_precip, 1),
            annual_et0_mm=round(annual_et0, 1) if annual_et0 else None,
            annual_t_mean_c=round(annual_t_mean, 1),
            aridity_index=round(aridity_index, 3),
            aridity_class=aridity_class,
            growing_season_days=growing_season_days,
            frost_free_days=frost_free_days,
            monthly=monthly,
            data_source=data_source,
            data_quality_level="L0" if data_source == "synthetic" else "L3",
        )

    def _fetch_open_meteo(self, lat: float, lon: float) -> list[MonthlyClimate] | None:
        """
        Try to fetch climate data from Open-Meteo.

        Open-Meteo provides free, no-API-key climate data.
        Endpoint: https://archive-api.open-meteo.com/v1/archive
        """
        try:
            import httpx

            # Get last 30 years of monthly data (climatology)
            url = "https://archive-api.open-meteo.com/v1/archive"
            params: dict[str, Any] = {
                "latitude": lat,
                "longitude": lon,
                "start_date": "1991-01-01",
                "end_date": "2020-12-31",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            if "daily" not in data:
                return None

            # Aggregate daily to monthly (climatology)
            daily = data["daily"]
            t_max = daily.get("temperature_2m_max", [])
            t_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            times = daily.get("time", [])

            if not times or not t_max:
                return None

            # Aggregate by month (30-year climatology)
            monthly_t_max: dict[int, list[float]] = {m: [] for m in range(1, 13)}
            monthly_t_min: dict[int, list[float]] = {m: [] for m in range(1, 13)}
            monthly_precip: dict[int, list[float]] = {m: [] for m in range(1, 13)}

            for i, date_str in enumerate(times):
                if i >= len(t_max) or i >= len(t_min) or i >= len(precip):
                    continue
                if t_max[i] is None or t_min[i] is None or precip[i] is None:
                    continue

                # Parse date
                try:
                    dt = datetime.fromisoformat(date_str)
                    month = dt.month
                    monthly_t_max[month].append(t_max[i])
                    monthly_t_min[month].append(t_min[i])
                    monthly_precip[month].append(precip[i])
                except (ValueError, TypeError):
                    continue

            # Build monthly averages
            monthly = []
            for m in range(1, 13):
                if not monthly_t_max[m]:
                    continue

                t_max_mean = sum(monthly_t_max[m]) / len(monthly_t_max[m])
                t_min_mean = sum(monthly_t_min[m]) / len(monthly_t_min[m])
                # Precipitation: sum of daily for month, then average over years
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                years = len(monthly_t_max[m]) / days_in_month[m - 1]
                total_precip = sum(monthly_precip[m])
                avg_monthly_precip = total_precip / years if years > 0 else 0

                monthly.append(
                    MonthlyClimate(
                        month=m,
                        t_min_c=round(t_min_mean, 1),
                        t_max_c=round(t_max_mean, 1),
                        t_mean_c=round((t_min_mean + t_max_mean) / 2, 1),
                        precipitation_mm=round(avg_monthly_precip, 1),
                        et0_mm=None,
                    )
                )

            return monthly if len(monthly) == 12 else None

        except Exception as e:
            logger.info(f"Open-Meteo fetch failed (using synthetic): {e}")
            return None

    def integrate_with_land(
        self,
        profile_id: str,
        lat: float,
        lon: float,
        elevation_m: float | None = None,
        terrain_type: str | None = None,
        soil_profile: Any | None = None,
    ) -> ClimateIntegrationResult:
        """
        Integrate climate data with land profile.

        Args:
            profile_id: Land profile ID
            lat: Latitude
            lon: Longitude
            elevation_m: Elevation (optional)
            terrain_type: Terrain type from land analysis (optional)
            soil_profile: Soil profile from Phase 2A (optional)

        Returns:
            ClimateIntegrationResult
        """
        start_time = time.time()

        try:
            # Build climate profile
            climate_profile = self.build_climate_profile(lat, lon, elevation_m)

            # Determine limitations
            limitations = []
            recommendations = []
            irrigation_required = False
            drought_only = False
            cold_climate = False
            heat_stress = False

            # Aridity-based limitations
            if climate_profile.aridity_class in [AridityClass.HYPER_ARID, AridityClass.ARID]:
                limitations.append("severe_water_scarcity")
                irrigation_required = True
                drought_only = True
                recommendations.append("Use drip irrigation for water efficiency")
                recommendations.append("Select drought-tolerant crop varieties")
            elif climate_profile.aridity_class == AridityClass.SEMI_ARID:
                limitations.append("water_scarcity")
                irrigation_required = True
                recommendations.append("Consider supplemental irrigation")
                recommendations.append("Use drought-adapted crop varieties")

            # Cold climate limitations
            if climate_profile.frost_free_days is not None:
                if climate_profile.frost_free_days < 120:
                    limitations.append("short_growing_season")
                    cold_climate = True
                    recommendations.append("Use short-season crop varieties")
                    recommendations.append("Consider season extension techniques")
                elif climate_profile.frost_free_days < 180:
                    limitations.append("moderate_growing_season")
                    cold_climate = True
                    recommendations.append("Choose varieties with appropriate maturity dates")

            # Heat stress
            if climate_profile.annual_t_mean_c > 25:
                heat_stress = True
                limitations.append("heat_stress_risk")
                recommendations.append("Consider heat-tolerant crop varieties")
                recommendations.append("Provide shade or windbreaks if possible")

            # Temperature extremes
            for m in climate_profile.monthly:
                if m.t_max_c > 40:
                    limitations.append("extreme_heat")
                    heat_stress = True
                    recommendations.append("Avoid planting during peak heat months")
                    break

            if not limitations:
                recommendations.append(
                    "Climate conditions are favorable - no special adaptations needed"
                )

            integration_time_ms = (time.time() - start_time) * 1000

            return ClimateIntegrationResult(
                profile_id=profile_id,
                success=True,
                climate_profile=climate_profile,
                irrigation_required=irrigation_required,
                drought_tolerant_crops_only=drought_only,
                cold_climate_limitation=cold_climate,
                heat_stress_risk=heat_stress,
                limitations=list(set(limitations)),
                recommendations=recommendations,
                integration_time_ms=integration_time_ms,
                data_quality_level=climate_profile.data_quality_level,
                # Taken from the profile this was derived from. The previous
                # hard-coded "modelled" erased the distinction
                # build_climate_profile makes: it sets "open_meteo" when a real
                # forecast was retrieved and "synthetic" when the series was
                # generated. Both arrived here labelled as one thing, so a
                # caller could not tell a forecast from a placeholder.
                # ClimateProfile carries the package vocabulary
                # ("open_meteo"/"synthetic"); the
                # ``_fold_data_source_onto_canonical_literal`` before-validator
                # maps it onto the canonical DataSource literal at runtime, so
                # the cast records what the validator guarantees.
                data_source=cast("DataSource", climate_profile.data_source),
                model="climate integrator",
            )

        except Exception as e:
            logger.error(f"Climate integration failed: {e}")
            integration_time_ms = (time.time() - start_time) * 1000
            return ClimateIntegrationResult(
                profile_id=profile_id,
                success=False,
                error_message=str(e),
                integration_time_ms=integration_time_ms,
                # The integration failed, so no climate profile was built and
                # nothing was derived. "modelled" claimed a model had run.
                data_source="unavailable",
                model="climate integrator",
            )
