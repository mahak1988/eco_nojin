# ECO-03: Units & Dimensional Analysis Contract — Report 08
## UNIFORMAT Unit Standardization Specification

---

## Executive Summary

ECO-02/ADR-005 defines UNIFORMAT unit standardization protocol. ECO-03 verifies the current state against source code.

**Status**: DESIGNED BUT NOT ENFORCED — UNIFORMAT is defined in documentation but NOT enforced in source code.

---

## 1. SI Canonical Units (Verified)

| Quantity | SI Unit | Symbol | ECO-01 Definition | Source Code Evidence | Status |
|----------|---------|--------|-------------------|---------------------|--------|
| Length | meter | m | ECO-01/08 §UNIFORMAT | `engine/hydroma/quantity.py` | DESIGNED |
| Mass | kilogram | kg | ECO-01/08 §UNIFORMAT | Not enforced in code | DESIGNED |
| Time | second | s | ECO-01/08 §UNIFORMAT | Not enforced in code | DESIGNED |
| Temperature | kelvin | K | ECO-01/08 §UNIFORMAT | Not enforced — C++ uses celsius internally | DESIGNED |
| Precipitation | mm/day | mm/day | ECO-01/08 §UNIFORMAT | `engine/cpp_core/src/climate.cpp` outputs mm/day | VERIFIED |
| ET (Evapotranspiration) | mm/day | mm/day | ECO-01 §11 | `penman_monteith_et0()` returns mm/day | VERIFIED |
| Flow | m³/s | m³/s | ECO-01 §11 | Not consistently applied | DESIGNED |
| Pressure | pascal | Pa | ECO-01 §11 | Not enforced | DESIGNED |
| Radiation | MJ/m²/day | MJ/m²/day | ECO-01 §11 | `fao56_net_radiation()` uses MJ | VERIFIED |

---

## 2. Unit Conversion Boundary (Location)

### ECO-02 Claim
> "Unit conversion boundary — all conversions happen at Engine Gateway boundary"

### ECO-03 Verification
**Status**: DESIGNED BUT NOT ENFORCED

- No `engine/gateway/units.py` module exists
- Unit conversion (if any) happens inside scientific model functions
- No centralized unit conversion boundary

### Current Conversion Locations (Scattered — VIOLATION)

| File | Line | Conversion | Status |
|------|------|------------|--------|
| `engine/hydroma/climate/et_calculator.py` | ~line 60 | Celsius to Kelvin | SCATTERED |
| `engine/hydroma/soil/physics.py` | ~line 50 | Various unit conversions | SCATTERED |
| `engine/hydroma/watershed/calculator.py` | Various | Unit handling | SCATTERED |
| `engine/cpp_core/src/climate.cpp` | Lines 130-145 | Internal C++ unit handling | SCATTERED |

**Finding**: Unit conversions are scattered across individual modules, NOT centralized at Engine Gateway.

---

## 3. Dimensional Validation

### ECO-02 Claim
> "Dimensional validation integrated into Evidence Tag lifecycle"

### ECO-03 Verification
**Status**: NOT VERIFIED

- `engine/strict_tests/test_s09_dimensional_consistency.py` exists but is PENDING/UNRUNNABLE
- No runtime dimensional validation exists
- No AST-based dimensional analysis

**Evidence**: 
- `engine/strict_tests/test_s09_dimensional_consistency.py` — test file exists but cannot run (no database package)
- No `engine/gateway/dimension_check.py` or similar module

---

## 4. Temperature Conventions (Verified)

### C++ Kernel Convention
From `engine/cpp_core/src/climate.cpp`:
```cpp
// Line 22: sat_vapor_pressure uses t_c (celsius)
double sat_vapor_pressure(double t_c) {
    return 0.6108 * std::exp(17.27 * t_c / (t_c + 237.3));
}

// Line 138: Uses Tmean + 273.0 for Kelvin conversion (FAO-56 eq. 6)
gamma * (900.0 / (t_mean + 273.0)) * u2 * (es - ea);
```

### Python Fallback Convention
From `engine/hydroma/cpp_bridge/__init__.py` (line 382-403):
```python
# Uses Tmean (celsius) for calculations
tmean = (tmin + tmax) / 2.0
# Converts to Kelvin: (tmax + 273.16) ** 4 — NOTE: uses 273.16 not 273
```

