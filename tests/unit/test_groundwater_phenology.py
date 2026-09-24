"""Tests for groundwater and phenology modules."""

import pytest

from engine.hydroma.groundwater.models import (
    GroundwaterBucketInput,
    run_groundwater_bucket,
)
from engine.hydroma.phenology import (
    CROP_PHENOLOGY,
    PhenologyInput,
    _daily_gdd,
    _stage_from_gdd,
    run_phenology,
)


class TestGroundwater:
    def test_mass_balance_no_pumping(self):
        out = run_groundwater_bucket(GroundwaterBucketInput(pumping_mm=0.0, months=12))
        assert out.final_storage_mm >= 0.0
        assert out.total_recharge_mm > 0.0
        assert out.total_baseflow_mm > 0.0

    def test_overdraft_reduces_storage(self):
        base = run_groundwater_bucket(GroundwaterBucketInput(pumping_mm=0.0, months=12))
        pumped = run_groundwater_bucket(GroundwaterBucketInput(pumping_mm=50.0, months=12))
        assert pumped.final_storage_mm < base.final_storage_mm

    def test_zero_recharge_drains_storage(self):
        out = run_groundwater_bucket(
            GroundwaterBucketInput(recharge_mm=0.0, pumping_mm=10.0, months=24)
        )
        assert out.final_storage_mm == 0.0

    def test_outputs_have_honest_provenance(self):
        out = run_groundwater_bucket(GroundwaterBucketInput())
        assert out.data_source == "simulated"
        assert "Groundwater bucket" in out.model

    def test_series_lengths_match(self):
        out = run_groundwater_bucket(GroundwaterBucketInput(months=6))
        assert len(out.storage_series_mm) == 6
        assert len(out.baseflow_series_mm) == 6
        assert len(out.recharge_series_mm) == 6
        assert len(out.pumping_series_mm) == 6


class TestPhenology:
    def test_gdd_accumulation(self):
        gdd = _daily_gdd(20.0, 30.0, t_base=10.0)
        assert gdd == pytest.approx(15.0)

    def test_gdd_below_base_is_zero(self):
        gdd = _daily_gdd(5.0, 8.0, t_base=10.0)
        assert gdd == 0.0

    def test_stage_progression_wheat(self):
        pheno = CROP_PHENOLOGY["wheat"]
        # Wheat needs ~120 GDD from sowing to emergence, so 50 GDD is still
        # pre-emergence (the previous expectation contradicted the crop table).
        assert _stage_from_gdd(50.0, pheno) == "pre_emergence"
        assert _stage_from_gdd(400.0, pheno) == "vegetative"
        assert _stage_from_gdd(700.0, pheno) == "flowering"
        assert _stage_from_gdd(800.0, pheno) == "grain_fill"
        assert _stage_from_gdd(1000.0, pheno) == "maturity"

    def test_run_phenology_basic(self):
        # 15/30 C with Tb=10 gives 12.5 GDD/day -> 1250 GDD over 100 days,
        # enough to reach wheat flowering (650) and maturity (950). The old
        # 10/20 C series only accumulated 500 GDD and could never flower.
        tmin = [15.0] * 100
        tmax = [30.0] * 100
        out = run_phenology(PhenologyInput(crop="wheat", tmin_daily=tmin, tmax_daily=tmax))
        assert out.current_stage in (
            "emergence",
            "vegetative",
            "flowering",
            "grain_fill",
            "maturity",
        )
        assert len(out.gdd_series) == 100
        assert out.days_to_flowering > 0
        assert out.days_to_maturity > 0

    def test_run_phenology_unknown_crop_uses_default(self):
        tmin = [12.0] * 50
        tmax = [24.0] * 50
        out = run_phenology(PhenologyInput(crop="quinoa", tmin_daily=tmin, tmax_daily=tmax))
        assert out.crop == "quinoa"
        assert len(out.gdd_series) == 50

    def test_outputs_have_honest_provenance(self):
        out = run_phenology(PhenologyInput())
        assert out.data_source == "simulated"
        assert "GDD" in out.model
