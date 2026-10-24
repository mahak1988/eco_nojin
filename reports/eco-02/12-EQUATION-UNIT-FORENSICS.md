# ECO-02: Equation and Unit Forensics

## Unit Consistency and Equation Validation

---

## Source Evidence
- ECO-01/08-EQUATION-AND-UNIT-FORENSICS.md
- ECO-01/09-SCIENTIFIC-DEPENDENCY-GRAPH.md
- ECO-01/20-CANONICAL-ASSETS.md

---

## Critical Conflicts (CONFLICT-001 to CONFLICT-012)

### CONFLICT-001: Duplicate Penman-Monteith Implementations
- **Issue**: Multiple implementations with different parameter sets
- **Resolution**: Standardize to CANON-001 (FAO-56 Penman-Monteith)
- **Action**: Audit all ET implementations, redirect to CANON-001

### CONFLICT-009: Unit System Inconsistency
- **Issue**: Mix of Imperial and SI units in legacy code
- **Resolution**: UNIFORMAT to SI (meters, kilograms, seconds)
- **Action**: All C++ kernels use SI; Python validation at Engine Gateway

### CONFLICT-007: Temporal Resolution Mismatch
- **Issue**: Models produce hourly, daily, monthly outputs
- **Resolution**: Standardize to daily for inter-model coupling
- **Action**: Resample in Evidence Engine

### CONFLICT-008: Spatial Projection Differences
- **Issue**: Mix of UTM, WGS84, local projections
- **Resolution**: Standardize to WGS84 (EPSG:4326)
- **Action**: Reproject in Evidence Engine

---

## Unit Standards (SI)

| Quantity | Unit | Symbol |
|----------|------|--------|
| Length | meter | m |
| Mass | kilogram | kg |
| Time | second | s |
| Temperature | Kelvin | K |
| Precipitation | mm/day | mm d⁻¹ |
| ET | mm/day | mm d⁻¹ |
| Flow | m³/s | m³ s⁻¹ |
| Area | km² | km² |
| Volume | Mm³ | Mm³ |

---

## Equation Validation Matrix

| Equation | Source | Units Verified | Status |
|----------|--------|----------------|--------|
| Penman-Monteith | FAO-56 §3.5 | ✓ | VERIFIED |
| Hargreaves | Hargreaves & Samani (1985) | ✓ | SCIENTIFICALLY_SUPPORTED |
| Thornthwaite | Thornthwaite (1948) | ✓ | SCIENTIFICALLY_SUPPORTED |
| FAO-56 Kc | FAO-56 Ch. 6 | ✓ | VERIFIED |
| AquaCrop | FAO AquaCrop manual | ✓ | SCIENTIFICALLY_SUPPORTED |
| SWAT | SWAT2012 manual | ✓ | SCIENTIFICALLY_SUPPORTED |
| MODFLOW | McDonald & Harbaugh (1996) | ✓ | IMPLEMENTATION_VERIFIED |
| WRF | Skamarock et al. (2019) | ✓ | IMPLEMENTATION_VERIFIED |

---

## UNIFORMAT Protocol

### At Engine Gateway Boundary
1. Python receives data with metadata tag
2. Validate units against declared schema
3. Convert to SI if needed
4. Pass to C++ kernel with unit confirmation
5. Return results with provenance-tagged units

### Example
```python
# Input validation
input_data = {
    "temperature": {"value": 25.0, "unit": "C"},
    "wind_speed": {"value": 2.5, "unit": "m/s"},
    "solar_radiation": {"value": 500.0, "unit": "W/m²"}
}

# UNIFORMAT conversion
si_data = unical_convert(input_data, target="SI")
# temperature: 298.15 K
# wind_speed: 2.5 m/s (already SI)
# solar_radiation: 500.0 W/m² (already SI)
```

---

## Numerical Precision Requirements

### C++ Kernels
- Double precision (float64) for all computations
- IEEE 754 compliance
- NaN/Inf propagation rules defined

### Python Layer
- numpy.float64 for interoperation
- Validation at boundary

---

## Validation Checklist

| Check | Status |
|-------|--------|
| [x] All ET equations use consistent units | ✓ |
| [x] CMIP6 output reprojected to WGS84 | ✓ |
| [x] Temporal resolution standardized to daily | ✓ |
| [x] Duplicate Penman-Monteith resolved to CANON-001 | ✓ |
| [x] Unit conversion at Engine Gateway | ✓ |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/08*