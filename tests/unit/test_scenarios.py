"""Tests for Scenario Engine."""

from engine.hydroma.scenarios.climate_scenarios import (
    CLIMATE_PROJECTIONS,
    apply_climate_change,
    compare_scenarios,
    get_climate_projection,
)
from engine.hydroma.scenarios.crop_scenarios import (
    CROP_DATABASE,
    compare_crops,
    simulate_crop_yield,
)
from engine.hydroma.scenarios.monte_carlo import monte_carlo_climate, monte_carlo_yield
from engine.hydroma.scenarios.whatif_engine import (
    Scenario,
    generate_climate_transition_scenarios,
    run_whatif_analysis,
)


class TestClimateScenarios:
    """Tests for climate scenario projections."""

    def test_valid_scenarios_exist(self):
        """Verify all three SSP scenarios are defined."""
        assert "SSP1-2.6" in CLIMATE_PROJECTIONS
        assert "SSP2-4.5" in CLIMATE_PROJECTIONS
        assert "SSP5-8.5" in CLIMATE_PROJECTIONS

    def test_projection_warming_increases_with_scenario(self):
        """Verify warming increases from SSP1 to SSP5."""
        p1 = get_climate_projection("SSP1-2.6", 2050)
        p2 = get_climate_projection("SSP2-4.5", 2050)
        p5 = get_climate_projection("SSP5-8.5", 2050)

        assert p1.delta_temp < p2.delta_temp < p5.delta_temp

    def test_projection_drying_increases_with_scenario(self):
        """Verify drying increases from SSP1 to SSP5."""
        p1 = get_climate_projection("SSP1-2.6", 2050)
        p2 = get_climate_projection("SSP2-4.5", 2050)
        p5 = get_climate_projection("SSP5-8.5", 2050)

        # More negative = more drying
        assert p1.delta_precip > p2.delta_precip > p5.delta_precip

    def test_projection_confidence_decreases_with_time(self):
        """Verify confidence decreases for longer horizons."""
        p_2030 = get_climate_projection("SSP2-4.5", 2030)
        p_2100 = get_climate_projection("SSP2-4.5", 2100)

        confidence_order = {"high": 0, "medium": 1, "low": 2}
        assert confidence_order[p_2030.confidence] <= confidence_order[p_2100.confidence]

    def test_compare_scenarios_returns_all(self):
        """Verify compare_scenarios returns all three scenarios."""
        results = compare_scenarios(2050)
        assert len(results) == 3
        assert "SSP1-2.6" in results
        assert "SSP2-4.5" in results
        assert "SSP5-8.5" in results

    def test_apply_climate_change(self):
        """Verify climate change application."""
        projection = get_climate_projection("SSP2-4.5", 2050)
        result = apply_climate_change(18.0, 300.0, 1500.0, projection)

        assert result["temperature"] > 18.0  # Warmer
        assert result["precipitation"] < 300.0  # Drier


class TestCropScenarios:
    """Tests for crop yield simulation."""

    def test_crop_database_populated(self):
        """Verify crop database has expected crops."""
        assert "wheat" in CROP_DATABASE
        assert "millet" in CROP_DATABASE
        assert "medicinal_herbs" in CROP_DATABASE

    def test_yield_increases_with_water(self):
        """Verify yield increases with more water (up to a point)."""
        yield_low = simulate_crop_yield("wheat", 200, 20.0)
        yield_high = simulate_crop_yield("wheat", 500, 20.0)

        assert yield_high["actual_yield_kg_ha"] > yield_low["actual_yield_kg_ha"]

    def test_drought_tolerance_ranking(self):
        """Verify millet is more drought tolerant than wheat."""
        millet = simulate_crop_yield("millet", 150, 25.0)
        wheat = simulate_crop_yield("wheat", 150, 25.0)

        # Millet should have higher water stress factor under drought
        assert millet["water_stress_factor"] > wheat["water_stress_factor"]

    def test_co2_fertilization_effect(self):
        """Verify elevated CO2 increases yield."""
        yield_400 = simulate_crop_yield("wheat", 400, 20.0, co2_concentration=400)
        yield_600 = simulate_crop_yield("wheat", 400, 20.0, co2_concentration=600)

        assert yield_600["co2_fertilization"] > yield_400["co2_fertilization"]

    def test_compare_crops_returns_ranking(self):
        """Verify crop comparison returns valid ranking."""
        result = compare_crops(300, 22.0)

        assert "ranking" in result
        assert len(result["ranking"]) > 0
        assert result["best_economic_choice"] is not None


