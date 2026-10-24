# Stage 41-D — Root cause of 33 non-reproducing records

## Summary

`stage41_reproducibility.json` compares 106 records: 73 reproduce within `1e-12`, and 33 do not. The maximum absolute difference is `5.244679861693808 t/ha`.

The 33 IDs identified by the artifact are:

```text
297, 619, 831, 1285, 1107, 226, 391, 1209, 1288, 1391, 398,
1117, 1211, 1290, 409, 1126, 1228, 254, 410, 1234, 1295, 267,
412, 657, 763, 827, 859, 1021, 1050, 1236, 1051, 1171, 1283
```

For every one of those 33 rows, the stored `differing_input_fields` includes `lai_status` and `ewsi_status`. The artifact also records Stage 40 weather-valid-day and satellite-acquisition values as null while Stage 41 has populated values, but it does not retain the paired daily numeric arrays or provider/cache response hashes needed to attribute the numeric prediction changes to a specific data source.

## Classification

| Cause | Count | Examples | Evidence |
|---|---:|---|---|
| DATA_CHANGED | 0 conclusively proven | — | Input status/provenance changed, but paired underlying numeric inputs/source hashes are absent |
| CODE_CHANGED | 0 conclusively proven | — | The input-pipeline hashes in the frozen manifest match; the changed seasonal predictor's Stage 40 diff is not available |
| BUG | 0 proven | — | No record is shown to have identical complete inputs with a different output |
| UNPROVEN | 33 | 297, 619, 831 | The artifact records differing LAI/EWSI statuses and output deltas, but not sufficient input values/hashes to determine source-data versus code-path cause |
| **Total** | **33** | | |

Examples:

- Record 297: `abs_diff_calibrated = 1.146238030336601 t/ha`; LAI and EWSI status differences.
- Record 619: `abs_diff_calibrated = 1.3234493309284048 t/ha`; LAI and EWSI status differences.
- Record 1209: `abs_diff_calibrated = 5.244679861693808 t/ha`; LAI and EWSI status differences.

The Stage 41 frozen manifest reports equal recorded/current hashes for `lai_model.py`, `ewsi_pipeline.py`, `par_pipeline.py`, `radiation_units.py`, and `weather_source.py`. That makes a change in those specific files unsupported by the available hashes, but it does not prove the external inputs were unchanged. The Stage 40 source revision for `seasonal_predictor.py` could not be recovered by hash.

## Conclusion

There is concrete evidence of an input-resolution/provenance difference on all 33 records, but the strict causal categories requested cannot be assigned honestly from the preserved data. Root cause remains `UNPROVEN = 33`; no `BUG` is established, and no claim is made that the benchmark is directly comparable with Stage 40.
