"""Stage 41 — run the full test benchmark in parallel shards and merge.

Launches ``--shards`` worker processes over a deterministic disjoint
interleave of the complete test frame, waits for them, relaunches any
shard that died (the runner is resumable), then merges the shard results
into one results file and writes the benchmark summary.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
DATA = ROOT / "engine/reports/data"
OUT_DIR = DATA / "stage41_test_benchmark"
SHARD_DIR = OUT_DIR / "shards"
FROZEN = DATA / "stage40_frozen_model_config.json"
MANIFEST41 = DATA / "stage41_frozen_model_manifest.json"
PYTHON = Path(r"D:\eco_nojin\.venv\Scripts\python.exe")

#: Terminal execution statuses; a record in one of these is final.
TERMINAL = ("COMPUTED", "PARTIAL_INPUTS", "BLOCKED", "FAILED")


def _acquire_lock(path: Path):
    """Take an exclusive single-instance lock.

    Two drivers over the same shards would process every record twice
    and double the load on the upstream APIs, so a second instance must
    refuse to start rather than quietly duplicate the work.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return path


def _release_lock(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink()
    except OSError:
        pass


def _retry_failed(shard_dir: Path) -> int:
    """Reset FAILED/BLOCKED records so the next pass retries them.

    A record that failed because the upstream API was rate-limiting (an
    HTTP 429, a read timeout) is not a final answer.  Only records that
    produced output keep their terminal status.
    """
    db = shard_dir / "execution_state.sqlite"
    if not db.exists():
        return 0
    try:
        with sqlite3.connect(str(db)) as conn:
            cur = conn.execute(
                "DELETE FROM record_state WHERE status IN ('FAILED', 'BLOCKED')"
            )
            conn.commit()
            return cur.rowcount or 0
    except sqlite3.Error:
        return 0


def _run_shards(args) -> None:
    procs = []
    for shard in range(args.shards):
        cmd = [
            str(PYTHON), "-u",
            str(HERE / "stage41_run_test_benchmark.py"),
            "--shard-index", str(shard),
            "--shard-count", str(args.shards),
            "--out-dir", str(OUT_DIR),
            "--capture-resolved-inputs",
        ]
        if args.max_records is not None:
            cmd += ["--max-records", str(args.max_records)]
        log_path = SHARD_DIR / f"shard_{shard:02d}.log"
        log = open(log_path, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT)
        )
        procs.append((shard, proc, log, log_path))
        print(
            f"shard {shard}/{args.shards} started (pid {proc.pid})",
            flush=True,
        )

    print()
    print("waiting for shards ...", flush=True)
    for shard, proc, log, _log_path in procs:
        code = proc.wait()
        log.close()
        # The launcher process can exit before the real interpreter does,
        # so wait for the shard's completion marker as well.
        marker = SHARD_DIR / f"shard_{shard:02d}" / "DONE"
        deadline = time.time() + 3600
        while not marker.exists() and time.time() < deadline:
            time.sleep(2)
        state = "OK" if code == 0 else f"EXIT {code}"
        print(f"  shard {shard:02d}: {state}", flush=True)
        try:
            marker.unlink()
        except OSError:
            pass


def _merged_records() -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for shard_dir in sorted(SHARD_DIR.glob("shard_*")):
        path = shard_dir / "record_results.jsonl"
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rid = str(rec["record_id"])
                if rid in seen:
                    continue
                seen.add(rid)
                merged.append(rec)
    return merged


def main() -> int:
    global OUT_DIR, SHARD_DIR

    parser = argparse.ArgumentParser()
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--max-passes", type=int, default=10)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    OUT_DIR = args.out_dir.resolve()
    SHARD_DIR = OUT_DIR / "shards"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    lock = _acquire_lock(OUT_DIR / "driver.lock")
    if lock is None:
        print(
            "another Stage 41 benchmark driver is already running; "
            "refusing to start a second one",
            flush=True,
        )
        return 3

    try:
        return _drive(args)
    finally:
        _release_lock(lock)


