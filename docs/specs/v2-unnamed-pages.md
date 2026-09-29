# v2 Unnamed Pages — audit of the 46 §5.3 items with no path

**Status:** specification. Nothing here is implemented.
**Scope:** the 46 pages `hydroma-nojin-master-plan.md` §5.3 describes in prose instead of naming a path.
**Date:** 2026-09-29.

---

## 0. How the routes were read

The three earlier passes that got this wrong read `services/api_gateway/routers/` and saw
only the shims. This pass resolved mounts from the app itself.

**The app was imported.** `services.api_gateway.main` imports cleanly in this environment
(`FastAPI 0.141.1`, Python 3.12.10, `.venv`), so `app.openapi()` was read directly. No
server was started; the lifespan never ran, so nothing below reflects runtime state.

One trap worth recording: `app.routes` is **not** usable on FastAPI 0.141. Every
`include_router` result is a `fastapi.routing._IncludedRouter` with `path = None`, so a
naive `app.routes` dump returns 86 rows of which 11 are routes and 75 are empty
placeholders. `app.openapi()` resolves them and returns **497 paths, 283 of them GET**.
Any script reproducing this must use the OpenAPI dump, not `app.routes`.

**Cross-check against the committed artefact.** `openapi.json` holds 489 paths / 277 GET
and is a **strict subset** of the live app — 8 paths are live but unpublished:

```
/api/v1/audit/certificate/{project_id}   /api/v1/security/status
/api/v1/audit/credits                    /api/v1/security/step-up/methods
/api/v1/audit/queue                      /api/v1/security/anti-phishing
/api/v1/audit/vote                       /api/v1/security/events
```

Nothing is in `openapi.json` that is not live, so the file is stale, not wrong.
`scripts/check-api-contract.mjs:15` reads `openapi.json`, not the app — so those 8 are
invisible to the contract gate today. See §4, item 1.

Probes that confirm the mount resolution is right (the ones the plan's own methodological
warning at §1.2 asks for): `GET /api/v1/commerce/orders` (`services/commerce/routers/commerce.py:145`),
`GET /api/v1/manual/sites`, `GET /api/v1/audit/queue` (`services/api_gateway/routers/audit.py:74`),
`GET /api/v1/security/status` (`services/api_gateway/routers/security_router.py:125`),
`GET /api/v1/finance/ledger/entries` (`services/finance/routers/finance.py:281`).
All five are present. `services/api_gateway/routers/disputes.py` is a shim — 11 lines that
re-export `services.dispute_resolution.routers.disputes` — and its contract appears as
`GET /api/v1/disputes` in the dump. The shim was followed.

**No claim below rests on a directory name.** `services/insurance/` does not exist; the
contract does, at `services/api_gateway/routers/insurance.py:40`. That is precisely the
error the audit caught, so it is recorded here rather than left implicit.

### Conventions read from the code, not assumed

| Convention | Where it is decided |
|---|---|
| `status` vocabulary: `live · capability · static · planned · unavailable` | `apps/web/src/lib/domains/page-catalog.ts:47` |
| `endpoint: null` + no route file → `unavailable`; `endpoint` + no route file → `planned` | `page-catalog.ts:277-289` |
| slug = `` `${domain}-${path.split('/').filter(Boolean).join('-')}`.replace(/[{}]/g,'') `` | `scripts/generate-resource-pages.mjs:430-431` |
| `sourceOfTruth` must exist on disk or be declared in `registry.ts` | `apps/web/src/lib/domains/page-catalog.test.ts:236-238` |
| `rowsKey` must be read from the handler; an undeclared contract is **not generated** | `generate-resource-pages.mjs:469-696`, `:828-833` |
| mutations are skipped on purpose | `generate-resource-pages.mjs:197-216` |
| a declared-content path (no contract, indexable) is legal and already used | `docs/frontend/contract-allowlist.json` |

### The two rendering facts that decide the marketplace rows

1. `/market` is reserved (`page-catalog.ts:222`) and `/market/[...segments]/page.tsx:42`
   ends in `if (!resolved) notFound()`. It serves only `{group.prefix}-{index}` slugs from
   `apps/web/src/lib/marketplace-routes.ts`. **A catalogue entry under `/market/` does not
   produce a page.** Every one of the 14 wallet rows needs a real route file.
2. `/(catalog)/[...slug]` is a required catch-all at the root, so `/admin/**`,
   `/hydroma/**`, `/research/**` and `/public/**` entries without their own route file are
   served by the catalogue catch-all. Those four domains *do* get a page from an entry.

---

## 1. Summary table — the 46

`status` is the catalogue status the entry would resolve to **today**.
"contract" is the mounted GET that answers the surface, or `none`.

### Wallet and finance (14) — marketplace

| # | Plan item | Route | Slug | Shape | Backing | Contract | Pri | Flags |
|---|---|---|---|---|---|---|---|---|
| 1 | EcoWallet hub | `/market/wallet` | `marketplace-market-wallet` | record | partial | `GET /api/v1/finance/wallet` | w1 | **route exists**; today bound to phantom `/api/v1/ecowallet` |
| 2 | history and statements | `/market/wallet/statements` | `marketplace-market-wallet-statements` | rows | partial | `GET /api/v1/finance/ledger/entries` | w1 | needs own route file |
| 3 | withdrawal and settlement | *(form)* | — | **form** | form | `POST /api/v1/ecowallet/redeem` | w1 | **FORM, not a route** |
| 4 | fees and transparency | `/market/wallet/fees` | `marketplace-market-wallet-fees` | rows | **unbacked** | none | w2 | — |
| 5 | escrow centre by order | `/market/escrow/orders` | `marketplace-market-escrow-orders` | rows `entries` | partial | `GET /api/v1/marketplace/payments/{payment_id}/escrow` | w1 | **SWALLOWED** by `/market/escrow/[id]` |
| 6 | micro-credit request + tracking | `/market/credit` | `marketplace-market-credit` | rows | **unbacked** | none | w2 | needs own route file |
| 7 | farmer credit score | `/market/credit/score` | `marketplace-market-credit-score` | record | **unbacked** | none | w3 | — |
| 8 | climate index insurance | `/market/insurance` | `marketplace-market-insurance` | record | partial | `GET /api/v1/insurance/capabilities` | w2 | — |
| 9 | claim event + payment trigger | *(form)* | — | **form** | form | `POST /api/v1/blockchain/oracle/report` | w2 | **FORM, not a route** |
| 10 | my policies | `/market/insurance/policies` | `marketplace-market-insurance-policies` | rows | **unbacked** | none | w3 | — |
| 11 | advanced arbitration | `/market/arbitration` | `marketplace-market-arbitration` | rows | partial | `GET /api/v1/disputes` | w2 | page + 2 forms |
| 12 | multi-stage returns | `/market/returns` | `marketplace-market-returns` | rows | **unbacked** | none | w2 | page + form |
| 13 | commission statement | `/market/commission` | `marketplace-market-commission` | rows | **unbacked** | none | w3 | — |
| 14 | tax centre | `/market/tax` | `marketplace-market-tax` | rows | **unbacked** | none | w3 | — |

### Scientific (10) — hydroma

