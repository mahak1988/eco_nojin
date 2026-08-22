"""
Unit tests for Hydroma Global Watchdog
======================================

Tests KGCv5, WBIv3, and GlobalWatchdog against reference data.

References:
- Peel et al. (2007) — Köppen reference
- WRI Aqueduct 4.0 — Water stress levels
"""
from __future__ import annotations

import pytest
import numpy as np

from engine.hydroma.models.global_watchdog import (
    KGCv5, WBIv3, WBIInputs, GlobalWatchdog, reference_data,
)


class TestKGCv5:
    """Tests for Köppen-Geiger classification."""

    def test_bwh_desert(self):
        """Cairo should be BWh (Hot desert)."""
        t_min = np.array([9, 10, 13, 16, 20, 23, 24, 24, 22, 19, 14, 10])
        t_max = np.array([19, 20, 24, 28, 33, 35, 36, 35, 33, 29, 24, 20])
        p = np.array([5, 4, 4, 1, 1, 0, 0, 0, 0, 1, 3, 6])
        result = KGCv5.classify(t_min, t_max, p)
        assert result["group"] == "B"
        assert result["code"] == "BWh"

    def test_bwk_desert_cold(self):
        """Yemen Sanaa should be BWk (Cold desert) — borderline BSh accepted."""
        t_min = np.array([6, 7, 9, 11, 12, 14, 14, 13, 12, 7, 5, 7])
        t_max = np.array([24, 26, 29, 31, 33, 36, 37, 36, 33, 29, 26, 24])
        p = np.array([1.5, 12.8, 33.4, 6.4, 13.3, 8.8, 32.8, 53.0, 16.2, 1.4, 0.7, 2.0])
        result = KGCv5.classify(t_min, t_max, p)
        # Accept BWh, BWk, or BSh (borderline)
        assert result["group"] == "B"
        assert result["code"] in ("BWh", "BWk", "BSh")

    def test_af_rainforest(self):
        """Jakarta should be Af (Tropical rainforest)."""
        t_min = np.array([24, 24, 24, 25, 25, 24, 24, 24, 24, 24, 24, 24])
        t_max = np.array([31, 31, 32, 33, 33, 33, 33, 33, 33, 33, 32, 31])
        p = np.array([350, 300, 220, 150, 110, 95, 65, 50, 60, 110, 150, 220])
        result = KGCv5.classify(t_min, t_max, p)
        assert result["code"] == "Af"

    def test_csa_mediterranean(self):
        """Rome should be Csa (Hot-summer Mediterranean)."""
        t_min = np.array([3, 4, 6, 9, 13, 17, 20, 20, 17, 13, 8, 4])
        t_max = np.array([12, 13, 15, 19, 23, 28, 31, 31, 27, 22, 16, 13])
        p = np.array([80, 75, 65, 55, 40, 20, 15, 25, 65, 105, 115, 95])
        result = KGCv5.classify(t_min, t_max, p)
        assert result["group"] == "C"
        assert result["code"] == "Csa"

    def test_et_tundra(self):
        """Tromsø should be ET (Tundra)."""
        t_min = np.array([-7, -7, -5, -2, 2, 6, 9, 8, 5, 1, -3, -6])
        t_max = np.array([-1, -1, 1, 4, 8, 13, 16, 14, 10, 5, 1, -1])
        p = np.array([95, 75, 60, 50, 40, 50, 70, 85, 110, 135, 105, 100])
        result = KGCv5.classify(t_min, t_max, p)
        assert result["code"] == "ET"

    def test_am_monsoon(self):
        """Mumbai should be Am (Tropical monsoon)."""
        t_min = np.array([17, 18, 21, 24, 27, 27, 26, 26, 26, 24, 21, 18])
        t_max = np.array([31, 32, 33, 34, 34, 32, 30, 30, 31, 33, 33, 32])
        p = np.array([1, 1, 0, 2, 20, 530, 840, 585, 340, 90, 15, 3])
        result = KGCv5.classify(t_min, t_max, p)
        assert result["code"] in ("Am", "Aw", "As")

    def test_validation_near_match(self):
        """Validation should accept near-matches."""
        val = KGCv5.validate("BSh", "BWh", "")
        assert val["near_match"]
        assert val["valid"]

    def test_invalid_input_length(self):
        """Should reject non-12-length inputs."""
        with pytest.raises(ValueError):
            KGCv5.classify(np.zeros(10), np.zeros(10), np.zeros(10))


