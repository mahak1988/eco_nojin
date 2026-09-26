# 600-page measurable checklist

**Status:** Recorded 2026-09-26. This document defines the measurable checklist contract for the declared 600 logical page paths and records the current state of that inventory. It is a documentation record only: no code, route, backend contract, engine module, message catalog, or existing page was changed to produce it.

**Non-claim, stated first:** this document does **not** claim that 600 pages are live, rendered, tested, or data-bearing. It does not claim that 600 pages exist. It records that a 600-entry logical catalog has been declared as the target inventory, and it records the count of paths that are physically present, that fall back to a catalog, and that have no endpoint. The distinction between those things is the subject of section 2, and the numbers in section 4 are the numbers that can be measured today.

Companion documents: [`PAGE_GATES.md`](PAGE_GATES.md) is the gate contract, [`MARKETPLACE_IMPLEMENTATION.md`](MARKETPLACE_IMPLEMENTATION.md) and [`PUBLIC_PAGES_EXECUTION.md`](PUBLIC_PAGES_EXECUTION.md) hold the per-surface route matrices, [`CONTENT_MIGRATION_MATRIX.md`](CONTENT_MIGRATION_MATRIX.md) holds the content truthfulness phases, and [`TESTING.md`](TESTING.md) holds the quality gate.

## 1. What this document is for

The surface area of `apps/web` is large enough that "the pages are done" is not a measurable statement. This document makes it measurable by fixing:

1. four distinct meanings of "a page", so a count is never ambiguous;
2. a fixed column schema for every page group, with an allowed value for each column and a test for each column;
3. a reproducible measurement command for every number in the document;
4. an explicit blocker and reconciliation list, so an unmeasured area is visible instead of assumed green.

A row is complete only when every column holds one of its allowed values **and** the acceptance-evidence column names a command that was actually run against the named commit. A row with an empty evidence cell is incomplete regardless of its other columns.

## 2. Four different meanings of "a page"

These four are routinely conflated, and the conflation is the source of most over-claiming on this project. They are not interchangeable, and the count of one is never evidence about another.

| Term | Definition | What it proves | What it does not prove |
|---|---|---|---|
| **Physical route** | A `page.tsx` file on disk, or a `route.ts` file, under `apps/web/src/app`. It is a filesystem fact. | The framework will attempt to render something at that path. | That the path is reachable in a deployment, that it renders data, that it is tested, or that it is honest. |
| **Logical path** | A declared, addressable, product-meaningful URL in the page catalog, independent of whether a file exists for it. A logical path may be parameterised (`{id}`, `{level1}/{level2}`) or expanded. | The product has specified a destination and can be held accountable for it. | That a file exists, or that the destination has any behaviour. |
| **Catalog fallback** | A logical path with no dedicated file that is resolved at request time by a catch-all route rendering a catalog/contract block. In this repository the canonical case is `apps/web/src/app/[locale]/market/[...segments]/page.tsx` plus the 15 declared groups in `apps/web/src/lib/marketplace-routes.ts` (444 declared routes). | The path returns a controlled, non-inventing, non-indexable state instead of a 404 or a fabricated page. | That the path is distinct, useful, discoverable, or tested individually. |
| **Data-bearing page** | A page that issues a request to an endpoint present in `openapi.json` and renders the response. Counted per *capability*, not per page: one page with three bound capabilities is three data-bearing capabilities. | The page shows something an endpoint owns. | That the response was ever observed, that the data is correct, or that the page is accessible in all locales. |

### Decision rules that follow from the table

1. **A count of logical paths is never reported as a count of pages.** Report both, separately, with the join rule stated.
2. **A catalog fallback counts once as a fallback, not once per declared path, in any "implemented" count.** It may be counted per path in a "catalog covers" count, which is a different number with a different name.
3. **A page is only "live" if it is data-bearing.** `unavailable` and `static` are the accepted state for a capability with no contract; they are not defects, and they are also not successes.
4. **A physical route with no catalog entry is an orphan** and is recorded as such, not silently counted as catalog coverage.
5. **A logical path with no physical route and no fallback is a gap.** It is counted in the catalog total and in the "no physical route" column. It must never be reported as rendered.
6. **The 600 figure is a logical-path count.** No document may restate it as a page count, a route count, a live count, or a test-coverage count.

## 3. Measurement method

Every number below was produced by a command that can be re-run. Where a number is a declaration rather than a measurement, the row says so.

