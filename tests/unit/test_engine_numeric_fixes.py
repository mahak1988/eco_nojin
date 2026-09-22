"""Regression tests for the engine fixes applied on 2026-09-21.

Each test pins the fixed behaviour to an external reference so the defect
cannot silently return.
"""

from __future__ import annotations

import math

import pytest

from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput
from engine.hydroma.soil.salinity import calculate_leaching_requirement
from engine.hydroma.groundwater.models import GroundwaterBucketInput, run_groundwater_bucket
from engine.hydroma.phenology import CROP_PHENOLOGY, _stage_from_gdd
from engine.hydroma.simulation.runners.rothc_runner import stabilization_split


class TestScsCnUnits:
    """SCS-CN must use the SI retention form S = 25400/CN - 254 [mm]."""

    def test_standard_example_matches_nrcs(self):
        # CN = 70, P = 50 mm  ->  S = 108.86 mm, Ia = 21.77 mm,
        # Q = (50-21.77)^2 / (50 + 0.8*108.86) = 5.8 mm  (NRCS worked example)
        out = RunoffCalculator().execute(
            RunoffInput(area_ha=1.0, precipitation_mm=50.0, curve_number=70)
        )
        runoff_depth_mm = out.volume_m3 / (1.0 * 10.0)
        assert runoff_depth_mm == pytest.approx(5.8, abs=0.2)

    def test_retention_is_millimetres_not_inches(self):
        out = RunoffCalculator().execute(
            RunoffInput(area_ha=1.0, precipitation_mm=50.0, curve_number=70)
        )
        # The inch-form bug produced ~45 mm of runoff for this input.
        assert out.volume_m3 < 100.0

    def test_below_initial_abstraction_gives_no_runoff(self):
        out = RunoffCalculator().execute(
            RunoffInput(area_ha=1.0, precipitation_mm=10.0, curve_number=70)
        )
        assert out.volume_m3 == 0.0


class TestLeachingRequirement:
    """FAO-29 / Rhoades (1974): LR = ECw / (5*ECe - ECw)."""

    def test_matches_fao_formula(self):
        # ECw = 1, target ECe = 4  ->  LR = 1/(5*4-1) = 0.0526
        res = calculate_leaching_requirement(ec_soil=8.0, ec_water=1.0)
        assert res["leaching_required"] is True
        assert res["leaching_fraction"] == pytest.approx(1.0 / 19.0, abs=1e-3)

    def test_no_fabricated_floor(self):
        # A tiny requirement must not be inflated to 10%.
        res = calculate_leaching_requirement(ec_soil=9.0, ec_water=0.2)
        assert res["leaching_fraction"] < 0.05

    def test_unsuitable_water_is_flagged_not_clamped(self):
        res = calculate_leaching_requirement(ec_soil=30.0, ec_water=25.0)
        assert "too high" in res["reason"].lower() or res.get("leaching_required") is False

    def test_no_leaching_when_soil_is_below_target(self):
        res = calculate_leaching_requirement(ec_soil=3.0, ec_water=1.0)
        assert res["leaching_required"] is False


class TestGroundwaterRecharge:
    def test_explicit_zero_recharge_drains_storage(self):
        out = run_groundwater_bucket(
            GroundwaterBucketInput(recharge_mm=0.0, pumping_mm=10.0, months=24)
        )
        assert out.total_recharge_mm == 0.0
        assert out.final_storage_mm == 0.0

    def test_derived_recharge_when_not_supplied(self):
        out = run_groundwater_bucket(GroundwaterBucketInput(months=12))
        assert out.total_recharge_mm > 0.0


class TestPhenologyStages:
    def test_grain_fill_stage_exists(self):
        pheno = CROP_PHENOLOGY["wheat"]
        assert _stage_from_gdd(700.0, pheno) == "flowering"
        assert _stage_from_gdd(800.0, pheno) == "grain_fill"
        assert _stage_from_gdd(1000.0, pheno) == "maturity"
        assert _stage_from_gdd(50.0, pheno) == "pre_emergence"


class TestRothcPartition:
    """RothC-26.3 clay-dependent CO2/(BIO+HUM) partition (Coleman 1996)."""

    def test_matches_published_ratio(self):
        # x = 1.67*(1.85 + 1.60*exp(-0.0786*23.4)) = 3.5143
        # CO2 = 0.7785, BIO+HUM = 0.2215
        co2, stab = stabilization_split(23.4)
        assert co2 == pytest.approx(0.7785, abs=0.002)
        assert stab == pytest.approx(0.2215, abs=0.002)

    def test_stabilized_fraction_stays_within_rothc_range(self):
        for clay in (0.0, 10.0, 23.4, 40.0, 60.0):
            _co2, stab = stabilization_split(clay)
            assert 0.14 <= stab <= 0.25, f"clay={clay} gives stab={stab}"

    def test_stabilization_increases_with_clay(self):
        _c0, stab_low = stabilization_split(5.0)
        _c1, stab_high = stabilization_split(50.0)
        assert stab_high > stab_low

    def test_constant_0_46_is_not_reproducible(self):
        # The old hard-coded 0.46 cannot arise from the RothC relation at any clay%.
        assert all(stabilization_split(c)[1] < 0.30 for c in range(0, 101, 5))
