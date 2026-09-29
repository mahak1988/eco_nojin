"""S09 — Cross-module dimensional and unit consistency.

Why this module exists
----------------------
The engine computes the same physical quantities in more than one place, in more
than one unit system, under more than one name. A defect confined to one module
is caught by that module's own tests. A defect that appears when two modules are
used together - a hectare-to-square-metre factor applied twice, a millimetre
value multiplied by a centimetre value - is caught nowhere, because neither
module is wrong on its own.

Each test below therefore compares two *independent* code paths for the same
quantity, or checks a value against a first-principles unit identity.

Unit ledger used throughout
---------------------------
    1 ha            = 10 000 m2
    1 m3            = 1000 L
    1 cm3/cm3       = 10 mm of water per metre of soil
    1 cm            = 10 mm
    1 MJ/m2         = 0.408 mm of equivalent evaporation (FAO-56 eq. 40)
    1 kg CO2        = 44/12 kg C
    1 dS/m         == 1 mS/cm
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from engine.hydroma.carbon.calculator import CarbonProjectType, calculate_carbon_sequestration
from engine.hydroma.climate.et_calculator import (
    ClimateData,
    calc_et0_penman_monteith,
    calc_saturation_vapor_pressure,
)
from engine.hydroma.groundwater.models import (
    GroundwaterBucketInput,
    estimate_aquifer_properties,
    run_groundwater_bucket,
)
from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput
from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG
from engine.hydroma.watershed.calculator import (
    calculate_runoff,
    design_check_dam,
    design_contour_trench,
)

HA_TO_M2 = 10_000.0
MM_PER_M_OF_SOIL = 1000.0  # 1 cm3/cm3 over 1 m = 1000 mm


class TestUnitIdentities:
    """The conversions the engine relies on, checked against their definitions."""

    def test_volume_scales_linearly_with_area(self) -> None:
        """1 ha = 10 000 m2, so 50 mm over 2 ha is 1000 m3 of rain.

        The rational RUNOFF volume carries the coefficient: C x P x A, which at
        the default C = 0.6 is 600 m3. It previously returned the full rainfall
        volume, ignoring C, while the peak flow of the same call used C.
        """
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=50.0, area_ha=2.0, method="Rational")
        )
        assert out.volume_m3 == pytest.approx(0.6 * 50.0 / 1000.0 * 2.0 * HA_TO_M2)

    def test_runoff_module_agrees_with_watershed_module_in_metres(self) -> None:
        """The same rational runoff expressed through two APIs and two unit
        systems must agree exactly."""
        area_m2, rain_mm, c = 75_000.0, 65.0, 0.42
        from_runoff_model = (
            RunoffCalculator()
            .execute(
                RunoffInput(
                    precipitation_mm=rain_mm,
                    area_ha=area_m2 / HA_TO_M2,
                    method="Rational",
                    rational_coefficient=c,
                )
            )
            .peak_flow_m3s
        )
        from_watershed = calculate_runoff(area_m2, rain_mm, c)
        # peak is m3/s for a 1-hour storm, so multiply the volume by 1/3600.
        assert from_runoff_model == pytest.approx(from_watershed / 3600.0, rel=1e-6)

    def test_hectare_to_square_metre_factor_is_not_applied_twice(self) -> None:
        """The check dam converts area to hectares for the rational method while
        the same function receives square metres. A double conversion would make
        the peak flow 10 000 times too small."""
        area_m2, rain_mm = 500_000.0, 100.0
        out = design_check_dam(5.0, area_m2, rain_mm, storm_duration_h=1.0)
        expected = 0.6 * rain_mm * (area_m2 / HA_TO_M2) / 360.0
        assert out["peak_flow_m3s"] == pytest.approx(expected, rel=1e-3)

    def test_litres_to_cubic_metres(self) -> None:
        out = estimate_aquifer_properties(1e-5, 0.12, 1e5, 3.0)
        assert out["volume_available_liters"] == pytest.approx(
            out["volume_available_m3"] * 1000.0, rel=1e-9
        )

    def test_volumetric_water_content_to_millimetres_per_metre(self) -> None:
        """theta of 0.2 cm3/cm3 over a 1 m root zone is 200 mm of water."""
        from engine.hydroma.soil.water_retention import calculate_available_water

        out = calculate_available_water(theta_fc=0.35, theta_wp=0.15, root_depth=100.0)
        assert out["total_available_water_mm"] == pytest.approx(0.20 * 1000.0, rel=1e-9)
        assert out["total_available_water_mm"] == pytest.approx(
            out["total_available_water"] * 10.0, rel=1e-9
        )

    def test_mj_to_millimetre_equivalent_evaporation(self) -> None:
        """FAO-56 eq. 40: 1 MJ/m2 of energy evaporates 0.408 mm of water."""
        # Hargreaves eq. 52 is linear in the millimetre-equivalent Ra.
        from engine.hydroma.climate.et_calculator import calc_et0_hargreaves

        single = calc_et0_hargreaves(t_min=10.0, t_max=25.0, ra_mj=10.0)
        double = calc_et0_hargreaves(t_min=10.0, t_max=25.0, ra_mj=20.0)
        assert double == pytest.approx(2.0 * single, rel=1e-9)

    def test_saturation_vapour_pressure_is_in_kilopascals(self) -> None:
        """FAO-56 eq. 11 returns kPa. At 25 C the accepted value is 3.169 kPa,
        which is 31.69 hPa and 0.3169 bar - if the engine returned bars the whole
        Penman-Monteith expression would be off by two orders of magnitude."""
        es = calc_saturation_vapor_pressure(25.0)
        assert es == pytest.approx(3.169, rel=2e-3)
        assert 1.0 < es < 10.0

    def test_carbon_is_reported_in_tonnes_of_co2(self) -> None:
        """The rate table is tonnes CO2 per hectare per year; if the module were
        returning tonnes of carbon the ratio to tonnes of C would be 44/12."""
        out = calculate_carbon_sequestration(CarbonProjectType.AFFORESTATION, 1.0, duration_years=1)
        expected_t_co2 = 8.0 * 0.85
        assert out["total_carbon_tonnes"] == pytest.approx(expected_t_co2, rel=1e-3)
        assert out["total_carbon_tonnes"] != pytest.approx(expected_t_co2 * 12.0 / 44.0, rel=1e-2)


class TestCrossModuleAgreement:
    def test_recharge_and_pumping_agree_in_millimetres(self) -> None:
        """The groundwater bucket speaks mm; a caller holding the irrigation
        scheduler's mm/day figures must be able to combine them directly."""
        depth = 25.0
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=100.0,
                recharge_mm=0.0,
                pumping_mm=depth,
                alpha=0.0,
                months=4,
            )
        )
        assert out.storage_series_mm == pytest.approx([75.0, 50.0, 25.0, 0.0], abs=1e-4)
        assert out.total_pumping_mm == pytest.approx(4 * depth, abs=1e-3)

    def test_storage_and_runoff_cover_are_the_same_depth(self) -> None:
        """A catchment that loses 30 mm to runoff has 70 mm left, both in mm."""
        area_m2, rain_mm, c = 100_000.0, 100.0, 0.3
        runoff_depth_mm = calculate_runoff(area_m2, rain_mm, c) / (area_m2 / 1000.0)
        assert runoff_depth_mm == pytest.approx(30.0, rel=1e-9)
        assert rain_mm - runoff_depth_mm == pytest.approx(70.0, rel=1e-9)

    def test_check_dam_runoff_matches_the_standalone_helper(self) -> None:
        """design_check_dam hard-codes C = 0.6; the helper must reproduce its
        runoff volume for the same coefficient, so a future change to one is
        caught."""
        area_m2, rain_mm = 250_000.0, 140.0
        out = design_check_dam(5.0, area_m2, rain_mm)
        assert out["runoff_volume_m3"] == pytest.approx(
            calculate_runoff(area_m2, rain_mm, 0.6), rel=2e-3
        )

    def test_contour_trench_volume_matches_its_section_and_length(self) -> None:
        """Length x section = volume, at the precision the engine publishes.

        total_length_m is rounded to whole metres and cross_section_m2 to three
        decimals, so reconstructing the volume from the published fields carries
        an error of about 0.0005 m2 x 167 000 m = 84 m3. The tolerance is sized
        to that, not to a relative guess.
        """
        out = design_contour_trench(
            5.0, 1_000_000.0, depth_m=0.5, bottom_width_m=0.4, side_slope_hv=0.75
        )
        reconstructed = out["total_length_m"] * out["cross_section_m2"]
        assert out["trench_volume_m3"] == pytest.approx(reconstructed, abs=100.0)
        assert out["infiltration_gain_m3"] == pytest.approx(
            out["trench_volume_m3"] * out["infiltration_efficiency"], abs=0.5
        )

    def test_soil_conductivity_table_is_in_centimetres_per_day(self) -> None:
        """The table header says cm/day. Sand at 712.8 cm/day is 29.7 cm/hr, the
        order of magnitude published for sand. A table in m/s would read 7.9e-5,
        and a table in mm/day would read 6.1e6."""
        sand = SOIL_PARAMETERS_VG["sand"]["Ks"]
        assert 100.0 < sand < 2000.0
        assert sand / 24.0 == pytest.approx(29.7, rel=0.05)

    def test_et0_outputs_are_millimetres_per_day(self) -> None:
        """A Penman-Monteith result must be an order-of-magnitude daily depth.
        Metres per day would read 0.005; micrometres per day would read 5e6."""
        data = ClimateData(
            tmin=20.0,
            tmax=32.0,
            rh_min=35.0,
            rh_max=75.0,
            wind_speed=2.0,
            solar_radiation=26.0,
            elevation=150.0,
        )
        et0 = calc_et0_penman_monteith(data)
        assert 0.5 < et0 < 15.0, f"{et0} is not a plausible mm/day figure"

    def test_peak_flow_is_cubic_metres_per_second(self) -> None:
        """Rational peak flow for a 50 mm/hr storm over 1 ha at C = 0.6 is
        0.6 * 50 * 1 * 10 / 3600 = 0.0833 m3/s. L/s would read 83.3."""
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=50.0, area_ha=1.0, method="Rational", rational_coefficient=0.6
            )
        )
        assert out.peak_flow_m3s == pytest.approx(0.0833, rel=1e-3)


