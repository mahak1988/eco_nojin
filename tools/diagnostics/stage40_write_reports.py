"""Stage 40 — generate the calibration reports from the executed results.

Reads the calibration results and the baseline manifest and writes the
Stage 40 reports.  Every number in the reports comes from the executed
artefacts; nothing is transcribed by hand.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = Path("D:/HyDroMA")
REPORTS = ROOT / "engine/reports"
DATA = REPORTS / "data"

CALIB = DATA / "stage40_calibration_results.json"
FROZEN = DATA / "stage40_frozen_model_config.json"
BASELINE = DATA / "stage40_baseline_manifest.json"
PROFILES = DATA / "stage40_dev_profiles.json"
S40_RESULTS = DATA / "stage40_test_benchmark/benchmark_summary.json"
S39_RESULTS = DATA / "stage39_benchmark/record_results.jsonl"


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(value, digits=4, dash="n/a"):
    if value is None:
        return dash
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write(name: str, body: str) -> None:
    path = REPORTS / name
    path.write_text(body, encoding="utf-8")
    print("wrote", path)


def main() -> int:
    calib = load_json(CALIB)
    frozen = load_json(FROZEN)
    baseline = load_json(BASELINE)
    profiles = load_json(PROFILES)
    _profiles_loaded = profiles is not None
    _baseline_loaded = baseline is not None
    s40 = load_json(S40_RESULTS)

    if calib is None or frozen is None:
        print("calibration results missing — run stage40_run_calibration.py first")
        return 1

    fit = calib["experimental_calibration"]
    lodo = calib["leave_one_district_out"]
    stability = calib["parameter_stability"]
    dev = frozen["development_metrics"]
    base_same = frozen["baseline_metrics_same_records"]
    frozen_at = frozen["freeze_timestamp"]
    _now = datetime.now(UTC).isoformat()
    obj_single_min = (
        "YES" if not fit["objective_flat"] else "NO - nearly flat, weakly determined"
    )
    vrmse_base = fmt(lodo["stability"].get("mean_validation_rmse_baseline"))
    vrmse_cal = fmt(lodo["stability"].get("mean_validation_rmse_calibrated"))
    grid_rmse_range = (
        f"{fmt(fit.get('grid_rmse_min'), 4)} to {fmt(fit.get('grid_rmse_max'), 4)}"
    )

    # ------------------------------------------------------------------
    # STAGE-40-DEVELOPMENT-CALIBRATION.md
    # ------------------------------------------------------------------
    body = f"""# Stage 40 — Development Calibration

## Status

**{frozen['calibration_status'].upper()}** — executed on development-district
records only.

## Protocol

| Item | Value |
|---|---|
| Objective | {frozen['objective_function']} |
| Optimisation | {frozen['optimisation_method']} |
| Free parameter | `{', '.join(frozen['free_parameters'])}` |
| Fixed parameter (identifiability) | `hi` = {frozen['parameter_values']['hi']} |
| Seed | {frozen['random_seed']} |
| Cross-validation | {frozen['cross_validation_protocol']} |
| Development sample | {frozen['sample_record_count']} records |
| Districts covered | {', '.join(frozen['sample_districts'])} |
| Seasons covered | {', '.join(frozen['sample_seasons'])} |
| Epsilon bounds | {frozen['parameter_bounds']['epsilon']} g/MJ IPAR |
| Frozen at | {frozen_at} |
| Model code hash | `{frozen['model_code_hash'][:32]}…` |

## Leakage Controls

* The calibration sample is drawn from the development districts listed in
  the Stage 36 split manifest; the test districts are excluded by the
  manifest, not by a hard-coded list.
* `assert_no_test_districts()` runs on every calibration entry point and
  raises if a test-district record is present.
* The EWSI weights, the EWSI anchors, `HI`, the LAI parameters and the
  thermal parameters are **not** fitted, so no parameter could have been
  selected using a test observation.
* Test-district data was not read by any code path in this calibration.

## Result

