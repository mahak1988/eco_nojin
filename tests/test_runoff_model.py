"""Unit tests for RunoffCalculator."""

import pytest
from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput


def test_runoff_calculator_scs_cn():
    # Arrange
    calculator = RunoffCalculator()
    input_data = RunoffInput(precipitation_mm=50.0, curve_number=70, area_ha=10.0, method="SCS-CN")

    # Act
    result = calculator.execute(input_data)

    # Assert
    assert result.volume_m3 >= 0
    # Expected volume (SI units): S = 25400/70 - 254 = 108.857 mm
    # Ia = 0.2 * S = 21.771 mm
    # Q = (P-Ia)^2/(P+0.8*S) = (50-21.771)^2/(50+87.086) = 5.813 mm
    # Volume = Q * A * 10 = 5.813 * 10 * 10 = 581.3 m3
    assert abs(result.volume_m3 - 581.3) < 1


def test_runoff_calculator_rational():
    # Arrange
    calculator = RunoffCalculator()
    input_data = RunoffInput(
        precipitation_mm=100.0, area_ha=5.0, method="Rational", rational_coefficient=0.6
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
