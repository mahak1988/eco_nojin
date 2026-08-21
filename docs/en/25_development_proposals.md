# 25. Eco Nojin Development Proposals — C++ Core, Modules, Frontend, Admin, Security

**Date:** 2026-08-17 | **Status:** Proposed (awaiting approval) | **Class:** Technical
**Basis:** Deep study doc 24 + raw reports in `docs/fa/24_study_reports/`.
Persian full version (authoritative): `docs/fa/25_development_proposals.md`.

## 1) Strengthen the C++20 Core (`engine/cpp_core`)
- Architecture: 3 layers — `core/` (pure math), `api/` (stable C ABI via
  extern "C" for ctypes), `bindings/` (pybind11); CMake + dual-platform CI.
- New algorithms (priority): Richards 2D/3D (FVM + GMRES/ILU + Picard/Newton),
  2D Saint-Venant SWE (HLLC + slope limiter), dual-source FAO-56
  (Shuttleworth-Wallace), multi-layer soil-plant water model (tipping bucket
  + Feddes root uptake), AquaCrop-like yield core (B = WP×ΣTr, dynamic HI),
  RothC/Century carbon core, weir/orifice hydraulics for check dams,
  Xoshiro256** + Latin Hypercube sampling.
- Performance: SIMD/AVX, OpenMP, SoA memory layout, memory pools.
- Quality: >90% core coverage, analytical-solution tests (Green-Ampt, wave),
  fuzz testing, regression benchmarks in CI.

## 2) Develop Basic/Incomplete Modules
- P1 (Phase 8): EcoCoin 70/15/10/5 engine + wallet UI; marketplace +
  traceability; VerificationOracle migration replacing simulated blockchain
  with a verifiable hash-chain registry on PostgreSQL.
- P2: Real Sentinel-2 ingestion (CDSE/S3) + NDVI/EVI/SAVI/NDWI/NBR; mandatory
  `data_source` simulated/real labels; SPEI + phenology calendar.
- P3: PINN trained on real ERA5; RAG upgrade TF-IDF → local embeddings
  (Ollama/bge-m3) with precise citations; yield prediction ML.
- P4 (from doc 22): NPK fertilizer calculator, biofertilizer/amendment
  recommender, auto watershed-structure designer (SCS-CN), resilient-cultivar
  recommender, climate dashboard (CMIP6 + GISTEMP).
- P5: unify the two DBs, migrate to PostgreSQL, real DVC pipeline.

## 3) Frontend — i18n, Components, UI
- Fix mojibake (modules/ai, profile, register, "âœ“", broken LEARNING_KEY);
  complete 36 missing keys (fa fallback); migrate gradually to next-intl or
  enforce key schema checks in CI.
- Unify navigation (drop old Navbar, single SiteNav); add global
  error/not-found/loading files; add /modules index (currently 404);
  connect or remove 11 orphan panels; fix /science crash
  (science-dashboard.tsx:110 useMemo at module scope).
- Optimize: replace FontLanguageProvider 500ms polling with events;
  extend React Query instead of raw fetch.
- UI: Lottie animations (doc 23) with prefers-reduced-motion; real PWA icons
  + enable registerServiceWorker; Persian typography per component spec.

## 4) Complete the Admin Panel
- KPI dashboard (users, transactions, errors, uptime) with recharts + CSV/PDF.
- Content CRUD with per-language translation status; bot/channel metrics
  (Telegram/Eitaa/Bale/Rubika + USSD/SMS/Voice) with test-send; error
  aggregation view with retry; users + RBAC + admin MFA; EcoCoin/ledger
  monitoring; model registry with calibration status; simulated/real data
  badges; MRV carbon reports; safe settings (masked secrets, feature flags).

## 5) Strengthen Security Layers
- Critical: purge `.env.backup` + `settings.py.env-backup` from git history
  (git filter-repo) and rotate ALL secrets; add gitleaks/detect-secrets
  pre-commit hook.
- Auth: JWT_SECRET from env only; short-lived access + rotating refresh;
  HttpOnly cookie instead of localStorage; admin MFA; lockout + audit log.
- API: authorization tests for all 147 endpoints; enable rate limiting,
  strict CORS, security headers, HTTPS; dependency scanning (pip-audit /
  npm audit) in CI; verify CVE-2025-66478 fix on Next 16.3.1.
- Data: encryption at rest (Postgres TLS), secrets manager, RLS, simulated/
  real data isolation, ledger audit (hash-chain), encrypted backups.

## Execution Order
1. Critical fixes (useMemo, env-in-git, PWA, JWT) — 1–2 days
2. Admin panel (KPI, errors, RBAC) — 1 week
3. Frontend (nav, orphans, i18n, /modules) — 1 week
4. Phase 8 modules (EcoCoin, marketplace, Oracle) — 2 weeks
5. C++ core (3-layer + Richards 2D + SWE) — 3–4 weeks
6. Real remote sensing + ML — 3 weeks
Each step keeps tests green (371+) and bilingual docs (STD).
