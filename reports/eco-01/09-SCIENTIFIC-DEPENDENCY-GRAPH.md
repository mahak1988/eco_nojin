# ECO-01 Scientific Dependency Graph

**Document ID:** ECO-01-09-SCIENTIFIC-DEPENDENCY-GRAPH  
**Scope:** engine/ + services/ model inter-dependencies  
**Purpose:** Map scientific knowledge flow from inputs to decisions

---

## 1. Primary Dependency Chains

### Chain-A: Climate → ET → Water Demand → Irrigation

```
┌─────────────────────────────────────────────────────────────────────┐
│                      INPUT DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────────┤
│  Weather Station Data ──┐                                          │
│  Satellite Data         ├──► Climate Data Assimilation              │
│  Forecast Data          └──                     │                    │
│                               engine/hydroma/climate/assimilation.py│
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        RADIATION COMPUTATION                         │
├─────────────────────────────────────────────────────────────────────┤
│  Extraterrestrial Radiation (R_a)                                    │
│  Solar Radiation (R_s)                                             │
│  Net Radiation (R_n)                                               │
│                               engine/hydorna/climate/radiation.py   │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                    ▼
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   PENMAN-MONTEITH ET0        │          │   HARGREAVES ET0            │
├─────────────────────────────┤          ├─────────────────────────────┤
│ Standard FAO reference method │          │ Temperature-based fallback   │
│ Requires: Radiation, Humidity,│          │ Requires: T min/max, R_a    │
│ Wind, Temperature              │          │                             │
│ engine/hydorna/climate/et_calculator.py │ engine/hydorna/climate/et_calculator.py │
└─────────────────────────────┘          └─────────────────────────────┘
                    │                                    │
                    └─────────────────┬──────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WATER DEMAND ESTIMATION                         │
├─────────────────────────────────────────────────────────────────────┤
│  ETc = Kc × ET0                                                     │
│  Net Demand = ETc - Precipitation - ΔStorage                        │
│                               engine/hydorna/models/water_demand.py │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    IRRIGATION SCHEDULING                             │
├─────────────────────────────────────────────────────────────────────┤
│  Threshold: Soil Moisture < PWP + Safety Margin                     │
│  Timing: Based on ET demand forecast                                │
│                               engine/hydorna/irrigation/scheduler.py│
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PRECISION IRRIGATION ADVISOR (EPIA)             │
├─────────────────────────────────────────────────────────────────────┤
│  Aggregates: ET0, Water Demand, Crop Coefficients, Soil Moisture    │
│  Provides: Irrigation recommendations                               │
│                               engine/hydorna/models/epia.py        │
└─────────────────────────────────────────────────────────────────────┘
```

### Chain-B: DEM → Terrain → Runoff → Watershed Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEM (Digital Elevation Model)                 │
├─────────────────────────────────────────────────────────────────────┤
│  Source: SRTM, LiDAR, or survey                                      │
│  Preprocessing: Fill sinks, reproject                                │
│                               engine/land/dem.py                    │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                    ▼
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   TERRAIN ANALYSIS           │          │   SLOPE / ASPECT             │
├─────────────────────────────┤          ├─────────────────────────────┤
│  Horn's method for derivatives│          │  3×3 finite difference       │
│  Hillshade, Curvature, TWI   │          │  Degrees from north          │
│  engine/land/terrain_analysis │          │  engine/land/models.py       │
└─────────────────────────────┘          └─────────────────────────────┘
                    │                                    │
                    ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    D8 FLOW DIRECTION                                │