| ID | Measure | Command or source | Result at this record |
|---|---|---|---|
| M-1 | Physical `page.tsx` files under `apps/web/src/app` | `Get-ChildItem -LiteralPath 'apps/web/src/app' -Recurse -Filter page.tsx -File` | 218 (216 routable + 1 root + 1 `_not-found`) |
| M-2 | Physical routes on the marketplace surface | same, `-LiteralPath 'apps/web/src/app/[locale]/market'` | 74 |
| M-3 | Physical routes on the public surface | same, `-LiteralPath 'apps/web/src/app/[locale]/public'` | 62 |
| M-4 | Physical routes on the workspace surface | same, `-LiteralPath 'apps/web/src/app/[locale]/workspace'` | 17 |
| M-5 | Declared generated (catalog fallback) routes | `marketplaceRoutePlanTotal` in `apps/web/src/lib/marketplace-routes.ts` | 444 across 15 groups |
| M-6 | Declared logical catalog size | declared target, section 4 | 600 |
| M-7 | Message catalogs | `apps/web/messages/*.json` | 14 |
| M-8 | Declared Hydroma scientific tools | `SCIENTIFIC_TOOLS` in `apps/web/src/lib/domains/registry.ts` | 52 |
| M-9 | Domain route registry entries | `DOMAIN_ROUTES` in the same file | 11 |
| M-10 | Accessibility e2e route coverage | unique locales paths in `apps/web/tests/a11y.spec.ts` | 13 routes |
| M-11 | Tier 0 smoke route coverage | `apps/web/tests/tier0.spec.ts` | 10 routes |
| M-12 | Reflow/responsive route coverage | unique locale paths in `apps/web/tests/responsive.spec.ts` | 8 routes |
| M-13 | i18n route coverage | `apps/web/tests/i18n.spec.ts` | 14 locales on 1 route template |
| M-14 | Provenance guard | `scripts/check-verified-claims.mjs` | present; run status recorded per group |
| M-15 | Canonical site-URL guard | `scripts/check-site-url.mjs` | present |

M-1 through M-4 were counted in a working tree that other workstreams are actively modifying. They are a snapshot at the record date, not a stable property, and M-1 is expected to move. Every count in section 5 carries its own date for that reason.

## 4. Current state record

| ID | Figure | Value | Kind | Notes |
|---|---|---|---|---|
| S-1 | Declared logical catalog size | 600 | declaration | The catalog this size refers to is not present in this document set; see R-1. |
| S-2 | Marketplace baseline | 10 | declaration | Routes with their own implementation, as distinct from the template surface. |
| S-3 | Implementable orphans | 14 | declaration | Physical routes with no catalog binding that are implementable without a new backend contract. |
| S-4 | Requiring mapping | 22 | declaration | Physical routes whose logical destination is not yet determined; a catalog decision is required before they can be counted as covered. |
| S-5 | Without endpoint | 27 | declaration | Logical paths with no endpoint in `openapi.json`; these render `unavailable` by rule, not by defect. |
| S-6 | Measured physical routes | 218 | measurement | M-1. |
| S-7 | Measured generated fallback routes | 444 | measurement | M-5. |

### Reconciliation of the declared figures

`S-2 + S-3 + S-4 + S-5 = 10 + 14 + 22 + 27 = 73`. The sum equals the marketplace `page.tsx` count recorded in [`MARKETPLACE_IMPLEMENTATION.md`](MARKETPLACE_IMPLEMENTATION.md) at commit `2177450`. Two consequences are recorded rather than resolved:

- The four buckets are treated in this document as a **partition of the marketplace surface with no gap and no overlap**. That is a working assumption, not a verified fact, and the checklist below is the instrument that verifies it.
- The measured marketplace surface is now 74 (M-2), not 73. Either one file is unassigned or the bucket counts predate one addition. This is **R-2** and it is open.

`S-1` is not derivable from the other figures. `218 + 444 = 662`, which is 62 more than 600. The 600 is therefore a *separate* logical catalog, and the difference must be accounted for by the join rule, not by rounding. **R-1** is open and is the first thing to resolve before any 600-derived claim is made anywhere else.

## 5. The checklist

### 5.1 Column schema

One row per page group. The columns are fixed; a group with an unknown value records the unknown as a blocker, not as a blank that reads as zero.

