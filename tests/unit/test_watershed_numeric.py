"""Additional numeric tests for watershed calculator (STD-014).

Tests the rational-method runoff model and structure design functions
with known inputs and documented tolerances.
"""

import pytest

from engine.hydroma.watershed.calculator import (
    calculate_runoff,
    design_check_dam,
    design_contour_trench,
    design_half_moon,
    design_watershed_structure,
)


class TestRunoffValidation:
    """Input validation tests for calculate_runoff."""

    def test_negative_area_raises(self):
        """Negative area must raise ValueError."""
        with pytest.raises(ValueError, match="Area must be positive"):
            calculate_runoff(area_m2=-100, rainfall_mm=100)

    def test_zero_area_raises(self):
        """Zero area must raise ValueError."""
        with pytest.raises(ValueError, match="Area must be positive"):
            calculate_runoff(area_m2=0, rainfall_mm=100)

    def test_negative_rainfall_raises(self):
        """Negative rainfall must raise ValueError."""
        with pytest.raises(ValueError, match="Rainfall must be non-negative"):
            calculate_runoff(area_m2=100, rainfall_mm=-10)

    def test_runoff_coefficient_out_of_range_high(self):
        """Runoff coefficient > 1 must raise ValueError."""
        with pytest.raises(ValueError, match="Runoff coefficient must be in"):
            calculate_runoff(area_m2=100, rainfall_mm=100, runoff_coefficient=1.5)

    def test_runoff_coefficient_out_of_range_low(self):
        """Runoff coefficient < 0 must raise ValueError."""
        with pytest.raises(ValueError, match="Runoff coefficient must be in"):
            calculate_runoff(area_m2=100, rainfall_mm=100, runoff_coefficient=-0.1)

    def test_zero_runoff_coefficient(self):
        """Zero runoff coefficient should return zero volume."""
        result = calculate_runoff(area_m2=1000, rainfall_mm=100, runoff_coefficient=0)
        assert result == 0.0

    def test_full_runoff_coefficient(self):
        """Coefficient of 1 should return full rainfall volume."""
        area = 1000  # m²
        rainfall = 100  # mm
        result = calculate_runoff(area_m2=area, rainfall_mm=rainfall, runoff_coefficient=1.0)
        expected = area * (rainfall / 1000)  # m³
        assert result == pytest.approx(expected, rel=0.01)


class TestRunoffNumeric:
    """Numeric tests with tolerance (STD-014)."""

    def test_known_runoff_volume(self):
        """10000 m², 100mm rain, 0.5 coefficient = 500 m³.

        Tolerance: 5% (rational method approximation).
        """
        result = calculate_runoff(area_m2=10000, rainfall_mm=100, runoff_coefficient=0.5)
        expected = 10000 * 0.1 * 0.5  # 500 m³
        assert result == pytest.approx(expected, rel=0.05)

    def test_large_area_scaling(self):
        """Runoff should scale linearly with area.

        Tolerance: 1% (linear model, no approximation).
        """
        small = calculate_runoff(area_m2=1000, rainfall_mm=50, runoff_coefficient=0.7)
        large = calculate_runoff(area_m2=10000, rainfall_mm=50, runoff_coefficient=0.7)
        assert large == pytest.approx(10 * small, rel=0.01)


class TestCheckDamNumeric:
    """Numeric tests for check dam design (STD-014)."""

    def test_dam_height_range(self):
        """Dam height should be between 0.5m and 3.0m.

        Tolerance: 5%.
        """
        result = design_check_dam(slope_pct=10, area_m2=5000, rainfall_mm=100)
        assert 0.4 <= result["dam_height_m"] <= 3.1

    def test_dam_volume_positive(self):
        """Dam volume must be positive."""
        result = design_check_dam(slope_pct=10, area_m2=5000, rainfall_mm=100)
        assert result["dam_volume_m3"] > 0

    def test_cost_estimation(self):
        """Cost estimate should be positive and reasonable."""
        result = design_check_dam(slope_pct=10, area_m2=5000, rainfall_mm=100)
        assert result["estimated_cost_usd"] > 0


class TestContourTrenchNumeric:
    """Numeric tests for contour trench design (STD-014)."""

    def test_trench_length_positive(self):
        """Trench length must be positive."""
        result = design_contour_trench(slope_pct=10, area_m2=5000, rainfall_mm=100)
        assert result["total_length_m"] > 0

    def test_trench_volume_positive(self):
        """Trench volume must be positive."""
        result = design_contour_trench(slope_pct=10, area_m2=5000, rainfall_mm=100)
        assert result["trench_volume_m3"] > 0


class TestHalfMoonNumeric:
    """Numeric tests for half-moon design (STD-014)."""

    def test_structure_count_positive(self):
        """Number of structures must be positive."""
        result = design_half_moon(slope_pct=8, area_m2=2500, rainfall_mm=100)
        assert result["n_structures"] > 0

    def test_total_volume_positive(self):
        """Total volume must be positive."""
        result = design_half_moon(slope_pct=8, area_m2=2500, rainfall_mm=100)
        assert result["total_volume_m3"] > 0


class TestDesignFunctionNumeric:
    """Numeric tests for the unified design function (STD-014)."""

    def test_design_check_dam(self):
        """design_watershed_structure should dispatch to check_dam."""
        result = design_watershed_structure(structure_type="check_dam", slope_pct=15, area_m2=10000)
        assert result["structure_type"] == "check_dam"
        assert result["dam_height_m"] > 0

    def test_design_contour_trench(self):
        """design_watershed_structure should dispatch to contour_trench."""
        result = design_watershed_structure(
            structure_type="contour_trench", slope_pct=10, area_m2=5000
        )
        assert result["structure_type"] == "contour_trench"

    def test_design_half_moon(self):
        """design_watershed_structure should dispatch to half_moon."""
        result = design_watershed_structure(structure_type="half_moon", slope_pct=8, area_m2=2500)
        assert result["structure_type"] == "half_moon"

    def test_design_invalid_type_raises(self):
        """Unknown structure type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown structure type"):
            design_watershed_structure(structure_type="invalid_type", slope_pct=15, area_m2=10000)
