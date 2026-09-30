"""Tests for the H-Pheno Savitzky-Golay smoother.

Two defects, both about the method being a method *only sometimes*:

1. When scipy was absent the filter silently became ``np.convolve(...,
   mode="same")`` -- a centred moving average. A moving average has no
   derivative-preserving property, so every downstream zero-crossing and
   ``np.gradient`` changed meaning depending on whether an optional dependency
   happened to be installed.
2. The window expression could produce an even window, which scipy rejects, and
   could reduce the window to 3 with the default ``polyorder=3``, which scipy also
   rejects -- raising a ValueError that the ``except ImportError`` did not catch.

The smoother is now a direct NumPy implementation, so the result does not depend
on the environment, and the window is always valid.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.models.hpheno import HPheno


def _series(n: int = 60) -> np.ndarray:
    """A smooth seasonal signal, band-limited to what the window can represent."""
    t = np.arange(n, dtype=float)
    return 0.3 + 0.25 * np.sin(2 * np.pi * t / 30.0)


# ------------------------------------------------------------------ the method


def test_kernel_reproduces_a_polynomial_exactly():
    """A local polynomial fit must be exact on a polynomial of the same order.

    Checked away from the edges. The implementation reflects at the boundaries,
    and the reflection of a linear function is not a linear continuation, so
    polynomial exactness is a property of the interior only -- which is the usual
    statement of the Savitzky-Golay property.
    """
    window, polyorder = 11, 3
    half = window // 2
    n = 41
    x = np.arange(n, dtype=float) - n / 2

    for degree in range(polyorder + 1):
        y = x**degree
        out = HPheno.smooth(y, window=window, polyorder=polyorder)
        interior = slice(half, n - half)
        assert np.allclose(out[interior], y[interior], atol=1e-8), (
            f"degree {degree} not reproduced exactly in the interior"
        )


def test_smoothing_preserves_a_constant():
    out = HPheno.smooth(np.full(40, 0.7), window=11, polyorder=3)

    assert np.allclose(out, 0.7, atol=1e-10)


def test_smoothing_preserves_a_linear_ramp():
    """Preserving a linear trend is what distinguishes this from a moving average."""
    n = 40
    y = np.linspace(0.1, 0.9, n)
    out = HPheno.smooth(y, window=11, polyorder=1)

    interior = out[6:-6]
    assert np.allclose(interior, y[6:-6], atol=1e-8), (
        "a degree-1 Savitzky-Golay filter must reproduce a linear signal exactly; "
        "a moving average would flatten the ramp"
    )


def test_smoothing_reduces_noise():
    """Noise variance must fall, away from the edges.

    The signal is band-limited to what an 11-point window can represent; a
    faster component would be aliased by the filter and the comparison would be
    measuring that rather than noise reduction.
    """
    rng = np.random.default_rng(0)
    clean = _series(80)
    noisy = clean + rng.normal(0, 0.01, clean.size)

    smoothed = HPheno.smooth(noisy, window=11, polyorder=3)
    # Stay clear of the reflect-padded edges, where the boundary treatment shows.
    interior = slice(10, -10)

    assert np.std(smoothed[interior] - clean[interior]) < np.std(noisy[interior] - clean[interior])


def test_result_is_derivative_preserving():
    """A moving average attenuates a sinusoid; Savitzky-Golay largely preserves it."""
    y = _series(120)
    out = HPheno.smooth(y, window=15, polyorder=3)
    interior = slice(10, -10)

    amp_in = np.ptp(y[interior])
    amp_out = np.ptp(out[interior])

    assert amp_out > 0.9 * amp_in, (
        f"smoothing attenuated the signal by more than 10%: {amp_in:.4f} -> {amp_out:.4f}. "
        "A moving-average filter does this; a degree-3 Savitzky-Golay does not."
    )


# ------------------------------------------------------ window validity


@pytest.mark.parametrize("n", [12, 13, 20, 21, 40, 41])
def test_output_length_always_matches_input(n: int):
    out = HPheno.smooth(_series(n), window=11, polyorder=3)

    assert out.shape == (n,)


@pytest.mark.parametrize(("window", "polyorder"), [(3, 3), (2, 1), (5, 5), (4, 2)])
def test_invalid_requests_are_clamped_not_raised(window: int, polyorder: int):
    """An even window, or polyorder >= window, must not raise.

    The old expression could reach scipy with exactly these and get a ValueError
    that the ImportError handler did not catch.
    """
    out = HPheno.smooth(_series(30), window=window, polyorder=polyorder)

    assert out.shape == (30,)
    assert np.all(np.isfinite(out))


def test_even_window_raises_when_requested_directly():
    with pytest.raises(ValueError, match="must be odd"):
        HPheno.savgol_coefficients(10, 3)


def test_polyorder_must_be_below_the_window():
    with pytest.raises(ValueError, match="must be less than the window"):
        HPheno.savgol_coefficients(5, 5)


def test_series_shorter_than_the_window():
    for n in (3, 5, 7, 11):
        out = HPheno.smooth(_series(n), window=11, polyorder=3)
        assert out.shape == (n,)
        assert np.all(np.isfinite(out))


def test_empty_series():
    out = HPheno.smooth(np.array([]), window=11, polyorder=3)

    assert out.size == 0


# ------------------------------------------------- independence from scipy


def test_result_does_not_depend_on_scipy_availability(monkeypatch):
    """The whole point: the method must not change with the environment."""
    y = _series(50)
    with_scipy = HPheno.smooth(y, window=11, polyorder=3)

    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name.startswith("scipy"):
            raise ImportError("scipy blocked for this test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    without_scipy = HPheno.smooth(y, window=11, polyorder=3)

    np.testing.assert_array_equal(with_scipy, without_scipy)


def test_does_not_match_a_moving_average():
    """Guards the old fallback: the result must differ from a centred mean."""
    y = _series(60)
    sg = HPheno.smooth(y, window=11, polyorder=3)
    moving = np.convolve(y, np.ones(11) / 11.0, mode="same")

    interior = slice(6, -6)
    assert np.max(np.abs(sg[interior] - moving[interior])) > 1e-3, (
        "the smoother is producing the same result as a moving average"
    )
