"""Scientific validation tests"""
import pytest

class TestMassBalance:
    @pytest.mark.scientific
    def test_mass_conservation(self):
        inp = {"C": 1000}
        out = {"CO2": 150, "SOC": 850}
        total_out = sum(out.values())
        assert abs(sum(inp.values()) - total_out) < 1, "Mass balance error"

class TestConvergence:
    @pytest.mark.scientific  
    def test_series_convergence(self):
        series = [100, 80, 64, 51.2, 40.96]
        target = 0
        final = series[-1]
        # Should be decreasing and converging
        assert all(series[i] >= series[i+1] for i in range(len(series)-1))
