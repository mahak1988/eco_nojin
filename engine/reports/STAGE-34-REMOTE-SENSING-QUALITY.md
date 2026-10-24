# Stage 34 — Remote Sensing Quality

## Satellite Reflectance Pipeline

### Supported Products

| Product | Bands | Resolution | Source |
|---|---|---|---|
| Sentinel-2 Level-2A | B8A (NIR), B11 (SWIR) | 20 m | Not implemented — requires Copernicus Data Space Ecosystem API access |
| Landsat Collection 2 Level-2 | B5 (NIR), B6 (SWIR) | 30 m | Not implemented — requires USGS EarthExplorer or AWS Open Data access |

### Access Status

**No satellite API access is configured.** Both `Sentinel2Source.fetch_reflectance()`
and `LandsatC2L2Source.fetch_reflectance()` raise `NotImplementedError`
until credentials and API access are configured.

No API keys or tokens are stored in code, reports, or git.

### NDMI Computation

NDMI = (NIR - SWIR) / (NIR + SWIR)

Implemented in `engine/hydroma/simulation/remote_sensing/spectral_indices.py`
using an exact zero-denominator guard (no epsilon bias). Result clipped
to [-1, 1].

### Quality Masking

Cloud, cloud shadow, snow, and invalid pixel masking supported via:

- `quality_mask_from_s2_qa60()` — Sentinel-2 QA60 band decoding
- `apply_quality_masks()` — per-acquisition quality metrics
- `is_pixel_clear()` — clear-pixel determination

Quality metrics tracked: cloud_fraction, cloud_shadow_fraction,
snow_fraction, invalid_fraction, valid_pixel_fraction,
valid_observation_count.

### Temporal Compositing

Sentinel-2 does not guarantee daily observations. Two methods:

1. **Nearest composite** — assigns nearest observation value to each
   target date. Interpolated dates flagged as `interpolated`.
2. **Linear interpolation** — interpolates between consecutive
   observations. Gaps exceeding `max_gap_days` flagged as `missing`.

Interpolated values are never labeled as `satellite_retrieved`.

### Disk Cache

`SatelliteCache` provides JSON-based disk caching with SHA-256 keys
incorporating site coordinates, date range, source product, and
processing level. TTL support for cache expiry.

## Files

- `engine/hydroma/simulation/remote_sensing/__init__.py`
- `engine/hydroma/simulation/remote_sensing/satellite_source.py`
- `engine/hydroma/simulation/remote_sensing/reflectance_quality.py`
- `engine/hydroma/simulation/remote_sensing/spectral_indices.py`
- `engine/hydroma/simulation/remote_sensing/temporal_composite.py`
- `engine/hydroma/simulation/remote_sensing/satellite_cache.py`