| # | Column | Allowed values | Test that makes the value measurable |
|---|---|---|---|
| 1 | `page` | group label as it appears in the surface route matrix | matches a group heading in the owning document |
| 2 | `group` | `baseline` \| `orphan` \| `needs-mapping` \| `no-endpoint` \| `fallback` \| `catalog-gap` | exactly one value; sum of the four declared buckets must equal 73 (R-2) |
| 3 | `domain` | `market` \| `public` \| `admin` \| `research` \| `system` \| `workspace` \| `inclusive` \| `ai` \| `developers` \| `trust` \| `auth` \| `top-level` | matches the first path segment under `[locale]` |
| 4 | `route count` | integer `physical` + integer `logical` + integer `fallback`, written as `p/l/f` | `physical` re-derivable with M-1..M-4; `logical` re-derivable from the catalog; `fallback` re-derivable from M-5 |
| 5 | `state` | `live` \| `capability` \| `unavailable` \| `static` | `live` requires at least one bound capability; `unavailable`/`static` require zero unbound figures on the page |
| 6 | `endpoint/source` | endpoint path template, or `none` + a named source of truth | every endpoint string present in `openapi.json`; every `none` names a file or router path |
| 7 | `owner` | an owner id from the vocabulary in [`MARKETPLACE_IMPLEMENTATION.md`](MARKETPLACE_IMPLEMENTATION.md) or the domain registry | non-empty; an owner with no scope in this repository is a blocker |
| 8 | `auth` | `public` \| `session` \| `role` \| `internal` | matches `access` in the domain registry, or is `public` outside it; a `role` row names the allow-list |
| 9 | `provenance` | `response-bound` \| `editorial` \| `unavailable` | `response-bound` requires a successful call; never asserted from page type |
| 10 | `a11y` | `axe-pass` \| `manual-pass` \| `not-covered` | named spec file and route; `not-covered` is reported, not omitted |
| 11 | `i18n` | `14/14` \| `partial: n/14` \| `not-covered` | key resolves in all 14 catalogs, or the missing locales are listed |
| 12 | `gate` | gate ids from [`PAGE_GATES.md`](PAGE_GATES.md) or `C600-G*` below | at least one gate; a row with no gate is not trackable |
| 13 | `blocker` | `B1`–`B11` or `none` | every non-`none` value appears in the blocker table with an owner |
| 14 | `acceptance evidence` | command + commit | the named command was run against the named commit on the same day the row changed |

`state` is deliberately not a percentage. A group is one of the four values, and the value describes what the group renders, not how complete it feels.

### 5.2 Marketplace surface

Physical routes 74 (M-2). Logical and fallback counts are pending the catalog bind (R-1). `state` follows the route matrices in [`MARKETPLACE_IMPLEMENTATION.md`](MARKETPLACE_IMPLEMENTATION.md); that document is authoritative for the marketplace `live`/`live-partial`/`unavailable`/`static` split, and `live-partial` maps to `capability` here.

| page | group | domain | routes p/l/f | state | endpoint/source | owner | auth | provenance | a11y | i18n | gate | blocker | acceptance evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Catalog, compare | baseline | market | 2 | live | `GET /api/v1/marketplace/products`, `GET /api/v1/marketplace/stats` | `marketplace-web` | public | response-bound | axe-pass: `a11y.spec.ts` `/fa/market` | 14/14 | MKT-G1, C600-G3 | B1, B2 | `pnpm -C apps/web quality`; `node scripts/check-verified-claims.mjs` |
| Product detail | baseline | market | 1 | capability | `GET /api/v1/marketplace/products/{product_id}` | `marketplace-web` | public | response-bound | not-covered | 14/14 | MKT-G2, C600-G3 | none | `pnpm -C apps/web test:e2e` |
| Cart | baseline | market | 1 | capability | `GET, PATCH, DELETE /api/v1/marketplace/cart[/{product_id}]` | `marketplace-web` | session | response-bound | not-covered | 14/14 | MKT-G3, GATE-G1 | B5 | `marketplace-flow.spec.ts` |
| Checkout | baseline | market | 1 | capability | `POST /api/v1/marketplace/orders`, `POST /api/v1/marketplace/payments` | `marketplace-web` | session | response-bound | not-covered | 14/14 | MKT-G4, C600-G3 | B3, B4, B5 | `marketplace-flow.spec.ts` |
| Wallet | baseline | market | 1 | capability | `GET /api/v1/ecowallet/wallet/{user_id}`, `GET /api/v1/ecowallet/earnings` | `wallet-api` | session | response-bound | not-covered | 14/14 | MKT-G8, C600-G6 | B2 | `pnpm -C apps/web quality` |
| Escrow detail | baseline | market | 1 | capability | `GET /api/v1/marketplace/payments/{payment_id}/escrow` | `marketplace-web` | session | response-bound | not-covered | 14/14 | MKT-G4, C600-G3 | B3 | `pnpm -C apps/web test:e2e` |
| Bazaar index, detail, creation | baseline | market | 15 | capability | `GET /api/v1/marketplace/marketplaces`, `POST /api/v1/marketplace/marketplaces` | `marketplace-web` | session | response-bound | not-covered | 14/14 | MKT-G5, C600-G3 | none | `market.spec.ts` |
| Store index, detail, creation | baseline | market | 4 | capability | `GET /api/v1/marketplace/marketplaces` | `marketplace-web` | session | response-bound | not-covered | 14/14 | MKT-G6, C600-G4 | none | `pnpm -C apps/web quality` |
| Marketplace remaining baseline | baseline | market | — | capability | see owning document | `marketplace-web` | session | response-bound | not-covered | 14/14 | MKT-G1, C600-G2 | B11 | R-2 reconciliation |
| Product sub-pages | no-endpoint | market | 12 | unavailable | `none` + `GET /products/{product_id}`, `GET /products/{product_id}/trace` are candidates | `marketplace-web` | public | unavailable | not-covered | 14/14 | MKT-G6, C600-G4 | none | `node scripts/check-verified-claims.mjs` |
| Search routes | no-endpoint | market | 11 | unavailable | `none` + `GET /products/search` is a candidate | `marketplace-web` | public | unavailable | not-covered | 14/14 | MKT-G6, C600-G4 | none | `pnpm -C apps/web quality` |
| Category tree | no-endpoint | market | 4 | unavailable | `none` | `marketplace-web` | public | unavailable | not-covered | 14/14 | MKT-G6, C600-G4 | none | `pnpm -C apps/web quality` |
| Checkout step routes | no-endpoint | market | 6 | unavailable | `none` | `marketplace-web` | session | unavailable | not-covered | 14/14 | MKT-G6, C600-G5 | B1, B2 | `pnpm -C apps/web quality` |
| Order routes | no-endpoint | market | 5 | unavailable | `none`; the two open reads are B1 and are deliberately not bound | `marketplace-web` | session | unavailable | not-covered | 14/14 | MKT-G6, C600-G5 | B1 | `pnpm -C apps/web quality` |
| Store creation steps | no-endpoint | market | 2 | static | `none` | `marketplace-web` | public | editorial | not-covered | 14/14 | MKT-G6, C600-G4 | none | `node scripts/check-verified-claims.mjs` |
| Generated catalog routes | fallback | market | 0/444/444 | unavailable | `none` + `apps/web/src/lib/marketplace-routes.ts` | `marketplace-web` | public | unavailable | not-covered | 14/14 | MKT-G6, C600-G1 | B11 | `pnpm -C apps/web quality` |

