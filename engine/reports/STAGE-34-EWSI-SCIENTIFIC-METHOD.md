# Stage 34 — EWSI Scientific Method

## EWSI (EcoNojin Water Stress Index)

### Definition

EWSI is a novel composite water stress index combining three components:

```
EWSI = w_ndmi * S_NDMI + w_vpd * S_VPD + w_soil * S_SOIL
```

Default weights: w_ndmi = 0.4, w_vpd = 0.3, w_soil = 0.3.

Range: [0, 1] where 0 = no water stress, 1 = severe water stress.

### Component Stress Indices

#### S_NDMI — NDMI-based water stress

NDMI = (NIR - SWIR) / (NIR + SWIR)

S_NDMI = clip((NDMI_ref - NDMI_t) / (NDMI_ref - NDMI_crit), 0, 1)

- NDMI_ref = 0.5 (reference under non-stressed conditions)
- NDMI_crit = -0.2 (critical NDMI at maximal stress)

Source: NDMI algebra from Gao (1996) NDWI paper — the expression
(NIR - SWIR) / (NIR + SWIR) is shared, but NDMI as a soil-water stress
index is not defined in that work.

#### S_VPD — Vapor Pressure Deficit stress

VPD = max(es(T) - ea(Td), 0)

es(T) = 0.6108 * exp(17.27 * T / (T + 237.3))  [FAO-56 Eq. 11]

S_VPD = clip((VPD - VPD_low) / (VPD_high - VPD_low), 0, 1)

- VPD_low = 0.5 kPa
- VPD_high = 4.0 kPa

Both anchors are unsourced project defaults.

#### S_SOIL — Soil moisture stress

S_SOIL = clip((FC - theta) / (FC - WP), 0, 1)

- FC = field capacity (m³/m³)
- WP = wilting point (m³/m³)
- theta = volumetric soil moisture (m³/m³)

When FC/WP are unavailable, a relative anomaly method is used:

SM_anomaly = theta_t - median(theta_reference)
S_anomaly = clip(-SM_anomaly / anomaly_scale, 0, 1)

### HYRUE Integration

HYRUE uses f_water = 1 - EWSI:

```
B_day = PAR * f_IPAR * epsilon * f_water * f_temp
f_water = 1 - EWSI
```

Confirmed in `engine/hydroma/models/hyrue.py:267`.

### Scientific Status

**Novel.** EWSI is not a published index. The three-factor composition,
weights, VPD anchors, and NDMI reference/critical values are project
defaults. Only the NDMI algebraic expression has an external source (Gao
1996, NDWI). EWSI must not be presented as a validated plant water stress
measurement.

### Missing Component Policy

- **strict:** All three components (NDMI, VPD, soil moisture) required.
  Missing any component → computation blocked.
- **allow_estimated:** Proceeds with available components. Weights of
  missing components redistributed proportionally. Missing components
  recorded in provenance.

## Files

- `engine/hydroma/models/ewsi.py` — EWSI core model
- `engine/hydroma/simulation/ewsi_pipeline.py` — EWSI pipeline with policy
- `engine/hydroma/simulation/quality_status.py` — Unified quality status vocabulary
