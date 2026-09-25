# Public pages execution

**Status:** Recorded from the repository at commit `2177450` on 2026-09-25. Every status in this document is derived from the page source and from `openapi.json`. Nothing here asserts that a page was verified against a running gateway, and no environment, dataset, or credential is claimed to be available.

This document narrows [`CONTENT_MIGRATION_MATRIX.md`](CONTENT_MIGRATION_MATRIX.md) to what is actually in the tree. Where the two disagree, this document is the current record and the matrix is the plan it was derived from.

## Method and counts

`apps/web/src/app/[locale]/public/**` contains 62 `page.tsx` files.

| Class | Count | Test applied |
|---|---|---|
| Endpoint-bound | 34 | The page calls `apiGet` and the path is present in `openapi.json` |
| Static editorial | 28 | The page makes no request and asserts no live figure |

A page is `static` when it renders fixed copy with a `StatusDot` at `down` and the `market.template.unavailable*` block. That is the accepted state for a capability with no contract, and it satisfies the rule in [`CONTENT_MIGRATION_MATRIX.md`](CONTENT_MIGRATION_MATRIX.md) that no number, DOI, date, status, or partner claim appears without a live response.

`ProvenanceStamp` receives `verified={false}` on every static page and on several endpoint-bound pages, so the claim of verification is not made anywhere on this surface.

## Matrix A — endpoint-bound pages

All 34 paths below are prefixed with `/{locale}`. `openapi.json` is the authority on the second column; a path not listed there does not exist.

| Page | Path | Endpoint | Status | Owner | Gate |
|---|---|---|---|---|---|
| Model count | `public/model-count` | `GET /api/v1/models` | `live` | `science-web` | PUB-G1 |
| Methodology | `public/science/methodology` | `GET /api/v1/models` | `live` | `science-web` | PUB-G1 |
| Data sources | `public/science/data-sources` | `GET /api/v1/science/datasets` | `live` | `science-web` | PUB-G1 |
| Benchmarks | `public/science/benchmarks` | `GET /api/v1/science/datasets` | `live-partial` | `science-web` | PUB-G2 |
| Case studies | `public/science/case-studies` | `GET /api/v1/science/citations/index` | `live` | `science-web` | PUB-G1 |
| Peer review | `public/science/peer-review` | `GET /api/v1/science/citations/index` | `live` | `science-web` | PUB-G1 |
| Evidence base | `public/science/evidence-base` | `GET /api/v1/science/citations/index` | `live` | `science-web` | PUB-G1 |
| Uncertainty | `public/science/uncertainty` | `GET /api/v1/science/model-cards` | `live` | `science-web` | PUB-G1 |
| Limitations | `public/science/limitations` | `GET /api/v1/science/model-cards` | `live` | `science-web` | PUB-G1 |
| Gap analysis | `public/science/gap-analysis` | `GET /api/v1/science/model-cards` | `live` | `science-web` | PUB-G1 |
| Validation | `public/science/validation` | `GET /api/v1/hydroma/validation` | `live` | `science-web` | PUB-G1 |
| Validation methods | `public/science/validation-methods` | `GET /api/v1/hydroma/validation` | `live` | `science-web` | PUB-G1 |
| Reproducibility | `public/science/reproducibility` | `GET /api/v1/hydroma/validation` | `live` | `science-web` | PUB-G1 |
| Privacy | `public/policy/privacy` | `GET /api/v1/legal-texts/{locale}/privacy` | `live` | `content-web` | PUB-G3 |
| Cookies | `public/policy/cookies` | `GET /api/v1/legal-texts/{locale}/cookies` | `live` | `content-web` | PUB-G3 |
| Terms | `public/policy/terms` | `GET /api/v1/legal-texts/{locale}/terms` | `live` | `content-web` | PUB-G3 |
| Learning library | `public/education/library` | `GET /api/v1/content/search` | `live` | `content-web` | PUB-G1 |
| Advanced search | `public/education/advanced-search` | `GET /api/v1/content/search` | `live` | `content-web` | PUB-G1 |
| Glossary | `public/education/glossary` | `GET /api/v1/science/agrovoc` | `live` | `science-web` | PUB-G1 |
| Marketplace demo | `public/components/marketplace` | `GET /api/v1/marketplace/stats`, `GET /api/v1/marketplace/producers` | `live` | `marketplace-web` | PUB-G1 |
| EcoWallet demo | `public/components/ecowallet` | `GET /api/v1/ecowallet/health`, `/earning-options`, `/redemption-options` | `live` | `wallet-web` | PUB-G1 |
| HyDroMa engine | `public/components/hydroma-engine` | `GET /api/v1/models`, `/models/cpp-status`, `/models/pinn-status` | `live` | `science-web` | PUB-G1 |
| MRV dashboard | `public/components/mrv-dashboard` | `GET /api/v1/mrv/public/dashboard-summary` | `live` | `mrv-web` | PUB-G1 |
| Land profiler | `public/components/land-profiler` | `GET /api/v1/land/profiles` | `live` | `land-web` | PUB-G1 |
| Satellite view | `public/components/satellite-view` | `GET /api/v1/satellite/health`, `/providers` | `live` | `satellite-web` | PUB-G1 |
| API playground | `public/components/api-playground` | `GET /api/v1/tool-registry` | `live` | `platform-web` | PUB-G1 |
| Water management | `public/services/water-management` | `GET /api/v1/hydroma/water` | `live` | `science-web` | PUB-G1 |
| Carbon registry | `public/services/carbon-registry` | `GET /api/v1/hydroma/carbon` | `live` | `science-web` | PUB-G1 |
| Land intelligence | `public/services/land-intelligence` | `GET /api/v1/land/health`, `GET /api/v1/land/profiles` | `live` | `land-web` | PUB-G1 |
| Satellite intelligence | `public/services/satellite-intelligence` | `GET /api/v1/satellite/health`, `/providers` | `live` | `satellite-web` | PUB-G1 |
| MRV verification | `public/services/mrv-verification` | `GET /api/v1/mrv/public/dashboard-summary` | `live` | `mrv-web` | PUB-G1 |
| AI advisor | `public/services/ai-advisor` | `GET /api/v1/ai/health` | `live` | `platform-web` | PUB-G1 |
| API access | `public/services/api-access` | `GET /api/v1/tool-registry`, `GET /api/v1/platform/health` | `live` | `platform-web` | PUB-G1 |
| Marketplace access | `public/services/marketplace-access` | `GET /api/v1/marketplace/stats`, `GET /api/v1/marketplace/marketplaces` | `live` | `marketplace-web` | PUB-G1 |