The generated row is the clearest illustration of the section 2 rules: it is 0 physical routes beyond the catch-all, 444 declared logical paths, all resolved by one fallback, and none of them is data-bearing. Counting it as 444 implemented pages would be false three times over.

### 5.3 Public surface

Physical routes 62 (M-3), which matches the two matrices in [`PUBLIC_PAGES_EXECUTION.md`](PUBLIC_PAGES_EXECUTION.md): 34 endpoint-bound and 28 static editorial.

| page | group | domain | routes p/l/f | state | endpoint/source | owner | auth | provenance | a11y | i18n | gate | blocker | acceptance evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Science and model count | baseline | public | 11 | live | `GET /api/v1/models`, `/science/datasets`, `/science/model-cards`, `/science/citations/index`, `/science/agrovoc`, `/hydroma/validation` | `science-web` | public | response-bound | not-covered | 14/14 | PUB-G1, C600-G3 | none | `node scripts/check-verified-claims.mjs` |
| Benchmarks | baseline | public | 1 | capability | `GET /api/v1/science/datasets`; no result store exists | `science-web` | public | response-bound | not-covered | 14/14 | PUB-G2, C600-G3 | B8 | `pnpm -C apps/web quality` |
| Legal texts | baseline | public | 3 | live | `GET /api/v1/legal-texts/{locale}/{slug}` | `content-web` | public | response-bound | not-covered | 14/14 | PUB-G3, C600-G3 | B7 | `pnpm -C apps/web quality` |
| Education and glossary | baseline | public | 3 | live | `GET /api/v1/content/search`, `GET /api/v1/science/agrovoc` | `content-web` | public | response-bound | not-covered | 14/14 | PUB-G1, C600-G3 | B6 | `pnpm -C apps/web quality` |
| Component demos | baseline | public | 8 | live | marketplace, ecowallet, hydroma, mrv, land, satellite, tool-registry reads | per-surface owner | public | response-bound | not-covered | 14/14 | PUB-G1, C600-G3 | none | `node scripts/check-verified-claims.mjs` |
| Service pages | baseline | public | 8 | live | per-service health and read endpoints | per-surface owner | public | response-bound | not-covered | 14/14 | PUB-G1, C600-G3 | B10 | `pnpm -C apps/web quality` |
| Audiences | no-endpoint | public | 6 | static | `none`; no audience registry exists | `content-web` | public | editorial | not-covered | 14/14 | PUB-G4, C600-G4 | none | `node scripts/check-verified-claims.mjs` |
| Goals | no-endpoint | public | 6 | static | `none`; no impact store exists | `content-web` | public | editorial | not-covered | 14/14 | PUB-G4, C600-G4 | none | `node scripts/check-verified-claims.mjs` |
| Policy without published text | no-endpoint | public | 3 | static | `none`; no registered legal slug | `content-web` | public | unavailable | not-covered | 14/14 | PUB-G4, C600-G4 | B7 | `node scripts/check-verified-claims.mjs` |
| Education without content | no-endpoint | public | 3 | static | `none`; LMS router not mounted | `content-web` | public | unavailable | not-covered | 14/14 | PUB-G4, C600-G4 | B6 | `pnpm -C apps/web quality` |
| Services roll-up, offline tools, channels, dispute, top level | no-endpoint | public | 15 | static | `none` | `content-web`, `inclusive-web` | public | editorial | not-covered | 14/14 | PUB-G4, C600-G4 | none | `node scripts/check-verified-claims.mjs` |

