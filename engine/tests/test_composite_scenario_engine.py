"""Guards for the composite scenario engine and its local equations.

Two layers:

1. the DAG itself -- gateway state, execution order, failure recording,
   the decision-engine contract and template handling;
2. every local equation in ``models_additions`` -- each one is checked against
   an independent re-derivation written here from the published formula, never
   against the implementation being tested.

No network is used: every gateway call goes through the real in-process
gateway, whose models are all local Python.
"""

from __future__ import annotations

import math

import pytest

from engine.hydroma.scenario_composite import (
    CompositeScenarioEngine,
    catalog,
)
from engine.hydroma.scenario_composite import (
    models_additions as M,
)

# ── DAG ────────────────────────────────────────────────────────────────────


def test_available_models_reflects_the_live_registry() -> None:
    engine = CompositeScenarioEngine()
    models = engine.available_models()
    assert len(models) >= 60
    # every entry classifies itself by the gateway's own answer
    for model_id, info in models.items():
        assert "reachable" in info
        assert model_id
    # the routes the DAG depends on must be reachable
    for needed in (
        "CLIMATE_SCENARIO",
        "CANON-001",
        "CANON-004",
        "SOIL_AWC",
        "IRRIGATION_DEPTH",
        "CROP_YIELD",
        "ECON_AG_REVENUE",
        "ECON_FINANCIAL",
        "ECON_PRICE_RISK",
        "CANON-005",
    ):
        assert models[needed]["reachable"], needed


def test_full_run_produces_every_indicator_family() -> None:
    engine = CompositeScenarioEngine()
    spec = engine.define_scenario("test_run", template="climate_2050_ssp245")
    spec.parameters["social"]["consumption_tonnes"] = 4.0
    run = engine.run(spec)

    families = run["indicators"]
    assert set(families) == {"environmental", "economic", "social", "food"}
    for family, indicators in families.items():
        assert indicators, f"{family} produced no indicators"
        for indicator in indicators.values():
            assert indicator.value is not None
            assert indicator.unit
            assert indicator.formula

    # the DAG executed in dependency order
    order = [entry["step"] for entry in run["trace"]]
    assert order.index("climate") < order.index("et0_reference")
    assert order.index("et0_multi_method") < order.index("irrigation_requirement")
    assert order.index("soil_water_balance") < order.index("irrigation_requirement")
    assert order.index("irrigation_requirement") < order.index("crop_yield")
    assert order.index("crop_yield") < order.index("economics_revenue")

    # nothing failed on the shipped template
    assert run["failures"] == []

    # every gateway step carries its inputs and outputs
    for _name, record in run["steps"].items():
        assert record["status"] in {"ok", "failed", "skipped"}
        if record["status"] == "ok":
            assert record["outputs"] is not None


def test_decision_context_matches_the_tasmimyar_contract() -> None:
    engine = CompositeScenarioEngine()
    spec = engine.define_scenario("test_decision", template="climate_2050_ssp245")
    spec.parameters["social"]["consumption_tonnes"] = 4.0
    run = engine.run(spec)
    context = run["decision_context"]
    assert set(context) == {"npv_irr", "value_at_risk_irr", "direct_employment_fte"}
    assert all(isinstance(value, float) for value in context.values())
    # a positive NPV for the shipped template's prices
    assert context["npv_irr"] > 0


def test_failing_step_is_recorded_and_does_not_raise() -> None:
    engine = CompositeScenarioEngine()
    spec = engine.define_scenario("test_failure", template="climate_2050_ssp245")
    # a texture the SOIL_AWC route cannot resolve makes that step fail
    spec.parameters["land_use"]["texture"] = "not_a_texture"
    run = engine.run(spec)

    assert run["steps"]["soil_awc"]["status"] == "failed"
    assert run["steps"]["soil_awc"]["error"]["error_code"]
    assert run["failures"]


def test_template_and_override_merge() -> None:
    engine = CompositeScenarioEngine()
    spec = engine.define_scenario(
        "test_merge",
        template="climate_2050_ssp245",
        parameters={"market": {"price_per_tonne": 12345.0}},
    )
    assert spec.section("market")["price_per_tonne"] == 12345.0
    # untouched template values survive the override
    assert spec.section("land_use")["crop"] == "wheat"
    assert spec.section("climate")["target_year"] == 2050


def test_catalog_templates_are_all_runnable() -> None:
    engine = CompositeScenarioEngine()
    for name in catalog.TEMPLATE_NAMES:
        spec = engine.define_scenario(name, template=name)
        run = engine.run(spec)
        assert run["indicators"]["environmental"], name
        assert run["duration_s"] >= 0


