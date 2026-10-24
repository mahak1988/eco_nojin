# ECO-01 Performance Knowledge

**Document ID:** ECO-01-PERF-PERFORMANCE-KNOWLEDGE  
**Scope:** engine/ + services/ performance-sensitive components  
**Purpose:** Identify performance-critical assets and classify their bottlenecks

---

## 1. Performance Assets Inventory

### 1.1 C++ Kernels (CPU-bound)

| Kernel | File | Operations | Classification |
|--------|------|-----------|----------------|
| Climate kernels | engine/cpp_core/src/climate.cpp | ET0, radiation, Hargreaves | CPU_BOUND |
| Soil kernels | engine/cpp_core/src/soil.cpp | Van Genuchten, soil water | CPU_BOUND |
| Vegetation indices | engine/cpp_core/src/indices.cpp | NDVI, EVI, MSAVI on arrays | CPU_BOUND |
| DEM processing | engine/cpp_core/src/dem.cpp | Slope, aspect, hillshade | CPU_BOUND |
| Hydrology kernels | engine/cpp_core/src/hydrology.cpp | D8 flow, accumulation | CPU_BOUND |

**Assessment:** These are well-placed in C++ for performance. All are CPU-bound calculations.

### 1.2 Raster Operations

| Operation | File | Classification | Notes |
|-----------|------|----------------|-------|
| DEM processing | engine/land/dem.py | CPU_BOUND | Large 2D arrays |
| Terrain analysis | engine/land/terrain_analysis.py | CPU_BOUND | Per-cell operations |
| NDVI/EVI | engine/hydroma/remote_sensing/indices.py | CPU_BOUND | Satellite image processing |
| Hillshade | engine/land/terrain_analysis.py | CPU_BOUND | Convolution-like |
| Flow accumulation | engine/land/hydrology.py | CPU_BOUND | Recursive or iterative |

**Assessment:** Raster operations are memory-bound when reading, CPU-bound during computation.

### 1.3 Large Arrays

| Component | Data Type | Size | Classification |
|-----------|-----------|------|----------------|
| DEM arrays | float32 | 10K x 10K common | MEMORY_BOUND |
| Climate time series | float64 | 365*30 years = ~11K | MEMORY_BOUND |
| Vegetation index arrays | float32 | Satellite tile size | MEMORY_BOUND |
| Soil profile arrays | float64 | Multiple depths * grid | MEMORY_BOUND |

**Assessment:** Large arrays cause memory pressure. Consider chunked processing.

### 1.4 Simulation Loops

| Loop | Location | Iterations | Classification |
|------|----------|-----------|----------------|
| Daily ET0 | engine/hydoma/climate/et_calculator.py | 365/year | CPU_BOUND |
| Water balance | engine/hydoma/simulation/balance.py | 365+/year | CPU_BOUND |
| Irrigation scheduling | engine/hydoma/irrigation/scheduler.py | Per-event | CPU_BOUND |
| Theis well function | engine/hydoma/models/groundwater_model.py | Over time series | CPU_BOUND |

**Assessment:** Iterative calculations are CPU-bound, especially over time series.

### 1.5 Optimization Loops

| Component | Location | Type | Classification |
|-----------|----------|------|----------------|
| Conjugate gradient | engine/hydoma/optimization/cg.py | Numerical optimization | CPU_BOUND |
| Irrigation optimization | engine/hydoma/irrigation/scheduler.py | Scheduling optimization | CPU_BOUND |

**Assessment:** Optimization is CPU-bound, can benefit from parallelization.

### 1.6 GIS Processing

| Component | Location | Classification | Notes |
|-----------|----------|----------------|-------|
| Spatial interpolation | engine/land/interpolation.py | CPU_BOUND | Large point sets |
| MRF segmentation | engine/hydoma/image/mrf.py | CPU_BOUND | Iterative pixel operations |
| Contour generation | engine/land/contour.py | CPU_BOUND | Marching squares |
| Overlay analysis | engine/land/overlay.py | CPU_BOUND | Raster algebra |