├─────────────────────────────────────────────────────────────────────┤
│  Flow direction on 8-connected neighbors                              │
│  Flow accumulation → drainage area                                  │
│  engine/land/hydrology.py                                           │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SCS-CN RUNOFF                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Q = (P - 0.2S)² / (P + 0.8S)                                        │
│  S = (1000/CN - 10) × 25.4                                           │
│  CN from: Land Use × Soil Type × Hydrologic Group                    │
│  engine/hydorna/models/runoff_model.py                              │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                    ▼
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   WATERSHED STRUCTURE       │          │   HYDROGRAPH ROUTING         │
├─────────────────────────────┤          ├─────────────────────────────┤
│  Design: check dams,        │          │  Modified Puls storage-      │
│  retention ponds, infiltration│          │  outflow routing             │
│  engine/hydorna/watershed/   │          │  engine/hydorna/reservoir/   │
└─────────────────────────────┘          └─────────────────────────────┘
```

### Chain-C: Soil Properties → Salinity/Carbon → Crop Management

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SOIL PROPERTIES                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Physical: Texture, Bulk Density, Porosity                          │
│  Chemical: pH, EC (Salinity), CEC                                   │
│  Hydraulic: Ksat, Theta_r, Theta_s, Alpha, N (VG)                   │
│  engine/hydorna/soil/physics.py                                     │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                    ▼
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   SOIL WATER RETENTION      │          │   SOIL SALINITY             │
├─────────────────────────────┤          ├─────────────────────────────┤
│  Van Genuchten (Forward +    │          │  EC, SAR, pH                  │
│  Inverse via Newton-Raphson)  │          │  Crop salt tolerance         │
│  engine/hydorna/soil/physics │          │  engine/hydorna/soil/salinity  │
└─────────────────────────────┘          └─────────────────────────────┘
                    │                                    │
                    ▼                                    ▼
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   SOIL CARBON STORAGE       │          │   SOIL EROSION (RUSLE)       │
├─────────────────────────────┤          ├─────────────────────────────┤
│  SOC% × Bulk Density × Depth │          │  A = R × K × LS × C × P      │
│  engine/hydorna/soil/carbon  │          │  engine/hydorna/soil/erosion │
└─────────────────────────────┘          └─────────────────────────────┘
                    │                                    │
                    └─────────────────┬──────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CROP MANAGEMENT DECISIONS                       │
├─────────────────────────────────────────────────────────────────────┤
│  Crop selection based on soil constraints                            │
│  Irrigation scheduling considering salinity effects                 │
│  Amendment recommendations (lime, organic matter)                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Chain-D: Groundwater → Pumping → Hydraulics

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GROUNDWATER FLOW                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Steady-state: Darcy's Law (Q = -K × A × dh/dl)                     │
│  Transient: Theis Well Function (s = Q/(4πT) × W(u))              │
│  engine/hydorna/models/groundwater_model.py                         │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                    ▼
┌─────────────────────────────┐          ┌─────────────────────────────┐
│   PUMP CURVE ANALYSIS        │          │   PIPE FLOW CALCULATIONS     │
├─────────────────────────────┤          ├─────────────────────────────┤
│  Pump performance curve       │          │  Manning/Darcy-Weisbach      │
│  System curve intersection    │          │  engine/hydorna/hydraulics   │
│  engine/hydorna/hydraulics/pump│          │                             │
└─────────────────────────────┘          └─────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WATER DELIVERY SYSTEM                             │
├─────────────────────────────────────────────────────────────────────┤
│  Pump selection and scheduling                                       │
│  Pressure management                                                 │
│  engine/hydorna/hydraulics/                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Direct Dependencies

| Model | Depends On | Dependency Type | Notes |
|-------|-----------|-----------------|-------|
| Penman-Monteith ET0 | Radiation Model, Climate Data | Scientific | Requires R_n, vapor pressure |
| Hargreaves ET0 | R_a computation, T data | Scientific | Requires extraterrestrial radiation |
| SCS-CN Runoff | Soil Type, Land Use | Scientific | CN from lookup tables |
| Darcy Flow | K (hydraulic conductivity) | Scientific | K from soil properties |
| Theis Solution | Darcy Flow (conceptually) | Scientific | Extends Darcy for transient |
| Van Genuchten | Soil Properties | Scientific | Requires alpha, n, theta_r, theta_s |
| RUSLE | Slope/Aspect (LS factor) | Scientific | Requires DEM-derived slope |
| Water Demand | ET0 (Penman or Hargreaves) | Scientific | ETc = Kc × ET0 |
| Irrigation Scheduler | Water Demand, Soil Moisture | Engineering | Decision based on thresholds |
| EPIA | ET0, Water Demand, Soil Properties | Composite | Aggregates multiple models |

---

## 3. Indirect Dependencies

| Model | Indirect Depends On | Chain Length | Notes |
|-------|---------------------|--------------|-------|
| Irrigation Scheduler | Climate Data → ET0 → Water Demand | 3 hops | Weather → ET0 → Demand → Schedule |
| Watershed Calculator | DEM → Slope/Aspect → Flow Direction → Runoff | 4 hops | Terrain → hydraulics → design |
| Surface Water Model | DEM → Flow Direction → Flow Accumulation → Channel Network | 4 hops | |
| Phenology Detection | Temperature data → GDD → Growth Stage → Crop Kc | 3 hops | |

---

## 4. Circular Dependencies

| Circle | Path | Severity | Notes |
|--------|------|----------|-------|
| None found at scientific level | - | None | No circular dependencies in model chain |

**Note:** Some service-level circular imports exist (documented in ECO-00 DEPENDENCY_FORENSICS.md) but these are architectural, not scientific.

---

## 5. Hidden Dependencies

| Model | Hidden Dependency | Evidence | Risk |
|-------|-------------------|----------|------|
| Van Genuchten Inverse | Newton-Raphson must converge | engine/hydorna/soil/physics.py:89 | MEDIUM - convergence may fail |
| Theis Well Function | Series expansion convergence | engine/hydorna/models/groundwater_model.py:134 | HIGH - overflow for u → 0 |
| Climate Assimilation | Assumes all sources available | engine/hydorna/climate/assimilation.py:45 | MEDIUM - source priority hidden |
| Irrigation Scheduler | Assumes crop coefficient curve | engine/hydorna/irrigation/scheduler.py:56 | MEDIUM - no validation |
| Pump Curve | Assumes system curve formula | engine/hydorna/hydraulics/pump.py:74 | LOW - simplified system curve |
| Radiation Model | Assumes clear-sky for R_s estimation | engine/hydorna/climate/radiation.py:45 | MEDIUM - Angstrom formula simplification |
| Water Demand | Assumes effective precipitation method | engine/hydorna/models/water_demand.py:67 | LOW - not documented |
| RUSLE | LS factor computation method unclear | engine/hydorna/soil/erosion.py:34 | MEDIUM - need to verify standard |

---

## 6. Legacy Dependencies (Scientific)

| Scientific Model | Legacy Dependency | Classification | Notes |
|-------------------|-------------------|----------------|-------|
| Climate Assimilation | Direct API calls to weather services | LEGACY | Should be isolated to adapter |
| Water Demand | Hard-coded crop coefficients | RETAIN_TEMPORARILY | Should become configurable |
| Irrigation Scheduler | Hard-coded safety factors | RETAIN_TEMPORARILY | Should become configurable |
| Some Soil Models | Hard-coded soil parameter sets | RETAIN_TEMPORARILY | Should move to database/config |

---

## 7. External Dependencies (Scientific)

| Model | External Dependency | Type | Notes |
|-------|---------------------|------|-------|
| Climate Data Assimilation | Weather API endpoints | External Service | API keys and endpoints |
| Radiation Model | Solar position calculations | Algorithm | Could be local |
| Remote Sensing | Satellite data providers | Data Source | Sentinel, Landsat, MODIS |
| GIS Processing | GDAL library | Library | Standard for geospatial |
| None others | - | - | Most scientific models are self-contained |

---

## 8. Model Dependency Matrix

```
                     ET0   Radiation  Climate  SCS-CN  Darcy  Theis  VG-Soil  RUSLE  WaterDemand  Irrigation  EPIA  Phenology
