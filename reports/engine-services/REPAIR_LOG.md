# Repair Log — Engine Services

> Per ECO-00 Section 29 (Repair Logging)

## Summary

Three BLOCKER-P1 import errors resolved. No existing code modified beyond
removing a forbidden cross-boundary import. All adapters are new files.

## Repair 1: `adapters/engine_adapter.py` (BLOCKER-P1)

**What** — Created missing module imported by `services/land/service.py:12`:
`from adapters.engine_adapter import EngineAdapter`.

**Why** — The service layer depended on `EngineAdapter` which did not exist
in the repository.

**Changed**
- `adapters/__init__.py` — new package marker.
- `adapters/engine_adapter.py` — new `EngineAdapter` class.

**Methods**
| Method | Delegates to | Returns |
|---|---|---|
| `analyze_terrain(dem_array, profile_id, resolution)` | `TerrainAnalyzer.analyze` | `TerrainAnalysis` |
| `analyze_drainage(dem_array, profile_id, resolution, area_km2)` | `DrainageAnalyzer.analyze` | `DrainageAnalysis` |
| `assess_capability(profile_id, slope_degrees, soil_depth_m, erosion_risk, drainage_class, climate_zone, soil_texture)` | `assess_land_capability` | `CapabilityAssessment` |

**Evidence** — 10 EngineAdapter assertions pass in `tests_adapters_full.py`.

## Repair 2: `adapters/hydroma_adapter.py` (BLOCKER-P1)

**What** — Created missing module imported by
`services/land/tests/test_integration.py:7`:
`from adapters.hydroma_adapter import HydromaAdapter`.

**Why** — The integration tests depended on `HydromaAdapter` which did not
exist in the repository.

**Changed**
- `adapters/hydroma_adapter.py` — new `HydromaAdapter` class.

**Methods**
| Method | Delegates to | Returns |
|---|---|---|
| `analyze_soil(soil_data)` | `classify_salinity(ec)` | `SoilAnalysisResult` |
| `analyze_climate(climate_data)` | `calc_et0_hargreaves` | `ClimateAnalysisResult` |
| `analyze_watershed(slope_pct, area_m2, rainfall_mm)` | `design_check_dam` | `WatershedAnalysisResult` |
| `analyze_groundwater(gw_data)` | `GroundwaterModel.execute` or measured passthrough | `GroundwaterAnalysisResult` |

**Evidence** — 12 HydromaAdapter assertions pass in `tests_adapters_full.py`.

## Repair 3: `engine/land/integration/water_adapter.py:230` (BLOCKER-P1-002)

**What** — Removed forbidden import at line 230:
`from services.map_engine.pipelines.runoff import RunoffPipeline`.

**Why** — ECO-00 Section 3: engine modules may not import from `services/`.
The import was inside a lazy try/except block but still crossed the layer
boundary. The imported `RunoffPipeline` was never actually invoked —
`calculate_runoff` implements SCS-CN inline.

**Changed**
- `engine/land/integration/water_adapter.py` — replaced the try/except
  import block with `self._runoff_pipeline = None` and updated docstrings.

**Evidence** — Static check in `tests_adapters_full.py` confirms no
`from services` or `import services` strings remain in the file.

## Validation

Test run: `python tests_adapters_full.py`

```
EngineAdapter Tests: 10 passed
HydromaAdapter Tests: 12 passed
LandService Tests: 23 passed
Forbidden-import check: 1 passed

=== Results: 45 passed, 0 failed ===
```
