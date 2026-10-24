"""Stage 40 — baseline vs calibrated on the *same* test records.

The Stage 39 baseline run covered only 40 test records, all from the
2016-17 season.  Comparing that against a full calibrated run would
compare different record sets, so this script evaluates **both**
parameter sets on the *same* records.

How the baseline is obtained
----------------------------
HYRUE's seasonal yield is exactly linear in epsilon:

    Y = epsilon * S * HI / 100

so for a fixed record with identical resolved inputs,

    Y_baseline = Y_calibrated * (epsilon_baseline / epsilon_calibrated)

This is an identity, not an approximation.  It is *validated* below
against the 40 records for which a real baseline prediction exists
(the Stage 39 run), and the validation is reported.

The validated baseline is then evaluated over every record the
calibrated run covered, giving a like-for-like comparison.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _pathutil import load_module as _load_module  # noqa: E402

ROOT = Path("D:/HyDroMA")
DATA = ROOT / "engine/reports/data"
STAGE40 = DATA / "stage40_test_benchmark/record_results.jsonl"
STAGE39 = DATA / "stage39_benchmark/record_results.jsonl"
FROZEN = DATA / "stage40_frozen_model_config.json"
OUT = DATA / "stage40_baseline_vs_calibrated.json"


def metrics(pairs: list[tuple[float, float]]) -> dict:
    """pairs = [(observed, predicted), ...]"""
    if not pairs:
        return {"n": 0, "rmse": None, "mae": None, "bias": None, "r2": None, "mape": None}
    import math

    n = len(pairs)
    ss_res = sum((o - p) ** 2 for o, p in pairs)
    mean_o = sum(o for o, _ in pairs) / n
    ss_tot = sum((o - mean_o) ** 2 for o, _ in pairs)
    rmse = math.sqrt(ss_res / n)
    mae = sum(abs(o - p) for o, p in pairs) / n
    bias = sum(p - o for o, p in pairs) / n
    r2 = None if ss_tot <= 1e-12 else 1.0 - ss_res / ss_tot
    nz = [(o, p) for o, p in pairs if abs(o) > 1e-6]
    mape = (
        sum(abs(p - o) / abs(o) for o, p in nz) / len(nz) * 100.0 if nz else None
    )
    return {
        "n": n,
        "rmse": rmse,
        "mae": mae,
        "bias": bias,
        "r2": r2,
        "mape": mape,
    }


def _num(v, digits=4):
    """Format a number, tolerating None."""
    return "n/a" if v is None else f"{v:.{digits}f}"


def main() -> int:
    bootstrap = _load_module(
        "_rt", str(ROOT / "engine/hydroma/eval/runtime_bootstrap.py")
    )
    bootstrap.ensure_engine_importable()

    with open(FROZEN, encoding="utf-8") as f:
        frozen = json.load(f)
    eps_cal = float(frozen["parameter_values"]["epsilon"])
    eps_base = 2.2  # HYRUEParams CROP_PRESETS["wheat"]
    ratio = eps_base / eps_cal

    def load(path: Path) -> list[dict]:
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    cal_records = load(STAGE40)
    base_records = load(STAGE39)

    cal = {
        str(r["record_id"]): r
        for r in cal_records
        if r.get("predicted_yield") is not None
    }
    base_real = {
        str(r["record_id"]): r
        for r in base_records
        if r.get("predicted_yield") is not None
    }

    print(f"calibrated records with a prediction : {len(cal)}")
    print(f"stage 39 baseline records            : {len(base_real)}")

    # --- Validation of the linearity identity on real baseline records ---
    validation = []
    for rid, brec in base_real.items():
        crec = cal.get(rid)
        if crec is None:
            continue
        derived = float(crec["predicted_yield"]) * ratio
        actual = float(brec["predicted_yield"])
        validation.append(
            {
                "record_id": rid,
                "district_id": crec.get("district_id"),
                "season": crec.get("season"),
                "baseline_actual": actual,
                "baseline_derived": derived,
                "abs_diff": abs(derived - actual),
                "rel_diff": (
                    abs(derived - actual) / abs(actual) if abs(actual) > 1e-12 else None
                ),
            }
        )

    max_abs = max((v["abs_diff"] for v in validation), default=None)
    max_rel = max(
        (v["rel_diff"] for v in validation if v["rel_diff"] is not None), default=None
    )
    n_valid = len(validation)
    n_within = sum(
        1
        for v in validation
        if v["abs_diff"] <= 1e-9 * max(1.0, abs(v["baseline_actual"]))
    )

    print()
    print("=== linearity identity validation (real baseline records) ===")
    print(f"  compared     : {n_valid}")
    print(f"  within 1e-9  : {n_within}")
    print(f"  max abs diff : {max_abs}")
    print(f"  max rel diff : {max_rel}")

    identity_validated = n_valid > 0 and n_within == n_valid
    print(f"  validated    : {identity_validated}")

    # --- Like-for-like comparison over every calibrated record ---
    def collect(records: dict) -> tuple[list, dict, dict, dict]:
        overall = []
        by_district: dict[str, list] = {}
        by_season: dict[str, list] = {}
        by_status: dict[str, list] = {}
        for rec in records.values():
            obs = float(rec["observed_yield"])
            cal_y = float(rec["predicted_yield"])
            overall.append((obs, cal_y))
            by_district.setdefault(str(rec.get("district_id")), []).append((obs, cal_y))
            by_season.setdefault(str(rec.get("season")), []).append((obs, cal_y))
            by_status.setdefault(str(rec.get("input_quality_status")), []).append(
                (obs, cal_y)
            )
        return overall, by_district, by_season, by_status

    overall_cal, by_district, by_season, by_status = collect(cal)
    overall_base = [(o, p * ratio) for o, p in overall_cal]

    def group_table(mapping):
        return {
            key: {
                "calibrated": metrics(pairs),
                "baseline": metrics([(o, p * ratio) for o, p in pairs]),
            }
            for key, pairs in sorted(mapping.items())
        }

    payload = {
        "method": (
            "Baseline evaluated on the same records as the calibrated model "
            "via the exact linearity of HYRUE yield in epsilon "
            "(Y = epsilon * S * HI / 100); identity validated against the "
            "real Stage 39 baseline predictions."
        ),
        "epsilon_calibrated": eps_cal,
        "epsilon_baseline": eps_base,
        "ratio_baseline_over_calibrated": ratio,
        "identity_validation": {
            "records_compared": n_valid,
            "records_within_1e-9": n_within,
            "max_abs_difference_t_ha": max_abs,
            "max_relative_difference": max_rel,
            "validated": identity_validated,
            "tolerance": "abs diff <= 1e-9 * max(1, |actual|)",
            "detail": validation,
        },
        "n_records_compared": len(overall_cal),
        "calibrated": metrics(overall_cal),
        "baseline": metrics(overall_base),
        "by_district": group_table(by_district),
        "by_season": group_table(by_season),
        "by_input_quality": group_table(by_status),
        "n_stage39_records_available": len(base_real),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print()
    print("=== like-for-like comparison ===")
    b = payload["baseline"]
    c = payload["calibrated"]
    print(f"  records      : {len(overall_cal)}")
    print(f"  baseline   rmse {_num(b.get('rmse'))}  r2 {_num(b.get('r2'))}")
    print(f"  calibrated rmse {_num(c.get('rmse'))}  r2 {_num(c.get('r2'))}")
    print(f"  written      : {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
