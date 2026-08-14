# 02. HyDroMa Engine

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Overview

HyDroMa is the scientific and computational engine of the Eco Nojin platform.
It is a hybrid engine: an orchestration layer in Python, a JIT-accelerated
numerical path (Numba), and a high-performance C++20 core with optional
pybind11 bindings. Every kernel has a numerically identical Python counterpart
so results are consistent regardless of the execution path.

## 2. Layers

1. **Python orchestration layer** (`engine/hydroma/`): API routers, data
   ingestion (satellite/meteorological providers), RAG knowledge assistant,
   scenario engine, marketplace logic, USSD/SMS gateway logic, database access.
2. **Accelerated numerical layer** (`engine/hydroma/cpp_bridge/`): Numba-JIT
   kernels for flood routing, vegetation indices, and soil physics, with
   automatic fallback to pure NumPy when Numba is unavailable.
3. **C++ core** (`engine/cpp_core/`): C++20 library with the same kernels —
   hydrology, soil physics, erosion (RUSLE), climate (FAO-56), vegetation
   indices — plus a pybind11 module `hydroma_core` for direct Python use.

## 3. Module Inventory

| Module | Path | Status |
|---|---|---|
| Core data model | `engine/hydroma/core/` | Implemented (SQLAlchemy, SQLite) |
| Hydrology (Muskingum-Cunge) | `cpp_bridge/hydrology_fast.py`, `cpp_core/src/hydrology.cpp` | Implemented |
| Soil physics (van Genuchten) | `cpp_bridge/soil_physics_fast.py`, `cpp_core/src/soil.cpp` | Implemented |
| Vegetation indices | `cpp_bridge/indices_fast.py`, `cpp_core/src/indices.cpp` | Implemented |
| Erosion (RUSLE) | `cpp_core/src/erosion.cpp` | Implemented (C++) |
| Climate (FAO-56 PM, Hargreaves) | `climate/et_calculator.py`, `cpp_core/src/climate.cpp` | Implemented |
| Carbon calculator | `carbon/calculator.py` | Implemented (estimate mode) |
| Scenarios (SSP, crop, Monte Carlo) | `scenarios/` | Implemented (simplified) |
| Satellite analysis | `satellite/` | Implemented (⚠ simulated bands) |
| Marketplace | `marketplace/` | Implemented (in-memory demo) |
| Knowledge assistant (RAG) | `ai_assistant/` | Implemented (TF-IDF) |
| Watershed structures | `watershed/` | Implemented (partial) |
| USSD/SMS gateway | `ussd/` | Implemented |
| Benchmarks | `performance/benchmarks.py` | Implemented |
| Groundwater (Richards), Saint-Venant, ML, MRV, blockchain | — | Planned |

## 4. Numerical Methods and References

- **Flood routing:** Muskingum-Cunge (Cunge 1969; Chow et al. 1988; HEC-HMS).
  Unconditionally stable, O(n) per timestep, physically based attenuation.
  Wave parameters from the kinematic-wave approximation of Manning's equation.
- **Soil water retention:** van Genuchten (1980) closed-form equation;
  conductivity via the van Genuchten-Mualem model. Texture parameters after
  Carsel & Parrish (1988).
- **Erosion:** RUSLE A = R·K·LS·C·P (Renard et al. 1997); LS factor per
  McCool et al. (1987); R-factor precipitation estimator per Renard &
  Freimund (1994) — a coarse estimate, measured R is preferred operationally.
- **Reference evapotranspiration:** full FAO-56 Penman-Monteith (Allen et al.
  1998) including net radiation balance, and Hargreaves-Samani (1985) as a
  temperature-only fallback (FAO-56 recommended).
- **Climate scenarios:** CMIP6 SSP pathways (IPCC AR6), simplified regional
  projections for the Middle East/Iran region.
- **Crop simulation:** simplified AquaCrop-style water-productivity approach
  (Steduto et al. 2009) — an educational approximation, not a validated
  AquaCrop deployment.

## 5. Knowledge Assistant

The RAG assistant (`ai_assistant/`) retrieves from a curated, FAO-aligned
knowledge base using TF-IDF + cosine similarity, returns cited answers with a
confidence score, and degrades gracefully when no document matches. The corpus
is English-only at present; Persian/Arabic retrieval is planned.

## 6. Performance

`performance/benchmarks.py` and `tests/benchmarks/` compare Numba vs NumPy
paths (10–50× expected on large satellite arrays). The C++ core provides the
same kernels for deployment-time performance where JIT warm-up is undesirable.

## 7. Scientific Honesty Notes

- Satellite band data are currently **synthetic (simulated)** in
  `satellite/providers/earth_search.py`; production use requires real
  GeoTIFF download before any field deployment.
- Carbon figures are **pre-verification estimates**; see `05_standards.md`.
- All approximations are documented at the function level with primary
  literature citations.

## 8. References

- Allen, R.G. et al. (1998). FAO Irrigation and Drainage Paper 56.
- Carsel, R.F., Parrish, R.S. (1988). Soil Sci. Soc. Am. J. 52:1762-1764.
- Cunge, J.A. (1969). J. Hydraul. Res. 7(2):205-230.
- Hargreaves, G.H., Samani, Z.A. (1985). Appl. Eng. Agric. 1(2):96-99.
- McCool, D.K. et al. (1987). Trans. ASAE 30:1387-1396.
- Renard, K.G. et al. (1997). USDA Agriculture Handbook No. 703.
- Renard, K.G., Freimund, J.R. (1994). J. Hydrology 157:287-306.
- Steduto, P. et al. (2009). "AquaCrop — The FAO crop model." Agron. J. 101.
- van Genuchten, M.Th. (1980). Soil Sci. Soc. Am. J. 44:892-898.