ET0 (PM)          -     → YES     ←      -        -        -        -        -        -            -        ←      -
Hargreaves        → Radi←         -      -        -        -        -        -        -            -        -      -
Climate Assim     → ET0←         -       → ET0←    -        -        -        -        -            -        -      -
Radiation          → ET0→         -        -        -        -        -        -        → ET0→        -        -      -
SCS-CN Runoff      -              → CN    -        -        -        → Soil→  → Slope→ -            -        -      -
Darcy Flow         -              -        -        -        <- Soil    -        -        -            -        -      -
Theis              -              -        -        -        → Darcy→   -        -        -            -        -      -
Van Genuchten      -              -        -        -        → Soil→   -        -        -            -        -      -
RUSLE              -              -        -        → Soil→  → Slope→  -        -        -            -        -      -
Water Demand      ← ET0←         → ET0→  → CN←    → Soil←  -        → Soil→  -        -            -        → Crop→  → Irrigation→
Irrigation          -              -        -        -        -        -        → Soil→  -        ← WaterDem← ←        ← Crop
EPIA               ← ET0←         ←        → CN→  → Soil→  → DG→    → Soil→  → Slope→ ← WaterDem→ ← Irrig→   -        ← Crop
Phenology          -              -        -        -        -        -        -        → Crop→    -        -        ← Crop
```

**Legend:** → = depends on, ← = depended upon by, ↑ = bidirectional, blank = no direct dependency

---

## 9. Dependency Risk Assessment

| Dependency | Coupling Strength | Risk Level | Recommendation |
|-----------|-------------------|------------|----------------|
| Climate → ET0 | HIGH | MEDIUM | Good modular design; maintain |
| Radiation → ET0 | HIGH | LOW | Standard; well-established |
| DEM → Terrain | HIGH | LOW | Standard GIS pipeline |
| SCS-CN → Soil/LU | HIGH | MEDIUM | Consider making CN configurable |
| Water Demand → ET0 | HIGH | LOW | Standard dependency |
| Irrigation → Water Demand + Soil | HIGH | MEDIUM | Business rules need configurability |
| EPIA → Multiple models | VERY HIGH | HIGH | Composite; ensure loose coupling |
| Van Genuchten → Newton-Raphson | MEDIUM | MEDIUM | Document convergence behavior |
| Theis → Series expansion | MEDIUM | HIGH | Document convergence bounds |

---

## 10. Future Integration Points (Eco Nojin)

| Current Chain End | Eco Nojin Integration | Required Adaptation |
|-------------------|----------------------|---------------------|
| ET0 results → Water Demand | Knowledge → Evidence → Model | Provenance metadata |
| Runoff → Watershed Design | Analysis → Decision → Action | Decision rules needed |
| Water Demand → Irrigation | Model → Decision → Action | Tasmimyar decision layer |
| EPIA composite output | AI Analysis → Decision | AI control boundary |
| Soil Carbon → Carbon Storage | Monitoring → Research → Model | Research integration |
| RUSLE → Soil Conservation | Monitoring → Decision | Local knowledge integration |

---

*See also: 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 07-MODEL-QUALITY-MATRIX.md, 08-EQUATION-AND-UNIT-FORENSICS.md*