# Stage 38 — Satellite Optimization

## Satellite Data Pipeline

Current pipeline for satellite data:
1. STAC search — Query Planetary Computer for Sentinel-2 L2A items overlapping site buffer
2. URL signing — Sign asset URLs via Planetary Computer signing service
3. Raster download — Download COG assets via `/vsicurl/`
4. Point sampling — Sample NIR/SWIR at point location using rasterio
5. Cloud masking — SCL band values {3, 8, 9, 10, 11}
6. NDMI computation — (NIR - SWIR) / (NIR + SWIR)

## Optimization Opportunities

### 1. STAC Search Deduplication

Multiple records may share the same or nearby coordinates. STAC search results can be cached by coordinates + date range + cloud threshold. Currently each record performs a separate STAC search (~18.7s each).

**Optimization:** Cache STAC search results in `ScientificCache` keyed by coordinates + date range + cloud threshold. Reuse results for records with overlapping search areas.

### 2. Windowed Raster Access

Sentinel-2 assets are Cloud-Optimized GeoTIFFs (COGs) that support random access via `/vsicurl/`. Instead of downloading entire assets, use `rasterio.open('/vsicurl/...')` with windowed reads to sample only the pixels needed.

**Current behavior:** `rasterio.open()` on signed URL downloads the full COG metadata and accesses pixels via HTTP range requests.

**Optimization:** Explicitly use `rasterio.windows.Window` to read only the pixel at the point of interest, minimizing data transfer.

### 3. Batch STAC Search

Instead of one STAC search per record, batch multiple nearby coordinates into a single search request and filter results locally.

**Optimization:** Group records by proximity, perform one STAC search per group, assign results to individual records.

## SSL Issue

During profiling, the Planetary Computer STAC API returned SSL errors:
```
SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol')
```

This is an infrastructure issue, not a code issue. The signing service (`planetary_computer.sign()`) works correctly, but the STAC search endpoint has intermittent SSL connectivity.

## Files

- `engine/hydroma/simulation/remote_sensing/satellite_source.py` — satellite fetch (SSL issue needs infrastructure fix)
- `engine/hydroma/simulation/data_cache.py` — persistent cache for STAC results
