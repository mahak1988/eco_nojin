# Stage 35 — Satellite Ingestion

## Pipeline

`engine/hydroma/simulation/remote_sensing/satellite_source.py`

### Sentinel-2 Level-2A (Primary)

**STAC Collection:** `sentinel-2-l2a` on Planetary Computer

**Bands used for NDMI:**
- NIR: B8A (865 nm, 20 m)
- SWIR: B11 (1610 nm, 20 m)
- Cloud mask: SCL (Scene Classification Layer)

**Bands NOT interchangeable without documentation:** B8 vs B8A, B11 vs B12 have different spectral responses and spatial resolutions.

### Processing Steps

1. **STAC search** — query Planetary Computer for items overlapping site buffer (±0.01°) and date range, cloud cover < 20%
2. **URL signing** — `planetary_computer.sign()` for Azure Blob Storage access
3. **CRS transform** — WGS84 → image CRS (EPSG:32644 for UTM zone 44N) using `rasterio.warp.transform`
4. **Point sampling** — `rasterio` reads pixel at transformed lat/lon
5. **Cloud masking** — SCL values {3, 8, 9, 10, 11} (cloud shadow, medium/high prob cloud, thin cirrus, snow) → acquisition excluded
6. **Scale factor** — 0.0001 (DN to surface reflectance)
7. **NDMI** — `(NIR - SWIR) / (NIR + SWIR)` with zero-denominator guard

### Quality Metrics Per Acquisition

- cloud_fraction (from eo:cloud_cover property)
- valid_pixel_fraction (1.0 if clear, 0.0 if cloudy)
- valid_observation_count
- quality_status: SATELLITE_RETRIEVED
- source_product: S2MSI2A
- processing_level: L2A
- spatial_resolution_m: 20.0

### Verified Output (Buxar, 2016-11-01 to 2017-04-21)

- 7 cloud-free Sentinel-2 acquisitions
- B8A reflectance range: ~0.25-0.45
- B11 reflectance range: ~0.20-0.35
- NDMI computed per acquisition

## Files

- `engine/hydroma/simulation/remote_sensing/satellite_source.py`
- `engine/hydroma/simulation/remote_sensing/spectral_indices.py`
- `engine/hydroma/simulation/remote_sensing/reflectance_quality.py`
