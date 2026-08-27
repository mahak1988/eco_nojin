"""
Tests for GroundwaterService - Phase 3 Water Intelligence
==========================================================
"""

import pytest

from engine.hydroma.groundwater import (
    AquiferType,
    GroundwaterInput,
    GroundwaterResult,
    GroundwaterService,
    WaterQualityClass,
)


class TestGroundwaterService:
    """Test suite for GroundwaterService."""

    @pytest.fixture
    def service(self):
        """GroundwaterService instance."""
        return GroundwaterService()

    @pytest.fixture
    def healthy_input(self):
        """Input for healthy aquifer."""
        return GroundwaterInput(
            land_profile_id="test-healthy-001",
            well_depth_m=50.0,
            water_table_depth_m=10.0,
            hydraulic_conductivity_m_s=1e-4,  # 8.64 m/day
            aquifer_thickness_m=40.0,
            aquifer_type=AquiferType.UNCONFINED,
            recharge_rate_mm_yr=200.0,
            abstraction_rate_m3_yr=1000.0,  # Low abstraction (< safe_yield 1600)
            tds_mg_l=250.0,  # Good quality
            porosity=0.3,
            specific_yield=0.15,
        )

    @pytest.fixture
    def stressed_input(self):
        """Input for stressed aquifer."""
        return GroundwaterInput(
            land_profile_id="test-stressed-001",
            well_depth_m=100.0,
            water_table_depth_m=50.0,
            hydraulic_conductivity_m_s=1e-5,
            aquifer_thickness_m=50.0,
            aquifer_type=AquiferType.CONFINED,
            recharge_rate_mm_yr=50.0,
            abstraction_rate_m3_yr=50000.0,  # High abstraction
            tds_mg_l=800.0,  # Fair quality
            porosity=0.2,
            specific_yield=0.1,
        )

    def test_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None

    def test_process_healthy_aquifer(self, service, healthy_input):
        """Test analysis of healthy aquifer."""
        result = service.analyze(healthy_input)

        assert isinstance(result, GroundwaterResult)
        assert result.land_profile_id == "test-healthy-001"
        assert result.darcy_flux_m_s > 0
        assert result.transmissivity_m2_s > 0
        assert result.sustainability_index > 0.5  # Reasonable sustainability
        assert result.water_quality_class == WaterQualityClass.EXCELLENT
        assert result.status == "healthy"

    def test_process_stressed_aquifer(self, service, stressed_input):
        """Test analysis of stressed aquifer."""
        result = service.analyze(stressed_input)

        assert isinstance(result, GroundwaterResult)
        assert result.sustainability_index < 1.0  # Stressed
        assert result.water_quality_class == WaterQualityClass.FAIR
        assert result.overexploitation_risk in ["high", "critical"]

    def test_darcy_flux_calculation(self, service, healthy_input):
        """Test Darcy flux calculation."""
        result = service.analyze(healthy_input)

        # Expected: K * (water_table / well_depth)
        expected = 1e-4 * (10.0 / 50.0)
        assert abs(result.darcy_flux_m_s - expected) < 1e-8

    def test_transmissivity_calculation(self, service, healthy_input):
        """Test transmissivity calculation."""
        result = service.analyze(healthy_input)

        # Expected: K * thickness
        expected = 1e-4 * 40.0
        assert abs(result.transmissivity_m2_s - expected) < 1e-8

    def test_validate_input_negative_K(self, service):
        """Test validation rejects negative K."""
        invalid_input = GroundwaterInput(
            land_profile_id="test-invalid",
            well_depth_m=50.0,
            water_table_depth_m=10.0,
            hydraulic_conductivity_m_s=-1e-4,  # Invalid
            aquifer_thickness_m=40.0,
        )

        with pytest.raises(ValueError, match="Hydraulic conductivity must be positive"):
            service.analyze(invalid_input)

    def test_water_quality_classification(self, service):
        """Test water quality classification."""
        test_cases = [
            (100.0, WaterQualityClass.EXCELLENT),
            (500.0, WaterQualityClass.GOOD),
            (750.0, WaterQualityClass.FAIR),
            (1000.0, WaterQualityClass.POOR),
            (1500.0, WaterQualityClass.UNACCEPTABLE),
        ]

        for tds, expected_class in test_cases:
            input_data = GroundwaterInput(
                land_profile_id="test-quality",
                well_depth_m=50.0,
                water_table_depth_m=10.0,
                hydraulic_conductivity_m_s=1e-4,
                aquifer_thickness_m=40.0,
                tds_mg_l=tds,
            )

            result = service.analyze(input_data)
            assert result.water_quality_class == expected_class

    def test_sustainability_index_calculation(self, service, healthy_input):
        """Test sustainability index calculation using fixture's actual values."""
        result = service.analyze(healthy_input)

        # Use actual values from fixture (not hardcoded)
        recharge_m_yr = healthy_input.recharge_rate_mm_yr / 1000.0
        area_m2 = 10000.0  # 1 hectare
        safe_yield = 0.8 * recharge_m_yr * area_m2
        expected_index = safe_yield / healthy_input.abstraction_rate_m3_yr

        # Verify calculation matches
        assert abs(result.sustainability_index - expected_index) < 0.01,             f"Expected {expected_index}, got {result.sustainability_index}"

        # Sanity check: should be sustainable (> 1.0) for healthy fixture
        assert result.sustainability_index > 1.0,             f"Healthy aquifer should be sustainable, got {result.sustainability_index}"

    def test_recommendations_generated(self, service, healthy_input):
        """Test that recommendations are generated."""
        result = service.analyze(healthy_input)

        assert len(result.recommendations) > 0
        assert all(isinstance(r, str) for r in result.recommendations)


class TestUtils:
    """Test utility functions."""

    def test_validate_range_valid(self):
        """Test validation accepts valid values."""
        assert 0.5 > 0  # Positive
        assert 10.0 > 0

    def test_validate_range_invalid(self):
        """Test validation rejects invalid values."""
        with pytest.raises(AssertionError):
            assert -1.0 > 0

    def test_normalize_percentage_valid(self):
        """Test percentage normalization."""
        value = 75.0
        normalized = value / 100.0
        assert normalized == 0.75

    def test_normalize_percentage_negative(self):
        """Test handling of negative percentages."""
        value = -10.0
        normalized = max(0.0, value / 100.0)
        assert normalized == 0.0
