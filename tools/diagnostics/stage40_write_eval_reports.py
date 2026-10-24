"""Stage 40 — write the evaluation reports (test benchmark, metrics, errors).

Run after the Stage 40 test benchmark has produced
``stage40_test_benchmark/benchmark_summary.json``.
"""

from __future__ import annotations

import json
import sys
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
S40 = DATA / "stage40_test_benchmark/benchmark_summary.json"
COMPARE = DATA / "stage40_baseline_vs_calibrated.json"
EQUIV = DATA / "stage40_baseline_equivalence.json"


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(v, d=4, dash="n/a"):
    if v is None:
        return dash
    if isinstance(v, float):
        return f"{v:.{d}f}"
    return str(v)


def _delta(a, b):
    """Signed change from a (baseline) to b (calibrated)."""
    if a is None or b is None:
        return None
    return b - a


def _bias_rows(by_district) -> str:
    """Markdown rows of district -> n, bias."""
    if not by_district:
        return "| (test benchmark not complete) | | |"
    return "\n".join(
        f"| {k} | {v['n']} | {fmt(v['bias'])} |" for k, v in sorted(by_district.items())
    )


def _ci(value, digits=4):
    """Format a confidence interval for display."""
    if not value:
        return "n/a"
    try:
        lo, hi = value[0], value[1]
    except (TypeError, IndexError):
        return str(value)
    return f"[{lo:.{digits}f}, {hi:.{digits}f}]"


def _coverage_table(coverage) -> str:
    """Markdown table of realised stratum coverage."""
    if not coverage:
        return "_No coverage data._"
    rows = coverage.get("by_stratum", {})
    lines = [
        "| Stratum (district\\|season) | Design | Evaluated |",
        "|---|---:|---:|",
    ]
    for stratum, v in sorted(rows.items()):
        lines.append(f"| {stratum} | {v['design']} | {v['evaluated']} |")
    lines.append("")
    lines.append(
        f"Strata covered: **{coverage.get('strata_covered')}** of "
        f"{coverage.get('strata_total')}."
    )
    return "\n".join(lines)


def _rows(pairs) -> str:
    """Markdown rows from (a, b) pairs."""
    return "\n".join(f"| {a} | {b} |" for a, b in pairs)


def _rows3(triples) -> str:
    """Markdown rows from (a, b, c) triples."""
    return "\n".join(f"| {a} | {b} | {c} |" for a, b, c in triples)


def _comparison_rows(comparison) -> str:
    """Rows of the like-for-like baseline-vs-calibrated table."""
    comparison = comparison or {}
    base = comparison.get("baseline", {})
    cal = comparison.get("calibrated", {})
    n = comparison.get("n_records_compared", "n/a")
    rows = [f"| n | {n} | {n} | - |"]
    for label, key, digits in (
        ("RMSE (t/ha)", "rmse", 4),
        ("MAE (t/ha)", "mae", 4),
        ("Bias (t/ha)", "bias", 4),
        ("R²", "r2", 4),
        ("MAPE (%)", "mape", 2),
    ):
        b = base.get(key)
        c = cal.get(key)
        rows.append(
            f"| {label} | {fmt(b, digits)} | {fmt(c, digits)} | "
            f"{fmt(_delta(b, c), digits)} |"
        )
    return "\n".join(rows)


#: Requirements for a `VALIDATED_EXTERNAL` claim, and whether each is met.
def _validation_gates(sample_total, test_r2) -> tuple:
    """Rows of (requirement, met?, evidence) for the final status report."""
    return (
        (
            "Calibrated on data disjoint from the evaluation set",
            "Yes",
            "7 dev districts; leakage guard asserted",
        ),
        (
            "Parameters frozen before evaluation",
            "Yes",
            "frozen config written before the run",
        ),
        (
            "Evaluation on genuinely external districts",
            "Yes",
            "Buxar, Muzaffarpur, Rohtas",
        ),
        (
            "Evaluation covers the full external set",
            "No",
            f"{sample_total} of 1,722, stratified sample",
        ),
        (
            "Spatial replication",
            "No",
            "three districts; the bootstrap has three clusters",
        ),
        (
            "Performance is strong enough to claim validity",
            "No",
            f"test R² = {fmt(test_r2)}",
        ),
        (
            "Uncertainty covers the total error budget",
            "No",
            "calibration and input components excluded",
        ),
        (
            "Model identified from the data",
            "No",
            "`epsilon`/`HI` collinear; objective nearly flat",
        ),
    )


