"""Audit persisted Stage 41 artifacts without running the model."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "engine" / "reports" / "data"
SHARDS = DATA / "stage41_test_benchmark" / "shards"
MANIFEST = DATA / "stage41_frozen_model_manifest.json"
SAMPLE = DATA / "stage40_test_sample.json"
ANALYSIS = DATA / "stage41_analysis.json"
REPRO = DATA / "stage41_reproducibility.json"
BLOCKED = DATA / "stage41c_blocked_records.jsonl"
REPORT_JSON = DATA / "stage41d_audit.json"
METRICS_JSON = DATA / "stage41d_metrics.json"
METRICS_MD = ROOT / "engine" / "reports" / "STAGE-41D-METRICS.md"
MERGED_RESULTS = DATA / "stage41_test_benchmark" / "record_results.jsonl"
STAGE40_RESULTS = DATA / "stage40_test_benchmark" / "record_results.jsonl"


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return rows


def metrics(observed: list[float], predicted: list[float]) -> dict[str, float | int]:
    n = len(observed)
    mean_observed = sum(observed) / n
    errors = [p - y for y, p in zip(observed, predicted)]
    sse = sum(error * error for error in errors)
    sst = sum((y - mean_observed) ** 2 for y in observed)
    return {
        "n": n,
        "r2": 1.0 - sse / sst if sst else float("nan"),
        "rmse": math.sqrt(sse / n),
        "mae": sum(abs(error) for error in errors) / n,
        "bias": sum(errors) / n,
        "mape": sum(abs(error / y) for y, error in zip(observed, errors) if y != 0)
        / sum(y != 0 for y in observed)
        * 100,
    }


def main() -> None:
    frozen_manifest = read_json(MANIFEST)
    test_sample = read_json(SAMPLE)
    analysis = read_json(ANALYSIS)
    reproducibility = read_json(REPRO)
    merged_rows = read_jsonl(MERGED_RESULTS) if MERGED_RESULTS.exists() else []
    stage40_rows = read_jsonl(STAGE40_RESULTS) if STAGE40_RESULTS.exists() else []

    frame_path = ROOT / "data" / "external" / "cimmyt_wheat" / "data" / "Wheat_Yld_Eastern_IND_Data.xlsx"
    frame_ids: set[str] = set()
    if frame_path.is_file():
        frame_df = pd.read_excel(frame_path)
        frame_ids = set(
            frame_df.loc[
                frame_df["District"].isin(frozen_manifest["test_set_manifest"]["districts"]),
                "Field_ID",
            ].astype(str)
        )

    all_rows: list[dict[str, Any]] = []
    shard_info: list[dict[str, Any]] = []
    db_states: dict[str, dict[str, str]] = {}
    state_records: dict[str, dict[str, str]] = {}
    log_record_hits: Counter[str] = Counter()
    log_ids: set[str] = set()
    for shard_log in sorted(SHARDS.glob("shard_*.log")):
        text = shard_log.read_text(encoding="utf-8", errors="replace")
        log_ids.update(
            line.split("Processing ", 1)[1].split(" ", 1)[0]
            for line in text.splitlines()
            if "Processing " in line
        )
        shard_info.append(
            {"path": str(shard_log.relative_to(ROOT)), "size_bytes": shard_log.stat().st_size}
        )

    for shard_dir in sorted(path for path in SHARDS.glob("shard_*") if path.is_dir()):
        result_path = shard_dir / "record_results.jsonl"
        state_path = shard_dir / "execution_state.sqlite"
        rows = read_jsonl(result_path) if result_path.exists() else []
        all_rows.extend(rows)
        state: dict[str, str] = {}
        if state_path.exists():
            with sqlite3.connect(state_path) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                if "record_state" in tables:
                    state = {
                        str(record_id): str(status)
                        for record_id, status in connection.execute(
                            "SELECT record_id, status FROM record_state"
                        )
                    }
        db_states[shard_dir.name] = state
        state_records[shard_dir.name] = state
        for item in rows:
            if item.get("record_id"):
                log_record_hits[str(item["record_id"])] += 1
        shard_info.append(
            {
                "path": str(result_path.relative_to(ROOT)),
                "size_bytes": result_path.stat().st_size if result_path.exists() else 0,
                "rows": len(rows),
                "state_rows": len(state),
            }
        )

    row_ids = [str(row["record_id"]) for row in all_rows]
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        by_id[str(row["record_id"])].append(row)

    computed = [
        row for row in all_rows
        if row.get("execution_status") == "COMPUTED"
        and row.get("predicted_yield") is not None
        and row.get("baseline_predicted_yield") is not None
        and row.get("observed_yield") is not None
    ]
    observed = [float(row["observed_yield"]) for row in computed]
    baseline = [float(row["baseline_predicted_yield"]) for row in computed]
    calibrated = [float(row["predicted_yield"]) for row in computed]
    mean_prediction = [sum(observed) / len(observed)] * len(observed) if observed else []
    metric_results = {
        "baseline_epsilon_2_2": metrics(observed, baseline) if observed else {},
        "calibrated_epsilon_2_63": metrics(observed, calibrated) if observed else {},
        "mean_predictor": metrics(observed, mean_prediction) if observed else {},
    }
    stage40_by_id = {
        str(row["record_id"]): row
        for row in stage40_rows
        if row.get("execution_status") == "COMPUTED"
        and row.get("predicted_yield") is not None
        and row.get("observed_yield") is not None
    }
    current_by_id = {
        str(row["record_id"]): row
        for row in computed
    }
    common_ids = sorted(set(stage40_by_id) & set(current_by_id))
    common_rows = [
        (stage40_by_id[record_id], current_by_id[record_id])
        for record_id in common_ids
        if float(stage40_by_id[record_id]["observed_yield"])
        == float(current_by_id[record_id]["observed_yield"])
    ]
    common_observed = [
        float(stage41_row["observed_yield"])
        for _stage40_row, stage41_row in common_rows
    ]
    common_stage40_predictions = [
        float(stage40_row["predicted_yield"])
        for stage40_row, _stage41_row in common_rows
    ]
    common_stage41_baseline = [
        float(stage41_row["baseline_predicted_yield"])
        for _stage40_row, stage41_row in common_rows
    ]
    common_stage41_calibrated = [
        float(stage41_row["predicted_yield"])
        for _stage40_row, stage41_row in common_rows
    ]
    common_mean = (
        [sum(common_observed) / len(common_observed)] * len(common_observed)
        if common_observed else []
    )
    common_metrics = {
        "stage40_calibrated": metrics(common_observed, common_stage40_predictions)
        if common_observed else {},
        "stage41_baseline_epsilon_2_2": metrics(common_observed, common_stage41_baseline)
        if common_observed else {},
        "stage41_calibrated_epsilon_2_63": metrics(common_observed, common_stage41_calibrated)
        if common_observed else {},
        "mean_predictor": metrics(common_observed, common_mean)
        if common_observed else {},
    }

    blocked_rows = read_jsonl(BLOCKED) if BLOCKED.exists() else []
    blocked_counts = Counter(str(row.get("block_reason", "UNKNOWN")) for row in blocked_rows)
    blocked_ids = {str(row.get("record_id")) for row in blocked_rows}
    current_status = Counter(str(row.get("execution_status", "UNKNOWN")) for row in all_rows)
    frame_missing = sorted(frame_ids - set(by_id)) if frame_ids else []
    all_state_records = {
        record_id: status
        for shard_states in state_records.values()
        for record_id, status in shard_states.items()
    }
    running_ids = sorted(
        record_id for record_id, status in all_state_records.items()
        if status == "RUNNING"
    )
    unstarted_ids = sorted(frame_ids - set(all_state_records)) if frame_ids else []
    repro_rows = reproducibility.get("records", [])
    nonrepro = [
        item for item in repro_rows
        if float(item.get("abs_diff_calibrated", 0.0)) > 1e-12
    ]
    repro_input_changes = Counter(
        field
        for item in nonrepro
        for field in item.get("differing_input_fields", [])
    )
    cache_path = DATA / "stage38_cache.sqlite"
    cache_summary: dict[str, Any] = {
        "path": str(cache_path.relative_to(ROOT)),
        "exists": cache_path.is_file(),
        "entries": 0,
        "status_counts": {},
    }
    if cache_path.is_file():
        with sqlite3.connect(cache_path) as connection:
            cache_summary["entries"] = connection.execute(
                "SELECT COUNT(*) FROM cache_entries"
            ).fetchone()[0]
            cache_summary["status_counts"] = dict(
                connection.execute(
                    "SELECT status, COUNT(*) FROM cache_entries GROUP BY status"
                ).fetchall()
            )

    expected_hashes = frozen_manifest.get("code_file_hashes", {})
    model_diff_checks: dict[str, Any] = {}
    for relative_path in (
        "engine/hydroma/eval/identifiability_calibration.py",
        "engine/hydroma/eval/seasonal_predictor.py",
    ):
        log = subprocess.run(
            ["git", "log", "--all", "--format=%H", "--", relative_path],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        matching_revisions: list[str] = []
        candidate_summaries: list[dict[str, Any]] = []
        for revision in log.stdout.splitlines():
            show = subprocess.run(
                ["git", "show", f"{revision}:{relative_path}"],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            if show.returncode:
                continue
            content_hash = hashlib.sha256(show.stdout).hexdigest()
            if content_hash == expected_hashes[relative_path]["recorded"]:
                matching_revisions.append(revision)
            candidate_summaries.append(
                {"revision": revision, "sha256": content_hash}
            )
        model_diff_checks[relative_path] = {
            "stage40_manifest_sha256": expected_hashes[relative_path]["recorded"],
            "manifest_current_sha256": expected_hashes[relative_path]["current"],
            "actual_worktree_sha256": hashlib.sha256(
                (ROOT / relative_path).read_bytes()
            ).hexdigest(),
            "matching_git_revisions": matching_revisions,
            "git_candidates": candidate_summaries,
        }

    current_counts = dict(current_status)
    current_counts["RUNNING"] = len(running_ids)
    current_counts["UNSTARTED"] = len(unstarted_ids)
    output = {
        "manifest": {
            "path": frozen_manifest["test_set_manifest"]["path"],
            "sha256": frozen_manifest["test_set_manifest"]["sha256"],
            "actual_sha256": hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
            "declared_frame_records": frozen_manifest["test_set_manifest"]["frame_record_count"],
            "sample_selected_records": test_sample.get("selected_total"),
            "sample_frame_count": test_sample.get("frame", {}).get("record_count"),
            "source_xlsx_exists": frame_path.is_file(),
            "source_xlsx_record_ids": len(frame_ids),
            "source_xlsx_sha256": hashlib.sha256(frame_path.read_bytes()).hexdigest()
            if frame_path.is_file()
            else None,
        },
        "shards": shard_info,
        "ledger": {
            "result_rows": len(all_rows),
            "unique_ids": len(by_id),
            "duplicate_rows": len(row_ids) - len(set(row_ids)),
            "duplicate_ids": {
                record_id: len(rows)
                for record_id, rows in by_id.items()
                if len(rows) > 1
            },
            "status_counts": dict(current_status),
            "merged_results_file": {
                "path": str(MERGED_RESULTS.relative_to(ROOT)),
                "exists": MERGED_RESULTS.is_file(),
                "rows": len(merged_rows),
                "status_counts": dict(
                    Counter(str(row.get("execution_status", "UNKNOWN")) for row in merged_rows)
                ),
            },
            "stage40_result_rows": len(stage40_rows),
            "stage40_unique_computed_ids": len(stage40_by_id),
            "computed_metric_rows": len(computed),
            "missing_from_source_frame": len(frame_missing),
            "missing_sample_ids": frame_missing,
            "running_ids": running_ids,
            "unstarted_from_source_frame": len(unstarted_ids),
            "input_cache_ids": sum(bool(row.get("cache_hits")) for row in all_rows),
            "logged_processing_ids": len(log_ids),
            "sqlite_state_counts": {
                shard: dict(Counter(state.values()))
                for shard, state in db_states.items()
            },
            "failure_records": [
                {
                    "record_id": str(row.get("record_id")),
                    "failure_reason": row.get("failure_reason"),
                    "shard_status": row.get("execution_status"),
                }
                for row in all_rows
                if row.get("execution_status") == "FAILED"
            ],
            "frame_terminal_and_pending_counts": current_counts,
        },
        "metrics_recomputed_from_shard_rows": metric_results,
        "stage40_shared_record_comparison": {
            "stage40_computed_rows": len(stage40_by_id),
            "stage41_computed_rows": len(current_by_id),
            "shared_ids_with_same_observed_yield": len(common_rows),
            "metrics": common_metrics,
        },
        "persisted_analysis_metrics": analysis.get("overall", {}),
        "blocked_ledger": {
            "rows": len(blocked_rows),
            "unique_ids": len(blocked_ids),
            "reason_counts": dict(blocked_counts),
            "ids_overlapping_shard_rows": sorted(blocked_ids & set(by_id)),
        },
        "input_cache": cache_summary,
        "model_git_history_hash_checks": model_diff_checks,
        "reproducibility": {
            "compared": reproducibility.get("records_compared"),
            "not_reproduced_by_artifact_count": len(nonrepro),
            "input_change_field_counts": dict(repro_input_changes),
            "nonreproducing_ids": [str(item.get("record_id")) for item in nonrepro],
            "input_diff_records_missing_numeric_inputs": [
                str(item.get("record_id"))
                for item in nonrepro
                if not all(
                    key in item
                    for key in (
                        "lai_40", "lai_41", "ewsi_40", "ewsi_41",
                        "vpd_40", "vpd_41", "par_40", "par_41",
                        "soil_moisture_40", "soil_moisture_41",
                    )
                )
            ],
        },
    }
    REPORT_JSON.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    metric_document = {
        "source": "Stage 41 shard JSONL files",
        "computed_records": len(computed),
        "manifest_records": len(frame_ids),
        "metrics": metric_results,
        "comparison": {
            "calibrated_rmse_minus_baseline_rmse": (
                metric_results["calibrated_epsilon_2_63"]["rmse"]
                - metric_results["baseline_epsilon_2_2"]["rmse"]
            ),
            "calibrated_rmse_minus_mean_rmse": (
                metric_results["calibrated_epsilon_2_63"]["rmse"]
                - metric_results["mean_predictor"]["rmse"]
            ),
            "stage40_rmse_reference": 1.2828,
            "calibrated_rmse_minus_stage40": (
                metric_results["calibrated_epsilon_2_63"]["rmse"] - 1.2828
            ),
        },
        "stage40_shared_record_comparison": output["stage40_shared_record_comparison"],
    }
    METRICS_JSON.write_text(json.dumps(metric_document, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Stage 41-D — Metrics recomputed from shard JSONL",
        "",
        f"Source: Stage 41 shard JSONL; computed rows = {len(computed)} of {len(frame_ids)} manifest records.",
        "This is a fresh calculation from shard records; it is distinct from the older `stage41_analysis.json` summary.",
        "",
        "| Metric | Baseline (ε=2.2) | Calibrated (ε=2.63) | Mean predictor |",
        "|---|---:|---:|---:|",
    ]
    labels = {"r2": "R²", "rmse": "RMSE (t/ha)", "mae": "MAE (t/ha)", "bias": "Bias (t/ha)", "mape": "MAPE (%)", "n": "n"}
    keys = ("baseline_epsilon_2_2", "calibrated_epsilon_2_63", "mean_predictor")
    for key, label in labels.items():
        values = [metric_results[name][key] for name in keys]
        if key == "n":
            formatted = [str(value) for value in values]
        else:
            formatted = [f"{value:.12g}" for value in values]
        md.append(f"| {label} | {formatted[0]} | {formatted[1]} | {formatted[2]} |")
    md.extend(
        [
            "",
            f"- Calibrated RMSE minus baseline RMSE: {metric_document['comparison']['calibrated_rmse_minus_baseline_rmse']:.12g} t/ha (negative means calibrated is better).",
            f"- Calibrated RMSE minus mean-predictor RMSE: {metric_document['comparison']['calibrated_rmse_minus_mean_rmse']:.12g} t/ha.",
            f"- Stage 40 reference RMSE = 1.2828; Stage 41 calibrated minus Stage 40 = {metric_document['comparison']['calibrated_rmse_minus_stage40']:.12g} t/ha.",
            "- No parameters were changed and no model was run by this audit.",
            "",
        ]
    )
    shared = output["stage40_shared_record_comparison"]
    if shared["shared_ids_with_same_observed_yield"]:
        md.extend(
            [
                "",
                f"## Stage 40 comparison on shared IDs ({shared['shared_ids_with_same_observed_yield']} records)",
                "",
                "| Metric | Stage 40 calibrated | Stage 41 baseline | Stage 41 calibrated | Mean predictor |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        stage40_shared = shared["metrics"]
        for key, label in labels.items():
            values = [
                stage40_shared[name][key]
                for name in (
                    "stage40_calibrated",
                    "stage41_baseline_epsilon_2_2",
                    "stage41_calibrated_epsilon_2_63",
                    "mean_predictor",
                )
            ]
            formatted = (
                [str(value) for value in values]
                if key == "n"
                else [f"{value:.12g}" for value in values]
            )
            md.append(
                f"| {label} | {formatted[0]} | {formatted[1]} | "
                f"{formatted[2]} | {formatted[3]} |"
            )
        md.extend(
            [
                "",
                "This is the like-for-like Stage 40 comparison. It excludes IDs whose observed yield differs between stored runs.",
            ]
        )
    METRICS_MD.write_text("\n".join(md), encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": output["manifest"],
                "shards": output["shards"],
                "ledger": {
                    key: value
                    for key, value in output["ledger"].items()
                    if key not in ("missing_sample_ids",)
                },
                "metrics": output["metrics_recomputed_from_shard_rows"],
                "blocked_ledger": output["blocked_ledger"],
                "input_cache": output["input_cache"],
                "model_git_history_hash_checks": output[
                    "model_git_history_hash_checks"
                ],
                "reproducibility": output["reproducibility"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
