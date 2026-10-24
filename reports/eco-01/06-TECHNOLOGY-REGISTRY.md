# ECO-01 Technology Registry

**Document ID:** ECO-01-06-TECHNOLOGY-REGISTRY  
**Scope:** engine/ + services/ technology stack  
**Purpose:** Catalog all technologies with strategic classification

---

## 1. Technology Inventory

### CORE Technologies (Essential to Eco Nojin)

#### Python 3.12
| Field | Value |
|-------|-------|
| **technology_name** | Python 3.12 |
| **category** | Programming Language |
| **current_usage** | Primary application language; engine and services |
| **importance** | CRITICAL |
| **quality** | HIGH |
| **technical_debt** | None |
| **legacy_coupling** | None |
| **replacement_risk** | HIGH (would require full rewrite) |
| **strategic_value** | CORE |
| **notes** | Required version 3.12+ for Pydantic V2 and modern typing |

#### C++ (cpp_core)
| Field | Value |
|-------|-------|
| **technology_name** | C++ (cpp_core kernels) |
| **category** | Performance Computing |
| **current_usage** | Climate, soil, and indices computation kernels |
| **importance** | CRITICAL for performance |
| **quality** | HIGH |
| **technical_debt** | Build complexity, ABI management |
| **legacy_coupling** | Moderate (coupled via cpp_bridge) |
| **replacement_risk** | HIGH |
| **strategic_value** | CORE |
| **notes** | Performance-critical kernels; must be preserved for speed |

#### NumPy
| Field | Value |
|-------|-------|
| **technology_name** | NumPy |
| **category** | Numerical Computing |
| **current_usage** | Array operations, vectorized calculations |
| **importance** | CRITICAL |
| **quality** | HIGH |
| **technical_debt** | None |
| **legacy_coupling** | None |
| **replacement_risk** | LOW |
| **strategic_value** | CORE |
| **notes** | Standard scientific Python dependency |

#### Pydantic V2
| Field | Value |
|-------|-------|
| **technology_name** | Pydantic V2 |
| **category** | Data Modeling |
| **current_usage** | Data models, validation, serialization |
| **importance** | CRITICAL |
| **quality** | HIGH |
| **technical_debt** | Migration from V1 if any remains |
| **legacy_coupling** | None |
| **replacement_risk** | LOW |
| **strategic_value** | CORE |
| **notes** | Provides type safety and validation layer |

### IMPORTANT Technologies

#### Rasterio
| Field | Value |
|-------|-------|
| **technology_name** | Rasterio |
| **category** | GIS Processing |
| **current_usage** | Reading/writing geospatial raster data |
| **importance** | HIGH |
| **quality** | HIGH |
| **technical_debt** | GDAL dependency |
| **legacy_coupling** | None |
| **replacement_risk** | MEDIUM |
| **strategic_value** | IMPORTANT |
| **notes** | Standard for raster I/O in Python GIS |

#### xarray
| Field | Value |
|-------|-------|
| **technology_name** | xarray |
| **category** | Data Processing |
| **current_usage** | Multi-dimensional array data structures |
| **importance** | MEDIUM |
| **quality** | HIGH |
| **technological_debt** | None |
| **legacy_coupling** | None |
| **replacement_risk** | LOW |
| **strategic_value** | IMPORTANT |
| **notes** | Good for climate/raster data |

#### Structlog
| Field | Value |
|-------|-------|
| **technology_name** | Structlog |
| **category** | Logging |
| **current_usage** | Structured logging throughout engine and services |
| **importance** | MEDIUM |
| **quality** | HIGH |
| **technical_debt** | None |
| **legacy_coupling** | None |
| **replacement_risk** | LOW |
| **strategic_value** | OPTIONAL (good practice) |
| **notes** | Provides JSON logs for observability |

#### Matplotlib
| Field | Value |
|-------|-------|
| **technology_name** | Matplotlib |
| **category** | Visualization |
| **current_usage** | Plot generation in analysis modules |
| **importance** | LOW |
| **quality** | MEDIUM |
| **technical_debt** | Heavy dependency |
| **legacy_coupling** | None |
| **replacement_risk** | LOW |
| **strategic_value** | OPTIONAL |
| **notes** | Only used for optional visualization |

