"""Parity of the optional Numba hot-loop accelerations in ``engine.land``.

The contract
------------
Every accelerated kernel must be **bit-identical** to the original pure-Python
path: the same float64 operation order, no re-association, exact ``==`` on the
emitted arrays. These tests assert that by running each function twice — once
with the module's ``_NUMBA_OK`` flag forced True (Numba kernel) and once forced
False (original pure loop) — and comparing the results bitwise. They also assert
the repo still works with Numba disabled, and that the accelerated path still
hits the public expected values already pinned in ``engine/land/tests``.

What is accelerated, and why it is bit-identical
------------------------------------------------
* ``hydrology.flow_accumulation`` — the D8 in-degree (Quinn et al. 1991)
  topological sweep. The only float op is ``acc[target] += acc[cell]``; cells
  are released in exactly row-major-then-topological order, so the additions
  happen in the same sequence with the same rounding.
* ``hydrology.strahler_order`` — one relaxation pass per iteration; stream-order
  values are non-negative integer-valued float64s, so ``max_up + 1.0`` is exact,
  and the ``np.allclose`` convergence test stays outside the kernel.
* ``terrain_analysis.calculate_tpi`` — the windowed mean. Numpy's ``np.mean``
  reduces with a specific ``pairwise_sum`` (block 128, 8-way unroll); the
  kernel reproduces that algorithm exactly over the C-ordered window.

What is deliberately NOT accelerated
-----------------------------------
``terrain_analysis.calculate_slope_aspect`` / ``calculate_curvature`` and
``erosion_risk.calculate_slope_degrees`` stay in pure Python. Their per-cell
formula uses ``x**2`` on numpy float64 *scalars*, which routes to libm
``pow(x, 2.0)`` (not ``x * x``) and drifts by 1 ULP from any multiply-based
(numba / vectorised) path, and ``np.arctan`` / ``np.arctan2`` have no Numba
implementation proven bit-identical to NumPy's scalar ufunc for all inputs. A
1-ULP drift is not a zero-behaviour-change, so those loops keep their original
code — ``TestHornDerivativeLoopsDeliberatelyPure`` pins exactly this.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import engine.land.erosion_risk as erosion
import engine.land.hydrology as hydrology
import engine.land.terrain_analysis as terrain
from engine.land.hydrology import FlowCycleError, flow_direction

try:  # pragma: no cover - introspection only
    import numba as _numba_mod
except Exception:  # pragma: no cover
    _numba_mod = None

HAS_NUMBA = bool(hydrology._NUMBA_OK and terrain._NUMBA_OK)


# --------------------------------------------------------------------------- #
# Deterministic fixtures (fixed seeds — never a wall clock)                    #
# --------------------------------------------------------------------------- #
def smooth_dem(rows: int, cols: int) -> np.ndarray:
    """A smooth, sinusoid+washboard surface; interior never NaN and not flat."""
    r = np.arange(rows)[:, None]
    c = np.arange(cols)[None, :]
    z = 400.0 * (
        0.4 * np.sin(r / 9.0 + 0.3) * np.cos(c / 7.0 - 0.2)
        + 0.2 * np.cos((r + c) / 11.0)
    ) + 20.0 + 0.05 * ((r * 7 + c * 3) % 5)
    # keep positive so TPI's NaN-fill branch is not exercised unless we ask for it
    return np.ascontiguousarray(z, dtype=np.float64)


def random_dem(rows: int, cols: int, seed: int) -> np.ndarray:
    return np.ascontiguousarray(
        np.random.default_rng(seed).uniform(100.0, 900.0, size=(rows, cols)),
        dtype=np.float64,
    )


def v_valley(rows: int = 5, cols: int = 7) -> np.ndarray:
    """V-shaped valley opening north; mirrors test_hydrology.v_valley."""
    r = np.arange(rows)[:, None]
    c = np.arange(cols)[None, :]
    return np.asarray(0.2 * r + 1.0 * np.abs(c - (cols - 1) / 2))


def cone(size: int = 9) -> np.ndarray:
    centre = (size - 1) / 2
    r = np.arange(size)[:, None]
    c = np.arange(size)[None, :]
    return np.asarray(np.hypot(r - centre, c - centre))


def east_ramp(rows: int = 9, cols: int = 9) -> np.ndarray:
    """West-to-east descending ramp; interiors drain east."""
    return np.broadcast_to(-np.arange(float(cols))[None, :], (rows, cols)).copy()


DEMS: dict[str, np.ndarray] = {
    "smooth_40x45": smooth_dem(40, 45),
    "random_60x55": random_dem(60, 55, seed=1234),
    "random_90x90": random_dem(90, 90, seed=99),
    "tall_137x61": random_dem(137, 61, seed=7),
}


@pytest.fixture(params=sorted(DEMS))
def dem(request) -> np.ndarray:
    return DEMS[request.param]


def dem_by(name: str) -> np.ndarray:
    return DEMS[name]


def _bit_identical(a, b) -> bool:
    """Exact bitwise equality for float64 arrays (NaN compares by payload)."""
    if isinstance(a, tuple):
        return all(_bit_identical(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, dict):
        return all(_bit_identical(a[k], b[k]) for k in a)
    na = np.ascontiguousarray(a)
    nb = np.ascontiguousarray(b)
    if na.dtype != nb.dtype or na.shape != nb.shape:
        return False
    if na.dtype == np.float64:
        return bool(np.array_equal(na.view(np.uint64), nb.view(np.uint64)))
    return bool(np.array_equal(na, nb))


def _reference_tpi(dem: np.ndarray, resolution: float = 30.0, scale_m: float = 90.0) -> np.ndarray:
    """Independent, pure-NumPy reimplementation of calculate_tpi (the original)."""
    dem = np.asarray(dem, dtype=float)
    dem_filled = np.where(np.isfinite(dem), dem, np.nan)
    if np.any(np.isnan(dem_filled)):
        median_val = float(np.nanmedian(dem_filled))
        dem_filled = np.where(np.isnan(dem_filled), median_val, dem_filled)
    rows, cols = dem.shape
    radius = max(1, int(scale_m / resolution))
    tpi = np.full_like(dem, np.nan, dtype=np.float64)
    for i in range(radius, rows - radius):
        for j in range(radius, cols - radius):
            window = dem_filled[i - radius : i + radius + 1, j - radius : j + radius + 1]
            tpi[i, j] = dem_filled[i, j] - np.mean(window)
    return tpi


# --------------------------------------------------------------------------- #
# Bit parity: Numba path == pure path (exact)                                  #
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not HAS_NUMBA, reason="numba not installed (optional 'fast' extra)")
class TestNumbaBitParity:
    def test_flag_reports_numba_present(self):
        assert hydrology._NUMBA_OK is True
        assert terrain._NUMBA_OK is True
        assert _numba_mod is not None

    def test_flow_accumulation_is_bit_identical(self, dem, monkeypatch):
        fd = flow_direction(dem)
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        pure = hydrology.flow_accumulation(fd, dem)
        monkeypatch.setattr(hydrology, "_NUMBA_OK", True)
        fast = hydrology.flow_accumulation(fd, dem)
        assert _bit_identical(pure, fast)

    def test_strahler_order_is_bit_identical(self, dem, monkeypatch):
        fd = flow_direction(dem)
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        pure_acc = hydrology.flow_accumulation(fd, dem)
        pure = hydrology.strahler_order(pure_acc, fd, 5.0)
        monkeypatch.setattr(hydrology, "_NUMBA_OK", True)
        fast_acc = hydrology.flow_accumulation(fd, dem)
        fast = hydrology.strahler_order(fast_acc, fd, 5.0)
        assert _bit_identical(pure, fast)
        assert _bit_identical(pure_acc, fast_acc)

    @pytest.mark.parametrize("scale_m", [90.0, 390.0, 450.0])
    def test_tpi_is_bit_identical_across_windows(self, dem, monkeypatch, scale_m):
        monkeypatch.setattr(terrain, "_NUMBA_OK", False)
        pure = terrain.calculate_tpi(dem, 30.0, scale_m)
        monkeypatch.setattr(terrain, "_NUMBA_OK", True)
        fast = terrain.calculate_tpi(dem, 30.0, scale_m)
        assert _bit_identical(pure, fast)

    def test_tpi_is_bit_identical_with_nan_fill(self, monkeypatch):
        d = random_dem(50, 50, seed=7)
        d = d.copy()
        d[3, 3] = np.nan
        d[10, 20:25] = np.nan
        monkeypatch.setattr(terrain, "_NUMBA_OK", False)
        pure = terrain.calculate_tpi(d, 30.0, 90.0)
        monkeypatch.setattr(terrain, "_NUMBA_OK", True)
        fast = terrain.calculate_tpi(d, 30.0, 90.0)
        assert _bit_identical(pure, fast)

    def test_twi_is_bit_identical_end_to_end(self, monkeypatch):
        # TWI composes flow_direction + flow_accumulation + slope; the only
        # accelerated link is flow_accumulation (hydrology), exercised here.
        d = smooth_dem(50, 50) * 10.0
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        pure = terrain.calculate_twi(d, 30.0)
        monkeypatch.setattr(hydrology, "_NUMBA_OK", True)
        fast = terrain.calculate_twi(d, 30.0)
        assert _bit_identical(pure, fast)


# --------------------------------------------------------------------------- #
# Absolute pins: the kernels reproduce an independent reference                 #
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not HAS_NUMBA, reason="numba not installed (optional 'fast' extra)")
class TestAcceleratedMatchesIndependentReference:
    def test_tpi_matches_numpy_mean_reference(self, dem, monkeypatch):
        monkeypatch.setattr(terrain, "_NUMBA_OK", True)
        got = terrain.calculate_tpi(dem, 30.0, 90.0)
        assert _bit_identical(got, _reference_tpi(dem, 30.0, 90.0))

    def test_flow_accumulation_matches_in_degree_reference(self, dem, monkeypatch):
        # Independent in-degree (Kahn) accumulation built with numpy+python here.
        fd = flow_direction(dem)
        monkeypatch.setattr(hydrology, "_NUMBA_OK", True)
        got = hydrology.flow_accumulation(fd, dem)
        assert _bit_identical(got, _reference_flow_accumulation(fd))


def _reference_flow_accumulation(flow_dir: np.ndarray) -> np.ndarray:
    from collections import deque

    from engine.land.hydrology import DIR_OFFSETS

    flow_dir = np.asarray(flow_dir, dtype=float)
    rows, cols = flow_dir.shape
    acc = np.ones((rows, cols), dtype=np.float64)
    codes = np.rint(flow_dir).astype(np.int64)
    pending = np.zeros((rows, cols), dtype=np.int64)
    down = -np.ones((rows, cols, 2), dtype=np.int64)
    for i in range(rows):
        for j in range(cols):
            code = int(codes[i, j])
            if code > 0:
                di, dj = DIR_OFFSETS[code]
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    down[i, j] = (ni, nj)
                    pending[ni, nj] += 1
    q = deque((int(i), int(j)) for i, j in zip(*np.nonzero(pending == 0), strict=True))
    while q:
        i, j = q.popleft()
        ni, nj = down[i, j]
        if ni < 0:
            continue
        acc[int(ni), int(nj)] += acc[i, j]
        pending[int(ni), int(nj)] -= 1
        if pending[int(ni), int(nj)] == 0:
            q.append((int(ni), int(nj)))
    return acc


# --------------------------------------------------------------------------- #
# Fallback: the repo works with Numba disabled (_NUMBA_OK = False)             #
# --------------------------------------------------------------------------- #
class TestPureFallbackWorks:
    """With Numba disabled the ORIGINAL pure path runs, unchanged and correct.

    These run regardless of whether the ``fast`` extra is installed, so they
    also guard the no-numba venv.
    """

    @pytest.mark.parametrize("name", sorted(DEMS))
    def test_flow_accumulation_pure_runs(self, name, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        dem = dem_by(name)
        acc = hydrology.flow_accumulation(flow_direction(dem), dem)
        assert acc.shape == dem.shape
        assert np.isfinite(acc).all()

    def test_flow_accumulation_pure_pins_valley_outlet(self, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        dem = v_valley()
        acc = hydrology.flow_accumulation(flow_direction(dem), dem)
        # value pinned in test_hydrology.TestValleyFlowsIntoItsOwnAxis
        assert acc[0, 3] == 16.0
        assert acc.max() == 16.0
        assert np.unravel_index(int(acc.argmax()), acc.shape) == (0, 3)
        assert acc[0, 0] == 1.0 and acc[4, 6] == 1.0

    def test_flow_accumulation_pure_pins_cone_peak(self, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        acc = hydrology.flow_accumulation(flow_direction(cone(9)), cone(9))
        # value pinned in test_hydrology.TestRadiallyConvergingDem
        assert acc[4, 4] == 49.0
        assert acc.max() == 49.0

    def test_flow_accumulation_pure_pins_ramp(self, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        acc = hydrology.flow_accumulation(flow_direction(east_ramp(9, 9)), east_ramp(9, 9))
        # value pinned in test_hydrology.test_accumulation_grows_downstream_by_one
        assert acc[4, 8] == 8.0
        assert acc[4, 1] == 1.0
        assert acc[4, 0] == 1.0

    def test_cycle_error_unchanged_without_numba(self, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        fd = np.zeros((5, 5), dtype=np.float64)
        fd[1, 1] = 3.0  # E
        fd[1, 2] = 7.0  # W
        with pytest.raises(FlowCycleError):
            hydrology.flow_accumulation(fd)

    def test_out_of_range_code_error_unchanged_without_numba(self, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        fd = np.zeros((4, 4), dtype=np.float64)
        fd[1, 1] = 9.0
        with pytest.raises(ValueError, match="0-8"):
            hydrology.flow_accumulation(fd)

    def test_tpi_pure_runs_without_numba(self, monkeypatch):
        monkeypatch.setattr(terrain, "_NUMBA_OK", False)
        tpi = terrain.calculate_tpi(random_dem(40, 40, 1), 30.0, 90.0)
        assert tpi.shape == (40, 40)
        assert np.isfinite(tpi[5:-5, 5:-5]).all()

    def test_strahler_pure_runs_without_numba(self, monkeypatch):
        monkeypatch.setattr(hydrology, "_NUMBA_OK", False)
        dem = dem_by("random_60x55")
        fd = flow_direction(dem)
        acc = hydrology.flow_accumulation(fd, dem)
        order, max_order = hydrology.strahler_order(acc, fd, 5.0)
        assert order.shape == dem.shape
        assert isinstance(max_order, int)


# --------------------------------------------------------------------------- #
# Documentation test: the Horn-derivative loops stay pure for a real reason     #
# --------------------------------------------------------------------------- #
class TestHornDerivativeLoopsDeliberatelyPure:
    """Slope / aspect / curvature / RUSLE-slope are kept in pure Python.

    This test *is* the finding: numpy's scalar ``x**2`` is libm ``pow``, not a
    multiply, so no vectorised/compiled path can reproduce it bit-for-bit.
    """

    def test_numpy_scalar_square_is_libm_pow_not_multiply(self):
        x = np.float64(0.09500076993455148)  # a value where pow(x, 2) != x*x
        assert x**2 == np.float64(math.pow(float(x), 2.0))
        assert (x * x) != (x**2)  # the multiply path differs by 1 ULP

    @pytest.mark.parametrize("flag", [True, False])
    def test_slope_aspect_independent_of_numba_flag(self, dem, monkeypatch, flag):
        monkeypatch.setattr(terrain, "_NUMBA_OK", flag)
        a = terrain.calculate_slope_aspect(dem, 30.0)
        monkeypatch.setattr(terrain, "_NUMBA_OK", not flag)
        b = terrain.calculate_slope_aspect(dem, 30.0)
        assert _bit_identical(a, b)  # no numba branch -> identical either way

    @pytest.mark.parametrize("flag", [True, False])
    def test_curvature_independent_of_numba_flag(self, dem, monkeypatch, flag):
        monkeypatch.setattr(terrain, "_NUMBA_OK", flag)
        a = terrain.calculate_curvature(dem, 30.0)
        monkeypatch.setattr(terrain, "_NUMBA_OK", not flag)
        b = terrain.calculate_curvature(dem, 30.0)
        assert _bit_identical(a, b)

    def test_rusle_slope_degrees_is_deterministic(self):
        dem = dem_by("random_60x55")
        a = erosion.calculate_slope_degrees(dem, 30.0)
        b = erosion.calculate_slope_degrees(dem, 30.0)
        assert _bit_identical(a, b)

    def test_rusle_slope_degrees_has_no_numba_branch(self):
        # erosion_risk does not import numba at all — it stays pure.
        assert not hasattr(erosion, "_NUMBA_OK")
        assert not hasattr(erosion, "njit")
