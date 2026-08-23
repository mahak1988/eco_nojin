"""
Tests for Water Adapters (Phase 3)
====================================
Tests connection to EXISTING water modules.
"""

import pytest

from engine.land.integration.water_adapter import (
    WaterBalanceInput,
    WaterBalanceResult,
    RunoffInput,
    RunoffResult,
    GroundwaterInput,
    GroundwaterResult,
    UnifiedWaterAnalysis,
    WaterBalanceIntegrator,
    WatershedIntegrator,
    GroundwaterIntegrator,
    UnifiedWaterAnalyzer,
)


# ============================================================
# Water Balance Tests
# ============================================================

class TestWaterBalance:
    """Test Water Balance Integrator"""
    
    @pytest.fixture
    def integrator(self):
        return WaterBalanceIntegrator()
    
    def test_simple_balance(self, integrator):
        inp = WaterBalanceInput(precipitation_mm=100.0, et0_mm=60.0)
        result = integrator.calculate_balance(inp)
        assert isinstance(result, WaterBalanceResult)
        assert result.is_balanced
        assert result.precipitation_mm == 100.0
    
    def test_mass_conservation(self, integrator):
        """P = ET + R + dP + dS"""
        inp = WaterBalanceInput(
            precipitation_mm=150.0,
            et0_mm=80.0,
            initial_storage_mm=100.0,
        )
        result = integrator.calculate_balance(inp)
        assert result.balance_error_mm < 0.1
    
    def test_et_limited_by_water(self, integrator):
        """ET cannot exceed available water"""
        inp = WaterBalanceInput(
            precipitation_mm=10.0,
            et0_mm=200.0,
            initial_storage_mm=0.0,
        )
        result = integrator.calculate_balance(inp)
        assert result.evapotranspiration_mm <= 10.0
    
    def test_deficit_calculation(self, integrator):
        """Test deficit when no initial storage available"""
        inp = WaterBalanceInput(
            precipitation_mm=50.0,
            et0_mm=150.0,
            initial_storage_mm=0.0,  # No storage - forces real deficit
        )
        result = integrator.calculate_balance(inp)
        assert result.metadata["water_deficit_mm"] > 0
        assert result.metadata["potential_deficit_mm"] > 0
    
    def test_potential_deficit_vs_actual(self, integrator):
        """potential_deficit >= water_deficit (storage can only reduce deficit)"""
        inp = WaterBalanceInput(
            precipitation_mm=50.0,
            et0_mm=150.0,
            initial_storage_mm=50.0,  # Some storage available
        )
        result = integrator.calculate_balance(inp)
        potential = result.metadata["potential_deficit_mm"]
        actual = result.metadata["water_deficit_mm"]
        assert potential >= actual
        assert potential == 100.0  # 150 - 50
        assert actual == 50.0  # 150 - (50 + 50)
    
    def test_zero_deficit_when_sufficient_water(self, integrator):
        """When P > ET, no deficit"""
        inp = WaterBalanceInput(
            precipitation_mm=200.0,
            et0_mm=80.0,
            initial_storage_mm=0.0,
        )
        result = integrator.calculate_balance(inp)
        assert result.metadata["water_deficit_mm"] == 0
        assert result.metadata["potential_deficit_mm"] == 0
    
    def test_surplus_calculation(self, integrator):
        inp = WaterBalanceInput(precipitation_mm=300.0, et0_mm=50.0)
        result = integrator.calculate_balance(inp)
        assert result.deep_percolation_mm > 0 or result.surface_runoff_mm > 0
    
    def test_negative_precipitation_error(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_balance(
                WaterBalanceInput(precipitation_mm=-10.0, et0_mm=50.0)
            )
    
    def test_negative_et_error(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_balance(
                WaterBalanceInput(precipitation_mm=100.0, et0_mm=-10.0)
            )
    
    def test_zero_area_error(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_balance(
                WaterBalanceInput(precipitation_mm=100.0, et0_mm=50.0, area_ha=0)
            )


# ============================================================
# SCS-CN Runoff Tests
# ============================================================

class TestSCSRunoff:
    """Test SCS-CN Runoff Integrator"""
    
    @pytest.fixture
    def integrator(self):
        return WatershedIntegrator()
    
    def test_simple_runoff(self, integrator):
        inp = RunoffInput(precipitation_mm=100.0, curve_number=75)
        result = integrator.calculate_runoff(inp)
        assert isinstance(result, RunoffResult)
        assert 0 < result.runoff_mm < 100.0
    
    def test_runoff_formula(self, integrator):
        """Verify SCS-CN formula: Q = (P-Ia)^2 / (P-Ia+S)"""
        cn = 80
        p = 100.0
        s = (25400 / cn) - 254  # 63.5
        ia = 0.2 * s  # 12.7
        expected_q = ((p - ia) ** 2) / ((p - ia) + s)
        
        result = integrator.calculate_runoff(
            RunoffInput(precipitation_mm=p, curve_number=cn)
        )
        assert abs(result.runoff_mm - expected_q) < 0.1
    
    def test_high_cn_more_runoff(self, integrator):
        low = integrator.calculate_runoff(RunoffInput(100.0, 50))
        high = integrator.calculate_runoff(RunoffInput(100.0, 90))
        assert high.runoff_mm > low.runoff_mm
    
    def test_low_precipitation_no_runoff(self, integrator):
        """P < Ia means no runoff"""
        result = integrator.calculate_runoff(
            RunoffInput(precipitation_mm=5.0, curve_number=70)
        )
        assert result.runoff_mm == 0.0
    
    def test_volume_scales_with_area(self, integrator):
        r1 = integrator.calculate_runoff(RunoffInput(100.0, 75, area_ha=1.0))
        r10 = integrator.calculate_runoff(RunoffInput(100.0, 75, area_ha=10.0))
        assert abs(r10.runoff_volume_m3 / r1.runoff_volume_m3 - 10.0) < 0.1
    
    def test_invalid_cn_too_high(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_runoff(RunoffInput(100.0, 150))
    
    def test_invalid_cn_too_low(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_runoff(RunoffInput(100.0, 10))
    
    def test_negative_precipitation(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_runoff(RunoffInput(-10.0, 75))
    
    def test_estimate_cn_sand(self, integrator):
        cn = integrator.estimate_cn("sand")
        assert 50 <= cn <= 70
    
    def test_estimate_cn_clay(self, integrator):
        cn = integrator.estimate_cn("clay")
        assert 80 <= cn <= 95
    
    def test_estimate_cn_slope_adjustment(self, integrator):
        cn_flat = integrator.estimate_cn("loam", slope_pct=2.0)
        cn_steep = integrator.estimate_cn("loam", slope_pct=15.0)
        assert cn_steep > cn_flat
    
    def test_amc_adjustment(self, integrator):
        """Wet conditions (AMC III) produce more runoff"""
        dry = integrator.calculate_runoff(
            RunoffInput(100.0, 75, antecedent_moisture="I")
        )
        wet = integrator.calculate_runoff(
            RunoffInput(100.0, 75, antecedent_moisture="III")
        )
        assert wet.runoff_mm > dry.runoff_mm


# ============================================================
# Groundwater Tests
# ============================================================

class TestGroundwater:
    """Test Groundwater Integrator (Darcy)"""
    
    @pytest.fixture
    def integrator(self):
        return GroundwaterIntegrator()
    
    def test_simple_darcy(self, integrator):
        inp = GroundwaterInput(
            hydraulic_conductivity_m_day=10.0,
            hydraulic_gradient=0.01,
            aquifer_thickness_m=50.0,
        )
        result = integrator.calculate_flow(inp)
        assert isinstance(result, GroundwaterResult)
        assert result.flow_rate_m3_day > 0
    
    def test_darcy_law(self, integrator):
        """Q = K * A * i"""
        k, i, a = 10.0, 0.01, 50.0
        width = 1000.0
        expected_q = k * (a * width) * i
        
        result = integrator.calculate_flow(GroundwaterInput(
            hydraulic_conductivity_m_day=k,
            hydraulic_gradient=i,
            aquifer_thickness_m=a,
            aquifer_width_m=width,
        ))
        assert abs(result.flow_rate_m3_day - expected_q) < 0.1
    
    def test_seepage_greater_than_darcy(self, integrator):
        """v_seepage = v_darcy / porosity"""
        result = integrator.calculate_flow(GroundwaterInput(
            hydraulic_conductivity_m_day=10.0,
            hydraulic_gradient=0.01,
            aquifer_thickness_m=50.0,
            porosity=0.3,
        ))
        assert result.seepage_velocity_m_day > result.darcy_velocity_m_day
    
    def test_higher_k_more_flow(self, integrator):
        low = integrator.calculate_flow(GroundwaterInput(1.0, 0.01, 50.0))
        high = integrator.calculate_flow(GroundwaterInput(100.0, 0.01, 50.0))
        assert high.flow_rate_m3_day > low.flow_rate_m3_day
    
    def test_zero_gradient_no_flow(self, integrator):
        result = integrator.calculate_flow(GroundwaterInput(10.0, 0.0, 50.0))
        assert result.flow_rate_m3_day == 0.0
    
    def test_invalid_k(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_flow(GroundwaterInput(-10.0, 0.01, 50.0))
    
    def test_invalid_porosity(self, integrator):
        with pytest.raises(ValueError):
            integrator.calculate_flow(GroundwaterInput(10.0, 0.01, 50.0, porosity=1.5))
    
    def test_estimate_k_clay(self, integrator):
        k = integrator.estimate_k("clay")
        assert k < 0.01
    
    def test_estimate_k_gravel(self, integrator):
        k = integrator.estimate_k("gravel")
        assert k > 50


# ============================================================
# Unified Analysis Tests
# ============================================================

class TestUnifiedWaterAnalysis:
    """Test Unified Water Analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return UnifiedWaterAnalyzer()
    
    def test_unified_analysis(self, analyzer):
        result = analyzer.analyze(
            precipitation_mm=100.0,
            et0_mm=60.0,
            soil_type="loam",
        )
        assert isinstance(result, UnifiedWaterAnalysis)
        assert result.water_balance is not None
        assert result.runoff is not None
        assert result.groundwater is not None
    
    def test_recommendations_generated(self, analyzer):
        result = analyzer.analyze(
            precipitation_mm=50.0,
            et0_mm=200.0,
            soil_type="clay",
        )
        assert len(result.recommendations) > 0
    
    def test_status_determination(self, analyzer):
        result = analyzer.analyze(
            precipitation_mm=100.0,
            et0_mm=60.0,
        )
        assert result.overall_status in [
            "balanced", "deficit", "critical_deficit",
            "excess_runoff", "warning", "error",
        ]
    
    def test_arid_scenario(self, analyzer):
        """Arid: low P, high ET"""
        result = analyzer.analyze(
            precipitation_mm=50.0,
            et0_mm=300.0,
            soil_type="sand",
        )
        assert result.overall_status in ["deficit", "critical_deficit"]
    
    def test_humid_scenario(self, analyzer):
        """Humid: high P, moderate ET"""
        result = analyzer.analyze(
            precipitation_mm=1500.0,
            et0_mm=800.0,
            soil_type="loam",
        )
        assert result.water_balance.surface_runoff_mm > 0 or \
               result.water_balance.deep_percolation_mm > 0
    
    def test_handles_error(self, analyzer):
        """Should handle errors gracefully"""
        result = analyzer.analyze(
            precipitation_mm=-100.0,  # Invalid
            et0_mm=60.0,
        )
        assert result.overall_status == "error"