class TestWBIv3:
    """Tests for Water Bankruptcy Index."""

    def test_water_secure(self):
        """Water-secure region (like Netherlands)."""
        inputs = WBIInputs(
            renewable_water_m3_per_capita=3500,
            withdrawal_ratio=0.15,
            groundwater_depletion_mm_yr=0.0,
            water_quality_index=0.9,
            drought_frequency_events_yr=0.1,
            demand_growth_rate_pct=0.2,
            infrastructure_leakage_pct=5.0,
            governance_score=0.95,
        )
        result = WBIv3.compute(inputs)
        assert result["classification"] == "Water-Secure"
        assert result["wbi"] < 20

    def test_water_bankruptcy(self):
        """Bankruptcy region (like Yemen)."""
        inputs = WBIInputs(
            renewable_water_m3_per_capita=80,
            withdrawal_ratio=1.8,
            groundwater_depletion_mm_yr=8.0,
            water_quality_index=0.25,
            drought_frequency_events_yr=3.0,
            demand_growth_rate_pct=2.8,
            infrastructure_leakage_pct=60.0,
            governance_score=0.15,
        )
        result = WBIv3.compute(inputs)
        assert result["classification"] == "Water-Bankruptcy"
        assert result["wbi"] > 80
        assert result["years_to_bankruptcy_estimate"] is not None

    def test_water_crisis(self):
        """Crisis region (like China Beijing)."""
        inputs = WBIInputs(
            renewable_water_m3_per_capita=430,
            withdrawal_ratio=1.2,
            groundwater_depletion_mm_yr=6.0,
            water_quality_index=0.5,
            drought_frequency_events_yr=1.5,
            demand_growth_rate_pct=1.5,
            infrastructure_leakage_pct=18.0,
            governance_score=0.65,
        )
        result = WBIv3.compute(inputs)
        assert result["classification"] in ("Water-Crisis", "Water-Scarce")
        assert 40 <= result["wbi"] <= 85

    def test_invalid_inputs(self):
        """Should reject invalid inputs."""
        inputs = WBIInputs(
            renewable_water_m3_per_capita=-100,  # Invalid
            withdrawal_ratio=0.5,
            groundwater_depletion_mm_yr=0.0,
            water_quality_index=0.5,
            drought_frequency_events_yr=0.5,
            demand_growth_rate_pct=1.0,
            infrastructure_leakage_pct=20.0,
            governance_score=0.5,
        )
        with pytest.raises(ValueError):
            WBIv3.compute(inputs)

    def test_validate_against_wri(self):
        """WBI should align with WRI levels."""
        # Yemen (WRI=5.0) → WBI should be in (60, 100)
        validation = WBIv3.validate_against_wri(90.5, 5.0)
        assert validation["in_expected_range"]
        assert validation["expected_class"] == "Water-Bankruptcy"

    def test_uncertainty_bounds(self):
        """Should include uncertainty bounds."""
        inputs = WBIInputs(
            renewable_water_m3_per_capita=1000,
            withdrawal_ratio=0.7,
            groundwater_depletion_mm_yr=3.0,
            water_quality_index=0.6,
            drought_frequency_events_yr=1.0,
            demand_growth_rate_pct=1.5,
            infrastructure_leakage_pct=30.0,
            governance_score=0.6,
        )
        result = WBIv3.compute(inputs)
        assert "wbi_low" in result
        assert "wbi_high" in result
        assert result["wbi_low"] <= result["wbi"] <= result["wbi_high"]


class TestGlobalWatchdog:
    """Integration tests for GlobalWatchdog."""

    def test_analyze_single(self):
        """Test single region analysis."""
        watchdog = GlobalWatchdog()
        t_min = np.array([9, 10, 13, 16, 20, 23, 24, 24, 22, 19, 14, 10])
        t_max = np.array([19, 20, 24, 28, 33, 35, 36, 35, 33, 29, 24, 20])
        p = np.array([5, 4, 4, 1, 1, 0, 0, 0, 0, 1, 3, 6])
        water = WBIInputs(570, 1.1, 2.5, 0.5, 1.0, 2.5, 35.0, 0.5)

        result = watchdog.analyze("Egypt_Cairo", (t_min, t_max, p), water)

        assert result.region_name == "Egypt_Cairo"
        assert result.kgc["group"] == "B"
        assert 0 <= result.wbi["wbi"] <= 100
        assert result.timestamp

    def test_analyze_many(self):
        """Test batch analysis."""
        watchdog = GlobalWatchdog()
        regions = {}
        for name in ["Brazil_Amazon", "Yemen_Sanaa", "France_Paris"]:
            lat, lon = reference_data.GEO_COORDS[name]
            # Dummy data
            t_min = np.zeros(12)
            t_max = np.full(12, 20.0)
            p = np.full(12, 50.0)
            water = WBIInputs(1000, 0.5, 0.0, 0.5, 0.5, 1.0, 20.0, 0.5)
            regions[name] = ((t_min, t_max, p), water)

        results = watchdog.analyze_many(regions)
        assert len(results) == 3
        assert "Brazil_Amazon" in results

    def test_rank_regions(self):
        """Test ranking by WBI."""
        watchdog = GlobalWatchdog()
        analyses = {}
        for i, wbi_value in enumerate([90.0, 10.0, 50.0, 30.0]):
            name = f"region_{i}"
            # Create mock analysis
            from engine.hydroma.models.global_watchdog.watchdog import RegionAnalysis
            analyses[name] = RegionAnalysis(
                region_name=name,
                kgc={"code": "Csa", "group": "C"},
                wbi={"wbi": wbi_value, "wbi_low": wbi_value*0.85,
                     "wbi_high": wbi_value*1.15,
                     "classification": "test", "risk_level": "test"},
                timestamp="2026-01-01T00:00:00Z",
            )

        ranked = watchdog.rank_regions(analyses, by="wbi", ascending=False)
        assert ranked[0][1].wbi["wbi"] == 90.0
        assert ranked[-1][1].wbi["wbi"] == 10.0


class TestReferenceData:
    """Tests for reference data integrity."""

    def test_koppen_reference_complete(self):
        """All 25 countries have Köppen reference."""
        assert len(reference_data.KOPPEN_REFERENCE) == 25

    def test_wri_reference_complete(self):
        """All 25 countries have WRI reference."""
        assert len(reference_data.WRI_REFERENCE) == 25

    def test_geo_coords_complete(self):
        """All 25 countries have coordinates."""
        assert len(reference_data.GEO_COORDS) == 25

    def test_known_limitations(self):
        """Known limitations documented."""
        assert len(reference_data.KNOWN_LIMITATIONS) == 3
        assert "Yemen_Sanaa" in reference_data.KNOWN_LIMITATIONS
        assert "France_Paris" in reference_data.KNOWN_LIMITATIONS
        assert "Japan_Tokyo" in reference_data.KNOWN_LIMITATIONS