`live` means the page renders what the endpoint returns and shows `statusLine.unavailable` with the error detail when the request fails. It does not mean a response was observed at build time; none was.

### The one `live-partial` entry

`public/science/benchmarks` declares the title "Benchmarks" and the description "Standard benchmarks for model evaluation", then calls `GET /api/v1/science/datasets` and renders dataset availability. The source comment at `public/science/benchmarks/page.tsx:58` states that no benchmark results are published by the gateway. The page is honest about the data it has, but it is not a benchmark page and its heading promises something the response does not contain. Gate PUB-G2 covers this.

## Matrix B — static editorial pages

These 28 pages make no request. Each renders the `unavailable` contract block and asserts no live figure.

| Group | Pages | Owner | Gate |
|---|---|---|---|
| Audiences | `public/audiences/{farmers,cooperatives,ngos,investors,government,researchers}` | `content-web` | PUB-G4 |
| Goals | `public/goals/{mission,vision,values,impact,manifesto,roadmap}` | `content-web` | PUB-G4 |
| Policy | `public/policy/{governance,accessibility,licensing}` | `content-web` | PUB-G4 |
| Education | `public/education/{courses,certifications,workshops,video-player,library-advanced}` | `content-web` | PUB-G4 |
| Channels | `public/channels` | `inclusive-web` | PUB-G4 |
| Components | `public/components/dispute-resolution` | `marketplace-web` | PUB-G4 |
| Services | `public/services/{overview,offline-tools}` | `content-web` | PUB-G4 |
| Top level | `public/{home,why,visit,cta}` | `content-web` | PUB-G4 |

`public/policy/licensing` declares the constant `LEGAL_TEXTS_PATH = '/api/v1/legal-texts/{locale}/{slug}'` but performs no request, because no `licensing` slug is registered. The page states this in both locales. It is correctly classified as static.

## Acceptance criteria

- **PUB-G1 live data fidelity.** Every figure on an endpoint-bound page is present in the response that produced it. When the request fails, the page shows `statusLine.unavailable` and the returned error, and shows no figure. The `ProvenanceStamp` source string equals the path actually requested.
- **PUB-G2 benchmark honesty.** Either the benchmarks page is bound to a benchmark endpoint, or its heading and description state that no benchmark results are published. A dataset table under a "Benchmarks" heading is not accepted.
- **PUB-G3 legal text.** A legal page shows body text only when `status === 'published'`. A draft or absent record shows the `unavailable` block. Version, status, and `effective_at` come from the record, never from a constant.
- **PUB-G4 static pages.** Each static page renders the `unavailable` contract block, shows a `StatusDot` at `down`, and contains no number, date, DOI, partner name, or certification that is not sourced. `scripts/check-verified-claims.mjs` reports zero offenders on this surface.
- **PUB-G5 locale parity.** All 14 catalogs in `apps/web/messages` contain the keys the 62 pages use, and every page renders in `fa` and `ar` without a missing-translation error.
- **PUB-G6 metadata.** Every page sets a canonical URL and a language alternates map. No page sets `verified={true}` on a stamp that is not backed by a successful response.

## Completable without a backend change

