# 05. Standards

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Guiding Frameworks

The platform aligns with the international frameworks recorded in
`99_conversation_summary.md`: FAO, IFAD, World Bank, WMO, ISO, OGC,
UN SDGs, GODAN, and global carbon/environmental reporting frameworks.

## 2. Scientific / Technical Standards

| Standard | Where applied | Status |
|---|---|---|
| FAO-56 (Penman-Monteith ET0) | `climate/et_calculator.py`, C++ core | Implemented |
| FAO AquaCrop principles | `scenarios/crop_scenarios.py` | Simplified approximation |
| RUSLE (USDA Handbook 703) | C++ core (`erosion.cpp`) | Implemented |
| van Genuchten / Mualem | soil physics kernels | Implemented |
| OGC API Features, WaterML 2.0 | output formatting | Planned |
| WMO meteorological guidance | NASA POWER usage | Partially applied |
| IPCC AR6 (SSP scenarios) | `scenarios/climate_scenarios.py` | Simplified regional tables |

## 3. Carbon Standards — honest status

- **ISO 14064:** architecture reserves MRV hooks, but no accredited
  verification workflow exists yet.
- **Verra VCS / Gold Standard:** the calculator cites their methodologies
  and rates, but current output is a **pre-verification estimate** with a
  blanket 15 % uncertainty discount. Real compliance requires additionality,
  baseline setting, leakage accounting, permanence buffers, and independent
  verification by an accredited body. The current `/verify` endpoint is an
  internal workflow demo, not certification.
- **Next step:** pick one methodology (e.g., Verra VM0017/VM0042 for soil
  carbon or ARR for afforestation) and implement its full workflow.

## 4. UN SDG Mapping

- SDG 1 (no poverty), 2 (zero hunger), 5 (gender equality), 6 (clean water),
  8 (decent work), 13 (climate action), 15 (life on land) — primary targets.

## 5. Data Standards

- Geographic data: GeoPackage/PostGIS geometries (planned).
- Time series: netCDF/CF conventions for climate rasters (planned).
- Identifiers: batch numbers and traceability codes follow farm → lot →
  product chain (implemented in marketplace traceability).

## 6. Compliance Review Cadence

Standards alignment is reviewed at each phase milestone
(see `09_roadmap.md`); deviations must be recorded in `99_conversation_summary.md`.
