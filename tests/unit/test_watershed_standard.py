"""Acceptance tests for the FAO-standard watershed structure design (S1-3).

These pin the remediation requirements: every public input must influence the
result (no decorative parameters) and the engineering outputs must respect the
FAO design bands.
"""

from __future__ import annotations

import pytest

from engine.hydroma.watershed.calculator import (
    design_check_dam,
    design_contour_trench,
    design_watershed_structure,
)


class TestCheckDamFaoSizing:
    def test_all_inputs_are_used(self):
        base = design_check_dam(12.0, 50_000.0, 120.0, target_retention_years=10)
        more_years = design_check_dam(12.0, 50_000.0, 120.0, target_retention_years=20)
        wider = design_check_dam(12.0, 50_000.0, 120.0, channel_width_m=8.0)
        more_sediment = design_check_dam(12.0, 50_000.0, 120.0, sediment_yield_t_ha_yr=20.0)

        # retention horizon must increase the required storage (was a dead input)
        assert more_years["storage_required_m3"] > base["storage_required_m3"]
        # a wider channel needs less height for the same storage
        assert wider["dam_height_m"] <= base["dam_height_m"]
        # more sediment yield needs more storage
        assert more_sediment["storage_required_m3"] > base["storage_required_m3"]

    def test_fao_design_bands(self):
        d = design_check_dam(12.0, 50_000.0, 120.0)
        assert 0.0 < d["trap_efficiency"] <= 0.95
        assert 0.3 <= d["freeboard_m"] <= 0.5
        assert d["spillway_width_m"] > 0.0
        assert d["design_standard"].startswith("FAO")
        assert 0.5 <= d["dam_height_m"] <= 6.0

    def test_sediment_volume_is_physical(self):
        # 5 t/ha/yr over 5 ha with bulk density 1.3 t/m3 -> 19.2 m3/yr
        d = design_check_dam(12.0, 50_000.0, 120.0)
        assert d["annual_sediment_m3"] == pytest.approx(19.23, abs=0.05)

    def test_peak_flow_uses_rational_method(self):
        # C=0.6, i=120/6=20 mm/h, A=5 ha -> Qp = 0.6*20*5/360 = 0.1667 m3/s
        d = design_check_dam(12.0, 50_000.0, 120.0)
        assert d["peak_flow_m3s"] == pytest.approx(0.1667, abs=0.001)

    def test_cost_scales_with_volume(self):
        small = design_check_dam(5.0, 10_000.0, 80.0)
        big = design_check_dam(5.0, 100_000.0, 80.0)
        assert big["estimated_cost_usd"] > small["estimated_cost_usd"]


class TestContourTrenchFao:
    def test_vertical_interval_is_capped(self):
        # 1% slope would give 30 m; the old 1/slope form produced 1000 m
        gentle = design_contour_trench(1.0, 50_000.0)
        assert gentle["vertical_interval_m"] == pytest.approx(30.0)
        steep = design_contour_trench(60.0, 50_000.0)
        assert steep["vertical_interval_m"] == pytest.approx(5.0)

    def test_interval_within_fao_band(self):
        for slope in (2.0, 5.0, 8.0, 12.0, 25.0):
            d = design_contour_trench(slope, 20_000.0)
            assert 5.0 <= d["vertical_interval_m"] <= 30.0

    def test_cross_section_geometry(self):
        d = design_contour_trench(12.0, 20_000.0, depth_m=0.4, bottom_width_m=0.3, side_slope_hv=0.5)
        # trapezoid: (0.3 + (0.3 + 2*0.5*0.4))/2 * 0.4 = 0.2 m2
        assert d["cross_section_m2"] == pytest.approx(0.2, abs=1e-6)

    def test_infiltration_assumption_is_labelled(self):
        d = design_contour_trench(12.0, 20_000.0)
        assert d["infiltration_efficiency"] == pytest.approx(0.7)
        assert "calibrate" in d["infiltration_note"]

    def test_invalid_slope_rejected(self):
        with pytest.raises(ValueError):
            design_contour_trench(0.0, 20_000.0)


class TestDispatcher:
    def test_retention_years_reach_the_check_dam(self):
        a = design_watershed_structure("check_dam", 12.0, 50_000.0, 120.0, target_retention_years=5)
        b = design_watershed_structure("check_dam", 12.0, 50_000.0, 120.0, target_retention_years=25)
        assert b["storage_required_m3"] > a["storage_required_m3"]

    def test_unknown_structure_rejected(self):
        with pytest.raises(ValueError):
            design_watershed_structure("not_a_structure", 10.0, 1000.0)