| Item | Work | Gate |
|---|---|---|
| Benchmarks heading | Rename the page to describe the dataset availability it actually shows, or add a note above the table stating that no benchmark results are published | PUB-G2 |
| Verified stamps | Set `verified` from the response state on the pages that currently hard-code `verified={false}` while holding live data, so the stamp reflects the call rather than the page type | PUB-G1 |
| Locale coverage | Extend `apps/web/src/content/public-pages.test.ts`, which asserts only `fa` and `en`, to all 14 catalogs so the parity gate in [`TESTING.md`](TESTING.md) is enforced where the content lives | PUB-G5 |
| Dataset metadata | Several pages define `TITLES` and `DESCRIPTIONS` as `{fa, en}` maps inline. Move them to the catalogs so all 14 locales resolve | PUB-G5 |
| Error surfacing | Show the returned error on the pages that currently collapse a failed request into the generic `unavailableDescription` | PUB-G1 |
| Static page ordering | `public/policy/{governance,accessibility,licensing}` and `public/goals/roadmap` are static while their neighbours are live; decide per page whether a live binding exists rather than leaving the split undocumented | PUB-G4 |

## Requires a new or changed backend API

| Item | Required change | Gate |
|---|---|---|
| Benchmarks | A benchmark registry and result endpoint. `services/api_gateway/routers/benchmark.py` exists; no read endpoint for stored results is in `openapi.json` | PUB-G2 |
| Learning courses | `services/api_gateway/routers/lms.py` declares the prefix `/api/v1/lms` but is neither imported nor included in `services/api_gateway/main.py`, so `/api/v1/lms/courses` does not exist. Mounting the router is the prerequisite | PUB-G4 |
| Audiences | An audience registry. No endpoint describes the six audience pages today | PUB-G4 |
| Goals | An impact and measurement store. `public/goals/impact` is static because no impact metric is published | PUB-G4 |
| Case studies and DOIs | `/api/v1/science/datasets/{slug}/doi` exists; the case-study and evidence pages read `/science/citations/index` only, so per-dataset DOI resolution is unused | PUB-G1 |
| Service health roll-up | A public aggregation endpoint. `public/services/overview` is static because each satellite service exposes only its own health route | PUB-G4 |
| Dispute resolution | A public dispute status projection. `services/api_gateway/routers/disputes.py` is mounted under `/disputes`, not under `/api/v1`, and no public projection exists | PUB-G4 |
| Governance and accessibility statements | Published legal text. The legal-texts service accepts only registered slugs, as `public/policy/licensing` already demonstrates | PUB-G4 |
| Video library and workshops | A media store with published content | PUB-G4 |
| Offline tools | A bundled tool manifest for the feature-phone channel | PUB-G4 |

## Definition of Done for the public surface

1. Each of the 62 pages carries exactly one status from the two matrices, and that status matches what the code renders.
2. Every `live-partial` entry has become `live` or has moved to the requires-new-API table with an owner.
3. `scripts/check-verified-claims.mjs` reports zero unverified claims marked verified across `apps/web`.
4. All 14 catalogs satisfy the parity gate, and `public-pages.test.ts` enforces all 14 rather than two.
5. No page asserts a figure that is not present in the response that produced it. This is verified by reading the page and the response together, not by a screenshot.
6. The full quality gate in [`TESTING.md`](TESTING.md) is green on the same commit, including the production-server end-to-end run across the public i18n routes.
7. Deployment remains disabled per [`DEPLOYMENT.md`](DEPLOYMENT.md). A green content gate is not a deployment approval.

## External blockers

| ID | Blocker | Owner |
|---|---|---|
| B6 | `services/api_gateway/routers/lms.py` is not mounted, so the LMS endpoints do not exist and `public/education/courses` cannot bind | `platform-web`, `content-web` |
| B7 | `/api/v1/legal-texts` returns only registered slugs. Legal copy for governance, accessibility, and licensing must be published before those pages can bind | `content-web` |
| B8 | No benchmark result store is published, so `public/science/benchmarks` cannot show benchmark outcomes | `science-web` |
| B9 | Resolved: `apps/web/src/config/site.ts` is the only environment reader, with `scripts/check-site-url.mjs` enforcing the invariant in quality/CI | `platform-web` |
| B10 | Public server-side `GET` requests use a 60-second revalidation window; browser requests and mutations remain `no-store`. Per-route ISR/static decisions are still required where full static generation is mandatory | `platform-web` |

## Execution result — 2026-09-25

- all 62 public pages now read registered gateway endpoints or render an explicit unavailable state.
- public science, education, component, service, policy, audience, goal, channel, and model-count surfaces no longer use local static numbers as live data.
- CTA and visit forms post to the registered newsletter and contact endpoints and expose non-2xx failures.
- `scripts/check-verified-claims.mjs` reports zero unsupported verified claims.
- B6–B8 and B10 remain external or require per-route static-generation decisions; B9 is resolved by the shared site-URL module and guard.
