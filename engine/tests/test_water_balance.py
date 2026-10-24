"""Unit and mass-balance correctness tests for engine/hydroma/water_balance.py.

These tests check the unit and mass-balance correctness of the water
balance P = ET + Q + dS (all terms mm per period) per spec section 8.3
("موازنه جرم"). They verify that the bucket's mass closes, that storage
never goes negative, and that water removed by the clamp is reported in
``excess_mm`` rather than silently dropped. They are NOT independent
scientific validation: no published benchmark series is used or
available offline, so these are correctness tests of the implemented
equation only.
"""

from __future__ import annotations

import numpy as np

from engine.hydroma.water_balance import water_balance

CLOSURE_TOL_MM = 1e-9


def test_mass_closure_on_deterministic_series():
    precip = [30.3, 12.7, 0.0, 45.5, 12.15, 8.65]
    et = [18.1, 22.6, 15.05, 9.3, 26.55, 11.2]
    runoff = [6.2, 4.35, 3.0, 7.55, 2.1, 9.05]
    storage0 = 60.0

    result = water_balance(precip, et, runoff, storage0=storage0)

    storage = result["storage"]
    closure_mm = result["closure_mm"]

    assert storage.shape == (6,)
    assert closure_mm.shape == (6,)

    # no clamp happened on this series
    assert np.all(storage > 0.0)
    assert np.array_equal(result["excess_mm"], np.zeros(6))

    # storage is exactly the clamped recurrence evaluated step by step
    expected_storage = []
    prev = storage0
    for p, e, q in zip(precip, et, runoff, strict=True):
        prev = max(0.0, prev + p - e - q)
        expected_storage.append(prev)
    assert np.allclose(storage, expected_storage, rtol=0.0, atol=CLOSURE_TOL_MM)

    # mass closure P = ET + Q + dS holds to below 1e-9 mm
    assert np.all(np.abs(closure_mm) < CLOSURE_TOL_MM)
    assert result["max_abs_closure"] < CLOSURE_TOL_MM


def test_storage_going_negative_reports_excess_and_closes():
    precip = [10.0, 0.0, 0.0]
    et = [50.0, 50.0, 50.0]
    runoff = [0.0, 0.0, 0.0]
    storage0 = 100.0

    result = water_balance(precip, et, runoff, storage0=storage0)

    storage = result["storage"]
    excess_mm = result["excess_mm"]

    assert np.array_equal(storage, [60.0, 10.0, 0.0])
    assert np.all(storage >= 0.0)

    # the clamp only bites in the last period
    assert np.array_equal(excess_mm[:2], [0.0, 0.0])
    assert excess_mm[2] > 0.0

    # excess equals the exact overflow: demand minus available water
    available = storage[1] + precip[2]
    overflow = et[2] + runoff[2] - available
    assert overflow == 40.0
    assert excess_mm[2] == overflow

    # despite the clamp the mass balance still closes to zero
    assert result["max_abs_closure"] < 1e-9
    assert np.all(np.abs(result["closure_mm"]) < 1e-9)


def test_all_zero_fluxes_give_zero_storage_change():
    n_periods = 5

    result = water_balance(
        [0.0] * n_periods, [0.0] * n_periods, [0.0] * n_periods, storage0=0.0
    )

    assert np.array_equal(result["storage"], np.zeros(n_periods))
    assert np.array_equal(result["excess_mm"], np.zeros(n_periods))
    assert np.array_equal(result["closure_mm"], np.zeros(n_periods))
    assert result["max_abs_closure"] == 0.0

    # a non-zero initial storage is preserved unchanged by zero fluxes
    result_kept = water_balance([0.0] * 3, [0.0] * 3, [0.0] * 3, storage0=15.0)
    assert np.array_equal(result_kept["storage"], [15.0, 15.0, 15.0])
    assert np.array_equal(result_kept["excess_mm"], np.zeros(3))
    assert result_kept["max_abs_closure"] == 0.0