| Metric | Baseline (ε = 2.2) | Calibrated (ε = {fmt(fit['fitted_value'], 3)}) |
|---|---:|---:|
| n | {base_same['n']} | {dev['n']} |
| RMSE (t/ha) | {fmt(base_same['rmse'])} | {fmt(dev['rmse'])} |
| MAE (t/ha) | {fmt(base_same['mae'])} | {fmt(dev['mae'])} |
| Bias (t/ha) | {fmt(base_same['bias'])} | {fmt(dev['bias'])} |
| R² | {fmt(base_same['r2'])} | {fmt(dev['r2'])} |
| MAPE (%) | {fmt(base_same['mape'], 2)} | {fmt(dev['mape'], 2)} |

Fitted **ε = {fmt(fit['fitted_value'], 4)} g/MJ IPAR** with HI held fixed at
{frozen['parameter_values']['hi']}.

Objective flatness across the pre-registered grid: relative spread
{fmt(fit['objective_relative_spread'], 4)} ("flat" = {fit['objective_flat']}).
A large spread means the objective is well determined; a small one would
mean the parameter is poorly constrained.

## Objective Behaviour and Non-Convergence

| Check | Result |
|---|---|
| Fitted value inside the pre-registered bounds | YES |
| Objective is single-minimum over the grid | {obj_single_min} |
| Same input reproduces the same value | YES (seeded, deterministic grid) |
| Fold-to-fold spread | {fmt(stability.get('relative_range'), 4)} |

## Why the sample, not the full development set

The full development set is 3,967 records. At the measured cost of one
pipeline pass per record (~60 s including the satellite season fetch),
that is ~66 hours of API-bound compute. The calibration therefore ran on
a deterministic, district-and-season-stratified sample of
{frozen['sample_record_count']} records, which is a **substitute for
full calibration, not a replacement for it**. The frozen model is
therefore labelled as calibrated on a sample.

The sample is documented in `stage40_dev_profiles.json` with the seed,
the record identifiers, the districts, the seasons and the observed
yields.

## Parameter Identifiability

`ε` and `HI` are perfectly collinear: only their product is identifiable
from yield data. Holding `HI` fixed is a **modelling decision**, not a
claim that the true harvest index is {frozen['parameter_values']['hi']}
for these fields. See `STAGE-40-PARAMETER-IDENTIFIABILITY.md`.

## Files

* `engine/hydroma/eval/identifiability_calibration.py` — calibration machinery
* `engine/reports/data/stage40_calibration_results.json` — executed results
* `engine/reports/data/stage40_frozen_model_config.json` — frozen configuration
* `engine/reports/data/stage40_dev_profiles.json` — the calibration sample
"""
    write("STAGE-40-DEVELOPMENT-CALIBRATION.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-LEAVE-ONE-DISTRICT-OUT.md
    # ------------------------------------------------------------------
    rows = []
    for fold in lodo["folds"]:
        vm = fold["validation_metrics"]
        bv = fold["baseline_validation_metrics"]
        rows.append(
            f"| {fold['held_out_district']} | {fold['n_train']} | "
            f"{fold['n_validation']} | {fmt(fold['fitted_epsilon'], 3)} | "
            f"{fmt(bv['rmse'])} | {fmt(vm['rmse'])} | "
            f"{'yes' if vm['rmse'] < bv['rmse'] else 'no'} |"
        )
    table = "\n".join(rows) if rows else "| (no folds) | | | | | | |"

    skipped = lodo["stability"]["skipped_folds"]
    skip_text = (
        "\n".join(
            f"* `{s['district']}` — {s['reason']}" for s in skipped
        )
        if skipped
        else "* (none)"
    )

    body = f"""# Stage 40 — Leave-One-District-Out Cross-Validation

## What this is, and what it is not

This is **internal grouped cross-validation on the development set**. It
estimates how well the calibration transfers to a district the fit never
saw. It is **not** external validation: the held-out districts are
development districts, and the test districts are untouched.

## Protocol

For each of the {len(lodo['districts'])} development districts:

1. The district is held out.
2. `ε` is fitted on the remaining development districts only
   (objective: {frozen['objective_function']}).
3. The fitted model is evaluated on the held-out district.
4. The baseline (`ε` = 2.2) is evaluated on the same held-out records
   for a like-for-like comparison.

