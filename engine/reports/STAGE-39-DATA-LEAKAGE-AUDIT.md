# Stage 39 — Data Leakage Audit

## Split Verification

Verified directly from the manifest and the source dataset — not copied
from the Stage 36 report.

| Attribute | Value |
|---|---|
| Dataset | CIMMYT eastern India wheat |
| Total records | 5,689 |
| Development records | 3,967 (7 districts) |
| Test records | 1,722 (3 districts) |
| Development districts | Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura |
| Test districts | Buxar, Muzaffarpur, Rohtas |
| Grouping column | `District` |
| Manifest hash | verified (recomputed hash matches stored hash) |

## Leakage Checks

| Check | Method | Result |
|---|---|---|
| District overlap between dev and test | set intersection | **PASS** — empty |
| Record-ID overlap between dev and test | set intersection | **PASS** — empty |
| All 10 districts accounted for | set union vs dataset | **PASS** |
| Manifest hash integrity | recompute and compare | **PASS** |
| Record counts match manifest | count vs manifest | **PASS** — 3,967 / 1,722 |
| Test data used in calibration | `run_development_calibration()` rejects any record whose district is a test district | **PASS** — enforced in code |

## Leakage Guard Implementation

`engine/hydroma/eval/stage39_benchmark.py::run_development_calibration()`
takes the test-district list and rejects any candidate record belonging to
those districts, reporting the count and the rejected record IDs:

```python
rejected = [r for r in dev_records if str(r.get("district_id", "")) in test_districts]
clean = [r for r in dev_records if str(r.get("district_id", "")) not in test_districts]
```

The result carries `n_rejected_test_district` and a `LEAKAGE GUARD` note
when anything was rejected. Covered by
`test_calibration_rejects_test_district_records`.

## Other Leakage Vectors Checked

| Vector | Result |
|---|---|
| Parameter selection using test observations | Not possible — the calibration entry point never receives test records |
| Feature selection using test data | Not performed; no feature selection stage exists |
| Normalisation statistics computed on test data | Not performed; no data-dependent normalisation is applied to inputs |
| Best model-version selection on test results | Not performed; the model version is frozen before the test run (`stage37_frozen_model_config.json`) |
| Test data influencing the benchmark code path | No — the runner reads the test manifest and processes records uniformly |

## Important Qualification — Coordinate Overlap

A separate analysis of the coordinate grid found that **374 of the 445
distinct 4-decimal coordinate cells in the test set also appear in the
development set**.

This is **not** a record-level or district-level leak, and it is a
property of the dataset rather than of the split: CIMMYT records cluster
on a coarse coordinate grid, and the same field can be observed in more
than one season. Because the split is by district, a coordinate can
appear in a development district and a test district only if the same
grid cell is referenced from two different districts.

**Consequence for interpretation**: a model calibrated on development
districts that happens to memorise coordinate-specific conditions could
transfer partially to the test set through those shared cells. With 374 of
445 test cells shared, the independence of the test set is weaker than the
record counts suggest.

**Mitigation options** (not implemented in Stage 39, recorded for Stage 40):

* exclude development records that share a coordinate cell with the test
  set from the calibration set (reduces the effective development set);
* report metrics separately for records on shared vs unshared coordinate
  cells.

## Conclusion

The district-based split is sound at the record level and is enforced by
code. The coordinate-cell overlap is a documented property of the dataset
that qualifies how much independence the test set actually provides; it
does not invalidate the split, but it does bound the strength of any
external-validation claim.

**Status: PASS with a documented qualification.**
