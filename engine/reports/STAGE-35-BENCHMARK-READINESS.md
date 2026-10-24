# Stage 35 — Benchmark Readiness

## Current Status: PARTIALLY_EVALUATED

### What Works (Verified with Real Data)

| Component | Status | Data Source |
|---|---|---|
| Weather (Tmin/Tmax/precip/shortwave) | ✅ Working | Open-Meteo ERA5-Land |
| VPD (dewpoint/RH-based) | ✅ Working | Open-Meteo ERA5-Land |
| Soil moisture (3 layers) | ✅ Working | Open-Meteo ERA5-Land |
| PAR (shortwave-based) | ✅ Working | Open-Meteo ERA5-Land |
| Satellite NIR/SWIR (Sentinel-2 L2A) | ✅ Working | Planetary Computer STAC |
| NDMI computation | ✅ Working | Sentinel-2 B8A/B11 |
| EWSI composite (strict policy) | ✅ Working | NDMI + VPD + soil moisture |
| HYRUE seasonal with EWSI | ✅ Working | All real inputs |
| CIMMYT data loading | ✅ Working | 5,689 records, 10 districts |
| Spatial split protocol | ✅ Defined | 3 test / 7 dev districts |
| Leakage audit | ✅ CLEAN | No site/field/season overlap |

### What Remains

| Item | Status | Blocker |
|---|---|---|
| EWSI calibration (weights, anchors) | ⬜ Pending | Requires dev-set calibration, not test-set tuning |
| Full benchmark execution | ⬜ Pending | Time-prohibitive for 5,689 records in one session |
| Validation metrics (RMSE, MAE, R², etc.) | ⬜ Pending | Requires executed test predictions |
| Baseline computation | ⬜ Pending | Requires dev-set mean yield |
| Bootstrap uncertainty | ⬜ Pending | Requires matched pairs |

### Path to COMPLETED

1. Calibrate EWSI parameters on dev districts
2. Execute HYRUE on test districts with frozen EWSI
3. Compute validation metrics vs observed yields
4. Compute baseline from dev data
5. Run cluster bootstrap for uncertainty
6. Transition status to COMPLETED
7. VALIDATED_EXTERNAL only with independent scientific evidence (not just successful execution)

### Status Transitions

- **READY** → pipeline ready (achieved in Stage 34)
- **RUNNING** → execution in progress (pilot completed)
- **PARTIALLY_EVALUATED** → current status (pilot done, full benchmark pending)
- **COMPLETED** → full benchmark executed (not yet)
- **VALIDATED_EXTERNAL** → independent scientific evidence (not yet — requires more than successful execution)

## Files

- `engine/reports/data/stage35_pilot_single.json`