**Assessment:** GIS processing is primarily CPU-bound for algorithmic parts, memory-bound for data.

---

## 2. GPU Candidacy Assessment

### 2.1 Strong GPU Candidates

| Component | Reason | Benefit Potential | Recommendation |
|-----------|--------|-------------------|----------------|
| Vegetation Index Computation | Massive pixel-level parallelism | 50-200x speedup | GPU_CANDIDATE |
| DEM Processing | Per-cell operations | 20-50x speedup | GPU_CANDIDATE |
| Terrain Analysis | Slope, aspect per cell | 20-50x speedup | GPU_CANDIDATE |
| Flow Accumulation | Grid-based propagation | 10-30x speedup | GPU_CANDIDATE |
| Climate Time Series | Independent per timestep | 10-100x speedup | GPU_CANDIDATE |

### 2.2 Moderate GPU Candidates

| Component | Reason | Benefit Potential | Recommendation |
|-----------|--------|-------------------|----------------|
| Van Genuchten (batch) | Vectorized soil calculations | 10-50x speedup | GPU_CANDIDATE |
| ET0 (large regions) | Per-pixel ET computation | 5-20x speedup | GPU_CANDIDATE |
| Spatial Interpolation | Parallel distance calculations | 5-15x speedup | GPU_CANDIDATE |

### 2.3 Not GPU-Suitable

| Component | Reason | Recommendation |
|-----------|--------|----------------|
| Kalman Filter | Sequential dependency | DISTRIBUTION_CANDIDATE |
| MRF Segmentation | Iterative convergence | DISTRIBUTION_CANDIDATE |
| Theis Well Function | Series convergence | CPU only (precision concern) |
| Model Registry | I/O bound | Not applicable |
| Report Generation | LLM I/O | Not applicable |

---

## 3. Distribution Candidacy

### 3.1 Strong Distribution Candidates

| Component | Reason | Benefit |
|-----------|--------|---------|
| Ensemble Climate Projections | Independent scenarios | Parallel scenario runs |
| Multiple Watersheds | Independent analysis | Parallel watershed processing |
| Satellite Tile Processing | Independent tiles | Parallel tile processing |
| Model Calibration | Independent parameter sets | Parallel calibration |

### 3.2 Moderate Distribution Candidates

| Component | Reason | Benefit |
|-----------|--------|---------|
| Large DEM Processing | Chunkable | Distributed raster processing |
| Time Series Analysis | Segmented time blocks | Parallel temporal chunks |

---

## 4. Performance Bottlenecks Identified

### 4.1 Algorithmic Bottlenecks

| Bottleneck | Location | Issue | Severity |
|-----------|----------|-------|----------|
| Python loops over pixels | engine/land/terrain_analysis.py | Per-pixel Python loop | MEDIUM |
| String formatting in loops | engine/hydoma/output/ | Repeated formatting | LOW |
| Repeated imports | Some modules | Redundant import in functions | LOW |
| List comprehensions on large arrays | Various | Memory allocation | LOW |

### 4.2 Memory Bottlenecks

| Bottleneck | Location | Issue | Severity |
|-----------|----------|-------|----------|
| Full DEM in memory | Multiple | Entire DEM loaded at once | MEDIUM |
| Climate arrays duplicated | Engine-wide | Data copied between functions | LOW |
| Unclosed file handles | Some modules | GDAL file handles | LOW |

### 4.3 I/O Bottlenecks

| Bottleneck | Location | Issue | Severity |
|-----------|----------|-------|----------|
| NetCDF reading | engine/hydoma/data/ | Sequential file reads | HIGH |
| JSON parsing large files | services/data | Large payload parsing | MEDIUM |
| Database queries | Services | N+1 query pattern | MEDIUM |

---

## 5. Performance Baseline (from ECO-00)

### 5.1 Computation Times (Representative)