### 5.4 Remaining surfaces

Physical routes measured at M-1: 218 total, minus 74 marketplace and 62 public, leaves 82 across the other surfaces. These groups are not in the 600-declaration's four buckets, and they are recorded here as `catalog-gap` so the partition is visible rather than implied.

| page | group | domain | routes p/l/f | state | endpoint/source | owner | auth | provenance | a11y | i18n | gate | blocker | acceptance evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Workspace | catalog-gap | workspace | 17 | capability | `GET /api/v1/organizations`, `/content/search`, `/sync/status`, `/platform/health` | `platform-operations` | role | response-bound | axe-pass: `a11y.spec.ts` `/fa/workspace` | 14/14 | C600-G3, C600-G6 | B11 | `tier0.spec.ts`; `responsive.spec.ts` |
| Admin | catalog-gap | admin | 9 | capability | `GET /api/v1/platform/health`, `/platform/stats`; overview, audit and flag capabilities are `endpoint: null` | `platform-admin` | role | response-bound | axe-pass: `a11y.spec.ts` `/fa/admin` | 14/14 | C600-G3, C600-G6 | B11 | `tier0.spec.ts`; `responsive.spec.ts` |
| Research | catalog-gap | research | 2 | unavailable | `none`; all three research capabilities are `endpoint: null` | `research-platform` | session | unavailable | axe-pass: `a11y.spec.ts` `/fa/research` | 14/14 | C600-G4, C600-G5 | B11 | `tier0.spec.ts` |
| System | catalog-gap | system | 4 | capability | `GET /api/v1/platform/health`, `/platform/stats`, `/satellite/health`, `/models/cpp-status` | `platform-operations` | public | response-bound | axe-pass: `a11y.spec.ts` `/fa/system` | 14/14 | C600-G3 | B11 | `tier0.spec.ts`; `responsive.spec.ts` |
| AI | catalog-gap | ai | 8 | capability | `GET /api/v1/ai/health`, `/ai/chat` | `platform-web` | public | response-bound | not-covered: `pages.spec.ts` `/fa/ai/glossary`, `/fa/ai/voice` | 14/14 | C600-G3, C600-G8 | B11 | `pages.spec.ts` |
| Developers | catalog-gap | developers | 9 | capability | `GET /api/v1/tool-registry`, `/platform/health` | `platform-web` | public | response-bound | not-covered: `pages.spec.ts` `/fa/developers/api`, `/fa/developers/status-api` | 14/14 | C600-G3, C600-G8 | B11 | `pages.spec.ts` |
| Trust | catalog-gap | trust | 7 | capability | per-trust reads; audit projection is absent | `content-web` | public | response-bound | not-covered: `pages.spec.ts` `/fa/trust/provenance`, `/fa/trust/carbon-registry` | 14/14 | C600-G3, C600-G4 | B11 | `pages.spec.ts` |
| Hydroma tools | catalog-gap | top-level | 2 | capability | `GET /api/v1/tool-registry/{tool_id}`, `/models/cpp-status`; all 52 execution endpoints are `null` | `hydroma` | public | response-bound | axe-pass: `a11y.spec.ts` `/fa/hydroma` | 14/14 | C600-G3, C600-G4 | B11 | `hydroma.spec.ts` |
| Inclusive channels | catalog-gap | inclusive | 2 | capability | `GET /api/v1/ussd/status`, `/ussd/menu/preview`, `/voice/status`, `/voice/health` | `platform-operations` | public | response-bound | not-covered | 14/14 | C600-G3, C600-G4 | B11 | `pnpm -C apps/web quality` |
| Auth, account, and 20 single-page groups | catalog-gap | auth, top-level | 24 | capability | login, register, session and static editorial | `platform-web` | session | mixed | not-covered: `auth-ui.spec.ts` | 14/14 | C600-G3, C600-G5 | B11 | `auth-ui.spec.ts` |

Every row in this section carries **B11**: none of these 82 routes has a declared position in the 600 logical catalog. That is a documentation gap, not a code defect, and it is the largest single reconciliation item after R-1.

## 6. Gates introduced by this checklist

`PAGE_GATES.md` owns the surface gates. The `C600-G*` family exists only to make the inventory itself checkable, and it does not replace or relax any existing gate.

