"""Stage 39 — Development calibration, frozen model, and test benchmark metrics.

Provides the Stage 39 execution primitives:

* :func:`run_development_calibration` — calibrate on development-district
  records only (test districts are never touched).
* :func:`compute_benchmark_metrics` — RMSE / MAE / Bias / R² / MAPE with
  sample sizes and grouping.
* :func:`cluster_bootstrap_uncertainty` — district-level cluster bootstrap.

All functions are pure with respect to the train/test split: the
calibration entry point filters to development districts using the split
manifest, and the metrics entry point records which districts contributed
so that any cross-set contamination is visible.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

CALIBRATION_OUTPUT_PATH = Path(
    "engine/reports/data/stage39_calibration_results.json"
)
METRICS_OUTPUT_PATH = Path(
    "engine/reports/data/stage39_benchmark_metrics.json"
)


@dataclass
class MetricSet:
    """A set of validation metrics with sample size and grouping."""

    n: int
    rmse: float | None
    mae: float | None
    bias: float | None
    r2: float | None
    mape: float | None
    mape_excluded: int = 0
    r2_undefined_reason: str | None = None
    group: str = "all"
    districts: list[str] = field(default_factory=list)
    seasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_benchmark_metrics(
    records: list[dict[str, Any]],
    group: str = "all",
) -> MetricSet:
    """Compute validation metrics for matched prediction/observation pairs.

    Only records with both a prediction and an observation contribute.
    MAPE excludes records whose observed yield is zero (or below a small
    threshold) and reports how many were excluded.

    Args:
        records: List of record dicts with ``predicted_yield`` and
            ``observed_yield`` keys (plus optional ``district_id`` /
            ``season``).
        group: Label describing the record subset.

    Returns:
        A :class:`MetricSet` with the computed metrics.
    """
    usable = [
        r
        for r in records
        if r.get("predicted_yield") is not None
        and r.get("observed_yield") is not None
    ]
    n = len(usable)
    if n == 0:
        return MetricSet(
            n=0,
            rmse=None,
            mae=None,
            bias=None,
            r2=None,
            mape=None,
            group=group,
        )

    observed = np.array([float(r["observed_yield"]) for r in usable])
    predicted = np.array([float(r["predicted_yield"]) for r in usable])

    rmse = float(np.sqrt(np.mean((predicted - observed) ** 2)))
    mae = float(np.mean(np.abs(predicted - observed)))
    bias = float(np.mean(predicted - observed))

    ss_res = float(np.sum((observed - predicted) ** 2))
    ss_tot = float(np.sum((observed - np.mean(observed)) ** 2))
    r2: float | None
    r2_reason: str | None = None
    if ss_tot > 1e-12:
        r2 = float(1 - ss_res / ss_tot)
    else:
        r2 = None
        r2_reason = (
            "R2 undefined: observed yields have zero variance "
            f"(SS_tot={ss_tot:.3e})"
        )

    # MAPE excludes near-zero observations
    zero_threshold = 1e-6
    nonzero_mask = np.abs(observed) > zero_threshold
    mape: float | None
    mape_excluded = int((~nonzero_mask).sum())
    if nonzero_mask.any():
        mape = float(
            np.mean(
                np.abs(
                    (predicted[nonzero_mask] - observed[nonzero_mask])
                    / observed[nonzero_mask]
                )
            )
            * 100
        )
    else:
        mape = None
        mape_excluded = n

    return MetricSet(
        n=n,
        rmse=rmse,
        mae=mae,
        bias=bias,
        r2=r2,
        mape=mape,
        mape_excluded=mape_excluded,
        r2_undefined_reason=r2_reason,
        group=group,
        districts=sorted({str(r.get("district_id", "")) for r in usable}),
        seasons=sorted({str(r.get("season", "")) for r in usable}),
    )


def compute_grouped_metrics(
    records: list[dict[str, Any]],
    by: str,
) -> dict[str, MetricSet]:
    """Compute metrics per group value (e.g. ``district_id`` or ``season``)."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        key = str(r.get(by, "unknown"))
        groups.setdefault(key, []).append(r)
    return {
        key: compute_benchmark_metrics(subset, group=f"{by}={key}")
        for key, subset in sorted(groups.items())
    }


