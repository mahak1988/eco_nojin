"""ECSI reference tests — pin the index to the canonical RothC-26.3 kernel.

Anchor: the Rothamsted Broadbalk steady state recorded in
``engine/hydroma/models/validation/reference_data.py`` (ECSI_VALIDATION).
"""

from __future__ import annotations

import math

import pytest

from engine.hydroma.models.ecsi import ECSI
from engine.hydroma.models.validation.reference_data import ECSI_VALIDATION
from engine.hydroma.simulation.runners.rothc_runner import (
    stabilization_split,
    temp_factor,
)


@pytest.fixture
def ecsi() -> ECSI:
    return ECSI()


class TestRothamstedAnchor:
    """The Broadbalk case must land in the published steady-state band."""

    def test_broadbalk_steady_state(self, ecsi):
        case = ECSI_VALIDATION["rothamsted_broadbalk"]
        lo, hi = case["expected_delta_soc"]
        # RothC-26.3 moisture behaviour needs a soil-moisture deficit: Broadbalk
        # summer SMD is ~40 mm against a ~100 mm maximum deficit.
        result = ecsi.compute(
            initial_soc_t_ha=case["initial_soc_t_ha"],
            carbon_input_t_ha=case["carbon_input_t_ha"],
            t_mean_c=case["t_mean_c"],
            rainfall_mm=case["rainfall_mm"],
            evaporation_mm=case["evaporation_mm"],
            clay_fraction=case["clay_fraction"],
            land_use=case["land_use"],
            smd_mm=40.0,
            max_smd_mm=100.0,
        )
        assert result["moisture_model"] == "rothc_smd_modifier"
        assert lo <= result["delta_soc_t_ha_yr"] <= hi, result["delta_soc_t_ha_yr"]


class TestCanonicalDelegation:
    """ECSI must not re-implement RothC maths (single source of truth)."""

    def test_temperature_factor_is_canonical(self, ecsi):
        for t in (-5.0, 0.0, 10.0, 15.0, 25.0, 40.0):
            assert ecsi.temperature_factor(t) == pytest.approx(temp_factor(t), rel=1e-12)

    def test_partition_comes_from_stabilization_split(self, ecsi):
        for clay_pct in (0.0, 10.0, 23.0, 40.0, 60.0):
            co2, stab = stabilization_split(clay_pct)
            result = ecsi.compute(
                initial_soc_t_ha=40.0,
                carbon_input_t_ha=2.0,
                t_mean_c=10.0,
                rainfall_mm=700.0,
                evaporation_mm=500.0,
                clay_fraction=clay_pct / 100.0,
            )
            assert result["co2_fraction"] == pytest.approx(co2, rel=1e-9)
            assert result["stabilized_fraction"] == pytest.approx(stab, rel=1e-9)

    def test_co2_bio_hum_ratio_matches_published_relation(self, ecsi):
        clay_pct = 23.4
        x_expected = 1.67 * (1.85 + 1.60 * math.exp(-0.0786 * clay_pct))
        assert ecsi.co2_bio_hum_ratio(clay_pct / 100.0) == pytest.approx(x_expected, rel=1e-9)

    def test_stabilized_fraction_is_in_rothc_range(self, ecsi):
        for clay_pct in (0.0, 10.0, 23.0, 40.0, 60.0, 100.0):
            _co2, stab = stabilization_split(clay_pct)
            assert 0.14 <= stab <= 0.25


class TestBehaviour:
    def test_mass_balance_no_input_matches_decay(self, ecsi):
        result = ecsi.compute(
            initial_soc_t_ha=40.0,
            carbon_input_t_ha=0.0,
            t_mean_c=10.0,
            rainfall_mm=700.0,
            evaporation_mm=500.0,
        )
        assert result["delta_soc_t_ha_yr"] < 0.0
        assert result["final_soc_t_ha"] < 40.0

    def test_input_reduces_loss(self, ecsi):
        no_input = ecsi.compute(40.0, 0.0, 10.0, 700.0, 500.0)
        with_input = ecsi.compute(40.0, 4.0, 10.0, 700.0, 500.0)
        assert with_input["delta_soc_t_ha_yr"] > no_input["delta_soc_t_ha_yr"]

    def test_higher_temperature_more_loss(self, ecsi):
        cool = ecsi.compute(40.0, 2.0, 5.0, 700.0, 500.0)
        warm = ecsi.compute(40.0, 2.0, 25.0, 700.0, 500.0)
        assert warm["delta_soc_t_ha_yr"] < cool["delta_soc_t_ha_yr"]

    def test_multi_year_scaling(self, ecsi):
        one = ecsi.compute(40.0, 2.0, 10.0, 700.0, 500.0, dt_years=1.0)
        five = ecsi.compute(40.0, 2.0, 10.0, 700.0, 500.0, dt_years=5.0)
        assert five["final_soc_t_ha"] < one["final_soc_t_ha"]

    def test_proxy_path_is_labelled_when_smd_missing(self, ecsi):
        result = ecsi.compute(40.0, 2.0, 10.0, 700.0, 500.0)
        assert result["moisture_model"] == "rainfall_evaporation_proxy"
        assert "Coleman" in result["kernel"]

    def test_smd_path_approaches_rothc_equilibrium(self, ecsi):
        # Canonical RothC with the Broadbalk modifiers has an equilibrium of
        # ~44.8 tC/ha for a 2 tC/ha/yr input. Year 1 sits just inside the
        # published steady-state band, and over decades SOC must grow towards
        # that equilibrium (40 < 44.8).
        one_year = ecsi.compute(40.0, 2.0, 10.0, 700.0, 500.0, smd_mm=40.0)
        assert abs(one_year["delta_soc_t_ha_yr"]) <= 0.5
        assert one_year["moisture_model"] == "rothc_smd_modifier"
        long_run = ecsi.compute(40.0, 2.0, 10.0, 700.0, 500.0, smd_mm=40.0, dt_years=50.0)
        assert long_run["final_soc_t_ha"] > 40.0
        assert long_run["final_soc_t_ha"] < 50.0

    def test_invalid_clay_rejected(self, ecsi):
        with pytest.raises(ValueError):
            ecsi.compute(40.0, 2.0, 10.0, 700.0, 500.0, clay_fraction=1.5)

    def test_invalid_soc_rejected(self, ecsi):
        with pytest.raises(ValueError):
            ecsi.compute(600.0, 2.0, 10.0, 700.0, 500.0)