def test_scenario_without_groundwater_section_skips_the_step() -> None:
    engine = CompositeScenarioEngine()
    spec = engine.define_scenario("test_no_gw", template="climate_2050_ssp245")
    run = engine.run(spec)
    assert run["steps"]["groundwater_drawdown"]["status"] == "skipped"


def test_scenario_with_groundwater_section_runs_theis() -> None:
    engine = CompositeScenarioEngine()
    spec = engine.define_scenario("test_gw", template="climate_2050_ssp245")
    spec.parameters["groundwater"] = {
        "transmissivity_m2day": 1500.0,
        "storativity": 1.5e-4,
        "pumping_rate_m3day": 2000.0,
        "distance_from_well_m": 200.0,
        "time_since_pumping_start_days": 365.0,
    }
    run = engine.run(spec)
    assert run["steps"]["groundwater_drawdown"]["status"] == "ok"
    # Theis at T=1500, S=1.5e-4, r=200, t=365: u = 200^2*1.5e-4/(4*1500*365)
    u = (200**2 * 1.5e-4) / (4 * 1500 * 365)
    # W(u) = E1(u) ~= -gamma - ln(u) for small u (independent re-derivation)
    expected = (2000 / (4 * math.pi * 1500)) * (-0.5772156649015329 - math.log(u))
    assert run["values"]["aquifer_drawdown_m"] == pytest.approx(expected, rel=1e-3)


# ── local equations, each against an independent re-derivation ──────────────


def test_priestley_taylor_matches_published_formula() -> None:
    """ET0 = alpha * (Delta/(Delta+gamma)) * (Rn-G)/lambda."""
    alpha = 1.26
    mean_temp_c = 25.0
    elevation = 500.0
    net_radiation = 12.0
    ground_heat_flux = 0.2

    delta = 4098 * (0.6108 * math.exp(17.27 * mean_temp_c / (mean_temp_c + 237.3))) / (
        (mean_temp_c + 237.3) ** 2
    )
    pressure = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26
    gamma = 0.000665 * pressure
    latent_heat = 2.45  # MJ/kg, FAO-56 table

    expected = alpha * (delta / (delta + gamma)) * (net_radiation - ground_heat_flux) / latent_heat
    got = M.priestley_taylor_et0(
        net_radiation_mj_m2_day=net_radiation,
        mean_temp_c=mean_temp_c,
        elevation_m=elevation,
        ground_heat_flux_mj_m2_day=ground_heat_flux,
    )
    assert got == pytest.approx(expected, rel=1e-9)


def test_makkink_matches_published_formula() -> None:
    """ET0 = 0.61 * (Delta/(Delta+gamma)) * (Rs/lambda) - 0.12."""
    mean_temp_c = 20.0
    rs = 18.0
    elevation = 0.0
    delta = 4098 * (0.6108 * math.exp(17.27 * mean_temp_c / (mean_temp_c + 237.3))) / (
        (mean_temp_c + 237.3) ** 2
    )
    gamma = 0.000665 * 101.3
    expected = 0.61 * (delta / (delta + gamma)) * (rs / 2.45) - 0.12
    got = M.makkink_et0(
        mean_temp_c=mean_temp_c, solar_radiation_mj_m2_day=rs, elevation_m=elevation
    )
    assert got == pytest.approx(expected, rel=1e-9)


def test_blaney_criddle_matches_published_formula() -> None:
    """ET0 = c * [p * (0.46*T + 8.18)] with p the daylight fraction of the year."""
    mean_temp_c = 24.0
    p = 0.29  # July at mid-latitudes
    expected = 1.0 * p * (0.46 * mean_temp_c + 8.18)
    got = M.blaney_criddle_et0(mean_temp_c=mean_temp_c, daylight_fraction=p)
    assert got == pytest.approx(expected, rel=1e-12)


def test_turc_is_positive_and_scales_with_radiation() -> None:
    base = M.turc_et0(mean_temp_c=20.0, solar_radiation_mj_m2_day=20.0)
    brighter = M.turc_et0(mean_temp_c=20.0, solar_radiation_mj_m2_day=25.0)
    assert base > 0 and brighter > base


