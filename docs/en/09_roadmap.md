# 09. Roadmap

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Phase Map (from `00_master_plan.md`) vs Reality

| Phase | Scope | Current state |
|---|---|---|
| 1 — Research & MVP | soil, water, crop simulation; SQLite/DuckDB | ✅ Mostly done (engine, API, tests) |
| 2 — Ecosystem & materials | biochar/compost, small watershed structures | 🟡 Compost + watershed calculators done; biochar guidance in KB only |
| 3 — Risk & crisis | drought/flood early warning, index insurance | 🟡 Flood routing + SSP scenarios done; EWS/insurance triggers pending |
| 4 — Inclusion & economy | nomad routing, marketplace, micro-credit, tokens | 🟡 Marketplace + USSD done; routing, credit, tokens pending |
| 5 — Global scale | carbon verification, blockchain ledger, PQC, international APIs | 🔴 Scaffolding only |

## 2. Completed (verified)

- HyDroMa engine: Muskingum-Cunge routing, van Genuchten soil physics,
  vegetation indices, FAO-56/Hargreaves ET0, RUSLE (C++ core, 35 tests green).
- API gateway with 11 router areas; health endpoint.
- Marketplace (catalog, orders, traceability) — in-memory.
- Carbon estimate calculator with project registry.
- Scenario engine (SSP, crop, what-if, Monte Carlo).
- Satellite analysis pipeline (STAC search + simulated bands).
- RAG knowledge assistant (TF-IDF, 10 FAO-aligned documents).
- Next.js PWA frontend, 14 languages, offline hooks, Capacitor config.
- USSD/SMS gateway (en/fa/ar).
- Test suite: 125/126 passing at last full run (one stale assertion pending).

## 3. Immediate Next Steps (priority order)

1. **Git + CI** — initialize repository; pin dependencies; run tests in CI.
2. **Real satellite data** — replace simulated bands with actual GeoTIFF
   downloads; add cloud masking and quality flags.
3. **Fix known defects** — `datetime` import bug in carbon verify endpoint;
   stale `mobile_features` test; CORS wildcard; README Persian encoding.
4. **AuthN/AuthZ** — implement the auth service (OIDC) and protect writes.
5. **Carbon pathway** — pick Verra methodology (ARR or VM0042), implement
   baseline/additionality/leakage/permanence; keep `/verify` clearly marked
   as internal until accredited verification is possible.
6. **Data layer upgrade** — PostGIS schema + Alembic migrations; persist
   marketplace/carbon/sync state.

## 4. Phase 3–5 Milestones

- **EWS:** integrate NASA POWER + forecast feeds into drought/flood indices
  with threshold alerts via SMS/USSD.
- **Insurance:** index-based trigger contracts over historical NDVI/rainfall.
- **Nomad routing:** forage availability from NDVI time series + migration
  corridors.
- **Ledger & MRV:** cryptographic hashing of measurements; consortium
  blockchain integration; PQC-ready signatures (ML-KEM/ML-DSA).
- **Ecotourism & gig economy:** listings, reviews, micro-payments.
- **International APIs:** OGC API Features + WaterML 2.0 outputs; GODAN/FAO
  data exchange profiles.

## 5. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| No version control today | git init immediately |
| Simulated satellite data mistaken for real | Remove/flag before pilot |
| Carbon numbers presented as certified | Standards doc + UI disclaimers |
| Placeholder services assumed live | Status tables in docs; per-service README |
| English-only RAG vs Persian users | Localized KB corpus next iteration |
| Hardcoded API URL in frontend | Configurable base URL |

## 6. Success Criteria (end of Phase 2)

- Field pilot with 3 pilot villages: real satellite NDVI verified against
  ground truth, compost/watershed recommendations adopted, USSD access used
  by ≥50 % of households.