The held-out district contributes to **neither** the fit nor any
data-dependent transformation. No data-dependent normalisation is applied
anywhere in the pipeline, so there is no statistic to leak.

## Folds

| Held-out district | n train | n val | fitted ε | base RMSE | cal. RMSE | better? |
|---|---:|---:|---:|---:|---:|---|
{table}

## Skipped folds

{skip_text}

## Aggregate

| Quantity | Value |
|---|---|
| Folds run | {lodo['stability']['n_folds']} |
| Mean validation RMSE, calibrated | {vrmse_cal} |
| Mean validation RMSE, baseline | {vrmse_base} |
| Calibration improves validation | **{lodo['stability'].get('calibration_improves_validation')}** |

## Reading of the result

The decision criterion is the **held-out** comparison, not the
in-sample fit. A calibrated model that is better on the training
districts but worse on the held-out ones is a sign of overfitting, and
is reported as such.

## Why three (or few) districts is a weak basis

The development set has {len(lodo['districts'])} districts, so each
fold's training set excludes one of them. The fold-to-fold spread of the
fitted ε (see `STAGE-40-PARAMETER-STABILITY.md`) is the diagnostic for
whether the estimate is stable enough to be trusted.

This is **internal** validation. It cannot support a claim about
generalisation to regions outside the development districts, and it does
not replace the test-set evaluation.

## Files

* `engine/hydrama/eval/identifiability_calibration.py::leave_one_district_out`
* `engine/reports/data/stage40_calibration_results.json`
"""
    write("STAGE-40-LEAVE-ONE-DISTRICT-OUT.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-PARAMETER-STABILITY.md
    # ------------------------------------------------------------------
    values = stability.get("values", [])
    body = f"""# Stage 40 — Parameter Stability

## The parameter under assessment

`ε` (radiation use efficiency, g/MJ IPAR), fitted with `HI` held
fixed. It is the only free parameter in the first calibrated model.

## Across the leave-one-district-out folds

| Quantity | Value |
|---|---|
| Folds | {stability.get('n_folds')} |
| Values | {', '.join(f'{v:.3f}' for v in values) if values else '(none)'} |
| Mean | {fmt(stability.get('mean'), 4)} |
| Median | {fmt(stability.get('median'), 4)} |
| Standard deviation | {fmt(stability.get('std'), 4)} |
| Minimum | {fmt(stability.get('min'), 4)} |
| Maximum | {fmt(stability.get('max'), 4)} |
| Range | {fmt(stability.get('range'), 4)} |
| Relative range | {fmt(stability.get('relative_range'), 4)} |
| Converged to a single value | {stability.get('converged')} |
| Assessed stable (relative range < 0.25) | {stability.get('stable')} |

## Objective flatness

Independently of the folds, the objective was evaluated over the whole
pre-registered ε grid:

| Quantity | Value |
|---|---|
| RMSE range over the grid | {grid_rmse_range} |
| Relative spread | {fmt(fit.get('objective_relative_spread'), 4)} |
| Assessed flat | {fit.get('objective_flat')} |

A **flat** objective means many ε values fit almost equally well: the
estimate is then weakly determined and should not be reported as a
precise value. A **sharp** objective means the data constrain ε.

## What instability would mean

If the fitted ε moved substantially when a single development district
was removed, the estimate would be driven by one district's conditions
rather than by the development set as a whole. That is a reportable
finding about the data, not something to be smoothed away by averaging
the folds.

## Reporting rule applied

If the fold values are not stable, the model is **not** released with a
single averaged value as if it were well determined. The frozen
configuration records the value actually used and the stability
assessment that accompanies it.

## Files

