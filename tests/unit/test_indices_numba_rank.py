"""Regression tests for the Numba vegetation-index kernels.

``indices_fast._ndvi_fast`` and its siblings unpack ``rows, cols = arr.shape``,
so they only compile for a 2-D layout. A 1-D array -- the normal shape of a
satellite reflectance time series -- raised
``numba.core.errors.TypingError: wrong tuple length`` on the first call.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.cpp_bridge import indices_fast as f


def _pairs(n: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    red = rng.uniform(0.01, 0.3, n)
    nir = rng.uniform(0.2, 0.9, n)
    return red, nir


# --------------------------------------------------------------------------
# 1-D input (the regression)
# --------------------------------------------------------------------------


def test_ndvi_fast_accepts_1d():
    red, nir = _pairs(1000)
    out = f.ndvi_fast(red, nir)

    assert out.shape == (1000,), f"expected 1-D output, got {out.shape}"


def test_ndvi_fast_1d_values_match_numpy():
    red, nir = _pairs(5000)
    out = f.ndvi_fast(red, nir)
    expected = (nir - red) / (nir + red)

    np.testing.assert_allclose(out, expected, rtol=1e-12, atol=1e-12)


def test_evi_fast_accepts_1d():
    rng = np.random.default_rng(3)
    red = rng.uniform(0.01, 0.3, 800)
    nir = rng.uniform(0.2, 0.9, 800)
    blue = rng.uniform(0.01, 0.2, 800)

    out = f.evi_fast(red, nir, blue)

    assert out.shape == (800,)


def test_savi_fast_accepts_1d():
    red, nir = _pairs(400)
    out = f.savi_fast(red, nir)

    assert out.shape == (400,)


def test_nbr_fast_accepts_1d():
    rng = np.random.default_rng(11)
    nir = rng.uniform(0.2, 0.9, 300)
    swir = rng.uniform(0.05, 0.5, 300)

    out = f.nbr_fast(nir, swir)

    assert out.shape == (300,)


# --------------------------------------------------------------------------
# 2-D input must be unchanged
# --------------------------------------------------------------------------


@pytest.mark.parametrize("shape", [(10, 100), (1000, 1000), (3, 4)])
def test_2d_shape_is_preserved(shape):
    red, nir = _pairs(int(np.prod(shape)))
    out = f.ndvi_fast(red.reshape(shape), nir.reshape(shape))

    assert out.shape == shape


def test_2d_values_match_numpy():
    red, nir = _pairs(20000)
    out = f.ndvi_fast(red.reshape(200, 100), nir.reshape(200, 100))
    expected = (nir - red) / (nir + red)

    np.testing.assert_allclose(out.reshape(-1), expected, rtol=1e-12)


# --------------------------------------------------------------------------
# Rank and dtype handling
# --------------------------------------------------------------------------


def test_3d_input_is_rejected_clearly():
    red, nir = _pairs(27)
    with pytest.raises(ValueError, match="1-D or 2-D"):
        f.ndvi_fast(red.reshape(3, 3, 3), nir.reshape(3, 3, 3))


def test_integer_input_is_promoted_without_overflow():
    """uint16 raw DN must not wrap in the denominator."""
    red = np.array([100, 200, 300], dtype=np.uint16)
    nir = np.array([3000, 4000, 5000], dtype=np.uint16)

    out = f.ndvi_fast(red, nir)
    expected = (nir.astype(np.float64) - red) / (nir.astype(np.float64) + red)

    assert out.dtype == np.float64
    np.testing.assert_allclose(out, expected, rtol=1e-12)


def test_zero_denominator_is_zero_not_nan():
    red = np.zeros(5)
    nir = np.zeros(5)
    out = f.ndvi_fast(red, nir)

    assert np.all(out == 0.0)
    assert not np.any(np.isnan(out))


def test_output_is_clipped_to_unit_range():
    rng = np.random.default_rng(5)
    red = rng.uniform(0, 0.5, 2000)
    nir = rng.uniform(0, 0.5, 2000)
    out = f.ndvi_fast(red, nir)

    assert np.all(out >= -1.0)
    assert np.all(out <= 1.0)


def test_prepare_reports_flatten_need():
    prepared, flatten = f._prepare(np.zeros(5), np.zeros(5))
    assert flatten is True
    assert prepared[0].shape == (5, 1)

    prepared, flatten = f._prepare(np.zeros((2, 3)), np.zeros((2, 3)))
    assert flatten is False
    assert prepared[0].shape == (2, 3)
