"""Bootstrap uncertainty estimation for validation metrics.

Provides confidence intervals for validation metrics that respect the
hierarchical structure of the data (sites, seasons, crops). The bootstrap
resampling is done at the unit of independence (e.g. site-level for
spatial generalization) rather than at the individual-record level,
which would underestimate uncertainty when multiple observations share
a site or growing season.

If there is insufficient data for a meaningful bootstrap (e.g. fewer
than 2 independent units), the uncertainty is reported as
``NOT_ASSESSED`` rather than producing an artificial narrow CI.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

from engine.hydroma.eval.validation_matching import ValidationPair


class UncertaintyStatus(StrEnum):
    """Status of uncertainty estimation."""

    ASSESSED = "assessed"
    NOT_ASSESSED = "not_assessed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class BootstrapResult:
    """Bootstrap confidence interval for a single metric.

    Attributes:
        metric_name: Name of the metric.
        point_estimate: The metric computed on the full sample.
        ci_lower: Lower bound of the confidence interval.
        ci_upper: Upper bound of the confidence interval.
        confidence_level: e.g. 0.95 for a 95% CI.
        bootstrap_sample_count: Number of bootstrap resamples.
        bootstrap_method: Description of the resampling method used.
        status: Whether uncertainty was assessable.
        notes: Explanatory notes.
    """

    metric_name: str
    point_estimate: float
    ci_lower: float | None
    ci_upper: float | None
    confidence_level: float
    bootstrap_sample_count: int
    bootstrap_method: str
    status: UncertaintyStatus
    notes: list[str]


@dataclass
class UncertaintyAssessment:
    """Complete uncertainty assessment for a validation run.

    Attributes:
        assessment_id: Unique identifier.
        metric_results: Per-metric bootstrap results.
        n_independent_units: Number of independent resampling units.
        unit_of_independence: What was resampled (e.g. "site").
        random_seed: Seed used for reproducibility.
    """

    assessment_id: str
    metric_results: list[BootstrapResult]
    n_independent_units: int
    unit_of_independence: str
    random_seed: int


def _group_pairs_by(
    pairs: list[ValidationPair],
    key_func: Callable,
) -> dict[str, list[ValidationPair]]:
    """Group pairs by a key function."""
    groups: dict[str, list[ValidationPair]] = {}
    for p in pairs:
        k = key_func(p)
        groups.setdefault(k, []).append(p)
    return groups


def _resample_indices(
    n_groups: int,
    rng: np.random.Generator,
    n_bootstrap: int,
) -> NDArray[np.int_]:
    """Generate bootstrap resampling indices (with replacement).

    Returns a (n_bootstrap, n_groups) array of indices.
    """
    return rng.integers(0, n_groups, size=(n_bootstrap, n_groups))


def _site_key(p: ValidationPair) -> str:
    return p.site_id


def _field_key(p: ValidationPair) -> str:
    return p.observation.field_id or p.site_id


def _season_key(p: ValidationPair) -> str:
    return p.season_id


def _get_key_func(unit_of_independence: str) -> Callable:
    """Return the appropriate key function for the independence unit."""
    if unit_of_independence == "site":
        return _site_key
    elif unit_of_independence == "field":
        return _field_key
    elif unit_of_independence == "season":
        return _season_key
    raise ValueError(f"unknown unit_of_independence {unit_of_independence!r}")


def compute_metric_on_pairs(
    pairs: list[ValidationPair],
    metric_fn: Callable,
    unit: str = "t/ha",
) -> float:
    """Compute a single metric on a list of pairs.

    Args:
        pairs: List of ValidationPair objects.
        metric_fn: Function (obs_array, pred_array) -> float.
        unit: Common unit for the metric.
    """
    obs = np.array([p.observed_yield_t_ha for p in pairs])
    pred = np.array([p.predicted_yield_t_ha for p in pairs])
    return float(metric_fn(obs, pred))


def bootstrap_metric(
    pairs: list[ValidationPair],
    metric_fn: Callable,
    *,
    unit_of_independence: str = "site",
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
    min_units: int = 2,
    random_seed: int = 42,
) -> BootstrapResult:
    """Bootstrap a confidence interval for a metric, respecting data structure.

    Resamples at the level of the unit of independence (e.g. site) rather than
    at the individual-record level, which avoids anti-conservative confidence
    intervals when observations are clustered within sites.

    Args:
        pairs: All matched validation pairs.
        metric_fn: A function (observed, predicted) -> float.
        unit_of_independence: ``"site"``, ``"field"``, or ``"season"``.
        confidence_level: e.g. 0.95 for 95% CI.
        n_bootstrap: Number of bootstrap resamples.
        min_units: Minimum number of independent units required.
        random_seed: Seed for reproducibility.

    Returns:
        A :class:`BootstrapResult` with the CI (or NOT_ASSESSED status).
    """
    metric_name = getattr(metric_fn, "__name__", "metric")

    if unit_of_independence == "site":
        key_func = _site_key
    elif unit_of_independence == "field":
        key_func = _field_key
    elif unit_of_independence == "season":
        key_func = _season_key
    else:
        raise ValueError(
            f"unknown unit_of_independence {unit_of_independence!r}"
        )

    groups = _group_pairs_by(pairs, key_func)
    group_keys = list(groups.keys())

    if len(group_keys) < min_units:
        return BootstrapResult(
            metric_name=metric_name,
            point_estimate=compute_metric_on_pairs(pairs, metric_fn),
            ci_lower=None,
            ci_upper=None,
            confidence_level=confidence_level,
            bootstrap_sample_count=n_bootstrap,
            bootstrap_method=f"cluster_bootstrap ({unit_of_independence})",
            status=UncertaintyStatus.NOT_ASSESSED,
            notes=[
                f"Insufficient independent units: {len(group_keys)} groups "
                f"available, need >= {min_units} for cluster bootstrap."
            ],
        )

    # Point estimate on full sample
    point_estimate = compute_metric_on_pairs(pairs, metric_fn)

    # Cluster bootstrap: resample groups with replacement, compute metric
    # on resampled pairs
    rng = np.random.default_rng(random_seed)
    boot_stats: list[float] = []

    for _ in range(n_bootstrap):
        # Resample group indices with replacement
        sampled_indices = rng.integers(
            0, len(group_keys), size=len(group_keys)
        )
        boot_pairs: list[ValidationPair] = []
        for idx in sampled_indices:
            boot_pairs.extend(groups[group_keys[idx]])

        if len(boot_pairs) < 2:
            continue

        boot_stat = compute_metric_on_pairs(boot_pairs, metric_fn)
        boot_stats.append(boot_stat)

    if len(boot_stats) < 10:
        return BootstrapResult(
            metric_name=metric_name,
            point_estimate=point_estimate,
            ci_lower=None,
            ci_upper=None,
            confidence_level=confidence_level,
            bootstrap_sample_count=len(boot_stats),
            bootstrap_method=f"cluster_bootstrap ({unit_of_independence})",
            status=UncertaintyStatus.INSUFFICIENT_DATA,
            notes=[
                "Too few bootstrap resamples produced valid results; "
                "uncertainty not assessed."
            ],
        )

    alpha = 1.0 - confidence_level
    ci_lower = float(np.percentile(boot_stats, 100 * alpha / 2))
    ci_upper = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))

    return BootstrapResult(
        metric_name=metric_name,
        point_estimate=point_estimate,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        confidence_level=confidence_level,
        bootstrap_sample_count=n_bootstrap,
        bootstrap_method=f"cluster_bootstrap ({unit_of_independence})",
        status=UncertaintyStatus.ASSESSED,
        notes=[],
    )


def assess_uncertainty(
    pairs: list[ValidationPair],
    *,
    unit_of_independence: str = "site",
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
    min_units: int = 2,
    random_seed: int = 42,
) -> UncertaintyAssessment:
    """Assess uncertainty for all key validation metrics.

    Uses cluster bootstrap at the unit of independence level to respect
    the hierarchical structure of the data.

    Args:
        pairs: All matched validation pairs.
        unit_of_independence: ``"site"``, ``"field"``, or ``"season"``.
        confidence_level: CI confidence level (default 0.95).
        n_bootstrap: Number of bootstrap resamples.
        min_units: Minimum independent units required for each metric.
        random_seed: Reproducibility seed.

    Returns:
        An :class:`UncertaintyAssessment` with per-metric results.
    """
    from engine.hydroma.eval.validation_metrics import bias, mae, rmse

    metrics: list[tuple[str, Callable]] = [
        ("rmse", rmse),
        ("mae", mae),
        ("bias", bias),
    ]

    results: list[BootstrapResult] = []
    for name, fn in metrics:
        result = bootstrap_metric(
            pairs=pairs,
            metric_fn=fn,
            unit_of_independence=unit_of_independence,
            confidence_level=confidence_level,
            n_bootstrap=n_bootstrap,
            min_units=min_units,
            random_seed=random_seed,
        )
        # Ensure the metric name is set correctly
        result.metric_name = name
        results.append(result)

    # Determine independent unit count
    key_func = _get_key_func(unit_of_independence)
    groups = _group_pairs_by(pairs, key_func)

    return UncertaintyAssessment(
        assessment_id=f"UNC-{uuid4().hex[:12].upper()}",
        metric_results=results,
        n_independent_units=len(groups),
        unit_of_independence=unit_of_independence,
        random_seed=random_seed,
    )