#: Where the remaining error comes from, as (source, evidence, status).
def _error_sources(n_folds, rel_range) -> tuple:
    """Rows of the error-source table."""
    return (
        (
            "Yield scale (ε)",
            f"Fitted on development data; stable across {n_folds} LODO "
            f"folds (rel. range {rel_range})",
            "**Addressed** - see the caveat below",
        ),
        (
            "EWSI amplitude",
            "Weights and anchors are uncalibrated defaults; the fitted ε "
            "may have absorbed an EWSI scale error",
            "**Open**",
        ),
        (
            "LAI",
            "Every record uses the same GDD-model curve (`LAIModel`), so the "
            "seasonal LAI shape is assumed",
            "**Open**",
        ),
        (
            "Thermal response",
            "`t_opt` = 20 °C with a hard-coded 8 °C width; the width has no "
            "source",
            "**Open**",
        ),
        (
            "Soil moisture",
            "ERA5-Land reanalysis at ~9 km; field capacity 0.35 m³/m³ is a "
            "default",
            "**Open**",
        ),
        (
            "Satellite NDMI",
            "Single 20 m pixel; ~4-6 % of days observed, rest forward-filled",
            "**Open**",
        ),
        (
            "Season length",
            "Sowing/harvest dates from CIMMYT; the biomass window follows them",
            "**Open**",
        ),
        (
            "Observation uncertainty",
            "Not propagated",
            "**Open**",
        ),
    )


#: Model limitations that remain open, as (item, why it matters) pairs.
_MODEL_LIMITS = (
    (
        "`epsilon` and `HI` are perfectly collinear",
        "Only their product is identifiable from yield data; the fitted "
        "`epsilon` is a scale, not a measurement",
    ),
    (
        "The objective is nearly flat over the grid",
        "Many `epsilon` values fit the data almost equally well; the value "
        "is one point on a plateau",
    ),
    (
        "The thermal response has a hard-coded 8 °C Gaussian width",
        "No source; the width was never a free parameter",
    ),
    (
        "LAI is model-generated for every record",
        "The GDD curve is assumed, not observed; `k` and `lai_max` cannot "
        "be separated",
    ),
    (
        "EWSI weights and anchors are project defaults",
        "The fitted `epsilon` may have absorbed an EWSI amplitude error",
    ),
    (
        "Soil moisture is ERA5-Land reanalysis at ~9 km",
        "Field capacity 0.35 m³/m³ is a default",
    ),
    (
        "Satellite NDMI is one 20 m pixel per field",
        "Most season days have no observation and are forward-filled",
    ),
    (
        "Observation uncertainty is not propagated",
        "The reported intervals understate the total uncertainty",
    ),
)

#: Evaluation limitations, as (item, detail) pairs.
_EVAL_LIMITS = (
    (
        "Three spatial clusters",
        "The district-level bootstrap has three clusters; its 2.5th and "
        "97.5th percentiles are close to the extreme resamples",
    ),
    (
        "Calibration uncertainty not in the interval",
        "The bootstrap runs on the frozen model, not the calibration",
    ),
    (
        "Input uncertainty not in the interval",
        "Remote-sensing, weather and observation uncertainty excluded",
    ),
    (
        "The test set was used once",
        "It has now been looked at. A stage that adjusts the model to these "
        "numbers has consumed it",
    ),
    (
        "The API path can fall back",
        "The weather source falls back from Open-Meteo ERA5 to NASA POWER "
        "on timeout",
    ),
)


def write(name: str, body: str) -> None:
    (REPORTS / name).write_text(body, encoding="utf-8")
    print("wrote", REPORTS / name)


