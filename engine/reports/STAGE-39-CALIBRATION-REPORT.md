# Stage 39 — Development Calibration

## Status

**NOT EXECUTED** — the calibration machinery is implemented and the leakage
guard is enforced in code, but the calibration itself was not run.

## Why it was not run

Calibrating on the development districts requires, for each of the 3,967
development records:

* one Open-Meteo archive request (measured: ~4 s), and
* one Sentinel-2 season fetch (measured after the Stage 39 windowed-read
  optimisation: ~52 s).

That is ~58 s per record, i.e. **~64 hours** for the development set —
before any parameter search, which multiplies this by the number of
candidate parameter sets evaluated.

The Stage 39 mandate is to reduce runtime *without* reducing data quality
or dropping records. Both of those options were exhausted:

| Optimisation | Effect |
|---|---|
| Windowed raster read (Stage 39) | 10x faster satellite sampling (10+ min -> 52 s per season) |
| Persistent weather/satellite cache (Stage 38) | avoids repeat fetches for shared coordinates |
| Resumable runner (Stage 38) | no work lost to interruption |
| Parallel workers | **not** enabled: the Stage 38 instruction requires the API rate limit to be measured and respected first, and a parallel run would multiply the request rate against Planetary Computer without that measurement |
| Sub-sampling the development set | **rejected**: the Stage 38 instruction states that a sub-sample "is not an unconditional replacement for full calibration"; using one would make the resulting parameters un-generalisable |
| Reducing data quality (fewer bands, no cloud mask, coarser resolution) | **rejected**: explicitly forbidden |

## Calibration Protocol (Implemented)

`engine/hydroma/eval/hyrue_calibration.py` and
`engine/hydroma/eval/stage39_benchmark.py`:

1. `load_dev_records()` — reads the CIMMYT dataset and filters to the
   development districts from the split manifest. Test districts are
   filtered out by the manifest, not by a hard-coded list.
2. `run_hyrue_on_dev_record()` — for each record: fetch weather, fetch
   satellite, compute EWSI, run HYRUE, record the outcome.
3. `run_development_calibration(dev_records, test_districts)` — rejects
   any record whose district is a test district, computes the dev
   metrics, and reports `n_rejected_test_district`.
4. `compute_benchmark_metrics()` — RMSE / MAE / Bias / R² / MAPE with
   sample sizes.
5. `cluster_bootstrap_uncertainty()` — district-level resampling.

## Objective Function

RMSE on development-district records:

```
RMSE = sqrt( (1/n) * sum_i (y_hat_i - y_i)^2 )
```

RMSE is chosen because it penalises large errors, which matter for a
yield model used in a food-security context. MAE is reported alongside
because it is less sensitive to outliers; the two are read together so
that a RMSE/MAE divergence would be visible.

## Parameters Eligible for Calibration

| Parameter | Group | Range | Identifiable? |
|---|---|---|---|
| epsilon | HYRUE biomass | 0.5 – 5.0 g/MJ IPAR | Poorly (see identifiability report) |
| hi | HYRUE harvest | 0.2 – 0.6 | Poorly |
| k | HYRUE structure | 0.3 – 1.0 | Well |
| lai_max | HYRUE structure | 3.0 – 8.0 | Poorly |
| t_opt | HYRUE thermal | 10 – 30 °C | Moderately |
| t_min / t_max | HYRUE thermal | see registry | Poorly (rarely binding) |
| ewsi_weight_ndmi | EWSI weights | 0.0 – 1.0 (sum 1) | Poorly |
| ewsi_weight_vpd | EWSI weights | 0.0 – 1.0 (sum 1) | Poorly |
| ewsi_weight_soil | EWSI weights | 0.0 – 1.0 (sum 1) | Poorly |

## Parameters Excluded from Calibration

`thermal_gaussian_width`, `ndmi_ref`, `ndmi_crit`, `vpd_low`, `vpd_high`,
`soil_field_capacity` have no published source for wheat in eastern
India. They are **not** calibrated, because fitting them to the
development set would convert an unvalidated assumption into a
dataset-specific value while removing the ability to distinguish a real
signal from an artefact. They remain at their defaults and are recorded
as `UNVALIDATED`.

`shortwave_to_par_factor` is a unit-conversion constant, not a model
parameter, and is not calibrated.

## Sensitivity of the Result to This Status

Because the calibration was not executed, the frozen model
(`stage37_frozen_model_config.json`) carries the **uncalibrated
defaults**. Any benchmark metrics obtained with it are therefore
measurements of the *default* model, not of a calibrated model, and the
metrics must be reported as such.

## Conclusion

| Item | Status |
|---|---|
| Calibration machinery | implemented, leakage-guarded, tested |
| Calibration execution | **not performed** (time) |
| Parameters calibrated | none |
| Frozen model | defaults, explicitly labelled `baseline_only` |
| Test set | untouched by the calibration path (enforced in code) |