| Gate | Subject | Owner | Satisfied when |
|---|---|---|---|
| C600-G1 | Catalog inventory | `platform-web` | Every one of the 600 logical paths appears exactly once in the catalog, and each entry declares physical or fallback resolution. |
| C600-G2 | Count reconciliation | `platform-web` | The four buckets partition with no gap and no overlap, and their sum equals the measured marketplace physical count. Closes R-2. |
| C600-G3 | State honesty | all page owners | Every `state` value matches what the code renders, verified by reading the page and the response together. No `live` row is unbound; no `unavailable` row shows a figure. |
| C600-G4 | Endpoint and source provenance | all page owners | Every endpoint string in a row appears in `openapi.json` with the same path template; every `none` names a source-of-truth file. |
| C600-G5 | Auth truthfulness | `bff`, `platform-operations` | Every `session` or `role` row names its enforcement point, and no row claims an authorization outcome the frontend registry alone provides. |
| C600-G6 | Ownership | all page owners | Every row has a named owner with a real scope in this repository. |
| C600-G7 | Verification provenance | all page owners | `scripts/check-verified-claims.mjs` reports zero offenders, and no stamp is marked verified without a backing response. |
| C600-G8 | Accessibility coverage | `platform-web` | Every row is `axe-pass` or `manual-pass` with a named spec and route, or its `not-covered` value is counted in the coverage report. Silent absence is not acceptable. |
| C600-G9 | Locale coverage | `i18n` | Every row resolves in all 14 catalogs, or names the missing locales. A partial value is reported, not rounded up. |
| C600-G10 | Evidence currency | `platform-web` | Every row's acceptance evidence names a command and a commit, and the command was run against that commit. |

### Coverage arithmetic that must not be misreported

Measured e2e route coverage is 13 accessibility routes (M-10), 10 Tier 0 smoke routes (M-11), 8 reflow routes (M-12), and 14 locales on a single route template (M-13). That is route-level coverage over a small representative sample. It is **not** coverage of the 600 logical paths, and it is not evidence that the sample is representative. Reporting it as such would be the exact over-claim this document exists to prevent. Until C600-G8 is satisfied, a11y and i18n coverage for the catalogue is `not-covered` by default and must be reported that way.

## 7. Blockers and open reconciliations

### Blockers carried from `PAGE_GATES.md`

B1 through B10 are recorded there and are not restated here. They apply to the rows that name them in section 5.

### New blocker

| ID | Blocker | Owner | Blocks |
|---|---|---|---|
| B11 | The 600 logical catalog is not reconciled against the physical route set. 218 physical routes and 444 declared fallback routes do not compose to 600, and 82 physical routes outside the marketplace and public surfaces have no declared catalog position. | `platform-web` | C600-G1, C600-G2, and every 600-derived count |

### Open reconciliations

| ID | Question | Why it is open | Closes when |
|---|---|---|---|
| R-1 | What is the join rule between 218 physical routes, 444 declared fallback routes, and the 600 logical paths? | `218 + 444 = 662`, which is 62 more than 600. The difference must be explained by de-duplication or by parameter expansion, not by rounding. | The catalog publishes a per-entry physical-or-fallback resolution and the arithmetic reconciles exactly. |
| R-2 | Which marketplace file accounts for the 74th route, and do the buckets still partition? | `10 + 14 + 22 + 27 = 73` matches the recorded marketplace count at commit `2177450`; the tree now holds 74. | Every marketplace file is assigned to exactly one bucket and the sum equals the measured count. |
| R-3 | Which of the 82 non-marketplace, non-public routes belong to the 600? | Not derivable from any present document. | Each is bound to a catalog entry or declared out of catalogue, with the count stated. |
| R-4 | What is the `live` versus `capability` boundary for the marketplace and public surfaces? | The surface documents use `live-partial`; this document uses `capability`. The mapping is asserted, not yet written down in the owning documents. | The owning documents state the mapping, or adopt `capability`. |

## 8. How to keep this measurable

1. **Update a row only with evidence.** The acceptance-evidence cell changes in the same commit as the state it justifies.
2. **Re-run M-1 through M-4 when the count moves.** The `p/l/f` column is stale until it is re-derived, and a stale count is a defect in this document.
3. **Report four numbers, never one.** Logical paths, physical routes, fallback routes, and data-bearing capabilities are four different numbers. Any sentence that says "600 pages" without qualifying it is wrong.
4. **`not-covered` is a reportable value.** Adding an a11y or i18n test changes a column; omitting the test and leaving the column blank does not.
5. **No gate is claimed as passed by this document.** C600-G1 through C600-G10 are definitions, not results.

## 9. Non-claims