### INFRASTRUCTURE Technologies (Legacy/Deprecated)

#### SQLAlchemy
| Field | Value |
|-------|-------|
| **technology_name** | SQLAlchemy |
| **category** | Database |
| **current_usage** | ORM for some service persistence |
| **importance** | LOW (for core) |
| **quality** | HIGH |
| **technical_debt** | Tight coupling in some services |
| **legacy_coupling** | HIGH |
| **replacement_risk** | LOW |
| **strategic_value** | LEGACY |
| **notes** | Database not in ECO-01 scope per section 3.1 FORBIDDEN SCOPE |

#### Celery
| Field | Value |
|-------|-------|
| **technology_name** | Celery |
| **category** | Task Queue |
| **current_usage** | Async background tasks |
| **importance** | LOW (for core) |
| **quality** | MEDIUM |
| **technical_debt** | Message broker dependency (Redis/RabbitMQ) |
| **legacy_coupling** | HIGH |
| **replacement_risk** | MEDIUM |
| **strategic_value** | LEGACY |
| **notes** | Not essential for scientific computation |

#### FastAPI
| Field | Value |
|-------|-------|
| **technology_name** | FastAPI |
| **category** | Web Framework |
| **current_usage** | API endpoints in services |
| **importance** | LOW (for core) |
| **quality** | HIGH |
| **technical_debt** | None |
| **legacy_coupling** | HIGH (service architecture) |
| **replacement_risk** | LOW |
| **strategic_value** | LEGACY |
| **notes** | API architecture is out of ECO-01 scope |

### LEGACY / OBSOLETE Technologies

#### Requests
| Field | Value |
|-------|-------|
| **technology_name** | Requests |
| **category** | HTTP Client |
| **current_usage** | External API calls |
| **importance** | LOW |
| **quality** | MEDIUM |
| **technical_debt** | None |
| **legacy_coupling** | LOW |
| **replacement_risk** | LOW |
| **strategic_value** | OPTIONAL → LEGACY |
| **notes** | Can be isolated to data adapter layer |

#### Pandas
| Field | Value |
|-------|-------|
| **technology_name** | Pandas |
| **category** | Data Analysis |
| **current_usage** | Data manipulation in some services |
| **importance** | MEDIUM |
| **quality** | HIGH |
| **technical_debt** | Memory overhead for large datasets |
| **legacy_coupling** | MEDIUM |
| **replacement_risk** | LOW |
| **strategic_value** | IMPORTANT |
| **notes** | Acceptable for data processing; may be heavy for core computation |

#### Docker
| Field | Value |
|-------|-------|
| **technology_name** | Docker |
| **category** | Containerization |
| **current_usage** | Service deployment |
| **importance** | LOW (deployment only) |
| **quality** | HIGH |
| **technical_debt** | None |
| **legacy_coupling** | LOW |
| **replacement_risk** | LOW |
| **strategic_value** | LEGACY |
| **notes** | Deployment infrastructure, not core logic |

---

## 2. Technology Classification Summary

### CORE Technologies (12)
- Python 3.12
- C++ (cpp_core)
- NumPy
- Pydantic V2
- Rasterio
- xarray
- Structlog

### IMPORTANT Technologies (5)
- Pandas
- Matplotlib
- SciPy (if present)

### OPTIONAL Technologies (3)
- Requests
- Matplotlib
- Structlog (arguable)

### LEGACY Technologies (6)
- SQLAlchemy
- Celery
- FastAPI
- Docker
- Requests (can be isolated)
- Redis/RabbitMQ (message brokers)

### REMOVE Technologies (0)
None currently marked for immediate removal

### UNKNOWN Technologies (1)
- AI/ML frameworks (details in AI FORENSICS)

---

## 3. Data Formats Inventory