def _drive(args) -> int:
    started = time.time()
    for attempt in range(1, args.max_passes + 1):
        print(
            f"=== pass {attempt}/{args.max_passes}: "
            f"{len(_merged_records())} records done ===",
            flush=True,
        )
        if attempt > 1:
            retried = 0
            for shard_dir in sorted(SHARD_DIR.glob("shard_*")):
                retried += _retry_failed(shard_dir)
            if retried:
                print(f"  re-queued {retried} failed/blocked records", flush=True)
        _run_shards(args)
        done = len(_merged_records())
        print(f"after pass {attempt}: {done} records", flush=True)

    elapsed = time.time() - started
    merged = _merged_records()
    print(f"\nfinished in {elapsed / 60:.1f} min, {len(merged)} unique records",
          flush=True)

    # --- Write merged results ---
    merged_path = OUT_DIR / "record_results.jsonl"
    with open(merged_path, "w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, default=str) + "\n")

    failed = [r for r in merged if r.get("execution_status") in ("FAILED", "BLOCKED")]
    with open(OUT_DIR / "failed_records.jsonl", "w", encoding="utf-8") as f:
        for rec in failed:
            f.write(json.dumps(rec, default=str) + "\n")

    # --- Summary ---
    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    metrics_mod = bootstrap.load_module("engine.hydroma.eval.stage39_benchmark")

    metrics = metrics_mod.compute_benchmark_metrics(merged, group="stage41_test")
    by_district = metrics_mod.compute_grouped_metrics(merged, "district_id")
    by_season = metrics_mod.compute_grouped_metrics(merged, "season")
    by_quality = metrics_mod.compute_grouped_metrics(merged, "input_quality_status")
    by_lai = metrics_mod.compute_grouped_metrics(merged, "lai_status")
    by_ewsi = metrics_mod.compute_grouped_metrics(merged, "ewsi_status")
    uncertainty = metrics_mod.cluster_bootstrap_uncertainty(merged)

    with open(FROZEN, encoding="utf-8") as f:
        frozen = json.load(f)
    m41 = {}
    if MANIFEST41.exists():
        with open(MANIFEST41, encoding="utf-8") as f:
            m41 = json.load(f)

    def counts(key):
        out: dict[str, int] = {}
        for r in merged:
            v = str(r.get(key, "unknown"))
            out[v] = out.get(v, 0) + 1
        return out

    status_counts = counts("execution_status")

    summary = {
        "stage": 41,
        "run_id": f"stage41_{int(time.time())}",
        "model_version": frozen["model_version"],
        "model_code_hash": frozen["model_code_hash"],
        "frozen_config_sha256": m41.get("frozen_config_sha256"),
        "parameter_values": frozen["parameter_values"],
        "calibration_status": frozen["calibration_status"],
        "test_districts": ["Buxar", "Muzaffarpur", "Rohtas"],
        "records_processed": len(merged),
        "target_records": m41.get("benchmark_run", {}).get("stage41_target_records"),
        "shards": args.shards,
        "elapsed_seconds": elapsed,
        "execution_status_counts": status_counts,
        "input_quality_summary": {
            "input_quality_counts": counts("input_quality_status"),
            "ewsi_status_counts": counts("ewsi_status"),
            "lai_status_counts": counts("lai_status"),
            "par_status_counts": counts("par_status"),
            "weather_source_counts": counts("weather_source"),
            "n_computed": status_counts.get("COMPUTED", 0),
            "n_partial_inputs": status_counts.get("PARTIAL_INPUTS", 0),
            "n_blocked": status_counts.get("BLOCKED", 0),
            "n_failed": status_counts.get("FAILED", 0),
            "n_with_prediction": sum(
                1 for r in merged if r.get("predicted_yield") is not None
            ),
        },
        "metrics_all": metrics.to_dict(),
        "metrics_by_district": {k: v.to_dict() for k, v in by_district.items()},
        "metrics_by_season": {k: v.to_dict() for k, v in by_season.items()},
        "metrics_by_input_quality": {k: v.to_dict() for k, v in by_quality.items()},
        "metrics_by_lai_status": {k: v.to_dict() for k, v in by_lai.items()},
        "metrics_by_ewsi_status": {k: v.to_dict() for k, v in by_ewsi.items()},
        "uncertainty": uncertainty,
        "results_path": str(merged_path),
        "failed_records_path": str(OUT_DIR / "failed_records.jsonl"),
    }

    summary_path = OUT_DIR / "benchmark_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print()
    print("=" * 60)
    print("STAGE 41 TEST BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"records processed : {len(merged)}")
    print(f"status counts     : {status_counts}")
    print(f"with prediction   : {summary['input_quality_summary']['n_with_prediction']}")
    print(f"RMSE              : {metrics.rmse}")
    print(f"MAE               : {metrics.mae}")
    print(f"Bias              : {metrics.bias}")
    print(f"R2                : {metrics.r2}")
    print(f"summary           : {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
