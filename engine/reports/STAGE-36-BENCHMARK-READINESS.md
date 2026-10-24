# Stage 36 — Benchmark Readiness

## Current Status: PARTIALLY_EVALUATED

## What Works (Verified with Real Data)

| Component | Status | Data Source |
|---|---|---|
| Weather (Tmin/Tmax/precip/shortwave) | Working | Open-Meteo ERA5-Land |
| VPD (dewpoint/RH-based) | Working | Open-Meteo ERA5-Land |
| Soil moisture (3 layers) | Working | Open-Meteo ERA5-Land |
| PAR (shortwave-based) | Working | Open-Meteo ERA5-Land |
| Satellite NIR/SWIR (Sentinel-2 L2A) | Working | Planetary Computer STAC |
| NDMI computation | Working | Sentinel-2 B8A/B11 |
| EWSI composite (strict policy) | Working | NDMI + VPD + soil moisture |
| HYRUE seasonal with EWSI | Working | All real inputs |
| CIMMYT data loading | Working | 5,689 records, 10 districts |
| Spatial split protocol | Defined | 3 test / 7 dev districts |
| Leakage audit | CLEAN | No site/field/season overlap |
| Parameter registry | Defined | 17 parameters registered |
| Split manifest | Verified | No district/record overlap |

## What Remains

| Item | Status | Blocker |
|---|---|---|
| EWSI calibration (weights, anchors) | Pending | Requires dev-set calibration |
| Full benchmark execution | Pending | Time-prohibitive for 1,722 test records |
| Validation metrics (RMSE, MAE, R², etc.) | Pending | Requires executed test predictions |
| Baseline computation | Pending | Requires dev-set mean yield |
| Bootstrap uncertainty | Pending | Requires matched pairs from test execution |
| Filesystem limitation | Pending | Python cannot import from models/, simulation/ |

## Path to COMPLETED

1. Resolve filesystem limitations (Python import from models/, simulation/)
2. Calibrate EWSI parameters on development districts
3. Freeze parameters in stage36_frozen_model_config.json
4. Execute HYRUE on test districts with frozen parameters
5. Compute validation metrics vs observed yields
6. Compute baseline from dev data
7. Run cluster bootstrap for uncertainty
8. Transition status to COMPLETED

## Path to VALIDATED_EXTERNAL

Requires independent scientific evidence beyond successful execution:
- Independent validation dataset
- Published validation protocol
- Scientific peer review of EWSI index
- Generalization beyond Bihar/eastern Uttar Pradesh, India

## Files

- All Stage 36 reports
- `engine/reports/data/stage36_frozen_model_config.json`
- `engine/reports/data/stage36_benchmark_split_manifest.json`
