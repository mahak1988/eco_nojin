"""Unit tests for RunoffCalculator."""
import pytest
from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput

def test_runoff_calculator_scs_cn():
    # Arrange
    calculator = RunoffCalculator()
    input_data = RunoffInput(
        precipitation_mm=50.0,
        curve_number=70,
        area_ha=10.0,
        method="SCS-CN"
    )

    # Act
    result = calculator.execute(input_data)

    # Assert
    assert result.volume_m3 >= 0 # Volume should be non-negative
    # Expected volume calculation: S = (1000/70)-10 = 4.2857, Ia = 0.2*S = 0.8571
    # P > Ia (50 > 0.8571), so Q = ((50-0.8571)^2) / (50 - 0.8571 + 4.2857) = 2371.9 / 53.4286 = 44.39 mm
    # Volume = 44.39 mm * 10 ha * 10000 m2/ha * 1m/1000mm = 4439 m3
    assert abs(result.volume_m3 - 4439) < 1 # Allow small rounding error

def test_runoff_calculator_rational():
    # Arrange
    calculator = RunoffCalculator()
    input_data = RunoffInput(
        precipitation_mm=100.0,
        area_ha=5.0,
        method="Rational",
        rational_coefficient=0.6
    )

    # Act
    result = calculator.execute(input_data)

    # Assert
    assert result.volume_m3 >= 0
    assert result.peak_flow_m3s >= 0
    # Volume: 100 mm * 5 ha * 10000 * 1/1000 = 5000 m3
    expected_vol = 5000.0
    assert abs(result.volume_m3 - expected_vol) < 1
    # Peak flow (assuming 1 hr duration): (0.6 * 100 mm/hr * 5 ha) / 360 = 0.833 m3/s
    expected_peak = (0.6 * 100 * 5) / 360
    assert abs(result.peak_flow_m3s - expected_peak) < 0.01
