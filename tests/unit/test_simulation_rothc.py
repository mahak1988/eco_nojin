"""Unit tests for the in-house RothC port (Phase 3, sprint 1)."""

import numpy as np
import pytest

from engine.hydroma.simulation.contracts import MonthClimate
from engine.hydroma.simulation.runners.rothc_runner import (
    BIO_FRAC,
    HUM_FRAC,
    RATES,
    RESIDUE_SPLIT,
    X_STAB,
    initial_pools,
    run_rothc,
    temp_factor,
    water_factor,
)


def _climate(months=12, tmean=15.0, smd=30.0, max_smd=60.0):
    return [
        MonthClimate(year=2020, month=m % 12 + 1, tmean_c=tmean, smd_mm=smd, max_smd_mm=max_smd)
        for m in range(months)
    ]


class TestRateModifiers:
    def test_temp_factor_bounds(self):
        # RothC's temperature modifier is ~1 at ~10 C (not 25 C)
        assert temp_factor(9.5) == pytest.approx(1.0, abs=0.05)
        assert 0.0 < temp_factor(0.0) < 1.0
        assert temp_factor(40.0) > temp_factor(25.0) > 1.0

    def test_water_factor_at_fc(self):
        assert water_factor(0.0, 60.0) == pytest.approx(1.0)

    def test_water_factor_both_branches(self):
        # below the 0.444*M breakpoint
        w1 = water_factor(10.0, 60.0)
        # above the breakpoint (0.444*60 = 26.64)
        w2 = water_factor(40.0, 60.0)
        assert 0.0 <= w2 < w1 <= 1.0

    def test_water_factor_zero_max_smd(self):
        assert water_factor(5.0, 0.0) == 1.0


class TestRothC:
    def test_initial_pools_sum_to_soc(self):
        soc = 60.0
        pools, iom = initial_pools(soc, 20.0)
        assert iom == pytest.approx(0.049 * soc ** 1.139, abs=1e-6)
        assert sum(pools.values()) + iom == pytest.approx(soc, abs=1e-6)

    def test_mass_balance_without_inputs(self):
        soc = 60.0
        result = run_rothc(initial_soc_t_ha=soc, clay_pct=20.0, monthly=_climate(months=12), years=1)
        total_after = sum(result["pools_t_ha"].values()) + result["iom_t_ha"] + result["co2_respired_t_ha"]
        assert total_after == pytest.approx(soc, abs=0.01)

    def test_soc_decays_without_inputs(self):
        result = run_rothc(initial_soc_t_ha=60.0, clay_pct=20.0, monthly=_climate(months=12), years=1)
        assert result["soc_after_t_ha"] < result["soc_before_t_ha"]
        assert result["co2_respired_t_ha"] > 0.0

    def test_higher_temperature_more_decomposition(self):
        cool = run_rothc(60.0, 20.0, _climate(months=12, tmean=10.0), years=1)
        warm = run_rothc(60.0, 20.0, _climate(months=12, tmean=25.0), years=1)
        assert warm["co2_respired_t_ha"] > cool["co2_respired_t_ha"]

    def test_residue_input_supports_soc(self):
        no_input = run_rothc(40.0, 20.0, _climate(months=12), residue_c_t_ha_per_month=0.0, years=1)
        with_input = run_rothc(40.0, 20.0, _climate(months=12), residue_c_t_ha_per_month=0.8, years=1)
        assert with_input["soc_after_t_ha"] > no_input["soc_after_t_ha"]

    def test_co2e_equals_delta_times_3_67(self):
        result = run_rothc(50.0, 25.0, _climate(months=12), residue_c_t_ha_per_month=0.5, years=1)
        assert result["co2e_t_ha"] == pytest.approx(result["soc_change_t_ha_yr"] * 3.67, abs=0.01)

    def test_empty_climate_rejected(self):
        with pytest.raises(ValueError):
            run_rothc(50.0, 25.0, [])

    def test_multi_year_run(self):
        one = run_rothc(50.0, 25.0, _climate(months=12), residue_c_t_ha_per_month=0.4, years=1)
        two = run_rothc(50.0, 25.0, _climate(months=12), residue_c_t_ha_per_month=0.4, years=2)
        assert two["co2_respired_t_ha"] > one["co2_respired_t_ha"]

    def test_long_run_equilibrium_matches_analytic(self):
        """Structural validation: steady state matches the analytic equilibrium.

        For the monthly-discrete scheme, pool_eq = in_pool / (1 - exp(-k_m))
        with k_m = RATE/12 * T * W * P. Total decomposition at steady state is
        input_m / (1 - X_STAB) because the stabilized fraction recycles into
        BIO/HUM until everything is respired.
        """
        monthly = _climate(months=12)
        r = run_rothc(50.0, 25.0, monthly, residue_c_t_ha_per_month=0.4, years=3000)
        t = temp_factor(15.0)
        w = water_factor(30.0, 60.0)
        p = 0.6
        input_m = 0.4
        total_dec = input_m / (1.0 - X_STAB)
        stabilized = total_dec * X_STAB
        in_c = {
            "DPM": input_m * RESIDUE_SPLIT["DPM"],
            "RPM": input_m * RESIDUE_SPLIT["RPM"],
            "BIO": stabilized * BIO_FRAC,
            "HUM": stabilized * HUM_FRAC,
        }
        for pool, rate in RATES.items():
            k_m = rate / 12.0 * t * w * p
            eq = in_c[pool] / (1.0 - np.exp(-k_m))
            assert r["pools_t_ha"][pool] == pytest.approx(eq, rel=0.02), pool

    def test_long_run_converges_and_mass_balances(self):
        """Structural validation: SOC converges; respired C -> annual input."""
        monthly = _climate(months=12)
        r = run_rothc(50.0, 25.0, monthly, residue_c_t_ha_per_month=0.4, years=3000)
        r_long = run_rothc(50.0, 25.0, monthly, residue_c_t_ha_per_month=0.4, years=10000)
        # converged: SOC identical at both horizons
        assert r["soc_after_t_ha"] == pytest.approx(r_long["soc_after_t_ha"], abs=0.05)
        # steady state: respired C per year ~= annual input (all C eventually respired)
        assert r_long["co2_respired_t_ha"] / 10000 == pytest.approx(0.4 * 12, abs=0.05)
        assert r_long["soc_after_t_ha"] > 0.0
