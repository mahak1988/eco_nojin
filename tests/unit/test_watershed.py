"""Tests for Watershed Structures module."""
import pytest
import math

from engine.hydroma.watershed.calculator import (
    StructureType,
    calculate_runoff, design_check_dam,
    design_contour_trench, design_half_moon,
    design_watershed_structure
)


class TestRunoffCalculation:
    def test_runoff_volume(self):
        runoff = calculate_runoff(area_m2=10000, rainfall_mm=100, runoff_coefficient=0.5)
        assert runoff == pytest.approx(500, rel=0.1)


class TestCheckDam:
    def test_check_dam_design(self):
        result = design_check_dam(slope_pct=15, area_m2=10000, rainfall_mm=100)
        assert result["dam_height_m"] > 0
        assert result["dam_volume_m3"] > 0
        assert result["estimated_cost_usd"] > 0

    def test_steeper_slope_taller_dam(self):
        result_flat = design_check_dam(slope_pct=5, area_m2=10000)
        result_steep = design_check_dam(slope_pct=30, area_m2=10000)
        assert result_steep["dam_height_m"] >= result_flat["dam_height_m"]


class TestContourTrench:
    def test_contour_trench_design(self):
        result = design_contour_trench(slope_pct=10, area_m2=5000, rainfall_mm=100)
        assert result["total_length_m"] > 0
        assert result["trench_volume_m3"] > 0
        assert result["estimated_cost_usd"] > 0


class TestHalfMoon:
    def test_half_moon_design(self):
        result = design_half_moon(slope_pct=8, area_m2=2500, rainfall_mm=100)
        assert result["n_structures"] > 0
        assert result["total_volume_m3"] > 0
        assert result["estimated_cost_usd"] > 0


class TestDesignFunction:
    def test_design_check_dam(self):
        result = design_watershed_structure(
            structure_type="check_dam", slope_pct=15, area_m2=10000
        )
        assert result["structure_type"] == "check_dam"

    def test_design_invalid_type(self):
        with pytest.raises(ValueError, match="Unknown structure type"):
            design_watershed_structure(
                structure_type="invalid_type", slope_pct=15, area_m2=10000
            )
