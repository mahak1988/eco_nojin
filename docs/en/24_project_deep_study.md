# 24. Eco Nojin Deep Study — Consolidated Report

**Date:** 2026-08-17 | **Status:** Approved | **Class:** Technical/Strategic
Persian full version: `docs/fa/24_project_deep_study.md`.
Raw study reports: `docs/fa/24_study_reports/` (a: backend, b: frontend,
c: data/ML/infra, d: docs/strategy).

## 1) Verified Overview
- ~24,650 Python LOC, ~10,268 TS/TSX LOC
- Backend tests: **371 passed** (93s, run 2026-08-17): 191 unit + 77
  integration + 101 data/ML + 2 benchmark; C++ core 70/70; frontend vitest 18/18
- API: 147 endpoints / 23 routers; 206 page.tsx files, 170-route registry
- Stack: Next.js 16.3.1, React 19.2.8, Tailwind v4, React Query 5, recharts
  3.10, Python 3.11 + FastAPI, C++20 core via pybind11/ctypes
- 14 languages (fa/en 389 keys; 12 others 353 — 36 missing); channels:
  Web, PWA, USSD, SMS, Voice + Telegram/Eitaa/Bale/Rubika bots

## 2) Strengths
Strong green test coverage; broad scientific domain (soil/climate/hydrology/
erosion/carbon/satellite/scenarios); real 14-language RTL; solid charts kit
(hydro log-scale, SSP comparison); shadcn/Radix UI kit with localized
data-table; extensive bilingual docs (STD-001..015).

## 3) Risks (priority)
**Critical:**
1. `/science` crash — `science-dashboard.tsx:110` useMemo at module scope
   (verified line 110; Invalid hook call at runtime)
2. Credentials in git — `.env.backup` and
   `engine/hydroma/config/settings.py.env-backup` are tracked (verified via
   `git ls-files`); purge from history + rotate keys
3. PWA effectively disabled — sw.js exists but `registerServiceWorker` never
   called; placeholder 70-byte PNG icons (breaks offline-first promise)

**High:**
4. Hardcoded JWT key (backend report) → move to env, rotate
5. Two parallel nav systems (old Navbar 23 pages vs SitePage/SiteNav 154)
6. `/modules` route 404 (no index page); no error/not-found/loading files
7. 16 orphan frontend files incl. 11 big panels (violates Zero Orphan Files)
8. Persian mojibake in modules/ai, profile, register + broken LEARNING_KEY="***"
9. 36 untranslated i18n keys; custom Context i18n instead of next-intl
10. Data tests failing in CI; two parallel DBs (econojin.db /
    hydroma_research.db)
**Medium:**
11. `typescript.ignoreBuildErrors: true`, `lint --max-warnings=1000`
12. FontLanguageProvider polls with setInterval 500ms
13. Only 2 components use React Query (rest raw fetch + JWT in localStorage)
14. Tokenomics discrepancy: 70/15/10/5 (Phase 8 doc) vs EcoCoin whitepaper
15. CVE-2025-66478 documented; verify fix status (Next upgraded to 16.3.1)

## 4) Recommended Actions
1. Fix science-dashboard useMemo; git filter-repo to purge .env backups +
   rotate all keys; enable registerServiceWorker
2. Unify navigation; add error/not-found/loading; add /modules index; fix
   mojibake; connect or remove 11 orphan panels
3. JWT to env; single DB; restore data CI; resolve tokenomics; translate 36 keys
4. New Phase 8/9 modules (see doc 22) must use the module registry + UI kit

## 5) Sources
Raw reports in `docs/fa/24_study_reports/` (study-a/b/c/d). Evidence this
session: real pytest run (371 pass), git ls-files check, line-110 check,
/modules index check.
