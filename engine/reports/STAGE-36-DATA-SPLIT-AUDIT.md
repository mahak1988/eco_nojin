# Stage 36 — Data Split Audit

## Split Verification

The benchmark split manifest has been verified:

| Check | Result |
|---|---|
| Manifest hash matches recomputed hash | PASS |
| No district overlap between dev and test | PASS |
| No record ID overlap between dev and test | PASS |
| Record counts match manifest | PASS |
| All districts accounted for | PASS |

## Split Details

| Attribute | Value |
|---|---|
| Dataset ID | CIMMYT_EASTERN_INDIA_WHEAT |
| Dataset version | 1.0.0 |
| Split version | stage36_v1 |
| Grouping column | District |
| Total records | 5,689 |
| Development records | 3,967 |
| Test records | 1,722 |
| Manifest hash | ff431502f98d5944bd4c7a354bc4128d234abd057c34d17c26ef6ce5f392d94d |

## Development Districts (7)

Begusarai, Bhojpur, Deoria, EastChamparan, Kushinagar, Lakhisarai, Madhepura

## Test Districts (3)

Buxar, Muzaffarpur, Rohtas

## Data Leakage Prevention

- Records are grouped by district; no district appears in both sets
- No record ID appears in both sets
- Calibration uses only development-district records
- Test-district records are never used for parameter estimation
- Manifest hash ensures reproducibility

## Files

- `engine/hydroma/eval/benchmark_split_manifest.py`
- `engine/reports/data/stage36_benchmark_split_manifest.json`
