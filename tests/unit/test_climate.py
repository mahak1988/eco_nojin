"""Test climate and ET0 calculations."""
import pytest
from engine.hydroma.climate.et_calculator import calc_et0_hargreaves

def test_hargreaves_et0_normal_conditions():
    """Verify ET0 calculation under normal agricultural conditions."""
    # Typical values for a spring day
    et0 = calc_et0_hargreaves(t_min=10.0, t_max=25.0, t_mean=17.5, ra_mj=15.0)
    assert et0 > 0
    # Expected approx: 0.0023 * 0.408 * 15 * 35.3 * 3.87 ~= 1.92 mm/day
    assert 1.5 < et0 < 2.5

def test_hargreaves_et0_invalid_temps():
    """Verify that invalid temperature inputs raise ValueError."""
    with pytest.raises(ValueError):
        calc_et0_hargreaves(t_min=20.0, t_max=15.0, t_mean=17.5, ra_mj=15.0)
