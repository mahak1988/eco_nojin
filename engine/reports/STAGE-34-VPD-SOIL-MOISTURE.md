# Stage 34 — VPD and Soil Moisture

## VPD (Vapor Pressure Deficit) Model

### Computation

VPD = max(es(T) - ea(Td), 0)

es(T) = 0.6108 * exp(17.27 * T / (T + 237.3))  [FAO-56 Eq. 11]

Two input methods:

1. **Dewpoint temperature:** ea = es(Td)
2. **Relative humidity:** ea = es(T) * RH / 100

When both are provided, dewpoint method is used; RH reported for
cross-checking only.

Hourly data can be aggregated: VPD computed per hour, then averaged
across the day (preferred over VPD from daily means).

### Temperature Units

Inputs expected in °C. Kelvin inputs explicitly converted via
`kelvin_to_celsius(t_k) = t_k - 273.15`. Unit guessing is not permitted.

### Validation

- Temperature range: [-50, 60] °C
- VPD range: [0, 10] kPa
- RH range: [0, 100] %
- Td > T → ValueError (physically impossible)

### Stress Transform

S_VPD = clip((VPD - VPD_low) / (VPD_high - VPD_low), 0, 1)

Default anchors: VPD_low = 0.5 kPa, VPD_high = 4.0 kPa. Both unsourced.

## Soil Moisture Model

### Soil Water Stress

When FC and WP available:

S_soil = clip((FC - theta) / (FC - WP), 0, 1)

When FC only:

S_soil = clip(1 - theta / FC, 0, 1)

When neither available (relative anomaly method):

SM_anomaly = theta_t - median(theta_reference)
S_anomaly = clip(-SM_anomaly / anomaly_scale, 0, 1)

### Validation

- Soil moisture: [0, 0.6] m³/m³
- Field capacity: > 0 and <= 0.6 m³/m³
- Wilting point: >= 0 and < FC
- FC == WP → ValueError

### Root-Zone Weighting

`root_zone_weighted_moisture()` computes root-zone weighted average
from multi-layer soil moisture, weighting by layer overlap with root
zone depth.

## Files

- `engine/hydroma/simulation/vpd_model.py`
- `engine/hydroma/simulation/soil_moisture_model.py`
