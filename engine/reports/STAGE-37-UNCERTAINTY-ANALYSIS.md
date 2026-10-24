# Stage 37 — Uncertainty Analysis

## Method

Cluster bootstrap at the district level to estimate uncertainty in HY-RUE yield predictions. District-level resampling accounts for spatial correlation of records within the same district.

## Minimum Districts

At least 3 independent districts are required for valid cluster bootstrap. The test set has exactly 3 districts (Buxar, Muzaffarpur, Rohtas), which is the minimum but provides limited statistical power.

## Status

**Status: NOT COMPLETED ON REAL DATA**

Uncertainty analysis requires completed benchmark execution on test districts. With only 3 test districts, bootstrap uncertainty estimates will have limited precision.

## Bootstrap Procedure (When Data Available)

1. Resample districts with replacement (Buxar, Muzaffarpur, Rohtas)
2. Include all records from each sampled district
3. Compute RMSE, MAE, Bias, R² on the bootstrap sample
4. Repeat 1,000 times
5. Report mean and 95% CI for each metric

## Limitation

With only 3 independent districts, the bootstrap will have very limited statistical power. The uncertainty intervals will be wide and should be interpreted with caution.

## Files

- `engine/hydroma/eval/hyrue_uncertainty_analysis.py` — cluster bootstrap implementation
- `engine/reports/data/stage36_uncertainty_results.json` — uncertainty results (when available)
