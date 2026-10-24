"""Stage 40 — build the stratified test-benchmark sample.

The Sentinel-2 COG reads dominate the benchmark cost (~66-130 s per band
per acquisition), and the upstream APIs throttle beyond roughly eight
concurrent readers, so evaluating all 1,722 test records would take
several hours of wall clock.

The benchmark is therefore run on a **documented stratified sample** of
the test set rather than the full set.  The design is:

* **Frame**: all 1,722 test-district records (Buxar, Muzaffarpur,
  Rohtas) in the CIMMYT eastern-India wheat dataset.
* **Strata**: district x season (3 x 6 = 18 strata).
* **Allocation**: proportional to stratum size, with a floor of
  ``min_per_stratum`` records per stratum so that every season of every
  district is represented.
* **Selection**: simple random sample without replacement within each
  stratum, with a fixed seed.
* **Seed**: 20240115 (the same seed used for the development profiles).

The manifest records the frame size, the allocation, the selected record
ids and a hash, so the sample is reproducible and auditable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
CIMMYT = ROOT / "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
OUT = ROOT / "engine/reports/data/stage40_test_sample.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=int, default=450)
    parser.add_argument("--min-per-stratum", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20240115)
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    split = bootstrap.load_module("engine.hydroma.eval.benchmark_split_manifest")

    import pandas as pd

    manifest = split.load_split_manifest()
    test_districts = manifest["test_districts"]

    df = pd.read_excel(CIMMYT)
    test = df[df["District"].isin(test_districts)].copy()
    frame_size = len(test)
    print(f"test frame size: {frame_size}", flush=True)

    test["stratum"] = test["District"].astype(str) + "|" + test["Year"].astype(str)
    strata = sorted(test["stratum"].unique())

    sizes = {s: int((test["stratum"] == s).sum()) for s in strata}
    print(f"strata: {len(strata)}", flush=True)

    # --- Proportional allocation with a floor ---
    raw = {s: args.total * sizes[s] / frame_size for s in strata}
    alloc = {s: max(args.min_per_stratum, int(raw[s])) for s in strata}
    # Fix up to the requested total without dropping a stratum below 1.
    while sum(alloc.values()) > args.total:
        # Take one from the largest over-allocation.
        s = max(alloc, key=lambda k: alloc[k] - raw[k])
        if alloc[s] <= 1:
            break
        alloc[s] -= 1
    # Distribute any remainder to the strata with the most headroom.
    while sum(alloc.values()) < args.total:
        s = max(strata, key=lambda k: sizes[k] - alloc[k])
        if sizes[s] - alloc[s] <= 0:
            break
        alloc[s] += 1
    for s in strata:
        alloc[s] = min(alloc[s], sizes[s])

    print(f"allocated total: {sum(alloc.values())}", flush=True)

    # --- Random selection within each stratum ---
    selected: list[str] = []
    allocation_detail = {}
    for s in strata:
        n = alloc[s]
        subset = test[test["stratum"] == s]
        picked = subset.sample(n=n, random_state=args.seed)
        picked_ids = [str(x) for x in picked["Field_ID"].tolist()]
        selected.extend(picked_ids)
        allocation_detail[s] = {
            "frame": sizes[s],
            "allocated": n,
            "selected": len(picked_ids),
            "proportional_target": round(raw[s], 2),
        }

    selected = sorted(set(selected))
    frame_ids = sorted({str(x) for x in test["Field_ID"].tolist()})
    overlap = len(set(selected) & set(frame_ids))

    payload = {
        "design": "stratified simple random sample without replacement",
        "frame": {
            "source": str(CIMMYT),
            "districts": test_districts,
            "record_count": frame_size,
            "record_ids_hash": hashlib.sha256(
                ",".join(frame_ids).encode()
            ).hexdigest(),
        },
        "strata_definition": "district x season",
        "n_strata": len(strata),
        "allocation_rule": (
            "proportional to stratum size, floor of min_per_stratum, capped "
            "at the stratum size"
        ),
        "min_per_stratum": args.min_per_stratum,
        "requested_total": args.total,
        "selected_total": len(selected),
        "seed": args.seed,
        "selected_ids_hash": hashlib.sha256(
            ",".join(selected).encode()
        ).hexdigest(),
        "all_selected_in_frame": overlap == len(selected),
        "allocation": allocation_detail,
        "record_ids": selected,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print()
    print(f"selected         : {len(selected)}")
    print(f"all in frame     : {payload['all_selected_in_frame']}")
    print(f"selected ids hash: {payload['selected_ids_hash'][:24]}")
    print(f"written          : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