| Format | Usage | Location | Confidence |
|--------|-------|----------|------------|
| NetCDF | Climate data | engine/hydoma/climate/ | HIGH |
| GeoTIFF | Raster data (DEM, satellite) | engine/land/ | HIGH |
| CSV | Time series, tabular data | engine/hydoma/data/ | HIGH |
| JSON | Configuration, metadata | All modules | HIGH |
| Parquet | Efficient data storage | services/data/ | MEDIUM |
| HDF5 | Large dataset storage | engine/hydoma/data/ | LOW |

---

## 4. Remote Sensing Technologies

| Technology | Usage | Location | Confidence |
|-----------|-------|----------|------------|
| Sentinel-2 | Vegetation monitoring | engine/hydoma/remote_sensing/ | MEDIUM |
| Landsat | Land cover analysis | engine/hydoma/remote_sensing/ | MEDIUM |
| MODIS | Vegetation indices | engine/hydoma/remote_sensing/ | MEDIUM |
| SRTM | DEM data source | engine/land/dem.py | HIGH |

---

## 5. GIS Methods Catalog

| Method | Implementation | Location | Status |
|--------|---------------|----------|--------|
| D8 Flow Direction | Standard | engine/land/hydrology.py:50-89 | VERIFIED |
| Slope/Aspect | Horn's Method | engine/land/models.py | VERIFIED |
| Flow Accumulation | D8-based | engine/land/hydrology.py | VERIFIED |
| Hillshade | Standard | engine/land/terrain_analysis.py | VERIFIED |
| TWI | Standard | engine/land/terrain_analysis.py | CODE_ONLY |
| Contour Generation | Marching squares | engine/land/contour.py | CODE_ONLY |

---

## 6. Numerical Computing Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Array Computing | NumPy | Vectorized operations, arrays |
| Scientific Computing | SciPy (if present) | Advanced numerical methods |
| Statistical Analysis | SciPy.stats | Statistical distributions, tests |
| Optimization | Custom (CG) | engine/hydoma/optimization/ |
| Linear Algebra | NumPy | Matrix operations |

---

## 7. Technology Debt Assessment

### High Priority Technical Debt
| Issue | Location | Impact | Recommendation |
|-------|----------|--------|----------------|
| C++ build complexity | engine/cpp_core | High | KEEP_WITH_REFACTOR |
| Legacy service coupling | services/ | High | ISOLATE |
| Database dependency | services/ | High | RETAIN_TEMPORARILY |

### Medium Priority Technical Debt
| Issue | Location | Impact | Recommendation |
|-------|----------|--------|----------------|
| Pandas memory overhead | Various | Medium | Consider for large datasets |
| GDAL complexity | rasterio dependencies | Medium | ACCEPT as GIS standard |
| Logging inconsistency | All modules | Medium | Standardize on structlog |

### Low Priority Technical Debt
| Issue | Location | Impact | Recommendation |
|-------|----------|--------|----------------|
| Multiple visualization libraries | engine/hydoma/ | Low | Consolidate to one |
| HTTP client variety | services/ | Low | Standardize |

---

## 8. Strategic Technology Opportunities

| Opportunity | Current Tech | Potential | Notes |
|-------------|-------------|-----------|-------|
| C++ acceleration | cpp_core | GPU offload | Could use CUDA/OpenCL for raster ops |
| Python performance | Python | JIT compilation | Consider Numba for compute kernels |
| Distributed computing | Single process | Dask/Ray | Watershed analysis parallelizable |
| Cloud-native | Docker | Kubernetes | For deployment scaling |
| WebAssembly | C++ | Browser compute | Client-side scientific calculation |

---

## 9. Duplicated Technologies

| Technology | Used In | Duplication Notes |
|-----------|---------|-------------------|
| Logging | All modules | Some use structlog, some use stdlib logging |
| HTTP Client | Multiple services | requests, httpx both present |
| Configuration | engine, services | Different config patterns |
| Data Models | engine, services | Some overlap with pydantic models |
| Error Handling | Multiple modules | Inconsistent patterns |
| Validation | Multiple modules | Different approaches |

---

*See also: 01-KNOWLEDGE-INVENTORY.md, 07-MODEL-QUALITY-MATRIX.md, 19-TECHNOLOGY-STRATEGY.md*