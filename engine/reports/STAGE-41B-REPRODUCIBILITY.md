# Stage 41-B — Reproducibility audit of 33 non-reproducing records

This audit uses the repository's authoritative comparison artifact:

- `engine/reports/data/stage41_reproducibility.json`

## Summary

The Stage 41 re-run control compared 106 records against the Stage 40 frozen model. Of those:

- 73 reproduced exactly within 1e-12
- 33 did not reproduce within 1e-12
- maximum absolute calibrated difference: 5.2447 t/ha
- `bit_identical`: false

This means the benchmark is not strictly re-run stable across Stage 40 and Stage 41, even though the model code itself remained numerically frozen. The failure pattern is not a re-calibration or equation change; it is an input-provenance / upstream-data drift problem.

## Evidence from the data

The non-reproducing records consistently show the same pattern:

- `lai_status_40 = "missing"` while `lai_status_41 = "estimated"`
- `ewsi_status_40 = "estimated"` or `"observed"`, while `ewsi_status_41` has a different quality state (often `"observed"`)
- `weather_valid_days_40` is null while `weather_valid_days_41` is a non-null daily count
- `satellite_acq_40` is null while `satellite_acq_41` is present

Examples from the actual artifact:

- record 297: `lai_status_40 = missing`, `lai_status_41 = estimated`, `ewsi_status_40 = estimated`, `ewsi_status_41 = observed`, `abs_diff_calibrated = 1.146238030336601`
- record 619: `lai_status_40 = missing`, `lai_status_41 = estimated`, `ewsi_status_40 = estimated`, `ewsi_status_41 = observed`, `abs_diff_calibrated = 1.3234493309284048`
- record 1209: high drift with both LAI and EWSI status changes, `abs_diff_calibrated = 5.244679861693808`

## Interpretation

This is a lock-violation on the input side, not a numerical model drift:

- the HYRUE equation and frozen parameters remain unchanged
- the Stage 41 and Stage 40 result differences are explained by different resolved input state and upstream data availability
- the upstream pipeline is sensitive to weather data coverage, Sentinel-2 acquisition availability, and model-generated fallback states

This is sufficient to conclude:

- the Stage 41 benchmark is not directly comparable with Stage 40 on the same record set without exact upstream-input parity;
- the Stage 41 benchmark is therefore not a clean scientific reproduction of the Stage 40 frozen model run.

## Conclusion

This satisfies the requirement to record a model-input lock violation as a Stage 41 benchmark comparability failure. The benchmark differs because the upstream inputs changed, not because `HYRUE` was reparameterized or its numerical equation was modified.
