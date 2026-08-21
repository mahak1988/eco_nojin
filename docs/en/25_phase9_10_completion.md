# Phase 9 & 10 Completion Report — Eco Nojin

**Date:** 2026-08-17 · **Branch:** feature/phase-b-alembic

## Phase 9 — Academic / Open-Science Layer (تمل)

| # | Item (master plan) | Status | Evidence |
|---|---|---|---|
| ⭐8 | Research dashboard: notebooks + model/dataset search | ✅ (dashboard + search) | `/science` page: 4 KPI cards, dataset DataTable (search/sort/pagination/CSV), citation index, model cards; notebook runner deferred to ops (Jupyter kernel) |
| ⭐9 | Zenodo + DOI | ✅ (honest client) | `services/science/zenodo.py` — `GET /api/v1/science/zenodo/status` returns `not_configured` without `ZENODO_TOKEN`; `POST /api/v1/science/datasets/{slug}/doi` → 501 honest when unconfigured; never fabricates a DOI |
| ⭐10 | Auto-citation in AI answers | ✅ | `POST /api/v1/ai/chat` now returns `citations[]` matched from the offline model-registry citation index (OpenAlex/Crossref connect later) |
| ⭐11 | Model/dataset cards (limits, validity, fidelity) | ✅ | `MODEL_CARDS` (22 cards) exposed via `GET /api/v1/science/model-cards` + rendered in the science dashboard (HuggingFace-style) |
| ⭐12 | AGROVOC knowledge graph | ✅ (offline) | `services/science/agrovoc.py` — 41 concepts with real FAO AGROVOC URIs, fa/en aliases; `GET /api/v1/science/agrovoc?q=` |
| RAG multilingual | ✅ (existing keyword RAG) | `engine/hydroma/ai_assistant/rag_engine.py` (TF-IDF) |

## Phase 10 — Advanced Operations, Scale, Pilot (تمل)

| # | Item | Status | Evidence |
|---|---|---|---|
| ⭐13 | Self-healing watchdog | ✅ | `scripts/watchdog.py` — EMA latency/error trend analysis (pure `analyze_samples()` unit-tested), restart command, human-in-the-loop by default, `--auto-restart` opt-in |
| ⭐14 | Post-quantum crypto (ML-DSA/ML-KEM) | ✅ | `services/ledger/pqc.py` — ML-DSA-65 signatures (FIPS 204) + ML-KEM-768 encapsulation (FIPS 203) on `cryptography` 50; round-trip tests; fail-fast if primitives missing |
| WhatsApp (Meta Cloud API) | ✅ (skeleton) | `services/bots/adapters/whatsapp.py` — token-gated, webhook verify + inbound parser; activates only with `WHATSAPP_TOKEN` |
| Index insurance (step 1) | ✅ | `engine/hydroma/insurance/index_insurance.py` + `POST /api/v1/insurance/index` — NDVI seasonal index vs reference, linear payout ramp; explicit "no pricing without actuarial review" |
| ⭐15 | Field pilot protocol (3 villages) | ✅ (protocol doc) | `docs/en/26_field_pilot_protocol.md` + fa — NDVI vs ground-truth, farmer acceptance, university collaboration |
| Load testing | ✅ (smoke) | `scripts/load_test.py` — concurrent probes, p50/p95/error report |
| Scale / 10k users | ⏳ (staged) | Next: k6/Locust + autoscaling after deployment target chosen (Liara/VPS) |
| Independent security audit | ⏳ | Requires deployment target |

## API Surface Added (5 new endpoints + 2 extended)

- `GET /api/v1/science/model-cards[?slug=]`
- `GET /api/v1/science/agrovoc?q=`
- `GET /api/v1/science/zenodo/status`
- `POST /api/v1/science/datasets/{slug}/doi` (501 honest when unconfigured)
- `POST /api/v1/insurance/index` + `GET /api/v1/insurance/capabilities`
- `POST /api/v1/ai/chat` → `citations[]` field

## Test Coverage

- `tests/integration/test_phase9_10.py` — **14 tests** (model cards 3, AGROVOC 2, Zenodo 2, PQC 2, insurance 3, watchdog 1, AI citations 1) — all green.

## Honest Outstanding (external / user action)

1. `ZENODO_TOKEN` → real DOI publishing (Zenodo account required).
2. Crossref/OpenAlex keys → live DOI resolution in citations.
3. AGROVOC online sync (SKOS full graph) — offline map is explicit and versioned.
4. ERA5 licence acceptance + CDSE creds → live ERA5/Sentinel-2.
5. WhatsApp/Meta app review + tokens.
6. Deployment target + TLS + k6 scale test + independent audit (post-deploy).
7. Actuarial review before any insurance premium offering.
