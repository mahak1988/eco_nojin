"""
Tests for NojinCalculator - Phase 5 Biofertilizer
===================================================
"""

import pytest

from engine.hydroma.biofertilizer import (
    NojinCalculator,
    NojinInput,
    NojinResult,
    SoilCondition,
    FormulationType,
    ApplicationMethod,
)


class TestNojinCalculator:
    """Test suite for NojinCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """NojinCalculator instance."""
        return NojinCalculator()
    
    @pytest.fixture
    def optimal_soil(self):
        """Optimal soil conditions."""
        return SoilCondition(
            ph=6.8,
            organic_carbon_pct=1.5,
            nitrogen_kg_ha=60,
            phosphorus_kg_ha=30,
            potassium_kg_ha=100,
            temperature_c=25,
            moisture_pct=55,
            texture="loam",
        )
    
    @pytest.fixture
    def poor_soil(self):
        """Poor soil conditions."""
        return SoilCondition(
            ph=5.0,  # Acidic
            organic_carbon_pct=0.3,  # Low OC
            nitrogen_kg_ha=20,  # Low N
            phosphorus_kg_ha=10,  # Low P
            potassium_kg_ha=40,
            temperature_c=12,  # Cool
            moisture_pct=25,  # Dry
            texture="sand",
        )
    
    @pytest.fixture
    def wheat_input(self, optimal_soil):
        """Input for wheat crop."""
        return NojinInput(
            land_profile_id="test-wheat-001",
            crop_type="wheat",
            soil=optimal_soil,
            target_yield_t_ha=5.0,
            application_method=ApplicationMethod.SOIL_APPLICATION,
            formulation_type=FormulationType.LIQUID,
        )
    
    def test_initialization(self, calculator):
        """Test calculator initializes correctly."""
        assert calculator is not None
    
    def test_calculate_wheat(self, calculator, wheat_input):
        """Test wheat application calculation."""
        result = calculator.calculate(wheat_input)
        
        assert isinstance(result, NojinResult)
        assert result.land_profile_id == "test-wheat-001"
        assert result.recommended_dosage_kg_ha > 0
        assert result.suitability_score > 0
    
    def test_optimal_soil_high_suitability(self, calculator, wheat_input):
        """Optimal soil should have high suitability."""
        result = calculator.calculate(wheat_input)
        
        assert result.suitability_score >= 80
        assert result.soil_compatibility_score >= 80
        assert result.risk_level == "low"
    
    def test_poor_soil_lower_suitability(self, calculator, poor_soil):
        """Poor soil should have lower suitability."""
        input_data = NojinInput(
            land_profile_id="test-poor-001",
            crop_type="wheat",
            soil=poor_soil,
            target_yield_t_ha=3.0,
        )
        
        result = calculator.calculate(input_data)
        
        assert result.suitability_score < 80
        assert result.risk_level in ["moderate", "high"]
    
    def test_dosage_varies_by_crop(self, calculator, optimal_soil):
        """Dosage should vary by crop type."""
        dosages = {}
        
        for crop in ["wheat", "rice", "corn"]:
            input_data = NojinInput(
                land_profile_id=f"test-{crop}",
                crop_type=crop,
                soil=optimal_soil,
                target_yield_t_ha=5.0,
            )
            result = calculator.calculate(input_data)
            dosages[crop] = result.recommended_dosage_kg_ha
        
        # Different crops should have different dosages
        assert len(set(dosages.values())) > 1
    
    def test_yield_increase_prediction(self, calculator, wheat_input):
        """Yield increase should be reasonable (5-30%)."""
        result = calculator.calculate(wheat_input)
        
        assert 5.0 <= result.expected_yield_increase_pct <= 30.0
    
    def test_nitrogen_fixation_prediction(self, calculator, wheat_input):
        """Nitrogen fixation should be reasonable (10-50 kg/ha)."""
        result = calculator.calculate(wheat_input)
        
        assert 10.0 <= result.expected_nitrogen_fixation_kg_ha <= 50.0
    
    def test_timing_calculation(self, calculator, wheat_input):
        """Application timing should be calculated."""
        result = calculator.calculate(wheat_input)
        
        # Soil application: -10 days (before planting)
        assert result.optimal_application_date_offset_days == -10
    
    def test_recommendations_generated(self, calculator, wheat_input):
        """Recommendations should be generated."""
        result = calculator.calculate(wheat_input)
        
        assert len(result.recommendations) > 0
        assert all(isinstance(r, str) for r in result.recommendations)
    
    def test_invalid_ph_raises_error(self, calculator, optimal_soil):
        """Invalid pH should raise ValueError."""
        invalid_soil = SoilCondition(
            ph=15.0,  # Invalid
            organic_carbon_pct=1.0,
            nitrogen_kg_ha=50,
            phosphorus_kg_ha=20,
            potassium_kg_ha=80,
            temperature_c=20,
            moisture_pct=50,
        )
        
        input_data = NojinInput(
            land_profile_id="test-invalid",
            crop_type="wheat",
            soil=invalid_soil,
            target_yield_t_ha=3.0,
        )
        
        with pytest.raises(ValueError, match="Soil pH"):
            calculator.calculate(input_data)
    
    def test_invalid_moisture_raises_error(self, calculator, optimal_soil):
        """Invalid moisture should raise ValueError."""
        invalid_soil = SoilCondition(
            ph=6.5,
            organic_carbon_pct=1.0,
            nitrogen_kg_ha=50,
            phosphorus_kg_ha=20,
            potassium_kg_ha=80,
            temperature_c=20,
            moisture_pct=150,  # Invalid > 100
        )
        
        input_data = NojinInput(
            land_profile_id="test-invalid",
            crop_type="wheat",
            soil=invalid_soil,
            target_yield_t_ha=3.0,
        )
        
        with pytest.raises(ValueError, match="Soil moisture"):
            calculator.calculate(input_data)
    
    def test_acidic_soil_recommendation(self, calculator):
        """Acidic soil should get lime recommendation."""
        acidic_soil = SoilCondition(
            ph=5.0,  # Acidic
            organic_carbon_pct=1.0,
            nitrogen_kg_ha=50,
            phosphorus_kg_ha=20,
            potassium_kg_ha=80,
            temperature_c=20,
            moisture_pct=50,
        )
        
        input_data = NojinInput(
            land_profile_id="test-acidic",
            crop_type="wheat",
            soil=acidic_soil,
            target_yield_t_ha=3.0,
        )
        
        result = calculator.calculate(input_data)
        
        # Should have lime recommendation
        assert any("lime" in r.lower() for r in result.recommendations)


class TestFormulationTypes:
    """Test different formulation types."""
    
    @pytest.fixture
    def calculator(self):
        return NojinCalculator()
    
    @pytest.fixture
    def optimal_soil(self):
        return SoilCondition(
            ph=6.8,
            organic_carbon_pct=1.5,
            nitrogen_kg_ha=60,
            phosphorus_kg_ha=30,
            potassium_kg_ha=100,
            temperature_c=25,
            moisture_pct=55,
        )
    
    def test_liquid_vs_powder_dosage(self, calculator, optimal_soil):
        """Powder should require higher dosage than liquid."""
        results = {}
        
        for formulation in [FormulationType.LIQUID, FormulationType.POWDER]:
            input_data = NojinInput(
                land_profile_id=f"test-{formulation.value}",
                crop_type="wheat",
                soil=optimal_soil,
                target_yield_t_ha=5.0,
                formulation_type=formulation,
            )
            results[formulation.value] = calculator.calculate(input_data).recommended_dosage_kg_ha
        
        assert results["powder"] > results["liquid"]
