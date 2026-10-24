"""Stage 40 — baseline equivalence check.

The Stage 40 work changed three things in the model path:

* ``HYRUE.__init__`` now gives explicit ``params`` precedence over the
  crop preset (previously the preset silently overwrote them);
* ``compute_hyrue_seasonal`` and ``SeasonalPredictionRequest`` accept an
  optional explicit parameter set;
* ``compute_seasonal_prediction`` accepts an optional ``input_sink``.

None of these change the *default* path, which is what the Stage 39
baseline used.  This script proves that empirically: it re-runs a sample
of the Stage 39 test records with the **current** code and the default
(crop-preset) parameters, and compares the predictions against the
recorded Stage 39 results.

A match means the Stage 39 baseline numbers remain valid for the
baseline-vs-calibrated comparison.
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
STAGE39 = ROOT / "engine/reports/data/stage39_benchmark/record_results.jsonl"
OUT = ROOT / "engine/reports/data/stage40_baseline_equivalence.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20240115)
    args = parser.parse_args()

    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()

    import pandas as pd

    runner_mod = bootstrap.load_module("engine.hydroma.eval.resumable_benchmark_runner")

    # --- Load the recorded Stage 39 results ---
    recorded: dict[str, dict] = {}
    with open(STAGE39, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("predicted_yield") is not None:
                recorded[str(rec["record_id"])] = rec
    print(f"stage 39 results with a prediction: {len(recorded)}", flush=True)

    # --- Load the source records for those ids ---
    cimmyt = ROOT / "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
    df = pd.read_excel(cimmyt)
    df = df[df["Field_ID"].astype(str).isin(recorded.keys())].copy()
    print(f"source records found: {len(df)}", flush=True)

    # Deterministic sample, spread across districts and seasons.
    df["stratum"] = df["District"].astype(str) + "|" + df["Year"].astype(str)
    strata = sorted(df["stratum"].unique())
    per_stratum = max(1, args.sample // max(len(strata), 1))
    picked = []
    for stratum in strata:
        subset = df[df["stratum"] == stratum]
        subset = subset.sample(n=min(per_stratum, len(subset)), random_state=args.seed)
        picked.extend(list(subset.itertuples(index=False)))
    sample = pd.DataFrame(picked).head(args.sample)
    print(f"sampled {len(sample)} records", flush=True)

    # --- Re-run with the current code and the default (preset) parameters ---
    runner = runner_mod.ResumableBenchmarkRunner(
        db_path=ROOT / "engine/reports/data/stage40_equiv_state.sqlite",
        results_path=ROOT / "engine/reports/data/stage40_equiv_results.jsonl",
        manifest_path=ROOT / "engine/reports/data/stage40_equiv_manifest.json",
        run_id="stage40_equivalence",
        data_label="stage40_equivalence",
    )

    comparisons = []
    for i, row in enumerate(sample.itertuples(index=False), 1):
        record = pd.Series(row._asdict())
        rid = str(row.Field_ID)
        try:
            result = runner.process_record(record)
        except Exception as exc:
            comparisons.append(
                {
                    "record_id": rid,
                    "status": "ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        ref = recorded.get(rid)
        new = result.predicted_yield
        old = ref.get("predicted_yield") if ref else None
        if new is None or old is None:
            comparisons.append(
                {
                    "record_id": rid,
                    "status": "NO_PREDICTION",
                    "stage39": old,
                    "stage40_rerun": new,
                }
            )
        else:
            diff = abs(new - old)
            comparisons.append(
                {
                    "record_id": rid,
                    "district_id": result.district_id,
                    "season": result.season,
                    "status": "COMPARED",
                    "stage39": old,
                    "stage40_rerun": new,
                    "abs_diff": diff,
                    "identical": diff <= 1e-12,
                }
            )
        if i % 10 == 0:
            print(f"  [{i}/{len(sample)}]", flush=True)

    compared = [c for c in comparisons if c.get("status") == "COMPARED"]
    identical = [c for c in compared if c.get("identical")]
    max_diff = max((c["abs_diff"] for c in compared), default=None)
    no_pred = [c for c in comparisons if c.get("status") == "NO_PREDICTION"]

    payload = {
        "purpose": (
            "Verify that the Stage 39 baseline results remain valid after the "
            "Stage 40 parameter-plumbing changes."
        ),
        "seed": args.seed,
        "sampled": len(sample),
        "compared": len(compared),
        "identical": len(identical),
        "not_identical": len(compared) - len(identical),
        "no_prediction": len(no_pred),
        "max_abs_difference_t_ha": max_diff,
        "verdict": (
            "baseline_preserved"
            if compared and len(identical) == len(compared)
            else "baseline_changed_or_incomplete"
        ),
        "tolerance_t_ha": 1e-12,
        "comparisons": comparisons,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print()
    print(f"compared        : {len(compared)}")
    print(f"identical       : {len(identical)}")
    print(f"max abs diff    : {max_diff}")
    print(f"no prediction   : {len(no_pred)}")
    print(f"verdict         : {payload['verdict']}")
    print(f"written         : {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