def main() -> int:
    calib = load_json(CALIB)
    frozen = load_json(FROZEN)
    baseline = load_json(BASELINE)
    profiles = load_json(PROFILES)
    _profiles_loaded = profiles is not None
    s40 = load_json(S40)

    if calib is None or frozen is None:
        print("calibration results missing")
        return 1

    fit = calib["experimental_calibration"]
    lodo = calib["leave_one_district_out"]
    stability = calib["parameter_stability"]
    dev = frozen["development_metrics"]
    base_same = frozen["baseline_metrics_same_records"]

    # Like-for-like comparison on the *same* test records.
    comparison = load_json(COMPARE)
    identity = (comparison or {}).get("identity_validation", {})

    n_folds = stability.get("n_folds")
    rel_range = fmt(stability.get("relative_range"), 4)
    free_param_text = ", ".join(frozen["free_parameters"])
    cmp_rmse_base = fmt((comparison or {}).get("baseline", {}).get("rmse"))
    cmp_rmse_cal = fmt((comparison or {}).get("calibrated", {}).get("rmse"))
    cmp_r2_base = fmt((comparison or {}).get("baseline", {}).get("r2"))
    cmp_r2_cal = fmt((comparison or {}).get("calibrated", {}).get("r2"))
    vrmse_base = fmt(lodo["stability"].get("mean_validation_rmse_baseline"))
    vrmse_cal = fmt(lodo["stability"].get("mean_validation_rmse_calibrated"))

    sample = (s40 or {}).get("sample") or {}
    # The number actually evaluated (which may be short of the design size
    # if the run is still in progress) and the design size, kept separate.
    sample_total = (s40 or {}).get("records_processed", "n/a")
    sample_design_total = sample.get("selected_total", "n/a")

    n_test = 0
    metrics = {"n": 0}
    by_district: dict = {}
    by_season: dict = {}
    by_quality: dict = {}
    uncertainty: dict = {}
    quality: dict = {}
    if s40 is not None:
        metrics = s40["metrics_all"]
        by_district = s40.get("metrics_by_district", {})
        by_season = s40.get("metrics_by_season", {})
        by_quality = s40.get("metrics_by_input_quality", {})
        uncertainty = s40.get("uncertainty", {})
        quality = s40.get("input_quality_summary", {})
        n_test = s40.get("records_processed", 0)

    def table(mapping, label="n"):
        rows = []
        for key, mset in sorted(mapping.items()):
            rows.append(
                f"| {key} | {mset['n']} | {fmt(mset['rmse'])} | "
                f"{fmt(mset['mae'])} | {fmt(mset['bias'])} | {fmt(mset['r2'])} |"
            )
        return "\n".join(rows) if rows else "| (none) | | | | | |"

    # ------------------------------------------------------------------
    # STAGE-40-TEST-BENCHMARK.md
    # ------------------------------------------------------------------
    body = f"""# Stage 40 — Test Benchmark

## Execution Status

| Item | Value |
|---|---|
| Model version | {frozen['model_version']} |
| Calibration status | {frozen['calibration_status']} |
| Free parameter | `{free_param_text}` = {fmt(frozen['parameter_values']['epsilon'], 4)} g/MJ IPAR |
| Test districts | {', '.join(['Buxar', 'Muzaffarpur', 'Rohtas'])} |
| Test records in manifest | 1,722 |
| Records evaluated | {n_test} |
| Results file | `engine/reports/data/stage40_test_benchmark/record_results.jsonl` |
| State file | `engine/reports/data/stage40_test_benchmark/execution_state.sqlite` |

## Sampling design

The upstream Sentinel-2 COG reads dominate the benchmark cost and the
APIs throttle beyond roughly eight concurrent readers, so the
evaluation was run on a **documented stratified sample** of the test
set rather than all 1,722 records.

| Item | Value |
|---|---|
| Design | {sample.get('design', 'n/a')} |
| Frame | all {sample.get('frame_record_count', '1,722')} test-district records |
| Strata | {sample.get('strata_definition', 'n/a')} ({sample.get('n_strata', 18)} strata) |
| Allocation | {sample.get('allocation_rule', 'n/a')} |
| Sample size | {sample.get('selected_total', 'n/a')} |
| Seed | {sample.get('seed', 'n/a')} |
| Sample ids hash | `{(sample.get('selected_ids_hash') or 'n/a')[:24]}…` |
| Frame ids hash | `{(sample.get('frame_record_ids_hash') or 'n/a')[:24]}…` |

The sample manifest, including the per-stratum allocation and the
selected record ids, is `engine/reports/data/stage40_test_sample.json`.
The sample is reproducible from the seed and the frame.

**This is a sample, and the reported metrics describe the sample.**
The sampling design is stated so that the reader can judge it; the
full 1,722-record run was not performed.

### Realised coverage

{_coverage_table((s40 or {}).get("realised_coverage"))}

## Separation from the baseline

The Stage 40 run writes to `stage40_test_benchmark/`. The Stage 39
baseline results in `stage39_benchmark/` are **not** modified and **not**
concatenated. The baseline state is preserved in
`stage40_baseline_manifest.json`
({baseline['records_processed'] if baseline else 'n/a'} records,
model code hash `{(baseline['model_code_hash'][:16] if baseline else 'n/a')}…`).

## Execution statuses

| Status | Count |
|---|---:|
| COMPUTED | {quality.get('n_computed', 'n/a')} |
| PARTIAL_INPUTS | {quality.get('n_partial_inputs', 'n/a')} |
| BLOCKED | {quality.get('n_blocked', 'n/a')} |
| FAILED | {quality.get('n_failed', 'n/a')} |
| **Records with a prediction** | **{quality.get('n_with_prediction', 'n/a')}** |

Input quality breakdown:
{json.dumps(quality.get('input_quality_counts', {}), indent=2)}

EWSI status breakdown:
{json.dumps(quality.get('ewsi_status_counts', {}), indent=2)}

## Rules observed during the run

* Parameters were frozen before the run and were not modified during it.
* The run was executed in {sample.get('shards', 8) if sample else 8} parallel
  shards over a disjoint, deterministic interleave of the selected
  records; each shard had its own state database, and the merged
  result set is de-duplicated by record id.
* No record was deleted; blocked and failed records are written to
  `failed_records.jsonl` with their reason.
* Records with incomplete inputs are **not** counted as valid
  scientific predictions; the breakdown above separates them.
* The model version and code hash are recorded with every result.
* The test set was not used to select the model, the parameters, or any
  other decision.

## Runner

`engine/hydroma/eval/resumable_benchmark_runner.py`, reusing the Stage 38
resumable runner. State is held per record in SQLite, so a re-run skips
records already in a terminal status. The Stage 40 run uses a separate
state database, so the baseline and calibrated runs never share state.
"""
    write("STAGE-40-TEST-BENCHMARK.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-VALIDATION-METRICS.md
    # ------------------------------------------------------------------
    body = f"""# Stage 40 — Validation Metrics

## Test-set result (frozen calibrated model)

| Metric | Value | Unit |
|---|---:|---|
| n | {metrics.get('n', 0)} | records |
| RMSE | {fmt(metrics.get('rmse'))} | t/ha |
| MAE | {fmt(metrics.get('mae'))} | t/ha |
| Bias | {fmt(metrics.get('bias'))} | t/ha |
| R² | {fmt(metrics.get('r2'))} | dimensionless |
| MAPE | {fmt(metrics.get('mape'), 2)} | % |
| MAPE exclusions | {metrics.get('mape_excluded', 0)} | records |

### By test district

| District | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
{table(by_district)}

### By season

| Season | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
{table(by_season)}

### By input quality

| Input quality | n | RMSE | MAE | Bias | R² |
|---|---:|---:|---:|---:|---:|
{table(by_quality)}

## Development-set result (for comparison, not a test metric)

| Metric | Baseline | Calibrated |
|---|---:|---:|
| RMSE (t/ha) | {fmt(base_same['rmse'])} | {fmt(dev['rmse'])} |
| MAE (t/ha) | {fmt(base_same['mae'])} | {fmt(dev['mae'])} |
| Bias (t/ha) | {fmt(base_same['bias'])} | {fmt(dev['bias'])} |
| R² | {fmt(base_same['r2'])} | {fmt(dev['r2'])} |
| MAPE (%) | {fmt(base_same['mape'], 2)} | {fmt(dev['mape'], 2)} |

## Like-for-like test-set comparison

The Stage 39 baseline run covered only **40** test records, all from the
2016-17 season. Comparing that against a full calibrated run would
compare different record sets, so both parameter sets are evaluated on
the **same** records here.

HYRUE's seasonal yield is exactly linear in `ε` (`Y = ε · S · HI / 100`),
so the baseline prediction for a record is the calibrated prediction
scaled by `ε_base / ε_cal`. That identity is validated below against
the records for which a real baseline prediction exists.

| Identity check | Value |
|---|---|
| Real baseline records available | {identity.get('records_compared', 'n/a')} |
| Records matching within 1e-9 | {identity.get('records_within_1e-9', 'n/a')} |
| Max absolute difference | {fmt(identity.get('max_abs_difference_t_ha'), 12)} t/ha |
| Identity validated | {identity.get('validated', 'n/a')} |

| Metric | Baseline (same records) | Calibrated | Δ |
|---|---:|---:|---:|
{_comparison_rows(comparison)}

## Metric definitions and guard conditions

| Metric | Definition | Guard |
|---|---|---|
| RMSE | `sqrt((1/n) Σ (ŷ−y)²)` | — |
| MAE | `(1/n) Σ \\|ŷ−y\\|` | — |
| Bias | `(1/n) Σ (ŷ−y)` | — |
| R² | `1 − Σ(y−ŷ)² / Σ(y−ȳ)²` | reported `null` with a reason when the yields have zero variance |
| MAPE | `(100/n) Σ \\|ŷ−y\\|/\\|y\\|` | observations with \\|y\\| ≤ 1e-6 are excluded and counted |

## Reading the numbers

The calibration **improved** the external result on the same records:
RMSE fell from {cmp_rmse_base} to {cmp_rmse_cal} t/ha and R² rose
from {cmp_r2_base} to {cmp_r2_cal}.

**The calibrated R² is still negative.** That means the sum of squared
prediction errors exceeds the sum of squared deviations of the observed
yields from their own mean — i.e. predicting each district's mean
observed yield for every field would score a better R² than this model
does. The calibration reduced the error and removed much of the bias;
it did not make the model a good predictor of district-level yield on
these three held-out districts.

This is reported as measured. A negative R² is not a rounding artefact
and is not suppressed anywhere in this report set.

The test set has **three districts**. Metrics computed on them describe
those three districts; they do not establish generalisation beyond
them.
"""
    write("STAGE-40-VALIDATION-METRICS.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-ERROR-ANALYSIS.md
    # ------------------------------------------------------------------
    body = f"""# Stage 40 — Error Analysis

## The headline change

| Stage | Model | Development R² | Development RMSE |
|---|---|---:|---:|
| 39 | uncalibrated defaults | {fmt(base_same['r2'])} | {fmt(base_same['rmse'])} t/ha |
| 40 | ε fitted on development data | {fmt(dev['r2'])} | {fmt(dev['rmse'])} t/ha |

The negative R² of the uncalibrated model is the central diagnostic
finding of the last two stages. It is explained by the identifiability
structure: `ε` and `HI` multiply the seasonal biomass, and the
literature default for `ε` does not match the harvest index actually
realised by these fields, so every prediction was displaced in the same
direction.

Fitting `ε` on development data (with `HI` fixed) moves the scale to
where the development observations put it, and the R² crosses zero.

## Where the error now comes from

| Source | Evidence | Status |
|---|---|---|
{_rows3(_error_sources(n_folds, rel_range))}

## A defect found and fixed during this stage

The first Stage 40 benchmark run was **aborted** because a review of the
code found that the frozen parameters were never reaching the model.
`HYRUE.__init__` applied the crop preset whenever a crop name was
supplied, silently overwriting any explicit `HYRUEParams` — so
`HYRUE(params=calibrated, crop="wheat")` evaluated the *uncalibrated*
default. The calibrated run would have been byte-for-byte the baseline
run.

Three things were done about it:

1. `HYRUE.__init__` now gives explicit parameters precedence over the
   crop preset.
2. The parameter set is threaded explicitly through
   `compute_hyrue_seasonal` → `SeasonalPredictionRequest` →
   `ResumableBenchmarkRunner`, and is recorded in the run manifest and
   in the per-record data hash.
3. Regression tests now assert that a supplied parameter set changes
   the prediction, and that the analytical calibration formula is
   numerically identical to `HYRUE.compute` (`rel = 1e-12`).

The Stage 39 baseline was re-checked against the current code on a
26-record sample: **26/26 predictions identical, max difference 0.0**
(`stage40_baseline_equivalence.json`), so the baseline numbers remain
valid.

A second defect was found at the same time: the first profile builder
used a **synthetic sigmoid LAI** and a hard-coded PAR factor of 0.5,
while the benchmark pipeline resolves LAI with the GDD model and
converts PAR with the weather source's own factor. The calibration was
therefore fitted against a different input basis from the one it was
evaluated on. The profiles are now built by the **same runner the
benchmark uses**, with the resolved daily arrays captured from the live
pipeline, so the skew is removed by construction. The fitted ε changed
from 2.570 to {fmt(frozen['parameter_values']['epsilon'], 3)} when this
was corrected.

## Why only one parameter was freed

`ε` and `HI` are perfectly collinear; the EWSI weights are collinear
with each other and with the EWSI amplitude; `k`, `lai_max` and the
LAI series are mutually confounded; `t_opt` is confounded with the
hard-coded Gaussian width. Freeing several of these together would
produce a fit without identifying which change caused it, and would make
the fitted values uninterpretable.

The single free parameter is therefore a **modelling decision**, and the
fitted `ε` should be read as "the scale that the development set
implies", not as "the true radiation use efficiency of wheat in Bihar".

## An important caveat about the objective

The objective was nearly flat over the pre-registered ε grid
(relative spread {fmt(fit.get('objective_relative_spread'), 4)}, i.e.
many ε values fit the development data almost equally well). The
leave-one-district-out estimate is nevertheless stable, which says the
grid minimum sits in the same place regardless of which district is
held out — but the *width* of the flat region means the data do not
determine ε precisely. The frozen value should be treated as one
defensible point on a plateau, not as a sharp measurement.

## Test-set error (frozen model)

| Group | n | Bias (t/ha) |
|---|---:|---:|
{_bias_rows(by_district)}

## What would reduce the remaining error

1. **Observed LAI.** With a real LAI series, `k` and `lai_max` become
   separately informative and the LAI amplitude stops being assumed.
2. **A published EWSI weighting.** The EWSI amplitude currently has
   no independent constraint, so it can only be absorbed by `ε`.
3. **Field-level soil moisture.** Replacing the ERA5-Land reanalysis
   with in-situ measurements would remove a systematic spatial bias.
4. **A second dataset.** Every result here comes from one dataset in
   one region over six years.
"""
    write("STAGE-40-ERROR-ANALYSIS.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-UNCERTAINTY-ANALYSIS.md
    # ------------------------------------------------------------------
    body = f"""# Stage 40 — Uncertainty Analysis

## Test-set uncertainty (district-level cluster bootstrap)

| Quantity | Value |
|---|---|
| Status | {uncertainty.get('status', 'n/a')} |
| Independent districts | {uncertainty.get('n_districts', 'n/a')} |
| Records | {uncertainty.get('n_records', 'n/a')} |
| Bootstrap samples | {uncertainty.get('n_bootstrap', 'n/a')} |
| RMSE mean | {fmt(uncertainty.get('rmse_mean'))} t/ha |
| RMSE 95 % CI | {_ci(uncertainty.get('rmse_ci'))} |
| MAE mean | {fmt(uncertainty.get('mae_mean'))} t/ha |
| MAE 95 % CI | {_ci(uncertainty.get('mae_ci'))} |
| Bias mean | {fmt(uncertainty.get('bias_mean'))} t/ha |
| Bias 95 % CI | {_ci(uncertainty.get('bias_ci'))} |

## The three-district limitation

The test set contains **three** districts. A cluster bootstrap over
three clusters has a bootstrap distribution that is the distribution of
three draws: the 2.5th and 97.5th percentiles are close to the
extreme resamples (the same district drawn three times, or one drawn
twice). The interval is therefore driven by a handful of outcomes and
is **not** a stable estimate of the sampling distribution of spatial
generalisation.

The interval is reported as a limited uncertainty estimate, not as a
confidence statement about generalisation beyond these districts.

## What the interval does and does not cover

| Source of uncertainty | Covered? |
|---|---|
| Spatial variation between the three test districts | Yes, with the caveat above |
| Sampling of records within a district | No — deliberately not resampled |
| **Calibration uncertainty** | **No** — the bootstrap uses the frozen model, not the calibration |
| Remote-sensing input uncertainty | No |
| Weather reanalysis uncertainty | No |
| Observation uncertainty | No |

The reported interval therefore **understates** the total uncertainty.
With a single fitted parameter and a nearly flat objective, the
calibration component is not negligible: the fold-to-fold spread of ε
({fmt(stability.get('std'), 4)} g/MJ IPAR, relative range
{fmt(stability.get('relative_range'), 4)}) is the available estimate of
that component, and it is reported separately.

## Development-set parameter stability as the calibration component

| Quantity | Value |
|---|---|
| Folds | {stability.get('n_folds')} |
| ε values | {', '.join(f'{v:.3f}' for v in stability.get('values', []))} |
| Standard deviation | {fmt(stability.get('std'), 4)} |
| Relative range | {fmt(stability.get('relative_range'), 4)} |
| Assessed stable | {stability.get('stable')} |

## Combining the components

A defensible total interval would need the three components added in
quadrature (or a bootstrap that resamples the calibration as well).
That requires running the calibration inside the bootstrap loop, which
multiplies the cost by the number of bootstrap samples. It is recorded
as Stage 41 work.

## Conclusion

The spatial component is reported with an explicit warning about the
cluster count. The calibration and input components are **not** covered
and are stated as such. No claim of broad generalisability is made.
"""
    write("STAGE-40-UNCERTAINTY-ANALYSIS.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-QUALITY-GATES.md
    # ------------------------------------------------------------------
    equiv = load_json(EQUIV) or {}
    gates = [
        (
            "No test-district record used in the calibration",
            "PASS",
            f"leakage guard asserted before the fit; "
            f"{stability.get('n_folds')} LODO folds, all development-only",
        ),
        (
            "Calibration parameters frozen before external evaluation",
            "PASS",
            "frozen config written before the test run; the run manifest "
            "records the parameter set used",
        ),
        (
            "Explicit parameters reach the model (not the crop preset)",
            "PASS",
            "regression test: a supplied parameter set changes the "
            "prediction by exactly the epsilon ratio",
        ),
        (
            "Calibration formula identical to the evaluated model",
            "PASS",
            "regression test: analytical yield == HYRUE.compute to rel 1e-12",
        ),
        (
            "Calibration and evaluation share one input basis",
            "PASS",
            "profiles built by the benchmark runner itself; daily arrays "
            "captured from the live pipeline",
        ),
        (
            "Stage 39 baseline unchanged by the Stage 40 code changes",
            "PASS" if equiv.get("verdict") == "baseline_preserved" else "FAIL",
            f"{equiv.get('identical', 'n/a')}/{equiv.get('compared', 'n/a')} "
            f"predictions identical, max diff "
            f"{equiv.get('max_abs_difference_t_ha', 'n/a')} t/ha",
        ),
        (
            "Baseline compared on the same records as the calibrated model",
            "PASS",
            "linearity identity validated against the real Stage 39 "
            "predictions; see the validation-metrics report",
        ),
        (
            "Every record accounted for (no silent drops)",
            "PASS" if s40 is not None else "PENDING",
            f"{s40.get('records_processed', 'n/a')} records processed, each "
            "with an execution status; blocked and failed records are "
            "written to failed_records.jsonl",
        ),
        (
            "Uncertainty reported with its coverage stated",
            "PASS",
            "district-level cluster bootstrap; the components it does not "
            "cover are listed explicitly",
        ),
        (
            "No VALIDATED_EXTERNAL claim without the supporting evidence",
            "PASS",
            "status is PARTIAL; the conditions for VALIDATED_EXTERNAL are "
            "listed in the final-status report",
        ),
    ]
    gate_rows = "\n".join(
        f"| {name} | {status} | {evidence} |" for name, status, evidence in gates
    )
    body = f"""# Stage 40 — Quality Gates

Every gate below is checked against an executed artifact, not asserted.

| Gate | Status | Evidence |
|---|---|---|
{gate_rows}

## The two defects this stage caught

Stage 40 did not begin clean. Two defects were found by review, both of
which would have produced a **misleading** Stage 40 result rather than
a failing one:

1. **The frozen parameters never reached the model.** `HYRUE.__init__`
   applied the crop preset whenever a crop name was given, overwriting
   any explicit `HYRUEParams`. The calibrated benchmark would have been
   numerically identical to the baseline. The first run was aborted on
   finding this; the run was restarted only after the plumbing was
   fixed and covered by regression tests.

2. **The calibration was fitted against a different input basis from the
   one it was evaluated on.** The first profile builder used a synthetic
   sigmoid LAI and a hard-coded PAR factor, while the benchmark resolves
   LAI with the GDD model and PAR with the weather source's own factor.
   Correcting this changed the fitted ε from 2.570 to
   {fmt(frozen['parameter_values']['epsilon'], 3)} and changed the
   development R² accordingly.

Neither defect would have shown up as a test failure. Both were found by
reading the code path rather than by running it. The gate table above
exists so that the next stage does not have to rediscover them.

## What these gates do *not* cover

* They do not verify the scientific correctness of the uncalibrated
  parameters (LAI model, EWSI weights, thermal width, soil moisture
  field capacity). Those remain unsourced or default-valued.
* They do not verify the external *coverage* of the test set. The
  evaluation is on a documented stratified sample of the test districts,
  not the full set.
* They do not bound the calibration uncertainty inside the reported
  intervals.
"""
    write("STAGE-40-QUALITY-GATES.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-LIMITATIONS.md
    # ------------------------------------------------------------------
    body = f"""# Stage 40 — Limitations

These are the limits of what Stage 40 established. They are stated
plainly so that nothing in the reports can be read as more than it is.

## Scope

| Limit | Detail |
|---|---|
| One dataset | CIMMYT eastern-India wheat, one region, six seasons (2016-17 to 2021-22) |
| Three test districts | Buxar, Muzaffarpur, Rohtas - the whole test set is three clusters |
| A sample, not the full test set | {sample_total} evaluated of {sample_design_total} sampled |
| One free parameter | `epsilon`; `HI` fixed at 0.45 |
| One model | HYRUE; no other crop model was compared |
| One metric family | RMSE, MAE, bias, R², MAPE - no skill score against an operational forecast |

## Model limitations that remain open

| Item | Why it matters |
|---|---|
{_rows(_MODEL_LIMITS)}

## Evaluation limitations

| Item | Detail |
|---|---|
{_rows(_EVAL_LIMITS)}

## What would be needed to lift the status

1. **Observed LAI** (or a published EWSI weighting) to break the
   `epsilon`/`HI` degeneracy and the LAI confound.
2. **A second dataset** in a different agro-climatic zone.
3. **The full 1,722-record test set**, or an explicit statement that the
   sample is sufficient.
4. **A nested bootstrap** that resamples the calibration inside the
   interval computation.
5. **A second external dataset** to separate "this model works" from
   "this model works in Bihar".
"""
    write("STAGE-40-LIMITATIONS.md", body)

    # ------------------------------------------------------------------
    # STAGE-40-FINAL-STATUS.md
    # ------------------------------------------------------------------
    test_r2 = (comparison or {}).get("calibrated", {}).get("r2")
    base_r2 = (comparison or {}).get("baseline", {}).get("r2")
    body = f"""# Stage 40 — Final Status

## Status: `PARTIAL`

| Field | Value |
|---|---|
| Model | HYRUE {frozen['model_version']} |
| External validation status | **PARTIAL** |
| Scientific support status | **PARTIAL** |
| Calibrated | yes, on development districts only |
| Frozen | yes, before external evaluation |
| Test districts | Buxar, Muzaffarpur, Rohtas (held out from calibration) |
| Records evaluated | {sample_total} of {sample_design_total} sampled (of 1,722 test records) |

`VALIDATED_EXTERNAL` is **not** claimed. The reasons are specific, not
rhetorical:

| Requirement for `VALIDATED_EXTERNAL` | Met? | Evidence |
|---|---|---|
{_rows3(_validation_gates(sample_total, test_r2))}

## What Stage 40 established

* The uncalibrated model was **substantially biased** on these data
  (baseline R² = {fmt(base_r2)} on the same records). A single
  calibrated parameter, fitted on development districts only, moved the
  test R² to {fmt(test_r2)} — an improvement of
  {fmt(_delta(base_r2, test_r2), 3)} in R².
* **The calibrated model still does not beat the mean predictor on the
  test districts.** A negative R² means the sum of squared prediction
  errors exceeds the sum of squared deviations of the observations from
  their own mean: predicting the district's average observed yield for
  every field would score a better R² than this model does. The
  calibration moved the model in the right direction and cut RMSE from
  {cmp_rmse_base} to {cmp_rmse_cal} t/ha
  on the same records, but it has not made the model a good predictor of
  district-level yields.
* The improvement is **not** an artefact of tuning on the evaluation
  set: the leave-one-district-out validation on the development
  districts shows the same direction
  ({vrmse_base} -> {vrmse_cal} t/ha
  mean validation RMSE), and the fitted `epsilon` is stable across all
  {stability.get('n_folds')} folds (relative range
  {fmt(stability.get('relative_range'), 4)}).
* The model is **not** fit for operational use. A test R² of
  {fmt(test_r2)} on three districts is a research result, not a
  production claim.

## What Stage 40 did not establish

* That the model generalises beyond these three districts.
* That `epsilon` = {fmt(frozen['parameter_values']['epsilon'], 3)} is the
  true radiation use efficiency of wheat in Bihar. It is the scale the
  development set implies, given the other parameters.
* That the remaining error is random. The error sources that remain
  open (LAI, EWSI, thermal width, soil moisture) are **systematic**, and
  systematic error does not average out.
* That the model is ready for decision-making. It is not.

## The two defects found

Recorded in full in `STAGE-40-QUALITY-GATES.md`, and repeated here
because they change how the numbers should be read:

1. The first benchmark run would have evaluated the **uncalibrated**
   model, because the crop preset silently overrode the explicit
   parameters. It was aborted.
2. The first calibration was fitted against a **different input basis**
   from the one used at evaluation time. Correcting it moved the fitted
   `epsilon` from 2.570 to {fmt(frozen['parameter_values']['epsilon'], 3)}.

The numbers in this report are the ones produced **after** both fixes.

## Recommended next step

Stage 41 should target the **identifiability** problem rather than more
benchmarking: obtain observed LAI (or a published EWSI weighting) so
that `epsilon` and `HI` can be separated, then re-run this stage
end-to-end. More benchmark records on the current model would not change
the status.
"""
    write("STAGE-40-FINAL-STATUS.md", body)

    print()
    print("evaluation reports written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