| # | Plan item | Route | Slug | Shape | Backing | Contract | Pri | Flags |
|---|---|---|---|---|---|---|---|---|
| 15 | in-product scientific assistant | `/hydroma/assistant` | `hydroma-hydroma-assistant` | rows `conversations` | partial | `GET /api/v1/ai/history` | w1 | page + POST form |
| 16 | map studio | `/hydroma/map-studio` | `hydroma-hydroma-map-studio` | record | partial | `GET /api/v1/soil/history/{farm_id}` | w2 | composite missing |
| 17 | uncertainty workshop | `/hydroma/uncertainty` | `hydroma-hydroma-uncertainty` | rows | partial | `GET /api/v1/hydroma/models/{model_id}/validation` | w2 | 3 more reads unmounted |
| 18 | MRV hub | `/hydroma/mrv` | `hydroma-hydroma-mrv` | rows `models` | **backed** | `GET /api/v1/hydroma/mrv` | w1 | — |
| 19 | reproducibility office | `/hydroma/reproducibility` | `hydroma-hydroma-reproducibility` | rows | partial | `GET /api/v1/hub/shared` | w2 | 2 reads unmounted |
| 20 | offline WASM compile | — | — | — | **wrong-context** | none | w3 | build target, not a page |
| 21 | local calibration management | `/hydroma/calibration` | `hydroma-hydroma-calibration` | rows | partial | none on the gateway | w2 | engine exists, no read |
| 22 | run-queue observer | `/hydroma/runs` | `hydroma-hydroma-runs` | rows `runs` | **backed** | `GET /api/v1/simulation/runs` | w1 | — |
| 23 | collaborative scenario editor (CRDT) | `/hydroma/scenarios/editor` | `hydroma-hydroma-scenarios-editor` | rows `events` | partial | `GET /api/v1/sync/pending` | w2 | page + POST form |
| 24 | model review room | `/hydroma/models/review` | `hydroma-hydroma-models-review` | rows `cards` | partial | `GET /api/v1/science/model-cards` | w2 | — |

### Admin (10) — admin

| # | Plan item | Route | Slug | Shape | Backing | Contract | Pri | Flags |
|---|---|---|---|---|---|---|---|---|
| 25 | feature flags | `/admin/feature-flags` | `admin-admin-feature-flags` | rows | partial | none | w1 | **route exists**, already honest |
| 26 | event_bus monitor | `/admin/event-bus` | `admin-admin-event-bus` | rows | partial | `GET /api/v1/admin/overview/health` | w2 | source value is a literal |
| 27 | jobs queue + replay | `/admin/jobs` | `admin-admin-jobs` | rows | partial | none mounted | w1 | **route exists**; 9 ops unmounted |
| 28 | multi-tenant management | `/admin/tenants` | `admin-admin-tenants` | rows | **backed** | `GET /api/v1/organizations` | w1 | **auth mismatch** |
| 29 | design token management | `/admin/design-tokens` | `admin-admin-design-tokens` | rows | **wrong-context** | n/a | w3 | **route exists**, build-time source |
| 30 | translation management | `/admin/localization/translations` | `admin-admin-localization-translations` | rows | partial | `GET /api/v1/admin/content/{item_id}/translations` | w1 | **route exists**; current binding is another domain |
| 31 | missing-translation monitor | `/admin/localization/coverage` | `admin-admin-localization-coverage` | rows | **wrong-context** | n/a | w3 | duplicate of #30 |
| 32 | pseudo-localisation tool | — | — | — | **wrong-context** | n/a | — | must not be routable |
| 33 | multilingual media management | `/admin/media` | `admin-admin-media` | rows | **unbacked** | none | w3 | only an images POST exists |
| 34 | responsible-AI dashboard | `/admin/responsible-ai` | `admin-admin-responsible-ai` | record | partial | `GET /api/v1/security/status` | w2 | 2 contracts absent from `openapi.json` |

### Research (6) — research

| # | Plan item | Route | Slug | Shape | Backing | Contract | Pri | Flags |
|---|---|---|---|---|---|---|---|---|
| 35 | dataset DOI and citation | `/research/science/datasets` | `research-research-science-datasets` | rows `datasets` | **backed** | `GET /api/v1/science/datasets` | w1 | **route exists**; mint half is a POST |
| 36 | internal preprint server | `/research/preprints` | `research-research-preprints` | rows | **unbacked** | none | w3 | — |
| 37 | reproducible pipeline | `/research/pipelines` | `research-research-pipelines` | rows | partial | `GET /api/v1/hub/runs` | w2 | 2 more reads unmounted |
| 38 | federated learning between pilots | `/research/federated` | `research-research-federated` | rows | **unbacked** | none | w3 | — |
| 39 | local ethics registration | `/research/ethics` | `research-research-ethics` | rows | **unbacked** | none | w3 | — |
| 40 | study-pattern library | `/research/patterns` | `research-research-patterns` | rows | **unbacked** | none | w3 | — |

### Regional (6) — public

| # | Plan item | Route | Slug | Shape | Backing | Contract | Pri | Flags |
|---|---|---|---|---|---|---|---|---|
| 41 | pilot landing — Iran | `/public/regions/iran` | `public-public-regions-iran` | record | **wrong-context** | none | w3 | content page |
| 42 | pilot landing — Pakistan | `/public/regions/pakistan` | `public-public-regions-pakistan` | record | **wrong-context** | none | w3 | content page |
| 43 | pilot landing — Afghanistan | `/public/regions/afghanistan` | `public-public-regions-afghanistan` | record | **wrong-context** | none | w3 | content page |
| 44 | pilot landing — Türkiye | `/public/regions/turkiye` | `public-public-regions-turkiye` | record | **wrong-context** | none | w3 | content page |
| 45 | pilot landing — Middle East | `/public/regions/middle-east` | `public-public-regions-middle-east` | record | **wrong-context** | none | w3 | content page |
| 46 | pilot landing — global | `/public/regions/global` | `public-public-regions-global` | record | **wrong-context** | none | w3 | content page |

---

## 2. The tally

| Backing | Count | Which |
|---|---:|---|
| `backed` | **3** | 18 MRV hub · 22 run-queue observer · 28 multi-tenant |
| `partially backed` | **19** | 1, 2, 5, 8, 11, 15, 16, 17, 19, 21, 23, 24, 25, 26, 27, 30, 34, 35, 37 |
| `unbacked` | **12** | 4, 6, 7, 10, 12, 13, 14, 33, 36, 38, 39, 40 |
| `wrong-context` | **10** | 20, 29, 31, 32, 41–46 |
| **forms, not pages** | **2** | 3 withdrawal-and-settlement · 9 claim-event-and-trigger |
| **total** | **46** | |

A further **7** items are a page *plus* a form on the same surface — 11 (escalate/resolve),
12 (return/refund), 15 (`POST /api/v1/ai/chat`), 23 (`POST /api/v1/sync/merge`),
27 (`POST /api/v1/jobs/{job_id}/retry`), 30 (`POST /api/v1/admin/content/{item_id}/translate`),
35 (`POST /api/v1/science/datasets/{slug}/doi`). The page shows the recorded state; the
form performs the action. They are not counted as forms above because a page genuinely
exists for them.

**Six of the 46 already have a route file on disk**, which the plan's "all 46 are
pathless" framing does not anticipate: 1 (`/market/wallet`), 25, 27, 29, 30
(`/admin/feature-flags`, `/admin/jobs`, `/admin/design-tokens`,
`/admin/localization/translations`) and 35 (`/research/science/datasets`). Four of those
five admin/marketplace pages are already *correct* — they read a real local artefact and
render `AdminUnavailable` for the missing contract. What they need is the endpoint binding
corrected, not a new page.

---

## 3. Dynamic-swallow and routing collisions the 46 would create

`generate-resource-pages.mjs:301-314` (`shadowedFallbacks`) is the rule: a dynamic
catalogue path of equal depth swallows a static sibling at the same depth. Re-run today
it reports **0** conflicts — the five the earlier generator named were all `POST`
mutations, which the script itself records as false positives at
`generate-resource-pages.mjs:286-292`:

> `/market/villages/engagements`, `/hydroma/carbon/verra/search`,
> `/admin/content/generate-draft`, `/system/iot/devices/provision-qr`,
> `/hydroma/carbon/tokenize`

So the specific examples in the brief are documented and retracted upstream, not
outstanding. Against the **on-disk** tree the check is stricter, and it finds three real
problems for the 46:

1. **`/market/escrow/orders` (#5) is swallowed by `/market/escrow/[id]`.** Both are three
   segments; `apps/web/src/app/[locale]/market/escrow/[id]/page.tsx` exists on disk.
   Without its own route file, `/market/escrow/orders` renders the escrow-by-identifier
   page with `id = "orders"`.
   **Disambiguation:** put the order view *under* the dynamic segment —
   `/market/escrow/orders/{order_id}` — and have it resolve the payment itself, which is
   the missing build anyway. Do **not** add a sibling `orders/` directory.
2. **All 13 other `/market/**` rows are unreachable without a route file**, for the
   §0 reason: `/market/[...segments]` returns `notFound()` for any slug that is not
   `{prefix}-{index}`. #1, 2, 4, 6, 7, 8, 10, 11, 12, 13, 14 are all in this state. A
   catalogue entry alone is a 404 for every one of them.
3. **The six regional pages create a future hazard, not a present one.** They are six
   static siblings under `/public/regions/`. They are safe today. The moment anyone adds
   `/public/regions/{region}` as a dynamic entry, all six are captured and
   `shadowedFallbacks` will refuse it. The catalogue already carries this hazard in
   `/learn/legal/{locale}/{slug}`, which is why `paramConflict` (`generate-resource-pages.mjs:424-427`)
   exists. Record the six as static siblings and forbid the dynamic sibling.

No collision exists for the 24 non-marketplace rows: `/admin/**`, `/hydroma/**`,
`/research/**` and `/public/**` have no depth-matching dynamic route except
`/research/workspace/{experimentId}` and `/hydroma/{carbon,climate,economics}/{model_id}`,
and none of the 24 sits at those depths.

---

## 4. What must be built before these can exist

Ordered by how many of the 46 each item unblocks. "Ops" counts operations already
written in a router that no request can reach.

### 1. Regenerate `openapi.json` — 0 lines of business code, 8 contracts become visible

`.venv\Scripts\python.exe scripts\generate_openapi_schema.py`. The committed schema is
missing 8 live paths (§0), and `scripts/check-api-contract.mjs:15` reads the file rather
than the app. A catalogue entry bound to `GET /api/v1/security/status` or
`GET /api/v1/audit/queue` is therefore treated as an *unpublished* path by the gate
today, so #34 cannot pass until this runs. **Cheapest item on this list and a
precondition for one page outright.**

### 2. Mount five written routers — 5 lines in `main.py`, 4 pages

| Router | Unmounted ops | Unblocks |
|---|---|---|
| `services/jobs/router.py:17` | 6 GET (`/jobs`, `/jobs/{job_id}`, `/jobs/{job_id}/events`, `/jobs/{job_id}/queue-position`, `/jobs/stats`, `/jobs/stats/summary`) + `POST /{job_id}/cancel|retry` | **#27 jobs queue** (replay is `POST …/retry` → form) |
| `services/provenance/router.py:22` | `GET /api/v1/provenance`, `GET /api/v1/provenance/models` | **#19 reproducibility office** |
| `services/validation/router.py:5` | `GET /api/v1/hydroma/validation/{run,checks,reference-data}` | **#17 uncertainty workshop** |
| `services/contracts/router.py:15` | `GET /api/v1/contracts`, `/{service_name}/compatibility`, `/diff` | **#37 reproducible pipeline** |
| `services/api_gateway/routers/motors.py:20` | `GET /motors/{list,health,status/{run_id},manual-sites}` | strengthens **#22** |

Each mount also needs one `CONTRACT_SHAPES` row (`generate-resource-pages.mjs:469`), or
the generator refuses the page by design (`:828-833`). This confirms the plan's §9
Phase 2 claim with a measured number rather than an estimate.

### 3. A research-registry read — 1 contract, 4 pages

One `GET /api/v1/research/registry?kind=` returning `preprints`, `ethics-registrations`,
`study-patterns` and `federated-cohorts` unblocks **#36, #38, #39, #40**. The best ratio
among the genuinely unbacked items. `/research/experiments/*` already carry
`endpoint: null` (6 entries, `status: 'unavailable'`) and would be the first rows.

### 4. A wallet-scoped money ledger — 1 contract family, 3 pages

`GET /api/v1/finance/ledger/entries` exists (`services/finance/routers/finance.py:281`,
`response_model=list[dict]`, `require_user` at `:288`) but takes no filter, so it cannot
answer statements, fees or commission. Adding `account_id` and `kind` query parameters
to that one handler unblocks **#2 statements, #4 fees, #13 commission**. A single read
is the whole difference between three `unavailable` entries and three `planned` ones.

### 5. A credits and underwriting read — 1 service, 3 pages

`GET /api/v1/insurance/capabilities` (`services/api_gateway/routers/insurance.py:40`)
returns `{"index": ..., "pricing": false, "phase": "phase10-step1"}` — an honest
capability statement that says outright it cannot price. `POST /api/v1/insurance/index`
is the only other operation. A `credit` read plus `underwrite` and `policies` reads
unblocks **#6, #7, #10**, and is the precondition for turning #8's `pricing` true.
Note `GET /api/v1/ecosystem/trust-score/{user_id}`
(`services/api_gateway/routers/ecosystem.py:232`, also unmounted) is an *activity
trust* score, not a credit score; citing it for #7 would be the exact substitution this
project forbids.

### 6. A real event-bus probe — 1 read, 1 page, and a correctness fix

`GET /api/v1/admin/overview/health` declares `response_model=list[ChannelHealth]`
(`services/api_gateway/routers/admin_overview.py:81`) and one row is a hardcoded literal:

```python
# services/api_gateway/routers/admin_overview.py:93
ChannelHealth(name="NATS Event Bus", status="healthy", latency_ms=3.7, last_check=...)
```

**A page built on that would render a fabricated latency of 3.7 ms and a fabricated
"healthy".** Replacing the literal with a real probe against `services/api_gateway/eventbus/`
is the precondition for #26, not an enhancement to it.

### 7. A returns / commission / tax read — 1 service, 3 pages

Two mutations already exist and no read does: `POST /api/v1/inventory/movements/return`
and `POST /api/v1/marketplace/payments/{payment_id}/escrow/refund`. A return-tracking
read unblocks **#12**; the same read with a `kind` covers **#13, #14**. Nothing in
`services/` mentions tax at all.

### 8. A calibration and scenario read on the gateway — 1 read, 2 pages

`engine/hydroma/calibration/calibrator.py`, `engine/hydroma/calibration/model_calibrator.py`
and `engine/hydroma/simulation/calibration.py` are real modules, and **no route exposes
them**. The engine existing is not a contract; #21 stays `unavailable` until a read
exists. `GET /api/v1/sync/status` + `GET /api/v1/sync/pending` already carry the CRDT
outbox for **#23**, so only the scenario document itself is missing.

### 9. A media library read — 1 read, 1 page

Only `POST /api/v1/marketplace/products/{product_id}/images`
(`services/api_gateway/routers/marketplace.py:223`) exists. #33 needs a read; without
one it is a mutation and the generator skips it.

### 10. `declaredContent` for 8 paths — 0 contracts, 8 pages

Six regional landings (#41–46) plus #31 and #20 are content. Adding them to
`docs/frontend/contract-allowlist.json` makes them `status: 'static'` and **indexable**
under the published rule (`page-catalog.ts:283-288`), with no contract invented. This is
the largest count for the smallest work, and it is the only correct use of that file for
#20 and #32's absence.

---

## 5. Which of the 46 should be dropped

The audit concluded the target is over capacity. Measured here, of the 46:
**3 can be built today, 19 need one contract each, 10 are content, 2 are forms, and 6
already have a route.** A recommendation to build fewer, honest pages is the useful
finding.

**Drop outright — 5.**

| # | Why |
|---|---|
| 32 pseudo-localisation tool | A developer tool. Routing it would make a dev affordance a public product surface. No contract, no user, and the honest home is `scripts/`. |
| 31 missing-translation monitor | Already delivered. `apps/web/src/app/[locale]/admin/localization/translations/page.tsx` imports `readLocaleCoverage` from `@/components/admin/admin-local-data` and reports coverage from `apps/web/messages/*.json` on every request. A second page duplicates it. |
| 20 offline WASM compile | A build target, not a document. There is no WASM module anywhere under `engine/` (filename scan returned nothing) and no contract could describe a compiler step. |
| 38 federated learning between pilots | No contract, no module, no pilot that federates yet. The nearest thing — `GET /api/v1/ecosystem/trust-score/{user_id}` — is a trust score, and reusing it would be a fabricated claim. |
| 39 local ethics registration | No contract and no registry to register into. Keep it as an innovation-backlog item, not a route. |

**Merge into a parent page rather than give a route — 3.** #6 micro-credit, #8 climate
index insurance and #9 claim event collapse into tabs of `/market/insurance`. The gateway
has one insurance contract and one claim mutation; three sibling routes would be three
pages over one record.

**Keep but hold at wave 3 until a contract exists — 6.** #7 credit score, #10 my
policies, #13 commission statement, #14 tax centre, #33 media management, #40
study-pattern library. Each is a legitimate surface; none has anything to render, and
`unavailable` + noindex is the correct state until then.

**Do not rebuild — 6.** #1, #25, #27, #29, #30, #35 already have route files. The work is
to correct the endpoint binding (or, for #1, replace the phantom `/api/v1/ecowallet` with
`/api/v1/finance/wallet`) and to mount the contracts #27 needs. #29 is already correct
and is classified `wrong-context` only in the sense that it is not an API page.

**Net result: 32 new routes, of which 3 are buildable today.** The remaining 29 are one
contract each or a content declaration, not 46 pages.

### Two access findings that outrank the page decisions

- **#28 multi-tenant at an `/admin/**` URL widens access.** `GET /api/v1/organizations`
  is `require_user` (`services/api_gateway/routers/organizations.py:92`), not an admin
  gate. Every neighbouring admin router uses `require_admin_with_mfa`
  (`admin_settings.py:39`, `admin_overview.py:43`, `admin_bots.py:43`,
  `admin_errors.py:68`, `admin_models.py:70`), `require_content_admin`
  (`admin_content.py:94`) or `require_security_admin` (`admin_security.py:50`). Serving
  the org list from an admin URL, and from `/workspace/overview` and `/workspace/team`
  which are already bound to it, hands the tenant directory to any signed-in user under a
  path that reads as privileged. Fix the auth or do not ship the page.
- **The admin pages are already noindex.** `/admin/feature-flags/page.tsx:47` and
  `/admin/jobs/page.tsx:30` both set `robots: { index: false, follow: false }`. The
  catalogue's `admin` group is `role-gated` and `noindex` is therefore the right posture
  for every row in that table; none of the ten should ever be indexed.

---

## 6. §5.3's 68 versus 74

**They do not reconcile through any category the plan failed to separate. 68 is a
miscount, and the plan already corrected it.** §0.1 row 3 states the change — 68 → 74 —
and gives the arithmetic: `8+6+8+14+6+6+10+10+6 = 74`, counted three times. The
`74 = 28 named-by-path + 46 described-in-prose` split in the §5.3 closing note follows
from the same sum. There is nothing else to explain; the 68 figure should be deleted
wherever it still appears rather than reconciled.

**Forms versus routes is a real split, but it is a different number and belongs in the
plan as one.** Of the 74:

| | count |
|---|---:|
| named by path and present (§5.3's 28) | 28 |
| described in prose, route-shaped | 44 |
| described in prose, wrong context (content or build-time) | 10 |
| **page-shaped total** | **82** … but only **72** are page-shaped: 74 − 2 forms |
| forms rather than pages | 2 |
| **can be built from a contract that exists today** | **31** |

**31 is the number the plan should carry for §5.3**: the 28 it already has, plus MRV hub,
run-queue observer and multi-tenant management. Every other one of the 46 needs a
contract, a content declaration, or a form.

---

## 7. Per-page catalogue entries

`status` is what `resolveCatalogStatus` (`page-catalog.ts:277-289`) returns for the entry
as it stands. Every `sourceOfTruth` below was checked to exist on disk, because
`page-catalog.test.ts:236-238` fails the suite otherwise. Copy follows the register of
`apps/web/messages/en.json` under `pageMeta.`: a short noun-phrase title and one line
that says what the gateway reports.

An entry with a contract and no route file resolves to `planned`. An entry with **no**
contract resolves to `unavailable`, and that is what the twelve unbacked rows get — an
endpoint string that does not resolve is the one thing this catalogue forbids.

---

### Wallet and finance

**1. EcoWallet hub** — `path: '/market/wallet'` · `endpoint: '/api/v1/finance/wallet'` ·
`method: 'GET'` · `status: 'planned'` → `'live'` · `shape: record` ·
`sourceOfTruth: services/finance/routers/finance.py`
`GET /api/v1/finance/wallet` (`finance.py:411`, `WalletBalanceResponse`, `require_user` at `:414`).
**Correction required:** the entry on disk declares `endpoint: '/api/v1/ecowallet'`, which
is not mounted — the plan itself lists it as a phantom path at §1.3. The read exists at
`/api/v1/ecowallet/wallet/{user_id}` and, for the caller's own balance, at
`/api/v1/finance/wallet`.
> `marketplace-market-wallet` — **Marketplace wallet** / *کیف پول بازارگاه* —
> "The wallet balance the gateway reports, or a statement that it could not be read." /
> *«مانده‌ای که دروازه گزارش می‌کند، یا بیان اینکه خوانده نشد.»* (unchanged — the key
> already exists in both catalogues)

**2. History and statements** — `path: '/market/wallet/statements'` ·
`endpoint: '/api/v1/finance/ledger/entries'` · `method: 'GET'` · `status: 'planned'` ·
`shape: rows`, **no `rowsKey`** — `finance.py:281` declares `response_model=list[dict]`, so
the payload *is* the array · `sourceOfTruth: services/finance/routers/finance.py`
Needs `account_id`/`kind` filters (§4 item 4) before it can be a statement page, and needs
its own route file (§3 item 2).
> `marketplace-market-wallet-statements` — **Wallet statements** / *صورتحساب کیف پول* —
> "The ledger entries the gateway holds for this wallet, in the order it returns them." /
> *«سطرهای دفترکل که دروازه برای این کیف پول نگه داشته است، به همان ترتیبی که برمی‌گرداند.»*

**3. Withdrawal and settlement — a form, not a route.** No catalogue entry. A catalogue
entry pointing at `POST /api/v1/ecowallet/redeem` or
`POST /api/v1/commerce/orders/{order_id}/settle` would never produce a page: the
generator drops every non-GET at `generate-resource-pages.mjs:208-216`. Ship the button on
`/market/checkout` and `/market/orders/{id}` and render the recorded state from
`GET /api/v1/commerce/orders/{order_id}/transitions` (`commerce.py:271`,
`response_model=list[str]`, `require_user` at `:273`).

**4. Fees and transparency** — `path: '/market/wallet/fees'` · `endpoint: null` ·
`method: 'GET'` · `status: 'unavailable'` · `shape: rows` ·
`sourceOfTruth: services/finance/routers/finance.py`
Nothing in `services/` names a fee. `POST /api/v1/compliance/greenwashing/disclosure`
(`services/api_gateway/routers/compliance.py`, unmounted) is the nearest disclosure
surface, and it is a mutation. A read must be built.
> `marketplace-market-wallet-fees` — **Fees and transparency** / *کارمزد و شفافیت* —
> "No fee schedule is published yet, so this page names what it is waiting for." /
> *«هنوز هیچ جدول کارمزدی منتشر نشده است؛ این صفحه می‌گوید منتظر چه چیزی است.»*

**5. Escrow centre by order** — `path: '/market/escrow/orders/{order_id}'` (**not**
`/market/escrow/orders` — §3 item 1) · `endpoint:
'/api/v1/marketplace/payments/{payment_id}/escrow'` · `method: 'GET'` ·
`status: 'unbacked'` for the order-keyed form · `shape: rows`, `rowsKey: 'entries'` ·
`sourceOfTruth: services/api_gateway/routers/marketplace.py`
The escrow read is keyed by **payment**, not order (`marketplace.py:1247`,
`response_model` list of entries, `require_user` at `:1250`). `POST …/escrow/release`
(`:1197`) and `POST …/escrow/refund` (`:1223`) are both `require_admin`. The order→payment
resolution is the missing build. The existing entry `/market/escrow/{id}` is bound to
`/api/v1/marketplace/payments`, the collection, not the escrow detail.
> `marketplace-market-escrow-orders-order_id` — **Escrow for an order** / *امانت سفارش* —
> "The escrow entries the gateway holds for this order's payment, with each transition." /
> *«سطرهای امانتی که دروازه برای پرداخت این سفارش نگه داشته است، با هر گذار.»*

**6. Micro-credit request and tracking** — `path: '/market/credit'` · `endpoint: null` ·
`method: 'GET'` · `status: 'unavailable'` · `shape: rows` ·
`sourceOfTruth: services/finance/routers/finance.py`
No credit facility, no application entity, no read. The request half is a `POST` and would
be a form regardless.
> `marketplace-market-credit` — **Micro-credit** / *تسهیلات خرد* —
> "No credit facility is published by the gateway yet, so nothing is listed here." /
> *«دروازه هنوز هیچ تسهیلات اعتباری منتشر نکرده است؛ پس فهرستی اینجا نیست.»*

**7. Farmer credit score** — `path: '/market/credit/score'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: record` ·
`sourceOfTruth: services/api_gateway/routers/finance.py`
Nothing in the mounted API computes a credit score.
> `marketplace-market-credit-score` — **Farmer credit score** / *امتیاز اعتباری کشاورز* —
> "No credit score is computed by the gateway, so no score is shown." /
> *«دروازه هیچ امتیاز اعتباری محاسبه نمی‌کند؛ پس امتیازی نمایش داده نمی‌شود.»*

**8. Climate index insurance** — `path: '/market/insurance'` ·
`endpoint: '/api/v1/insurance/capabilities'` · `method: 'GET'` ·
`status: 'planned'` · `shape: record` · `sourceOfTruth: services/api_gateway/routers/insurance.py`
`insurance.py:40` returns the index basis, `pricing: false`, and a note that payment needs
actuarial review. The page must render that, not a premium.
> `marketplace-market-insurance` — **Climate index insurance** / *بیمهٔ شاخص اقلیمی* —
> "The insurance capability the gateway declares, including that it cannot yet price." /
> *«توانایی بیمه‌ای که دروازه اعلام می‌کند، از جمله اینکه هنوز قیمت‌گذاری نمی‌تواند.»*

**9. Claim event and payment trigger — a form, not a route.** No catalogue entry.
`POST /api/v1/blockchain/oracle/report` and `POST /api/v1/blockchain/impact/certificate`
are both mutations. The readable half is
`GET /api/v1/blockchain/impact/certificate/{certificate_id}`.

**10. My policies** — `path: '/market/insurance/policies'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` ·
`sourceOfTruth: services/api_gateway/routers/insurance.py`
There is no policy entity in the API; `capabilities` describes a product class, not a
contract held by a person.
> `marketplace-market-insurance-policies` — **My policies** / *بیمهنامه‌های من* —
> "No policy record is held by the gateway for this account." /
> *«دروازه هیچ سابقهٔ بیمه‌ای برای این حساب نگه نمی‌دارد.»*

**11. Advanced arbitration** — `path: '/market/arbitration'` ·
`endpoint: '/api/v1/disputes'` · `method: 'GET'` · `status: 'planned'` · `shape: rows`,
no `rowsKey` — `services/dispute_resolution/routers/disputes.py:50` · `sourceOfTruth:
services/dispute_resolution/routers/disputes.py`
Read half is backed: the list at `:50` and the detail at `:61`, both `require_user`
(`:55`, `:76`). `POST /{dispute_id}/escalate` (`:87`) and `POST /{dispute_id}/resolve`
(`:71`) are the action half and are forms. "Advanced" — evidence, multi-stage — is not
in the contract; `/market/orders/{id}/evidence` is a page with no endpoint.
> `marketplace-market-arbitration` — **Dispute arbitration** / *داوری اختلاف* —
> "The disputes the gateway has recorded, with the stage each one has reached." /
> *«اختلاف‌هایی که دروازه ثبت کرده است، با مرحله‌ای که هرکدام به آن رسیده.»*

**12. Multi-stage returns** — `path: '/market/returns'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` · `sourceOfTruth:
services/api_gateway/routers/marketplace.py`
Two mutations exist (`POST /api/v1/inventory/movements/return`,
`POST /api/v1/marketplace/payments/{payment_id}/escrow/refund`) and no read of a return's
state.
> `marketplace-market-returns` — **Returns** / *مرجوعی چندمرحله‌ای* —
> "The gateway can record a return but publishes no read of one, so no return is listed." /
> *«دروازه می‌تواند مرجوعی ثبت کند اما خواندنی برای آن منتشر نمی‌کند؛ پس فهرستی نیست.»*

**13. Commission statement** — `path: '/market/commission'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` · `sourceOfTruth: services/finance/routers/finance.py`
The commission rate is not a field of any mounted response.
> `marketplace-market-commission` — **Commission statement** / *صورتحساب کمیسیون* —
> "No commission rate is published by the gateway, so no amount is stated here." /
> *«دروازه هیچ نرخ کمیسیونی منتشر نمی‌کند؛ پس مبلغی اینجا ذکر نمی‌شود.»*

**14. Tax centre** — `path: '/market/tax'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` · `sourceOfTruth: services/finance/routers/finance.py`
The word tax appears nowhere under `services/` as a financial concept.
> `marketplace-market-tax` — **Tax centre** / *مرکز مالیات* —
> "No tax record is published by the gateway for this account." /
> *«دروازه هیچ سابقهٔ مالیاتی برای این حساب منتشر نمی‌کند.»*

---

### Scientific

**15. In-product scientific assistant** — `path: '/hydroma/assistant'` ·
`endpoint: '/api/v1/ai/history'` · `method: 'GET'` · `status: 'planned'` · `shape: rows`,
`rowsKey: 'conversations'` · `sourceOfTruth: services/api_gateway/routers/ai_chat.py`
`ai_chat.py:255` returns `{"count": …, "conversations": […]}`; `require_user` at `:256`.
The answer itself is `POST /api/v1/ai/chat` (`:222`, `require_user`) — a form on the page.
> `hydroma-hydroma-assistant` — **Scientific assistant** / *دستیار علمی* —
> "The question history the gateway has stored for this account." /
> *«تاریخچهٔ پرسش‌هایی که دروازه برای این حساب نگه داشته است.»*

**16. Map studio** — `path: '/hydroma/map-studio'` · `endpoint:
'/api/v1/soil/history/{farm_id}'` · `method: 'GET'` · `status: 'partially backed'` ·
`shape: record` · `sourceOfTruth: services/api_gateway/routers/soil.py`
Four reads exist and none is a studio composite:
`GET /api/v1/soil/history/{farm_id}`, `GET /api/v1/satellite/indices`,
`GET /api/v1/elevation/grid/{site_id}`, `GET /api/v1/hub/shared`. The catalogue is
`static` on the read side, which is the honest way to render a composite of four
contracts rather than inventing a fifth.
> `hydroma-hydroma-map-studio` — **Map studio** / *مطب نقشه* —
> "The map layers the gateway can serve for one site, named one by one." /
> *«لایه‌های نقشه‌ای که دروازه برای یک سایت می‌دهد، یکی‌یکی نام‌برده.»*

**17. Uncertainty workshop** — `path: '/hydroma/uncertainty'` · `endpoint:
'/api/v1/hydroma/models/{model_id}/validation'` · `method: 'GET'` ·
`status: 'partially backed'` · `shape: record` —
`response_model=ValidationReport` at `hydroma_dashboard.py:752` is one document, not a list ·
`sourceOfTruth: services/api_gateway/routers/hydroma_dashboard.py`
Mounted today: the per-model validation read (`hydroma_dashboard.py:752`), plus the
engine-wide `GET /api/v1/hydroma/validation` (`hydroma_ops.py:20`, which runs
`services.validation.formula_checks.run_all`). Unmounted and written:
`GET /api/v1/hydroma/validation/run`, `/checks`, `/reference-data`
(`services/validation/router.py:5`) — three more reads with no work, per §4 item 2.
> `hydroma-hydroma-uncertainty` — **Uncertainty workshop** / *کارگاه عدمقطعیت* —
> "The validation and reference data the gateway holds for the selected model." /
> *«دادهٔ اعتبارسنجی و مرجعی که دروازه برای مدل انتخاب‌شده نگه داشته است.»*

**18. MRV hub** — `path: '/hydroma/mrv'` · `endpoint: '/api/v1/hydroma/mrv'` ·
`method: 'GET'` · `status: 'planned'` → `'live'` · `shape: rows`, `rowsKey: 'models'` ·
`sourceOfTruth: services/api_gateway/routers/hydroma_mrv.py`
`hydroma_mrv.py:139` returns `{"count": len(_SPECS), "models": _SPECS}` — the same shape as
the other nine hydroma list endpoints, already declared at
`generate-resource-pages.mjs:539-541`. The public aggregate is
`GET /api/v1/mrv/public/dashboard-summary` (record).
> `hydroma-hydroma-mrv` — **MRV hub** / *هاب MRV* —
> "The MRV tools the engine registers, with the run each one last recorded." /
> *«ابزارهای MRV که موتور ثبت کرده است، با آخرین اجرای هرکدام.»*

**19. Reproducibility office** — `path: '/hydroma/reproducibility'` ·
`endpoint: '/api/v1/hub/shared'` · `method: 'GET'` · `status: 'planned'` · `shape: rows`,
`rowsKey: 'runs'` · `sourceOfTruth: services/provenance/router.py`
`hydroma_hub.py:129` is mounted and is the shared-run read. The actual provenance records
are at `services/provenance/router.py:60` (`GET /api/v1/provenance`) and `:140`
(`GET /api/v1/provenance/models`) — **written, unmounted**. Mount them and this page stops
being a share link and becomes the office the plan describes.
> `hydroma-hydroma-reproducibility` — **Reproducibility office** / *دفتر انتقال‌پذیری* —
> "The provenance records and shared runs the gateway holds for this model version." /
> *«سوابق انتقال‌پذیری و اجراهای به‌اشتراک‌گذاشته‌شده‌ای که دروازه برای این نسخهٔ مدل دارد.»*

**20. Offline WASM compile — wrong context.** No entry. Not a document. There is no WASM
module under `engine/` and a compiler step cannot be described by a GET. If it ships, it
ships as a build artefact and a documented offline check, not a route. See §5.

**21. Local calibration management** — `path: '/hydroma/calibration'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` · `sourceOfTruth:
engine/hydroma/calibration/calibrator.py`
The engine modules are real — `engine/hydroma/calibration/calibrator.py`,
`engine/hydroma/calibration/model_calibrator.py`,
`engine/hydroma/simulation/calibration.py` — and **no route exposes any of them**. The
catalogue status must stay `unavailable`; the honest page names the modules as the thing
that exists and the missing read as the thing that does not.
> `hydroma-hydroma-calibration` — **Calibration** / *مدیریت کالیبراسیون* —
> "The engine holds calibration routines; the gateway publishes no read of them yet." /
> *«موتور روال‌های کالیبراسیون را دارد؛ دروازه هنوز خواندنی برای آن‌ها منتشر نکرده است.»*

**22. Run-queue observer** — `path: '/hydroma/runs'` · `endpoint:
'/api/v1/simulation/runs'` · `method: 'GET'` · `status: 'planned'` → `'live'` ·
`shape: rows`, `rowsKey: 'runs'` · `sourceOfTruth: services/api_gateway/routers/simulation.py`
`simulation.py:58` returns `{"count": len(rows), "runs": [...]}`, filterable by `site_id`
and `limit`. Live per-run progress is `GET /api/v1/simulation/progress/{run_id}` (`:135`).
> `hydroma-hydroma-runs` — **Run queue** / *صف اجرا* —
> "The simulation runs the gateway has recorded, newest first." /
> *«اجراهای شبیه‌سازی که دروازه ثبت کرده است، از جدید به قدیم.»*

**23. Collaborative scenario editor** — `path: '/hydroma/scenarios/editor'` ·
`endpoint: '/api/v1/sync/pending'` · `method: 'GET'` · `status: 'partially backed'` ·
`shape: rows`, `rowsKey: 'events'` ·
`sourceOfTruth: services/api_gateway/routers/sync.py`
`sync.py:173` returns `{"ok": …, "count": …, "events": [...]}`; `GET /api/v1/sync/status`
(`:25`) is the pair. The merge is `POST /api/v1/sync/merge` (`:301`) — a form. **No CRDT
module exists under `engine/`** (filename scan: nothing), so "collaborative" is currently
a sync outbox, and the page should say so rather than imply a CRDT document.
> `hydroma-hydroma-scenarios-editor` — **Scenario editor** / *ویرایشگر سناریو* —
> "The sync outbox the gateway holds for this scenario, with the conflicts it has not merged." /
> *«صندوق همگام‌سازی که دروازه برای این سناریو دارد، با تعارض‌های ادغام‌نشده.»*

**24. Model review room** — `path: '/hydroma/models/review'` · `endpoint:
'/api/v1/science/model-cards'` · `method: 'GET'` · `status: 'partially backed'` ·
`shape: rows`, `rowsKey: 'cards'` · `sourceOfTruth: services/api_gateway/routers/science.py`
`science.py:37` returns `{"count": …, "cards": [...]}`. `GET /api/v1/admin/models` is the
operator's list and is `require_admin_with_mfa` (`admin_models.py:70`) — it must not be
the backing contract for a page a researcher can open. There is no verdict read: nothing
in the API records a review outcome.
> `hydroma-hydroma-models-review` — **Model review** / *اتاق بازبینی مدل* —
> "The model cards the gateway publishes, with the validation each one reports." /
> *«کارت‌های مدلی که دروازه منتشر می‌کند، با اعتبارسنجی‌ای که هرکدام گزارش می‌دهد.»*

---

### Admin

Neighbouring auth in this area, read from the routers: `require_admin_with_mfa`
(`admin_settings.py:39`, `admin_overview.py:43`, `admin_bots.py:43`,
`admin_errors.py:68`, `admin_models.py:70`), `require_content_admin`
(`admin_content.py:94`), `require_security_admin` (`admin_security.py:50`),
`require_user_admin` (`admin_users.py:52`). Every new row needs one of these, and the
`admin` catalogue group is `role-gated` with `noindex`.

**25. Feature flags** — `path: '/admin/feature-flags'` · `endpoint: null` ·
`status: 'unavailable'` → the page is honest today · `shape: rows` ·
`sourceOfTruth: apps/web/src/lib/domains/registry.ts`
**Route exists and is correct.** The page reads the capability matrix from
`apps/web/src/lib/domains/registry.ts` and then renders `AdminUnavailable` for runtime
`ENABLE_*` flags with `source="services/api_gateway/routers/admin_settings.py"`
(`feature-flags/page.tsx:155-159`). No flag read is mounted — a keyword scan of all 277
mounted GETs for `flag` returns nothing. What this needs is a `GET /api/v1/admin/flags`
that reads `engine/hydroma/config/settings.py`; the page will pick it up with no edit.
> `admin-admin-feature-flags` — **Feature flags** / *پرچم ویژگی* —
> "Capability flags read from the registry; runtime flags are not yet published by the gateway." /
> *«پرچم‌های توانایی از رجیستری؛ پرچم‌های زمان اجرا هنوز از سوی دروازه منتشر نشده‌اند.»*

**26. Event-bus monitor** — `path: '/admin/event-bus'` · `endpoint:
'/api/v1/admin/overview/health'` · `method: 'GET'` · `status: 'unbacked'` ·
`shape: rows`, no `rowsKey` (`response_model=list[ChannelHealth]`) ·
`sourceOfTruth: services/api_gateway/routers/admin_overview.py`
**Do not build this page on the existing read.** `admin_overview.py:93` returns a
hardcoded `ChannelHealth(name="NATS Event Bus", status="healthy", latency_ms=3.7, …)`.
A page over it shows a latency that was never measured. A real probe is the precondition.
> `admin-admin-event-bus` — **Event bus** / *مونیتور event_bus* —
> "Channel health the gateway measures; the NATS row is not yet measured and says so." /
> *«سلامت کانال‌هایی که دروازه می‌سنجد؛ سطر NATS هنوز سنجیده نشده و همین را می‌گوید.»*

**27. Jobs queue and replay** — `path: '/admin/jobs'` · `endpoint: null` ·
`status: 'unavailable'` → `'planned'` on mount · `shape: rows` ·
`sourceOfTruth: services/jobs/router.py`
**Route exists and is already honest**: it renders `AdminSourceNote source="openapi.json"
ok={false}` (`jobs/page.tsx:87`). The contract is written — `services/jobs/router.py:17`
declares `GET /api/v1/jobs`, `/{job_id}`, `/{job_id}/events`,
`/{job_id}/queue-position`, `/stats`, `/stats/summary`, plus `POST /{job_id}/cancel` and
`POST /{job_id}/retry`. **None of the nine is mounted.** Replay is `POST …/retry` — a form
on the page, never a route.
> `admin-admin-jobs` — **Jobs queue** / *صف jobs* —
> "The compute jobs the gateway has queued; the replay action is a form on this page." /
> *«کارهای محاسباتی که دروازه در صف گذاشته است؛ کنش بازپخش فرمی روی همین صفحه است.»*

**28. Multi-tenant management** — `path: '/admin/tenants'` · `endpoint:
'/api/v1/organizations'` · `method: 'GET'` · `status: 'planned'` → `'live'` ·
`shape: rows` · `sourceOfTruth: services/api_gateway/routers/organizations.py`
`organizations.py:90` (list) and `:118` (one tenant), mounted at `main.py:241`.
**Access mismatch — resolve before shipping.** Both reads are `require_user`
(`organizations.py:92`, `:121`), not an admin gate, and `/workspace/overview` and
`/workspace/team` are already bound to the same endpoint. Either raise the dependency or
do not publish it under `/admin/**`. See §5.
> `admin-admin-tenants` — **Tenants** / *مستاجرها* —
> "The organizations the gateway has registered, with the members each one records." /
> *«سازمان‌هایی که دروازه ثبت کرده است، با اعضایی که هرکدام نگه می‌دارد.»*

**29. Design token management — wrong context, and already right.** No new entry. The page
exists at `/admin/design-tokens` and reads `apps/web/tokens/dtcg.json`,
`apps/web/tokens/variables.css` and `apps/web/src/app/globals.css` at request time through
`readDesignTokens` / `readCssVariables` from
`apps/web/src/components/admin/admin-local-data.ts:18-20`. Those are build-time artefacts
gated by `scripts/check-token-references.mjs` and `scripts/check-contrast.mjs`; a gateway
read would be a copy that can drift. The page is correct as it stands; its only defect is
the catalogue binding to `/api/v1/platform/health`, which should become `endpoint: null`
and `status: 'unavailable'`.

**30. Translation management** — `path: '/admin/localization/translations'` ·
`endpoint: '/api/v1/admin/content/{item_id}/translations'` · `method: 'GET'` ·
`status: 'partially backed'` · `shape: rows`, no `rowsKey`
(`generate-resource-pages.mjs:637`) · `sourceOfTruth: services/api_gateway/routers/admin_content.py`
**Route exists; the binding is wrong today.** The entry declares
`/api/v1/legal-texts/locales` — a *legal text* locale list, not the app's UI strings. The
genuine content-translation read is `admin_content.py` (mounted at `main.py:229`,
`require_content_admin` at `:94`), whose per-item MT action is
`POST /api/v1/admin/content/{item_id}/translate` and whose draft action is
`POST /api/v1/admin/content/generate-draft` — both forms. The per-locale **UI** coverage
that the page already renders from `apps/web/messages/*.json`
(`translations/page.tsx:10-14`) has no gateway contract by design; it is build-time and
stays build-time.
> `admin-admin-localization-translations` — **Translations** / *مدیریت ترجمه* —
> "Per-locale coverage read from the message catalogues, and the content translations the gateway holds." /
> *«پوشش هر زبان از کاتالوگ‌های پیام، و ترجمه‌های محتوایی که دروازه نگه داشته است.»*

**31. Missing-translation monitor — wrong context; drop.** Already delivered by #30's page
through `readLocaleCoverage` (`admin-local-data.ts:21`,
`MESSAGES_GLOB_PATH = apps/web/messages/*.json`). The CI enforcement is
`scripts/check-locale-depth.mjs` and `scripts/check-message-usage.mjs`. A second route
would render the same rows twice.

**32. Pseudo-localisation tool — wrong context; drop.** A developer tool with no contract
and no product user. Routing it would put a dev affordance on the public internet; the
honest home is `scripts/`.

**33. Multilingual media management** — `path: '/admin/media'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` ·
`sourceOfTruth: services/api_gateway/routers/marketplace.py`
The only media operation is `POST /api/v1/marketplace/products/{product_id}/images`
(`marketplace.py:223`, `require_user`) — an upload, not a library. There is no read of a
media set, localised or otherwise.
> `admin-admin-media` — **Media** / *رسانهٔ چندزبانه* —
> "The gateway can receive an image but publishes no media library to read." /
> *«دروازه می‌تواند تصویر بگیرد اما کتابخانهٔ رسانه‌ای برای خواندن منتشر نمی‌کند.»*

**34. Responsible-AI dashboard** — `path: '/admin/responsible-ai'` · `endpoint:
'/api/v1/ai/health'` · `method: 'GET'` · `status: 'partially backed'` · `shape: record` ·
`sourceOfTruth: services/api_gateway/routers/security_router.py`
Four reads back the panels: `GET /api/v1/ai/health` (record, already declared at
`generate-resource-pages.mjs:482`), `GET /api/v1/ai/analysis/providers` (record, `:473`),
`GET /api/v1/security/status` (`security_router.py:125`, record — the live middleware
stack, which is exactly what a posture page should show), and
`GET /api/v1/security/events` (`:257`, rows, `rowsKey: 'events'`).
**The last two are absent from the committed `openapi.json`** and are therefore invisible
to `check-api-contract.mjs` until §4 item 1 runs. `GET /api/v1/audit/queue` (rows,
`rowsKey: 'queue'`) is a fourth panel and is in the same position.
> `admin-admin-responsible-ai` — **Responsible AI** / *داشبورد هوش مصنوعی مسئول* —
> "The AI, security and audit posture the gateway actually reports, panel by panel." /
> *«وضعیت هوش مصنوعی، امنیت و حسابرسی که دروازه واقعاً گزارش می‌کند، پنل‌به‌پنل.»*

---

### Research

**35. Dataset DOI and citation** — `path: '/research/science/datasets'` ·
`endpoint: '/api/v1/science/datasets'` · `method: 'GET'` · `status: 'live'` already ·
`shape: rows`, `rowsKey: 'datasets'` · `sourceOfTruth: services/api_gateway/routers/science.py`
**Route exists and the read is backed.** `science.py:29` returns
`{"count": …, "live": …, "datasets": [...], "note": …}`; the citation index is
`GET /api/v1/science/citations/index` (`:21`, rows `items`). The DOI half —
`POST /api/v1/science/datasets/{slug}/doi` (`:81`) — is a mutation and is already
catalogued correctly as a `POST` entry at `/research/science/datasets/{slug}/doi`. It
never produces a page, which is correct: minting a DOI is a form on the dataset page.
> `research-research-science-datasets` — **Research datasets** / *مجموعه‌داده‌های پژوهشی* —
> "Datasets the research hub has registered, with their access state." /
> *«مجموعه‌داده‌هایی که مرکز پژوهش ثبت کرده است، با وضعیت دسترسی‌شان.»* (unchanged)

**36. Internal preprint server** — `path: '/research/preprints'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` · `sourceOfTruth: services/api_gateway/routers/science.py`
`GET /api/v1/science/zenodo/status` (`:73`) reports the status of the **external** Zenodo
deposit client. Reusing it for an internal server would report the wrong thing.
> `research-research-preprints` — **Preprints** / *پیش‌چاپ‌ها* —
> "No internal preprint server is published; the gateway only reports its Zenodo client status." /
> *«هیچ سرور پیش‌چاپ داخلی منتشر نشده است؛ دروازه تنها وضعیت کلاینت Zenodo خود را گزارش می‌کند.»*

**37. Reproducible pipeline** — `path: '/research/pipelines'` · `endpoint:
'/api/v1/hub/runs'` · `method: 'GET'` · `status: 'partially backed'` · `shape: rows`,
`rowsKey: 'runs'` · `sourceOfTruth: services/api_gateway/routers/hydroma_hub.py`
`hydroma_hub.py:82` lists runs; `GET /api/v1/hub/shared` (`:129`) lists shared ones;
`GET /api/v1/simulation/runs` lists engine runs. The *contract* side — the plan's
"versioned contract before finance" rule — is written and unmounted at
`services/contracts/router.py:69` (`GET /api/v1/contracts`), `:105` (`/compatibility`),
`:119` (`/diff`). A pipeline page without the contract compatibility read would show runs
with no notion of what they were valid against.
> `research-research-pipelines` — **Pipelines** / *خط لولهٔ بازتولیدشونده* —
> "The runs the gateway holds, with the service-contract version each was executed against." /
> *«اجراهایی که دروازه نگه داشته است، با نسخهٔ قرارداد سرویسی که هرکدام با آن اجرا شده.»*

**38. Federated learning between pilots** — `path: '/research/federated'` ·
`endpoint: null` · `status: 'unavailable'` · `shape: rows` ·
`sourceOfTruth: services/api_gateway/routers/ecosystem.py`
Nothing. Recommended for the backlog, not the catalogue. See §5.

**39. Local ethics registration** — `path: '/research/ethics'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` ·
`sourceOfTruth: services/api_gateway/routers/science.py`
No registry exists to register into. See §5.

**40. Study-pattern library** — `path: '/research/patterns'` · `endpoint: null` ·
`status: 'unavailable'` · `shape: rows` · `sourceOfTruth: services/api_gateway/routers/science.py`
The nearest reads are `GET /api/v1/science/model-cards` (rows `cards`) and the six
`/research/experiments/*` entries that already declare `endpoint: null` and resolve to
`unavailable`. A study-pattern library with no study registry behind it is the 8:1
page-to-contract ratio §5.2 warns about.
> `research-research-patterns` — **Study patterns** / *کتابخانهٔ الگوهای مطالعه* —
> "No study registry is published, so no pattern can be listed." /
> *«هیچ رجیستری مطالعه‌ای منتشر نشده است؛ پس الگویی فهرست نمی‌شود.»*

---

### Regional — six declared content pages

None of the six has, or should have, a gateway contract. `GET /api/v1/pilot/stats`
(`services/api_gateway/routers/pilot.py:73`) returns Iranian application aggregates —
`applications`, `provinces`, `total_hectares` — and states its own limit in the payload:
`"outcomes_status": "awaiting_verified_data"` (`:92`). **Reusing it as a per-pilot
outcome number would be exactly the fabrication this project forbids.** These six are
content, and the repository already has the correct mechanism:
`docs/frontend/contract-allowlist.json` `declaredContent`, which makes a path
`status: 'static'` and indexable under `page-catalog.ts:283-288`.

All six: `endpoint: null` · `method: 'GET'` · `status: 'static'` · `shape: record` ·
`sourceOfTruth: docs/frontend/contract-allowlist.json` · `access: 'public'` ·
`indexable: true`.

| # | `path` | slug | title (en) | title (fa) |
|---|---|---|---|---|
| 41 | `/public/regions/iran` | `public-public-regions-iran` | Pilot — Iran | پیلوت — ایران |
| 42 | `/public/regions/pakistan` | `public-public-regions-pakistan` | Pilot — Pakistan | پیلوت — پاکستان |
| 43 | `/public/regions/afghanistan` | `public-public-regions-afghanistan` | Pilot — Afghanistan | پیلوت — افغانستان |
| 44 | `/public/regions/turkiye` | `public-public-regions-turkiye` | Pilot — Türkiye | پیلوت — ترکیه |
| 45 | `/public/regions/middle-east` | `public-public-regions-middle-east` | Pilot — Middle East | پیلوت — خاورمیانه |
| 46 | `/public/regions/global` | `public-public-regions-global` | Pilot — global | پیلوت — جهانی |

Descriptions follow the pattern of the existing declared content pages
(`/public/policy/*`, `/public/components/*`) and state the content's own status:

- 41–45: "What the pilot covers, in the pilot's own words. No outcome figure is shown
  until the gateway publishes a verified one." / *«آنچه پیلوت پوشش می‌دهد، به زبان خود پیلوت. تا وقتی دروازه عدد تأییدشده منتشر نکند، هیچ رقمی از نتیجه نشان داده نمی‌شود.»*
- 46: "The countries the platform is being prepared for. Preparation is not participation." /
  *«کشورهایی که سکو برایشان آماده می‌شود. آماده‌سازی مشارکت نیست.»*

**Static siblings, not a dynamic one.** See §3 item 3.

---

## 8. Undecided

Three questions this pass could not settle from the code. Each names what would settle
it, rather than guessing.

1. **Is `/market/escrow/orders/{order_id}` (#5) the right shape, or should escrow by order
   reuse the existing `/market/escrow/{id}` page with a payment resolver?** Both are
   defensible. The deciding fact is whether an order carries a payment id in
   `services/commerce/routers/commerce.py` — read `OrderCreateRequest` and the order
   response at `commerce.py:145`. If it does, the existing page is enough and #5 is a
   detail view, not a new route. This pass did not open the model.
2. **Should the ten admin rows be `admin` or `workspace`?** The catalogue's `admin` group is
   `role-gated` with a command rail; `workspace` is also `role-gated` but scoped to a
   tenant. #28 multi-tenant management is the only row where this changes the answer, and
   it turns on whether a tenant administrator is a platform administrator. That is a
   product decision, not a code fact.
3. **Does #35's DOI half belong on the dataset page or on its own route?** The catalogue
   already treats `/research/science/datasets/{slug}/doi` as a `POST` entry, which is
   right for the generator but leaves a researcher with no URL to cite. Settled by whether
   the DOI is minted per dataset (page) or per version (a `/research/datasets/{slug}/versions/{v}`
   route that does not exist). The model at `science.py:81` takes only `slug`, which
   suggests per-dataset, but that is an inference from one signature.

---

## 9. Verification notes

- **The app was imported.** `from services.api_gateway.main import app` succeeded; routes
  come from `app.openapi()`, not `app.routes`, which returns 75 empty
  `_IncludedRouter` placeholders on FastAPI 0.141. No server was started, so nothing here
  reflects runtime state, and no finding is weaker for it.
- **`openapi.json` is stale by 8 paths** (all `audit` and `security`), never wrong. Any
  conclusion drawn from the file alone about those 8 would have been wrong; all eight are
  listed in §0 and §4 item 1.
- **Every `sourceOfTruth` in §7 was checked to exist on disk.**
  `page-catalog.test.ts:236-238` fails the suite otherwise, and three paths that looked
  plausible — `services/compliance/routers/compliance.py`,
  `services/api_gateway/routers/hub_shared.py` and
  `services/api_gateway/routers/hydroma_models.py` — do not exist. All three were dropped
  rather than written down; the real file for `/api/v1/hydroma/models/{model_id}/validation`
  turned out to be `hydroma_dashboard.py:752`, found by grepping for the route rather than
  for the name.
- **No contract is asserted because a directory of the same name exists.** `services/insurance/`
  does not exist and the contract does; `services/api_gateway/eventbus.py` does not exist
  and the package `services/api_gateway/eventbus/` does. Both were resolved by the mounted
  route table, not by the name.
- **The dry run of `node scripts/generate-resource-pages.mjs` was read, not written.** It
  reports 600 entries, 256 with a contract and no page, 132 page-shaped, 118 actions, and
  **0 dynamic-swallow conflicts** — consistent with §3.
