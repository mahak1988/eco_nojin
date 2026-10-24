# Stage 34 — Limitations

## Scientific Limitations

1. **EWSI is novel.** Not a published index. Weights (0.4/0.3/0.3),
   VPD anchors (0.5/4.0 kPa), and NDMI reference/critical values
   (0.5/-0.2) are project defaults, not validated parameters.

2. **NDMI source correction.** Gao (1996) defines NDWI, not NDMI.
   The algebra (NIR - SWIR)/(NIR + SWIR) is shared, but NDMI as a
   soil-water stress index is not sourced from that work.

3. **VPD anchors unsourced.** VPD_low=0.5 kPa and VPD_high=4.0 kPa
   have no published source. VPD stress saturates at 4.0 kPa.

4. **Synthetic EWSI in CIMMYT integration.** Real satellite NIR/SWIR,
   VPD, and soil moisture data are not available from configured sources.
   CIMMYT integration used synthetic EWSI inputs — results are NOT
   validation-grade.

5. **No generalization.** Results valid only for wheat in Bihar/eastern
   Uttar Pradesh, India, 2016-2022. No generalization to other crops
   or regions.

## Data Limitations

1. **Satellite access not configured.** Copernicus Data Space Ecosystem
   and USGS EarthExplorer credentials not available. Sentinel-2 and
   Landsat reflectance cannot be fetched.

2. **Weather data gaps.** Open-Meteo provides Tmin/Tmax/precip/shortwave
   but not dewpoint, RH, or soil moisture. NASA POWER provides PAR but
   not NIR/SWIR for NDMI.

3. **Spatial resolution.** Satellite pixels (20-30 m) do not match
   CIMMYT field parcels (~1 km coordinate resolution). Footprint
   uncertainty not quantified.

4. **Temporal gaps.** Sentinel-2 5-day revisit with cloud cover creates
   temporal gaps. Interpolation is flagged but not validated.

## Method Limitations

1. **No model calibration on test data.** EWSI weights and anchors
   were not derived from CIMMYT test data.

2. **No uncertainty quantification.** No numerical uncertainty bounds
   on EWSI components or composite index.

3. **No sensitivity analysis published.** OAT sensitivity to NDMI,
   VPD, soil moisture, and weights not computed on real data.

## Files

All Stage 34 reports.
