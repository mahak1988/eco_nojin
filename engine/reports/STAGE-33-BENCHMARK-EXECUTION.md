# Stage 33: Benchmark Execution Report

## Summary

| Item | Value |
|---|---|
| **Benchmark Status** | BLOCKED |
| **Total Test Records** | 1722 |
| **Sampled Records** | 80 |
| **Weather Cache Entries** | 80 |

### Prediction Results by Policy

| Policy | Successful | Failed | Success Rate |
|---|---|---|---|
| STRICT (primary) | 0 | 80 | 0.0% |
| ALLOW_ESTIMATED (secondary) | 0 | 80 | 0.0% |
| DIAGNOSTIC (supplementary) | 80 | 0 | 100.0% |

## A. Weather Data Acquisition

Network access to weather APIs was verified:
- **Open-Meteo ERA5-Land archive**: Accessible (HTTP 200)
- **NASA POWER MERRA-2**: Accessible (HTTP 200)

Weather was fetched for a representative sample of 80 records
from the test set, using coordinates and growing season dates from CIMMYT.
Weather cache contained 80 unique entries.

## B. STRICT Policy Execution (Primary)

All STRICT predictions failed. The failure reasons are:

1. **PAR provenance:** Open-Meteo provides shortwave radiation, not direct PAR.
   PAR is derived via the 0.5 shortwave-to-PAR conversion (Status B calibration
   assumption), which has `estimated` provenance. STRICT policy requires
   `satellite_retrieved` or `field_measured` PAR.
   - *NASA POWER provides direct PAR via `ALLSKY_SFX_PAR_TOT` (CERES SYN1deg),
     which is `satellite_retrieved`. However, Open-Meteo is the primary source
     and does not provide PAR directly.*

2. **LAI provenance:** LAI is not available in the CIMMYT dataset. The GDD-based
   sigmoid model (`LAIModel`) is used, which has `model_generated` provenance.
   STRICT policy requires `observed` LAI.

3. **EWSI availability:** EWSI inputs (NIR/SWIR, VPD, soil moisture) are NOT
   available from Open-Meteo or NASA POWER. The EWSI model
   (`engine/hydroma/models/ewsi.py`) requires all three inputs to compute.
   Without EWSI, HYRUE seasonal mode cannot execute.

## C. ALLOW_ESTIMATED_INPUTS Policy Execution (Secondary)

All ALLOW_ESTIMATED predictions failed at the `compute_hyrue_seasonal` step.
The failure chain:

1. Weather fetched successfully (Open-Meteo ERA5-Land) ✓
2. PAR derived from shortwave (estimated provenance) ✓
3. LAI generated via GDD model (model_generated provenance) ✓
4. `build_seasonal_climate_inputs` produces `SeasonalClimateInputs` with
   `input_quality = "partial"` (missing EWSI) ✓ (correctly identified as partial)
5. `compute_hyrue_seasonal` checks `input_quality != "complete"` →
   `allow_legacy_fallback=False` (only enabled for DIAGNOSTIC) →
   raises `WeatherUnavailable("Cannot run HYRUE seasonal mode: missing inputs (ewsi)...")` ✗

The EWSI inputs are fundamentally unavailable:
- **NIR/SWIR:** Requires Sentinel-2 or Landsat reflectance data — not implemented
- **VPD:** Can be computed from NASA POWER RH+T, but NIR/SWIR and soil moisture still needed
- **Soil moisture:** Available from ERA5-Land (Copernicus CDS), but not implemented in the pipeline

## D. DIAGNOSTIC Policy (Supplementary Analysis)

The DIAGNOSTIC policy enables `allow_legacy_fallback=True`, which allows HYRUE
to run with scalar mean values when daily LAI/EWSI are incomplete. This produces
predictions in `legacy_constant` mode.

**WARNING:** Legacy constant mode assumes identical conditions for all days
and is documented to overstate seasonal totals. These results are NOT suitable
for validation claims.

| Metric | Value |
|---|---|
| Diagnostic predictions produced | 80 |
| Diagnostic predictions failed | 0 |

## E. Execution Verdict

Both STRICT and ALLOW_ESTIMATED evaluations blocked. STRICT: PAR estimated, LAI model-generated, EWSI unavailable. ALLOW_ESTIMATED: EWSI inputs (NIR/SWIR/VPD/soil moisture) not available from any implemented data source. HYRUE seasonal mode requires daily EWSI.

## F. Data File Hash Verification

| Property | Value |
|---|---|
| File | D:\HyDroMA\data\external\cimmyt_wheat\data\Wheat_Yld_Eastern_IND_Data.xlsx |
| SHA-256 | 919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde |
| Expected (Stage 32) | 919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde |
| Match | True |
| Size (bytes) | 1609655 |
