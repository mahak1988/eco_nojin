"""Stage 41 — Part 3/4/5: baseline reconstruction, R2 attribution, grouping.

Produces ``stage41_analysis.json`` containing:

* the like-for-like baseline-vs-calibrated comparison on the **same**
  records with the same inputs;
* the validation of the epsilon-linearity reconstruction of the baseline
  against the real Stage 40 baseline predictions;
* the mean-predictor reference model (diagnostic only);
* per-record error analysis (error, |error|, error^2, contribution);
* error attribution by district, season, observed-yield band, input
  quality, LAI/EWSI status, weather validity and satellite acquisitions;
* structural error checks (regression to the mean, bias sign by group).

No parameter, weight, or model selection is performed here.  The
evaluation-set mean is used only to compute the diagnostic reference
model, never to fit or tune HYRUE.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
DATA = ROOT / "engine/reports/data"
S41 = DATA / "stage41_test_benchmark/record_results.jsonl"
S40 = DATA / "stage40_test_benchmark/record_results.jsonl"
FROZEN = DATA / "stage40_frozen_model_config.json"
OUT = DATA / "stage41_analysis.json"

EPS_BASELINE = 2.2
MAPE_EPS = 1e-6


# ----------------------------------------------------------------------
# Metric helpers
# ----------------------------------------------------------------------
def metrics(pairs: list[tuple[float, float]]) -> dict:
    """pairs = [(observed, predicted), ...]"""
    if not pairs:
        return {
            "n": 0, "rmse": None, "mae": None, "bias": None, "r2": None,
            "mape": None, "mape_excluded": 0,
        }
    n = len(pairs)
    ss_res = sum((o - p) ** 2 for o, p in pairs)
    mean_o = sum(o for o, _ in pairs) / n
    ss_tot = sum((o - mean_o) ** 2 for o, _ in pairs)
    rmse = math.sqrt(ss_res / n)
    mae = sum(abs(o - p) for o, p in pairs) / n
    bias = sum(p - o for o, p in pairs) / n
    r2 = None if ss_tot <= 1e-12 else 1.0 - ss_res / ss_tot
    nz = [(o, p) for o, p in pairs if abs(o) > MAPE_EPS]
    mape = (
        sum(abs(p - o) / abs(o) for o, p in nz) / len(nz) * 100.0 if nz else None
    )
    return {
        "n": n,
        "rmse": rmse,
        "mae": mae,
        "bias": bias,
        "r2": r2,
        "mape": mape,
        "mape_excluded": n - len(nz),
        "sst": ss_tot,
        "sse": ss_res,
        "mean_observed": mean_o,
    }


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_stage41_records() -> list[dict]:
    """Load the Stage 41 results, from the merged file and the shard files.

    The merged file is written when the run finishes; the shard files are
    the live state.  Both are read and de-duplicated by record id so the
    analysis can also run while the benchmark is still in flight.
    """
    records: list[dict] = []
    seen: set[str] = set()
    sources = [S41]
    shard_dir = S41.parent / "shards"
    if shard_dir.is_dir():
        sources.extend(sorted(shard_dir.glob("shard_*/record_results.jsonl")))
    for src in sources:
        for rec in load_jsonl(src):
            rid = str(rec.get("record_id"))
            if rid in seen:
                continue
            seen.add(rid)
            records.append(rec)
    return records


def band(value: float | None, edges: list[float]) -> str:
    if value is None:
        return "unknown"
    for e in edges:
        if value <= e:
            return f"<= {e}"
    return f"> {edges[-1]}"


def main() -> int:
    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()

    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    eps_cal = float(frozen["parameter_values"]["epsilon"])
    ratio = EPS_BASELINE / eps_cal

    s41 = load_stage41_records()
    s40 = load_jsonl(S40)
    computed = [r for r in s41 if r.get("predicted_yield") is not None]
    by_id = {str(r["record_id"]): r for r in computed}

    print(f"stage41 records total      : {len(s41)}")
    print(f"stage41 records with result: {len(computed)}")

    # ------------------------------------------------------------------
    # 3.1 Validate the epsilon-linearity reconstruction
    # ------------------------------------------------------------------
    s40_pred = {
        str(r["record_id"]): float(r["predicted_yield"])
        for r in s40
        if r.get("predicted_yield") is not None
    }
    validation = []
    for rid, actual in s40_pred.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        derived = float(rec["predicted_yield"]) * ratio
        validation.append(
            {
                "record_id": rid,
                "baseline_actual": actual,
                "baseline_derived": derived,
                "abs_diff": abs(derived - actual),
            }
        )
    n_val = len(validation)
    n_within = sum(
        1
        for v in validation
        if v["abs_diff"] <= 1e-9 * max(1.0, abs(v["baseline_actual"]))
    )
    max_abs = max((v["abs_diff"] for v in validation), default=None)
    identity = {
        "method": (
            "HYRUE's seasonal yield is Y = epsilon * S * HI / 100, exactly "
            "linear in epsilon; the baseline prediction is therefore the "
            "calibrated prediction scaled by epsilon_base/epsilon_cal."
        ),
        "conditions": {
            "equation_linear_in_epsilon": True,
            "all_other_factors_identical": True,
            "no_epsilon_dependent_clamp_or_postprocessing": True,
            "no_unit_lai_ewsi_or_par_difference": True,
            "confirmed_against_real_baseline_runs": n_within == n_val and n_val > 0,
        },
        "records_compared": n_val,
        "records_within_1e-9": n_within,
        "max_abs_difference_t_ha": max_abs,
        "validated": bool(n_val > 0 and n_within == n_val),
        "tolerance": "abs diff <= 1e-9 * max(1, |actual|)",
    }

    # ------------------------------------------------------------------
    # 3.2 Like-for-like comparison on the shared records
    # ------------------------------------------------------------------
    # The baseline is preferred from the in-pass dual evaluation (same
    # resolved inputs, same code path).  The epsilon-linear reconstruction
    # is only a fallback for records where the in-pass baseline is absent.
    overall_pairs = []
    n_inpass = 0
    for rec in computed:
        obs = float(rec["observed_yield"])
        cal = float(rec["predicted_yield"])
        base_val = rec.get("baseline_predicted_yield")
        if base_val is None:
            base_val = cal * ratio
        else:
            n_inpass += 1
        overall_pairs.append((obs, cal, rec, float(base_val)))

    def pairs_of(items):
        return [(o, p) for o, p, _, _ in items]

    cal_metrics = metrics(pairs_of(overall_pairs))
    base_metrics = metrics([(o, b) for o, _, _, b in overall_pairs])
    reconstructed_metrics = metrics(
        [(o, p * ratio) for o, p, _, _ in overall_pairs]
    )

    # Mean-predictor reference (diagnostic only).
    eval_mean = cal_metrics["mean_observed"]
    mean_ref = metrics([(o, eval_mean) for o, _, _, _ in overall_pairs])

    # ------------------------------------------------------------------
    # 4.1 Observed-yield distribution
    # ------------------------------------------------------------------
    obs_values = [float(r["observed_yield"]) for r in computed]
    obs_sorted = sorted(obs_values)
    quartiles = (
        statistics.quantiles(obs_sorted, n=4)
        if len(obs_sorted) >= 4
        else None
    )
    mean_obs = statistics.fmean(obs_values) if obs_values else None
    sd_obs = statistics.stdev(obs_values) if len(obs_values) > 1 else None
    near_zero = sum(1 for v in obs_values if abs(v) <= MAPE_EPS)
    low = [v for v in obs_values if v < 0.5]
    outliers = [
        v for v in obs_values
        if mean_obs is not None and sd_obs is not None
        and abs(v - mean_obs) > 3 * sd_obs
    ]
    observed_stats = {
        "n": len(obs_values),
        "mean": mean_obs,
        "median": statistics.median(obs_values) if obs_values else None,
        "stdev": sd_obs,
        "min": min(obs_values) if obs_values else None,
        "max": max(obs_values) if obs_values else None,
        "q1": quartiles[0] if quartiles else None,
        "q3": quartiles[2] if quartiles else None,
        "iqr": (quartiles[2] - quartiles[0]) if quartiles else None,
        "n_exact_zero": near_zero,
        "n_below_0_5_t_ha": len(low),
        "n_3sigma_outliers": len(outliers),
        "outlier_values": sorted(outliers)[:20],
        "by_district": {
            d: {
                "n": len(vals),
                "mean": statistics.fmean(vals),
                "median": statistics.median(vals),
                "stdev": statistics.stdev(vals) if len(vals) > 1 else None,
                "min": min(vals),
                "max": max(vals),
            }
            for d, vals in sorted(
                {
                    d: [float(r["observed_yield"]) for r in computed
                        if str(r.get("district_id")) == d]
                    for d in {str(r.get("district_id")) for r in computed}
                }.items()
            )
        },
        "by_season": {
            s: {
                "n": len(vals),
                "mean": statistics.fmean(vals),
                "median": statistics.median(vals),
                "stdev": statistics.stdev(vals) if len(vals) > 1 else None,
            }
            for s, vals in sorted(
                {
                    s: [float(r["observed_yield"]) for r in computed
                        if str(r.get("season")) == s]
                    for s in {str(r.get("season")) for r in computed}
                }.items()
            )
        },
    }

    # ------------------------------------------------------------------
    # 4.3/4.4 Per-record error analysis
    # ------------------------------------------------------------------
    records = []
    for obs, cal, rec, base_val in overall_pairs:
        e = cal - obs
        records.append(
            {
                "record_id": str(rec["record_id"]),
                "district_id": str(rec.get("district_id")),
                "season": str(rec.get("season")),
                "observed": obs,
                "calibrated": cal,
                "baseline": base_val,
                "baseline_in_pass": rec.get("baseline_predicted_yield") is not None,
                "error": e,
                "abs_error": abs(e),
                "squared_error": e * e,
                "baseline_error": base_val - obs,
                "baseline_abs_error": abs(base_val - obs),
                "observed_band": band(obs, [2.0, 3.5, 5.0, 7.0]),
                "input_quality": str(rec.get("input_quality_status")),
                "lai_status": str(rec.get("lai_status")),
                "ewsi_status": str(rec.get("ewsi_status")),
                "par_status": str(rec.get("par_status")),
                "weather_source": str(rec.get("weather_source")),
                "weather_valid_days": rec.get("weather_valid_days"),
                "weather_coverage": rec.get("weather_coverage"),
                "satellite_acquisition_count": rec.get(
                    "satellite_acquisition_count"
                ),
                "satellite_coverage": rec.get("satellite_coverage"),
                "data_hash": rec.get("data_hash"),
            }
        )

    total_sse = sum(r["squared_error"] for r in records) or 1.0
    for r in records:
        r["sse_contribution_pct"] = 100.0 * r["squared_error"] / total_sse

    top_abs = sorted(records, key=lambda r: -r["abs_error"])[:25]
    top_sse = sorted(records, key=lambda r: -r["squared_error"])[:25]

    # ------------------------------------------------------------------
    # 4.5 Structural error checks
    # ------------------------------------------------------------------
    cal_values = [r["calibrated"] for r in records]
    structural = {
        "prediction_range": {
            "predicted_min": min(cal_values) if cal_values else None,
            "predicted_max": max(cal_values) if cal_values else None,
            "predicted_mean": statistics.fmean(cal_values) if cal_values else None,
            "predicted_stdev": (
                statistics.stdev(cal_values) if len(cal_values) > 1 else None
            ),
            "observed_min": observed_stats["min"],
            "observed_max": observed_stats["max"],
            "observed_mean": mean_obs,
            "observed_stdev": sd_obs,
        },
        "regression_to_the_mean": {
            "pearson_r_pred_obs": _pearson(cal_values, obs_values),
            "note": (
                "A prediction range narrower than the observed range with "
                "r < 1 indicates shrinkage toward the mean."
            ),
        },
        "bias_by_observed_band": {},
        "under_over_estimation": {
            "n_overpredicted": sum(1 for r in records if r["error"] > 0),
            "n_underpredicted": sum(1 for r in records if r["error"] < 0),
            "n_exact": sum(1 for r in records if r["error"] == 0),
        },
    }
    for b, items in sorted(
        {b: [r for r in records if r["observed_band"] == b]
         for b in {r["observed_band"] for r in records}}.items()
    ):
        m = metrics([(r["observed"], r["calibrated"]) for r in items])
        structural["bias_by_observed_band"][b] = {
            "n": m["n"], "bias": m["bias"], "rmse": m["rmse"], "r2": m["r2"],
            "mean_observed": m["mean_observed"],
            "mean_predicted": (
                statistics.fmean([r["calibrated"] for r in items]) if items else None
            ),
        }

    # ------------------------------------------------------------------
    # 4.4/5 Group metrics
    # ------------------------------------------------------------------
    def group_by(key: str) -> dict:
        groups = defaultdict(list)
        for r in records:
            groups[r[key]].append(r)
        out = {}
        for g, items in sorted(groups.items()):
            cal = metrics([(r["observed"], r["calibrated"]) for r in items])
            base = metrics([(r["observed"], r["baseline"]) for r in items])
            meanref = metrics(
                [(r["observed"], eval_mean) for r in items]
            )
            out[g] = {
                "calibrated": cal,
                "baseline": base,
                "mean_reference": meanref,
                "mean_observed": cal["mean_observed"],
                "mean_predicted": (
                    statistics.fmean([r["calibrated"] for r in items]) if items else None
                ),
                "n_estimated_inputs": sum(
                    1 for r in items
                    if r["lai_status"] != "observed"
                    or r["ewsi_status"] != "observed"
                    or r["par_status"] != "observed"
                ),
                "n_with_prediction": len(items),
                "sample_size_warning": len(items) < 30,
            }
        return out

    groups = {
        "by_district": group_by("district_id"),
        "by_season": group_by("season"),
        "by_observed_band": group_by("observed_band"),
        "by_input_quality": group_by("input_quality"),
        "by_lai_status": group_by("lai_status"),
        "by_ewsi_status": group_by("ewsi_status"),
        "by_par_status": group_by("par_status"),
        "by_weather_source": group_by("weather_source"),
    }

    # Correlation of |error| with input-quality variables.
    def corr(xs, ys):
        pairs = [(x, y) for x, y in zip(xs, ys, strict=False) if x is not None and y is not None]
        if len(pairs) < 3:
            return None
        return _pearson([p[0] for p in pairs], [p[1] for p in pairs])

    abs_errs = [r["abs_error"] for r in records]
    input_error_correlations = {
        "abs_error_vs_weather_valid_days": corr(
            abs_errs, [r["weather_valid_days"] for r in records]
        ),
        "abs_error_vs_satellite_acquisition_count": corr(
            abs_errs, [r["satellite_acquisition_count"] for r in records]
        ),
        "abs_error_vs_weather_coverage": corr(
            abs_errs, [r["weather_coverage"] for r in records]
        ),
        "abs_error_vs_satellite_coverage": corr(
            abs_errs, [r["satellite_coverage"] for r in records]
        ),
        "abs_error_vs_observed_yield": corr(abs_errs, [r["observed"] for r in records]
                                            ),
    }

    # ------------------------------------------------------------------
    # 3.3 Stage 40 sample vs the full test frame
    # ------------------------------------------------------------------
    s40_ids = {str(r["record_id"]) for r in s40}
    sample_ids = set(by_id) & s40_ids
    s40_metrics = metrics(
        [
            (float(by_id[i]["observed_yield"]), float(by_id[i]["predicted_yield"]))
            for i in sample_ids
            if i in by_id
        ]
    )
    s40_base = metrics(
        [
            (float(by_id[i]["observed_yield"]),
             float(by_id[i]["predicted_yield"]) * ratio)
            for i in sample_ids
            if i in by_id
        ]
    )
    sample_vs_full = {
        "stage40_sample_n": len(sample_ids),
        "stage40_sample_calibrated": s40_metrics,
        "stage40_sample_baseline": s40_base,
        "full_frame_n": len(records),
        "full_frame_calibrated": cal_metrics,
        "full_frame_baseline": base_metrics,
        "sampling": {
            "design": "stratified by district x season, proportional with a floor",
            "preserves_frame_distribution": True,
            "note": (
                "The 450-record sample was drawn proportionally within "
                "district x season strata, so its district and season "
                "composition matches the full frame by design. The "
                "comparison below quantifies the residual difference."
            ),
        },
    }

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------
    status_counts = Counter(str(r.get("execution_status")) for r in s41)
    payload = {
        "stage": 41,
        "generated_from": str(S41),
        "model": {
            "version": frozen["model_version"],
            "model_code_hash": frozen["model_code_hash"],
            "epsilon_calibrated": eps_cal,
            "epsilon_baseline": EPS_BASELINE,
            "hi": float(frozen["parameter_values"]["hi"]),
            "ratio_baseline_over_calibrated": ratio,
        },
        "record_accounting": {
            "manifest_total_records": 1722,
            "records_in_results_file": len(s41),
            "records_with_prediction": len(computed),
            "execution_status_counts": dict(status_counts),
            "counts_sum_equals_records": sum(status_counts.values()) == len(s41),
        },
        "linearity_identity": identity,
        "overall": {
            "calibrated": cal_metrics,
            "baseline": base_metrics,
            "baseline_reconstructed": reconstructed_metrics,
            "baseline_source": (
                "in-pass dual evaluation (same inputs, same code path)"
                if n_inpass == len(overall_pairs)
                else f"in-pass for {n_inpass} of {len(overall_pairs)} records, "
                "epsilon-linear reconstruction for the rest"
            ),
            "n_baseline_in_pass": n_inpass,
            "mean_reference": mean_ref,
            "mean_reference_note": (
                "yhat = mean of the observed yields in this evaluation set. "
                "Diagnostic reference only; this mean is never used to fit "
                "or tune HYRUE."
            ),
        },
        "observed_yield_distribution": observed_stats,
        "structural_error": structural,
        "input_error_correlations": input_error_correlations,
        "groups": groups,
        "sample_vs_full": sample_vs_full,
        "top_absolute_error_records": top_abs,
        "top_squared_error_records": top_sse,
        "all_records": records,
    }

    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print()
    print(f"identity validated : {identity['validated']} "
          f"({identity['records_within_1e-9']}/{identity['records_compared']})")
    print(f"calibrated  rmse {cal_metrics['rmse']}  r2 {cal_metrics['r2']}")
    print(f"baseline    rmse {base_metrics['rmse']}  r2 {base_metrics['r2']}")
    print(f"mean ref    rmse {mean_ref['rmse']}  r2 {mean_ref['r2']}")
    print(f"written: {OUT}")
    return 0


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


if __name__ == "__main__":
    raise SystemExit(main())
