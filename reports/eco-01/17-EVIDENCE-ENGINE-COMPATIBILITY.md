# ECO-01 Evidence Engine Compatibility

**Document ID:** ECO-01-17-EVIDENCE-ENGINE-COMPATIBILITY  
**Scope:** engine/ + services/ evidence/data sources  
**Purpose:** Determine if current assets can support automatic evidence extraction

---

## 1. Evidence Engine Requirements

The Evidence Engine must extract evidence from multiple sources:

| Source | Current Support | Required Metadata | Status |
|--------|-----------------|-------------------|--------|
| Satellite | PARTIAL | Spatial/temporal resolution, band info, license | PARTIAL |
| Climate | YES | Station metadata, accuracy, time range | PARTIAL |
| Weather | YES | Forecast vs observed, accuracy | PARTIAL |
| Soil | PARTIAL | Sampling depth, method, lab info | PARTIAL |
| Water | PARTIAL | Gauge location, method, accuracy | PARTIAL |
| Land Cover | PARTIAL | Classification method, accuracy | PARTIAL |
| Vegetation | PARTIAL | Index type, processing level | PARTIAL |
| Remote Sensing | PARTIAL | Sensor, processing level, calibration | PARTIAL |
| Historical Observations | NONE | Source, collection method | NONE |
| Field Monitoring | PARTIAL | Observer, method, timestamp | PARTIAL |
| Scientific Literature | NONE | Citation, DOI, peer review | NONE |
| Local Knowledge | NONE | Originator, cultural context | NONE |

---

## 2. Evidence Types and Requirements

### 2.1 Evidence Type Matrix

| Evidence Type | Currently Captured | Required Metadata | Confidence |
|---------------|-------------------|-------------------|------------|
| **Satellite Imagery** | Remote sensing indices (NDVI, EVI) | Sensor, date, cloud cover, spatial resolution, processing level, license | MEDIUM |
| **Climate Data** | Daily weather data | Station ID, location, elevation, measurement method, accuracy, time period | HIGH |
| **Weather Forecast** | Climate scenarios | Model source, scenario (SSP), confidence interval | LOW |
| **Soil Measurements** | Soil parameters | Sampling depth, method, lab, date sampled, accuracy | PARTIAL |
| **Water Level/Gauge** | Runoff/surface water data | Gauge location, datum, method, date | PARTIAL |
| **Vegetation Index** | NDVI, EVI, MSAVI | Index formula, band sources, temporal resolution | MEDIUM |
| **DEM/Elevation** | DEM data | Source (SRTM/ASTER), resolution, datum, accuracy | MEDIUM |
| **Field Observations** | Monitoring data | Observer ID, timestamp, GPS, method, accuracy | PARTIAL |
| **Scientific Results** | Model outputs | Model version, parameters, assumptions | HIGH |
| **Local Knowledge** | Not captured | Originator, community, date recorded, verification status | NONE |

---

## 3. Satellite and Remote Sensing Capabilities

### Current Remote Sensing Assets

| Capability | Location | Status | License |
|-----------|----------|--------|---------|
| NDVI Calculation | engine/hydoma/remote_sensing/indices.py | IMPLEMENTATION_VERIFIED | UNKNOWN |
| EVI Calculation | engine/hydoma/remote_sensing/indices.py | IMPLEMENTATION_VERIFIED | UNKNOWN |
| MSAVI Calculation | engine/hydoma/remote_sensing/indices.py | IMPLEMENTATION_VERIFIED | UNKNOWN |
| Wavelet Analysis | engine/hydoma/remote_sensing/wavelet.py | CODE_ONLY | UNKNOWN |
| MRF Segmentation | engine/hydoma/image/mrf.py | CODE_ONLY | UNKNOWN |
| Satellite Data Access | services/satellite/ | EXPERIMENTAL | UNKNOWN |
| Land Cover Classification | services/land/classification.py | CODE_ONLY | UNKNOWN |

### Satellite Data Requirements