**Critical Finding**: 
- C++ uses `t_mean + 273.0` (FAO-56 standard)
- Python fallback uses `tmax + 273.16` (different constant)
- This is a **numerical divergence** that creates inconsistent results between C++ and Python backends
- Documented in `cpp_bridge/__init__.py` line 134: `gamma * (900.0 / (t_mean + 273.0))` (C++) vs Python uses 273.16

**Status**: CONFLICTING EVIDENCE — C++ and Python backends produce different results for the same inputs due to temperature constant difference.

---

## 5. Pressure Conventions

| Source | Convention | Evidence |
|--------|------------|----------|
| C++ `climate.cpp:127` | Atmosphere pressure calculated from elevation | `101.3 * pow((293.0 - 0.0065 * z) / 293.0, 5.26)` |
| Python fallback | Same formula | `engine/hydroma/cpp_bridge/__init__.py` line 390 |

**Status**: VERIFIED — Both use same formula.

---

## 6. Time Conventions

| Source | Convention | Evidence |
|--------|------------|----------|
| `extraterrestrial_radiation()` | Day of year (1-366) | `engine/cpp_core/src/climate.cpp:63` |
| `penman_monteith_et0_array()` | Day of year (int) | Same |

**Status**: VERIFIED — Consistent day-of-year convention.

---

## 7. Area/Volume Conventions

**Status**: NOT VERIFIED

- No centralized area/volume conversion in codebase
- Units documented but not enforced
- ECO-02 ADR-005 §UNIFORMAT defines conventions but no implementation

---

## 8. Water-Depth Conventions

From ECO-01/08 §UNIFORMAT:
- Water depth: mm (precipitation), m (groundwater)
- **Status**: DESIGNED BUT NOT ENFORCED

---

## 9. Soil EC Conventions

From ECO-01/08 §UNIFORMAT:
- Soil EC: dS/m (deciSiemens per meter)
- **Status**: NOT VERIFIED — No runtime enforcement found

---

## 10. Coordinate Conventions

| Source | Convention | Evidence |
|--------|------------|----------|
| Various | WGS84 (EPSG:4326) | Documented in ECO-02 diagrams |
| `engine/land/` | Lat/Lon in degrees | `terrain_analysis.py` |

**Status**: VERIFIED — WGS84 used consistently in land analysis.

---

## 11. Unit Consistency Test Results

### `test_s09_dimensional_consistency.py`
- **Status**: PENDING (test exists but UNRUNNABLE due to missing `database/` package)
- **Evidence**: `reports/engine-services/TEST-REPORT.md §3`: Test type DIMENSIONAL, Status UNRUNNABLE

---

## 12. Findings

1. **CONFLICTING EVIDENCE**: C++ kernel uses `273.0` for Kelvin conversion, Python fallback uses `273.16`. This creates numerical divergence between backends.

2. **DESIGNED BUT NOT ENFORCED**: UNIFORMAT unit standardization is defined in ADR-005 but no runtime enforcement exists in code.

3. **DESIGNED BUT NOT ENFORCED**: Unit conversion boundary at Engine Gateway — no gateway module exists.

4. **NOT VERIFIED**: Dimensional validation "integrated into Evidence Tag lifecycle" — no Evidence Engine exists in code.

5. **BLOCKING**: Test suite for dimensional consistency cannot run due to missing `database/` package.

---

## 13. Unit Invariants

| Invariant | Status | Evidence |
|-----------|--------|----------|
| All C++ kernels use SI units | PARTIAL | Climate kernel uses celsius for temperature input |
| Unit conversion only at gateway boundary | NOT ENFORCED | Conversions scattered in model code |
| No unit conversion in multiple locations | VIOLATED | Conversions in climate.cpp, soil/physics.py, watershed/calculator.py |
| Temperature: consistent kelvin vs celsius | VIOLATED | C++: 273.0, Python: 273.16 |

---

## 14. Required Unit Contract (For ECO-04)

```python
# engine/gateway/units.py (TO BE IMPLEMENTED)
class UnitConverter:
    """Single source of truth for unit conversion."""
    
    @staticmethod
    def to_si(value: float, from_unit: str, quantity: str) -> float:
        """Convert any unit to SI."""
        # All conversions centralized here
        pass
    
    @staticmethod
    def validate_dimensions(value: float, unit: str, expected_dimension: str) -> bool:
        """Validate dimensional consistency."""
        pass
```

---

*Report generated: 2026-10-08*
*Status: CONFLICTING EVIDENCE (temperature constant diverges)*