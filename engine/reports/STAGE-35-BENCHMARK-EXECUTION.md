# Stage 35 — Benchmark Execution

## Execution Protocol

Following Stage 33 spatial split:
- **Test districts (3):** Buxar, Muzaffarpur, Rohtas — 1,722 records
- **Development districts (7):** remaining 7 districts — 3,967 records
- **No field/site/season overlap** between test and dev (leakage audit: CLEAN)

## Execution Status

### Pilot (Completed ✅)
- 1 record (Buxar, 2016-17) executed end-to-end with real data
- All EWSI components from real sources (weather + satellite)
- HYRUE prediction computed: 10.899 t/ha vs observed 6.680 t/ha

### Full Benchmark Execution
**NOT YET EXECUTED** on full dataset.

Reasons:
1. **Performance:** Full pipeline (weather + satellite download per record) for 5,689 records would require extensive COG downloads and API calls. Time-prohibitive in a single session.
2. **EWSI calibration:** NDMI_ref, NDMI_crit, VPD_low, VPD_high, FC, WP are uncalibrated project defaults. Benchmark metrics would not be scientifically meaningful without calibration on development data.
3. **No model parameter tuning** — per Stage 35 rule #6, no parameters tuned on test data.

## What Would Be Required for Full Execution

1. **Development phase:** Calibrate EWSI weights and anchors on dev districts (3,967 records)
2. **Test phase:** Run HYRUE with frozen EWSI on test districts (1,722 records)
3. **Metrics:** RMSE, MAE, Bias, R², MAPE on test predictions vs observed
4. **Baseline:** Mean yield from dev set as naive baseline
5. **Uncertainty:** Cluster bootstrap at district level (10 districts → adequate for spatial generalization)

## Benchmark Status

**PARTIALLY_EVALUATED**

- Pipeline verified with real data on 1 pilot record
- Full benchmark not yet executed (calibration + scale-up pending)
- No validation-grade metrics computed yet

## Files

- `engine/reports/data/stage35_pilot_single.json`