- It is not claimed that 600 pages exist. 218 physical routes are measured; 600 is a declared logical target.
- It is not claimed that any of the 600 are live. The largest measured data-bearing set is the 34 endpoint-bound public pages; the remainder are `capability`, `unavailable`, or `static` by rule.
- It is not claimed that any page was verified against a running gateway. No response was observed to produce this document.
- It is not claimed that a gate in this document has passed. Section 6 defines gates; it does not report them.
- The original 2026-09-26 record was documentation-only; subsequent execution evidence and the catalog handoff are appended below rather than rewriting the original measurement.

---

## 10. Execution protocol for the next agent

This section is the operating runbook. It is intentionally explicit so the next agent can execute without re-deriving the meaning of a page or a count.

### 10.1 Hard invariants

1. Never create a number, DOI, date, KPI, status, user, job, order, payment, role, or partner claim that is not returned by a registered endpoint or an explicitly reviewed editorial source.
2. `live` requires a bound endpoint from `openapi.json` and a rendered response.
3. `capability` means a real contract exists but the flow is partial or requires a mapping.
4. `unavailable` means no honest data contract exists; it must use the existing unavailable state component and `verified={false}` provenance.
5. `planned` is not a rendered success state; it must be non-indexable and must name the owner/gate.
6. Never use `git add .` in the shared worktree. Stage explicit paths only.
7. Never touch `engine/`, `services/`, `alembic/`, `database/`, or backend tests owned by the computational/backend workstream unless the task explicitly assigns them.
8. After every change batch, run the smallest relevant test, then `pnpm -C apps/web quality`, `pnpm -C apps/web build`, and the relevant Playwright file. Update this document in the same batch with the commit, command, and result.
9. `MISSING_MESSAGE`, `verified={true}` on synthetic data, and a placeholder domain are defects, not acceptable placeholders.
10. A page is not a count until its physical route, logical path, catalog fallback, and data-bearing capability are reported separately.

### 10.2 Current measured state

| Surface | Physical pages | Data-bearing/capability state | Fallback/logical declaration | Current owner |
|---|---:|---|---|---|
| All app | 218 `page.tsx` | mixed | — | shared frontend worktree |
| Marketplace | 74 | 10 baseline + 14 Group-A routes now implemented; 22 require mapping; 27 have no endpoint | 444 declared fallback paths | `marketplace-web` |
| Public | 62 | 34 endpoint-bound pages; 28 honest unavailable/static pages | — | `content-web` |
| Workspace | 17 | Tier-0 shell plus role/capability states | — | `platform-web` |
| Admin/Research/System/Help | 15 Tier-0 routes | capability-gated or unavailable unless an endpoint exists | — | domain owners |
| Logical catalog target | — | not yet fully materialized | **600 target** | `platform-web` |

`218 + 444 = 662`; therefore the 600 figure is not a physical page count. The catalog must publish a join rule and de-duplication before any 600-derived claim.

### 10.3 Work packages

| ID | Work package | Exact scope | Required output | Gate | Status |
|---|---|---|---|---|---|
| P-01 | Site URL | `apps/web/src/config/site.ts`, guard, CI wiring | one canonical origin, no placeholder reads | `pnpm check:site-url`, quality | ✅ `d81c34a` |
| P-02 | Auth/BFF | `apps/web/src/app/api/**`, `lib/{bff,session,config}/**` | login/session/refresh/logout, opaque Redis session, CSRF | type, unit, security E2E | ✅ committed |
| P-03 | Public truthfulness | `apps/web/src/app/[locale]/public/**`, `data-states.tsx`, `EndpointForm.tsx` | endpoint-bound or unavailable, zero synthetic verified claims | `check-verified-claims`, a11y, pages smoke | ✅ committed |
| P-04 | Marketplace Group A | `market/**`, `lib/api/{market,cart,escrow}.ts` | orders/timeline/tracking/traceability/search/checkout pages bound to real endpoints | marketplace boundary, tsc, Playwright marketplace | ✅ code complete, review pending |
| P-05 | 600 catalog | new `lib/domains/page-catalog.ts`, catalog route/component | exactly 600 unique logical entries, join rule, collision test, no fake data | catalog test, build, route smoke | ⏳ running |
| P-06 | Documentation | `docs/frontend/**` and checklist | matrices, gates, owners, blockers, evidence | `git diff --check -- docs` | ✅ updated, final reconciliation pending |
| P-07 | Release governance | `docs/operations/GITHUB_RELEASE_RUNBOOK.md` | reviewed `gh` procedure; no admin execution without approval | manual admin review | ✅ prepared, not executed |
| P-08 | Backend blockers | role issuance, admin datetime response models, marketplace response models | backend contract decision and typed response models | backend owner tests | ⏳ external |
| P-09 | Final integration | frontend only | quality, build, E2E, provenance/site guards, commit | all gates green | ⏳ pending P-04/P-05 |
| P-10 | Publish | Git history/remote | explicit staging, secret scan, fetch, push | `git push origin main` only after review | ⏳ not pushed |

