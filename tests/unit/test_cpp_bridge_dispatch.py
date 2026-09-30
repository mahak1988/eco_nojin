"""Tests for the array backend dispatch in the C++ bridge.

The ``*_array`` symbols bind ``const std::vector<double>&``, so pybind11 converts
NumPy arrays element-by-element through Python objects. That conversion cost
scales with the ROW count, which made a (N, 1) request -- the natural shape for a
reflectance time series -- catastrophically slow: 6.77 s at N=1e6 versus
0.010 s for the same elements arranged as (250000, 2). Because the shape is
chosen by the caller, this was a remote CPU-exhaustion vector.

Array calls are therefore routed Numba -> C++ -> NumPy. The Numba
``parallel=True`` kernels were measured 3.5x faster than C++ on well-behaved 2-D
input and 1100-1450x faster on the pathological shape, with bit-identical
results. These tests pin the dispatch decision, the closed latency cliff and the
numerical parity that makes the reordering safe.
"""

from __future__ import annotations

import numpy as np
import pytest

import engine.hydroma.cpp_bridge as bridge


@pytest.fixture(autouse=True)
def _clean_telemetry():
    bridge.reset_telemetry()
    yield
    bridge.reset_telemetry()


def _bands(n: int, shape=None) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    shape = shape or (n,)
    return (
        rng.uniform(0.01, 0.3, shape),
        rng.uniform(0.2, 0.9, shape),
    )


# --------------------------------------------------------------------------
# Dispatch decision
# --------------------------------------------------------------------------


def test_array_call_uses_numba_when_available():
    red, nir = _bands(50_000)
    if not bridge._NUMBA_AVAILABLE:
        pytest.skip("Numba is not installed")

    bridge.ndvi(red, nir)

    assert bridge.get_telemetry()["numba_calls"] == 1
    assert bridge.get_telemetry()["cpp_calls"] == 0


def test_row_count_no_longer_dominates_cost():
    """The (N,1) cliff is the regression: cost must track elements, not rows."""
    red_flat, nir_flat = _bands(400_000, (400_000,))
    red_col, nir_col = _bands(400_000, (400_000, 1))
    red_wide, nir_wide = _bands(400_000, (200_000, 2))

    import time

    def best(fn, *a):
        fn(*a)
        return min(
            (lambda: (lambda t0: time.perf_counter() - t0)(time.perf_counter()))()
            if False
            else _timed(fn, a)
            for _ in range(2)
        )

    t_flat = _timed(bridge.ndvi, (red_flat, nir_flat))
    t_col = _timed(bridge.ndvi, (red_col, nir_col))
    t_wide = _timed(bridge.ndvi, (red_wide, nir_wide))

    # The (N,1) case must no longer cost orders of magnitude more than the same
    # elements in a wide layout. Budget: 10x, was ~270x.
    assert t_col < max(t_wide, t_flat) * 10, (
        f"row-count penalty returned: (N,1)={t_col:.5f}s vs (N/2,2)={t_wide:.5f}s"
    )


def _timed(fn, args) -> float:
    import time

    fn(*args)
    best = 1e9
    for _ in range(3):
        t0 = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - t0)
    return best


def test_scalar_call_still_uses_cpp():
    """Scalar calls have no conversion overhead, so C++ keeps them."""
    if not bridge.is_cpp_available():
        pytest.skip("C++ extension is not built")

    bridge.ndvi(0.1, 0.8)

    assert bridge.get_telemetry()["cpp_calls"] == 1
    assert bridge.get_telemetry()["numba_calls"] == 0


def test_telemetry_exposes_all_three_backends():
    keys = set(bridge.get_telemetry())

    assert {"numba_calls", "cpp_calls", "fallback_calls"} <= keys


# --------------------------------------------------------------------------
# Numerical parity: the reordering is only safe if the results match
# --------------------------------------------------------------------------


@pytest.mark.parametrize("shape", [(1000,), (100, 10)])
def test_1d_and_2d_input_are_supported_and_correct(shape):
    red, nir = _bands(int(np.prod(shape)), shape)

    out = bridge.ndvi(red, nir)
    expected = (nir - red) / (nir + red)

    assert out.shape == shape
    np.testing.assert_allclose(out, expected, rtol=1e-12, atol=1e-12)


def test_3d_input_is_rejected_with_a_clear_message():
    """The kernels only support 1-D/2-D; a 3-D request must fail loudly."""
    red, nir = _bands(1000, (10, 10, 10))

    with pytest.raises(ValueError, match="1-D or 2-D"):
        bridge.ndvi(red, nir)


def test_bridge_matches_cpp_and_numba_bitwise():
    """Any backend choice must produce the same number."""
    red, nir = _bands(20_000, (200, 100))

    via_bridge = bridge.ndvi(red, nir)
    via_cpp = bridge._hydroma_core.ndvi_array(red.reshape(-1), nir.reshape(-1))
    via_numba = bridge._numba_indices.ndvi_fast(red, nir)
    via_numpy = (nir - red) / (nir + red)

    np.testing.assert_array_equal(via_bridge.reshape(-1), via_cpp)
    np.testing.assert_array_equal(via_bridge.reshape(-1), via_numba.reshape(-1))
    np.testing.assert_allclose(via_bridge, via_numpy, rtol=1e-12, atol=1e-12)


def test_zero_denominator_stays_zero_across_dispatch():
    red = np.zeros(10)
    nir = np.zeros(10)

    out = bridge.ndvi(red, nir)

    assert np.all(out == 0.0)
    assert not np.any(np.isnan(out))


@pytest.mark.parametrize(
    ("name", "args_builder"),
    [
        ("ndvi", lambda r, n: (r, n)),
        ("evi", lambda r, n: (r, n, r)),
        ("savi", lambda r, n: (r, n)),
        ("nbr", lambda r, n: (n, r)),
    ],
)
def test_every_numba_twin_preserves_range(name, args_builder):
    red, nir = _bands(2000)
    out = getattr(bridge, name)(*args_builder(red, nir))

    assert out.shape == (2000,)
    assert np.all(np.isfinite(out))
    assert np.all(out >= -1.0000001)
    assert np.all(out <= 1.0000001)
