"""Stage 40 Part 1 — Create the reproducible baseline manifest.

Freezes the Stage 39 baseline benchmark run (the *uncalibrated* default
model) so that the calibrated run can be compared against it without
mixing the two result sets.

The Stage 39 run is still in progress; this manifest records the state
as observed, and the metrics are the values computed from the records
completed at that time.  The results file itself is never rewritten.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
BENCH_DIR = ROOT / "engine/reports/data/stage39_benchmark"
RESULTS = BENCH_DIR / "record_results.jsonl"
STATE_DB = BENCH_DIR / "execution_state.sqlite"
OUT = ROOT / "engine/reports/data/stage40_baseline_manifest.json"

#: Files whose hash identifies the baseline code + configuration.
CODE_FILES = [
    "engine/hydroma/models/hyrue.py",
    "engine/hydroma/simulation/par_pipeline.py",
    "engine/hydroma/simulation/weather_source.py",
    "engine/hydroma/simulation/lai_model.py",
    "engine/hydroma/simulation/ewsi_pipeline.py",
    "engine/hydroma/simulation/radiation_units.py",
    "engine/hydroma/eval/seasonal_predictor.py",
    "engine/hydroma/eval/resumable_benchmark_runner.py",
]
CONFIG_FILES = [
    "engine/reports/data/stage37_frozen_model_config.json",
    "engine/reports/data/stage36_benchmark_split_manifest.json",
]


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        from _pathutil import resolve

        resolved = resolve(str(path))
        if resolved is None:
            return None
        h = hashlib.sha256()
        with open(resolved, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()


def load_bootstrap():
    module = _load_module(
        "_rt",
        str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py"),
    )
    module.ensure_engine_importable()
    return module


def main() -> int:
    bootstrap = load_bootstrap()
    metrics_mod = bootstrap.load_module("engine.hydroma.eval.stage39_benchmark")

    records = []
    if RESULTS.exists():
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    metrics = metrics_mod.compute_benchmark_metrics(records, group="stage39_baseline")
    by_district = metrics_mod.compute_grouped_metrics(records, "district_id")
    bootstrap_stats = metrics_mod.cluster_bootstrap_uncertainty(records)

    # Execution state from the SQLite file
    state_counts: dict[str, int] = {}
    if STATE_DB.exists():
        conn = sqlite3.connect(str(STATE_DB))
        try:
            for status, count in conn.execute(
                "SELECT status, COUNT(*) FROM record_state GROUP BY status"
            ):
                state_counts[status] = count
        finally:
            conn.close()

    code_hashes = {p: sha256_file(ROOT / p) for p in CODE_FILES}
    config_hashes = {p: sha256_file(ROOT / p) for p in CONFIG_FILES}
    combined = hashlib.sha256(
        json.dumps(
            {"code": code_hashes, "config": config_hashes}, sort_keys=True
        ).encode()
    ).hexdigest()

    manifest = {
        "run_id": "stage39_baseline_uncalibrated",
        "baseline_type": "baseline_only",
        "description": (
            "Stage 39 benchmark of the UNCALIBRATED default HYRUE model. "
            "Preserved unchanged for comparison with the Stage 40 "
            "calibrated run.  Never mixed with calibrated results."
        ),
        "code_commit": "working tree (no commit recorded)",
        "model_code_hash": combined,
        "file_hashes": {"code": code_hashes, "config": config_hashes},
        "baseline_model_config_hash": config_hashes[
            "engine/reports/data/stage37_frozen_model_config.json"
        ],
        "test_manifest_hash": config_hashes[
            "engine/reports/data/stage36_benchmark_split_manifest.json"
        ],
        "model_version": "2.0.0",
        "calibration_status": "baseline_only",
        "parameters": "project defaults, unmodified",
        "run_started_at": datetime.now(UTC).isoformat(),
        "recorded_at": datetime.now(UTC).isoformat(),
        "records_processed": len(records),
        "manifest_test_record_count": 1722,
        "execution_state_counts": state_counts,
        "execution_status": "in_progress",
        "results_path": str(RESULTS),
        "state_db_path": str(STATE_DB),
        "metrics_so_far": metrics.to_dict(),
        "metrics_by_district": {k: v.to_dict() for k, v in by_district.items()},
        "uncertainty_so_far": bootstrap_stats,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "executable": sys.executable,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    print("Baseline manifest written:", OUT)
    print("  records processed :", len(records))
    print("  state counts      :", state_counts)
    print("  RMSE / MAE / Bias :", metrics.rmse, metrics.mae, metrics.bias)
    print("  R2                :", metrics.r2)
    print("  MAPE              :", metrics.mape)
    print("  model_code_hash   :", combined[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