| Operation | Time (typical) | C++ Time | Python Time | Speedup |
|-----------|----------------|----------|-------------|---------|
| ET0 (single day) | 0.3ms | 0.02ms | 0.3ms | 15x |
| Radiation calculation | 0.5ms | 0.03ms | 0.5ms | 16x |
| Van Genuchten (1000 pts) | 15ms | 0.8ms | 15ms | 18x |
| NDVI (1000x1000 pixel) | 500ms | 5ms | 500ms | 100x |
| D8 Flow Direction (100x100) | 100ms | 2ms | 100ms | 50x |
| Terrain slope (1000x1000) | 2s | 20ms | 2s | 100x |

### 5.2 Memory Usage

| Component | Memory Footprint | Notes |
|-----------|-----------------|-------|
| DEM loading (10K x 10K) | ~400MB (float32) | Fits in memory on most systems |
| Climate time series (30 years) | ~260MB (float64) | Manageable |
| Vegetation indices (tile) | ~300MB | Depends on resolution |
| Full simulation (watershed) | ~2GB peak | May need chunking |

---

## 6. Performance Recommendations

### 6.1 Short-term (Keep C++, Improve Python)

| Action | Priority | Effort | Benefit |
|--------|----------|--------|---------|
| Ensure C++ fallback works | HIGH | Low | Safety |
| Document performance-critical paths | HIGH | Low | Maintainability |
| Add memory mapping for large arrays | MEDIUM | Medium | Memory reduction |
| Use __slots__ for data classes | LOW | Low | Memory reduction |

### 6.2 Medium-term (GPU Exploration)

| Action | Priority | Effort | Benefit |
|--------|----------|--------|---------|
| Prototype GPU NDVI | MEDIUM | High | 50x speedup |
| Prototype GPU DEM processing | MEDIUM | High | 20x speedup |
| Consider Numba JIT | MEDIUM | Medium | 5-50x speedup |

### 6.3 Long-term (Distribution)

| Action | Priority | Effort | Benefit |
|--------|----------|--------|---------|
| Dask for ensemble runs | LOW | High | Scale to large workloads |
| Distributed watershed analysis | LOW | High | Regional scale |

---

## 7. Performance Asset Classification

| Asset | Classification | Notes |
|-------|----------------|-------|
| C++ Climate Kernels | CPU_BOUND | Core performance asset |
| C++ Soil Kernels | CPU_BOUND | Core performance asset |
| C++ Indices | CPU_BOUND | Core performance asset |
| C++ DEM Processing | CPU_BOUND | Core performance asset |
| Rasterio I/O | IO_BOUND | Standard, acceptable |
| NumPy Vectorized Operations | CPU_BOUND | Good |
| Python loops (hot paths) | CPU_BOUND | Needs C++ or vectorization |
| Climate array processing | CPU_BOUND | Good candidates for GPU |
| Theis series computation | CPU_BOUND | Not GPU-suitable (precision) |
| Kalman filter | CPU_BOUND | Sequential, not parallelizable |

---

## 8. GPU/Distribution Classification Summary

| Component | CPU_BOUND | MEMORY_BOUND | IO_BOUND | GPU_CANDIDATE | DISTRIBUTION_CANDIDATE |
|-----------|-----------|-------------|----------|---------------|----------------------|
| C++ Climate Kernels | YES | NO | NO | NO | NO |
| C++ Soil Kernels | YES | NO | NO | NO | NO |
| Vegetation Indices | YES | NO | NO | YES | YES |
| DEM Processing | YES | YES | NO | YES | YES |
| Terrain Analysis | YES | YES | NO | YES | YES |
| D8 Flow Direction | YES | YES | NO | YES | YES |
| Climate Time Series | YES | YES | NO | YES | YES |
| Van Genuchten | YES | NO | NO | YES | NO |
| Kalman Filter | YES | NO | NO | NO | NO |
| MRF Segmentation | YES | YES | NO | NO | NO |
| NetCDF I/O | NO | NO | YES | NO | YES |
| Spatial Interpolation | YES | YES | NO | YES | YES |
| Water Balance (daily) | YES | NO | NO | NO | YES |

---

*See also: 11-CPP-PYTHON-BOUNDARY.md, 10-HYDROMA-FORENSICS.md, 19-TECHNOLOGY-STRATEGY.md, 25-RECOMMENDED-NEXT-PHASE.md*