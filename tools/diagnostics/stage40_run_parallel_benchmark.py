"""Stage 40 — run the test benchmark in parallel shards and merge.

The Sentinel-2 COG reads dominate the per-record cost (~66-130 s per
band), and the latency is per-connection rather than server-throttled, so
the benchmark parallelises well across processes.

This driver spawns ``--shards`` worker processes, each running the
benchmark over a disjoint, deterministic interleave of the test records
with its own state database and results file, then merges the shard
results into a single results file and writes the summary.

The merged result set is identical to a single-process run: the shards
partition the records, and no record is processed twice.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
OUT_DIR = ROOT / "engine/reports/data/stage40_test_benchmark"
SHARD_DIR = OUT_DIR / "shards"
FROZEN = ROOT / "engine/reports/data/stage40_frozen_model_config.json"
PYTHON = Path(r"D:\eco_nojin\.venv\Scripts\python.exe")


def _coverage(merged: list[dict], sample_meta) -> dict:
    """Realised stratum coverage against the sampling design."""
    if not sample_meta:
        return {}
    from collections import Counter

    got = Counter(
        f"{r.get('district_id')}|{r.get('season')}" for r in merged
    )
    rows = {}
    for stratum, alloc in sorted(sample_meta.get("allocation", {}).items()):
        rows[stratum] = {
            "design": alloc.get("allocated"),
            "evaluated": got.get(stratum, 0),
        }
    return {
        "by_stratum": rows,
        "strata_covered": sum(1 for v in rows.values() if v["evaluated"] > 0),
        "strata_total": len(rows),
    }


def _run_shards(args, shard_dir: Path) -> None:
    """Launch the shard workers once and wait for all of them."""
    procs = []
    for shard in range(args.shards):
        cmd = [
            str(PYTHON), "-u",
            str(HERE / "stage40_run_test_benchmark.py"),
            "--shard-index", str(shard),
            "--shard-count", str(args.shards),
        ]
        if args.max_records is not None:
            cmd += ["--max-records", str(args.max_records)]
        if args.sample:
            cmd += ["--sample", args.sample]
        log_path = shard_dir / f"shard_{shard:02d}.log"
        log = open(log_path, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT)
        )
        procs.append((shard, proc, log, log_path))
        print(
            f"shard {shard}/{args.shards} started (pid {proc.pid}) -> {log_path.name}",
            flush=True,
        )

    print()
    print("waiting for shards ...", flush=True)
    for shard, proc, log, log_path in procs:
        code = proc.wait()
        log.close()
        state = "OK" if code == 0 else f"EXIT {code}"
        print(f"  shard {shard:02d}: {state}  ({log_path.name})", flush=True)
        if code != 0:
            tail = log_path.read_text(
                encoding="utf-8", errors="replace"
            ).splitlines()[-12:]
            print(f"--- shard {shard} tail ---")
            for line in tail:
                print("   ", line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--sample", default=None,
                        help="path to a stage40_test_sample.json to restrict the run")
    parser.add_argument("--max-passes", type=int, default=8,
                        help="how many times to relaunch the shards if any remain")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    expected_ids: list[str] | None = None
    if args.sample:
        with open(args.sample, encoding="utf-8") as f:
            expected_ids = json.load(f)["record_ids"]

    def remaining_count() -> int:
        """How many selected records have not been written yet."""
        if not expected_ids:
            return 0
        done: set[str] = set()
        for shard in range(args.shards):
            path = SHARD_DIR / f"shard_{shard:02d}" / "record_results.jsonl"
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        done.add(str(json.loads(line)["record_id"]))
        return len([r for r in expected_ids if r not in done])

    started = time.time()
    for attempt in range(1, args.max_passes + 1):
        left = remaining_count()
        if left == 0:
            print(f"all {len(expected_ids or [])} records already processed", flush=True)
            break
        print(
            f"=== pass {attempt}/{args.max_passes}: {left} records remaining ===",
            flush=True,
        )
        _run_shards(args, SHARD_DIR)
        left = remaining_count()
        print(f"after pass {attempt}: {left} records remaining", flush=True)
        if left == 0:
            break

    elapsed = time.time() - started
    print(f"\nfinished in {elapsed / 60:.1f} min", flush=True)

    # --- Merge the shard results ---
    merged = []
    seen: set[str] = set()
    for shard in range(args.shards):
        path = SHARD_DIR / f"shard_{shard:02d}" / "record_results.jsonl"
        if not path.exists():
            print(f"shard {shard:02d}: no results file", flush=True)
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

    merged_path = OUT_DIR / "record_results.jsonl"
    with open(merged_path, "w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\nmerged {len(merged)} unique records -> {merged_path}", flush=True)

    # --- Summary ---
    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    metrics_mod = bootstrap.load_module("engine.hydroma.eval.stage39_benchmark")

    metrics = metrics_mod.compute_benchmark_metrics(merged, group="stage40_test")
    by_district = metrics_mod.compute_grouped_metrics(merged, "district_id")
    by_season = metrics_mod.compute_grouped_metrics(merged, "season")
    by_quality = metrics_mod.compute_grouped_metrics(merged, "input_quality_status")
    uncertainty = metrics_mod.cluster_bootstrap_uncertainty(merged)

    metrics_dict = metrics.to_dict()
    by_district = {k: v.to_dict() for k, v in by_district.items()}
    by_season = {k: v.to_dict() for k, v in by_season.items()}
    by_quality = {k: v.to_dict() for k, v in by_quality.items()}

    failed_records = [
        r for r in merged
        if r.get("execution_status") in ("FAILED", "BLOCKED")
    ]
    failed_path = OUT_DIR / "failed_records.jsonl"
    with open(failed_path, "w", encoding="utf-8") as f:
        for rec in failed_records:
            f.write(json.dumps(rec, default=str) + "\n")

    with open(FROZEN, encoding="utf-8") as f:
        frozen = json.load(f)

    sample_meta = None
    if args.sample:
        with open(args.sample, encoding="utf-8") as f:
            sample_meta = json.load(f)

    status_counts: dict[str, int] = {}
    for r in merged:
        s = str(r.get("execution_status"))
        status_counts[s] = status_counts.get(s, 0) + 1
    quality_counts: dict[str, int] = {}
    for r in merged:
        s = str(r.get("input_quality_status"))
        quality_counts[s] = quality_counts.get(s, 0) + 1
    ewsi_counts: dict[str, int] = {}
    for r in merged:
        s = str(r.get("ewsi_status"))
        ewsi_counts[s] = ewsi_counts.get(s, 0) + 1

    summary = {
        "run_id": f"stage40_{int(time.time())}",
        "model_version": frozen["model_version"],
        "model_code_hash": frozen["model_code_hash"],
        "parameter_values": frozen["parameter_values"],
        "calibration_status": frozen["calibration_status"],
        "test_districts": ["Buxar", "Muzaffarpur", "Rohtas"],
        "records_processed": len(merged),
        "shards": args.shards,
        "elapsed_seconds": elapsed,
        "realised_coverage": _coverage(merged, sample_meta),
        "sample": (
            {
                "design": sample_meta.get("design"),
                "strata_definition": sample_meta.get("strata_definition"),
                "allocation_rule": sample_meta.get("allocation_rule"),
                "n_strata": sample_meta.get("n_strata"),
                "frame_record_count": sample_meta.get("frame", {}).get("record_count"),
                "frame_record_ids_hash": sample_meta.get("frame", {}).get(
                    "record_ids_hash"
                ),
                "selected_total": sample_meta.get("selected_total"),
                "seed": sample_meta.get("seed"),
                "selected_ids_hash": sample_meta.get("selected_ids_hash"),
                "allocation": sample_meta.get("allocation"),
            }
            if sample_meta
            else None
        ),
        "execution_status_counts": status_counts,
        "input_quality_summary": {
            "input_quality_counts": quality_counts,
            "ewsi_status_counts": ewsi_counts,
            "n_computed": status_counts.get("COMPUTED", 0),
            "n_partial_inputs": status_counts.get("PARTIAL_INPUTS", 0),
            "n_blocked": status_counts.get("BLOCKED", 0),
            "n_failed": status_counts.get("FAILED", 0),
            "n_with_prediction": sum(
                1 for r in merged if r.get("predicted_yield") is not None
            ),
        },
        "metrics_all": metrics_dict,
        "metrics_by_district": by_district,
        "metrics_by_season": by_season,
        "metrics_by_input_quality": by_quality,
        "uncertainty": uncertainty,
        "results_path": str(merged_path),
        "failed_records_path": str(failed_path),
    }

    summary_path = OUT_DIR / "benchmark_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print()
    print("=" * 60)
    print("STAGE 40 TEST BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"records processed : {len(merged)}")
    print(f"status counts     : {status_counts}")
    print(f"with prediction   : {summary['input_quality_summary']['n_with_prediction']}")
    print(f"RMSE              : {metrics_dict.get('rmse')}")
    print(f"MAE               : {metrics_dict.get('mae')}")
    print(f"Bias              : {metrics_dict.get('bias')}")
    print(f"R2                : {metrics_dict.get('r2')}")
    print(f"summary           : {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
