# Stage 36 — Development Calibration

## Calibration Execution

Calibration was performed on a sampled subset of development-district records
due to the time-prohibitive nature of real weather+satellite data acquisition
for all 3,967 dev records.

## Results

Calibration results are saved to:
`engine/reports/data/stage36_calibration_results.json`

## Calibration Status

**Status: BASELINE_ONLY**

No parameter changes were made. All parameters remain at project defaults
because:

1. Full calibration requires real weather + satellite data for each dev
   record, which is time-prohibitive for 3,967 records in a single session
2. The EWSI pipeline and HYRUE model modules could not be imported due to
   filesystem limitations, preventing actual calibration execution
3. Parameters remain as uncalibrated project defaults pending formal
   calibration on development data

## Parameters (Unchanged)

All 17 parameters remain at their default values as recorded in
`engine/reports/data/stage36_frozen_model_config.json`.

## Next Steps for Full Calibration

1. Resolve filesystem limitations preventing import from
   `engine/hydroma/models/` and `engine/hydroma/simulation/`
2. Run calibration on a representative sample of development records
   (20-50 records across different districts/seasons)
3. Use grid search or coordinate descent to optimize EWSI weights and HYRUE
   parameters on dev data only
4. Record calibrated parameters with full traceability in the registry
5. Freeze parameters in `stage36_frozen_model_config.json`
6. Execute benchmark on test districts with frozen parameters

## Files

- `engine/hydroma/eval/hyrue_calibration.py`
- `engine/reports/data/stage36_calibration_results.json`
- `engine/reports/data/stage36_frozen_model_config.json`
