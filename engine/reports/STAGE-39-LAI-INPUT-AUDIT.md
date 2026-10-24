# Stage 39 — LAI Input Audit

## Audit Scope

Where LAI values enter the HYRUE pipeline, how they are prioritised, and
whether a silent constant fallback can reach the benchmark.

## LAI Input Hierarchy

`_resolve_lai_with_policy()` in `engine/hydroma/eval/seasonal_predictor.py`:

| Priority | Source | Provenance recorded | Status |
|---|---|---|---|
| 1 | `request.lai_array` — directly observed LAI | `observed` | observed |
| 2 | `request.ndvi_array` — NDVI → empirical LAI (`3.5 x NDVI`) | `model_generated` | estimated |
| 3 | GDD model (`LAIModel`, thermal time) | `model_generated` | estimated |
| 4 | none | `missing` | missing |

## Constant LAI Fallback — Audit Result

**The Stage 35 pilot error was again in the pilot script, not the library.**

The pilot script hard-coded:

```python
lai_vals = np.full(n_days, 3.0)     # constant, whole season
```

In the library:

* `_resolve_lai_with_policy()` has **no constant fallback** — priority 3
  is the GDD model, and priority 4 is `missing`.
* `build_seasonal_climate_inputs()` (par_pipeline) also has no constant
  fallback: when neither `lai_array` nor `ndvi_array` is supplied and the
  GDD model cannot run, `"lai"` is added to `missing_fields`.
* `compute_hyrue_seasonal()` raises `WeatherUnavailable` when required
  inputs are missing, unless `allow_legacy_fallback=True`.
* The **only** constant-LAI path is `_run_legacy_fallback()`, which is
  reached solely via the explicit `allow_legacy_fallback=True` flag. That
  flag is set only for `InputSourcePolicy.DIAGNOSTIC`:

  ```python
  allow_legacy_fallback=(
      request.input_source_policy == InputSourcePolicy.DIAGNOSTIC
  )
  ```

## GDD Model Availability

`build_seasonal_climate_inputs()` imports the GDD model lazily
(`from engine.hydroma.simulation.lai_model import LAIModel, LAIModelConfig`)
and calls `model.compute_with_provenance(t_mean_for_lai)`. The model needs
only the daily mean temperature, which the weather source always provides.

**However**: Stage 37 changed the library so that LAI is computed from
the GDD model when neither observed LAI nor NDVI is available. In the
Stage 35 pilot this path was not taken, because the pilot script
supplied its own constant LAI.

## Impact on the Pilot Error

| Component | Stage 35 pilot | Stage 37 corrected |
|---|---|---|
| PAR | shortwave (2x too large) | shortwave x 0.5 (correct) |
| LAI | constant 3.0 | GDD model (crop-stage dependent) |
| EWSI | VPD + soil moisture, NDMI missing | same |
| Predicted | 10.899 t/ha | 4.807 t/ha |
| Error | +63.2% | −28.0% |

Both the PAR and the LAI contributions were corrected. The residual
−28% is attributable to uncalibrated parameters.

## LAI Provenance in Benchmark Output

`RecordResult.lai_status` records the LAI source for every record, and
`input_quality_summary.json` aggregates the counts, so the report can
distinguish records that used observed LAI from records that used an
estimated (GDD) LAI.

## Scientific Caveat

The empirical NDVI→LAI coefficient (3.5) and the GDD model parameters
are **not** validated for wheat in eastern India. They are recorded as
`estimated` and are candidates for the development-set calibration.

## Conclusion

| Check | Result |
|---|---|
| Constant LAI in the benchmark main path | Not present |
| Constant LAI reachable only via explicit DIAGNOSTIC policy | Confirmed |
| LAI provenance preserved per record | Confirmed |
| LAI missing handled as a missing input, not zero | Confirmed |
