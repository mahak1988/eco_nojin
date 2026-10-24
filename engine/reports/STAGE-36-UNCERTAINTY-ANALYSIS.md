# Stage 36 — Uncertainty Analysis

## Method

Cluster bootstrap at the district level to estimate uncertainty in HY-RUE
yield predictions. District-level resampling accounts for spatial
correlation of records within the same district.

## Minimum Districts

At least 3 independent districts are required for valid cluster bootstrap.
With only 3 test districts (Buxar, Muzaffarpur, Rohtas), bootstrap
uncertainty estimates will have limited precision.

## Results

Uncertainty results are saved to:
`engine/reports/data/stage36_uncertainty_results.json`

## Status

**Status: NOT COMPLETED ON REAL DATA**

Uncertainty analysis requires completed benchmark execution on test
districts. With only 3 test districts, the bootstrap will have limited
statistical power.

## Files

- `engine/hydroma/eval/hyrue_uncertainty_analysis.py`
- `engine/reports/data/stage36_uncertainty_results.json`
