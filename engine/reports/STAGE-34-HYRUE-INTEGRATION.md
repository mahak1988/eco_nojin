# Stage 34 — HYRUE Integration

## EWSI-HYRUE Contract Verification

### f_water = 1 - EWSI

**Confirmed.** `engine/hydroma/models/hyrue.py:267`:

```python
f_water = 1 - ewsi_arr
```

EWSI semantics (hyrue.py:337-342): EWSI is a stress index in [0, 1]
where 0 = no water stress, 1 = severe water stress. f_water = 1 means
no stress, f_water = 0 means complete water limitation.

### HYRUE Seasonal Mode

EWSI integrates with HYRUE seasonal mode (array inputs):

```
B_day = PAR * f_IPAR * epsilon * f_water * f_temp
B_season = sum(B_day)
Y_t_ha = B_season * HI / 100
```

### Integration Test

`test_ewsi_hyrue_integration` (test_stage34_ewsi_pipeline.py) verifies:
1. EWSI computed from synthetic inputs
2. EWSI = 0 → f_water = 1 → HYRUE produces positive yield
3. Full provenance chain preserved

### Provenance Tracking

EWSI output provenance includes:
- source_model, source_date, unit, valid_range
- quality_status, method, reference, scientific_status
- weights (effective and original)
- missing_fields, component_provenance (per-component status)
- computation_policy (strict / allow_estimated)

All fields flow through `SeasonalClimateInputs` → `PredictionResult`
→ `OperationalReport`.

## Files

- `engine/hydroma/models/hyrue.py` — HYRUE model (f_water = 1 - EWSI)
- `engine/hydroma/simulation/ewsi_pipeline.py` — EWSI pipeline
- `engine/hydroma/simulation/par_pipeline.py` — SeasonalClimateInputs
- `engine/hydroma/eval/seasonal_predictor.py` — Pipeline orchestrator
- `engine/hydroma/eval/prediction.py` — PredictionResult types
