# OPEN DECISIONS — ECO Nojin / HyDroMA

* **Status:** Active · **Opened:** 2026-10-11 · **Rule:** an agent may never close these rows.
  Only the listed approver closes one, with **reason + date + consequences** appended.
* Format: `D-XX · question · current repo state · recommended default · approver · needs decision by`

## Product & legal (must close before dependent phases)

| ID | Decision needed | Current repo state | Recommended default | Approver | By |
|---|---|---|---|---|---|
| D-01 | Frontend stack & repo layout | **CLOSED 2026-10-13** by the user's execution instruction: the frontend was *removed*, not chosen — `frontend/`, `docs/FRONTEND-DESIGN-2026-10-11.md`, `frontend_audit/`, `docs/project/FRONTEND-REDESIGN-PLAN.md`, `reports/ROADMAP-PHASE-5B-FRONTEND-2026-10-11.md`, `tools/check_frontend_layering.py`, `tools/frontend_bundle_audit.*`, `pnpm-workspace.yaml`, `.npmrc` and the CI `frontend` job are all gone; the repo is backend-only and the gateway's OpenAPI document is its contract | no frontend; a new one (any stack) is a new decision row, not a resumption of this one | Product owner + architecture | **closed** |
| D-18 | Reactivating a frontend after D-01 | **Product owner approved a new React/Vite initiative on 2026-10-14.** The local `frontend/` scaffold is untracked and is not part of the backend-only committed architecture; this work records a proposal, not an architecture sign-off | Keep `frontend/` as a separate client, generated/verified against OpenAPI; enforce authorization in APIs, not routes; stage by verified API capability; 15 locales remain incomplete until reviewed | Product owner + architecture | **architecture review pending** |
| D-02 | First-launch languages | notification templates ship EN/FA; locale middleware exists | `fa` (RTL default) + `en`; content language independent of UI language | Product owner | **before P12** |
| D-03 | Pilot jurisdiction(s) | none registered; `services/legal` has 8 static slugs | one pilot country + limited activity set, then extend | Product owner + legal counsel | **before P9** |
| D-04 | Eco Coin nature | code already live (KN-02): balances persisted via raw SQL, `ecocoin.transfer` permission exists — **writes frozen in P1** behind `HYDROMA_ECOCOIN_WRITES_ENABLED` (reads untouched) | keep the freeze until D-04 closes; treat as internal points, no transfer/convert claims; then either migrate to a governed ledger or remove | Product owner + finance + legal | **decision open; freeze in force since P1** |
| D-05 | Blockchain / tokenization | `services/blockchain` has Oracle/ImpactCertificate/EcoCoin ledger code; no external chain dependency in requirements | stay off-chain until a separate architecture decision is recorded | Architecture (separate ADR) | P5 |
| D-06 | NATS necessity | JetStream client implemented as optional import (degrades to no-op when `nats` is absent); dependency undeclared in `requirements*.txt`. **P2 analysis recorded 2026-10-11 (row still open — approver must sign):** live emit sites are commerce, marketplace/hub, legacy auth, sync/outbox; 5 of 9 publisher families have no callers (see `architecture/dependency-graph.md` event policy). Recommended resolution: keep NATS an **optional extra**, keep the outbox as the durability mechanism, forbid any phase from relying on JetStream until this row closes | Architecture + ops | **analysis done in P2; awaiting approver** |
| D-07 | Payment providers / settlement model | `com_payment_intents` + bank webhook (fail-closed secret) exist; provider is not selected | keep webhook+idempotency contract; document the chosen provider set | Finance + security + legal | **before P6** |
| D-08 | Session model | gateway applies CSRF + Idempotency + rate-limit middleware; cookie/BFF decision undocumented | secure cookies + CSRF (already enforced by middleware) over bearer tokens in browser code; document per OWASP session management | Security + architecture | **before P12** |

## Architecture & money model (block P5/P6)

| ID | Decision needed | Current repo state | Recommended default | Approver | By |
|---|---|---|---|---|---|
| D-09 | Money source-of-truth & settlement model | **CLOSED 2026-10-11** by the user's execution instruction: `architecture/MONEY-CONTRACT-v1.md` ratifies the journal (`fin_journal_entries`) as the single source of truth; wallets/ecosystem/commerce are read models that post *through* finance in the same transaction | — (decided) | closed |
| D-10 | Shared user key for cross-ledger attribution | **CLOSED 2026-10-11** by the user's execution instruction: `users.id` is the shared key; `ledger_entries.user_id` added by `20261011_150000`; the cross-ledger report (`services/finance/cross_ledger_report.py`) is the sanctioned per-user view. Historical NULLs stay NULL — compensation, not retroactive edits | — (decided) | closed |
| D-11 | Which money domains may own balances | **CLOSED 2026-10-11** by the user's execution instruction: `services.finance` only; the static boundary scan in `test_p5_money_invariants.py` already holds and stays the guard | — (decided) | closed |
| D-12 | Offline scope (eco.md 3 tiers) | nothing implemented | Tier 1 public content read-only; Tier 2 drafts (tour proposal, village form, product draft); Tier 3 (payments, approvals) always server-authoritative | Product + security + architecture | P13 |
| D-13 | HyDroMA model release bar | registry has stub/unvalidated/validated + card-based honesty folding | publish only `validated`; surface status in every payload | Science owner | **P10 entry** |
| D-14 | Local-brand usage & village validation model | no code | separate: local approval ≠ brand permission ≠ legal trademark ≠ product certification | Community + legal counsel | P7 |

## Deployment & ops

| ID | Decision needed | Current repo state | Recommended default | Approver | By |
|---|---|---|---|---|---|
| D-15 | Hosting / deployment model | FastAPI monolith, single Alembic head | one deployable + staged rollout; no microservice split without load evidence | Architecture + security + ops | P15 |
| D-16 | WAL/SQLite posture (KN-09) | runtime 3.49.1 < 3.51.3 | upgrade SQLite **before** any WAL deployment; keep the gate check in P15 | Ops | **before P15** |
| D-17 | Backup/restore RPO/RTO | `runtime/backup.py` with sha256 manifests | drill restore in P4 and re-drill before every release | Ops | P4/P15 |

## Answered by the tree (recorded, no longer open)

* `duckdb`/`supabase`: **optional, commented out** — kept for legacy connectors (do not delete).
* API counting myth (113 vs 630): **113 registered routes / 630 documented paths — different things.** Closed.
* Import-guard 16-vs-0 contradiction: **0 violations is correct** (measured). Closed.
