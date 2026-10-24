# HYDROMA API CONTRACTS

**Generated**: 2026-10-09  
**Purpose**: Define all API contracts for HyDroMA engine, services, and external interfaces

---

## 1. Engine Gateway API

### GatewayRequest
```python
@dataclass
class GatewayRequest:
    model_id: str                    # CANON-XXX or service model ID
    inputs: dict[str, Any]           # Input parameters
    input_units: dict[str, UnitSpec] # Units for each input
    provenance: ProvenanceSpec        # Data source chain
    parameters: dict[str, Any]       # Optional model parameters
    uncertainty: UncertaintySpec | None  # Optional uncertainty
    execution_metadata: ExecutionMetadata | None
```

### GatewayResult
```python
@dataclass
class GatewayResult:
    model_id: str
    status: str              # SUCCESS, EXECUTION_ERROR, TIMEOUT
    data: dict[str, Any]     # Results
    provenance: list[str]    # Full provenance chain
    uncertainty: dict[str, Any] | None
    execution_metadata: ExecutionMetadata
```

### GatewayError
```python
@dataclass
class GatewayError:
    model_id: str
    status: str = "EXECUTION_ERROR"
    message: str
    detail: str | None       # Only shown in dev mode
    error_code: str          # Standardized error codes
```

**Error Codes**:
- `MODEL_NOT_FOUND` — Unknown model_id
- `DEPS_MISSING` — Required dependencies unavailable (e.g., numpy)
- `VALIDATION_ERROR` — Input validation failed
- `EXECUTION_TIMEOUT` — Execution timed out
- `COMPUTATION_ERROR` — Computation failed

---

## 2. Scientific Facade API

All functions in `services/_gateway_facade.py` follow a consistent signature:
```python
def <function_name>(param1: type, param2: type, ...) -> dict[str, Any]:
    """
    Docstring describing the computation.
    Returns: {'data': ..., 'model_id': ..., 'provenance': ..., 'uncertainty': ...}
    """
    return _execute("MODEL_ID", {"param1": param1, ...})
```

### Climate Functions
| Function | Model ID | Parameters | Return |
|----------|----------|------------|--------|
| `calc_et0_hargreaves` | CANON-002 | t_min, t_max, t_mean, ra_mj | dict with `et0` |
| `calc_et0_penman_monteith` | CANON-001 | ClimateData | dict with `et0` |
| `calc_extraterrestrial_radiation` | CANON-011 | lat, doy | dict with `ra_mj` |
| `fetch_daily_weather` | SAT_WEATHER | lat, lon, days | list of daily data |

### Soil Functions
| Function | Model ID | Parameters | Return |
|----------|----------|------------|--------|
| `calculate_cec` | CANON-015 | clay_pct, organic_matter_pct, ph | dict with `cec` |
| `calculate_sar` | SOIL_CHEMISTRY | sodium, calcium, magnesium | dict with `sar` |
| `calculate_soil_health_index` | SOIL_HEALTH | organic_carbon_pct, bulk_density, ph, texture, drainage | dict with `health_index` |
| `classify_texture` | SOIL_TEXTURE | clay_pct, silt_pct, sand_pct | dict with `texture_class` |
| `calculate_water_retention_curve` | CANON-006 | pressure_points, vg_params | dict with `theta` |

### Satellite Functions
| Function | Model ID | Parameters | Return |
|----------|----------|------------|--------|
| `calculate_ndvi` | SAT_NDVI | red, nir | dict with `ndvi` |
| `calculate_ndwi` | SAT_NDWI | green, nir | dict with `ndwi` |
| `retrieve_ndvi` | SAT_OBSERVATION | bbox, date_range | dict with `indices` |

### Economics Functions
| Function | Parameters | Return |
|----------|------------|--------|
| `calculate_npv` | cash_flows, discount_rate | dict with `npv` |
| `calculate_payback` | cash_flows | dict with `payback_period` |
| `calculate_financial_metrics` | revenues, costs, discount_rate | dict with metrics |

### Decision Engine API
```python
POST /api/v1/decisions/recommend
{
    "criteria": [...],
    "model_id": "string",
    "inputs": {...},
    "parameters": {...}
}

Response:
{
    "recommendation": "string",
    "confidence": 0.0-1.0,
    "evidence_ids": ["string"],
    "trace": {...}
}
```

---

## 3. Service API Routes

### Gateway Route
```
GET /api/v1/gateway/{model_id}
POST /api/v1/gateway/{model_id}/execute
GET /api/v1/gateway/metadata
GET /api/v1/gateway/{model_id}/info
```

### Tasmimyar Decision Service
```
POST /api/v1/decisions/recommend
POST /api/v1/decisions/evaluate
GET /api/v1/decisions/{id}
```

### Soil Router (hydroma_soil)
```
GET /api/v1/hydroma/soil          # metadata for all soil tools
GET /api/v1/hydroma/soil/{id}     # metadata for one tool
POST /api/v1/hydroma/soil/{id}/run # execute tool
```

---

## 4. C++ Bridge API

Direct access via `hydroma_core.cp312-win_amd64.pyd`:

### Classes (14)
- BottomBoundary, CropWaterParams, CropWaterResult, RichardsOptions, RichardsResult
- RoutingResult, RusleCell, SaintVenantOptions, SaintVenantResult
- SuitabilityResult, TimeStepControl, TopBoundary, WaveParameters, YieldStats

### Functions (47)
- `ndvi(red, nir) -> float`
- `ndwi(green, nir) -> float`
- `hargreaves_et0(t_min, t_max, t_mean, ra) -> float`
- `penman_monteith_et0(...) -> float`
- `rusle_annual_soil_loss(R, K, LS, C, P) -> float`
- `extraterrestrial_radiation(lat, doy) -> float`
- `fao56_net_radiation(...) -> float`
- `soil_water_content(...) -> float`
- `estimate_rainfall_erosivity(precip) -> float`

---

## 5. Version Compatibility

| Component | Version |
|-----------|---------|
| Python | 3.12.10 |
| numpy | 2.3.5 |
| scipy | 1.16.3 |
| pydantic | 2.13.4 |
| FastAPI | 0.141.1 |
| Gateway Protocol | 1.0 |

**Backward compatibility**: ModelSpec model_id format is stable (CANON-XXX, SERVICE_XXX, C-CPP-XXX). API contracts use semantic versioning.