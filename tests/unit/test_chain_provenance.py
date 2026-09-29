"""Regression tests for the simulation chain's provenance integrity.

Two of the six chain steps were fabricated while presenting the output contract
of a real implementation:

* ``_run_rothc`` returned ``soc_after = soc_before * 0.95`` -- carbon always
  decayed by exactly 5% per year regardless of climate, clay or residue -- while
  advertising ``model="RothC (in-house port, pending reference validation)"``,
  a label pointing at the real, validated port that was never called.
* ``_run_swat_plus`` returned seven constant arrays and carried **no** provenance
  label at all, so the invented hydrology was indistinguishable from a real run.

These tests pin the real implementations and the explicit "not computed" result
that replaces fabrication.
"""

from __future__ import annotations

import pytest

from engine.hydroma.simulation.contracts import (
    ChainInputs,
    MonthClimate,
    RothCInput,
    ScenarioParams,
    SWATInput,
)
from engine.hydroma.simulation.orchestrator import _run_rothc, _run_swat_plus, run_chain


def _monthly() -> list[MonthClimate]:
    return [
        MonthClimate(year=2020, month=m, tmean_c=14.0, smd_mm=20.0, max_smd_mm=60.0)
        for m in range(1, 13)
    ]


def _rothc_input(clay: float = 27.0) -> RothCInput:
    return RothCInput(
        land_profile_id="site-1",
        soil_organic_carbon_t_ha=40.0,
        crop_residues_t_ha=2.0,
        temperature_data=[14.0] * 12,
        rainfall_data=[20.0] * 12,
        clay_content_percent=clay,
    )


# --------------------------------------------------------------------------
# RothC must be the real monthly loop
# --------------------------------------------------------------------------


def test_rothc_is_not_the_five_percent_fudge():
    """The old implementation returned soc_after == soc_before * 0.95 always."""
    monthly = _monthly()
    out = _run_rothc(_rothc_input(), monthly, years=1)

    assert out["soc_after_t_ha"] != pytest.approx(40.0 * 0.95, rel=1e-9), (
        "RothC still returns the 0.95 fudge instead of the real monthly loop"
    )


def test_rothc_responds_to_clay_content():
    """A real RothC partitions carbon by clay; a fudge cannot."""
    monthly = _monthly()
    low_clay = _run_rothc(_rothc_input(clay=8.0), monthly, years=5)
    high_clay = _run_rothc(_rothc_input(clay=45.0), monthly, years=5)

    assert low_clay["soc_after_t_ha"] != pytest.approx(high_clay["soc_after_t_ha"])


def test_rothc_responds_to_climate():
    """Respiration must depend on the temperature modifier."""
    cold = [MonthClimate(year=2020, month=m, tmean_c=2.0, smd_mm=20.0, max_smd_mm=60.0) for m in range(1, 13)]
    warm = [MonthClimate(year=2020, month=m, tmean_c=26.0, smd_mm=20.0, max_smd_mm=60.0) for m in range(1, 13)]

    cold_out = _run_rothc(_rothc_input(), cold, years=3)
    warm_out = _run_rothc(_rothc_input(), warm, years=3)

    assert cold_out["co2_respired_t_ha"] < warm_out["co2_respired_t_ha"]


def test_rothc_reports_stabilisation_fraction_from_clay():
    out = _run_rothc(_rothc_input(clay=20.0), _monthly(), years=1)

    assert 0.0 < out["stabilized_fraction"] < 0.5
    assert out["co2_fraction"] > out["stabilized_fraction"]


def test_rothc_carries_truthful_provenance():
    out = _run_rothc(_rothc_input(), _monthly(), years=1)

    assert out["data_source"] == "simulated"
    assert "RothC-26.3" in out["model"]
    assert out["final_pools_t_ha"] is not None
    assert set(out["final_pools_t_ha"]) == {"DPM", "RPM", "BIO", "HUM"}


def test_rothc_soc_change_is_annualised():
    """A 3-year run must report a per-year delta, not a cumulative one."""
    out = _run_rothc(_rothc_input(), _monthly(), years=3)
    cumulative = out["soc_after_t_ha"] - out["soc_before_t_ha"]

    assert out["soc_change_t_ha_yr"] == pytest.approx(cumulative / 3.0, rel=1e-3)


# --------------------------------------------------------------------------
# SWAT+ must not fabricate
# --------------------------------------------------------------------------


def test_swat_plus_returns_none_when_binary_absent(monkeypatch):
    """No binary, no numbers: the chain must be able to say so."""
    monkeypatch.delenv("SWAT_EXECUTABLE", raising=False)
    monkeypatch.delenv("SWAT_PROJECT_DIR", raising=False)

    out = _run_swat_plus(
        SWATInput(
            land_profile_id="site-1",
            start_date=__import__("datetime").date(2023, 1, 1),
            end_date=__import__("datetime").date(2023, 12, 31),
        )
    )

    assert out is None, "SWAT+ fabricated a result instead of reporting unavailability"


# --------------------------------------------------------------------------
# The chain marks dependent steps as not computed
# --------------------------------------------------------------------------


def _chain_inputs() -> ChainInputs:
    return ChainInputs(
        site_id="site-1",
        area_ha=10.0,
        scenario=ScenarioParams(
            name="Baseline",
            cn_change=0.0,
            c_factor_factor=1.0,
            p_factor=1.0,
        ),
        r_factor=100.0,
        k_factor=0.3,
        ls_factor=1.0,
        c_factor_base=0.3,
        initial_soc_t_ha=40.0,
        clay_pct=27.0,
    )


def test_chain_marks_swat_dependent_steps_not_computed(monkeypatch):
    """WEAP and HEC-RAS consume SWAT+ output and must not report numbers."""
    monkeypatch.delenv("SWAT_EXECUTABLE", raising=False)
    monkeypatch.delenv("SWAT_PROJECT_DIR", raising=False)

    result = run_chain(_chain_inputs())

    assert result.status in ("ok", "partial")
    assert result.outputs["swat_plus"]["status"] == "not_computed"
    assert result.outputs["swat_plus"]["data_source"] == "unavailable"
    assert result.outputs["weap"]["status"] == "not_computed"
    assert result.outputs["hecras"]["status"] == "not_computed"


def test_chain_still_computes_independent_steps(monkeypatch):
    """RUSLE, RothC and AquaCrop do not depend on SWAT+ and must still run."""
    monkeypatch.delenv("SWAT_EXECUTABLE", raising=False)
    monkeypatch.delenv("SWAT_PROJECT_DIR", raising=False)

    result = run_chain(_chain_inputs())

    assert result.outputs["rusle"]["erosion_before_t_ha"] > 0
    assert result.outputs["rothc"]["data_source"] == "simulated"
    assert result.outputs["aquacrop"]["data_source"] == "simulated"


def test_every_chain_step_declares_provenance(monkeypatch):
    """No step may return numbers without saying where they came from."""
    monkeypatch.delenv("SWAT_EXECUTABLE", raising=False)
    monkeypatch.delenv("SWAT_PROJECT_DIR", raising=False)

    result = run_chain(_chain_inputs())

    for step, payload in result.outputs.items():
        assert isinstance(payload, dict), f"{step} is not a dict"
        assert "data_source" in payload, f"{step} has no data_source tag"
