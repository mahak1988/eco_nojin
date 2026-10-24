# Stage 37 — LAI Input Audit

## Audit Finding

The Stage 36 pilot used a constant `LAI = 3.0 m²/m²` for the entire growing season. This misrepresents wheat canopy development (near zero at emergence, peaking at anthesis, senescing before harvest).

## Current LAI Pipeline (VERIFIED CORRECT)

`_resolve_lai_with_policy()` in `seasonal_predictor.py` uses the following priority:

| Priority | Source | Method |
|---|---|---|
| 1 | `request.lai_array` | Directly observed LAI (field/satellite) |
| 2 | `request.ndvi_array` | Empirical LAI = 3.5 × NDVI |
| 3 | GDD model | `LAIModel` with thermal time |
| 4 | None | Marked as missing |

No constant LAI=3.0 fallback exists in the main code path. If LAI is unavailable:
- `input_quality` is set to `"partial"` or `"unavailable"`
- `compute_hyrue_seasonal()` raises `WeatherUnavailable` unless `allow_legacy_fallback=True`

## Legacy Fallback (EXPLICIT OPT-IN ONLY)

`_run_legacy_fallback()` in `par_pipeline.py` uses scalar means with `lai_scalar = 3.0` as default when LAI is missing. This is only invoked when `allow_legacy_fallback=True` — an explicit opt-in that is NOT used in benchmark execution.

## LAI Provenance

All LAI sources carry provenance metadata:

| Source | Quality Status | Scientific Status |
|---|---|---|
| Direct observation | `observed` | `observed` |
| NDVI empirical | `model_generated` | `estimated` |
| GDD model | `model_generated` | `estimated` |
| Missing | `missing` | `missing` |

## Recommendation

For benchmark execution, LAI should be provided per-record from either:
1. Direct field measurements (highest quality)
2. Satellite NDVI-derived LAI (empirical, `3.5 × NDVI`)
3. GDD model (model-generated, clearly labeled)

Constant LAI=3.0 must NOT be used as an implicit fallback in benchmark execution.

## Files

- `engine/hydroma/eval/seasonal_predictor.py` — `_resolve_lai_with_policy()` (already correct)
- `engine/hydroma/simulation/par_pipeline.py` — `_run_legacy_fallback()` (explicit opt-in only)
- `engine/hydroma/simulation/lai_model.py` — LAI model (GDD-based)
