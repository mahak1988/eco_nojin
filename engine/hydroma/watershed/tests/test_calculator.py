"""
Tests for WatershedCalculator enhancements - Phase 3
=====================================================
"""

import pytest
import numpy as np

from engine.hydroma.watershed.calculator import (
    calculate_strahler_order,
    calculate_horton_ratios,
    calculate_kirpich_tc,
    muskingum_route,
)


class TestStrahlerOrdering:
    """Test Strahler stream ordering."""
    
    def test_simple_network(self):
        """Test simple Y-shaped network."""
        network = {
            "nodes": [1, 2, 3, 4],
            "edges": [
                {"id": "e1", "from_node": 1, "to_node": 3},
                {"id": "e2", "from_node": 2, "to_node": 3},
                {"id": "e3", "from_node": 3, "to_node": 4},
            ]
        }
        
        result = calculate_strahler_order(network)
        
        assert result["max_order"] == 2
        assert result["stream_count"] == 3
        # e1 and e2 are order 1, e3 should be order 2
        assert result["orders"]["e1"] == 1
        assert result["orders"]["e2"] == 1
        assert result["orders"]["e3"] == 2
    
    def test_linear_network(self):
        """Test linear (non-branching) network."""
        network = {
            "nodes": [1, 2, 3],
            "edges": [
                {"id": "e1", "from_node": 1, "to_node": 2},
                {"id": "e2", "from_node": 2, "to_node": 3},
            ]
        }
        
        result = calculate_strahler_order(network)
        
        # All should be order 1 (no branching)
        assert result["max_order"] == 1
    
    def test_empty_network(self):
        """Test empty network."""
        network = {"nodes": [], "edges": []}
        result = calculate_strahler_order(network)
        
        assert result["max_order"] == 0
        assert result["stream_count"] == 0


class TestHortonRatios:
    """Test Horton ratio calculations."""
    
    def test_basic_ratios(self):
        """Test basic Horton ratio calculation."""
        strahler = {
            "orders": {"e1": 1, "e2": 1, "e3": 1, "e4": 2, "e5": 2, "e6": 3},
            "max_order": 3,
        }
        
        lengths = {
            "e1": 1000, "e2": 1000, "e3": 1000,
            "e4": 2000, "e5": 2000,
            "e6": 4000,
        }
        
        result = calculate_horton_ratios(strahler, lengths)
        
        assert result["Rb"] > 0  # Bifurcation ratio
        assert result["Rl"] > 0  # Length ratio
    
    def test_single_order(self):
        """Test with single order network."""
        strahler = {"orders": {"e1": 1, "e2": 1}, "max_order": 1}
        lengths = {"e1": 1000, "e2": 1000}
        
        result = calculate_horton_ratios(strahler, lengths)
        
        # No ratios for single order
        assert result["Rb"] == 0


class TestKirpichTC:
    """Test Kirpich time of concentration."""
    
    def test_typical_values(self):
        """Test with typical watershed values."""
        length_m = 5000.0  # 5 km
        slope = 0.02  # 2%
        
        tc = calculate_kirpich_tc(length_m, slope)
        
        # Should be reasonable (tens of minutes to hours)
        assert tc > 0
        assert tc < 1000  # Less than ~16 hours
    
    def test_zero_length(self):
        """Test with zero length."""
        tc = calculate_kirpich_tc(0.0, 0.02)
        assert tc == 0.0
    
    def test_zero_slope(self):
        """Test with zero slope."""
        tc = calculate_kirpich_tc(5000.0, 0.0)
        assert tc == 0.0


class TestMuskingumRouting:
    """Test Muskingum routing."""
    
    def test_simple_routing(self):
        """Test simple inflow routing."""
        # Create simple triangular inflow
        inflow = np.array([0, 10, 50, 100, 50, 10, 0], dtype=float)
        
        K = 2.0  # hours
        x = 0.2
        dt = 1.0  # hours
        
        outflow = muskingum_route(inflow, K, x, dt)
        
        # Outflow should be delayed and attenuated
        assert len(outflow) == len(inflow)
        assert outflow[0] == inflow[0]  # Initial condition
        assert np.max(outflow) < np.max(inflow)  # Attenuation
    
    def test_conservation(self):
        """Test mass conservation."""
        inflow = np.array([0, 10, 50, 100, 50, 10, 0, 0, 0, 0], dtype=float)
        
        K = 1.0
        x = 0.2
        dt = 1.0
        
        outflow = muskingum_route(inflow, K, x, dt)
        
        # Total volume should be approximately conserved
        inflow_volume = np.sum(inflow) * dt
        outflow_volume = np.sum(outflow) * dt
        
        # Allow 5% error due to numerical approximation
        assert abs(outflow_volume - inflow_volume) / inflow_volume < 0.05
    
    def test_invalid_parameters(self):
        """Test with invalid parameters."""
        inflow = np.array([0, 10, 50, 100, 50, 10, 0], dtype=float)
        
        # K <= 0 should return copy
        outflow = muskingum_route(inflow, K=0.0, x=0.2, dt=1.0)
        np.testing.assert_array_equal(outflow, inflow)
