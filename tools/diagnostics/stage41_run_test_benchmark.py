"""Stage 41 — run the full 1,722-record frozen-model test benchmark.

Same frozen Stage 40 model (unchanged), extended from the 450-record
stratified sample to the **complete** test-district frame.

The record schema is enriched with the Stage 41 provenance requirements:
model code hash, resolved-input data hash, valid satellite acquisition
count, valid weather day count, and weather/satellite provenance.

The run is sharded, resumable and self-healing: each shard owns its own
state database, and a relaunch skips records already in a terminal state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
DATA = ROOT / "engine/reports/data"
FROZEN = DATA / "stage40_frozen_model_config.json"
MANIFEST41 = DATA / "stage41_frozen_model_manifest.json"
OUT_DIR = DATA / "stage41_test_benchmark"


def _json_safe(value):
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--capture-resolved-inputs", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.shard_count > 1:
        work_dir = out_dir / "shards" / f"shard_{args.shard_index:02d}"
    else:
        work_dir = out_dir
    work_dir.mkdir(parents=True, exist_ok=True)

    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()
    runner_mod = bootstrap.load_module("engine.hydroma.eval.resumable_benchmark_runner")
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

    code_file_hashes = {}
    for relative_path in frozen["file_hashes"]:
        source_path = ROOT / relative_path
        code_file_hashes[relative_path] = hashlib.sha256(
            source_path.read_bytes()
        ).hexdigest()
    model_code_hash = hashlib.sha256(
        json.dumps(code_file_hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()

    # Baseline parameter set: the uncalibrated wheat preset (epsilon 2.2).
    # Every record gets a second prediction from the SAME resolved inputs,
    # so the baseline/calibrated comparison is exactly like-for-like.
    baseline_values = dict(values)
    baseline_values["epsilon"] = 2.2
    baseline_params = hyrue_mod.HYRUEParams(
        epsilon=baseline_values["epsilon"],
        k=baseline_values["k"],
        hi=baseline_values["hi"],
        lai_max=baseline_values["lai_max"],
        t_opt=baseline_values["t_opt"],
        t_min=baseline_values["t_min"],
        t_max=baseline_values["t_max"],
    )

    runner = runner_mod.ResumableBenchmarkRunner(
        db_path=work_dir / "execution_state.sqlite",
        results_path=work_dir / "record_results.jsonl",
        manifest_path=work_dir / "run_manifest.json",
        hyrue_params=params,
        baseline_params=baseline_params,
        run_id="stage41e_live",
        data_label="stage41e_live_full_frame",
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        model_code_hash=model_code_hash,
    )
    resolved_inputs = [] if args.capture_resolved_inputs else None
    runner.input_sink = resolved_inputs

    print("=" * 62, flush=True)
    print(
        f"Stage 41-E live-input benchmark "
        f"shard {args.shard_index}/{args.shard_count}",
        flush=True,
    )
    print(
        f"frozen model v{frozen['model_version']}: "
        f"epsilon={values['epsilon']:.4f}, hi={values['hi']}, "
        f"t_opt={values['t_opt']}, lai_max={values['lai_max']}",
        flush=True,
    )
    print(f"model code hash: {model_code_hash}", flush=True)
    print("=" * 62, flush=True)

    summary = runner.run(max_records=args.max_records)
    print(f"shard {args.shard_index} done: {summary}", flush=True)

    identity = {
        "run_id": "stage41e_live",
        "data_label": "stage41e_live_full_frame",
        "model_code_hash": model_code_hash,
        "current_code_file_hashes": code_file_hashes,
        "frozen_config_sha256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
        "frozen_parameters": values,
        "baseline_epsilon": baseline_values["epsilon"],
        "captured_inputs": args.capture_resolved_inputs,
    }
    (work_dir / "execution_identity.json").write_text(
        json.dumps(identity, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if resolved_inputs is not None:
        with (work_dir / "resolved_inputs.jsonl").open(
            "w", encoding="utf-8"
        ) as input_file:
            for resolved_input in resolved_inputs:
                input_file.write(
                    json.dumps(_json_safe(resolved_input), allow_nan=False) + "\n"
                )

    # Completion marker.  On this platform the venv ``python.exe`` is a
    # launcher that spawns the real interpreter as a child, so the
    # launcher's exit does not mean the shard is finished.  The driver
    # waits for this marker instead of for the process.
    try:
        (work_dir / "DONE").write_text(
            f"{summary.get('completed', 0)} {summary.get('failed', 0)}",
            encoding="utf-8",
        )
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
