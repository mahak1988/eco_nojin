# Reference data

Published input, not engine output: `fao56_examples.csv` holds the FAO-56
Example 18 row (Rome, 6 July) verbatim and `fao56_examples.md` explains where
every number in it comes from.

## The sidecar contract

Every file here ships a sidecar named `<path>.meta.json` — the full file name
with `.meta.json` appended, so `fao56_examples.csv` is described by
`fao56_examples.csv.meta.json`. That is the single convention
`engine/data/meta_contract.py:meta_path_for` returns and the `*.meta.json` glob
of spec §4.2; the `<stem>.meta.json` spelling is not used.

The sidecar carries the §4.2 raw-data fields (`dataset_id`, `source`, `url`,
`license`, `retrieved_at`, `spatial_resolution`, `temporal_resolution`,
`checksum_sha256`, `local_path`) together with the §4.6 required fields
(`dataset_version`, `source_id`, `variable`, `unit`, `content_hash`). The §4.2
names `source`, `url`, `checksum_sha256` and `local_path` are accepted as
aliases of `source_id`, `source_uri_or_reference`, `content_hash` and
`geometry_or_location`. A missing required field is an error, a missing
recommended field is a warning — see `engine/data/meta_contract.py`.

## Adding new data

Never commit a bare file. ZED §2.2ج (قواعد داده) requires a local mirror with a
checksum for every external dataset, forbids live download inside the scientific
core, and requires everything to be reproducible offline. So: mirror the file,
record its real `sha256_of` hash, describe it with `build_meta`, check it with
`validate_meta`, and keep the `local_path` pointing at the mirror.

`fao56_examples.meta.json` is the worked example and validates with zero errors
(`engine/tests/test_meta_contract.py`).
