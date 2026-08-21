# C++ Integration Guide for Scientific Motors

Generated: 2026-08-20 20:03:12

## Overview

This guide shows how to integrate each scientific motor with the C++ bridge.

## Available C++ Functions

| Function | Description | Speedup |
|---|---|---|
| `ndvi(red, nir)` | NDVI calculation | 10-20× |
| `evi(red, nir, blue)` | EVI calculation | 10-20× |
| `rusle_annual_soil_loss(...)` | RUSLE erosion | 5-10× |
| `simulate_richards(...)` | Richards equation | 100-1000× |
| `simulate_crop_water(...)` | Crop water simulation | 10-50× |
| `penman_monteith_et0(...)` | FAO-56 ETo | 5-10× |

## Integration Pattern

```python
# At top of your motor file:
try:
    from engine.hydroma.cpp_bridge import ndvi, is_cpp_available
    _cpp_available = is_cpp_available()
except ImportError:
    _cpp_available = False

# In your function:
def calculate_ndvi(red, nir):
    if _cpp_available:
        try:
            return ndvi(red, nir)  # C++ fast path
        except Exception:
            pass  # Fall through to Python
    # Python fallback
    return (nir - red) / (nir + red + 1e-10)
```

## Motors to Integrate

### erosion_rusle.py

Functions to integrate:
- `rusle_annual_soil_loss` → `rusle_annual_soil_loss`
- `ls_factor` → `ls_factor`
- `soil_erodibility_k` → `soil_erodibility_k`
- `estimate_rainfall_erosivity` → `estimate_rainfall_erosivity`

### carbon_sequestration.py

Functions to integrate:
- `simulate_richards` → `simulate_richards`

### irrigation_scheduler.py

Functions to integrate:
- `simulate_crop_water` → `simulate_crop_water`
- `penman_monteith_et0` → `penman_monteith_et0`

### satellite_integration.py

Functions to integrate:
- `ndvi` → `ndvi`
- `evi` → `evi`
- `savi` → `savi`
- `ndwi` → `ndwi`
- `nbr` → `nbr`

