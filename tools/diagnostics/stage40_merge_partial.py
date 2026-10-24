"""Merge whatever shard results exist into a summary (used for partial checks)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
OUT_DIR = ROOT / "engine/reports/data/stage40_test_benchmark"
SHARD_DIR = OUT_DIR / "shards"
FROZEN = ROOT / "engine/reports/data/stage40_frozen_model_config.json"
SAMPLE = ROOT / "engine/reports/data/stage40_test_sample.json"


def main() -> int:
    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    metrics_mod = bootstrap.load_module("engine.hydroma.eval.stage39_benchmark")

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

    metrics = metrics_mod.compute_benchmark_metrics(merged, group="stage40_test")
    by_district = metrics_mod.compute_grouped_metrics(merged, "district_id")
    by_season = metrics_mod.compute_grouped_metrics(merged, "season")
    by_quality = metrics_mod.compute_grouped_metrics(merged, "input_quality_status")
    uncertainty = metrics_mod.cluster_bootstrap_uncertainty(merged)

    with open(FROZEN, encoding="utf-8") as f:
        frozen = json.load(f)
    with open(SAMPLE, encoding="utf-8") as f:
        sample_meta = json.load(f)

    def counts(key):
        out: dict[str, int] = {}
        for r in merged:
            v = str(r.get(key, "unknown"))
            out[v] = out.get(v, 0) + 1
        return out

    from collections import Counter

    got = Counter(f"{r.get('district_id')}|{r.get('season')}" for r in merged)
    cov_rows = {}
    for stratum, alloc in sorted(sample_meta.get("allocation", {}).items()):
        cov_rows[stratum] = {
            "design": alloc.get("allocated"),
            "evaluated": got.get(stratum, 0),
        }
    coverage = {
        "by_stratum": cov_rows,
        "strata_covered": sum(1 for v in cov_rows.values() if v["evaluated"] > 0),
        "strata_total": len(cov_rows),
    }

    status_counts = counts("execution_status")
    summary = {
        "run_id": "stage40_partial",
        "model_version": frozen["model_version"],
        "model_code_hash": frozen["model_code_hash"],
        "parameter_values": frozen["parameter_values"],
        "calibration_status": frozen["calibration_status"],
        "test_districts": ["Buxar", "Muzaffarpur", "Rohtas"],
        "records_processed": len(merged),
        "shards": 8,
        "realised_coverage": coverage,
        "sample": {
            "design": sample_meta.get("design"),
            "strata_definition": sample_meta.get("strata_definition"),
            "allocation_rule": sample_meta.get("allocation_rule"),
            "n_strata": sample_meta.get("n_strata"),
            "frame_record_count": sample_meta.get("frame", {}).get("record_count"),
            "frame_record_ids_hash": sample_meta.get("frame", {}).get("record_ids_hash"),
            "selected_total": sample_meta.get("selected_total"),
            "seed": sample_meta.get("seed"),
            "selected_ids_hash": sample_meta.get("selected_ids_hash"),
            "allocation": sample_meta.get("allocation"),
        },
        "execution_status_counts": status_counts,
        "input_quality_summary": {
            "input_quality_counts": counts("input_quality_status"),
            "ewsi_status_counts": counts("ewsi_status"),
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
        "uncertainty": uncertainty,
    }

    out = OUT_DIR / "benchmark_summary.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    results_path = OUT_DIR / "record_results.jsonl"
    with open(results_path, "w", encoding="utf-8") as f:
        for rec in merged:
            f.write(json.dumps(rec, default=str) + "\n")

    print(f"merged {len(merged)} -> {out}")
    print(f"RMSE {metrics.rmse}  MAE {metrics.mae}  bias {metrics.bias}  R2 {metrics.r2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
