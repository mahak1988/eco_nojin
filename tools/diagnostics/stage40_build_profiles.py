"""Stage 40 — build cached season profiles from development-district records.

Runs the full pipeline (weather -> satellite -> EWSI -> HYRUE daily terms)
once per development record and stores the daily arrays plus the
seasonal light-and-stress integral ``S``.

Because ``epsilon`` and ``HI`` multiply ``S`` after the daily sum, caching
``S`` makes every subsequent parameter sweep free.  This is what makes an
identifiability-constrained calibration feasible within a session.

Writes ``engine/reports/data/stage40_dev_profiles.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
sys.path.insert(0, str(ROOT))

CIMMYT = ROOT / "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
OUT = ROOT / "engine/reports/data/stage40_dev_profiles.json"


def load_engine():
    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    return bootstrap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-records", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20240115)
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    bootstrap = load_engine()
    # Load the model modules first: they carry the relative imports
    # (``from .base import ...``) that the sandbox's directory scan
    # intermittently breaks.
    hyrue_mod = bootstrap.load_module("engine.hydroma.models.hyrue")
    split = bootstrap.load_module("engine.hydroma.eval.benchmark_split_manifest")
    calib = bootstrap.load_module("engine.hydroma.eval.identifiability_calibration")
    runner_mod = bootstrap.load_module("engine.hydroma.eval.resumable_benchmark_runner")

    manifest = split.load_split_manifest()
    dev_districts = manifest["development_districts"]
    test_districts = manifest["test_districts"]
    dev_ids = set(manifest["development_record_ids"])

    df = pd.read_excel(CIMMYT)
    dev_df = df[df["Field_ID"].isin(dev_ids)].copy()
    print(f"development records in dataset: {len(dev_df)}", flush=True)

    # Deterministic, stratified sample: spread across districts and seasons.
    dev_df["stratum"] = dev_df["District"].astype(str) + "|" + dev_df["Year"].astype(str)
    strata = sorted(dev_df["stratum"].unique())
    per_stratum = max(1, args.max_records // max(len(strata), 1))
    picked: list[pd.Series] = []
    for stratum in strata:
        subset = dev_df[dev_df["stratum"] == stratum]
        subset = subset.sample(n=min(per_stratum, len(subset)), random_state=args.seed)
        picked.extend(list(subset.itertuples(index=False)))
    sample = pd.DataFrame(picked).head(args.max_records)
    print(f"sampled {len(sample)} records across {sample['stratum'].nunique()} strata", flush=True)

    params = hyrue_mod.HYRUEParams.for_crop("wheat")

    # The profiles are built by the *same* runner the benchmark uses, so the
    # daily arrays cached here are exactly the ones the benchmark evaluates
    # on.  This removes the train/serve skew that a hand-rolled profile
    # builder would introduce (different LAI model, different PAR factor).
    runner = runner_mod.ResumableBenchmarkRunner(
        db_path=ROOT / "engine/reports/data/stage40_profile_state.sqlite",
        results_path=ROOT / "engine/reports/data/stage40_profile_results.jsonl",
        manifest_path=ROOT / "engine/reports/data/stage40_profile_manifest.json",
        run_id="stage40_profile",
        data_label="stage40_profile",
    )

    profiles = []
    failures = []
    t_start = time.time()

    for i, row in enumerate(sample.itertuples(index=False), 1):
        record = pd.Series(row._asdict())
        try:
            sink: list = []
            runner.input_sink = sink
            result = runner.process_record(record)
            runner.input_sink = None

            if not sink:
                raise ValueError(
                    "pipeline did not resolve daily inputs "
                    f"(status={result.execution_status})"
                )
            resolved = sink[-1]

            par = np.asarray(resolved["par"], dtype=float)
            lai = np.asarray(resolved["lai"], dtype=float)
            ewsi_arr = np.asarray(resolved["ewsi"], dtype=float)
            t_mean = np.asarray(resolved["t_mean"], dtype=float)
            n_days = int(par.size)

            params = hyrue_mod.HYRUEParams.for_crop("wheat")
            f_ipar = hyrue_mod.HYRUE.f_ipar(lai, params.k, params.lai_max)
            f_water = 1.0 - ewsi_arr
            below = t_mean < params.t_min
            above = t_mean > params.t_max
            clipped = np.where(below | above, params.t_opt, t_mean)
            f_temp = np.exp(-(((clipped - params.t_opt) / 8.0) ** 2))
            f_temp = np.where(below | above, 0.0, f_temp)
            s_integral = float(np.sum(par * f_ipar * f_water * f_temp))

            lai_prov = resolved.get("lai_provenance") or {}
            ewsi_prov = resolved.get("ewsi_provenance") or {}
            missing = list(resolved.get("missing_fields") or [])
            ewsi_missing = list((ewsi_prov or {}).get("missing_fields") or [])

            profile = calib.SeasonProfile(
                record_id=str(row.Field_ID),
                district_id=str(row.District),
                season=str(row.Year),
                observed_yield=float(row.GrainYield),
                s_integral=s_integral,
                n_days=n_days,
                par=par,
                lai=lai,
                ewsi=ewsi_arr,
                t_mean=t_mean,
                input_quality=resolved.get("input_quality", "complete"),
                ewsi_missing=ewsi_missing,
            )
            profiles.append(profile)
            print(
                f"[{i}/{len(sample)}] {row.Field_ID} {row.District} {row.Year}: "
                f"S={s_integral:.1f} obs={row.GrainYield} "
                f"lai={lai_prov.get('quality_status', '?')} "
                f"ewsi_missing={ewsi_missing} missing={missing}",
                flush=True,
            )
        except Exception as exc:
            failures.append(
                {
                    "record_id": str(row.Field_ID),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            print(f"[{i}/{len(sample)}] {row.Field_ID}: FAILED {exc}", flush=True)

    elapsed = time.time() - t_start

    payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "seed": args.seed,
        "requested_records": args.max_records,
        "n_profiles": len(profiles),
        "n_failures": len(failures),
        "elapsed_seconds": elapsed,
        "development_districts": dev_districts,
        "test_districts_excluded": test_districts,
        "strata_sampled": sample["stratum"].nunique(),
        "profiles_hash": calib.hash_profiles(profiles),
        "failures": failures,
        "profiles": [
            {
                "record_id": p.record_id,
                "district_id": p.district_id,
                "season": p.season,
                "observed_yield": p.observed_yield,
                "s_integral": p.s_integral,
                "n_days": p.n_days,
                "input_quality": p.input_quality,
                "ewsi_missing": p.ewsi_missing,
            }
            for p in profiles
        ],
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    # Also persist the daily arrays so parameter sweeps over k / t_opt are free.
    npz_path = out_path.with_suffix(".npz")
    np.savez_compressed(
        npz_path,
        record_ids=np.array([p.record_id for p in profiles]),
        districts=np.array([p.district_id for p in profiles]),
        par=np.array([p.par for p in profiles], dtype=object),
        lai=np.array([p.lai for p in profiles], dtype=object),
        ewsi=np.array([p.ewsi for p in profiles], dtype=object),
        t_mean=np.array([p.t_mean for p in profiles], dtype=object),
    )

    print()
    print(f"profiles built : {len(profiles)} ({len(failures)} failed)")
    print(f"elapsed        : {elapsed:.1f}s")
    print(f"written        : {out_path}")
    print(f"arrays         : {npz_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
