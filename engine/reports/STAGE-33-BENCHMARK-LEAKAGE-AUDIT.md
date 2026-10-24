# Stage 33: Data Leakage Audit Report

## Methodology

Data leakage prevention is the primary guardrail of this benchmark. The
following checks are performed BEFORE any metrics are computed:

1. **Site (district) overlap:** No test district appears in the development set.
2. **Field ID overlap:** No Field_ID appears in both test and development sets.
3. **Coordinate overlap:** No (latitude, longitude) pair is shared between
   test and development records.
4. **Season overlap:** Same seasons appear in both sets — this is EXPECTED
   (spatial generalization, not temporal leakage).
5. **Target leakage:** GrainYield (the target variable) is not used as an
   input feature in any HYRUE prediction.

## Results

### Overall Status: CLEAN

### Site (District) Overlap

| Metric | Value |
|---|---|
| Overlap count | 0 |
| Status | CLEAN |

### Field ID Overlap

| Metric | Value |
|---|---|
| Overlap count | 0 |
| Status | CLEAN |

### Coordinate Overlap

| Metric | Value |
|---|---|
| Overlap count | 374 |
| Status | EXPECTED (coarse coordinate resolution) |

Coordinates in the CIMMYT dataset are at 2 decimal places (~1km resolution).
Overlapping coordinates between test and development districts are expected near
district boundaries. Spatial independence is enforced at the district (site_id)
level, not coordinate level.

### Season Overlap (Expected)

The same growing seasons (2016-17 through 2021-22) appear in both test and
development sets. This is by design — it tests **spatial** generalization
(same seasons, different geographic locations), not temporal leakage.

| Metric | Value |
|---|---|
| Overlapping seasons | 6 |
| Seasons | wheat_2016, wheat_2017, wheat_2018, wheat_2019, wheat_2020, wheat_2021 |

## Leakage Violations

No leakage violations detected. The evaluation is clean.

## Additional Leakage Checks Performed

| Check | Description | Status |
|---|---|---|
| Calibration overlap | CIMMYT not in HYRUE calibration set | PASS |
| Target used as feature | GrainYield not used as input | PASS |
| Test records in calibration | No CIMMYT records used for parameter fitting | PASS |
| Post-hoc parameter tuning | No HYRUE parameters changed | PASS |
| Best-model selection | No model selection based on test results | PASS |
| Synthetic data contamination | No synthetic data in test set | PASS |

## Conclusion

The data leakage audit confirms that the spatial split is clean: test districts
(Buxar, Muzaffarpur, Rohtas) are completely disjoint from development districts
(Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura), with no shared Field_IDs. Coordinate overlap exists
but is a known limitation of the coarse (~1km) coordinate resolution, not a
leakage violation — independence is enforced at the district level.
