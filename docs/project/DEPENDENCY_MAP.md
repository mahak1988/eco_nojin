# DEPENDENCY MAP — ECO Nojin / HyDroMA

* **Status:** Active · **Recorded:** 2026-10-11 · **Sources:** `tools/detect_imports.py`,
  `tools/check_service_boundaries.py`, `architecture/*.yaml`, `docs/ARCHITECTURE-REFERENCE-2026-10-11.md`

## 1. Hard boundaries (enforced, currently 0 violations)

```
engine/**  ──✗──▶  services/**            (banned; engine is inbound-only)
services/** ──✗──▶  engine internals      (banned except the sanctioned facade)
services/** ──▶──▶  engine/*  via  services/_gateway_facade.py   (the only legal bridge)
* ──▶──▶ database.config / database.base   (sanctioned persistence-bridge exceptions, ADR-014)
```

* 8 architecture rules total; import guard: **0 violations**; service boundaries: **140 edges,
  140 policy entries, 0 stale**.
* Policy data files that must be edited **with a dated rationale** (never silently):
  `tools/import_guard_policy.json`, `architecture/rules.yaml`,
  `architecture/eco-nojin-architecture.yaml`, `architecture/dependency-graph.md`.

## 2. Phase dependency graph (from `PHASE_PLAN.md`)

```
P0 ─▶ P1 ─▶ P2 ─────────┬──▶ P3 (identity) ─┐
                        │                   ├──▶ P6 (marketplace) ─┐
                        ├──▶ P4 (data) ─────┼──▶ P5 (money) ───────┼──▶ P8 (tourism)
                        │                   │                      │
                        └──▶ P10 (engine) ──┼──▶ P11 (daneshyar/   │
                                            │      tasmimyar/eco) │
                        P2 ──▶ P7 (governance) ────────────────────┤
                                            └──▶ P9 (compliance) ──┘
                        P12 (frontend) ── retired 2026-10-13 (no longer a dependency)
                        P13 (perf) ── needs stable P6/P8 routes
                        P14 (QA) ── needs the phases it audits
                        P15 (release) ── needs P14 + D-15/D-16 closed
```

Parallel-safe today (measured): **P3 ∥ P4 ∥ P10** after P2 (different file trees:
`services/auth`+gateway / `alembic`+`database/models.py` / `engine/**`).
Serial-required: **P5 before P6**, **P6 before P8's booking→settlement E2E**, **P2 before P12**.

## 3. Money-flow dependency (the 5-ledger chain)

```
commerce (com_orders / com_payment_intents)
   │ writes via finance contract (D-09)
   ▼
finance (fin_accounts / fin_journal_batches / fin_journal_entries)   ← source of truth
   ▲                     ▲                     ▲
wallet (eco_wallets)   ledger (ledger_entries/  ecosystem
                        escrow_records)       (eco_balance_*)
blockchain (ecocoin_balances, raw SQL — KN-02)  ← currently BYPASSES this chain
```

Until D-09/D-10 land: no domain may add new balance writes; every change must extend the finance
journal contract and add a reconciliation test.

## 4. File-ownership map for parallel agents (anti-collision)

| Owner | Exclusive write scope | Never touches |
|---|---|---|
| A01 | `services/api_gateway/routers/tourism_router.py`, `services/blockchain/**` (freeze), `docs/project/**` | engine, database/models.py |
| A02 | `architecture/**`, `docs/project/DEPENDENCY_MAP.md`, contract docs | application code |
| A03 | `services/auth/**`, `services/api_gateway/middleware/**` | database/models.py |
| A04 | `database/models.py`, `database/hub.py`, `alembic/**` (one new revision per phase) | services business logic |
| A05 | `services/finance/**`, `services/wallet/**`, `services/ledger/**` | marketplace, tourism |
| A06 | `services/marketplace/**`, `services/commerce/**` | finance internals |
| A07 | `services/api_gateway/routers/nojin.py`, `services/nojin/**`, `services/rangeland/**`, new `services/village/**`, new `services/territory/**` | finance internals |
| A08 | `services/api_gateway/routers/dashboard.py` (public endpoints), `services/tourism/**` | finance internals |
| A09 | `services/legal/**`, new `services/compliance/**` | finance internals |
| A10 | `engine/**` | services, database/models.py |
| A11 | `services/knowledge/**`, `services/tasmimyar/**` | engine internals |
| A12 | (frontend/** retired 2026-10-13 — no tree to own) | — |
| A13 | `services/api_gateway/routers/lms.py`, perf configs, `tools/coverage_gate.py`-adjacent tooling | feature code |
| A14/A15 | test plans, release tooling | feature code |

## 5. External coupling to keep in view

* **OpenAPI (630 paths)** is the public HTTP contract — `tools/export_openapi.py` writes the
  snapshot (default `docs/openapi.json`). There is no client tree any more, so no typed-client
  drift gate runs in CI. Any API change must state version status: compatible / additive /
  breaking-with-version / deprecated-with-migration.
* **`Idempotency-Key` + `EcoNojinException` + Decimal money serialization** are cross-cutting
  contracts (P2 ratifies them; every phase inherits them).
* **NATS (optional, undeclared pin)** — event owners and retry/idempotency rules required before any
  phase depends on it (D-06).
* **SQLite 3.49.1 vs WAL-safe 3.51.3** — deployment gate, not a phase dependency.
* **Heavy RAG/torch tests** crash xdist under memory pressure (KN-15) — keep them in a shard of
  their own (`-n` smaller, or `pytest services/ai,tests` alone).

## 6. Remaining data-provisioning items (owner-gated)

| Item | Owner | Required action | Notes |
|------|-------|----------------|-------|
| `services/nojin/**` catalog | A07 | Provision `MATERIALS` registry + `NojinMaterial`/`NojinRecipe`/`NojinSoilType` data from authoritative source | No fabrication; currently empty `{}` |
| `data/master/eco_nojin_master.duckdb` | A04/A10 | Add `ref_rules`, `ref_units_reference` (+ 150 reference tables) | Currently only 5 tables; wiring in `database/hub.py` is done |
| `lms` env vars | A13 | Set `SUPABASE_URL`, `SUPABASE_ANON_KEY` | Ops-level; router is 503-ready |
| RAG/torch test suite | A14/A15 | Isolate RAG tests in own shard (`-n` smaller) | KN-15: xdist memory crash |
