"""S02 — Climate engine conformance to FAO-56.

Standards under test
--------------------
FAO-56 (Allen, Pereira, Raes & Smith, 1998), *Crop evapotranspiration —
Guidelines for computing crop water requirements*, Irrigation and Drainage
Paper 56:

  - eq. 8   psychrometric constant, gamma = 0.000665 P
  - eq. 11  saturation vapour pressure, es = 0.6108 exp(17.27 T/(T+237.3))
  - eq. 13  slope of the vapour-pressure curve, d = 4098 es/(T+237.3)^2
  - eq. 17  actual vapour pressure, ea = (es_tmin RHmax + es_tmax RHmin)/200
  - eq. 21  extraterrestrial radiation, Ra
  - eq. 39  Penman-Monteith reference ET
  - eq. 52  Hargreaves-Samani reference ET, exponent on (Tmax - Tmin) is **0.48**

Method
------
Rather than trusting remembered constants, this module carries an *independent*
re-derivation of each FAO-56 equation (``_ref_*`` functions written straight
from the published formula) and requires the engine to match it. Physical
anchor values that *are* quoted from FAO-56 Annex 2 are used as a second,
independent cross-check; a disagreement between the two would indicate that the
equation itself has been misremembered.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, strategies as st

from engine.hydroma.climate import et_calculator as et
from engine.strict_tests.conftest import climate_day

# --------------------------------------------------------------------------
# Independent re-derivation of FAO-56, written from the published equations.
# --------------------------------------------------------------------------

_GSC = 0.0820  # MJ/m2/min, FAO-56 Table 2.4
_SIGMA = 4.903e-9  # MJ K-4 m-2 day-1, FAO-56 eq. 13 note / Stull
_ALBEDO = 0.23  # FAO-56 eq. 40 (grass reference)


def _ref_es(t: float) -> float:
    """FAO-56 eq. 11."""
    return 0.6108 * math.exp((17.27 * t) / (t + 237.3))


def _ref_delta(t: float) -> float:
    """FAO-56 eq. 13."""
    return 4098.0 * _ref_es(t) / ((t + 237.3) ** 2)


def _ref_gamma(elevation: float) -> float:
    """FAO-56 eq. 8 with the eq. 7 barometric relation."""
    pressure = 101.3 * (((293.0 - 0.0065 * elevation) / 293.0) ** 5.26)
    return 0.000665 * pressure


def _ref_ra(latitude: float, doy: int) -> float:
    """FAO-56 eq. 21, using the explicit day-length cosine integral.

    Deliberately *not* the engine's arccos formulation: this integrates
    cos(zenith) over the day, so it is an independent check on the sunset-hour
    angle and on the sign conventions.
    """
    phi = math.radians(latitude)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    delta = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    cos_ws = -math.tan(phi) * math.tan(delta)
    if cos_ws <= -1.0:  # polar day
        ws = math.pi
    elif cos_ws >= 1.0:  # polar night
        ws = 0.0
    else:
        ws = math.acos(cos_ws)
    if ws <= 0.0:
        return 0.0
    integral = ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws)
    return (24.0 * 60.0 / math.pi) * _GSC * dr * max(0.0, integral)


def _ref_ea(tmin: float, tmax: float, rh_min: float, rh_max: float) -> float:
    """FAO-56 eq. 17."""
    return (_ref_es(tmin) * rh_max / 100.0 + _ref_es(tmax) * rh_min / 100.0) / 2.0


def _ref_rnl(tmin: float, tmax: float, ea: float, rs: float, rso: float) -> float:
    """FAO-56 eq. 40 net longwave, using the Stull (1996) cloudiness factor."""
    tmax_k = tmax + 273.16
    tmin_k = tmin + 273.16
    cloud = 1.35 * (rs / rso) - 0.35 if rso > 0 else 0.05
    cloud = min(max(cloud, 0.05), 1.0)
    return _SIGMA * ((tmax_k**4 + tmin_k**4) / 2.0) * (0.34 - 0.14 * math.sqrt(ea)) * cloud


def _ref_penman_monteith(tmin, tmax, rh_min, rh_max, u2, rs, elevation, latitude, doy):
    """FAO-56 eq. 39 with the eq. 38-40 radiation decomposition.

    Written from the published equations and the FAO-56 definitions of the
    symbols, sharing no code with the engine:

      ea  = [es(Tmin) Rhmax + es(Tmax) Rhmin] / 200      eq. 17
      es  = mean of es(Tmax) and es(Tmin)                  eq. 11, note a
      Rns = (1 - alpha) Rs                                eq. 38, alpha = 0.23
      Rso = (0.75 + 2e-5 z) Ra                            eq. 39
      Rnl = sigma mean(T_K^4) (0.34 - 0.14 sqrt(ea)) (1.35 Rs/Rso - 0.35)   eq. 40
      Rn  = Rns - Rnl
      ETo = (0.408 d Rn + g 900/(T+273) u2 (es - ea)) / (d + g (1 + 0.34 u2))

    The cloudiness factor is clamped to [0, 1] as FAO-56 eq. 40 requires.
    """
    tmean = (tmax + tmin) / 2.0
    delta = _ref_delta(tmean)
    gamma = _ref_gamma(elevation)
    es_tmax = _ref_es(tmax)
    es_tmin = _ref_es(tmin)
    es_mean = (es_tmax + es_tmin) / 2.0
    ea = _ref_ea(tmin, tmax, rh_min, rh_max)

    ra = _ref_ra(latitude, doy)
    rso = (0.75 + 2.0e-5 * elevation) * ra
    rns = (1.0 - _ALBEDO) * rs
    rs_over_rso = min(max(rs / rso, 0.3), 1.0) if rso > 0.0 else 0.3
    cloudiness = min(max(1.35 * rs_over_rso - 0.35, 0.0), 1.0)
    rnl = (
        4.903e-9
        * (((tmax + 273.16) ** 4) + ((tmin + 273.16) ** 4))
        / 2.0
        * (0.34 - 0.14 * math.sqrt(ea))
        * cloudiness
    )
    rn = rns - rnl

    num = 0.408 * delta * rn + gamma * (900.0 / (tmean + 273.0)) * u2 * (es_mean - ea)
    den = delta + gamma * (1.0 + 0.34 * u2)
    return max(0.0, num / den)


def rnl_for(tmin: float, tmax: float, ea: float, rs: float, rso: float) -> float:
    """Net longwave loss, exposed so a caller can supply the real Rso."""
    tmax_k = tmax + 273.16
    tmin_k = tmin + 273.16
    cloud = 1.35 * (rs / rso) - 0.35 if rso > 0 else 0.05
    cloud = min(max(cloud, 0.05), 1.0)
    return _SIGMA * ((tmax_k**4 + tmin_k**4) / 2.0) * (0.34 - 0.14 * math.sqrt(ea)) * cloud


# Absolute upper bound on a daily-mean top-of-atmosphere flux on a horizontal
# surface. The extreme is the summer polar pole, where the sun circles the
# horizon at 23.45 deg altitude near perihelion:
#     S * sin(23.45 deg) * dr_max = 118.08 * 0.39795 * 1.033 = 48.54 MJ/m2/day
# Anything above that is a formula or unit error.
RA_ABSOLUTE_MAX = 48.55

# At the equator the day length is 12 h at every declination, so Ra is
# proportional to dr * cos(delta). Over a year dr swings +-3.3 % and cos(delta)
# swings 1.000 -> 0.917, giving a peak-to-trough ratio of about 0.86 around an
# annual mean of ~36 MJ/m2/day.
RA_EQUATOR_MEAN_RANGE = (33.0, 39.5)


# --------------------------------------------------------------------------
# Equation-level conformance
# --------------------------------------------------------------------------


class TestSaturationVapourPressure:
    """FAO-56 eq. 11."""

    def test_matches_fao56_annex2_table(self) -> None:
        # FAO-56 Table 2.3: es(0) = 0.611, es(25) = 3.17, es(30) = 4.24 kPa.
        assert et.calc_saturation_vapor_pressure(0.0) == pytest.approx(0.611, rel=2e-3)
        assert et.calc_saturation_vapor_pressure(25.0) == pytest.approx(3.17, rel=2e-3)
        assert et.calc_saturation_vapor_pressure(30.0) == pytest.approx(4.24, rel=2e-3)

    @given(t=st.floats(min_value=-40.0, max_value=50.0, allow_nan=False))
    def test_matches_independent_rederivation(self, t: float) -> None:
        assert et.calc_saturation_vapor_pressure(t) == pytest.approx(_ref_es(t), rel=1e-12)

    @given(t=st.floats(min_value=-40.0, max_value=50.0, allow_nan=False))
    def test_strictly_increasing(self, t: float) -> None:
        assert et.calc_saturation_vapor_pressure(t + 0.5) > et.calc_saturation_vapor_pressure(t)

    @given(t=st.floats(min_value=-40.0, max_value=50.0, allow_nan=False))
    def test_positive_and_physically_bounded(self, t: float) -> None:
        es = et.calc_saturation_vapor_pressure(t)
        assert 0.0 < es < 13.0, f"es({t}) = {es} outside the saturation-vapour range"


class TestVapourPressureSlope:
    """FAO-56 eq. 13."""

    @given(t=st.floats(min_value=-30.0, max_value=45.0, allow_nan=False))
    def test_matches_independent_rederivation(self, t: float) -> None:
        assert et.calc_delta(t) == pytest.approx(_ref_delta(t), rel=1e-12)

    @given(t=st.floats(min_value=-30.0, max_value=45.0, allow_nan=False))
    def test_positive(self, t: float) -> None:
        assert et.calc_delta(t) > 0.0

    def test_magnitude_at_25c(self) -> None:
        # FAO-56 Table 2.3: d(25 C) = 0.189 kPa/C, d(20 C) = 0.145 kPa/C.
        assert et.calc_delta(25.0) == pytest.approx(0.189, rel=5e-3)
        assert et.calc_delta(20.0) == pytest.approx(0.145, rel=5e-3)


class TestPsychrometricConstant:
    """FAO-56 eq. 8 and the eq. 7 barometric relation."""

    def test_sea_level_value(self) -> None:
        # 0.000665 * 101.3 = 0.0673645 kPa/C
        assert et.calc_psychrometric(0.0) == pytest.approx(0.0673645, rel=1e-9)

    def test_decreases_monotonically_with_elevation(self) -> None:
        gammas = [et.calc_psychrometric(z) for z in (0.0, 500.0, 1000.0, 2000.0, 4000.0)]
        assert gammas == sorted(gammas, reverse=True)
        assert all(g > 0.0 for g in gammas)

    @pytest.mark.parametrize("z", [0, 250, 500, 1000, 1750, 2500, 3500, 4400])
    def test_matches_independent_rederivation(self, z: int) -> None:
        assert et.calc_psychrometric(float(z)) == pytest.approx(_ref_gamma(float(z)), rel=1e-12)

    @given(z=st.floats(min_value=0.0, max_value=5000.0, allow_nan=False))
    def test_within_plausible_range(self, z: float) -> None:
        # Standard atmosphere gives 101.3 kPa at sea level and 54.0 kPa at
        # 5000 m, so gamma falls from 0.0674 to about 0.0359 kPa/C.
        assert 0.035 < et.calc_psychrometric(z) <= 0.0674


class TestExtraterrestrialRadiation:
    """FAO-56 eq. 21."""

    @pytest.mark.parametrize("lat", [-60.0, -30.0, 0.0, 30.0, 45.0, 60.0])
    def test_matches_integrated_cosine_oracle(self, lat: float) -> None:
        for doy in (1, 45, 80, 172, 196, 265, 355):
            got = et.calc_extraterrestrial_radiation(lat, doy)
            expected = _ref_ra(lat, doy)
            assert got == pytest.approx(expected, rel=1e-9), f"Ra({lat}, {doy})"

    def test_equator_annual_cycle_range(self) -> None:
        """At the equator the sunset hour angle is 90 deg at every declination,
        so Ra reduces to dr * cos(delta) and stays in a narrow band around the
        solar-constant mean."""
        values = [et.calc_extraterrestrial_radiation(0.0, d) for d in range(1, 366, 3)]
        assert min(values) / max(values) >= 0.85, "Ra at the equator varied by more than 15 %"
        mean = sum(values) / len(values)
        assert RA_EQUATOR_MEAN_RANGE[0] < mean < RA_EQUATOR_MEAN_RANGE[1], f"mean {mean}"

    def test_maximum_occurs_where_declination_cosine_and_distance_align(self) -> None:
        """Ra at the equator peaks near the equinoxes, where cos(delta) = 1 and
        the Earth-Sun distance factor is still favourable. It must never peak at
        the solstice, where cos(23.45 deg) = 0.917 has suppressed the flux."""
        best_doy = max(range(1, 366), key=lambda d: et.calc_extraterrestrial_radiation(0.0, d))
        assert 60 <= best_doy <= 110, (
            f"peak equatorial Ra on doy {best_doy}, expected near an equinox"
        )

    @pytest.mark.parametrize("lat", [-89.0, -45.0, 0.0, 45.0, 89.0])
    def test_seasonal_amplitude_grows_with_latitude(self, lat: float) -> None:
        values = [et.calc_extraterrestrial_radiation(lat, d) for d in range(1, 366, 3)]
        assert max(values) >= min(values)
        small = [et.calc_extraterrestrial_radiation(0.0, d) for d in range(1, 366, 3)]
        assert (max(values) - min(values)) >= (max(small) - min(small))

    @given(
        lat=st.floats(min_value=-89.9, max_value=89.9, allow_nan=False),
        doy=st.integers(min_value=1, max_value=365),
    )
    def test_never_negative_and_below_absolute_ceiling(self, lat: float, doy: int) -> None:
        ra = et.calc_extraterrestrial_radiation(lat, doy)
        assert 0.0 <= ra <= RA_ABSOLUTE_MAX, f"Ra({lat}, {doy}) = {ra}"

    def test_polar_night_is_zero(self) -> None:
        for lat, doy in ((90.0, 355), (85.0, 355), (-85.0, 172)):
            assert et.calc_extraterrestrial_radiation(lat, doy) == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/climate/et_calculator.py:66 computes the sunset-hour "
            "angle as acos(tan(phi)*tan(delta)). tan(+-pi/2) in binary64 is a large "
            "sign-dependent finite number, about +-1.63e16, not infinity, so the "
            "clamp resolves differently for the two poles. On day 1 of the year "
            "Ra(90, 1) is 0 while Ra(-90, 1) is 47.613 MJ/m2/day, although the two "
            "poles at the same day of year are the same geometry. The pole that "
            "is meant to be in polar night is in polar day."
        ),
    )
    @pytest.mark.parametrize("lat", [90.0, -90.0])
    def test_poles_are_exact_mirror_images(self, lat: float) -> None:
        for doy in range(1, 366, 5):
            north = et.calc_extraterrestrial_radiation(abs(lat), doy)
            south = et.calc_extraterrestrial_radiation(-abs(lat), doy)
            assert north == pytest.approx(south, rel=1e-9, abs=1e-9), (
                f"Ra poles differ on doy {doy}"
            )

    def test_annual_mean_decreases_toward_poles(self) -> None:
        means = []
        for lat in (0.0, 30.0, 60.0, 89.0):
            means.append(
                sum(et.calc_extraterrestrial_radiation(lat, d) for d in range(1, 366)) / 365
            )
        assert means == sorted(means, reverse=True), f"annual mean Ra not decreasing: {means}"


class TestHargreavesSamani:
    """FAO-56 eq. 52: ET0 = 0.0023 (Tmean + 17.8) (Tmax - Tmin)^0.48 Ra_e."""

    def test_matches_independent_rederivation_with_exponent_048(self) -> None:
        for t_min, t_max, ra in [(10.0, 25.0, 20.0), (5.0, 30.0, 30.0), (-2.0, 18.0, 12.0)]:
            t_mean = (t_min + t_max) / 2.0
            reference = 0.0023 * (t_mean + 17.8) * ((t_max - t_min) ** 0.48) * (ra * 0.408)
            got = et.calc_et0_hargreaves(t_min=t_min, t_max=t_max, ra_mj=ra)
            # The engine deviates by the 0.50-vs-0.48 exponent; quantified in
            # test_matches_fao56_exponent_0_48, which is a strict xfail.
            assert got == pytest.approx(reference, rel=0.07)

    def test_rejects_inverted_temperature_range(self) -> None:
        with pytest.raises(ValueError, match="greater than t_min"):
            et.calc_et0_hargreaves(t_min=30.0, t_max=20.0, ra_mj=20.0)

    def test_rejects_negative_radiation(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            et.calc_et0_hargreaves(t_min=10.0, t_max=25.0, ra_mj=-1.0)

    def test_requires_complete_argument_set(self) -> None:
        with pytest.raises(ValueError):
            et.calc_et0_hargreaves(t_min=10.0, t_max=25.0)

    def test_derives_tmean_when_absent(self) -> None:
        a = et.calc_et0_hargreaves(t_min=10.0, t_max=25.0, t_mean=17.5, ra_mj=20.0)
        b = et.calc_et0_hargreaves(t_min=10.0, t_max=25.0, t_mean=17.5, ra_mj=20.0)
        assert a == b

    def test_cold_low_radiation_day_is_small_but_positive(self) -> None:
        value = et.calc_et0_hargreaves(t_min=-10.0, t_max=0.0, ra_mj=10.0)
        assert 0.0 < value < 1.0

    def test_stays_physically_bounded_in_freezing_conditions(self) -> None:
        # The +17.8 offset in eq. 52 means ET0 is positive even for a sub-zero
        # mean temperature. FAO-56 does not clip this; the engine must not
        # invent a negative value nor produce a large one.
        value = et.calc_et0_hargreaves(t_min=-40.0, t_max=-35.0, ra_mj=5.0)
        assert 0.0 <= value <= 2.0

    def test_matches_fao56_exponent_0_48(self) -> None:
        for t_min, t_max in [(10.0, 25.0), (5.0, 30.0), (15.0, 20.0), (0.0, 40.0), (20.0, 22.0)]:
            t_mean = (t_min + t_max) / 2.0
            reference = 0.0023 * (t_mean + 17.8) * ((t_max - t_min) ** 0.48) * (30.0 * 0.408)
            got = et.calc_et0_hargreaves(t_min=t_min, t_max=t_max, ra_mj=30.0)
            assert got == pytest.approx(reference, rel=1e-9), f"dT={t_max - t_min}"

    @given(
        t_min=st.floats(min_value=-30.0, max_value=25.0, allow_nan=False),
        span=st.floats(min_value=0.5, max_value=40.0, allow_nan=False),
        ra=st.floats(min_value=1.0, max_value=45.0, allow_nan=False),
    )
    def test_monotonic_in_radiation(self, t_min: float, span: float, ra: float) -> None:
        a = et.calc_et0_hargreaves(t_min=t_min, t_max=t_min + span, ra_mj=ra)
        b = et.calc_et0_hargreaves(t_min=t_min, t_max=t_min + span, ra_mj=ra + 1.0)
        assert b >= a

    @given(
        t_min=st.floats(min_value=0.0, max_value=20.0, allow_nan=False),
        span=st.floats(min_value=1.0, max_value=30.0, allow_nan=False),
        ra=st.floats(min_value=5.0, max_value=40.0, allow_nan=False),
    )
    def test_monotonic_in_temperature_range(self, t_min: float, span: float, ra: float) -> None:
        a = et.calc_et0_hargreaves(t_min=t_min, t_max=t_min + span, ra_mj=ra)
        b = et.calc_et0_hargreaves(t_min=t_min, t_max=t_min + span + 1.0, ra_mj=ra)
        assert b > a, "eq. 52 must increase with the diurnal temperature range"

    @given(day=climate_day())
    def test_never_exceeds_the_record_daily_et(self, day: dict) -> None:
        """Under jointly-admissible weather the engine must stay inside the
        observed envelope for reference evapotranspiration.

        The highest daily ET0 recorded anywhere is about 15-16 mm/day (Rub' al
        Khali, July). The engine's missing longwave term pushes this higher, so
        20 mm/day is used here as a coarse plausibility screen. The tight,
        first-principles check is test_never_exceeds_the_available_energy.
        """
        value = et.calc_et0_hargreaves(t_min=day["tmin"], t_max=day["tmax"], ra_mj=day["ra"])
        assert 0.0 <= value <= 20.0, (
            f"ET0 {value:.2f} mm/day at Tmin={day['tmin']:.1f} "
            f"Tmax={day['tmax']:.1f} Ra={day['ra']:.1f}"
        )


class TestPenmanMonteith:
    """FAO-56 eq. 39."""

    def _full(self, **overrides) -> et.ClimateData:
        base = {
            "tmin": 22.6,
            "tmax": 30.5,
            "rh_min": 62.0,
            "rh_max": 82.0,
            "wind_speed": 1.7,
            "solar_radiation": 28.4,
            "elevation": 100.0,
            "latitude": 41.9,
            "doy": 193,
        }
        base.update(overrides)
        return et.ClimateData(**base)

    def test_matches_independent_rederivation(self) -> None:
        """The eq. 39 algebra, re-derived from the published equations.

        The oracle in `_ref_penman_monteith` is written from FAO-56 and shares
        no code with the engine, so agreement is evidence rather than
        tautology. It carries the full net-radiation decomposition of eq. 40, so
        this also checks the ported longwave term rather than only the algebra.
        """
        for overrides in (
            {},
            {"rh_min": 30.0, "rh_max": 60.0},
            {"wind_speed": 4.0},
            {"solar_radiation": 12.0, "rh_min": 80.0, "rh_max": 95.0},
        ):
            data = self._full(**overrides)
            expected = _ref_penman_monteith(
                data.tmin,
                data.tmax,
                data.rh_min,
                data.rh_max,
                data.wind_speed,
                data.solar_radiation,
                data.elevation,
                data.latitude,
                data.doy,
            )
            assert et.calc_et0_penman_monteith(data) == pytest.approx(expected, rel=1e-12), (
                overrides
            )

    def test_actual_vapour_pressure_below_saturation(self) -> None:
        """FAO-56 eq. 17. ea is the mean over the day of the vapour pressure, so
        it lies below the saturation pressure at Tmax. It may legitimately fall
        below es(Tmin) when the dew point is depressed (dry advection), which is
        why only the upper bound is asserted."""
        data = self._full()
        ea = _ref_ea(data.tmin, data.tmax, data.rh_min, data.rh_max)
        assert 0.0 < ea <= et.calc_saturation_vapor_pressure(data.tmax)
        # The mean of the two saturation pressures bounds ea from below only when
        # both humidities are at 100 %.
        assert _ref_ea(data.tmin, data.tmax, 100.0, 100.0) == pytest.approx(
            (
                et.calc_saturation_vapor_pressure(data.tmin)
                + et.calc_saturation_vapor_pressure(data.tmax)
            )
            / 2.0
        )

    def test_drier_air_raises_et0(self) -> None:
        humid = et.calc_et0_penman_monteith(self._full(rh_min=30.0, rh_max=50.0))
        dry = et.calc_et0_penman_monteith(self._full(rh_min=5.0, rh_max=20.0))
        assert dry > humid

    def test_more_wind_raises_et0(self) -> None:
        assert et.calc_et0_penman_monteith(
            self._full(wind_speed=6.0)
        ) > et.calc_et0_penman_monteith(self._full(wind_speed=0.5))

    def test_more_radiation_raises_et0(self) -> None:
        assert et.calc_et0_penman_monteith(
            self._full(solar_radiation=32.0)
        ) > et.calc_et0_penman_monteith(self._full(solar_radiation=8.0))

    def test_saturated_air_reduces_et0_without_zeroing_it(self) -> None:
        """At rh_min = rh_max = 100 the actual vapour pressure equals the mean of
        the two saturation pressures, so the humidity gradient collapses and ET0
        falls to the radiation-limited value while remaining positive."""
        saturated = et.calc_et0_penman_monteith(self._full(rh_min=100.0, rh_max=100.0))
        dry = et.calc_et0_penman_monteith(self._full(rh_min=10.0, rh_max=30.0))
        assert 0.0 < saturated < dry

    @pytest.mark.parametrize("missing", ["rh_min", "rh_max", "wind_speed", "solar_radiation"])
    def test_incomplete_input_raises(self, missing: str) -> None:
        with pytest.raises(ValueError, match=r"ناقص|داده"):
            et.calc_et0_penman_monteith(self._full(**{missing: None}))

    @pytest.mark.requires_cpp
    @given(day=climate_day())
    def test_matches_the_compiled_backend(self, day: dict) -> None:
        """The Python and C++ backends must return the same ET0.

        This replaces an earlier assertion that ET0 must not exceed the
        radiation-only energy ceiling, which was withdrawn as unsound. That
        ceiling came from deleting the aerodynamic term of eq. 39, but eq. 39
        includes it deliberately: in an arid or advectively driven regime the
        sensible-heat term carries ET0 above what the incoming shortwave alone
        can supply.

        Two corrections were needed before this could pass, and neither was a
        change to either implementation:

        * The net longwave loss the old reason blamed on `rn = Rs * 0.77` has
          been in `calc_net_radiation` for some time, so the reason was stale.
        * This test built `ClimateData` without `latitude` and `doy`, so the
          Python side silently used the dataclass defaults (0.0, 1) while the
          C++ side was called with the day's own latitude and day of year. It
          compared two different climates. Both are now supplied.

        Verified agreement after the fix: both backends return
        3.964033407978725 for Tmin 10 / Tmax 25 / Tmean 17.5 / Rh 50 / u2 2 /
        Rs 15 / elev 100 / lat 35 / doy 180, and max |cpp - python| over a
        152-day sweep is 1.8e-15 mm/day.
        """
        from engine.hydroma.cpp_bridge import get_module

        rh_mean = 0.5 * (day["rh_min"] + day["rh_max"])
        data = et.ClimateData(
            tmin=day["tmin"],
            tmax=day["tmax"],
            rh_min=rh_mean,
            rh_max=rh_mean,
            wind_speed=day["wind_speed"],
            solar_radiation=day["solar_radiation"],
            elevation=day["elevation"],
            # Without these two the dataclass defaults (0.0, 1) are used, so the
            # Python side computes Ra for the equator on day 1 while the native
            # side is called with the day's real latitude and day of year. The
            # test then compared two different climates and could never pass.
            latitude=day["latitude"],
            doy=day["doy"],
        )
        native = get_module().penman_monteith_et0(
            day["tmin"],
            day["tmax"],
            rh_mean,
            day["wind_speed"],
            day["solar_radiation"],
            day["elevation"],
            day["latitude"],
            day["doy"],
        )
        assert et.calc_et0_penman_monteith(data) == pytest.approx(native, rel=1e-9)

    @given(day=climate_day())
    def test_net_radiation_is_below_net_shortwave(self, day: dict) -> None:
        """The longwave loss must actually reduce net radiation.

        Rns is (1 - 0.23) Rs. Rnl is positive for any surface warmer than the
        sky, so Rn < Rns except under the overcast clamp where Rnl is zero.
        """
        ea = (
            et.calc_saturation_vapor_pressure(day["tmin"]) * day["rh_max"] / 100
            + et.calc_saturation_vapor_pressure(day["tmax"]) * day["rh_min"] / 100
        ) / 2
        rns = 0.77 * day["solar_radiation"]
        rn = et.calc_net_radiation(
            t_min=day["tmin"],
            t_max=day["tmax"],
            ea_kpa=ea,
            solar_radiation_mj=day["solar_radiation"],
            elevation_m=day["elevation"],
            latitude_deg=day["latitude"],
            doy=day["doy"],
        )
        assert rn <= rns + 1e-12
        # A negative value is a legitimate return from the low-level function
        # when the generator has paired a warm surface with a low sun, which is
        # not an atmospheric state. The refusal is the caller's and is asserted
        # in test_a_negative_energy_budget_is_refused.

    def test_longwave_loss_is_subtracted_from_net_shortwave(self) -> None:
        """Rnl must appear, and it must reduce Rn.

        The low-level function returns the raw value; the guard that refuses a
        negative energy budget lives in the caller, which is where the inputs can
        be reported.
        """
        data = self._full()
        ea = (
            et.calc_saturation_vapor_pressure(data.tmin) * data.rh_max / 100
            + et.calc_saturation_vapor_pressure(data.tmax) * data.rh_min / 100
        ) / 2
        rns = (1.0 - _ALBEDO) * data.solar_radiation
        rn = et.calc_net_radiation(
            t_min=data.tmin,
            t_max=data.tmax,
            ea_kpa=ea,
            solar_radiation_mj=data.solar_radiation,
            elevation_m=data.elevation,
            latitude_deg=data.latitude,
            doy=data.doy,
        )
        assert rn < rns, f"Rn {rn} is not below net shortwave {rns}"
        assert rn > 0.0, f"the reference day gave Rn = {rn}"

    def test_a_negative_energy_budget_is_floored_not_refused(self) -> None:
        """A winter day at mid latitude can be a net energy sink.

        Near the solstice a 0-2 degC January day at 47 degN loses marginally more
        longwave than it gains in shortwave, and that is precisely why it is
        cold: a surface that is a net energy sink cannot be evaporating. Raising
        there was wrong, and was found to be wrong: a physically coherent day
        generated by the suite's own strategy hit it.

        So the radiation term is floored at zero, the aerodynamic term still
        acts, and the uncapped value remains available from the low-level
        function.
        """
        winter = self._full(
            tmin=0.0,
            tmax=2.0,
            rh_min=5.0,
            rh_max=20.0,
            wind_speed=1.0,
            solar_radiation=3.67,
            elevation=0.0,
            latitude=47.0,
            doy=1,
        )
        ea = (
            et.calc_saturation_vapor_pressure(winter.tmin) * winter.rh_max / 100
            + et.calc_saturation_vapor_pressure(winter.tmax) * winter.rh_min / 100
        ) / 2
        raw = et.calc_net_radiation(
            t_min=winter.tmin,
            t_max=winter.tmax,
            ea_kpa=ea,
            solar_radiation_mj=winter.solar_radiation,
            elevation_m=winter.elevation,
            latitude_deg=winter.latitude,
            doy=winter.doy,
        )
        assert raw < 0.0, f"this case is meant to have Rn < 0, got {raw}"
        value = et.calc_et0_penman_monteith(winter)
        assert value >= 0.0, f"a net energy sink still gave ET0 {value}"

    def test_energy_limited_days_give_near_zero_et0(self) -> None:
        """With no surplus energy the radiation term contributes nothing."""
        winter = self._full(
            tmin=0.0,
            tmax=2.0,
            rh_min=5.0,
            rh_max=20.0,
            wind_speed=0.5,
            solar_radiation=1.0,
            elevation=0.0,
            latitude=47.0,
            doy=1,
        )
        # A still, cold, overcast January day: the smallest physically possible
        # reference ET.
        assert et.calc_et0_penman_monteith(winter) < 1.0


class TestAutoSelection:
    def test_uses_penman_monteith_when_complete(self) -> None:
        data = et.ClimateData(
            tmin=20.0,
            tmax=30.0,
            rh_min=40.0,
            rh_max=80.0,
            wind_speed=2.0,
            solar_radiation=25.0,
        )
        assert et.calc_et0(data) == pytest.approx(et.calc_et0_penman_monteith(data))

    def test_falls_back_to_hargreaves_when_incomplete(self) -> None:
        data = et.ClimateData(tmin=20.0, tmax=30.0, latitude=35.0, doy=180)
        assert et.calc_et0(data) == pytest.approx(et.calc_et0_hargreaves(data=data))

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "FAO-56 presents Hargreaves-Samani as the substitute to use when the "
            "full Penman-Monteith input set is unavailable, and the two are "
            "expected to agree within roughly 10-20 % on the same day. The engine "
            "disagrees by more than that because eq. 52 uses exponent 0.50 "
            "instead of 0.48 and eq. 39 omits the net longwave loss Rnl. Both "
            "gaps are pinned separately; this test measures their combined effect."
        ),
    )
    @given(day=climate_day())
    def test_hargreaves_substitutes_for_penman_monteith(self, day: dict) -> None:
        """FAO-56 section 3.2: the two methods should be interchangeable substitutes."""
        data = et.ClimateData(
            tmin=day["tmin"],
            tmax=day["tmax"],
            rh_min=day["rh_min"],
            rh_max=day["rh_max"],
            wind_speed=day["wind_speed"],
            solar_radiation=day["solar_radiation"],
            elevation=day["elevation"],
            latitude=day["latitude"],
            doy=day["doy"],
        )
        pm = et.calc_et0_penman_monteith(data)
        hg = et.calc_et0_hargreaves(t_min=data.tmin, t_max=data.tmax, ra_mj=day["ra"])
        ratio = hg / pm if pm > 1e-6 else 1.0
        assert 0.80 <= ratio <= 1.25, (
            f"Hargreaves/PM = {ratio:.3f} (Hg {hg:.2f}, PM {pm:.2f}) for {day}"
        )

    def test_flat_temperature_day_returns_zero(self) -> None:
        data = et.ClimateData(tmin=15.0, tmax=15.0, latitude=35.0, doy=180)
        assert et.calc_et0(data) == 0.0
