# Stage 39 — Test Benchmark

## Execution Status

The benchmark is **running** against the frozen Stage 39 model. This report
describes the protocol and the state at the time of writing; the final
record counts and metrics are in `benchmark_summary.json` (written when the
run completes) and in `STAGE-39-VALIDATION-METRICS.md`.

## Test Set

| Attribute | Value |
|---|---|
| Source | `engine/reports/data/stage36_benchmark_split_manifest.json` |
| Test districts | Buxar, Muzaffarpur, Rohtas |
| Test records | 1,722 |
| Development records | 3,967 (not used in the test run) |
| Record overlap dev/test | none |

## Frozen Model

`engine/reports/data/stage37_frozen_model_config.json` — all 17 parameters
at their default values, `calibration_status: "baseline_only"`.

The benchmark reads the split manifest and the frozen configuration. The
parameters were **not** changed after the freeze, and no test observation
influenced any parameter.

## Per-Record Execution

`engine/hydroma/eval/resumable_benchmark_runner.py::process_record()`:

1. **Validate** — coordinates, dates, observed yield.
2. **Fetch weather** — Open-Meteo ERA5-Land: Tmin, Tmax, precipitation,
   shortwave, dew-point, relative humidity, soil moisture (0-7 cm).
3. **Fetch satellite** — Planetary Computer STAC, Sentinel-2 L2A: B8A
   (NIR), B11 (SWIR), SCL (cloud mask).
4. **Compute NDMI** — `(NIR - SWIR) / (NIR + SWIR)` from the sampled
   reflectance.
5. **Compute EWSI** — `0.4·S_NDMI + 0.3·S_VPD + 0.3·S_SOIL`, with
   weight redistribution when a component is unavailable.
6. **Run HYRUE** — seasonal mode, GDD-derived LAI, PAR from
   shortwave × 0.5, f_water = 1 − EWSI.
7. **Record** — status, prediction, error, coverage, provenance.

## Execution Statuses

| Status | Meaning |
|---|---|
| `COMPUTED` | Prediction produced from the seasonal HYRUE path |
| `PARTIAL_INPUTS` | Prediction produced but with estimated/missing inputs |
| `BLOCKED` | Required input unavailable; no prediction |
| `FAILED` | Error during processing; the reason is recorded |

**No record is deleted.** Every record that was attempted appears in
`record_results.jsonl` with a status; records that could not be attempted
appear in `failed_records.jsonl` with their reason.

## Resumability

State is held in `execution_state.sqlite` (one row per record, terminal
statuses `COMPUTED`, `PARTIAL_INPUTS`, `BLOCKED`, `FAILED`,
`SKIPPED_DUPLICATE`). Re-running the script skips records already in a
terminal state, so an interrupted run resumes rather than restarting.

The SQLite connection is explicitly closed after each operation (the
Stage 38 `with sqlite3.connect(...)` pattern leaked the connection and
locked the file on Windows).

## Performance Work (Stage 39)

The first run of the benchmark was not completing a record in 15 minutes.
Profiling identified the cause in the satellite sampler:

```python
val = ds.read(1)[row, col]     # reads the ENTIRE 63 MB COG
```

`ds.read(1)` materialises the whole band before indexing one pixel.
Replaced with a windowed read:

```python
val = ds.read(1, window=Window(col, row, 1, 1))[0, 0]
```

GDAL then issues HTTP range requests for only the containing tile.

Measured effect on a full season (7 acquisitions × 2 bands + 7 SCL reads):

| Variant | Time per season |
|---|---|
| Full-band read | > 10 minutes |
| Windowed read | **52.3 s** |

The cloud-mask read was windowed as well.

## Outputs

| File | Content |
|---|---|
| `run_manifest.json` | run id, districts, record counts, timings |
| `record_results.jsonl` | one JSON object per attempted record |
| `execution_state.sqlite` | per-record execution state (resume support) |
| `failed_records.jsonl` | blocked/failed records with reasons |
| `benchmark_summary.json` | metrics overall, per district, per season; uncertainty |
| `input_quality_summary.json` | counts by input/quality status |
| `provenance_summary.json` | data provenance per component |
| `run.log` | console log of the run |

## Data Provenance Recorded Per Record

```
weather_source   Open-Meteo ERA5-Land (reanalysis estimate)
satellite_source Planetary Computer Sentinel-2 L2A (satellite retrieved)
par_conversion   shortwave x 0.5 (estimated, not measured)
ewsi_components  NDMI (satellite), VPD (reanalysis), soil moisture (reanalysis)
lai_source       GDD model (model estimate)
```
