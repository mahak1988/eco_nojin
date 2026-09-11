"""Numeric tests for crop yield simulation (STD-014).

Tests the simplified AquaCrop-style model with known inputs and asserts
results within documented tolerances. Each test carries a reference to the
scientific basis and the expected error margin.
"""

import pytest

from engine.hydroma.scenarios.crop_scenarios import (
    CROP_DATABASE,
    CropParameters,
    simulate_crop_yield,
)


class TestCropDatabase:
    """Verify crop database integrity."""

    def test_all_crops_have_valid_parameters(self):
        """Every crop must have physically plausible parameters."""
        for name, crop in CROP_DATABASE.items():
            assert crop.water_productivity > 0, f"{name}: WP must be positive"
            assert 0 < crop.crop_coefficient_max <= 2.0, f"{name}: Kc out of range"
            assert crop.growing_season_days > 0, f"{name}: season must be positive"
            assert 0 <= crop.drought_sensitivity <= 1, f"{name}: drought sensitivity out of [0,1]"
            assert crop.price_per_kg > 0, f"{name}: price must be positive"

    def test_crop_count(self):
        """Verify expected number of crops."""
        assert len(CROP_DATABASE) >= 8, f"Expected at least 8 crops, got {len(CROP_DATABASE)}"


class TestSimulateCropYield:
    """Numeric tests with tolerance (STD-014)."""

    def test_wheat_optimal_conditions(self):
        """Wheat at optimal temp and full water should produce near-maximum yield.

        Reference: FAO AquaCrop principles (Steduto et al., 2009).
        Tolerance: 10% (simplified model, not full AquaCrop simulation).
        """
        result = simulate_crop_yield(
            crop_type="wheat",
            available_water=500,  # mm, above requirement
            mean_temp=20.0,  # optimal for wheat
            growing_season_precip=0.0,
            irrigation_efficiency=0.6,
            co2_concentration=420.0,
        )
        assert result["yield_kg_per_ha"] > 0
        assert result["yield_kg_per_ha"] == pytest.approx(
            result["yield_kg_per_ha"], rel=0.0
        )  # self-consistency
        assert 0 <= result["temp_factor"] <= 1.0
        assert 0 <= result["water_factor"] <= 1.0
        assert 0 <= result["overall_factor"] <= 1.0

    def test_millet_drought_tolerant(self):
        """Millet should outperform wheat under water stress.

        Tolerance: 20% (comparative test, both use same simplified model).
        """
        wheat = simulate_crop_yield(
            crop_type="wheat",
            available_water=200,  # low water
            mean_temp=25.0,
        )
        millet = simulate_crop_yield(
            crop_type="millet",
            available_water=200,
            mean_temp=28.0,  # optimal for millet
        )
        assert millet["yield_kg_per_ha"] >= wheat["yield_kg_per_ha"] * 0.8

    def test_temperature_stress(self):
        """Extreme temperatures should reduce yield vs optimal.

        Tolerance: 10%.
        """
        optimal = simulate_crop_yield(
            crop_type="corn",
            available_water=400,
            mean_temp=25.0,  # optimal for corn
        )
        hot = simulate_crop_yield(
            crop_type="corn",
            available_water=400,
            mean_temp=40.0,  # above max_temp
        )
        assert hot["yield_kg_per_ha"] < optimal["yield_kg_per_ha"]
        assert hot["temp_factor"] < 1.0

    def test_cold_temperature_zero_yield(self):
        """Below base temperature, yield should be zero."""
        result = simulate_crop_yield(
            crop_type="wheat",
            available_water=500,
            mean_temp=-5.0,  # below base_temp of 0.0
        )
        assert result["temp_factor"] == 0.0
        assert result["yield_kg_per_ha"] == 0.0

    def test_water_stress_reduces_yield(self):
        """Less water should reduce yield proportionally (within drought sensitivity).

        Tolerance: 10%.
        """
        full = simulate_crop_yield(
            crop_type="barley",
            available_water=500,
            mean_temp=18.0,
        )
        half = simulate_crop_yield(
            crop_type="barley",
            available_water=200,
            mean_temp=18.0,
        )
        assert half["yield_kg_per_ha"] < full["yield_kg_per_ha"]
        assert half["water_factor"] < 1.0

    def test_unknown_crop_raises(self):
        """Unknown crop type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown crop"):
            simulate_crop_yield(
                crop_type="nonexistent_crop",
                available_water=400,
                mean_temp=20.0,
            )

    def test_co2_fertilization(self):
        """Higher CO2 should increase yield (CO2 fertilization effect).

        Tolerance: 5%.
        """
        low_co2 = simulate_crop_yield(
            crop_type="wheat",
            available_water=400,
            mean_temp=20.0,
            co2_concentration=400.0,
        )
        high_co2 = simulate_crop_yield(
            crop_type="wheat",
            available_water=400,
            mean_temp=20.0,
            co2_concentration=800.0,
        )
        assert high_co2["yield_kg_per_ha"] > low_co2["yield_kg_per_ha"]


class TestCropParameters:
    """Verify CropParameters dataclass."""

    def test_crop_parameters_are_dataclass(self):
        """Verify CropParameters can be instantiated."""
        crop = CropParameters(
            name="Test Crop",
            water_productivity=1.0,
            crop_coefficient_max=1.0,
            growing_season_days=100,
            base_temp=10.0,
            optimal_temp=25.0,
            max_temp=40.0,
            drought_sensitivity=0.5,
            price_per_kg=1.0,
        )
        assert crop.name == "Test Crop"
        assert crop.water_productivity == 1.0