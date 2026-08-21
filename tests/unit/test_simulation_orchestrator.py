"""Tests for the simulation chain orchestrator + contracts (Phase 3, sprint 1)."""

import pytest
from pydantic import ValidationError

from engine.hydroma.simulation.contracts import ChainInputs
from engine.hydroma.simulation.orchestrator import run_chain
from engine.hydroma.simulation.scenarios import SCENARIOS


def _inputs(**overrides) -> ChainInputs:
    base = dict(
        site_id="sim-test-1",
        area_ha=10.0,
        scenario=SCENARIOS["Medium"],
        r_factor=1200.0,
        k_factor=0.04,
        ls_factor=2.0,
        c_factor_base=0.30,
        initial_soc_t_ha=55.0,
        clay_pct=20.0,
    )
    base.update(overrides)
    return ChainInputs(**base)


class TestContracts:
    def test_scenario_matrix_complete(self):
        assert set(SCENARIOS) == {"Baseline", "Medium", "Intensive"}
        assert SCENARIOS["Medium"].cn_change == -8.0
        assert SCENARIOS["Intensive"].c_factor_factor == 0.70

    def test_validation_errors(self):
        with pytest.raises(ValidationError):
            _inputs(area_ha=-5.0)
        with pytest.raises(ValidationError):
            _inputs(initial_soc_t_ha=0.0)


class TestChain:
    def test_full_chain_runs(self):
        result = run_chain(_inputs())
        assert result.status in ("ok", "partial")
        assert result.scenario == "Medium"
        assert "rusle" in result.outputs
        assert "aquacrop" in result.outputs
        assert "rothc" in result.outputs

    def test_rusle_reduction_matches_factors(self):
        result = run_chain(_inputs())
        rusle = result.outputs["rusle"]
        if "error" not in rusle:
            # Medium: C * 0.85, P * 0.50 -> after/before = 0.425
            assert rusle["erosion_after_t_ha"] == pytest.approx(
                rusle["erosion_before_t_ha"] * 0.425, rel=1e-6
            )
            assert 50.0 < rusle["reduction_pct"] < 70.0

    def test_outputs_have_honest_provenance(self):
        result = run_chain(_inputs())
        for key in ("rusle", "aquacrop", "rothc"):
            out = result.outputs[key]
            assert out.get("data_source") == "simulated", key
            assert "model" in out, key

    def test_rothc_soc_plausible(self):
        result = run_chain(_inputs())
        rothc = result.outputs["rothc"]
        if "error" not in rothc:
            assert abs(rothc["soc_change_t_ha_yr"]) < rothc["soc_before_t_ha"]
            assert rothc["co2e_t_ha"] == pytest.approx(rothc["soc_change_t_ha_yr"] * 3.67, abs=0.01)

    def test_baseline_no_erosion_reduction(self):
        result = run_chain(_inputs(scenario=SCENARIOS["Baseline"]))
        rusle = result.outputs["rusle"]
        if "error" not in rusle:
            assert rusle["reduction_pct"] == pytest.approx(0.0, abs=1e-9)

    def test_real_weather_used_when_requested(self, monkeypatch):
        from engine.hydroma.simulation import weather_source
        from engine.hydroma.simulation.runners.aquacrop_runner import synthetic_weather

        calls = {}

        def fake_fetch(lat, lon, start, end, session=None):
            calls["args"] = (lat, lon, start, end)
            return synthetic_weather("2020/03/01", "2020/08/04")

        monkeypatch.setattr(weather_source, "fetch_daily_weather", fake_fetch)
        result = run_chain(_inputs(lat=36.5, lon=54.0, use_real_weather=True))
        aquacrop = result.outputs["aquacrop"]
        assert aquacrop.get("weather_source") == "open-meteo (real)"
        assert calls["args"][0] == 36.5
        assert calls["args"][2].startswith("2020-03-01")

    def test_real_weather_failure_falls_back_honestly(self, monkeypatch):
        from engine.hydroma.simulation import weather_source

        def boom(*args, **kwargs):
            raise weather_source.WeatherUnavailable("network down")

        monkeypatch.setattr(weather_source, "fetch_daily_weather", boom)
        result = run_chain(_inputs(lat=36.5, lon=54.0, use_real_weather=True))
        aquacrop = result.outputs["aquacrop"]
        assert result.status == "partial"
        assert aquacrop.get("weather_source") == "synthetic (fallback)"
        assert "weather_error" in aquacrop
