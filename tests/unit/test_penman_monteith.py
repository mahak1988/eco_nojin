"""Tests for FAO-56 Penman-Monteith and Hargreaves ET0 calculations."""

import pytest

from engine.hydroma.climate.et_calculator import (
    ClimateData,
    calc_delta,
    calc_et0,
    calc_et0_hargreaves,
    calc_et0_penman_monteith,
    calc_extraterrestrial_radiation,
    calc_psychrometric,
    calc_saturation_vapor_pressure,
)


class TestHelperFunctions:
    """Unit tests for FAO-56 helper functions."""

    def test_saturation_vapor_pressure_25c(self):
        es = calc_saturation_vapor_pressure(25.0)
        assert 3.1 < es < 3.3

    def test_delta_positive(self):
        delta = calc_delta(25.0)
        assert delta > 0

    def test_psychrometric_sea_level(self):
        gamma = calc_psychrometric(elevation=0.0)
        assert 0.06 < gamma < 0.07

    def test_psychrometric_high_elevation(self):
        gamma = calc_psychrometric(elevation=2000.0)
        assert gamma < calc_psychrometric(0.0)

    def test_extraterrestrial_radiation_positive(self):
        ra = calc_extraterrestrial_radiation(latitude=35.0, doy=180)
        assert ra > 0


class TestHargreaves:
    """Hargreaves-Samani ET0 tests."""

    def test_normal_conditions(self):
        et0 = calc_et0_hargreaves(t_min=10.0, t_max=25.0, t_mean=17.5, ra_mj=15.0)
        assert et0 > 0
        assert 1.5 < et0 < 2.5

    def test_invalid_temps_raise(self):
        with pytest.raises(ValueError):
            calc_et0_hargreaves(t_min=20.0, t_max=15.0, t_mean=17.5, ra_mj=15.0)

    def test_negative_ra_raises(self):
        with pytest.raises(ValueError):
            calc_et0_hargreaves(t_min=10.0, t_max=25.0, t_mean=17.5, ra_mj=-1.0)

    def test_dataclass_api(self):
        data = ClimateData(tmin=10.0, tmax=25.0, latitude=35.0, doy=180)
        et0 = calc_et0_hargreaves(data=data)
        assert et0 > 0


class TestPenmanMonteith:
    """Full FAO-56 Penman-Monteith ET0 tests."""

    def test_full_pm_with_all_params(self):
        data = ClimateData(
            tmin=15.0,
            tmax=30.0,
            rh_min=30.0,
            rh_max=70.0,
            wind_speed=2.0,
            solar_radiation=20.0,
            elevation=0.0,
            latitude=35.0,
            doy=180,
        )
        et0 = calc_et0_penman_monteith(data)
        assert et0 > 0
        assert 1.0 < et0 < 12.0

    def test_pm_hot_dry_day(self):
        data = ClimateData(
            tmin=25.0,
            tmax=42.0,
            rh_min=10.0,
            rh_max=30.0,
            wind_speed=3.5,
            solar_radiation=28.0,
            elevation=0.0,
            latitude=32.0,
            doy=200,
        )
        et0 = calc_et0_penman_monteith(data)
        assert et0 > 3.0

    def test_pm_cool_humid_day(self):
        data = ClimateData(
            tmin=8.0,
            tmax=18.0,
            rh_min=70.0,
            rh_max=95.0,
            wind_speed=1.0,
            solar_radiation=8.0,
            elevation=500.0,
            latitude=45.0,
            doy=30,
        )
        et0 = calc_et0_penman_monteith(data)
        assert et0 < 3.0

    def test_pm_missing_params_raises(self):
        data = ClimateData(tmin=15.0, tmax=30.0, latitude=35.0, doy=180)
        with pytest.raises(ValueError, match="داده‌های ناقص"):
            calc_et0_penman_monteith(data)

    def test_pm_never_negative(self):
        data = ClimateData(
            tmin=10.0,
            tmax=15.0,
            rh_min=80.0,
            rh_max=100.0,
            wind_speed=0.5,
            solar_radiation=5.0,
            elevation=0.0,
            latitude=35.0,
            doy=180,
        )
        et0 = calc_et0_penman_monteith(data)
        assert et0 >= 0.0


class TestAutoSelect:
    """Test calc_et0 auto-selection between PM and Hargreaves."""

    def test_auto_select_pm_when_complete(self):
        data = ClimateData(
            tmin=15.0,
            tmax=30.0,
            rh_min=30.0,
            rh_max=70.0,
            wind_speed=2.0,
            solar_radiation=20.0,
            elevation=0.0,
            latitude=35.0,
            doy=180,
        )
        et0 = calc_et0(data)
        assert et0 > 0

    def test_auto_select_hargreaves_when_incomplete(self):
        data = ClimateData(tmin=10.0, tmax=25.0, latitude=35.0, doy=180)
        et0 = calc_et0(data)
        assert et0 > 0
