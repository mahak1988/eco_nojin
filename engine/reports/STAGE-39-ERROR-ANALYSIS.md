# Stage 39 — Error Analysis

## Pilot Versus Test Set

The Stage 37 pilot (one record, Buxar 2016-17) gave 4.807 t/ha against an
observed 6.680 t/ha (−28.0%). The Stage 39 benchmark reproduces that figure
**exactly** for the same record (4.807 t/ha), which is a useful
reproducibility check: the runtime-integrity fix and the windowed-read
optimisation changed *how* the satellite data is fetched, not *what* is
computed.

## Candidate Error Sources

The residual error is not attributable to a single cause. The
contributions below are ordered by how much they can be isolated with the
available data.

| Source | Evidence available | Diagnosis |
|---|---|---|
| **LAI representation** | `lai_status` recorded per record; GDD model is used because no observed LAI exists for CIMMYT | The GDD model's thermal-time parameters are the project defaults, not validated for wheat in eastern India. A wrong LAI curve rescales the whole season's IPAR and therefore the yield. **The single largest identified contributor.** |
| **ε (RUE) and HI (harvest index)** | Not separable from yield data (see the identifiability report) | The *product* ε·HI sets the yield scale. Literature wheat values in a different climate can be off by ±20-30% in either direction. |
| **EWSI weights and anchors** | `ewsi_provenance` records which components were present | The weights (0.4/0.3/0.3) and anchors (NDMI 0.3/−0.2, VPD 0.5/4.0 kPa) have no published source. A different weighting changes `f_water` and therefore the yield. |
| **PAR conversion** | Verified; the 0.5 factor is a documented approximation | A ±0.05 error in the true PAR fraction (0.45-0.55) propagates almost directly to yield. |
| **Soil moisture stress** | ERA5-Land reanalysis, 0-7 cm layer | Reanalysis soil moisture is a grid-cell estimate at ~9 km resolution, not a field measurement. The 0.35 m³/m³ field capacity is a project default. |
| **VPD stress** | ERA5-Land reanalysis, hourly aggregated to daily | Same resolution caveat; the 0.5/4.0 kPa anchors have no source. |
| **Satellite sampling** | `satellite_coverage` per record; NDMI from a single 20 m pixel | Two limitations: (i) a point sample is not a field average; (ii) with ~4% of season days having an observation, the NDMI series is heavily forward-filled. |
| **Season length** | Planting/harvest dates from CIMMYT | The date range defines the biomass integration window. If the reported harvest date is not the actual grain-harvest date, the season is mis-specified. |
| **Temperature stress** | `t_opt` = 20 °C, Gaussian width hard-coded | Winter wheat in Bihar experiences November-February cooling; whether 20 °C is the right optimum for that phenology is unverified. |
| **Unit errors** | Audited in `STAGE-39-PAR-UNIT-AUDIT.md` | **Ruled out.** The chain is dimensionally closed and double-conversion is prevented. |
| **Data leakage** | Audited in `STAGE-39-DATA-LEAKAGE-AUDIT.md` | **Ruled out at record and district level.** A coordinate-cell overlap (374 of 445 test cells also appear in development) qualifies the independence but is a property of the dataset, not of the split. |

## How the Error Will Be Analysed

The benchmark writes, per record: prediction, observation, absolute and
relative error, input-quality status, satellite coverage, and the EWSI
provenance. Once the run completes, the error will be broken down by:

* district (3 groups) — spatial bias;
* season (6 groups) — temporal bias;
* input-quality status — whether degraded inputs drive the error;
* satellite coverage — whether records with sparser NDMI support are
  worse;
* observed-yield band — whether the bias depends on the yield level.

The error analysis is **diagnostic**. It does not authorise parameter
changes: any parameter that is to be changed must be re-estimated on the
development set under the protocol in
`STAGE-39-CALIBRATION-REPORT.md`, and the test run must then be repeated
with a new frozen model version.

## The Parameter That Cannot Be Diagnosed This Way

ε and HI cannot be separated by any error analysis, because they are
perfectly collinear. An observed systematic bias (all records
over-predicted by 15%) is equally consistent with ε being 15% too high,
with HI being 15% too high, or with the product ε·HI being right and
the EWSI amplitude being wrong. Only a development-set fit with the
identifiability constraints of the protocol can resolve this — which is
why the calibration step is not optional for a validated claim.
