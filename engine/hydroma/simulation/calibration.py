"""Sensitivity analysis & uncertainty utilities (Phase 3, sprint 2).

Implements Saltelli sampling and Sobol' first/total-order indices
(Saltelli et al. 2010) in pure numpy. The implementation is verified
against the Ishigami function, whose analytical Sobol' indices are known
(see tests/unit/test_simulation_calibration.py).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def sample_uniform(n: int, lo: np.ndarray, hi: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Draw an (n, d) uniform sample within per-parameter bounds."""
    return rng.uniform(lo, hi, size=(n, lo.size))


def sample_normal(n: int, mu: np.ndarray, sigma: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Draw an (n, d) normal sample with the given means and stds."""
    return rng.normal(mu, sigma, size=(n, mu.size))


def saltelli_matrices(a: np.ndarray, b: np.ndarray) -> list[np.ndarray]:
    """Build the 2d+2 Saltelli matrices from A and B (each N x d).

    Returns [A, B, AB_0..AB_{d-1}, BA_0..BA_{d-1}].
    """
    n, d = a.shape
    matrices = [a, b]
    for i in range(d):
        ab = a.copy()
        ab[:, i] = b[:, i]
        matrices.append(ab)
        ba = b.copy()
        ba[:, i] = a[:, i]
        matrices.append(ba)
    return matrices


def sobol_indices(
    a: np.ndarray,
    b: np.ndarray,
    f: Callable[[np.ndarray], np.ndarray],
) -> dict:
    """First- and total-order Sobol' indices (Saltelli 2010 estimators).

    Args:
        a, b: independent (N, d) input samples.
        f: scalar model ``f(X) -> (N,)``.

    Returns:
        dict with ``S1`` (first order), ``ST`` (total order), ``var``.
    """
    matrices = saltelli_matrices(a, b)
    y = np.asarray([f(m) for m in matrices], dtype=float)  # (2d+2, N)
    ya, yb = y[0], y[1]
    var = float(np.var(np.concatenate([ya, yb]), ddof=1))
    if var <= 0.0:
        raise ValueError("zero output variance; cannot compute Sobol' indices")
    d = a.shape[1]
    s1 = np.zeros(d)
    st = np.zeros(d)
    for i in range(d):
        # saltelli_matrices interleaves: [A, B, AB0, BA0, AB1, BA1, ...]
        yab = y[2 + 2 * i]
        yba = y[3 + 2 * i]
        s1[i] = float(np.mean(yb * (yab - ya)) / var)
        st[i] = float(np.mean((ya - yab) ** 2) / (2.0 * var))
    return {"S1": s1, "ST": st, "var": var}


def sensitivity_of_metric(
    f: Callable[[np.ndarray], np.ndarray],
    bounds: list[tuple[float, float]],
    n: int = 2048,
    seed: int = 42,
    dist: str = "uniform",
    **dist_kwargs,
) -> dict:
    """Convenience wrapper: uniform bounds -> Sobol' indices of a scalar metric.

    Args:
        f: model mapping an (N, d) parameter matrix to (N,) scalar metrics.
        bounds: [(lo, hi), ...] per parameter (uniform), or normal kwargs
            via ``dist="normal"`` and ``mu``/``sigma`` lists.
        n: Saltelli base sample size (total model evals = n * (2d + 2)).
        seed: RNG seed for reproducibility.
    """
    rng = np.random.default_rng(seed)
    d = len(bounds)
    if dist == "uniform":
        lo = np.array([b[0] for b in bounds], dtype=float)
        hi = np.array([b[1] for b in bounds], dtype=float)
        a = sample_uniform(n, lo, hi, rng)
        b = sample_uniform(n, lo, hi, rng)
    elif dist == "normal":
        mu = np.asarray(dist_kwargs["mu"], dtype=float)
        sigma = np.asarray(dist_kwargs["sigma"], dtype=float)
        a = sample_normal(n, mu, sigma, rng)
        b = sample_normal(n, mu, sigma, rng)
    else:  # pragma: no cover - defensive
        raise ValueError(f"unsupported distribution: {dist}")
    return sobol_indices(a, b, f)


def ishigami(x: np.ndarray, a: float = 7.0, b: float = 0.1) -> np.ndarray:
    """Ishigami test function (analytical Sobol' indices known)."""
    return np.sin(x[:, 0]) + a * np.sin(x[:, 1]) ** 2 + b * x[:, 2] ** 4 * np.sin(x[:, 0])
