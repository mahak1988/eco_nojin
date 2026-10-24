"""Unit-consistency tests for engine/hydroma/water_productivity.py.

These tests check the unit and mass-balance correctness of the FAO
WaPOR water-productivity definition WP = Y / ET (kg/m3) per spec section
8.3 ("موازنه جرم"). They verify the unit bridge 1 mm over 1 ha = 10 m3,
the worked example 5000 kg/ha with 500 mm ET = 1.0 kg/m3, agreement with
the conversion computed the long way, and the input validation. They are
NOT independent scientific validation: no published benchmark values
are used or available offline, so these are correctness tests of the
implemented equation only.
"""

from __future__ import annotations

import pytest

from engine.hydroma.water_productivity import (
    M3_PER_MM_PER_HA,
    WP_KG_PER_M3_PER_MM_HA,
    water_productivity,
    water_productivity_from_m3,
)


def test_worked_example_5000_kg_ha_with_500_mm_et_is_1_kg_per_m3():
    # verified unit bridge: 1 mm over 1 ha = 0.001 m x 10 000 m2 = 10 m3
    assert 0.001 * 10000.0 == 10.0
    assert M3_PER_MM_PER_HA == 10.0
    assert WP_KG_PER_M3_PER_MM_HA == 1.0 / 10.0

    yield_kg_ha = 5000.0
    et_mm = 500.0

    volume_m3_per_ha = et_mm * M3_PER_MM_PER_HA
    assert volume_m3_per_ha == 5000.0

    assert water_productivity(yield_kg_ha, et_mm) == 1.0
    assert water_productivity_from_m3(yield_kg_ha, volume_m3_per_ha) == 1.0


def test_unit_consistency_with_long_way_volume():
    yield_kg_ha = 3200.0
    et_mm = 420.0

    wp = water_productivity(yield_kg_ha, et_mm)

    # the long way: depth in m over a hectare gives the consumed volume
    depth_m = et_mm * 0.001
    volume_m3_per_ha = depth_m * 10000.0
    assert volume_m3_per_ha == pytest.approx(et_mm * M3_PER_MM_PER_HA, abs=1e-9)

    wp_long_way = yield_kg_ha / volume_m3_per_ha
    assert wp == pytest.approx(wp_long_way, rel=1e-12, abs=0.0)
    assert water_productivity_from_m3(yield_kg_ha, volume_m3_per_ha) == pytest.approx(
        wp_long_way, rel=1e-12, abs=0.0
    )


@pytest.mark.parametrize("et_mm", [0.0, -0.5, -100.0])
def test_non_positive_et_raises_value_error(et_mm):
    with pytest.raises(ValueError):
        water_productivity(5000.0, et_mm)


def test_zero_volume_in_m3_variant_raises_value_error():
    with pytest.raises(ValueError):
        water_productivity_from_m3(5000.0, 0.0)


@pytest.mark.parametrize("yield_kg_ha", [-0.1, -5000.0])
def test_negative_yield_raises_value_error(yield_kg_ha):
    with pytest.raises(ValueError):
        water_productivity(yield_kg_ha, 500.0)
    with pytest.raises(ValueError):
        water_productivity_from_m3(yield_kg_ha, 5000.0)
