# Stage 38 — Error Analysis

## Pilot Result vs Full Test Set

The Stage 37 pilot (1 record, Buxar 2016-17) showed:
- Predicted: 4.807 t/ha
- Observed: 6.680 t/ha
- Error: −1.873 t/ha (−28.0%)

This is an improvement over Stage 35 (+63.2% overestimate) due to the PAR unit correction (shortwave × 0.5 → PAR).

## Remaining Error Sources

The remaining −28% error could be attributed to:

| Potential Source | Description |
|---|---|
| LAI representation | No LAI data available; HYRUE requires LAI input |
| EWSI weights | Uncalibrated (0.4/0.3/0.3 project defaults) |
| EWSI anchors | NDMI (0.3/-0.2), VPD (0.5/4.0 kPa) uncalibrated |
| RUE (epsilon) | 2.2 g/MJ IPAR from wheat preset, not calibrated |
| Harvest index | 0.45 from wheat preset, not calibrated |
| Temperature stress | t_opt=20°C, Gaussian width=8°C hard-coded |
| PAR conversion | 0.5 factor is estimated, not measured |
| Spatial mismatch | Point sampling vs field-average yield |
| Temporal mismatch | Daily weather vs seasonal yield |

## Error Analysis Approach

When benchmark execution is complete, analyze errors by:

1. **District** — Systematic over/under-prediction in specific districts
2. **Season** — Seasonal bias patterns
3. **Yield level** — Whether model over/under-predicts at different yield levels
4. **Input completeness** — Records with complete vs partial EWSI/LAI inputs
5. **Data quality** — Records with low cloud cover vs high cloud cover satellite data

## No Parameter Tuning on Test Data

Per Stage 35 rule #6, no parameters will be tuned using observed test yields. Any parameter changes must be based on development data only.

## Files

- `engine/reports/data/stage38_benchmark_results.jsonl` — per-record results (when available)