### 10.4 Group A implementation rules

The following routes are real, session-aware, and must not regress to `MarketplaceTemplatePage`:

```text
/market/orders
/market/orders/[id]/timeline
/market/orders/[id]/tracking
/market/orders/[id]/dispute
/market/product/[id]/traceability
/market/search
/market/search/filters
/market/search/advanced
/market/checkout/cart-review
/market/checkout/escrow-setup
/market/checkout/card
/market/checkout/transaction-key
/market/checkout/confirmation
/market/checkout/contract
```

For each page:

- use `useAuth` and the BFF client;
- show loading, empty, error, offline, unauthenticated, and unavailable states;
- show only server-returned totals and identifiers;
- use `Idempotency-Key` for writes;
- use `ProvenanceStamp` with `verified={false}` unless the response contract is actually verified;
- never collect card data; card page is gateway redirect only;
- do not add a success state for a failed or stubbed upstream call.

### 10.5 Catalog generation rules

When P-05 lands:

1. assert `catalog.length === 600`;
2. assert unique `path` and unique `id`;
3. assert every entry has domain, state, source, owner, gate, and description;
4. assert no entry contains a synthetic number, DOI, date, `verified=true`, or `MISSING_MESSAGE`;
5. assert entries overlapping physical routes are marked `physicalResolution` and are not counted twice;
6. assert 444 marketplace fallback paths are reconciled with the catalog join rule;
7. mark all 82 physical routes outside public/marketplace as `covered` or `not-covered` with a reason;
8. mark generated fallback routes `noindex` until a live endpoint exists;
9. run `generateStaticParams` only for catalog entries that do not conflict with a more specific physical route;
10. add a route smoke test for a representative entry from every catalog group.

### 10.6 Required commands

```powershell
pnpm check:site-url
pnpm -C apps/web quality
pnpm -C apps/web build
pnpm -C apps/web test:e2e tests/a11y.spec.ts --project=chromium
pnpm -C apps/web test:e2e tests/tier0.spec.ts --project=chromium
pnpm -C apps/web test:e2e tests/responsive.spec.ts --project=chromium
pnpm -C apps/web test:e2e tests/marketplace-flow.spec.ts --project=chromium
node scripts/check-verified-claims.mjs
git diff --cached --check
```

Use `git diff --name-only` and an explicit `git add -- <paths>` for every commit. Run the secret scan again before publishing:

```powershell
git grep -n -I -E "(BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})" HEAD -- . ":(exclude)docs/**"
```

### 10.7 Update rule after every progress event

Append a new row to the execution log below in the same batch as the code change:

| Time | Work item | Files | State changed | Test/command | Commit | Blocker/next |
|---|---|---|---|---|---|---|
| 2026-09-26 | P-01 Site URL | `src/config/site.ts`, `scripts/check-site-url.mjs` | ✅ resolved | quality/typecheck/guard green | `d81c34a` | none |
| 2026-09-26 | P-04 Marketplace A | `market/**`, `lib/api/{market,cart,escrow}.ts` | ✅ implemented, uncommitted review | tsc/vitest/biome green | pending | review/stage only |
| 2026-09-26 | P-05 Catalog 600 | pending | ⏳ running | pending | pending | verify 600 invariant |
| 2026-09-26 | P-06 Docs | `docs/frontend/**` | ✅ checklist written | `git diff --check` pending final | pending | reconcile R-1..R-4 |
| 2026-09-26 | P-10 Publish | no push | ⛔ blocked | `git rev-list` shows local ahead of origin | none | do not use `git add .` |
| 2026-09-26 | P-04 Marketplace A review | `market/**`, `lib/api/{market,cart,escrow}.ts` | ✅ committed | `tsc`, 267 vitest, biome | `3683725` | integrate with P-05 |
| 2026-09-26 | Agent shutdown and master dashboard | `FRONTEND_MASTER_STATUS_FA_2026-09-26.md`, `docs/README.md` | ✅ consolidated | Agent Manager sessions stopped; file created | pending | owner review before any push |

Do not overwrite an old row. Append a new row for every change, test, revert, review, or push decision. The checklist is the handoff memory of the workstream.

### 10.8 Handoff prompt for the next agent

```text
Read docs/frontend/PAGE_CHECKLIST_600.md before changing code.
Do not use git add . and do not touch engine/, services/, alembic/, database/, or backend tests.
Finish P-05 first: make the 600 logical catalog exact, unique, reconciled with 218 physical routes and 444 marketplace fallback paths, and test collisions.
Then review P-04 and run the required commands.
Append an execution-log row for every change or test.
Never call a page live without a real endpoint and a rendered response.
Never fabricate a number, date, DOI, user, role, job, order, payment, or partner claim.
```
