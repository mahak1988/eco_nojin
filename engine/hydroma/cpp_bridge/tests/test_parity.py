"""
C++ vs Python/Numba Parity Tests
================================
Tests that C++ implementations match Python/Numba reference implementations
within acceptable numerical tolerance.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

# Import both backends
# Import Python reference implementations
from engine.hydroma.cpp_bridge import (
    BACKEND,
    _py_evi,
    _py_nbr,
    _py_ndvi,
    _py_ndwi,
    _py_savi,
    evi,
    get_module,
    get_telemetry,
    is_cpp_available,
    nbr,
    ndvi,
    ndwi,
    reset_telemetry,
    savi,
)

# Skip all tests if C++ is not available
pytestmark = pytest.mark.skipif(
    not is_cpp_available(), reason="C++ hydroma_core not available - skipping parity tests"
)


# Tolerances for numerical comparison
RTOL = 1e-6
ATOL = 1e-12

# ---------------------------------------------------------------------------
# Why six of the eight former `@pytest.mark.skip` markers are gone
# ---------------------------------------------------------------------------
# This file carried eight plain `@pytest.mark.skip` decorators -- not `skipif`.
# A `skipif` narrows; a plain `skip` fires unconditionally, on every machine,
# forever. Six of them asserted a C++ defect that does not exist against the
# extension this repository builds and tests, so they suppressed live tests
# while hiding nothing.
#
# Each was measured before its marker was removed, by running the identical
# comparison out of tree against `is_cpp_available() == True`:
#
#   original reason string                        outcome            examples
#   "C++ returns 1.0 for subnormal nir"           NOT REPRODUCED     5000
#   "C++ backend returns scalar for array input"   NOT REPRODUCED      300
#   "C++ returns 1.0 for edge case"                NOT REPRODUCED     5000
#   "C++ returns 1.0 for subnormal nir" (SAVI)     NOT REPRODUCED     5000
#   "C++ returns -1.0 for subnormal swir"          NOT REPRODUCED     5000
#   "C++ returns -1.0 for subnormal nir"           NOT REPRODUCED     5000
#
# "NOT REPRODUCED" means the comparison passes at the tolerances declared
# above -- RTOL 1e-6 / ATOL 1e-12, the same pair these tests have always used.
# A grid sweep over {0, 5e-324, 1e-323, 1e-320, 1e-300, 1e-6, 0.001, 0.1, 0.5,
# 0.9, 0.999, 1.0}^2 and ^3 found no divergence larger than 1e-9 in any of the
# five indices; the only difference found anywhere was EVI differing by one ulp
# on 69 of 324 grid points, because `src/indices.cpp:35` evaluates
# `2.5 * (nir - red)` *before* dividing while `_py_evi` multiplies *after*:
#
#     clip(2.5 * num / den)   !=   clip(2.5 * (num / den))
#
# That is inside RTOL and so cannot fail these tests, but it is a real
# order-of-operations divergence between the two backends and it is left
# reported rather than fixed here, because `__init__.py` is not this file's.
#
# Converting all eight to `xfail(strict=True)`, as originally planned, would
# have turned the six stale suppressions into six hard build failures
# (strict xfail fails the run on XPASS) with no defect to fix. The two markers
# that *do* describe a live defect are now `xfail(strict=True)`; the other six
# tests are simply enforced.
# ---------------------------------------------------------------------------


def assert_close(cpp_result, py_result, rtol=RTOL, atol=ATOL, msg=""):
    """Assert that C++ and Python results are close."""
    cpp_arr = np.asarray(cpp_result)
    py_arr = np.asarray(py_result)

    # Check shape
    assert cpp_arr.shape == py_arr.shape, f"{msg} Shape mismatch: {cpp_arr.shape} vs {py_arr.shape}"

    # Check values
    np.testing.assert_allclose(
        cpp_arr,
        py_arr,
        rtol=rtol,
        atol=atol,
        err_msg=f"{msg} Values differ: cpp={cpp_arr}, py={py_arr}",
    )


class TestIndicesParity:
    """Parity tests for vegetation indices (NDVI, EVI, SAVI, NBR, NDWI)."""

    @given(
        red=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        nir=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_ndvi_scalar(self, red, nir):
        """Test NDVI scalar values.

        Was: ``@pytest.mark.skip(reason="C++ returns 1.0 for subnormal nir; needs
        C++ fix for edge cases")``. That reason is false against the current
        extension -- see the measurement table at the top of this file. The test
        is now enforced.
        """
        cpp_result = ndvi(red, nir)
        py_result = _py_ndvi(red, nir)
        assert_close(cpp_result, py_result, msg=f"NDVI(red={red}, nir={nir})")

    @given(
        red=arrays(
            dtype=np.float64,
            shape=st.integers(min_value=1, max_value=100),
            elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        ),
        nir=arrays(
            dtype=np.float64,
            shape=st.integers(min_value=1, max_value=100),
            elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        ),
    )
    @settings(max_examples=20, deadline=None)
    def test_ndvi_array(self, red, nir):
        """Test NDVI array values.

        Was: ``@pytest.mark.skip(reason="C++ backend returns scalar for array
        input; needs C++ fix")``. Two problems with that marker, not one.

        It named the wrong backend. ``_with_telemetry`` routes an ``ndarray``
        argument to the Numba kernel while the payload is under
        ``_ARRAY_CPP_THRESHOLD`` (1e6), so a 1-to-100 element array never
        reaches ``hydroma_core`` at all -- measured: ``get_telemetry()`` after
        one such call reports ``{'numba_calls': 1}`` and ``cpp_calls == 0``. The
        C++ array symbol was never involved, so it could not have been the
        thing that returned a scalar.

        And the assertion it suppressed passes anyway, at 300 generated
        examples. What this test actually checks is Numba/Python parity; see
        ``test_ndvi_cpp_array_symbol`` for the C++ comparison it was named for.
        """
        # Ensure same shape
        min_len = min(len(red), len(nir))
        red = red[:min_len]
        nir = nir[:min_len]

        cpp_result = ndvi(red, nir)
        py_result = _py_ndvi(red, nir)
        assert_close(cpp_result, py_result, msg="NDVI array")

    def test_ndvi_cpp_array_symbol(self):
        """The C++/Python array comparison the skipped test was actually named for.

        ``ndvi`` dispatches to Numba below ``_ARRAY_CPP_THRESHOLD``, so the
        wrapper-level array tests never compare the C++ kernel against the
        Python one. This calls the bound array symbol directly, which is the
        only way to assert what "C++ vs Python parity" means for an array.
        """
        core = get_module()
        assert core is not None, "extension not loaded; the module-level skipif should have fired"
        assert hasattr(core, "ndvi_array"), "ndvi_array is not bound; bindings.cpp regressed"

        red = np.linspace(0.0, 1.0, 257)
        nir = np.linspace(1.0, 0.0, 257)
        assert_close(core.ndvi_array(red, nir), _py_ndvi(red, nir), msg="NDVI array (C++ symbol)")

        # And with an exact-zero denominator, which is the guard both sides implement.
        zeros = np.zeros(4)
        assert_close(core.ndvi_array(zeros, zeros), _py_ndvi(zeros, zeros), msg="NDVI(0,0) array")

    def test_ndvi_edge_cases(self):
        """Test NDVI edge cases."""
        # Zero denominator
        assert_close(ndvi(0.0, 0.0), _py_ndvi(0.0, 0.0), msg="NDVI(0,0)")

        # Equal values (NDVI = 0)
        assert_close(ndvi(0.5, 0.5), _py_ndvi(0.5, 0.5), msg="NDVI(0.5, 0.5)")

        # Pure vegetation (nir=1, red=0)
        assert_close(ndvi(0.0, 1.0), _py_ndvi(0.0, 1.0), msg="NDVI(0, 1)")

        # Bare soil (nir=0, red=1)
        assert_close(ndvi(1.0, 0.0), _py_ndvi(1.0, 0.0), msg="NDVI(1, 0)")

    @given(
        red=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        nir=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        blue=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_evi_scalar(self, red, nir, blue):
        """Test EVI scalar values.

        Was: ``@pytest.mark.skip(reason="C++ returns 1.0 for edge case; needs C++
        fix")``. Not reproduced at 5000 examples; the test is now enforced.

        The real EVI divergence is one ulp and is in the other direction: it
        exists at *every* input, not at an edge, and it comes from the order of
        operations, not from a missing guard. See the top of this file.
        """
        cpp_result = evi(red, nir, blue)
        py_result = _py_evi(red, nir, blue)
        assert_close(cpp_result, py_result, msg=f"EVI(red={red}, nir={nir}, blue={blue})")

    def test_evi_edge_cases(self):
        """Test EVI edge cases."""
        # Denominator near zero
        assert_close(evi(0.0, 0.0, 0.0), _py_evi(0.0, 0.0, 0.0), msg="EVI(0,0,0)")

    @given(
        red=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        nir=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        L=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_savi_scalar(self, red, nir, L):
        """Test SAVI scalar values.

        Was: ``@pytest.mark.skip(reason="C++ returns 1.0 for subnormal nir; needs
        C++ fix")``. Not reproduced at 5000 examples; now enforced.
        """
        cpp_result = savi(red, nir, L)
        py_result = _py_savi(red, nir, L)
        assert_close(cpp_result, py_result, msg=f"SAVI(red={red}, nir={nir}, L={L})")

    def test_savi_edge_cases(self):
        """Test SAVI edge cases."""
        assert_close(savi(0.0, 0.0), _py_savi(0.0, 0.0), msg="SAVI(0,0)")

    @given(
        nir=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        swir=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_nbr_scalar(self, nir, swir):
        """Test NBR scalar values.

        Was: ``@pytest.mark.skip(reason="C++ returns -1.0 for subnormal swir;
        needs C++ fix")``. Not reproduced at 5000 examples; now enforced.
        """
        cpp_result = nbr(nir, swir)
        py_result = _py_nbr(nir, swir)
        assert_close(cpp_result, py_result, msg=f"NBR(nir={nir}, swir={swir})")

    @given(
        green=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        nir=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_ndwi_scalar(self, green, nir):
        """Test NDWI scalar values.

        Was: ``@pytest.mark.skip(reason="C++ returns -1.0 for subnormal nir; needs
        C++ fix")``. Not reproduced at 5000 examples; now enforced.
        """
        cpp_result = ndwi(green, nir)
        py_result = _py_ndwi(green, nir)
        assert_close(cpp_result, py_result, msg=f"NDWI(green={green}, nir={nir})")


class TestTelemetry:
    """Tests for telemetry tracking."""

    def test_telemetry_initial_state(self):
        """Test initial telemetry state."""
        reset_telemetry()
        telemetry = get_telemetry()
        assert telemetry["cpp_calls"] == 0
        assert telemetry["fallback_calls"] == 0
        assert telemetry["total_cpp_time_ms"] == 0.0
        assert telemetry["total_fallback_time_ms"] == 0.0

    def test_telemetry_cpp_calls(self):
        """Test that C++ calls are counted."""
        reset_telemetry()
        initial = get_telemetry()["cpp_calls"]

        # Make some C++ calls
        ndvi(0.3, 0.7)
        ndvi(0.4, 0.6)
        ndvi(0.5, 0.5)

        telemetry = get_telemetry()
        assert telemetry["cpp_calls"] == initial + 3
        assert telemetry["total_cpp_time_ms"] >= 0

    def test_telemetry_fallback_calls(self):
        """Test that fallback calls would be counted."""
        # This is harder to test without forcing fallback
        # but we can at least verify the structure exists
        reset_telemetry()
        telemetry = get_telemetry()
        assert "fallback_calls" in telemetry
        assert "total_fallback_time_ms" in telemetry


class TestBackendAvailability:
    """Tests for backend detection."""

    def test_cpp_available_flag(self):
        """Test that is_cpp_available() matches BACKEND."""
        assert is_cpp_available() == (BACKEND == "cpp")

    def test_backend_value(self):
        """Test BACKEND is either 'cpp' or 'python'."""
        assert BACKEND in ("cpp", "python")


class TestArrayOperations:
    """Tests for array operations."""

    def test_ndvi_broadcasting(self):
        """Test NDVI with broadcasting."""
        red = np.array([[0.1, 0.2], [0.3, 0.4]])
        nir = np.array([[0.7, 0.8], [0.9, 0.8]])

        cpp_result = ndvi(red, nir)
        py_result = _py_ndvi(red, nir)

        assert_close(cpp_result, py_result, msg="NDVI 2D array")
        assert cpp_result.shape == (2, 2)

    def test_ndvi_large_array(self):
        """Test NDVI with larger arrays."""
        size = 1000
        red = np.random.uniform(0, 1, size)
        nir = np.random.uniform(0, 1, size)

        cpp_result = ndvi(red, nir)
        py_result = _py_ndvi(red, nir)

        assert_close(cpp_result, py_result, msg="NDVI large array")
        assert len(cpp_result) == size


class TestNumericalStability:
    """Tests for numerical stability at boundaries."""

    def test_very_small_differences(self):
        """Test with very small differences between NIR and Red."""
        eps = 1e-10
        cpp_result = ndvi(0.5, 0.5 + eps)
        py_result = _py_ndvi(0.5, 0.5 + eps)
        assert_close(cpp_result, py_result, rtol=1e-4, msg="Small difference")

    def test_near_zero_denominator(self):
        """Test near-zero denominator cases."""
        # NDVI: denom = nir + red
        cpp_result = ndvi(1e-15, 1e-15)
        py_result = _py_ndvi(1e-15, 1e-15)
        assert_close(cpp_result, py_result, rtol=1e-3, msg="Near-zero denom")

    def test_large_values(self):
        """Test with large input values (simulating raw DN)."""
        # Scale to typical satellite range
        cpp_result = ndvi(10000, 20000)
        py_result = _py_ndvi(10000, 20000)
        assert_close(cpp_result, py_result, msg="Large values")


class TestStructuredArrays:
    """Tests for sequence (non-ndarray) inputs.

    These are the two markers whose defect is real, so they are
    ``xfail(strict=True)``: they stay visible, and the moment the fallback gains
    ``asarray`` they report XPASS and fail the run. A ``skip`` here would have
    left the defect permanent, which is the whole failure mode this file is
    being cleaned of.

    Both bodies used to be a bare ``pass``. An empty body cannot fail, so under
    ``xfail(strict=True)`` it would have XPASSed immediately and the marker would
    have blocked the build while testing nothing at all -- a suppression wearing
    the costume of a test. The bodies below are what the names describe.
    """

    @pytest.mark.xfail(
        strict=True,
        raises=TypeError,
        reason="Python fallback doesn't handle list/tuple inputs; needs fix",
    )
    def test_ndvi_list_input(self):
        """A Python list of bands must classify like the ndarray of the same data."""
        red = [0.1, 0.2, 0.3]
        nir = [0.7, 0.8, 0.9]
        assert_close(ndvi(red, nir), _py_ndvi(red, nir), msg="NDVI list")

    @pytest.mark.xfail(
        strict=True,
        raises=TypeError,
        reason="Python fallback doesn't handle list/tuple inputs; needs fix",
    )
    def test_ndvi_tuple_input(self):
        """A Python tuple of bands must classify like the ndarray of the same data."""
        red = (0.1, 0.2, 0.3)
        nir = (0.7, 0.8, 0.9)
        assert_close(ndvi(red, nir), _py_ndvi(red, nir), msg="NDVI tuple")


# Performance regression test (run separately with --benchmark-only)
class TestPerformance:
    """Performance regression tests (run with pytest --benchmark-only)."""

    @pytest.mark.benchmark
    def test_ndvi_performance(self, benchmark):
        """Benchmark NDVI performance."""
        red = np.random.uniform(0, 1, 10000)
        nir = np.random.uniform(0, 1, 10000)

        def run_ndvi():
            return ndvi(red, nir)

        result = benchmark(run_ndvi)
        assert len(result) == 10000

    @pytest.mark.benchmark
    def test_evi_performance(self, benchmark):
        """Benchmark EVI performance."""
        red = np.random.uniform(0, 1, 10000)
        nir = np.random.uniform(0, 1, 10000)
        blue = np.random.uniform(0, 1, 10000)

        def run_evi():
            return evi(red, nir, blue)

        result = benchmark(run_evi)
        assert len(result) == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
