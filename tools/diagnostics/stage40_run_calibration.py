"""Stage 40 — execute the identifiability-constrained calibration.

Reads the cached development season profiles, fits ``epsilon`` with ``HI``
held fixed, runs leave-one-district-out cross-validation, assesses
parameter stability, and writes the frozen model configuration.

Writes:
    engine/reports/data/stage40_calibration_results.json
    engine/reports/data/stage40_frozen_model_config.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
PROFILES = ROOT / "engine/reports/data/stage40_dev_profiles.json"
NPZ = ROOT / "engine/reports/data/stage40_dev_profiles.npz"
CALIB_OUT = ROOT / "engine/reports/data/stage40_calibration_results.json"
FROZEN_OUT = ROOT / "engine/reports/data/stage40_frozen_model_config.json"


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hi", type=float, default=0.45)
    parser.add_argument("--min-train-records", type=int, default=3)
    args = parser.parse_args()

    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    calib = bootstrap.load_module("engine.hydroma.eval.identifiability_calibration")
    split = bootstrap.load_module("engine.hydroma.eval.benchmark_split_manifest")

    manifest = split.load_split_manifest()
    test_districts = manifest["test_districts"]

    # --- Load profiles ---
    with open(PROFILES, encoding="utf-8") as f:
        payload = json.load(f)

    npz = np.load(NPZ, allow_pickle=True)
    profiles = []
    for i, meta in enumerate(payload["profiles"]):
        profiles.append(
            calib.SeasonProfile(
                record_id=meta["record_id"],
                district_id=meta["district_id"],
                season=meta["season"],
                observed_yield=meta["observed_yield"],
                s_integral=meta["s_integral"],
                n_days=meta["n_days"],
                par=npz["par"][i],
                lai=npz["lai"][i],
                ewsi=npz["ewsi"][i],
                t_mean=npz["t_mean"][i],
                input_quality=meta["input_quality"],
                ewsi_missing=meta["ewsi_missing"],
            )
        )
    print(f"loaded {len(profiles)} development profiles", flush=True)

    # --- Leakage guard (before anything else) ---
    calib.assert_no_test_districts(
        [
            {"record_id": p.record_id, "district_id": p.district_id}
            for p in profiles
        ],
        test_districts,
    )
    print("leakage guard: no test-district records present", flush=True)

    # --- Part A: experimental calibration on the sample ---
    fit = calib.calibrate_epsilon(profiles, hi=args.hi)
    print()
    print("=== experimental calibration (development sample) ===", flush=True)
    print(f"  n records        : {fit['n_records']}", flush=True)
    print(f"  fitted epsilon   : {fit['fitted_value']:.3f} g/MJ IPAR", flush=True)
    print(f"  HI held fixed at : {fit['hi_fixed']}", flush=True)
    print(
        f"  baseline RMSE    : {fit['baseline_metrics']['rmse']:.4f}",
        flush=True,
    )
    print(
        f"  calibrated RMSE  : {fit['fitted_metrics']['rmse']:.4f}",
        flush=True,
    )
    print(
        f"  baseline R2      : {fit['baseline_metrics']['r2']}",
        flush=True,
    )
    print(
        f"  calibrated R2    : {fit['fitted_metrics']['r2']}",
        flush=True,
    )
    print(
        f"  objective spread : {fit['objective_relative_spread']:.4f} "
        f"(flat={fit['objective_flat']})",
        flush=True,
    )

    # --- Part B: leave-one-district-out cross-validation ---
    lodo = calib.leave_one_district_out(
        profiles,
        test_districts=test_districts,
        hi=args.hi,
        min_train_records=args.min_train_records,
    )
    stability = lodo["stability"]
    print()
    print("=== leave-one-district-out ===", flush=True)
    print(f"  folds run        : {stability['n_folds']}", flush=True)
    print(f"  skipped folds    : {len(stability['skipped_folds'])}", flush=True)
    print(f"  epsilon values   : {[round(v, 3) for v in stability['values']]}", flush=True)
    print(f"  mean / std       : {stability['mean']:.3f} / {stability['std']:.3f}", flush=True)
    print(f"  relative range   : {stability['relative_range']:.4f}", flush=True)
    print(f"  stable           : {stability['stable']}", flush=True)
    print(
        f"  validation RMSE  : calibrated {stability['mean_validation_rmse_calibrated']:.4f} "
        f"vs baseline {stability['mean_validation_rmse_baseline']:.4f}",
        flush=True,
    )
    print(
        f"  improves validation: {stability['calibration_improves_validation']}",
        flush=True,
    )

    stability_report = calib.parameter_stability_report(
        stability["values"], parameter="epsilon"
    )

    # --- Part C: freeze ---
    fitted = fit["fitted_value"]
    all_metrics = calib.evaluate(profiles, epsilon=fitted, hi=args.hi)
    baseline_metrics = calib.evaluate(
        profiles,
        epsilon=calib.PARAMETER_REGISTRY["epsilon"].default_value,
        hi=args.hi,
    )

    code_hashes = {
        p: sha256_file(ROOT / p)
        for p in (
            "engine/hydroma/models/hyrue.py",
            "engine/hydroma/simulation/par_pipeline.py",
            "engine/hydroma/simulation/weather_source.py",
            "engine/hydroma/simulation/lai_model.py",
            "engine/hydroma/simulation/ewsi_pipeline.py",
            "engine/hydroma/simulation/radiation_units.py",
            "engine/hydroma/eval/seasonal_predictor.py",
            "engine/hydroma/eval/identifiability_calibration.py",
        )
    }
    model_code_hash = hashlib.sha256(
        json.dumps(code_hashes, sort_keys=True).encode()
    ).hexdigest()

    frozen = {
        "model_name": "HY-RUE",
        "model_version": "2.0.1",
        "code_commit": "working tree (no commit recorded)",
        "model_code_hash": model_code_hash,
        "file_hashes": code_hashes,
        "calibration_status": (
            "calibrated" if stability["calibration_improves_validation"] else
            "calibrated_no_validation_gain"
        ),
        "calibration_method": (
            "deterministic grid search on RMSE over the pre-registered "
            "epsilon bounds, HI held fixed, validated leave-one-district-out"
        ),
        "objective_function": "RMSE on development-district records (t/ha)",
        "optimisation_method": "grid search (0.1 coarse, 0.01 refine)",
        "random_seed": payload.get("seed"),
        "calibration_dataset_hash": payload.get("profiles_hash"),
        "calibration_record_ids_hash": payload.get("profiles_hash"),
        "test_manifest_hash": sha256_file(
            ROOT / "engine/reports/data/stage36_benchmark_split_manifest.json"
        ),
        "cross_validation_protocol": (
            "leave-one-district-out over the development districts; the held-out "
            "district contributes to neither the fit nor any data-dependent "
            "transformation"
        ),
        "equation_version": "hyrue.py as of Stage 40",
        "radiation_contract_version": "stage37_v1",
        "remote_sensing_pipeline_version": "stage39_v1",
        "input_policy": "allow_estimated",
        "freeze_timestamp": datetime.now(UTC).isoformat(),
        "parameter_values": {
            "epsilon": fitted,
            "hi": args.hi,
            "k": calib.PARAMETER_REGISTRY["k"].default_value,
            "lai_max": calib.PARAMETER_REGISTRY["lai_max"].default_value,
            "t_opt": calib.PARAMETER_REGISTRY["t_opt"].default_value,
            "t_min": calib.PARAMETER_REGISTRY["t_min"].default_value,
            "t_max": calib.PARAMETER_REGISTRY["t_max"].default_value,
            "thermal_gaussian_width": 8.0,
            "ewsi_weight_ndmi": 0.4,
            "ewsi_weight_vpd": 0.3,
            "ewsi_weight_soil": 0.3,
            "ndmi_ref": 0.3,
            "ndmi_crit": -0.2,
            "vpd_low": 0.5,
            "vpd_high": 4.0,
            "soil_field_capacity": 0.35,
            "shortwave_to_par_factor": 0.5,
        },
        "parameter_bounds": {
            name: [spec.allowed_min, spec.allowed_max]
            for name, spec in calib.PARAMETER_REGISTRY.items()
        },
        "fixed_parameters": sorted(
            name
            for name, spec in calib.PARAMETER_REGISTRY.items()
            if spec.parameter_class
            in (calib.ParameterClass.FIXED, calib.ParameterClass.INSUFFICIENT_DATA)
        ),
        "free_parameters": ["epsilon"],
        "parameter_classes": {
            name: spec.parameter_class.value
            for name, spec in calib.PARAMETER_REGISTRY.items()
        },
        "development_metrics": all_metrics,
        "baseline_metrics_same_records": baseline_metrics,
        "sample_record_count": len(profiles),
        "sample_districts": sorted({p.district_id for p in profiles}),
        "sample_seasons": sorted({p.season for p in profiles}),
        "note": (
            "Calibrated on a stratified development sample, not the full "
            "development set (the full set costs ~33 h of API-bound compute). "
            "The sample is documented in stage40_dev_profiles.json."
        ),
    }

    FROZEN_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(FROZEN_OUT, "w", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2, default=str)
    with open(CALIB_OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "experimental_calibration": fit,
                "leave_one_district_out": lodo,
                "parameter_stability": stability_report,
                "frozen_config_path": str(FROZEN_OUT),
            },
            f,
            indent=2,
            default=str,
        )

    print()
    print(f"frozen config : {FROZEN_OUT}", flush=True)
    print(f"calibration   : {CALIB_OUT}", flush=True)
    print(f"epsilon       : {fitted:.4f} g/MJ IPAR (HI fixed at {args.hi})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
