# Stage 33: Benchmark Protocol Definition

## Summary

| Item | Value |
|---|---|
| **Benchmark ID** | BENCH-STAGE33 |
| **Benchmark Version** | 1.0 |
| **Model** | HY-RUE v2.0.0 |
| **Dataset** | cimmyt_wheat_eastern_india_10.71682/10549424 v1.0.0 |
| **Calibration Dataset** | hydromas_calibration_v1 (HY-RUE internal — NOT CIMMYT) |
| **Evaluation Dataset** | cimmyt_wheat_eastern_india_10.71682/10549424 (CIMMYT) |
| **Evaluation Target** | spatial_and_temporal |
| **Split Method** | spatial_grouped_holdout |
| **Unit of Independence** | district |
| **Protocol Status** | COMPLETE |

## A. Dataset Verification

| Check | Result |
|---|---|
| File SHA-256 verified | YES |
| Hash matches Stage 32 | True |
| File size | 1609655 bytes |

## B. Evaluation Scope

- **Crop:** Wheat (Rabi Season)
- **Region:** Bihar and Eastern Uttar Pradesh, India
- **Seasons:** 2016-17 to 2021-22 (6 seasons)
  - **Sites:** 10 districts
- **Test Districts:** Buxar, Muzaffarpur, Rohtas
- **Development Districts:** Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura
- **Test Records:** 1722
- **Development Records:** 3967

## C. Spatial Split Design

The spatial split is the primary evaluation mechanism. Districts are assigned
to development or test sets deterministically (seed=42). No within-district
splitting is performed, ensuring spatial independence.

| District | Records | Role |
|---|---|---|
| Begusarai | 380 | DEVELOPMENT |
| Bhojpur | 632 | DEVELOPMENT |
| Buxar | 709 | TEST |
| Deoria | 669 | DEVELOPMENT |
| EastChamparan | 825 | DEVELOPMENT |
| Kushinagar | 556 | DEVELOPMENT |
| Lakhisarai | 347 | DEVELOPMENT |
| Madhepura | 558 | DEVELOPMENT |
| Muzaffarpur | 427 | TEST |
| Rohtas | 586 | TEST |

## D. Input Source Policy

### Primary Evaluation: STRICT

The STRICT policy requires:
- **PAR:** Measured (field) or satellite-retrieved — NOT estimated
- **LAI:** Observed (field or satellite) — NOT model-generated
- **EWSI:** Observed — NOT model-generated
- **Temperature:** Real daily data (fetched from weather API)

### Secondary Evaluation: ALLOW_ESTIMATED_INPUTS

The ALLOW_ESTIMATED_INPUTS policy permits:
- **PAR:** Estimated via 0.5 shortwave conversion (Monteith & Unsworth 2013)
- **LAI:** GDD model-generated (LAIModel)
- **EWSI:** Must still be provided — NOT available from any source

## E. Key Constraints

1. No HYRUE parameters, biological coefficients, EWSI weights, or PAR conversion
   coefficients are changed using test data.
2. No synthetic data is substituted for real data without explicit labeling.
3. Monthly-to-daily conversion of temperature is NOT performed without a
   documented method.
4. STRICT and ALLOW_ESTIMATED results are kept in separate tables.
5. Random record-level splitting between train/test is prohibited.

## F. Baseline

The baseline is the mean observed yield from the development set
(spatially independent districts). The baseline does NOT use any test-set
information for its value.

## G. Uncertainty Method

Bootstrap at the spatial unit of independence (district level), with
1,000 resamples and 95% confidence intervals, when >= 2 independent
districts have successful predictions.
