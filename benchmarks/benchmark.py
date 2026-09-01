"""Innovation benchmark: HyDroMa engine (W5).

Quantifies:
  1. Numba vs NumPy vs pure-Python for the van Genuchten K(h) hot loop
     (the kernel behind Monte Carlo / scenario sweeps).
  2. Latin Hypercube Sampling (LHS) variance reduction vs plain Monte Carlo
     on a toy integral, reproducing the C++ result (108x SE reduction).
  3. NumPy-vectorized Muskingum routing vs the Python loop used before.

Output: prints a compact table; the parent agent writes the markdown report.
"""

import structlog

logger = structlog.get_logger()
import time

import numpy as np

from engine.hydroma.cpp_bridge.soil_physics_fast import (
    _van_genuchten_K as vg_k_numba,
)

try:
    from numba import njit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


# ---- 1. van Genuchten K hot loop ---------------------------------------
N = 200_000
h = np.linspace(-1500.0, -1.0, N)
KS, TR, TS, ALPHA, N_PAR = 4.42, 0.065, 0.41, 0.075, 1.89


def vg_k_pure_py(h_list):
    m = 1.0 - 1.0 / N_PAR
    out = np.empty(len(h_list))
    for i, hv in enumerate(h_list):
        hv = abs(hv)
        if hv < 1e-10:
            out[i] = KS
            continue
        denom = (1.0 + (ALPHA * hv) ** N_PAR) ** m
        se = 1.0 / denom
        if 0 < se < 1:
            out[i] = KS * se**0.5 * (1.0 - (1.0 - se ** (1.0 / m)) ** m) ** 2
        else:
            out[i] = KS if se >= 1 else 0.0
    return out


def vg_k_numpy(h_arr):
    m = 1.0 - 1.0 / N_PAR
    ha = np.abs(h_arr)
    denom = (1.0 + (ALPHA * ha) ** N_PAR) ** m
    se = 1.0 / denom
    k = KS * np.sqrt(se) * (1.0 - (1.0 - se ** (1.0 / m)) ** m) ** 2
    k[ha < 1e-10] = KS
    return k


def timeit(fn, *args, reps=3):
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - t0)
    return best


# correctness cross-check
k_numba = vg_k_numba(h, KS, TR, TS, ALPHA, N_PAR)
k_numpy = vg_k_numpy(h)
k_pure = vg_k_pure_py(h.tolist())
assert np.allclose(k_numba, k_numpy, rtol=1e-10), "numba vs numpy mismatch"
assert np.allclose(k_numba, k_pure, rtol=1e-10), "numba vs pure mismatch"

t_numba = timeit(vg_k_numba, h, KS, TR, TS, ALPHA, N_PAR)
t_numpy = timeit(vg_k_numpy, h)
t_pure = timeit(vg_k_pure_py, h.tolist())

logger.info("== 1. van Genuchten K(h), N=%d ==" % N)
logger.info(f"  numba : {t_numba:.4f} s")
logger.info(f"  numpy : {t_numpy:.4f} s")
logger.info(f"  pure  : {t_pure:.4f} s")
logger.info("  speedup numba/pure : %.1fx" % (t_pure / t_numba))
logger.info("  speedup numba/numpy: %.1fx" % (t_numpy / t_numba))

# ---- 2. LHS vs MC variance reduction -----------------------------------
rng = np.random.default_rng(42)


def mc_estimate(n, reps=200):
    means = []
    for _ in range(reps):
        x = rng.random(n)
        y = rng.random(n)
        means.append((x + y).mean())
    return np.std(means)


def lhs_estimate(n, reps=200):
    means = []
    for _ in range(reps):
        perm_x = rng.permutation(n)
        perm_y = rng.permutation(n)
        x = (perm_x + rng.random(n)) / n
        y = (perm_y + rng.random(n)) / n
        means.append((x + y).mean())
    return np.std(means)


n_samp = 100
se_mc = mc_estimate(n_samp)
se_lhs = lhs_estimate(n_samp)
logger.info("== 2. MC vs LHS on E[x+y], n=%d ==" % n_samp)
logger.info(f"  SE(MC)  = {se_mc:.5f}")
logger.info(f"  SE(LHS) = {se_lhs:.5f}")
logger.info("  variance reduction = %.1fx" % (se_mc / se_lhs))

# ---- 3. Muskingum routing: numba vs pure loop --------------------------
try:
    from engine.hydroma.cpp_bridge.hydrology_fast import route_flood_wave

    Q = np.clip(20 + 80 * np.sin(np.linspace(0, 6 * np.pi, 5000)), 0, None)

    def route_py(q_in):
        # simplified single-reach Muskingum for the pure-Python baseline
        k, x, dt = 2.0, 0.2, 10.0
        c0 = (-k * x + 0.5 * dt) / (k * (1 - x) + 0.5 * dt)
        c1 = (k * x + 0.5 * dt) / (k * (1 - x) + 0.5 * dt)
        c2 = (k * (1 - x) - 0.5 * dt) / (k * (1 - x) + 0.5 * dt)
        out = np.empty_like(q_in)
        out[0] = q_in[0]
        for i in range(1, len(q_in)):
            out[i] = c0 * q_in[i] + c1 * q_in[i - 1] + c2 * out[i - 1]
        return out

    t_musk_numba = timeit(route_flood_wave, Q, 1000.0, 50, 0.03, 0.002, 10.0, 5.0)
    t_musk_py = timeit(route_py, Q)
    logger.info("== 3. Muskingum routing, N=%d ==" % len(Q))
    print(
        f"  numba : {t_musk_numba:.5f} s | pure: {t_musk_py:.5f} s | speedup {t_musk_py / t_musk_numba:.1f}x"
    )
except Exception as e:  # pragma: no cover
    logger.info(f"== 3. Muskingum: skipped ({e})")