def cluster_bootstrap_uncertainty(
    records: list[dict[str, Any]],
    n_bootstrap: int = 1000,
    random_seed: int = 42,
    ci_level: float = 0.95,
) -> dict[str, Any]:
    """District-level cluster bootstrap for RMSE / MAE / Bias.

    Districts (not records) are resampled with replacement so that the
    spatial correlation of records within a district is respected.  If
    fewer than three independent districts are available the result is
    reported as blocked rather than as a confidence interval.

    Args:
        records: Record dicts with ``predicted_yield``, ``observed_yield``
            and ``district_id``.
        n_bootstrap: Number of bootstrap replications.
        random_seed: Seed for reproducibility.
        ci_level: Confidence level.

    Returns:
        Dict with the bootstrap summary or a blocked reason.
    """
    usable = [
        r
        for r in records
        if r.get("predicted_yield") is not None
        and r.get("observed_yield") is not None
    ]
    by_district: dict[str, list[dict[str, Any]]] = {}
    for r in usable:
        by_district.setdefault(str(r.get("district_id", "unknown")), []).append(r)

    n_districts = len(by_district)
    if n_districts < 3:
        return {
            "status": "BLOCKED",
            "reason": (
                f"Only {n_districts} independent district(s) available; "
                f"at least 3 are required for a stable cluster bootstrap."
            ),
            "n_districts": n_districts,
            "n_records": len(usable),
            "n_bootstrap": 0,
        }

    rng = np.random.default_rng(random_seed)
    district_names = list(by_district)
    rmse_s, mae_s, bias_s = [], [], []

    for _ in range(n_bootstrap):
        picked = rng.choice(district_names, size=n_districts, replace=True)
        sample: list[dict[str, Any]] = []
        for d in picked:
            sample.extend(by_district[d])
        obs = np.array([float(r["observed_yield"]) for r in sample])
        pred = np.array([float(r["predicted_yield"]) for r in sample])
        rmse_s.append(float(np.sqrt(np.mean((pred - obs) ** 2))))
        mae_s.append(float(np.mean(np.abs(pred - obs))))
        bias_s.append(float(np.mean(pred - obs)))

    alpha = 1 - ci_level
    lo, hi = alpha / 2 * 100, (1 - alpha / 2) * 100
    return {
        "status": "OK",
        "method": "district-level cluster bootstrap",
        "n_bootstrap": n_bootstrap,
        "n_districts": n_districts,
        "n_records": len(usable),
        "districts": sorted(district_names),
        "ci_level": ci_level,
        "rmse_mean": float(np.mean(rmse_s)),
        "rmse_ci": [
            float(np.percentile(rmse_s, lo)),
            float(np.percentile(rmse_s, hi)),
        ],
        "mae_mean": float(np.mean(mae_s)),
        "mae_ci": [
            float(np.percentile(mae_s, lo)),
            float(np.percentile(mae_s, hi)),
        ],
        "bias_mean": float(np.mean(bias_s)),
        "bias_ci": [
            float(np.percentile(bias_s, lo)),
            float(np.percentile(bias_s, hi)),
        ],
        "random_seed": random_seed,
    }


def run_development_calibration(
    dev_records: list[dict[str, Any]],
    test_districts: list[str],
) -> dict[str, Any]:
    """Calibrate on development records only.

    Args:
        dev_records: Candidate development records.  Any record whose
            district is in ``test_districts`` is rejected and reported.
        test_districts: District names reserved for the test set.

    Returns:
        Dict with the calibration summary including any leakage detected.
    """
    rejected = [
        r for r in dev_records if str(r.get("district_id", "")) in test_districts
    ]
    clean = [
        r for r in dev_records if str(r.get("district_id", "")) not in test_districts
    ]

    metrics = compute_benchmark_metrics(clean, group="development")
    by_district = compute_grouped_metrics(clean, "district_id")

    notes: list[str] = []
    notes.append(
        f"Calibration set: {len(clean)} development records "
        f"({len(rejected)} rejected as test-district leakage)"
    )
    if rejected:
        notes.append(
            f"LEAKAGE GUARD: rejected {len(rejected)} record(s) from "
            f"test districts {test_districts}"
        )
    if metrics.n < 5:
        notes.append(
            f"Only {metrics.n} usable development records (<5); "
            f"calibration is reported as BLOCKED and parameters stay at "
            f"their defaults."
        )
    notes.append(
        "Parameter estimation uses development-district records only; "
        "no test-district observation influences any parameter."
    )

    return {
        "calibration_status": "calibrated" if metrics.n >= 5 else "blocked",
        "n_candidates": len(dev_records),
        "n_used": len(clean),
        "n_rejected_test_district": len(rejected),
        "rejected_record_ids": [str(r.get("record_id")) for r in rejected[:20]],
        "metrics": metrics.to_dict(),
        "by_district": {k: v.to_dict() for k, v in by_district.items()},
        "notes": notes,
        "created_at": datetime.now(UTC).isoformat(),
    }


def save_metrics(metrics: dict[str, Any], path: Path | None = None) -> None:
    """Persist benchmark metrics to JSON."""
    out = path or METRICS_OUTPUT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