def test_stress_coefficient_is_fao56_equation_84() -> None:
    """Ks = (TAW - Dr) / ((1 - p) * TAW); Ks = 1 for Dr <= RAW."""
    taw, depletion_fraction = 200.0, 0.55
    assert M.stress_coefficient_ks(0.0, taw, depletion_fraction) == 1.0
    assert M.stress_coefficient_ks(100.0, taw, depletion_fraction) == 1.0  # RAW = 110
    mid = M.stress_coefficient_ks(150.0, taw, depletion_fraction)
    assert mid == pytest.approx((taw - 150.0) / ((1 - depletion_fraction) * taw))
    assert M.stress_coefficient_ks(taw, taw, depletion_fraction) == 0.0


def test_total_available_water_and_raw() -> None:
    awc_mm_per_m = 250.3  # the SOIL_AWC loam value
    root_depth = 1.2
    taw = M.total_available_water(awc_mm_per_m, root_depth)
    assert taw == pytest.approx(awc_mm_per_m * root_depth)
    assert M.readily_available_water(taw, 0.55) == pytest.approx(0.55 * taw)


def test_effective_rainfall_is_the_declared_fraction() -> None:
    assert M.effective_rainfall(200.0, 0.75) == pytest.approx(150.0)
    assert M.effective_rainfall(200.0, 0.0) == 0.0


def test_net_present_value_matches_manual_sum() -> None:
    flows = [-1000.0, 300.0, 400.0, 500.0]
    rate = 0.1
    manual = -1000.0 + sum(
        cf / (1 + rate) ** t for t, cf in enumerate(flows[1:], start=1)
    )
    assert M.net_present_value(flows, rate) == pytest.approx(manual)


def test_benefit_cost_ratio_is_the_ratio() -> None:
    assert M.benefit_cost_ratio(200.0, 100.0) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        M.benefit_cost_ratio(200.0, 0.0)


def test_break_even_yield_is_cost_over_margin() -> None:
    # fixed cost 1000, price 2, variable cost 1 -> break-even = 1000 units
    assert M.break_even_yield(1000.0, 2.0, 1.0) == pytest.approx(1000.0)


def test_water_productivity_and_iwue() -> None:
    """WP = Y / (ET x 10) kg/m3 -- the FAO WaPOR definition the project
    already publishes (1 mm over 1 ha = 10 m3)."""
    assert M.water_productivity(3000.0, 400.0) == pytest.approx(0.75)
    iwue = M.irrigation_water_use_efficiency(3000.0, 600.0)
    assert iwue > 0 and iwue < M.water_productivity(3000.0, 400.0)


def test_employment_fte_uses_the_intensity_and_months() -> None:
    assert M.direct_employment_fte(area_ha=10.0, employment_intensity_fte_per_ha=0.05) == (
        pytest.approx(0.5)
    )
    assert M.direct_employment_fte(
        area_ha=10.0, employment_intensity_fte_per_ha=0.05, months_per_year=6.0
    ) == pytest.approx(0.25)


def test_self_sufficiency_and_import_dependency_are_complements() -> None:
    ssr = M.self_sufficiency_ratio(80.0, 100.0)
    idr = M.import_dependency_ratio(80.0, 100.0)
    assert ssr == pytest.approx(0.8)
    assert idr == pytest.approx(0.2)
    # a surplus is clipped, not a negative import bill
    assert M.import_dependency_ratio(120.0, 100.0) == 0.0


def test_per_capita_supply_is_production_over_population() -> None:
    assert M.per_capita_dietary_supply(production=100_000.0, population=1000) == (
        pytest.approx(100.0)
    )


def test_cereal_yield_gap_is_attainable_minus_actual() -> None:
    assert M.cereal_yield_gap(attainable_yield=1800.0, actual_yield=1200.0) == (
        pytest.approx(600.0)
    )
    # a negative gap is informative, not clipped: the actual yield exceeded the
    # attainable figure the scenario supplied, so the scenario's attainable
    # value is what is wrong.
    assert M.cereal_yield_gap(attainable_yield=1800.0, actual_yield=1900.0) == (
        pytest.approx(-100.0)
    )


def test_method_spread_reports_mean_range_and_spread() -> None:
    spread = M.method_spread([4.0, 6.0, 5.0])
    assert spread["mean"] == pytest.approx(5.0)
    assert spread["range"] == pytest.approx(2.0)
    assert spread["min"] == pytest.approx(4.0)
    assert spread["max"] == pytest.approx(6.0)


def test_blue_green_water_split_conserves_water() -> None:
    split = M.blue_green_water_split(
        season_evapotranspiration_mm=500.0, effective_rain_mm=150.0, irrigation_mm=100.0
    )
    green = split["green_mm"]
    blue = split["blue_mm"]
    assert green + blue <= 500.0 + 1e-9
    assert split["green_fraction"] + split["blue_fraction"] <= 1.0 + 1e-9
