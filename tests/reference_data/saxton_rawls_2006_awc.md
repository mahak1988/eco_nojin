# Saxton & Rawls (2006) — Available Water Capacity table (vendored offline)

Published source: Saxton, K.D. and Rawls, W.J. (2006), "Soil
science society of america journal" 70(5):975-987, Table 6, p.980.
DOI: 10.2136/sssaj2005.0184

The table gives plant-available water capacity (AWC) in mm/m for each of
the 12 USDA texture classes, computed as theta(FC) at -33 kPa minus
theta(PWP) at -1500 kPa. These are the same values used in
`engine/strict_tests/conftest.py::SAXTON_RAWLS_2006_AWC_MM_PER_M`, now
formally vendored with a checksum sidecar.

| Texture    | AWC (mm/m) |
|------------|-----------|
| sand       | 16        |
| loamy_sand | 22        |
| sandy_loam | 63        |
| loam       | 110       |
| silt_loam  | 140       |
| silt       | 150       |
| sandy_clay_loam | 86   |
| clay_loam  | 120       |
| silty_clay_loam | 111  |
| sandy_clay | 80        |
| silty_clay | 120       |
| clay       | 130       |

Constraint: AR-01 — the scientific core is not connected to the internet;
this table is vendored with a sha256 checksum sidecar (`.meta.json`)
and no gate depends on a live download.
