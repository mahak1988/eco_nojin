"""Stage 40 — test benchmark with the frozen calibrated model.

Runs the resumable benchmark against the *frozen* Stage 40 model
configuration, writing to a separate output directory so the Stage 39
baseline results are never overwritten or mixed.

Usage:
    python tools/stage40_run_test_benchmark.py --max-records N
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
OUT_DIR = ROOT / "engine/reports/data/stage40_test_benchmark"
FROZEN = ROOT / "engine/reports/data/stage40_frozen_model_config.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--sample", default=None,
                        help="path to a stage40_test_sample.json to restrict the run")
    args = parser.parse_args()

    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()

    runner_mod = bootstrap.load_module("engine.hydroma.eval.resumable_benchmark_runner")
    metrics_mod = bootstrap.load_module("engine.hydroma.eval.stage39_benchmark")
    hyrue_mod = bootstrap.load_module("engine.hydroma.models.hyrue")

    with open(FROZEN, encoding="utf-8") as f:
        frozen = json.load(f)

    values = frozen["parameter_values"]
    params = hyrue_mod.HYRUEParams(
        epsilon=values["epsilon"],
        k=values["k"],
        hi=values["hi"],
        lai_max=values["lai_max"],
        t_opt=values["t_opt"],
        t_min=values["t_min"],
        t_max=values["t_max"],
    )
    print(
        f"frozen model v{frozen['model_version']}: "
        f"epsilon={values['epsilon']:.4f}, hi={values['hi']}",
        flush=True,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # In a sharded run each shard owns its own state database and results
    # file, so shards never contend for the same rows.
    if args.shard_count > 1:
        work_dir = OUT_DIR / "shards" / f"shard_{args.shard_index:02d}"
    else:
        work_dir = OUT_DIR
    work_dir.mkdir(parents=True, exist_ok=True)

    sample_ids = None
    sample_meta = None
    if args.sample:
        with open(args.sample, encoding="utf-8") as f:
            sample_meta = json.load(f)
        sample_ids = sample_meta["record_ids"]
        print(
            f"restricted to the stratified sample: {len(sample_ids)} records",
            flush=True,
        )

    runner = runner_mod.ResumableBenchmarkRunner(
        db_path=work_dir / "execution_state.sqlite",
        results_path=work_dir / "record_results.jsonl",
        manifest_path=work_dir / "run_manifest.json",
        hyrue_params=params,
        run_id="stage40",
        data_label="stage40_benchmark",
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        record_ids=sample_ids,
    )

    print("=" * 60, flush=True)
    print(
        f"Stage 40 Test Benchmark (frozen calibrated model) "
        f"shard {args.shard_index}/{args.shard_count}",
        flush=True,
    )
    print("=" * 60, flush=True)

    summary = runner.run(max_records=args.max_records)

    records = []
    results_path = work_dir / "record_results.jsonl"
    if results_path.exists():
        with open(results_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    metrics = metrics_mod.compute_benchmark_metrics(records, group="stage40_test")
    by_district = metrics_mod.compute_grouped_metrics(records, "district_id")
    by_season = metrics_mod.compute_grouped_metrics(records, "season")
    by_quality = metrics_mod.compute_grouped_metrics(records, "input_quality_status")
    uncertainty = metrics_mod.cluster_bootstrap_uncertainty(records)

    failed = [
        r for r in records
        if r.get("execution_status") in ("FAILED", "BLOCKED")
    ]
    with open(work_dir / "failed_records.jsonl", "w", encoding="utf-8") as f:
        for r in failed:
            f.write(json.dumps(r, default=str) + "\n")

    def counts(key):
        out: dict[str, int] = {}
        for r in records:
            v = str(r.get(key, "unknown"))
            out[v] = out.get(v, 0) + 1
        return out

    quality = {
        "n_records": len(records),
        "n_computed": counts("execution_status").get("COMPUTED", 0),
        "n_partial_inputs": counts("execution_status").get("PARTIAL_INPUTS", 0),
        "n_blocked": counts("execution_status").get("BLOCKED", 0),
        "n_failed": counts("execution_status").get("FAILED", 0),
        "n_with_prediction": sum(
            1 for r in records if r.get("predicted_yield") is not None
        ),
        "ewsi_status_counts": counts("ewsi_status"),
        "input_quality_counts": counts("input_quality_status"),
        "model_version": frozen["model_version"],
        "model_code_hash": frozen["model_code_hash"],
        "frozen_config_hash": frozen.get("model_code_hash"),
        "test_manifest_hash": frozen.get("test_manifest_hash"),
    }

    provenance = {
        "weather_source": "Open-Meteo ERA5-Land (reanalysis estimate)",
        "satellite_source": "Planetary Computer STAC, Sentinel-2 L2A",
        "par_conversion": "shortwave x 0.5 (estimated)",
        "ewsi_components": ["NDMI (satellite)", "VPD (reanalysis)", "soil (reanalysis)"],
        "model_version": frozen["model_version"],
        "calibration_status": frozen["calibration_status"],
        "free_parameters": frozen["free_parameters"],
        "fixed_parameters": frozen["fixed_parameters"],
    }

    benchmark_summary = {
        "run_id": summary["run_id"],
        "model_version": frozen["model_version"],
        "model_code_hash": frozen["model_code_hash"],
        "calibration_status": frozen["calibration_status"],
        "started_at": summary["created_at"],
        "test_districts": summary["test_districts"],
        "test_record_count_manifest": summary["test_record_count"],
        "records_processed": len(records),
        "metrics_all": metrics.to_dict(),
        "metrics_by_district": {k: v.to_dict() for k, v in by_district.items()},
        "metrics_by_season": {k: v.to_dict() for k, v in by_season.items()},
        "metrics_by_input_quality": {k: v.to_dict() for k, v in by_quality.items()},
        "uncertainty": uncertainty,
        "input_quality_summary": quality,
        "provenance_summary": provenance,
        "note": (
            "Stage 40 calibrated run. Written to a separate directory; the "
            "Stage 39 baseline results are untouched."
        ),
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "sample": (
            {
                "design": sample_meta.get("design"),
                "frame_record_count": sample_meta.get("frame", {}).get("record_count"),
                "selected_total": sample_meta.get("selected_total"),
                "seed": sample_meta.get("seed"),
                "selected_ids_hash": sample_meta.get("selected_ids_hash"),
            }
            if sample_meta
            else None
        ),
    }

    for name, payload in (
        ("benchmark_summary.json", benchmark_summary),
        ("input_quality_summary.json", quality),
        ("provenance_summary.json", provenance),
    ):
        with open(work_dir / name, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

    print()
    print("=" * 60, flush=True)
    print("STAGE 40 BENCHMARK SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"records processed : {len(records)}", flush=True)
    print(f"metrics n        : {metrics.n}", flush=True)
    if metrics.n:
        print(f"RMSE             : {metrics.rmse:.4f} t/ha", flush=True)
        print(f"MAE              : {metrics.mae:.4f} t/ha", flush=True)
        print(f"Bias             : {metrics.bias:+.4f} t/ha", flush=True)
        print(f"R2               : {metrics.r2}", flush=True)
        print(f"MAPE             : {metrics.mape}", flush=True)
    print(f"uncertainty      : {uncertainty.get('status')}", flush=True)
    print(f"outputs          : {OUT_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
