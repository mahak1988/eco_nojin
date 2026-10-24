"""External validation metrics with strict edge-case handling.

This module extends the basic metrics in :mod:`engine.hydroma.eval.metrics`
with proper handling of degenerate inputs:

- **R² (zero variance):** when all observed values are identical
  (``SS_tot == 0``), R² is mathematically undefined.  It is reported as
  ``None`` with an explanatory note rather than silently returning 0 or 1.

- **MAPE (zero observations):** MAPE is only computed when ``all(abs(obs) > 0)``.
  If any observed value is exactly zero, MAPE is ``None`` with a note
  explaining the division-by-zero avoidance.

All functions return :class:`MetricResult` so callers receive both the
numeric value (or ``None``) and a machine-readable explanation.

This module is import-safe: numpy + dataclasses only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from engine.hydroma.eval.metrics import (
    bias,
    mae,
    rmse,
)


@dataclass
class MetricResult:
    """A single metric value with optional explanatory notes.

    Attributes:
        name: Human-readable metric name.
        value: The numeric result, or ``None`` if undefined.
        unit: Unit of the metric (``"t/ha"``, ``"dimensionless"``, etc.).
        n_samples: Number of paired observations used.
        notes: Explanatory notes (e.g. why a metric is undefined).
    """

    name: str
    value: float | None
    unit: str
    n_samples: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "n_samples": self.n_samples,
            "notes": list(self.notes),
        }


@dataclass
class ValidationMetrics:
    """Bundle of all validation metrics for an evaluation run.

    Attributes:
        rmse_result: RMSE in the common unit.
        mae_result: MAE in the common unit.
        bias_result: Bias in the common unit.
        r_squared_result: R² (dimensionless, may be None).
        mape_result: MAPE in percent (may be None).
        n_samples: Number of paired (prediction, observation) records.
        mean_observed: Mean of observed values.
        mean_predicted: Mean of predicted values.
        common_unit: The unit conversions were normalized to.
    """

    rmse_result: MetricResult
    mae_result: MetricResult
    bias_result: MetricResult
    r_squared_result: MetricResult
    mape_result: MetricResult
    n_samples: int
    mean_observed: float
    mean_predicted: float
    common_unit: str = "t/ha"


def _coerce_pair(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
) -> tuple[np.ndarray, np.ndarray]:
    """Coerce observed and predicted to equal-length float arrays."""
    obs = np.asarray(observed, dtype=float).ravel()
    pred = np.asarray(predicted, dtype=float).ravel()
    if obs.size == 0 or pred.size == 0:
        raise ValueError("input arrays must not be empty")
    if obs.size != pred.size:
        raise ValueError(
            f"length mismatch: {obs.size} observed vs {pred.size} predicted"
        )
    if not np.all(np.isfinite(obs)):
        raise ValueError("observed array must not contain NaN or Inf")
    if not np.all(np.isfinite(pred)):
        raise ValueError("predicted array must not contain NaN or Inf")
    return obs, pred


def compute_r_squared_with_notes(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
) -> MetricResult:
    """R² with explicit handling of zero-variance observed data.

    When ``SS_tot == 0`` (all observations identical), R² is undefined
    and reported as ``None`` with a note — never silently returned as
    0.0 or 1.0.
    """
    obs, pred = _coerce_pair(observed, predicted)
    n = obs.size
    ss_res = float(np.sum((obs - pred) ** 2))
    ss_tot = float(np.sum((obs - np.mean(obs)) ** 2))

    if ss_tot == 0:
        return MetricResult(
            name="r_squared",
            value=None,
            unit="dimensionless",
            n_samples=n,
            notes=[
                "R² is undefined when all observed values are identical "
                "(SS_tot=0). The model cannot be distinguished from the "
                "mean baseline."
            ],
        )

    r2 = 1.0 - ss_res / ss_tot
    return MetricResult(
        name="r_squared",
        value=float(r2),
        unit="dimensionless",
        n_samples=n,
        notes=[],
    )


def compute_mape_with_notes(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
    zero_threshold: float = 1e-12,
) -> MetricResult:
    """MAPE with explicit handling of zero-valued observations.

    MAPE is only computed when ``all(abs(obs) > zero_threshold)``.
    If any observed value is exactly (or near) zero, MAPE is ``None``
    with a note explaining the division-by-zero avoidance.
    """
    obs, pred = _coerce_pair(observed, predicted)
    n = obs.size

    near_zero = [i for i, v in enumerate(obs) if abs(v) <= zero_threshold]
    if near_zero:
        return MetricResult(
            name="mape",
            value=None,
            unit="percent",
            n_samples=n,
            notes=[
                f"MAPE is undefined when any observed value is zero "
                f"or near-zero ({len(near_zero)} of {n} values |obs| <= "
                f"{zero_threshold}). No imputation or epsilon smoothing was "
                f"applied to avoid biasing the metric."
            ],
        )

    mape_val = float(np.mean(np.abs((obs - pred) / np.abs(obs))) * 100)
    return MetricResult(
        name="mape",
        value=mape_val,
        unit="percent",
        n_samples=n,
        notes=[],
    )


def compute_validation_metrics(
    observed: np.ndarray | list[float],
    predicted: np.ndarray | list[float],
    unit: str = "t/ha",
) -> ValidationMetrics:
    """Compute the full suite of validation metrics.

    Args:
        observed: Reference (observed) yield values in ``unit``.
        predicted: Model-predicted yield values in ``unit``.
        unit: The common unit both arrays are expressed in.

    Returns:
        A :class:`ValidationMetrics` bundle with all metrics and notes.
    """
    obs, pred = _coerce_pair(observed, predicted)
    n = obs.size

    rmse_val = float(rmse(obs, pred))
    mae_val = float(mae(obs, pred))
    bias_val = float(bias(obs, pred))
    r2_result = compute_r_squared_with_notes(obs, pred)
    mape_result = compute_mape_with_notes(obs, pred)

    return ValidationMetrics(
        rmse_result=MetricResult(
            name="rmse", value=rmse_val, unit=unit, n_samples=n
        ),
        mae_result=MetricResult(
            name="mae", value=mae_val, unit=unit, n_samples=n
        ),
        bias_result=MetricResult(
            name="bias", value=bias_val, unit=unit, n_samples=n
        ),
        r_squared_result=r2_result,
        mape_result=mape_result,
        n_samples=n,
        mean_observed=float(np.mean(obs)),
        mean_predicted=float(np.mean(pred)),
        common_unit=unit,
    )