| Requirement | Current Support | Gap |
|------------|-----------------|-----|
| Data source identification | NONE | Need metadata on satellite/sensor |
| Spatial resolution | Implicit (pixel size) | Not tracked |
| Temporal resolution | Daily | Not tracked |
| Cloud cover | NOT considered | Critical for optical data |
| Processing level | L1C/L2A assumed | Not documented |
| License/usage rights | NONE | Critical for legal use |
| Calibration/validation | NONE | Data quality |

### Critical Gap: No Metadata Tracking
The current codebase processes satellite/imagery data but does NOT track:
- Which satellite/sensor produced the data
- Spatial resolution
- Temporal coverage
- Cloud cover percentage
- Processing level
- Calibration information
- License terms

---

## 4. Climate and Weather Evidence

### Currently Available
| Data Type | Source | Location | Metadata Available |
|-----------|--------|----------|-------------------|
| Daily Tmin/Tmax | Weather station | engine/hydoma/climate/ | Date, value |
| Precipitation | Weather station | engine/hydoma/climate/ | Date, value, units |
| Humidity | Weather station | engine/hydoma/climate/ | Date, value, units |
| Wind Speed | Weather station | engine/hydoma/climate/ | Date, value, units |
| Radiation | Calculated/Model | engine/hydoma/climate/ | Units only |
| Climate Scenarios | IPCC-based | engine/hydoma/scenarios/ | Scenario name, year |

### Missing Metadata for Evidence
| Field | Available | Required For Evidence |
|-------|-----------|----------------------|
| Station ID | NO | Source identification |
| Station location (lat/lon) | NO | Spatial provenance |
| Station elevation | NO | Atmospheric correction |
| Measurement method | NO | Accuracy assessment |
| Measurement accuracy | NO | Uncertainty |
| Instrument type | NO | Calibration |
| Quality flags | NO | Data validation |
| Temporal coverage | PARTIAL (date only) | Time range |
| Update frequency | NO | Freshness |

---

## 5. Soil Evidence

### Currently Available
| Data Type | Source | Location | Metadata |
|-----------|--------|----------|----------|
| Soil texture | Input parameter | engine/hydoma/soil/physics.py | sand, clay % |
| Soil moisture | Van Genuchten model | engine/hydoma/soil/physics.py | Calculated from parameters |
| Bulk density | Input parameter | engine/hydoma/soil/carbon.py | Measured value |
| Organic matter | Input parameter | engine/hydoma/soil/ | % |
| pH | Input parameter | services/soil/ | pH value |
| EC (salinity) | Model output | engine/hydoma/soil/salinity.py | dS/m |

### Missing for Evidence
| Field | Gap |
|-------|-----|
| Sampling depth | Not tracked |
| Sampling date | Not tracked |
| Laboratory/method | Not tracked |
| Measurement uncertainty | Not tracked |
| Spatial location | Not tracked (point vs. field) |
| Soil classification | Not standardized |

---

## 6. Water Evidence

### Currently Available
| Data Type | Source | Location | Metadata |
|-----------|--------|----------|----------|
| Streamflow | Input/model | engine/hydoma/hydrology/ | m³/s |
| Groundwater level | Model | engine/hydoma/models/groundwater_model.py | m |
| Runoff volume | SCS-CN model | engine/hydoma/models/runoff_model.py | mm |

### Missing for Evidence
| Field | Gap |
|-------|-----|
| Gauge station ID | Not tracked |
| Measurement date/time | Not tracked |
| Datum (reference level) | Not tracked |
| Measurement method | Not tracked |
| Accuracy/error | Not tracked |
| Spatial extent covered | Not tracked |

---

## 7. Vegetation/Land Cover Evidence

### Currently Available
| Data Type | Source | Location | Metadata |
|-----------|--------|----------|----------|
| Vegetation indices | Calculated | engine/hydoma/remote_sensing/ | Index value |
| Land use type | Input | engine/hydoma/ | Categorical |

### Missing for Evidence
| Field | Gap |
|-------|-----|
| Classification method | Not documented |
| Accuracy assessment (confusion matrix) | Not present |
| Spatial resolution | Not tracked |
| Temporal resolution | Not tracked |
| Training data source | Not tracked |
| Classification confidence | Not tracked |

---

## 8. Required Evidence Metadata Schema

### Evidence Metadata Requirements