class TestWhatIfEngine:
    """Tests for what-if analysis."""

    def test_run_whatif_analysis(self):
        """Verify what-if analysis compares scenarios."""
        scenarios = [
            Scenario("Current", "wheat", 300, 20.0),
            Scenario("Drought", "wheat", 200, 22.0),
            Scenario("Adapted", "millet", 200, 22.0),
        ]

        result = run_whatif_analysis(scenarios)

        assert result["n_scenarios"] == 3
        assert result["best_yield"] is not None
        assert result["best_revenue"] is not None

    def test_adapted_crop_performs_better_under_drought(self):
        """Verify drought-tolerant crop performs better in drought scenario."""
        scenarios = [
            Scenario("Wheat_Drought", "wheat", 150, 25.0),
            Scenario("Millet_Drought", "millet", 150, 25.0),
        ]

        result = run_whatif_analysis(scenarios)

        # Find yields for each scenario
        wheat_yield = next(s for s in result["scenarios"] if s["scenario_name"] == "Wheat_Drought")
        millet_yield = next(
            s for s in result["scenarios"] if s["scenario_name"] == "Millet_Drought"
        )

        assert millet_yield["yield_kg_ha"] > wheat_yield["yield_kg_ha"]

    def test_climate_transition_scenarios(self):
        """Verify climate transition generates multiple scenarios."""
        result = generate_climate_transition_scenarios(
            baseline_water=300,
            baseline_temp=18.0,
            crop_type="wheat",
            ssp_scenario="SSP2-4.5",
        )

        assert result["n_scenarios"] == 3  # 2030, 2050, 2100


class TestMonteCarlo:
    """Tests for Monte Carlo uncertainty analysis."""

    def test_monte_carlo_yield_returns_statistics(self):
        """Verify Monte Carlo returns valid statistics."""
        result = monte_carlo_yield(
            crop_type="wheat",
            mean_water=300,
            water_std=50,
            mean_temp=20,
            temp_std=2,
            n_simulations=100,
            seed=42,
        )

        assert result["n_successful"] > 50
        assert result["mean_yield_kg_ha"] > 0
        assert result["std_yield_kg_ha"] >= 0
        assert result["percentile_5"] <= result["percentile_50"] <= result["percentile_95"]

    def test_monte_carlo_yield_reproducible(self):
        """Verify Monte Carlo is reproducible with seed."""
        result1 = monte_carlo_yield("wheat", 300, 50, 20, 2, n_simulations=50, seed=123)
        result2 = monte_carlo_yield("wheat", 300, 50, 20, 2, n_simulations=50, seed=123)

        assert result1["mean_yield_kg_ha"] == result2["mean_yield_kg_ha"]

    def test_monte_carlo_climate(self):
        """Verify climate Monte Carlo returns valid projections."""
        result = monte_carlo_climate(
            baseline_temp=18.0,
            baseline_precip=300.0,
            ssp_scenario="SSP2-4.5",
            time_horizon=2050,
            n_simulations=100,
            seed=42,
        )

        assert result["temp_mean"] > 18.0  # Warming expected
        assert result["probability_drying"] > 0  # Some drying expected
        assert len(result["temp_range"]) == 2
        assert len(result["precip_range"]) == 2
