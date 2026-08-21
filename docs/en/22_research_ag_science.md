# 22. Agricultural Science, Simulators & Scientific Cores — HyDroMa Master Research

**Date:** 2026-08-17 | **Status:** Approved | **Class:** Knowledge/Architecture
Persian full version (authoritative): `docs/fa/22_research_ag_science.md`.
Raw reports: `docs/fa/22_research_reports/` (a: simulators, b: fertilizers,
c: watershed/crops, d: HyDroMa implementation steps).

> Methodology note: the "monitoring" sub-agent produced an implementation
> roadmap instead of a monitoring report; section 4 below was completed from
> standard knowledge + this session's searches.

## 1. Crop & Hydrology Simulators
- Crop models: DSSAT/CERES, APSIM, AquaCrop (FAO), WOFOST, EPIC.
  AquaCrop core: B = WP × ΣTr (biomass = water productivity × cumulative
  transpiration); Y = B × HI.
- Hydrology: SWAT, HEC-HMS, MIKE SHE, HBV. Key equations:
  - FAO-56 Penman-Monteith ET0:
    ET0 = (0.408·Δ·(Rn−G) + γ·(900/(T+273))·u2·(es−ea)) / (Δ + γ·(1+0.34·u2))
  - Hargreaves-Samani: ET0 = 0.0023·(Tmean+17.8)·(Tmax−Tmin)^0.5·Ra
  - Richards: ∂θ/∂t = ∂/∂z[K(θ)·(∂h/∂z + 1)]
  - SCS-CN: Q = (P−0.2S)²/(P+0.8S), S = 25400/CN − 254
  - Saint-Venant (open-channel flow)
  - RUSLE: A = R·K·LS·C·P
- Numerical methods: finite difference/volume, RK4, Newton-Raphson, CFL
  stability; vectorize with NumPy/Numba, hot cores in C++20 via pybind11.
- Calibration/validation: NSE, RMSE, R², KGE, PBIAS; GLUE/PEST/Bayesian;
  Morris/Sobol sensitivity; Monte Carlo uncertainty; EnKF assimilation.
  Golden rule: never present simulated data as real observations.
- Service architecture: REST/OpenAPI, data contracts, FAIR, offline-first.

## 2. Biofertilizers, Fertilizers & Soil Amendments
- Biofertilizers: Rhizobium, Azotobacter, Azospirillum, PSB, KSB, PGPR
  (siderophores, IAA, ACC-deaminase), AMF mycorrhiza, cyanobacteria,
  compost/vermicompost, green manure; carriers (peat/liquid/granule).
- Fertilizer chemistry: NPK blending (urea/DAP/MOP linear mix), urea
  hydrolysis, nitrification inhibitors (DCD/NBPT), slow/controlled release,
  chelated micronutrients (EDTA/EDDHA/DTPA, amino-acid chelates), fertigation,
  compost C/N ratio (ideal 25–30:1).
- Amendments: biochar (pyrolysis 350–700°C), zeolite, gypsum (sodic soils),
  lime, superabsorbent hydrogels, sulfur, nano-amendments (note: field
  efficacy of some nano products still debated).
- N rate = (crop need − soil supply) / NUE (0.3–0.5 typical).
- 4R nutrient stewardship (right source/rate/time/place) + VRA.
- Market: global biofertilizers ~USD 2.7–3.3B in 2025 (Future Market
  Insights; GlobeNewswire → 11.08B by 2035); China: 11,358 registered
  products (Feb 2025).

## 3. Watershed Engineering & Resilient Crops
- Structures: check dams (loose rock/gabion/concrete), terracing, contour
  trenches/diversion channels, half-moon/banquette, gully plugs, grassed
  waterways, rainwater harvesting, percolation ponds, recharge wells, LID/BMP.
- Design: Rational Q = C·I·A; SCS-CN.
- Drought/salt/flood tolerance: deep roots, WUE, osmotic adjustment;
  halophytes (quinoa, salicornia); SUB1 submergence rice; local Iranian
  cultivars.
- Breeding: MAS, genomic selection, CRISPR/Cas9 (chickpea 4CL/RVE7 DNA-free
  drought editing; salt-tolerance reviews Springer 2024, Frontiers 2023),
  speed breeding, UAV phenotyping, biofortification, orphan crops
  (teff, millet, sorghum, amaranth).
- Resilient systems: intercropping, agroforestry, conservation agriculture.

## 4. Monitoring & Modern Tech (completed from standard knowledge)
- Indices: NDVI, EVI = 2.5·(NIR−R)/(NIR+6R−7.5B+1), SAVI (L=0.5),
  NDWI, NBR — Sentinel-2 10m via CDSE/STAC; Sentinel-1 SAR (soil moisture,
  floods), SMAP, SIF (OCO-2); drought indices SPI/SPEI/VCI/VHI.
- IoT: capacitive/TDR/FDR soil sensors, weather stations; MQTT/LoRaWAN/NB-IoT.
- UAV multispectral NDVI mapping; ML yield prediction; CNN pest detection;
  RAG assistant (existing); digital soil mapping; satellite carbon MRV;
  blockchain traceability.

## 5. HyDroMa Implementation Roadmap (from research-d)
- Phase 1: watershed structure modules (HP-WH-01..05), RUSLE erosion with
  C-factor from NDVI, microbial consortium recommender (HP-BT-01), vegetation
  module (HP-VG-01/02).
- Phase 2: integrated modeling (SWAT+, RothC, AquaCrop/WEAP/HEC-RAS).
- Phase 3: early warning + anticipatory action (drought indices, alerts).
- Phase 4: interactive maps & dashboards. Phases 5–6: data assimilation,
  public API, multilingual scale-out.

## Sources (searched this session)
FAO AquaCrop PDF, HEC-HMS SCS-CN docs, Agron. J. 2009, Frontiers Plant Sci.
2023, Springer 2024, Yuan et al. 2022, Future Market Insights, GlobeNewswire,
UCAR Climate Data Guide, svs.gsfc.nasa.gov/5603, LottieFiles/Dribbble/Vercel
(see doc 23).
