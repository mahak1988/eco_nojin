# 27. Implementation Plan for the Hydroma Nojin PDF + Gap vs World Standards

**Date:** 2026-08-17 | **Status:** Proposed | **Class:** Strategic/Technical

## Part A — Implementation Plan (7 phases, ~18 weeks)

**4 principles:** (1) integrate proven open-source models instead of
reimplementing them (SWAT+, AquaCrop-OSPy, RothC, HEC-RAS are validated
globally; keep the C++ core for custom solvers and hot loops); (2) real data
before any claim (simulated/real labels mandatory); (3) implement approved
carbon methodologies (Verra VCS / Gold Standard, e.g., VM0032/VM0017) rather
than generic SOC; (4) security + standards from day one.

- **P1 (w1–2) Stabilize:** fix doc-24 criticals (/science crash, purge
  .env.backup from git + rotate keys, enable PWA, JWT to env); migrate to
  PostgreSQL/PostGIS; unify the two DBs.
- **P2 (w3–6) Real 3-level MRV (EM-01):** Sentinel-2 real pipeline via CDSE
  STAC (NDVI/LAI/C-factor monthly) + Landsat LST + Sentinel-1 soil moisture;
  IoT ingestion (MQTT/LoRaWAN: TDR, EC, Parshall flume) with QA/QC; offline
  citizen reporting (PWA form); public transparency dashboard
  (tCO₂e, erosion, SOC%, income, restored ha). Enables pilot Step 5.
- **P3 (w5–10) Integrated simulation chain:** couple SWAT+ → RUSLE →
  AquaCrop-OSPy → RothC (biochar pools) → WEAP and HEC-RAS via data
  contracts; 3 intervention scenarios; calibration SUFI-2 + MOD16A2/ESA CCI
  + modern Sobol sensitivity & Monte Carlo UQ.
- **P4 (w8–12) Decision Engine (EM-03):** What-if on the chain; crop-pattern
  recommendation (ECMWF 3-month forecast + soil moisture); sowing/harvest
  timing; ET₀-based irrigation alerts.
- **P5 (w10–14) Carbon (EM-06):** adopt VCS/GS methodology; map MRV data to
  methodology requirements; VerificationOracle as audit core; path to a pilot
  certificate (Dishmook).
- **P6 (w12–16):** EM-07 store, EM-08 LMS (for FFS Step 4), EM-05
  accounting/warehouse, EM-04 counselor/manager panel.
- **P7 (w14–18) Deploy/scale:** CI/CD (fix data tests), TLS, k6,
  independent security audit; **no Docker** (project architecture) — deploy on
  local PostgreSQL 16 / Windows service; bilingual docs per module.
- Team: 1–2 backend, 1 frontend, 1 data scientist. KPI: ≥90% PDF coverage,
  500+ tests, real MRV, first pilot verification report, pilot carbon cert.

## Part B — Gap vs World Science & Tech Standards (2025)

**Good news:** the PDF's concept is state of the art — coupled
SWAT–MODFLOW–AquaCrop is a 2025 research frontier (Hu et al., ScienceDirect);
SWAT+ released a global high-res framework (swat.tamu.edu, 2025); IoT soil
moisture + LoRaWAN are mainstream (2025 reviews). The 6-model chain is
scientifically current; the gaps are in execution depth.

**Gaps (10 areas):**
1. Modeling: world standard = integrate validated OSS (AquaCrop-OSPy, SWAT+,
   RothC); PDF says "6 models" without implementation; platform has only
   RUSLE/FAO-56/NDVI.
2. Calibration/UQ: world = data assimilation (EnKF), Sobol sensitivity,
   ML surrogates; PDF = SUFI-2 + KGE 55–65 (pre-study level).
3. Carbon: world = approved methodologies (VCS/GS/ART-TREES) + satellite
   digital MRV; PDF names Verra/GS without methodology; platform has IPCC
   module + planned Oracle.
4. IoT: world = MQTT/LoRaWAN/NB-IoT + QA/QC + OGC SensorThings; PDF lists
   sensors without protocols; platform: missing.
5. Spatial data: world = STAC/Planetary Computer/cloud-native; PDF's datasets
   (ERA5-Land, SoilGrids, Sentinel-2) are right; platform's CDSE/STAC is
   current — just needs real connection.
6. AI: world = digital twins, LLM advisory, ML prediction; PDF silent;
   platform ahead (RAG, PINN, index insurance).
7. Model data standards: world = ICASA/AgMIP for crop-model inputs; not
   mentioned in PDF; add to the model registry.
8. Security: world = NIST FIPS 203/204, secrets management; platform ahead
   (PQC implemented); complete per doc 25.
9. Deployment: world = containerized, observability, managed Postgres;
   PDF = self-hosted Superset/PostGIS; platform: local PostgreSQL 16 + CI,
   docker-compose removed.
10. Digital inclusion: platform's 14 languages, offline-first, USSD/SMS/
    Voice + Iranian messengers is a real competitive advantage over
    smartphone-centric Western platforms.

**Verdict:** "PDF concept + world OSS models + existing platform
infrastructure" yields a region-leading position. The PDF is conceptually
aligned but pre-study in execution; the platform is ahead in AI/security/
inclusion and behind in real satellite data, model integration, IoT, and
carbon methodology compliance. Execute Part A (18 weeks).

## Sources (searched this session)
- Verra VCS: https://verra.org/programs/verified-carbon-standard/
- Arbonics Verra/GS: https://www.arbonics.com/knowledge-hub/abc-verra-and-gold-standard
- Remote sensing MRV market: https://dataintelo.com/report/remote-sensing-mrv-for-carbon-market
- SWAT-MODFLOW-AquaCrop 2025: https://www.sciencedirect.com/science/article/pii/S0378377425002306
- SWAT-AquaCrop 2017 (MDPI): https://www.mdpi.com/2073-4441/9/3/157
- SWAT+ 2025: https://swat.tamu.edu/news/2025/
- IoT soil moisture 2025: https://www.sciencedirect.com/science/article/pii/S294991192500053X
- IoT precision ag 2025 (PMC): https://pmc.ncbi.nlm.nih.gov/articles/PMC12116683/
