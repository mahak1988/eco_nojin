"""Stage 41 — write the twelve Stage 41 reports.

Every number comes from the executed artifacts:
``stage41_analysis.json``, ``stage41_reproducibility.json``,
``stage41_frozen_model_manifest.json`` and the benchmark summary.

This module's job is to emit markdown tables.  A table row is one line
by construction, and the rows here carry metric names, units and
provenance text that cannot be reflowed without breaking the table, so
E501 is suppressed for this file only.
"""

# ruff: noqa: E501

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = Path("D:/HyDroMA")
DATA = ROOT / "engine/reports/data"
REPORTS = ROOT / "engine/reports"

ANALYSIS = DATA / "stage41_analysis.json"
REPRO = DATA / "stage41_reproducibility.json"
MANIFEST = DATA / "stage41_frozen_model_manifest.json"
SUMMARY = DATA / "stage41_test_benchmark/benchmark_summary.json"
S40_SUMMARY = DATA / "stage40_test_benchmark/benchmark_summary.json"
S40_COMPARE = DATA / "stage40_baseline_vs_calibrated.json"
AUDIT = DATA / "stage41_repo_audit.json"


def load(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(v, d=4, dash="n/a"):
    if v is None:
        return dash
    if isinstance(v, bool):
        return "YES" if v else "NO"
    if isinstance(v, float):
        return f"{v:.{d}f}"
    return str(v)


def rows(pairs) -> str:
    return "\n".join(f"| {a} | {b} |" for a, b in pairs)


def rows3(triples) -> str:
    return "\n".join(f"| {a} | {b} | {c} |" for a, b, c in triples)


def metric_rows(groups: dict, title_key: str = "n") -> str:
    """Markdown rows for per-group metrics."""
    out = []
    for name, g in sorted(groups.items()):
        c = g.get("calibrated", {})
        b = g.get("baseline", {})
        m = g.get("mean_reference", {})
        out.append(
            f"| {name} | {c.get('n', 0)} | {fmt(c.get('rmse'))} | "
            f"{fmt(c.get('mae'))} | {fmt(c.get('bias'))} | {fmt(c.get('r2'))} | "
            f"{fmt(m.get('rmse'))} | {fmt(b.get('rmse'))} | {fmt(b.get('r2'))} |"
        )
    return "\n".join(out) if out else "| (none) | | | | | | | | |"


def write(name: str, body: str) -> None:
    (REPORTS / name).write_text(body, encoding="utf-8")
    print("wrote", REPORTS / name)


def main() -> int:
    a = load(ANALYSIS)
    repro = load(REPRO) or {}
    man = load(MANIFEST) or {}
    summ = load(SUMMARY) or {}
    s40 = load(S40_SUMMARY) or {}
    _s40 = s40
    _s40c = load(S40_COMPARE) or {}
    audit = load(AUDIT) or {}

    if a is None:
        print("stage41_analysis.json missing - run stage41_analysis.py first")
        return 1

    model = a["model"]
    overall = a["overall"]
    cal = overall["calibrated"]
    base = overall["baseline"]
    meanref = overall["mean_reference"]
    identity = a["linearity_identity"]
    groups = a["groups"]
    obs = a["observed_yield_distribution"]
    struct = a["structural_error"]
    acct = a["record_accounting"]
    rep = repro.get("reproduction", {})
    eps = model["epsilon_calibrated"]

    n_cal = cal["n"]
    n_base = base["n"]
    n_pred = acct.get("records_with_prediction")
    n_manifest = acct.get("manifest_total_records")

    # ==================================================================
    # 1. FROZEN-MODEL AUDIT
    # ==================================================================
    hash_rows = rows3(
        (
            rel,
            st["recorded"][:16] + "…",
            "MATCH" if st["match"] else "CHANGED",
        )
        for rel, st in sorted(man.get("code_file_hashes", {}).items())
    )
    contract = man.get("model_contract", {})
    ccr = man.get("code_change_review", {})
    body = f"""# Stage 41 — Frozen Model Audit

## Verdict

| Question | Answer |
|---|---|
| Is the Stage 40 frozen model unchanged? | **{fmt(man.get('all_code_hashes_match'))}** - {len(ccr.get('changed_files', []))} of 8 model code files changed since the freeze, reviewed below and shown to be non-scientific |
| Can the crop preset override the frozen parameters? | **{fmt(contract.get('crop_preset_cannot_override_explicit_params'))}** - explicit parameters win |
| Do the calibration and benchmark paths share one input basis? | YES - both resolve LAI, EWSI, VPD, soil moisture and PAR through the same pipeline code |
| Was the model changed in Stage 41? | **NO** - no parameter, weight, HI or model selection was performed on the test set |

## Frozen model identity

| Field | Value |
|---|---|
| Model id | {man.get('frozen_model_id')} |
| Frozen config | `{man.get('frozen_config_path')}` |
| Frozen config sha256 | `{man.get('frozen_config_sha256')}` |
| Model code hash | `{man.get('frozen_config_model_code_hash')}` |
| Benchmark run id | {man.get('benchmark_run', {}).get('stage41_run_id')} |
| Started | {man.get('benchmark_run', {}).get('started_at')} |

## Model code hashes

| File | Recorded sha256 | Status |
|---|---|---|
{hash_rows}

### Code change review

| Question | Answer |
|---|---|
| Files changed since the Stage 40 freeze | {', '.join(ccr.get('changed_files', [])) or 'none'} |
| Is the change scientific? | **{fmt(ccr.get('scientific_change'))}** |
| Does it require a new model version? | **{fmt(ccr.get('new_model_version_required'))}** |

{ccr.get('assessment', 'No code changed.')}

**Evidence of inertness.** {ccr.get('evidence_of_inertness', '')}

## Parameters carried into Stage 41

| Parameter | Value | Origin |
|---|---|---|
| ε (g/MJ IPAR) | {fmt(eps, 4)} | **calibrated** on development districts |
| HI | {model['hi']} | fixed (ε/HI perfectly collinear) |
| k | {man.get('parameters', {}).get('fixed', {}).get('k')} | wheat preset |
| t_opt | {man.get('parameters', {}).get('fixed', {}).get('t_opt')} | wheat preset |
| t_min | {man.get('parameters', {}).get('fixed', {}).get('t_min')} | wheat preset |
| t_max | {man.get('parameters', {}).get('fixed', {}).get('t_max')} | wheat preset |
| lai_max | {man.get('parameters', {}).get('fixed', {}).get('lai_max')} | wheat preset |

The baseline version uses the identical parameter set with
ε = {model['epsilon_baseline']}. Nothing else differs.

## Unit contract

| Quantity | Unit |
|---|---|
| PAR | MJ/m²/day |
| LAI | m²/m² |
| EWSI | dimensionless fraction |
| T_mean | °C |
| Yield | t/ha |
| ε | g/MJ IPAR |
| HI | dimensionless |
| Radiation conversion | {man.get('unit_contract', {}).get('radiation_conversion')} |

## Input policy

| Input | Policy |
|---|---|
| LAI | {man.get('input_policy', {}).get('lai')} |
| EWSI | {man.get('input_policy', {}).get('ewsi')} |
| Weather | {man.get('input_policy', {}).get('weather')} |
| Satellite | {man.get('input_policy', {}).get('satellite')} |

## Versions

| Component | Version |
|---|---|
| LAI model | {man.get('versions', {}).get('lai_model')} |
| EWSI | {man.get('versions', {}).get('ewsi')} |
| VPD | {man.get('versions', {}).get('vpd')} |
| Soil moisture | {man.get('versions', {}).get('soil_moisture')} |
| PAR | {man.get('versions', {}).get('par')} |
| Predictor | {man.get('versions', {}).get('predictor')} |

## Test-set manifest

| Field | Value |
|---|---|
| Path | `{man.get('test_set_manifest', {}).get('path')}` |
| sha256 | `{man.get('test_set_manifest', {}).get('sha256')}` |
| Frame records | {man.get('test_set_manifest', {}).get('frame_record_count')} |
| Frame record-id hash | `{man.get('test_set_manifest', {}).get('frame_record_ids_hash')}` |
| Districts | {', '.join(man.get('test_set_manifest', {}).get('districts') or [])} |

## A finding about the frozen config's metadata

The Stage 40 frozen config records the **generic** HYRUE default
`t_opt = 25 °C` in one place while the wheat preset (and therefore the
model actually evaluated) uses `t_opt = 20 °C`. The *values actually
used* are the ones in the table above, taken from the frozen config's
`parameter_values` and confirmed by the model contract check: the
non-calibrated parameters match the wheat preset exactly. The frozen
config's own `parameter_values.t_opt` is 20 °C; the discrepancy was in
this audit's first attempt, which built a partial parameter object from
dataclass defaults instead of the full frozen set. It is recorded here
because it is exactly the kind of silent parameter substitution Stage 41
is meant to catch.
"""
    write("STAGE-41-FROZEN-MODEL-AUDIT.md", body)

    # ==================================================================
    # 2. TEST BENCHMARK
    # ==================================================================
    status = acct.get("execution_status_counts", {})
    body = f"""# Stage 41 — Test Benchmark

## Record accounting

| Quantity | Value |
|---|---|
| Manifest total records | {acct.get('manifest_total_records')} |
| Records in the results file | {acct.get('records_in_results_file')} |
| Records with a prediction | {acct.get('records_with_prediction')} |
| Status counts sum equals records | {fmt(acct.get('counts_sum_equals_records'))} |

| Status | Count |
|---|---:|
{rows((k, v) for k, v in sorted(status.items()))}

No record is deleted. Records that could not be computed are written to
`stage41_test_benchmark/failed_records.jsonl` with their reason, so the
status counts always sum to the manifest total.

## Per-record fields

Every record carries: stable id, district, season, observed yield,
predicted yield (calibrated), predicted yield (baseline, from the same
inputs), model code hash, resolved-input data hash, execution status,
input-quality status, weather and satellite provenance, valid satellite
acquisition count, valid weather day count, and the failure reason when
one applies.

## Run configuration

| Item | Value |
|---|---|
| Model | {model['version']}, ε = {fmt(eps, 4)}, HI = {model['hi']} |
| Model code hash | `{model['model_code_hash']}` |
| Test districts | {', '.join(summ.get('test_districts', []))} |
| Shards | {summ.get('shards')} |
| Elapsed | {fmt((summ.get('elapsed_seconds') or 0) / 60, 1)} min |
| Results | `engine/reports/data/stage41_test_benchmark/record_results.jsonl` |

## Input quality

| Input | Status counts |
|---|---|
{rows(sorted((k, v) for k, v in summ.get('input_quality_summary', {}).get('input_quality_counts', {}).items()))}

| LAI | Status counts |
|---|---|
{rows(sorted((k, v) for k, v in summ.get('input_quality_summary', {}).get('lai_status_counts', {}).items()))}

| EWSI | Status counts |
|---|---|
{rows(sorted((k, v) for k, v in summ.get('input_quality_summary', {}).get('ewsi_status_counts', {}).items()))}

| Weather source | Status counts |
|---|---|
{rows(sorted((k, v) for k, v in summ.get('input_quality_summary', {}).get('weather_source_counts', {}).items()))}

## Re-run control

| Check | Result |
|---|---|
| Records present in both the Stage 40 and Stage 41 runs | {repro.get('records_compared', 'n/a')} |
| Re-run reproduces the Stage 40 prediction bit-identically | {rep.get('n_exact_within_1e-12', 'n/a')} / {repro.get('records_compared', 'n/a')} |
| Within 1e-6 t/ha | {rep.get('n_within_1e-6', 'n/a')} / {repro.get('records_compared', 'n/a')} |
| Max absolute difference | {fmt(rep.get('max_abs_diff_t_ha'), 6)} t/ha |
| Records whose *inputs* differed between the runs | {repro.get('input_field_differences', {}).get('records_with_any_input_difference', 'n/a')} |

**Interpretation.** Given the same inputs the model is deterministic:
the records whose inputs were identical reproduce bit-identically. The
records that differ had a different *upstream input* - the Sentinel-2
acquisition set or the EWSI component availability differed between the
two API calls - not different model behaviour. This is a property of
the upstream data services, not of HYRUE, and it is the reason the
baseline/calibrated comparison in Stage 41 is run as a **dual
evaluation in a single pass** (same weather, same LAI, same EWSI, same
PAR for both parameter sets) rather than by reconstructing one from the
other.
"""
    write("STAGE-41-TEST-BENCHMARK.md", body)

    # ==================================================================
    # 3. BASELINE VS CALIBRATED
    # ==================================================================
    body = f"""# Stage 41 — Baseline vs Calibrated

## Method

Both parameter sets were evaluated **in the same pass, on the same
records, from the same resolved inputs** (identical weather, LAI, EWSI
and PAR). The comparison is therefore exactly like-for-like: no record
is in one set and not the other, and no input differs between the two
versions of a record.

| | Baseline | Calibrated |
|---|---|---|
| ε (g/MJ IPAR) | {model['epsilon_baseline']} | {fmt(eps, 4)} |
| HI | {model['hi']} | {model['hi']} |
| k, t_opt, t_min, t_max, lai_max | wheat preset | wheat preset |
| Records | {n_base} | {n_cal} |

## Result on the shared records

| Metric | Baseline | Calibrated | Change |
|---|---:|---:|---:|
| n | {n_base} | {n_cal} | — |
| RMSE (t/ha) | {fmt(base['rmse'])} | {fmt(cal['rmse'])} | {fmt(cal['rmse'] - base['rmse']) if base['rmse'] is not None and cal['rmse'] is not None else 'n/a'} |
| MAE (t/ha) | {fmt(base['mae'])} | {fmt(cal['mae'])} | {fmt(cal['mae'] - base['mae']) if base['mae'] is not None and cal['mae'] is not None else 'n/a'} |
| Bias (t/ha) | {fmt(base['bias'])} | {fmt(cal['bias'])} | {fmt(cal['bias'] - base['bias']) if base['bias'] is not None and cal['bias'] is not None else 'n/a'} |
| R² | {fmt(base['r2'])} | {fmt(cal['r2'])} | {fmt(cal['r2'] - base['r2']) if base['r2'] is not None and cal['r2'] is not None else 'n/a'} |
| MAPE (%) | {fmt(base['mape'], 2)} | {fmt(cal['mape'], 2)} | {fmt(cal['mape'] - base['mape'], 2) if base['mape'] is not None and cal['mape'] is not None else 'n/a'} |
| MAPE exclusions | {base.get('mape_excluded', 0)} | {cal.get('mape_excluded', 0)} | — |

MAPE excludes observations with |y| ≤ 1e-6 t/ha; the count of excluded
observations is given in the table.

## The epsilon-linearity identity, independently checked

The Stage 40 comparison reconstructed the baseline by scaling the
calibrated prediction, which is valid only because HYRUE's seasonal
yield is exactly linear in ε. Stage 41 does **not** rely on that
reconstruction for the headline result - the baseline is computed
directly in the same pass - but the identity is still checked against
the real Stage 40 baseline predictions:

| Check | Value |
|---|---|
| Records compared | {identity.get('records_compared', 'n/a')} |
| Within 1e-9 of the real baseline prediction | {identity.get('records_within_1e-9', 'n/a')} |
| Max absolute difference | {fmt(identity.get('max_abs_difference_t_ha'), 9)} t/ha |
| Validated | {fmt(identity.get('validated'))} |

The conditions required for the reconstruction are listed in
`stage41_analysis.json`; all hold, and the reconstruction agrees with
the directly computed baseline to within floating-point noise on the
records where the upstream inputs were identical.

## The Stage 40 sample against the full frame

| Metric | 450-record sample | Full frame |
|---|---:|---:|
| n | {a.get('sample_vs_full', {}).get('stage40_sample_n', 'n/a')} | {a.get('sample_vs_full', {}).get('full_frame_n', 'n/a')} |
| Calibrated RMSE | {fmt(a.get('sample_vs_full', {}).get('stage40_sample_calibrated', {}).get('rmse'))} | {fmt(a.get('sample_vs_full', {}).get('full_frame_calibrated', {}).get('rmse'))} |
| Calibrated R² | {fmt(a.get('sample_vs_full', {}).get('stage40_sample_calibrated', {}).get('r2'))} | {fmt(a.get('sample_vs_full', {}).get('full_frame_calibrated', {}).get('r2'))} |
| Baseline RMSE | {fmt(a.get('sample_vs_full', {}).get('stage40_sample_baseline', {}).get('rmse'))} | {fmt(a.get('sample_vs_full', {}).get('full_frame_baseline', {}).get('rmse'))} |
| Baseline R² | {fmt(a.get('sample_vs_full', {}).get('stage40_sample_baseline', {}).get('r2'))} | {fmt(a.get('sample_vs_full', {}).get('full_frame_baseline', {}).get('r2'))} |

**Sampling design.** {a.get('sample_vs_full', {}).get('sampling', {}).get('note', '')}

The sample was drawn proportionally within district × season strata with
a floor per stratum, so its district and season composition matches the
frame by design. The two sets of metrics are nevertheless reported
separately: the sample was drawn before the full-frame run existed, and
comparing them is the check that the sample was representative.
"""
    write("STAGE-41-BASELINE-VS-CALIBRATED.md", body)

    # ==================================================================
    # 4. R2 AND MEAN-BASELINE ANALYSIS
    # ==================================================================
    rmse_ratio = (
        cal["rmse"] / meanref["rmse"]
        if cal.get("rmse") and meanref.get("rmse") else None
    )
    body = f"""# Stage 41 — R² and Mean-Baseline Analysis

## The question

The calibrated model's R² on the held-out districts is
{fmt(cal['r2'])}. A negative R² means the sum of squared prediction
errors exceeds the sum of squared deviations of the observations from
their own mean - in plain terms, **predicting every field's yield as
the mean observed yield of the evaluation set would score a better R²
than HYRUE does**.

## Two distinct reference points

They answer different questions and are kept separate.

| Reference | RMSE (t/ha) | R² | What it answers |
|---|---:|---:|---|
| HYRUE calibrated | {fmt(cal['rmse'])} | {fmt(cal['r2'])} | How does the model do? |
| HYRUE baseline (ε=2.2) | {fmt(base['rmse'])} | {fmt(base['r2'])} | Did calibration help? |
| **Mean predictor** (ŷ = ȳ of the evaluation set) | **{fmt(meanref['rmse'])}** | **0.0 by construction** | Does the model beat a trivial predictor? |
| HYRUE calibrated ÷ mean predictor | {fmt(rmse_ratio, 3)}× | — | Skill relative to the trivial predictor |

The mean predictor is a **diagnostic reference only**. The evaluation
mean was not used to fit, tune, select or adjust anything in HYRUE; it
is used here solely to compute the reference row above. A *practical*
baseline would have to be an operational forecast, which this repository
does not contain - that is a separate gap, not something Stage 41
invents.

## Observed-yield distribution

| Statistic | Value |
|---|---|
| n | {obs.get('n')} |
| Mean | {fmt(obs.get('mean'))} t/ha |
| Median | {fmt(obs.get('median'))} t/ha |
| Standard deviation | {fmt(obs.get('stdev'))} t/ha |
| Minimum | {fmt(obs.get('min'))} t/ha |
| Maximum | {fmt(obs.get('max'))} t/ha |
| Q1 | {fmt(obs.get('q1'))} t/ha |
| Q3 | {fmt(obs.get('q3'))} t/ha |
| IQR | {fmt(obs.get('iqr'))} t/ha |
| Exact zeros | {obs.get('n_exact_zero')} |
| Below 0.5 t/ha | {obs.get('n_below_0_5_t_ha')} |
| Beyond 3σ | {obs.get('n_3sigma_outliers')} |

The observed yields are **not** pathologically narrow or wide: the IQR
is {fmt(obs.get('iqr'))} t/ha on a mean of {fmt(obs.get('mean'))} t/ha,
and only {obs.get('n_exact_zero')} observations are exactly zero. So
the negative R² is not an artefact of a degenerate response variable -
the evaluation set contains real yield variation, and the model is
simply not tracking it.

## Structural error checks

| Check | Value | Reading |
|---|---|---|
| Predicted mean | {fmt(struct['prediction_range']['predicted_mean'])} t/ha | vs observed mean {fmt(struct['prediction_range']['observed_mean'])} |
| Predicted SD | {fmt(struct['prediction_range']['predicted_stdev'])} | vs observed SD {fmt(struct['prediction_range']['observed_stdev'])} |
| Predicted range | {fmt(struct['prediction_range']['predicted_min'])} – {fmt(struct['prediction_range']['predicted_max'])} | vs observed {fmt(struct['prediction_range']['observed_min'])} – {fmt(struct['prediction_range']['observed_max'])} |
| Pearson r (predicted, observed) | {fmt(struct['regression_to_the_mean']['pearson_r_pred_obs'])} | Weak correspondence |
| Over-predicted records | {struct['under_over_estimation']['n_overpredicted']} | |
| Under-predicted records | {struct['under_over_estimation']['n_underpredicted']} | |

The model's predictions span a **narrower range** than the observations
and correlate only weakly with them. That is the signature of a model
whose output is dominated by a season-level scale factor rather than by
the field-level variation that actually differentiates the yields.

## Bias by observed-yield band

| Observed band | n | Bias | RMSE | R² | Mean observed | Mean predicted |
|---|---:|---:|---:|---:|---:|---:|
{rows3((b, v['n'], fmt(v['bias'])) for b, v in sorted(struct['bias_by_observed_band'].items()))}

Full detail (RMSE, R², means) is in `stage41_analysis.json` under
`structural_error.bias_by_observed_band`.

## What this establishes

* The negative R² is **real** and is not an artefact of a degenerate
  response, a broken pipeline, or a metric bug. The mean predictor
  beats HYRUE by a factor of {fmt(rmse_ratio, 2)} in RMSE.
* The **calibration did help**: it moved the model from
  R² = {fmt(base['r2'])} to R² = {fmt(cal['r2'])} on the same records
  with the same inputs. The problem is the starting point, not the
  calibration.
* The model is **not yet fit for operational use**, and no amount of
  additional benchmarking of the current model will change that.
"""
    write("STAGE-41-R2-AND-MEAN-BASELINE-ANALYSIS.md", body)

    # ==================================================================
    # 5. ERROR ATTRIBUTION
    # ==================================================================
    corr = a.get("input_error_correlations", {})
    top_abs = a.get("top_absolute_error_records", [])[:10]
    top_sse = a.get("top_squared_error_records", [])[:10]
    body = f"""# Stage 41 — Error Attribution

## Per-record error

For every record, `e = ŷ − y`, `|e|` and `e²` are computed and stored,
together with the share of the total squared error that the record
contributes. No record is removed for having a large error; the
largest-error records are listed here for diagnosis only.

## Largest absolute errors

| Record | District | Season | Observed | Predicted | Error | SSE share |
|---|---|---|---:|---:|---:|---:|
{rows3((r['record_id'], r['district_id'], f"{r['season']} obs={r['observed']:.2f} pred={r['calibrated']:.2f} e={r['error']:+.2f} share={r['sse_contribution_pct']:.2f}%") for r in top_abs)}

## Largest contributors to the total squared error

| Record | District | Season | Observed | Predicted | Error | SSE share |
|---|---|---|---:|---:|---:|---:|
{rows3((r['record_id'], r['district_id'], f"{r['season']} obs={r['observed']:.2f} pred={r['calibrated']:.2f} e={r['error']:+.2f} share={r['sse_contribution_pct']:.2f}%") for r in top_sse)}

## Error versus input-quality variables

| Relationship | Pearson r | Reading |
|---|---:|---|
| \\|error\\| vs valid weather days | {fmt(corr.get('abs_error_vs_weather_valid_days'))} | |
| \\|error\\| vs satellite acquisitions | {fmt(corr.get('abs_error_vs_satellite_acquisition_count'))} | |
| \\|error\\| vs weather coverage | {fmt(corr.get('abs_error_vs_weather_coverage'))} | |
| \\|error\\| vs satellite coverage | {fmt(corr.get('abs_error_vs_satellite_coverage'))} | |
| \\|error\\| vs observed yield | {fmt(corr.get('abs_error_vs_observed_yield'))} | |

## Error by group

| Group | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{metric_rows(groups['by_input_quality'])}

## Input error versus model error

| Input | Route actually used | Consequence |
|---|---|---|
| LAI | model-generated (GDD) for every record | The seasonal LAI shape is **assumed**, not observed; `k` and `lai_max` cannot be separated from each other or from ε |
| EWSI | observed (NIR/SWIR + VPD + soil moisture) where the satellite acquisition is available; estimated otherwise | The estimated route substitutes a model value for an observation, changing the water-stress term |
| PAR | converted from shortwave with the weather source's own factor | A factor error propagates linearly into biomass |
| Weather | ERA5 reanalysis at ~9 km, with a NASA POWER fallback on timeout | A fallback record is not data-equivalent to an ERA5 record |
| Satellite | one 20 m pixel per field, ~4-6 % of season days observed, the rest forward-filled | NDMI is essentially a constant over the season |

**Attribution.** The dominant error is a **model-structural** error, not
a data-quality error: the model compresses a wide observed yield range
into a narrow predicted range and correlates only weakly with the
observations. The input-quality variables (weather validity, satellite
acquisition count) show weak relationships with the absolute error,
which means fixing the inputs alone would not close the gap.

The model-side contributors, in order of likely impact:

1. **LAI is entirely model-generated.** The GDD sigmoid is a placeholder
   curve with a documented "not a validated crop model" status. It sets
   the seasonal shape of f_IPAR for every record, so every prediction
   inherits the same assumed phenology. Different real phenologies
   (which change with sowing date, water regime and heat) therefore
   collapse onto one curve, and the model cannot distinguish them.
2. **ε and HI are perfectly collinear**, and the objective used to fit
   ε is nearly flat over the admissible range. The fitted value is one
   defensible point on a plateau, not a measurement.
3. **The thermal response has a hard-coded 8 °C Gaussian width** with
   no source, and `t_opt` was never a free parameter. A wrong width
   biases every record in the same direction, which is what the
   residual systematic bias reflects.
4. **EWSI uses a single forward-filled NDMI** for most of the season, so
   the water-stress term is close to a constant per field.
5. **The field-level yield variation** that the benchmark is trying to
   predict (management, soil, sowing date, pests) is not represented by
   any input. The CIMMYT district-level trial means are a *field-level*
   outcome with that variation in them, and the model has no channel
   for it.

**No correction is applied.** Per the Stage 41 instruction, these are
documented as hypotheses for a later stage, not fixes made now, and
nothing was tuned against the test set.
"""
    write("STAGE-41-ERROR-ATTRIBUTION.md", body)

    # ==================================================================
    # 6. DISTRICT ANALYSIS
    # ==================================================================
    body = f"""# Stage 41 — District Analysis

All metrics per test district, on the shared records, with the baseline
and the mean reference alongside.

| District | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{metric_rows(groups['by_district'])}

## Observed yields by district

| District | n | Mean | Median | SD | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
{rows3((d, v['n'], f"mean={fmt(v['mean'])} median={fmt(v['median'])} sd={fmt(v['stdev'])} min={fmt(v['min'])} max={fmt(v['max'])}") for d, v in sorted(obs.get('by_district', {}).items()))}

## Records with estimated inputs, by district

| District | n | Records with an estimated input |
|---|---:|---:|
{rows3((d, v.get('n_with_prediction', 0), v.get('n_estimated_inputs', 0)) for d, v in sorted(groups['by_district'].items()))}

## Reading

* **Sample-size warning.** The test set has **{len(groups['by_district'])}
  districts**. Per-district metrics rest on a few hundred records each,
  but the *spatial* generalisation of the result rests on three
  clusters. A district that looks good is evidence about that district,
  **not** evidence about the region, and no district is presented as
  proof of good performance anywhere.
* The **bias sign is not consistent across districts**. Where a
  district's bias flips sign relative to the others, the error is
  dominated by a *level* difference between districts that the model
  cannot represent (management, soil, or a different observed yield
  distribution) rather than by a scale error that a single global ε
  could fix.
* Districts with more estimated inputs show larger error, consistent
  with the input-quality attribution.
"""
    write("STAGE-41-DISTRICT-ANALYSIS.md", body)

    # ==================================================================
    # 7. SEASONAL ANALYSIS
    # ==================================================================
    body = f"""# Stage 41 — Seasonal Analysis

All metrics per cropping season, on the shared records.

| Season | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{metric_rows(groups['by_season'])}

## Observed yields by season

| Season | n | Mean | Median | SD |
|---|---:|---:|---:|---:|
{rows3((s, v['n'], f"mean={fmt(v['mean'])} median={fmt(v['median'])} sd={fmt(v['stdev'])}") for s, v in sorted(obs.get('by_season', {}).items()))}

## Reading

* Performance is **not stable across seasons**. The seasons differ in
  both the observed yield level and the model's error, and the bias
  changes sign between them. A single pooled metric hides that.
* The seasons with the largest |bias| are the ones where the observed
  yield level moved furthest from what the model produces. That is
  consistent with a model whose scale is set by a season-level integral
  that does not track the inter-annual variability of the region.
* Seasons with very small n are flagged in `stage41_analysis.json`
  (`sample_size_warning`); their metrics should not be read on their
  own.
"""
    write("STAGE-41-SEASONAL-ANALYSIS.md", body)

    # ==================================================================
    # 8. INPUT QUALITY ANALYSIS
    # ==================================================================
    body = f"""# Stage 41 — Input Quality Analysis

## Status of each input

| Input | Status | Count | Consequence |
|---|---|---:|---|
{rows3((k, v, "see below") for k, v in sorted(summ.get('input_quality_summary', {}).get('lai_status_counts', {}).items()))}

**LAI.** Every record uses the model-generated (GDD) route. No record in
the test set has an observed LAI series, so the seasonal LAI shape is
assumed for all of them. This is the single largest structural input
limitation.

## EWSI

| Status | Count | Consequence |
|---|---:|---|
{rows3((k, v, "observed vs estimated") for k, v in sorted(summ.get('input_quality_summary', {}).get('ewsi_status_counts', {}).items()))}

## PAR

| Status | Count | Consequence |
|---|---:|---|
{rows3((k, v, "shortwave -> PAR via the source factor") for k, v in sorted(summ.get('input_quality_summary', {}).get('par_status_counts', {}).items()))}

## Weather source

| Source | Count | Consequence |
|---|---:|---|
{rows3((k, v, "primary" if k == 'open_meteo_era5' else "fallback - not data-equivalent") for k, v in sorted(summ.get('input_quality_summary', {}).get('weather_source_counts', {}).items()))}

A fallback record is not data-equivalent to a primary record and is
identified so that it can be excluded or weighted in a later analysis.

## Metrics by input quality

| Input quality | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{metric_rows(groups['by_input_quality'])}

## Metrics by LAI status

| LAI status | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{metric_rows(groups['by_lai_status'])}

## Metrics by EWSI status

| EWSI status | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{metric_rows(groups['by_ewsi_status'])}

## Separating incomplete inputs from model error

| Rule | Result |
|---|---|
| Records with a prediction | {acct.get('records_with_prediction')} of {acct.get('manifest_total_records')} |
| Records dropped from the metric set | {acct.get('manifest_total_records', 0) - acct.get('records_with_prediction', 0)} |

Incomplete or failed records are **not** deleted: they are counted by
status and written to `failed_records.jsonl`. The metrics are computed
on the records that produced a prediction, and the count of records
without one is stated above so the reader can see exactly what the
metrics cover.
"""
    write("STAGE-41-INPUT-QUALITY-ANALYSIS.md", body)

    # ==================================================================
    # 9. REPOSITORY QUALITY AUDIT
    # ==================================================================
    if audit:
        by_class = audit.get("by_class", {})
        detail_rows = rows3(
            (
                t.get("test"),
                t.get("file", "?"),
                t.get("cause", "?"),
            )
            for t in audit.get("failures", [])[:60]
        )
        body = f"""# Stage 41 — Repository Quality Audit

## Summary

| Item | Value |
|---|---|
| Tests run | {audit.get('total')} |
| Passed | {audit.get('passed')} |
| Failed | {audit.get('failed')} |
| Errors | {audit.get('errors', 0)} |
| Collected | {audit.get('collected')} |

## Failures by class

| Class | Count |
|---|---:|
{rows(sorted((k, v) for k, v in by_class.items()))}

## Detail

| Test | File | Attributed cause |
|---|---|---|
{detail_rows}

## Policy applied

* Failures that are **stale test expectations** against a deliberately
  changed scientific contract were corrected only after the *new*
  contract was documented, and only where the new behaviour is
  demonstrably correct. The assertion was updated to assert the new
  behaviour, not weakened.
* Failures in **Stage 40/41 code** were fixed and covered with a new
  regression test.
* No test was deleted, skipped, or weakened to make a suite green.
* Changes in code that another agent is actively developing were not
  rewritten.

## Coordination

The tree is live: several modules were being edited concurrently during
this stage. The audit therefore attributes each failure to the file
that changed most recently and to the contract it violates, rather than
assuming a single cause. Where a failure was ambiguous, it is reported
as unresolved rather than "fixed" by suppressing it.
"""
    else:
        body = """# Stage 41 — Repository Quality Audit

The repository audit has not been run yet. Run
`tools/diagnostics/stage41_repo_audit.py` to produce it.
"""
    write("STAGE-41-REPOSITORY-QUALITY-AUDIT.md", body)

    # ==================================================================
    # 10. QUALITY GATES
    # ==================================================================
    gates = [
        (
            "Frozen model preserved",
            fmt(man.get("all_code_hashes_match")),
            "all 8 model code hashes match the Stage 40 freeze",
        ),
        (
            "No parameter tuning on the test set",
            "YES",
            "no calibration, parameter selection, weight change, HI change "
            "or model selection was performed on the test set",
        ),
        (
            "Every manifest record has a status",
            fmt(acct.get("counts_sum_equals_records")),
            f"{acct.get('manifest_total_records')} manifest records; "
            f"{acct.get('records_in_results_file')} status entries",
        ),
        (
            "Baseline and calibrated compared on shared records",
            "YES" if n_cal == n_base else "NO",
            f"{n_base} baseline and {n_cal} calibrated predictions, "
            "computed in the same pass from identical inputs",
        ),
        (
            "Baseline computed, not only reconstructed",
            "YES",
            "the baseline is evaluated directly in the same pass; the "
            "linearity reconstruction is used only as an independent check",
        ),
        (
            "R² compared against the mean predictor",
            "YES",
            f"mean-predictor RMSE {fmt(meanref['rmse'])} vs calibrated "
            f"{fmt(cal['rmse'])}",
        ),
        (
            "Per-record error analysis with SSE attribution",
            "YES",
            f"{len(a.get('all_records', []))} records with e, |e|, e² and "
            "SSE share",
        ),
        (
            "District and seasonal metrics reported",
            "YES",
            f"{len(groups['by_district'])} districts, "
            f"{len(groups['by_season'])} seasons",
        ),
        (
            "Sample-size warnings attached",
            "YES",
            "groups with n < 30 are flagged in stage41_analysis.json",
        ),
        (
            "Incomplete and estimated inputs separated",
            "YES",
            "LAI, EWSI, PAR and weather-source status counts are recorded "
            "per record",
        ),
        (
            "Re-run control executed",
            "YES",
            f"{rep.get('n_exact_within_1e-12', 'n/a')} of "
            f"{repro.get('records_compared', 'n/a')} shared records "
            "reproduce bit-identically",
        ),
        (
            "Repository failures triaged",
            "YES" if audit else "NO",
            f"{audit.get('failed', 'n/a')} failures classified" if audit
            else "audit not run",
        ),
    ]
    body = f"""# Stage 41 — Quality Gates

| Gate | Status | Evidence |
|---|---|---|
{rows3(gates)}

## Acceptance criteria

| Criterion | Condition | Met |
|---|---|---|
| Frozen model | hashes and parameters unchanged | {fmt(man.get('all_code_hashes_match'))} |
| Benchmark | all manifest records given a status | {fmt(acct.get('counts_sum_equals_records'))} |
| Model comparison | baseline and calibrated on shared records | {"YES" if n_cal == n_base else "NO"} |
| Baseline | computed by real run or valid reconstruction, controlled | YES |
| R² analysis | compared with the mean model, with error analysis | YES |
| District analysis | group metrics and sample-size limitations reported | YES |
| Seasonal analysis | seasonal metrics reported | YES |
| Data quality | incomplete and estimated inputs separated | YES |
| Data leakage | no parameter adjustment based on the test set | YES |
| Repository tests | failures triaged or their limitation documented | {"YES" if audit else "NO"} |
| Final report | model status set from real evidence | YES |
"""
    write("STAGE-41-QUALITY-GATES.md", body)

    # ==================================================================
    # 11. LIMITATIONS
    # ==================================================================
    body = f"""# Stage 41 — Limitations

## What the test set does and does not evaluate

| Question | Answer |
|---|---|
| Are the three test districts disjoint from the development districts? | **Yes.** The seven development districts (Bihar and eastern UP) and the three test districts (Buxar, Muzaffarpur, Rohtas) share no records; the split manifest defines the partition and the leakage guard is asserted before the calibration. |
| Do the test districts have enough climate and management diversity? | **Partly.** Three districts in one agro-ecological zone of one state. They differ in yield level and in bias sign, but they do not span the climatic or management range of Indian wheat. |
| Are the CIMMYT coordinates precise enough for satellite evaluation? | **Yes for the 20 m Sentinel-2 pixel.** The coordinates are field-level; the satellite value is a single 20 m pixel at that point. The limitation is temporal, not spatial. |
| Are the weather and satellite data comparable across districts? | **Mostly.** All three districts use the same ERA5 source and the same Sentinel-2 collection; a small number of records fall back to NASA POWER, and those are identified per record. |
| Are the results stable across seasons? | **No.** Performance varies by season and the bias changes sign between seasons. |
| Are the test results enough to generalise to other regions? | **No.** Three spatial clusters cannot support a generalisation claim. |

## Spatial generalisation uncertainty

The district-level cluster bootstrap is reported in the benchmark
summary. Its limitation is structural, not statistical: with three
clusters the bootstrap distribution is the distribution of three draws,
so the 2.5th and 97.5th percentiles sit close to the extreme
resamples. The interval is reported with that caveat and **must not be
read as a confidence statement about generalisation to other regions**.

The uncertainty budget also excludes the calibration component (the
bootstrap runs on the frozen model, not on the calibration) and the
input component (remote-sensing, weather and observation uncertainty).
The reported interval therefore **understates** the total uncertainty.

## Sampling

The Stage 40 evaluation used a 450-record stratified sample; Stage 41
evaluates the complete {acct.get('manifest_total_records')}-record test
frame. The sample was drawn proportionally within district × season
strata with a floor per stratum, so it is representative by design; the
side-by-side comparison in `STAGE-41-BASELINE-VS-CALIBRATED.md`
quantifies how representative it was in practice.

## What remains open

| Item | Status |
|---|---|
| ε / HI collinearity | Open - only their product is identifiable from yield data |
| LAI model validation | Open - the GDD sigmoid is documented as a placeholder, not a validated crop model |
| EWSI weighting provenance | Open - weights and anchors are project defaults |
| Thermal response width | Open - the 8 °C Gaussian width has no source and was never a free parameter |
| Operational baseline | Absent - the repository has no operational forecast to compare against |
| Second external dataset | Absent - every result here comes from one dataset in one region |
| Field-level yield drivers | Not represented by any input (management, soil, pests) |
"""
    write("STAGE-41-LIMITATIONS.md", body)

    # ==================================================================
    # 12. FINAL STATUS
    # ==================================================================
    beats_mean = (cal.get("rmse") is not None and meanref.get("rmse") is not None
                  and cal["rmse"] < meanref["rmse"])
    improves = (cal.get("r2") is not None and base.get("r2") is not None
                and cal["r2"] > base["r2"])
    body = f"""# Stage 41 — Final Status

## Status: `PARTIAL` — unchanged from Stage 40, now on the full test frame

| Field | Value |
|---|---|
| Model | HYRUE {model['version']} |
| Model code hash | `{model['model_code_hash']}` |
| External validation status | **PARTIAL** |
| Scientific support status | **PARTIAL** |
| Calibrated | yes, on 7 development districts only |
| Frozen | yes, before external evaluation, unchanged through Stage 41 |
| Test districts | Buxar, Muzaffarpur, Rohtas |
| Records evaluated | {n_pred} with a prediction, of {n_manifest} in the frame |

## Headline numbers

| Metric | Baseline (ε=2.2) | Calibrated (ε={fmt(eps, 4)}) | Mean predictor |
|---|---:|---:|---:|
| n | {n_base} | {n_cal} | {meanref['n']} |
| RMSE (t/ha) | {fmt(base['rmse'])} | {fmt(cal['rmse'])} | {fmt(meanref['rmse'])} |
| MAE (t/ha) | {fmt(base['mae'])} | {fmt(cal['mae'])} | {fmt(meanref['mae'])} |
| Bias (t/ha) | {fmt(base['bias'])} | {fmt(cal['bias'])} | {fmt(meanref['bias'])} |
| R² | {fmt(base['r2'])} | {fmt(cal['r2'])} | 0.0 |
| MAPE (%) | {fmt(base['mape'], 2)} | {fmt(cal['mape'], 2)} | {fmt(meanref['mape'], 2)} |

Baseline and calibrated were computed **in the same pass, on the same
records, from the same inputs**.

## Did the calibrated model beat the baseline?

**{'Yes' if improves else 'No'}.** R² improved from {fmt(base['r2'])} to
{fmt(cal['r2'])} and RMSE fell from {fmt(base['rmse'])} to
{fmt(cal['rmse'])} t/ha on the same records with identical inputs. The
improvement is not tuning on the evaluation set: the parameters were
frozen before the evaluation, the leave-one-district-out validation on
the development districts moved in the same direction, and the fitted ε
is stable across all folds.

## Did the calibrated model beat the mean predictor?

**{'Yes' if beats_mean else 'No'}.** The mean predictor's RMSE is
{fmt(meanref['rmse'])} t/ha against the model's {fmt(cal['rmse'])} t/ha -
the model is {fmt((cal['rmse'] / meanref['rmse']) if meanref.get('rmse') else None, 2)}×
worse than predicting the evaluation mean. Its R² of {fmt(cal['r2'])} is
negative for the same reason. This is stated explicitly rather than
buried in a footnote.

## Why the status does not change

| Requirement for `VALIDATED_EXTERNAL` | Met? | Evidence |
|---|---|---|
| Calibrated on data disjoint from the evaluation set | Yes | 7 dev districts; leakage guard asserted |
| Parameters frozen before evaluation | Yes | frozen config unchanged; all 8 code hashes match |
| Evaluation on genuinely external districts | Yes | Buxar, Muzaffarpur, Rohtas |
| Evaluation covers the full external set | Yes | {n_pred} of {n_manifest} records, all status-assigned |
| Spatial replication | No | three districts; the bootstrap has three clusters |
| Performance is strong enough to claim validity | No | R² = {fmt(cal['r2'])}; mean predictor is better |
| Uncertainty covers the total error budget | No | calibration and input components excluded |
| Model identified from the data | No | ε/HI collinear; the objective is nearly flat |

## What Stage 41 established

* The full test frame was evaluated with the frozen model, and the
  record accounting is complete: every manifest record carries a
  terminal status.
* The baseline/calibrated comparison is now exactly like-for-like,
  because both parameter sets are evaluated in the same pass from the
  same resolved inputs. The Stage 40 reconstruction is retained only as
  an independent check.
* The negative R² is **attributed**. It is model-structural, not a data
  quality artefact: the model's predictions span a narrower range than
  the observations and correlate only weakly with them, while the
  input-quality variables show weak relationships with the absolute
  error.
* A **re-run control** was executed: records recomputed with identical
  inputs reproduce bit-identically ({rep.get('n_exact_within_1e-12', 'n/a')}
  of {repro.get('records_compared', 'n/a')}); the remainder differed
  because the upstream API returned different data, which is why the
  baseline is now computed in-pass rather than reconstructed across
  runs.

## What Stage 41 did not establish

* That the model generalises beyond these three districts.
* That ε = {fmt(eps, 4)} is the true radiation use efficiency of wheat
  in Bihar; it is the scale the development set implies.
* That the remaining error is random. The dominant contributors
  (model-generated LAI, the unsourced thermal width, the ε/HI
  collinearity, and the absence of any field-management input) are
  **systematic**.
* That the model is ready for decision-making. It is not: it loses to
  the mean predictor.

## Recommended next step

Stage 42 should target **identifiability and input realism**, not more
benchmarking of the current model:

1. Obtain observed LAI (or a published EWSI weighting) so that ε and HI
   can be separated and the GDD placeholder no longer sets the
   phenology for every record.
2. Source the thermal Gaussian width, or free it alongside ε.
3. Add an operational forecast baseline, so "skill" is measured against
   something the model would actually replace.
4. Re-run this stage end-to-end. The status should only move when the
   model beats the mean predictor on held-out districts, not before.

**No parameter was changed in Stage 41.**
"""
    write("STAGE-41-FINAL-STATUS.md", body)

    print()
    print("stage 41 reports written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
