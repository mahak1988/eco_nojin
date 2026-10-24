"""Validate Stage 41-E outputs and compute metrics for a live-input rerun."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "engine" / "reports" / "data"
SOURCE_XLSX = (
    ROOT
    / "data"
    / "external"
    / "cimmyt_wheat"
    / "data"
    / "Wheat_Yld_Eastern_IND_Data.xlsx"
)
VALID_STATUSES = {"COMPUTED", "PARTIAL_INPUTS", "BLOCKED", "FAILED"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
    return rows


def _score(
    observed: np.ndarray, predicted: np.ndarray
) -> dict[str, float | int | None]:
    errors = predicted - observed
    total_sum_squares = float(np.sum((observed - observed.mean()) ** 2))
    r2 = (
        1.0 - float(np.sum(errors**2)) / total_sum_squares
        if total_sum_squares > 0
        else None
    )
    nonzero = observed != 0
    return {
        "n": int(observed.size),
        "r2": r2,
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "bias": float(np.mean(errors)),
        "mape_percent": (
            float(np.mean(np.abs(errors[nonzero] / observed[nonzero])) * 100)
            if np.any(nonzero)
            else None
        ),
        "mape_n": int(np.count_nonzero(nonzero)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=DATA / "stage41e_live_rerun",
    )
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()

    merged_path = run_dir / "record_results.jsonl"
    results = _read_jsonl(merged_path)
    result_ids = [str(row["record_id"]) for row in results]
    duplicate_ids = sorted(
        record_id for record_id in set(result_ids) if result_ids.count(record_id) > 1
    )
    invalid_status_rows = [
        row for row in results if row.get("execution_status") not in VALID_STATUSES
    ]
    status_counts: dict[str, int] = {}
    for row in results:
        status = str(row.get("execution_status", "UNKNOWN"))
        status_counts[status] = status_counts.get(status, 0) + 1
    source_counts: dict[str, int] = {}
    quality_counts: dict[str, int] = {}
    for row in results:
        source = str(row.get("weather_source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        quality = str(row.get("input_quality_status") or "unknown")
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
    noncomputed_records = [
        {
            "record_id": str(row["record_id"]),
            "status": str(row.get("execution_status", "UNKNOWN")),
            "failure_reason": str(row.get("failure_reason") or "unspecified"),
        }
        for row in results
        if row.get("execution_status") != "COMPUTED"
    ]
    noncomputed_reason_counts: dict[tuple[str, str], list[str]] = {}
    for row in noncomputed_records:
        key = (row["status"], row["failure_reason"])
        noncomputed_reason_counts.setdefault(key, []).append(row["record_id"])

    manifest = json.loads((DATA / "stage41_frozen_model_manifest.json").read_text(
        encoding="utf-8"
    ))
    frozen_model = json.loads(
        (DATA / "stage40_frozen_model_config.json").read_text(encoding="utf-8")
    )
    expected_count = int(manifest["benchmark_run"]["stage41_target_records"])
    split = json.loads((DATA / "stage40_test_sample.json").read_text(encoding="utf-8"))
    frame = pd.read_excel(SOURCE_XLSX)
    test_districts = set(split["frame"]["districts"])
    source_ids = {
        str(record_id)
        for record_id in frame.loc[frame["District"].isin(test_districts), "Field_ID"]
    }
    if len(source_ids) != expected_count:
        raise ValueError(
            f"Source workbook has {len(source_ids)} frame IDs, expected "
            f"{expected_count}."
        )
    sorted_source_ids = sorted(source_ids)
    source_ids_sha256 = hashlib.sha256(
        "\n".join(sorted_source_ids).encode("utf-8")
    ).hexdigest()
    missing_ids = sorted(source_ids - set(result_ids))
    unexpected_ids = sorted(set(result_ids) - source_ids)

    input_rows = []
    for path in sorted(run_dir.glob("shards/shard_*/resolved_inputs.jsonl")):
        input_rows.extend(_read_jsonl(path))
    if not (run_dir / "shards").exists():
        input_rows.extend(_read_jsonl(run_dir / "resolved_inputs.jsonl"))
    input_ids = [str(row["record_id"]) for row in input_rows]
    duplicate_input_ids = sorted(
        record_id for record_id in set(input_ids) if input_ids.count(record_id) > 1
    )
    computed_ids = {
        str(row["record_id"])
        for row in results
        if row.get("execution_status") == "COMPUTED"
        and row.get("predicted_yield") is not None
    }
    missing_input_ids = sorted(computed_ids - set(input_ids))

    computed = [
        row
        for row in results
        if row.get("execution_status") == "COMPUTED"
        and row.get("observed_yield") is not None
        and row.get("predicted_yield") is not None
        and row.get("baseline_predicted_yield") is not None
    ]
    observed = np.asarray([float(row["observed_yield"]) for row in computed])
    baseline = np.asarray(
        [float(row["baseline_predicted_yield"]) for row in computed]
    )
    calibrated = np.asarray([float(row["predicted_yield"]) for row in computed])
    mean_prediction = np.full(observed.size, float(observed.mean()))

    metrics = {
        "baseline_epsilon_2_2": _score(observed, baseline),
        "calibrated_epsilon_2_63": _score(observed, calibrated),
        "mean_predictor": _score(observed, mean_prediction),
    }
    metrics["delta_rmse_calibrated_minus_baseline"] = (
        metrics["calibrated_epsilon_2_63"]["rmse"]
        - metrics["baseline_epsilon_2_2"]["rmse"]
    )
    metrics["delta_rmse_calibrated_minus_mean"] = (
        metrics["calibrated_epsilon_2_63"]["rmse"]
        - metrics["mean_predictor"]["rmse"]
    )

    identities = []
    for path in sorted(run_dir.glob("shards/shard_*/execution_identity.json")):
        identities.append(json.loads(path.read_text(encoding="utf-8")))
    if not identities and (run_dir / "execution_identity.json").exists():
        identities.append(
            json.loads((run_dir / "execution_identity.json").read_text(encoding="utf-8"))
        )
    identity_hashes = sorted({item["model_code_hash"] for item in identities})
    execution_file_hashes = {}
    for relative_path in (
        "engine/hydroma/eval/resumable_benchmark_runner.py",
        "engine/hydroma/eval/seasonal_predictor.py",
        "engine/hydroma/eval/identifiability_calibration.py",
        "engine/hydroma/simulation/weather_source.py",
        "engine/hydroma/simulation/par_pipeline.py",
        "engine/hydroma/models/hyrue.py",
        "tools/diagnostics/stage41_run_test_benchmark.py",
        "tools/diagnostics/stage41_run_parallel_benchmark.py",
    ):
        execution_file_hashes[relative_path] = hashlib.sha256(
            (ROOT / relative_path).read_bytes()
        ).hexdigest()
    frozen_file_hashes = frozen_model.get("file_hashes", {})
    frozen_file_comparison = {
        path: {
            "stage40_sha256": frozen_file_hashes.get(path),
            "current_sha256": current_hash,
            "matches": frozen_file_hashes.get(path) == current_hash,
        }
        for path, current_hash in execution_file_hashes.items()
        if path in frozen_file_hashes
    }

    audit = {
        "run_dir": str(run_dir),
        "expected_records": expected_count,
        "source_workbook_sha256": hashlib.sha256(
            SOURCE_XLSX.read_bytes()
        ).hexdigest(),
        "test_sample_manifest_sha256": hashlib.sha256(
            (DATA / "stage40_test_sample.json").read_bytes()
        ).hexdigest(),
        "source_record_ids_sha256": source_ids_sha256,
        "source_record_ids_hash_method": "SHA-256 of sorted IDs joined with LF",
        "result_rows": len(results),
        "unique_result_ids": len(set(result_ids)),
        "status_counts": status_counts,
        "weather_source_counts": source_counts,
        "input_quality_counts": quality_counts,
        "noncomputed_records": noncomputed_records,
        "noncomputed_reason_counts": [
            {
                "status": status,
                "failure_reason": reason,
                "count": len(record_ids),
                "record_ids": sorted(record_ids),
            }
            for (status, reason), record_ids in sorted(
                noncomputed_reason_counts.items()
            )
        ],
        "duplicate_result_ids": duplicate_ids,
        "invalid_status_rows": len(invalid_status_rows),
        "missing_record_ids": missing_ids,
        "unexpected_record_ids": unexpected_ids,
        "resolved_input_rows": len(input_rows),
        "unique_resolved_input_ids": len(set(input_ids)),
        "duplicate_resolved_input_ids": duplicate_input_ids,
        "computed_records_missing_captured_inputs": missing_input_ids,
        "model_code_hashes": identity_hashes,
        "stage40_frozen_model_code_hash": frozen_model.get("model_code_hash"),
        "stage40_frozen_file_comparison": frozen_file_comparison,
        "execution_file_hashes": execution_file_hashes,
        "metrics": metrics,
        "complete_accounting": (
            len(results) == expected_count
            and len(set(result_ids)) == expected_count
            and not duplicate_ids
            and not invalid_status_rows
            and not missing_ids
            and not unexpected_ids
        ),
        "complete_computed_input_capture": (
            not missing_input_ids and not duplicate_input_ids
        ),
        "stage40_code_freeze_proven": False,
        "live_inputs_captured": True,
    }
    (run_dir / "stage41e_audit.json").write_text(
        json.dumps(audit, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    lines = [
        "# Stage 41-E — Live-input benchmark",
        "",
        f"- Records expected: {expected_count}",
        f"- Source workbook SHA-256: "
        f"`{audit['source_workbook_sha256']}`",
        f"- Test-frame IDs SHA-256: `{source_ids_sha256}`",
        f"- Result rows: {len(results)}",
        f"- Unique record IDs: {len(set(result_ids))}",
        f"- Status counts: `{status_counts}`",
        f"- Weather-source counts: `{source_counts}`",
        f"- Input-quality counts: `{quality_counts}`",
        f"- Captured resolved-input records: {len(set(input_ids))}",
        f"- Missing results: {len(missing_ids)}",
        f"- Computed rows missing input capture: {len(missing_input_ids)}",
        "- Parameters: ε=2.63, HI=0.45; baseline ε=2.2",
        f"- Current pipeline identity hash: `{identity_hashes}`",
        f"- Stage 40 frozen model code hash: "
        f"`{frozen_model.get('model_code_hash')}`",
        f"- Runner/driver source hashes: `{execution_file_hashes}`",
        f"- Stage 40 file-hash comparison: `{frozen_file_comparison}`",
        "- This is a fresh live-input run using current code; it is not proof "
        "of Stage 40 code equivalence or direct comparability with Stage 40.",
        "- Current and Stage 40 aggregate model-code hashes differ; both "
        "`seasonal_predictor.py` and `identifiability_calibration.py` have "
        "different file hashes. Numerical scientific equivalence is unproven.",
        "- Weather-source attribution is not verified: fetch results do not "
        "set the `source` attribute consumed by the runner, which defaults "
        "successful rows to `open_meteo_era5`; the logs also record HTTP 429 "
        "and NASA POWER fallback messages.",
        "",
        "| Metric | Baseline ε=2.2 | Calibrated ε=2.63 | Mean predictor |",
        "|---|---:|---:|---:|",
    ]
    for metric, label in (
        ("n", "n"),
        ("rmse", "RMSE"),
        ("mae", "MAE"),
        ("bias", "Bias"),
        ("r2", "R²"),
        ("mape_percent", "MAPE (%)"),
    ):
        values = (
            metrics["baseline_epsilon_2_2"][metric],
            metrics["calibrated_epsilon_2_63"][metric],
            metrics["mean_predictor"][metric],
        )
        rendered = [
            f"{value:.10g}" if isinstance(value, (int, float)) else "N/A"
            for value in values
        ]
        lines.append(f"| {label} | {rendered[0]} | {rendered[1]} | {rendered[2]} |")
    lines.extend(
        [
            "",
            "## Non-computed records",
            "",
            "| Status | Failure reason | Count | Record IDs |",
            "|---|---|---:|---|",
        ]
    )
    for item in audit["noncomputed_reason_counts"]:
        lines.append(
            f"| {item['status']} | {item['failure_reason']} | "
            f"{item['count']} | {', '.join(item['record_ids'])} |"
        )
    lines.extend(
        [
            "",
            f"- Calibrated minus baseline ΔRMSE: "
            f"{metrics['delta_rmse_calibrated_minus_baseline']:.10g} t/ha.",
            f"- Calibrated minus mean ΔRMSE: "
            f"{metrics['delta_rmse_calibrated_minus_mean']:.10g} t/ha.",
            f"- Complete 1,722-row accounting: `{audit['complete_accounting']}`.",
            f"- Complete input capture for computed records: "
            f"`{audit['complete_computed_input_capture']}`.",
            "- Stage 40 equivalence remains unproven; this run alone does not "
            "upgrade the Stage 41 closure verdict.",
            "",
        ]
    )
    report_text = "\n".join(lines)
    (run_dir / "STAGE-41E-LIVE-RERUN.md").write_text(
        report_text,
        encoding="utf-8",
    )
    (ROOT / "engine/reports/STAGE-41E-LIVE-RERUN.md").write_text(
        report_text,
        encoding="utf-8",
    )
    print(json.dumps(audit, indent=2, allow_nan=False))
    return 0 if audit["complete_accounting"] and audit["complete_computed_input_capture"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
