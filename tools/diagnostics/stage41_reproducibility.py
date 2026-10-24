"""Stage 41 — re-run reproducibility check.

Compares the Stage 40 and Stage 41 predictions for the same records
under the same frozen model, and separates two effects:

1. **Run-to-run reproducibility** - does the same record recomputed with
   the same frozen model and the same inputs give the same answer?
2. **The epsilon-linearity identity** - does the baseline prediction
   reconstructed from the calibrated one match the real baseline
   prediction?

Effect 2 is only meaningful if effect 1 is clean, because the Stage 40
baseline was produced in a *different run* with its own inputs.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path("D:/HyDroMA")
DATA = ROOT / "engine/reports/data"
S40 = DATA / "stage40_test_benchmark/record_results.jsonl"
S41_DIR = DATA / "stage41_test_benchmark"
OUT = DATA / "stage41_reproducibility.json"

EPS_BASELINE = 2.2


def load(paths):
    out = {}
    for p in paths:
        if not Path(p).exists():
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    out[str(r["record_id"])] = r
    return out


def main() -> int:
    s40 = load([S40])
    s41 = load(sorted(glob.glob(str(S41_DIR / "shards" / "shard_*" / "record_results.jsonl"))))
    s41.update(load([S41_DIR / "record_results.jsonl"]))

    common = [
        rid for rid in s40
        if rid in s41
        and s40[rid].get("predicted_yield") is not None
        and s41[rid].get("predicted_yield") is not None
    ]
    print(f"records in both runs: {len(common)}")

    rows = []
    for rid in common:
        a = s40[rid]
        b = s41[rid]
        y40 = float(a["predicted_yield"])
        y41 = float(b["predicted_yield"])
        ratio = EPS_BASELINE / 2.630
        # Stage 40's own baseline for this record is not stored, so the
        # comparison is against the *reconstructed* baseline using each
        # run's own calibrated value.
        rows.append(
            {
                "record_id": rid,
                "district_id": b.get("district_id"),
                "season": b.get("season"),
                "observed": float(b["observed_yield"]),
                "stage40_calibrated": y40,
                "stage41_calibrated": y41,
                "abs_diff_calibrated": abs(y41 - y40),
                "rel_diff_calibrated": (
                    abs(y41 - y40) / abs(y40) if abs(y40) > 1e-12 else None
                ),
                "stage40_baseline_reconstructed": y40 * ratio,
                "stage41_baseline_reconstructed": y41 * ratio,
                "weather_valid_days_40": a.get("weather_valid_days"),
                "weather_valid_days_41": b.get("weather_valid_days"),
                "satellite_acq_40": a.get("satellite_acquisition_count"),
                "satellite_acq_41": b.get("satellite_acquisition_count"),
                "lai_status_40": a.get("lai_status"),
                "lai_status_41": b.get("lai_status"),
                "ewsi_status_40": a.get("ewsi_status"),
                "ewsi_status_41": b.get("ewsi_status"),
            }
        )

    diffs = [r["abs_diff_calibrated"] for r in rows]
    rels = [r["rel_diff_calibrated"] for r in rows if r["rel_diff_calibrated"] is not None]
    n_exact = sum(1 for d in diffs if d <= 1e-12)
    n_within_1e6 = sum(1 for d in diffs if d <= 1e-6)
    n_within_1e3 = sum(1 for d in diffs if d <= 1e-3)

    # Which inputs differ?
    differing_inputs = []
    for r in rows:
        diffs_in = []
        if r["lai_status_40"] != r["lai_status_41"]:
            diffs_in.append("lai_status")
        if r["ewsi_status_40"] != r["ewsi_status_41"]:
            diffs_in.append("ewsi_status")
        if r["satellite_acq_40"] is not None and r["satellite_acq_41"] is not None:
            if r["satellite_acq_40"] != r["satellite_acq_41"]:
                diffs_in.append("satellite_acquisition_count")
        r["differing_input_fields"] = diffs_in
        if diffs_in:
            differing_inputs.append(
                {
                    "record_id": r["record_id"],
                    "fields": diffs_in,
                    "abs_diff_calibrated": r["abs_diff_calibrated"],
                }
            )

    payload = {
        "purpose": (
            "Re-run control: does a record recomputed with the same frozen "
            "model reproduce the same prediction, and is the epsilon-linearity "
            "reconstruction of the baseline valid?"
        ),
        "epsilon_baseline": EPS_BASELINE,
        "epsilon_calibrated": 2.630,
        "records_compared": len(rows),
        "reproduction": {
            "n_exact_within_1e-12": n_exact,
            "n_within_1e-6": n_within_1e6,
            "n_within_1e-3": n_within_1e3,
            "max_abs_diff_t_ha": max(diffs) if diffs else None,
            "mean_abs_diff_t_ha": (sum(diffs) / len(diffs)) if diffs else None,
            "max_rel_diff": max(rels) if rels else None,
            "bit_identical": n_exact == len(rows) if rows else None,
        },
        "input_field_differences": {
            "records_with_any_input_difference": len(differing_inputs),
            "detail": differing_inputs[:50],
        },
        "records": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print()
    print(f"exact (<=1e-12)   : {n_exact}/{len(rows)}")
    print(f"within 1e-6       : {n_within_1e6}/{len(rows)}")
    print(f"within 1e-3       : {n_within_1e3}/{len(rows)}")
    print(f"max abs diff      : {max(diffs) if diffs else None}")
    print(f"records w/ input diffs: {len(differing_inputs)}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