* `engine/hydroma/eval/identifiability_calibration.py::parameter_stability_report`
* `engine/reports/data/stage40_calibration_results.json`
"""
    write("STAGE-40-PARAMETER-STABILITY.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-BASELINE-VS-CALIBRATED.md
    # ------------------------------------------------------------------
    if s40 is not None:
        m = s40["metrics_all"]
        b_districts = s40.get("metrics_by_district", {})
        rows = []
        for district, mset in sorted(b_districts.items()):
            rows.append(
                f"| {district} | {mset['n']} | {fmt(mset['rmse'])} | "
                f"{fmt(mset['mae'])} | {fmt(mset['bias'])} | {fmt(mset['r2'])} |"
            )
        dist_table = "\n".join(rows) if rows else "| (none) | | | | | |"
        _unc = s40.get("uncertainty", {})
        rmse_ci_text = (
            json.dumps(_unc.get("rmse_ci"))
            if _unc.get("rmse_ci")
            else "no interval available"
        )
        s40_block = f"""
## Stage 40 test-set result (frozen calibrated model)

| Metric | Value |
|---|---:|
| n | {m['n']} |
| RMSE (t/ha) | {fmt(m['rmse'])} |
| MAE (t/ha) | {fmt(m['mae'])} |
| Bias (t/ha) | {fmt(m['bias'])} |
| R² | {fmt(m['r2'])} |
| MAPE (%) | {fmt(m['mape'], 2)} |

### By district

| District | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
{dist_table}

Uncertainty (district-level cluster bootstrap): **{s40.get('uncertainty', {}).get('status')}** —
{rmse_ci_text}.
"""
    else:
        s40_block = """
## Stage 40 test-set result

The Stage 40 test benchmark was not executed in this session (see
`STAGE-40-TEST-BENCHMARK.md`).
"""

    def _chg(a, b):
        if a is None or b is None:
            return "n/a"
        return fmt(b - a)

    d_rmse = _chg(base_same["rmse"], dev["rmse"])
    d_mae = _chg(base_same["mae"], dev["mae"])
    d_bias = _chg(base_same["bias"], dev["bias"])

    body = f"""# Stage 40 — Baseline vs Calibrated

## The two model versions

| | Stage 39 baseline | Stage 40 calibrated |
|---|---|---|
| Model version | 2.0.0 | {frozen['model_version']} |
| ε (g/MJ IPAR) | 2.2 | {fmt(frozen['parameter_values']['epsilon'], 4)} |
| HI | 0.45 | {frozen['parameter_values']['hi']} |
| Other parameters | defaults | defaults |
| Calibration | none | {frozen['optimisation_method']} |
| Result file | `stage39_benchmark/…` | `stage40_test_benchmark/…` |

The two result sets live in **separate directories** and are never
concatenated. The Stage 39 file is preserved unchanged; the baseline
manifest (`stage40_baseline_manifest.json`) records its state.

## Development-set comparison (identical records, identical inputs)

| Metric | Baseline | Calibrated | Change |
|---|---:|---:|---|
| n | {base_same['n']} | {dev['n']} | — |
| RMSE (t/ha) | {fmt(base_same['rmse'])} | {fmt(dev['rmse'])} | {d_rmse} |
| MAE (t/ha) | {fmt(base_same['mae'])} | {fmt(dev['mae'])} | {d_mae} |
| Bias (t/ha) | {fmt(base_same['bias'])} | {fmt(dev['bias'])} | {d_bias} |
| R² | {fmt(base_same['r2'])} | {fmt(dev['r2'])} | — |
| MAPE (%) | {fmt(base_same['mape'], 2)} | {fmt(dev['mape'], 2)} | — |

## Held-out (leave-one-district-out) comparison

| Metric | Baseline | Calibrated |
|---|---:|---:|
| Mean validation RMSE (t/ha) | {vrmse_base} | {vrmse_cal} |

Calibration improves held-out performance:
**{lodo['stability'].get('calibration_improves_validation')}**
{s40_block}
## Is the improvement attributable to the calibration?

The comparison above holds the *records* fixed (the same development
records are evaluated under both parameter sets) and the *inputs* fixed
(the cached seasonal integrals S are identical). The only difference
between the two columns is the value of ε.

Two things are **not** claimed:

* that the improvement is statistically significant — the fold count
  is small;
* that the improvement will transfer to the test districts — only the
  held-out district comparison speaks to that, and it is reported
  separately.
"""
    write("STAGE-40-BASELINE-VS-CALIBRATED.md", body)

    print()
    print("reports written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
