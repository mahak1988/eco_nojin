# 26. Gap Analysis: Project vs the "Hydroma Nojin" PDF — Step 0 to Final Step

**Date:** 2026-08-17 | **Status:** Approved | **Class:** Strategic
**Sources:** "هیدروما نوژین" PDF (205 pages, attachment 2026-08-17) vs actual
codebase state (doc 24 + raw reports in `docs/fa/24_study_reports/`).

## 1) Overall
- Pilot execution steps (0–5, 18 months): software support ~50%
- Platform modules EM-01..08: ~45% (3 partial, 5 incomplete)
- Integrated simulation chain (SWAT+ → RUSLE → RothC → AquaCrop → WEAP →
  HEC-RAS): ~20% (only RUSLE complete + basic models)
- Tech stack: ~60% (SQLite vs PostGIS; custom dashboards vs Superset;
  CDSE vs GEE; simulated blockchain vs Ethereum)
- **Overall software platform: ~40–45%** of the PDF spec

## 2) Pilot Steps (گام ۰–۵)
- **Step 0** (prep, GIS 1:2000 maps, permits): no GIS map repository (EM-02
  could host) — medium gap
- **Step 1** (contour lines, spiral canals, infiltration pits): watershed
  module exists (SCS-CN) but no auto layout/earthwork — medium
- **Step 2** (check dams, injection wells, reservoirs; produce Nojin/Hygro):
  formulation base exists; no production calculator linked to inventory
  (EM-05) — medium
- **Step 3** (full planting, Nojin moisture spray): crop module basic; no
  planting-pattern recommender (EM-03 core) — high
- **Step 4** (FFS schools, 20 farmer observers): chat/RAG exists; no real
  LMS (EM-08) or counselor panel (EM-04) — high
- **Step 5** (monthly monitoring + verification via Eco Nojin): satellite
  indices basic but `earth_search` is SIMULATED; **real 3-level MRV is the
  biggest gap** — high

## 3) Platform Modules (EM-01..08)
- EM-01 MRV: Level 1 partial (NDVI only, simulated), Level 2 IoT sensors
  missing, Level 3 KoboToolbox offline missing, public transparency
  dashboard incomplete → biggest gap
- EM-02 Knowledge Hub: docs good, but no searchable product repository —
  partial
- EM-03 Decision Engine: AquaCrop/RothC not implemented, no What-if,
  no ET₀ irrigation alerts → high
- EM-04 Career/psych counseling: human service; missing counselor/manager
  panel
- EM-05 Accounting/warehouse: ledger + EcoCoin wallet in Phase 8; basic
- EM-06 Carbon facilitation: IPCC module exists; Verra/GS connection
  missing (VerificationOracle planned) → high
- EM-07 B2B/B2C store: marketplace incomplete in Phase 8
- EM-08 LMS: no tests/certificates/progress → high

## 4) Simulation Chain (PDF section 41)
Present: RUSLE (basic), FAO-56/Hargreaves ET₀, CMIP6 scenarios, NDVI/Numba
flood routing.
Missing: **SWAT+ (largest scientific gap), AquaCrop, RothC, WEAP, HEC-RAS
(basic Saint-Venant exists), and the coupled chain** with scenario matrix
(Baseline/Medium/Intensive). Data: ERA5-Land, SoilGrids, Sentinel-2 real,
SUFI-2 calibration.

## 5) Tech Stack
PostGIS: migration planned; Superset: replaced by custom Next.js dashboards
(keep); GEE: replaced by CDSE/Copernicus (equivalent); Ethereum: simulated
blockchain — decide real chain vs VerificationOracle; KoboToolbox: missing.

## 6) Priorities
1. Real 3-level MRV (EM-01) — required for Step 5
2. Simulation chain: SWAT+, AquaCrop, RothC (C++ core per doc 25)
3. Decision Engine What-if + irrigation alerts (EM-03)
4. Carbon link (Verra/GS) via VerificationOracle; store (EM-07); LMS (EM-08)
5. PostGIS + DB unification

Reaching ~60% after Phase 8/9; 90%+ requires the simulation chain + real
MRV (3–6 months with current team).

## Sources
- PDF text: `.openclaw/tmp/hydroma_nojin_pdf.txt` (sections 6, 41, 51)
- Codebase state: doc 24 + `docs/fa/24_study_reports/`
- Filling proposals: doc 25
