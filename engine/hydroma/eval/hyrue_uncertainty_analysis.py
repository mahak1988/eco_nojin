"""HY-RUE uncertainty analysis using cluster bootstrap.

Performs cluster bootstrap at the district level to estimate uncertainty
in HY-RUE yield predictions. District-level resampling accounts for
spatial correlation of records within the same district.

If the number of independent districts is insufficient for valid
bootstrap, the uncertainty is reported as BLOCKED with an explicit
limitation note.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

UNCERTAINTY_RESULTS_PATH = Path(
    "engine/reports/data/stage36_uncertainty_results.json"
)

#: Minimum number of independent districts for valid cluster bootstrap.
MIN_DISTRICTS_FOR_BOOTSTRAP = 3


@dataclass
class UncertaintyResult:
    """Uncertainty analysis results.

    Attributes:
        method: Uncertainty method used ("cluster_bootstrap", "blocked", etc.).
        n_bootstrap_samples: Number of bootstrap samples.
        n_districts: Number of independent districts.
        rmse_mean: Mean RMSE across bootstrap samples.
        rmse_std: Standard deviation of RMSE across bootstrap samples.
        rmse_ci_lower: Lower bound of RMSE confidence interval.
        rmse_ci_upper: Upper bound of RMSE confidence interval.
        mae_mean: Mean MAE across bootstrap samples.
        mae_std: Standard deviation of MAE.
        bias_mean: Mean bias across bootstrap samples.
        bias_std: Standard deviation of bias.
        r2_mean: Mean R² across bootstrap samples.
        r2_std: Standard deviation of R².
        blocked_reason: Reason if uncertainty analysis is blocked.
        notes: Human-readable notes.
    """

    method: str
    n_bootstrap_samples: int
    n_districts: int
    rmse_mean: float | None = None
    rmse_std: float | None = None
    rmse_ci_lower: float | None = None
    rmse_ci_upper: float | None = None
    mae_mean: float | None = None
    mae_std: float | None = None
    bias_mean: float | None = None
    bias_std: float | None = None
    r2_mean: float | None = None
    r2_std: float | None = None
    blocked_reason: str | None = None
    notes: list[str] = field(default_factory=list)


def cluster_bootstrap_uncertainty(
    record_results: list[dict[str, Any]],
    n_bootstrap: int = 1000,
    random_seed: int = 42,
    ci_level: float = 0.95,
) -> UncertaintyResult:
    """Perform cluster bootstrap uncertainty analysis.

    Resamples districts (not individual records) to account for spatial
    correlation within districts. For each bootstrap sample:
    1. Sample districts with replacement
    2. Include all records from sampled districts
    3. Compute RMSE, MAE, Bias, R² on the bootstrap sample

    Args:
        record_results: List of record result dicts with 'district',
            'observed_yield', 'predicted_yield', 'computation_status'.
        n_bootstrap: Number of bootstrap samples.
        random_seed: Random seed for reproducibility.
        ci_level: Confidence level for CI (default 0.95).

    Returns:
        UncertaintyResult with bootstrap statistics or blocked reason.
    """
    rng = np.random.default_rng(random_seed)

    # Filter to successful records
    successful = [
        r for r in record_results
        if r.get("computation_status") == "success"
        and r.get("observed_yield") is not None
        and r.get("predicted_yield") is not None
    ]

    if len(successful) == 0:
        return UncertaintyResult(
            method="cluster_bootstrap",
            n_bootstrap_samples=0,
            n_districts=0,
            blocked_reason="No successful records for uncertainty analysis",
            notes=["No records with both observed and predicted yield."],
        )

    # Group by district
    districts: dict[str, list[dict[str, Any]]] = {}
    for r in successful:
        district = r.get("district", "unknown")
        districts.setdefault(district, []).append(r)

    district_names = list(districts.keys())
    n_districts = len(district_names)

    if n_districts < MIN_DISTRICTS_FOR_BOOTSTRAP:
        return UncertaintyResult(
            method="cluster_bootstrap",
            n_bootstrap_samples=0,
            n_districts=n_districts,
            blocked_reason=(
                f"Insufficient independent districts ({n_districts}) for "
                f"valid cluster bootstrap (minimum {MIN_DISTRICTS_FOR_BOOTSTRAP})"
            ),
            notes=[
                f"Only {n_districts} districts available. "
                f"Minimum {MIN_DISTRICTS_FOR_BOOTSTRAP} required."
            ],
        )

    # Bootstrap
    rng = np.random.default_rng(random_seed)
    rmse_samples = []
    mae_samples = []
    bias_samples = []
    r2_samples = []

    for _ in range(n_bootstrap):
        # Sample districts with replacement
        sampled_districts = rng.choice(
            district_names, size=n_districts, replace=True
        )

        # Collect all records from sampled districts
        sample_records = []
        for d in sampled_districts:
            sample_records.extend(districts[d])

        observed = np.array([r["observed_yield"] for r in sample_records])
        predicted = np.array([r["predicted_yield"] for r in sample_records])

        # RMSE
        rmse = float(np.sqrt(np.mean((predicted - observed) ** 2)))
        rmse_samples.append(rmse)

        # MAE
        mae = float(np.mean(np.abs(predicted - observed)))
        mae_samples.append(mae)

        # Bias
        bias = float(np.mean(predicted - observed))
        bias_samples.append(bias)

        # R²
        ss_res = np.sum((observed - predicted) ** 2)
        ss_tot = np.sum((observed - np.mean(observed)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
        r2_samples.append(r2)

    # Compute statistics
    alpha = 1 - ci_level
    ci_lower_pct = (alpha / 2) * 100
    ci_upper_pct = (1 - alpha / 2) * 100

    return UncertaintyResult(
        method="cluster_bootstrap",
        n_bootstrap_samples=n_bootstrap,
        n_districts=n_districts,
        rmse_mean=float(np.mean(rmse_samples)),
        rmse_std=float(np.std(rmse_samples)),
        rmse_ci_lower=float(np.percentile(rmse_samples, ci_lower_pct)),
        rmse_ci_upper=float(np.percentile(rmse_samples, ci_upper_pct)),
        mae_mean=float(np.mean(mae_samples)),
        mae_std=float(np.std(mae_samples)),
        bias_mean=float(np.mean(bias_samples)),
        bias_std=float(np.std(bias_samples)),
        r2_mean=float(np.mean(r2_samples)),
        r2_std=float(np.std(r2_samples)),
        notes=[
            f"Cluster bootstrap with {n_bootstrap} samples, "
            f"{n_districts} districts.",
            "Resampling unit: district (accounts for spatial correlation).",
        ],
    )


def save_uncertainty_results(
    result: UncertaintyResult,
    output_path: Path | None = None,
) -> None:
    """Save uncertainty results to JSON."""
    out_path = output_path or UNCERTAINTY_RESULTS_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "method": result.method,
        "n_bootstrap_samples": result.n_bootstrap_samples,
        "n_districts": result.n_districts,
        "rmse_mean": result.rmse_mean,
        "rmse_std": result.rmse_std,
        "rmse_ci_lower": result.rmse_ci_lower,
        "rmse_ci_upper": result.rmse_ci_upper,
        "mae_mean": result.mae_mean,
        "mae_std": result.mae_std,
        "bias_mean": result.bias_mean,
        "bias_std": result.bias_std,
        "r2_mean": result.r2_mean,
        "r2_std": result.r2_std,
        "blocked_reason": result.blocked_reason,
        "notes": result.notes,
        "saved_at": datetime.now(UTC).isoformat(),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)


if __name__ == "__main__":
    # Example with synthetic data for testing
    np.random.seed(42)
    n_records = 50
    districts = ["Buxar", "Muzaffarpur", "Rohtas", "Begusarai", "Bhojpur"]
    synthetic_records = []
    for i in range(n_records):
        obs = np.random.uniform(3, 8)
        pred = obs + np.random.normal(0, 1.5)
        synthetic_records.append({
            "district": districts[i % len(districts)],
            "observed_yield": obs,
            "predicted_yield": pred,
            "computation_status": "success",
        })

    result = cluster_bootstrap_uncertainty(synthetic_records)
    print("=" * 60)
    print("Stage 36 Uncertainty Analysis (synthetic test data)")
    print("=" * 60)
    print(f"Method: {result.method}")
    print(f"Districts: {result.n_districts}")
    print(f"Bootstrap samples: {result.n_bootstrap_samples}")
    if result.rmse_mean is not None:
        print(f"RMSE: {result.rmse_mean:.3f} +/- {result.rmse_std:.3f}")
        print(f"RMSE 95% CI: [{result.rmse_ci_lower:.3f}, {result.rmse_ci_upper:.3f}]")
        print(f"MAE: {result.mae_mean:.3f} +/- {result.mae_std:.3f}")
        print(f"Bias: {result.bias_mean:+.3f} +/- {result.bias_std:.3f}")
        print(f"R²: {result.r2_mean:.3f} +/- {result.r2_std:.3f}")
    else:
        print(f"Blocked: {result.blocked_reason}")
    for note in result.notes:
        print(f"  - {note}")
    save_uncertainty_results(result)
    print(f"\nResults saved to {UNCERTAINTY_RESULTS_PATH}")
