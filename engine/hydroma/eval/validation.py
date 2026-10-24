"""Validation utilities for evaluating model outputs against references.

Provides a structured way to run validation checks against reference
datasets, including cross-validation support for k-fold splits.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from engine.hydroma.eval.metrics import (
    EvaluationResult,
    compute_metrics,
    relative_error,
)


@dataclass
class ValidationSummary:
    """Summary of a validation run against a reference."""

    metric_name: str
    computed_value: float
    reference_value: float
    tolerance: float
    passed: bool
    relative_error: float
    reference_source: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "computed_value": self.computed_value,
            "reference_value": self.reference_value,
            "tolerance": self.tolerance,
            "passed": self.passed,
            "relative_error": self.relative_error,
            "reference_source": self.reference_source,
            "notes": self.notes,
        }


def validate_against_reference(
    computed_value: float,
    reference_value: float,
    reference_source: str,
    tolerance: float = 0.1,
    metric_name: str = "value",
) -> ValidationSummary:
    """Validate a computed scalar against a reference value.

    Args:
        computed_value: The model's output value.
        reference_value: The accepted reference value.
        reference_source: Description of where the reference came from.
        tolerance: Maximum acceptable relative error (fraction, e.g. 0.1 = 10%).
        metric_name: Human-readable name for the metric being validated.

    Returns:
        A :class:`ValidationSummary`.
    """
    rel_err = relative_error(computed_value, reference_value)
    passed = rel_err <= tolerance

    return ValidationSummary(
        metric_name=metric_name,
        computed_value=float(computed_value),
        reference_value=float(reference_value),
        tolerance=tolerance,
        passed=passed,
        relative_error=rel_err,
        reference_source=reference_source,
    )


@dataclass
class CrossValidationResult:
    """Results from a k-fold cross-validation."""

    fold_metrics: list[EvaluationResult]
    mean_rmse: float
    std_rmse: float
    mean_mae: float
    mean_r_squared: float
    n_folds: int
    fold_notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_folds": self.n_folds,
            "mean_rmse": self.mean_rmse,
            "std_rmse": self.std_rmse,
            "mean_mae": self.mean_mae,
            "mean_r_squared": self.mean_r_squared,
            "fold_rmse_values": [m.rmse_value for m in self.fold_metrics],
        }


def cross_validate(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
    k: int = 5,
    metric_fn: Callable | None = None,
) -> CrossValidationResult:
    """Run k-fold cross-validation on paired observations.

    Args:
        observed: Reference values.
        predicted: Model predictions.
        k: Number of folds.
        metric_fn: Optional custom metric function(obs, pred) -> float.
            Defaults to RMSE.

    Returns:
        CrossValidationResult with per-fold metrics.
    """
    obs = np.asarray(observed, dtype=float).ravel()
    pred = np.asarray(predicted, dtype=float).ravel()
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")
    if obs.size < k:
        raise ValueError(f"need at least {k} samples for {k}-fold CV, got {obs.size}")

    metric_fn = metric_fn or (lambda o, p: float(np.sqrt(np.mean((p - o) ** 2))))

    fold_size = obs.size // k
    fold_metrics: list[EvaluationResult] = []

    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else obs.size
        fold_result = compute_metrics(obs[start:end], pred[start:end])
        fold_metrics.append(fold_result)

    rmse_values = [m.rmse_value for m in fold_metrics]
    return CrossValidationResult(
        fold_metrics=fold_metrics,
        mean_rmse=float(np.mean(rmse_values)),
        std_rmse=float(np.std(rmse_values, ddof=1)) if len(rmse_values) > 1 else 0.0,
        mean_mae=float(np.mean([m.mae_value for m in fold_metrics])),
        mean_r_squared=float(np.mean([m.r_squared_value for m in fold_metrics])),
        n_folds=k,
    )