```python
class EvidenceMetadata(BaseModel):
    # Core identification
    evidence_id: str
    evidence_type: Literal[
        "satellite", "climate", "soil", "water", 
        "observation", "measurement", "model_output",
        "literature", "local_knowledge", "expert_opinion"
    ]
    source_system: str  # Where evidence came from
    source_id: Optional[str]  # Original source identifier
    
    # Temporal
    collected_at: datetime  # When collected
    valid_from: datetime  # Valid period start
    valid_to: Optional[datetime]  # Valid period end
    temporal_resolution: Optional[str]  # e.g., "daily", "hourly"
    
    # Spatial
    spatial_extent: Optional[Geometry]  # GeoJSON geometry
    spatial_resolution: Optional[float]  # meters per pixel if raster
    coordinate_system: Optional[str]  # CRS
    
    # Quality
    accuracy: Optional[float]  # Measurement accuracy
    confidence: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    quality_flags: List[str]  # Data quality indicators
    
    # Provenance
    provider: str  # Source organization/provider
    instrument: Optional[str]  # Sensor/instrument used
    methodology: Optional[str]  # Collection method
    processing_level: Optional[str]  # For satellite: L1C, L2A, etc.
    calibration: Optional[str]  # Calibration info
    
    # Legal
    license: Optional[str]  # Usage rights
    copyright_holder: Optional[str]  # Data copyright
    
    # Scientific
    peer_reviewed: bool
    references: List[str]  # Citations
    epistemic_status: Literal[
        "observation", "measurement", "model_output",
        "expert_opinion", "local_knowledge"
    ]
```

---

## 9. Spatial Resolution Requirements

| Evidence Type | Required Spatial Resolution | Currently Available | Gap |
|---------------|---------------------------|---------------------|-----|
| Satellite (vegetation) | 10m (Sentinel-2) | Processable but not metadata-tracked | Metadata |
| Satellite (land cover) | 10-30m | Processable | Metadata |
| DEM/Elevation | 30m (SRTM) or 10m (Copernicus) | 30m assumed | Metadata |
| Climate data | 1km grid or station | Station-based (point) | Spatial interpolation |
| Soil data | 100m-1km | Field-level assumed | Spatial scale |
| Water gauge | Point measurement | Point | N/A |
| Historical observations | Point/time location | Unknown | Capture needed |

---

## 10. Temporal Resolution Requirements

| Evidence Type | Required Temporal Resolution | Currently Available | Gap |
|---------------|------------------------------|---------------------|-----|
| Weather | Hourly/Daily | Daily | Hourly needed for some models |
| Climate | Monthly/Annual | Monthly | Annual needed for trends |
| Satellite | 5-16 days (Sentinel-2) | Processable | Metadata |
| Soil moisture | Daily/Event | Rarely | Insufficient frequency |
| Streamflow | Hourly/Daily | Daily | Hourly needed for flood |
| Vegetation | 5-16 days | Processable | Metadata |

---

## 11. Processing Requirements

### Required Processing Pipeline

```
DATA INGESTION
    ↓
Metadata Extraction (REQUIRED)
    ↓
Quality Control
    ↓
Provenance Assignment
    ↓
Evidence Entity Creation
    ↓
Indexing & Cataloging
    ↓
Availability for Decision Support
```

### Current Processing Gaps

| Requirement | Current Status | Gap Description |
|-------------|----------------|-----------------|
| Metadata extraction | NONE | No systematic metadata capture |
| Quality control | PARTIAL | Some in climate assimilation |
| Provenance assignment | PARTIAL | Basic provenance exists |
| Evidence cataloging | NONE | No unified evidence catalog |
| Indexing | NONE | No search/discovery for evidence |

---

## 12. Licensing and Legal Requirements

### Current State
No license tracking for any data sources.

### Required for Evidence Engine

| Data Source | License Tracked? | Needed For |
|-------------|-----------------|------------|
| Satellite data | NO | Legal compliance for reuse |
| Weather station | NO | Attribution, restrictions |
| Soil surveys | NO | Data use agreements |
| Model outputs | NO (generated) | N/A |

---

## 13. Evidence Engine Compatibility Assessment