class TestMagnitudeSanity:
    """Each engine subsystem, exercised on one realistic input, must produce a
    number in the range the physical literature reports. This is the coarsest
    net that catches a factor-of-100 unit slip that no single unit test sees."""

    def test_check_dam_cost_is_a_plausible_project_value(self) -> None:
        """A 50 ha catchment check dam at 150 USD/m3 should cost thousands, not
        millions or cents."""
        out = design_check_dam(5.0, 500_000.0, 120.0)
        assert 1_000.0 < out["estimated_cost_usd"] < 5_000_000.0

    def test_contour_trench_cost_is_a_plausible_project_value(self) -> None:
        out = design_contour_trench(8.0, 100_000.0)
        assert 100.0 < out["estimated_cost_usd"] < 5_000_000.0

    def test_carbon_revenue_is_a_plausible_annual_value(self) -> None:
        """100 ha of afforestation at IPCC Tier-1 is 800 t/yr gross; even at an
        implausible 1000 USD/t that is under 1e6 USD/yr, and at a realistic
        4 USD/t it is under 1e4 USD/yr."""
        out = calculate_carbon_sequestration(
            CarbonProjectType.AFFORESTATION, 100.0, duration_years=10
        )
        assert 100.0 < out["annual_revenue_usd"] < 1_000_000.0

    def test_groundwater_storage_is_a_plausible_depth(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(initial_storage_mm=500.0, recharge_mm=20.0, months=24)
        )
        assert 0.0 <= out.final_storage_mm <= 500.0 + 20.0 * 24

    @given(
        area_m2=st.floats(min_value=1000.0, max_value=1e8, allow_nan=False),
        rain=st.floats(min_value=10.0, max_value=500.0, allow_nan=False),
        c=st.floats(min_value=0.05, max_value=0.95, allow_nan=False),
    )
    def test_runoff_depth_never_exceeds_rainfall_depth(
        self, area_m2: float, rain: float, c: float
    ) -> None:
        depth_mm = calculate_runoff(area_m2, rain, c) / (area_m2 / 1000.0)
        assert 0.0 <= depth_mm <= rain + 1e-9

    @given(
        tmin=st.floats(min_value=0.0, max_value=30.0, allow_nan=False),
        tmax=st.floats(min_value=5.0, max_value=45.0, allow_nan=False),
        rh_min=st.floats(min_value=5.0, max_value=95.0, allow_nan=False),
        rh_max=st.floats(min_value=10.0, max_value=100.0, allow_nan=False),
        u2=st.floats(min_value=0.3, max_value=8.0, allow_nan=False),
        rs=st.floats(min_value=1.0, max_value=35.0, allow_nan=False),
    )
    def test_penman_monteith_stays_in_millimetre_range(
        self, tmin: float, tmax: float, rh_min: float, rh_max: float, u2: float, rs: float
    ) -> None:
        value = calc_et0_penman_monteith(
            ClimateData(
                tmin=tmin,
                tmax=max(tmax, tmin + 1.0),
                rh_min=min(rh_min, rh_max - 1.0),
                rh_max=rh_max,
                wind_speed=u2,
                solar_radiation=rs,
                elevation=0.0,
            )
        )
        assert 0.0 <= value <= 100.0, (
            f"{value} is outside the mm/day range; a unit slip of 1000x would land here"
        )
