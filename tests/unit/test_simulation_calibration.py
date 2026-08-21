"""Tests for the Sobol' sensitivity implementation (Phase 3, sprint 2).

Verified against the Ishigami function with known analytical indices:
S1 = (0.3139, 0.4424, 0.0), ST = (0.5576, 0.4424, 0.2437).
"""

import numpy as np
import pytest

from engine.hydroma.simulation.calibration import (
    ishigami,
    saltelli_matrices,
    sensitivity_of_metric,
    sobol_indices,
)

ISHIGAMI_BOUNDS = [(-np.pi, np.pi)] * 3


class TestSaltelliMatrices:
    def test_shape_and_structure(self):
        rng = np.random.default_rng(0)
        a = rng.uniform(size=(100, 3))
        b = rng.uniform(size=(100, 3))
        mats = saltelli_matrices(a, b)
        assert len(mats) == 2 + 2 * 3
        assert np.allclose(mats[0], a)
        assert np.allclose(mats[1], b)
        # AB_0 differs from A only in column 0
        assert np.allclose(mats[2][:, 1:], a[:, 1:])
        assert np.allclose(mats[2][:, 0], b[:, 0])


class TestIshigamiIndices:
    def test_first_order_indices(self):
        result = sensitivity_of_metric(ishigami, ISHIGAMI_BOUNDS, n=8192, seed=42)
        s1, st = result["S1"], result["ST"]
        assert s1[0] == pytest.approx(0.3139, abs=0.04)
        assert s1[1] == pytest.approx(0.4424, abs=0.04)
        assert s1[2] == pytest.approx(0.0, abs=0.02)

    def test_total_order_indices(self):
        result = sensitivity_of_metric(ishigami, ISHIGAMI_BOUNDS, n=8192, seed=42)
        st = result["ST"]
        assert st[0] == pytest.approx(0.5576, abs=0.05)
        assert st[1] == pytest.approx(0.4424, abs=0.04)
        assert st[2] == pytest.approx(0.2437, abs=0.05)

    def test_total_order_at_least_first_order(self):
        result = sensitivity_of_metric(ishigami, ISHIGAMI_BOUNDS, n=2048, seed=7)
        assert np.all(result["ST"] >= result["S1"] - 1e-9)

    def test_zero_variance_raises(self):
        def constant(_x):
            return np.full(_x.shape[0], 5.0)

        with pytest.raises(ValueError, match="zero output variance"):
            sensitivity_of_metric(constant, ISHIGAMI_BOUNDS, n=256)

    def test_reproducible_with_seed(self):
        r1 = sensitivity_of_metric(ishigami, ISHIGAMI_BOUNDS, n=1024, seed=1)
        r2 = sensitivity_of_metric(ishigami, ISHIGAMI_BOUNDS, n=1024, seed=1)
        assert np.allclose(r1["S1"], r2["S1"])
