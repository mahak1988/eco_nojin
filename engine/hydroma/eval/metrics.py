"""Statistical metrics for model evaluation.

All functions are independent of any model internals — they operate on
plain numpy arrays or lists of floats.  This ensures the evaluation
framework can be used to validate any scientific model output without
circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


def _coerce(arr: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
    """Convert input to a 1-D float numpy array, raising on NaN/Inf."""
    result = np.asarray(arr, dtype=float).ravel()
    if result.size == 0:
        raise ValueError("input arrays must not be empty")
    if not np.all(np.isfinite(result)):
        raise ValueError("input arrays must not contain NaN or Inf")
    return result


def rmse(observed: np.ndarray | list[float], predicted: np.ndarray | list[float]) -> float:
    """Root Mean Square Error."""
    obs = _coerce(observed)
    pred = _coerce(predicted)
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")
    residuals = pred - obs
    return float(np.sqrt(np.mean(residuals ** 2)))


def mae(observed: np.ndarray | list[float], predicted: np.ndarray | list[float]) -> float:
    """Mean Absolute Error."""
    obs = _coerce(observed)
    pred = _coerce(predicted)
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")
    return float(np.mean(np.abs(pred - obs)))


def bias(observed: np.ndarray | list[float], predicted: np.ndarray | list[float]) -> float:
    """Mean bias (predicted - observed). Positive = model overestimates."""
    obs = _coerce(observed)
    pred = _coerce(predicted)
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")
    return float(np.mean(pred - obs))


def r_squared(observed: np.ndarray | list[float], predicted: np.ndarray | list[float]) -> float:
    """Coefficient of determination (R²)."""
    obs = _coerce(observed)
    pred = _coerce(predicted)
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")
    ss_res = float(np.sum((obs - pred) ** 2))
    ss_tot = float(np.sum((obs - np.mean(obs)) ** 2))
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1.0 - ss_res / ss_tot


def relative_error(computed: float, reference: float, epsilon: float = 1e-9) -> float:
    """Relative error |computed - reference| / (|reference| + epsilon)."""
    return abs(computed - reference) / (abs(reference) + epsilon)


def mean_absolute_percentage_error(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
    epsilon: float = 1e-9,
) -> float:
    """MAPE in percent.  Uses epsilon to avoid division by zero."""
    obs = _coerce(observed)
    pred = _coerce(predicted)
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")
    return float(np.mean(np.abs((obs - pred) / (np.abs(obs) + epsilon))) * 100)


@dataclass
class EvaluationResult:
    """Metrics computed for a single evaluation run."""

    rmse_value: float
    mae_value: float
    bias_value: float
    r_squared_value: float
    n_samples: int
    mean_observed: float
    mean_predicted: float
    relative_error_pct: float | None = None
    mape_pct: float | None = None
    metric_notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rmse": self.rmse_value,
            "mae": self.mae_value,
            "bias": self.bias_value,
            "r_squared": self.r_squared_value,
            "n_samples": self.n_samples,
            "mean_observed": self.mean_observed,
            "mean_predicted": self.mean_predicted,
            "relative_error_pct": self.relative_error_pct,
            "mape_pct": self.mape_pct,
        }


def compute_metrics(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
    reference_scalar: float | None = None,
) -> EvaluationResult:
    """Compute all evaluation metrics between observed and predicted values.

    Args:
        observed: Reference (observed or accepted) values.
        predicted: Model-predicted values.
        reference_scalar: Optional single reference value for relative
            error computation (e.g. a published yield).

    Returns:
        An :class:`EvaluationResult` with all metrics.
    """
    obs = _coerce(observed)
    pred = _coerce(predicted)
    if obs.size != pred.size:
        raise ValueError(f"length mismatch: {obs.size} vs {pred.size}")

    result = EvaluationResult(
        rmse_value=rmse(obs, pred),
        mae_value=mae(obs, pred),
        bias_value=bias(obs, pred),
        r_squared_value=r_squared(obs, pred),
        n_samples=int(obs.size),
        mean_observed=float(np.mean(obs)),
        mean_predicted=float(np.mean(pred)),
    )

    if reference_scalar is not None:
        if not np.isfinite(reference_scalar) or reference_scalar == 0:
            result.relative_error_pct = None
        else:
            mean_pred = float(np.mean(pred))
            result.relative_error_pct = relative_error(mean_pred, reference_scalar) * 100

    result.mape_pct = mean_absolute_percentage_error(obs, pred)
    return result