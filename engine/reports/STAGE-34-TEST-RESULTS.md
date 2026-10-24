# Stage 34 — Test Results

## Test Summary

**42 tests, 42 passed, 0 failed.**

Test file: `engine/tests/test_stage34_ewsi_pipeline.py`

## Test Coverage (Stage 34 Part L — 30 required tests)

| # | Test | Status |
|---|------|--------|
| 1 | NDMI with valid values | PASSED |
| 2 | NDMI with denominator zero | PASSED |
| 3 | NDMI with invalid reflectance | PASSED |
| 4 | Scaling and offset control | PASSED |
| 5 | Band alignment control | PASSED |
| 6 | Cloud mask control | PASSED |
| 7 | VPD with valid T and Td | PASSED |
| 8 | VPD with Kelvin input | PASSED |
| 9 | VPD with Td > T | PASSED |
| 10 | VPD with invalid RH | PASSED |
| 11 | Volumetric soil moisture to stress index | PASSED |
| 12 | FC == WP control | PASSED |
| 13 | Soil moisture out of range | PASSED |
| 14 | EWSI with all three valid | PASSED |
| 15 | EWSI with missing component in strict | PASSED |
| 16 | EWSI with estimated in allow_estimated | PASSED |
| 17 | Weight sum control | PASSED |
| 18 | Negative weight control | PASSED |
| 19 | EWSI out of [0,1] control | PASSED |
| 20 | Date and timezone control | PASSED |
| 21 | Data outside growing season | PASSED |
| 22 | Satellite interpolation control | PASSED |
| 23 | Long temporal gap control | PASSED |
| 24 | API timeout control | PASSED |
| 25 | Invalid API response | PASSED |
| 26 | Cache control | PASSED |
| 27 | Provenance control | PASSED |
| 28 | Reproducibility control | PASSED |
| 29 | EWSI-HYRUE integration | PASSED |
| 30 | No model parameter change | PASSED |

### Additional Tests (12)

QualityStatus enum, quality helpers, quality_rank, VPD stress transform,
NDMI stress transform, soil stress FC-only, relative anomaly, root-zone
weighted moisture, satellite source defaults, quality mask result,
rate limiter, cache TTL expiry.

## Regression

Stage 33 tests (49 tests) continue to pass — no regressions.

## Lint

`ruff check` passes on all new/modified files with 0 violations.
Import guard (`tools/detect_imports.py`) passes with 0 violations.