### Ready for Reuse
| Asset | Evidence Support | Quality |
|-------|-----------------|---------|
| Model Registry | ✅ Strong - model outputs tracked | HIGH |
| Provenance Engine | ✅ Strong - source tracking | HIGH |
| Formula Catalog | ✅ Evidence of scientific basis | HIGH |
| Climate Models | ✅ Process observed data | HIGH |
| Soil Models | ✅ Process soil measurements | MEDIUM |
| Vegetation Index Calculations | ✅ Compute indices | MEDIUM |
| Terrain Analysis | ✅ Dem-derived evidence | HIGH |

### Needs Enhancement
| Asset | Gap | Enhancement Needed |
|-------|-----|-------------------|
| Remote Sensing | No metadata | Add satellite/sensor/resolution metadata |
| Climate Data | No station metadata | Add station info, accuracy |
| Soil Data | No sampling metadata | Add sampling depth, lab info |
| Water Data | No gauge metadata | Add gauge info, datum |
| Provenance | Limited epistemic status | Add knowledge type tracking |
| Model Registry | No output uncertainty | Add uncertainty estimates |

### Missing Completely
| Needed | Not Available | Priority |
|--------|---------------|----------|
| Evidence catalog | None | HIGH |
| Metadata schema | None | HIGH |
| License tracking | None | MEDIUM |
| Data quality scoring | None | HIGH |
| Evidence search/indexing | None | HIGH |
| Local knowledge capture | None | HIGH |
| Literature integration | None | LOW |
| Expert opinion capture | None | MEDIUM |

---

## 14. Recommendations

### Phase 1: Evidence Foundation (Architecture Phase)
1. ✅ **Preserve existing models** as evidence sources
2. ⚠️ **Extend provenance** to capture epistemic status and knowledge type
3. ⚠️ **Add metadata schema** for all evidence types
4. ❌ **Create evidence catalog** service for indexing
5. ❌ **Add license tracking** for external data

### Phase 2: Processing Pipeline (Implementation)
1. **Metadata extraction layer** - extracts metadata from each data source
2. **Quality control pipeline** - validates and scores evidence
3. **Evidence entity creation** - creates standardized evidence records
4. **Catalog service** - indexes and makes evidence discoverable

### Phase 3: Integration
1. Connect evidence → Tasmimyar decision support
2. Connect evidence → Daneshyar knowledge types
3. Connect evidence → research/validation loops

---

## 15. Required Evidence Requirements by Source

### Satellite Evidence Requirements
| Requirement | Specification |
|------------|---------------|
| Spatial Resolution | 10m for vegetation, 30m for land cover |
| Temporal Resolution | 5-day revisit minimum |
| Bands Required | Red, NIR, SWIR for vegetation indices |
| Processing Level | L2A minimum (surface reflectance) |
| Cloud Cover | <20% for usable images |
| License | CC-BY or public domain preferred |

### Climate Evidence Requirements
| Requirement | Specification |
|------------|---------------|
| Temporal Resolution | Hourly for weather, daily for climate |
| Parameters | Temperature, precipitation, humidity, wind, radiation |
| Accuracy | Temperature ±0.5°C, precipitation ±10% |
| Station Info | Location (lat/lon/elevation), method, instrument |
| Duration | Minimum 10 years for climate normals |

### Soil Evidence Requirements
| Requirement | Specification |
|------------|---------------|
| Parameters | Texture, bulk density, pH, EC, organic matter, CEC |
| Depth | Multiple layers (0-30, 30-60, 60-100, 100+) |
| Method | Laboratory analysis per standard methods |
| Accuracy | ±5% for texture, ±0.1 pH units |
| Location | GPS coordinates, datum |

### Water Evidence Requirements
| Requirement | Specification |
|------------|---------------|
| Parameters | Streamflow, groundwater level, water quality |
| Frequency | Hourly for streamflow, daily minimum for groundwater |
| Datum | Chart datum or local benchmark |
| Gauge Info | Station ID, location, type |
| Duration | Minimum 1 year continuous |

---

*See also: 12-AI-FORENSICS.md, 15-DANESHYAR-COMPATIBILITY.md, 16-TASMIMYAR-COMPATIBILITY.md, 24-UNKNOWN-AND-CONFLICTS.md*