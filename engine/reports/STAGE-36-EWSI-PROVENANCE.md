# Stage 36 — EWSI Provenance

## EWSI Component Provenance

Each EWSI component must carry provenance metadata. The following
provenance vocabulary is used:

| Status | Meaning |
|---|---|
| OBSERVED | Direct field or in-situ measurement |
| SATELLITE_RETRIEVED | Satellite-derived product (not ground measurement) |
| REANALYSIS_ESTIMATE | Reanalysis / gridded modelled product (e.g. ERA5-Land) |
| MODEL_ESTIMATE | Output of an internal model |
| INTERPOLATED | Value filled between observations via interpolation |
| MISSING | No data available |
| INVALID | Data present but failed quality control |

## Component Tracking

For each EWSI computation, the following must be recorded:

| Field | Description |
|---|---|
| ndmi_source | Source of NIR/SWIR reflectance |
| ndmi_acquisition_date | Date of satellite observation |
| ndmi_cloud_quality | Cloud mask quality for the observation |
| vpd_source | Source of VPD data |
| vpd_model | Method used to compute VPD |
| soil_moisture_source | Source of soil moisture data |
| soil_moisture_depth | Depth of soil moisture layer |
| ewsi_component_status | Per-component quality status |
| ewsi_missing_components | List of missing components |
| ewsi_policy | Computation policy (strict / allow_estimated) |
| ewsi_provenance | Overall provenance metadata |

## Component Grouping in Reports

1. Records with complete EWSI and valid inputs
2. Records with complete EWSI but partial/temporal estimated inputs
3. Records with incomplete or invalid EWSI

## Files

- `engine/hydroma/eval/ewsi_pipeline.py`
- `engine/hydroma/simulation/quality_status.py`
