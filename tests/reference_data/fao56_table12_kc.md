# FAO-56 Table 12 — Kc mid-season values (vendored offline)

Published source: Allen et al. 1998, FAO Irrigation and Drainage Paper 56,
Chapter 6, Table 12 — single crop coefficient (Kc) values for mid-season stage.

This file carries the published Kc_mid tabulated values used to validate
`engine/hydroma/data/kc_lookup.py::get_average_kc`. The engine's
`kc_data.csv` stores `kc_gs_avg` (growing-season average) which, for corn and
wheat, corresponds to the Kc_mid column of FAO-56 Table 12:

| crop    | Kc_mid (FAO-56 Table 12) | engine kc_data.csv |
|---------|--------------------------|--------------------|
| corn    | 1.20                     | 1.20               |
| wheat   | 1.15                     | 1.15               |

Rice is intentionally omitted: FAO-56 Table 12 lists paddy rice Kc values that
are water-management dependent (flooded vs. non-flooded), so a single scalar
is not a faithful transcription; the engine's rice=1.25 is treated as a
project default pending a provenance decision.

Constraint: AR-01 — the scientific core is not connected to the internet; this
table is vendored with a sha256 checksum sidecar (`.meta.json`) and no gate
depends on a live download.
