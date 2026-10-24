"""Tests for Stage 27: Validation metrics with edge-case handling.

Tests cover:
- MAE, RMSE, Bias correctness on known values
- R² with normal data and zero-variance (all identical observations)
- MAPE with normal data and zero-valued observations
- Edge cases: single sample, empty arrays, NaN/Inf inputs, length mismatch
"""

from __future__ import annotations

import pytest

from engine.hydroma.eval.validation_metrics import (
    MetricResult,
    compute_mape_with_notes,
    compute_r_squared_with_notes,
    compute_validation_metrics,
)


class TestRMSE:
    """Tests for RMSE computation."""

    def test_rmse_zero_for_perfect(self):
        """RMSE is 0 for perfect predictions."""
        m = compute_validation_metrics([1, 2, 3], [1, 2, 3])
        assert m.rmse_result.value == pytest.approx(0.0)

    def test_rmse_known_value(self):
        """RMSE matches hand-computed value."""
        m = compute_validation_metrics([1, 2, 3], [2, 3, 4])
        # residuals = [1, 1, 1], RMSE = sqrt(1) = 1
        assert m.rmse_result.value == pytest.approx(1.0)

    def test_rmse_n_samples(self):
        """RMSE reports correct n_samples."""
        m = compute_validation_metrics([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        assert m.rmse_result.n_samples == 5


class TestMAE:
    """Tests for MAE computation."""

    def test_mae_zero_for_perfect(self):
        """MAE is 0 for perfect predictions."""
        m = compute_validation_metrics([1, 2, 3], [1, 2, 3])
        assert m.mae_result.value == pytest.approx(0.0)

    def test_mae_known_value(self):
        """MAE matches hand-computed value."""
        m = compute_validation_metrics([1, 2, 3], [2, 3, 4])
        # |residuals| = [1, 1, 1], MAE = 1
        assert m.mae_result.value == pytest.approx(1.0)


class TestBias:
    """Tests for Bias computation."""

    def test_bias_zero_for_perfect(self):
        """Bias is 0 for perfect predictions."""
        m = compute_validation_metrics([1, 2, 3], [1, 2, 3])
        assert m.bias_result.value == pytest.approx(0.0)

    def test_bias_positive_when_overestimating(self):
        """Positive bias means model overestimates."""
        m = compute_validation_metrics([1, 2, 3], [2, 3, 4])
        assert m.bias_result.value == pytest.approx(1.0)

    def test_bias_negative_when_underestimating(self):
        """Negative bias means model underestimates."""
        m = compute_validation_metrics([3, 4, 5], [2, 3, 4])
        assert m.bias_result.value == pytest.approx(-1.0)


class TestRSquared:
    """Tests for R² with edge-case handling."""

    def test_r_squared_perfect(self):
        """R² is 1.0 for perfect predictions."""
        result = compute_r_squared_with_notes([1, 2, 3], [1, 2, 3])
        assert result.value == pytest.approx(1.0)
        assert result.notes == []

    def test_r_squared_known_value(self):
        """R² matches hand-computed value."""
        # obs = [1, 2, 3], pred = [2, 3, 4]
        # SS_res = 3, SS_tot = 2, R² = 1 - 3/2 = -0.5
        result = compute_r_squared_with_notes([1, 2, 3], [2, 3, 4])
        assert result.value == pytest.approx(-0.5)

    def test_r_squared_zero_variance_returns_none(self):
        """R² is None when all observations are identical (SS_tot=0)."""
        # obs = [5, 5, 5], pred = [4, 5, 6]
        # SS_tot = 0 -> undefined
        result = compute_r_squared_with_notes([5, 5, 5], [4, 5, 6])
        assert result.value is None
        assert len(result.notes) > 0
        assert "undefined" in result.notes[0].lower() or "zero" in result.notes[0].lower()

    def test_r_squared_zero_variance_perfect_pred(self):
        """R² is None even for perfect prediction when all obs identical."""
        result = compute_r_squared_with_notes([5, 5, 5], [5, 5, 5])
        assert result.value is None
        assert "undefined" in result.notes[0].lower()

    def test_r_squared_negative_for_poor_fit(self):
        """R² can be negative when model is worse than the mean."""
        m = compute_validation_metrics([10, 20, 30], [1, 1, 1])
        assert m.r_squared_result.value < 0


class TestMAPE:
    """Tests for MAPE with edge-case handling."""

    def test_mape_known_value(self):
        """MAPE matches hand-computed value."""
        result = compute_mape_with_notes([100, 200, 300], [110, 190, 330])
        # errors: 10/100=0.1, 10/200=0.05, 30/300=0.1
        # MAPE = (0.1+0.05+0.1)/3 * 100 = 8.333...
        assert result.value == pytest.approx((0.1 + 0.05 + 0.1) / 3 * 100)

    def test_mape_zero_observation_returns_none(self):
        """MAPE is None when any observation is exactly zero."""
        result = compute_mape_with_notes([0, 100, 200], [0, 110, 190])
        assert result.value is None
        assert len(result.notes) > 0
        assert "zero" in result.notes[0].lower()

    def test_mape_near_zero_observation_returns_none(self):
        """MAPE is None when observation is near zero (below threshold)."""
        result = compute_mape_with_notes([1e-15, 100], [5, 110])
        assert result.value is None
        assert "zero" in result.notes[0].lower()

    def test_mape_all_nonzero_succeeds(self):
        """MAPE computes normally when all observations are non-zero."""
        result = compute_mape_with_notes([1, 2, 3], [1.1, 2.1, 2.9])
        assert result.value is not None
        assert result.value > 0


class TestValidationMetricsBundle:
    """Tests for the compute_validation_metrics bundle."""

    def test_all_fields_populated(self):
        """ValidationMetrics has all expected fields."""
        m = compute_validation_metrics([1, 2, 3, 4, 5], [1.1, 2.1, 2.9, 4.1, 4.8])
        assert m.rmse_result.value is not None
        assert m.mae_result.value is not None
        assert m.bias_result.value is not None
        assert m.r_squared_result.value is not None  # obs have variance
        assert m.mape_result.value is not None  # no zero obs
        assert m.n_samples == 5
        assert m.common_unit == "t/ha"

    def test_mean_observed_and_predicted(self):
        """Means are computed correctly."""
        m = compute_validation_metrics([1, 2, 3], [2, 3, 4])
        assert m.mean_observed == pytest.approx(2.0)
        assert m.mean_predicted == pytest.approx(3.0)

    def test_r_squared_none_when_zero_variance_in_bundle(self):
        """Bundle correctly reports R² as None for zero-variance obs."""
        m = compute_validation_metrics([5, 5, 5], [4, 6, 5])
        assert m.r_squared_result.value is None
        # MAPE should compute since 5 is non-zero
        assert m.mape_result.value is not None
        # Actually MAPE should compute since 5 is non-zero
        assert m.mape_result.value is not None

    def test_mape_none_when_zero_obs_in_bundle(self):
        """Bundle correctly reports MAPE as None for zero observations."""
        m = compute_validation_metrics([0, 10, 20], [1, 9, 21])
        assert m.mape_result.value is None
        assert "zero" in m.mape_result.notes[0].lower()

    def test_metric_result_to_dict(self):
        """MetricResult serializes to dict."""
        result = MetricResult(
            name="test", value=1.5, unit="t/ha", n_samples=3, notes=["note"]
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert d["value"] == 1.5
        assert d["n_samples"] == 3
        assert d["notes"] == ["note"]

    def test_empty_arrays_raise(self):
        """Empty input arrays raise ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            compute_validation_metrics([], [])

    def test_nan_input_raises(self):
        """NaN inputs raise ValueError."""
        with pytest.raises(ValueError, match="NaN or Inf"):
            compute_validation_metrics([1, float("nan")], [1, 2])

    def test_length_mismatch_raises(self):
        """Mismatched lengths raise ValueError."""
        with pytest.raises(ValueError, match="length mismatch"):
            compute_validation_metrics([1, 2, 3], [1, 2])
