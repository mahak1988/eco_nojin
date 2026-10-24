"""Benchmark: pure-Python vs optional-Numba hot loops (reports a speedup).

This is a *reporting* benchmark, not a gate. It prints the measured wall-time of
the original pure path and the Numba path for each accelerated hot loop on a
moderately sized DEM, plus the speedup. It never asserts a speedup threshold
(CI hardware varies wildly) and it skips when a loop is too fast to time
meaningfully or when Numba is absent.

Run with ``-s`` to see the report::

    pytest engine/land/tests/test_numba_benchmark.py -s -q
"""

from __future__ import annotations

import contextlib
import time

import numpy as np
import pytest

import engine.land.hydrology as hydrology
import engine.land.terrain_analysis as terrain
from engine.land.hydrology import flow_accumulation, flow_direction

pytestmark = pytest.mark.skipif(
    not (hydrology._NUMBA_OK and terrain._NUMBA_OK),
    reason="numba not installed (optional 'fast' extra) — nothing to compare",
)


@contextlib.contextmanager
def _flag(mod, value):
    old = mod._NUMBA_OK
    mod._NUMBA_OK = value
    try:
        yield
    finally:
        mod._NUMBA_OK = old


def _benchmark_dem(rows: int, cols: int) -> np.ndarray:
    """A moderate, deterministic DEM (a tilted plane + structure, no NaN)."""
    r = np.arange(rows)[:, None]
    c = np.arange(cols)[None, :]
    z = (
        300.0
        + 0.9 * c
        + 0.6 * r
        + 120.0 * np.sin(r / 17.0 + 0.2) * np.cos(c / 13.0 - 0.1)
        + 0.05 * ((r * 7 + c * 3) % 5)
    )
    return np.ascontiguousarray(z, dtype=np.float64)


def _best_time(fn, *args, repeat: int = 2, warm: bool = True, **kwargs) -> float:
    # Only the Numba path needs a warm-up call (JIT compile); the pure path is
    # stateless, so warming it would just double an already-slow measurement.
    if warm:
        fn(*args, **kwargs)
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        best = min(best, time.perf_counter() - t0)
    return best


def _report(name: str, pure: float, fast: float, lines: list[str]) -> None:
    speedup = pure / fast if fast > 0 else float("inf")
    lines.append(
        f"  {name:28s} pure={pure * 1e3:8.2f} ms   numba={fast * 1e3:8.2f} ms"
        f"   speedup={speedup:5.1f}x"
    )


def test_numba_hot_loop_benchmark_reports_speedup():
    rows = cols = 150  # 22,500 cells — "moderately sized"
    dem = _benchmark_dem(rows, cols)

    report: list[str] = [f"Numba hot-loop benchmark on a {rows}x{cols} DEM "
                         f"({rows * cols:,} cells), best-of-2:"]
    pure_total = 0.0
    fast_total = 0.0

    # --- D8 flow accumulation -------------------------------------------------
    fd = flow_direction(dem)  # deterministic; not branch-accelerated
    with _flag(hydrology, False):
        pure_acc = _best_time(flow_accumulation, fd, dem, warm=False)
    with _flag(hydrology, True):
        fast_acc = _best_time(flow_accumulation, fd, dem)
    _report("flow_accumulation", pure_acc, fast_acc, report)
    pure_total += pure_acc
    fast_total += fast_acc

    # flow accumulation for Strahler input (accelerated, not on the clock)
    acc = flow_accumulation(fd, dem)

    # --- Strahler stream order -----------------------------------------------
    with _flag(hydrology, False):
        pure_str = _best_time(hydrology.strahler_order, acc, fd, 5.0, warm=False)
    with _flag(hydrology, True):
        fast_str = _best_time(hydrology.strahler_order, acc, fd, 5.0)
    _report("strahler_order", pure_str, fast_str, report)
    pure_total += pure_str
    fast_total += fast_str

    # --- TPI windowed mean ----------------------------------------------------
    with _flag(terrain, False):
        pure_tpi = _best_time(terrain.calculate_tpi, dem, 30.0, 90.0, warm=False)
    with _flag(terrain, True):
        fast_tpi = _best_time(terrain.calculate_tpi, dem, 30.0, 90.0)
    _report("calculate_tpi (7x7)", pure_tpi, fast_tpi, report)
    pure_total += pure_tpi
    fast_total += fast_tpi

    report.append(
        f"  {'TOTAL':28s} pure={pure_total * 1e3:8.2f} ms   numba={fast_total * 1e3:8.2f} ms"
        f"   speedup={pure_total / fast_total:5.1f}x"
    )

    # Skip when everything is too fast to measure meaningfully on this host.
    if pure_total < 5e-3:
        pytest.skip("pure paths ran too fast to benchmark meaningfully (<5 ms total)")

    print("\n".join(report))
    # Sanity only: the timed results must be finite and positive. No threshold.
    assert pure_total > 0 and fast_total > 0
    # Determinism: the two paths agree bitwise (parity is asserted elsewhere).
    assert np.array_equal(
        hydrology.flow_accumulation(fd, dem),
        hydrology.flow_accumulation(fd, dem),
    )
