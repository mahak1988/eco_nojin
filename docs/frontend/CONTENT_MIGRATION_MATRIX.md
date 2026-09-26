# Content migration matrix

This matrix records the public-page truthfulness audit completed on 2026-09-25. The rule is: no number, DOI, date, status, or partner claim may be shown with `verified={true}` unless it comes from a live backend response or a controlled editorial source.

## How a phase is measured

Each group below is a **physical route** group, measured by `page.tsx` file, not a logical page path. A group counts as migrated only when every path in it satisfies the measurable rule recorded for that group in [`PAGE_CHECKLIST_600.md`](PAGE_CHECKLIST_600.md): the `state` value matches what the code renders, every endpoint string appears in `openapi.json`, the provenance value is backed by a response, and the acceptance-evidence cell names a command that was run against the named commit.

A group whose `state` is `static` because no contract exists is complete when it asserts nothing, not when a contract appears. A group whose `state` is `live` is incomplete while any figure on the page is absent from the response that produced it. Phase completion is reported per group, not as a page total, and a phase is never reported complete from a count of logical paths.

## Phase 0 — frontend-only honesty

Target: remove unsupported claims and show the existing `statusLine.unavailable` / `market.template.unavailable*` states.

- `public/audiences/*`
- `public/goals/{impact,vision,mission,values,manifesto}`
- `public/policy/{governance,accessibility}`
- `public/science/{case-studies,peer-review,benchmarks,uncertainty,validation,reproducibility,validation-methods,gap-analysis,limitations}`
- `public/education/{certifications,video-player,library,library-advanced,glossary,workshops}`
- `trust/{sanctions,page}`
- `developers/{changelog,sdks,webhooks,partners,status-api}`

## Phase 1 — use live endpoints

- `public/model-count` → `/api/v1/models`
- `public/science/data-sources` → `/api/v1/science/datasets`
- `public/science/methodology` → `/api/v1/science/model-cards`
- `public/policy/{privacy,cookies,terms}` → `/api/v1/legal-texts`
- `public/education/courses` → `/api/v1/lms/courses`
- `public/components/*` → the corresponding satellite, land, marketplace, wallet, MRV and dispute endpoints
- `public/services/*` → aggregated live health endpoints
- `developers/api` → generated from `openapi.json`
- `developers/status-api` → platform and service health only; quota remains unavailable
- `ai/voice` → `/api/v1/ai/chat` plus browser speech synthesis until voice endpoints are real
- `ai/feedback` → support/contact endpoint when content is connected

## Phase 2 — backend prerequisites

1. Keep `content_public.router` registered and seed published content.
2. Add a public service-health aggregation router.
3. Add a public trust projection over audit, carbon and product trace data.
4. Do not connect pages to stubbed or placeholder endpoints.

## Phase 3 — new stores/APIs

- Benchmark registry and runner
- Reproducibility run ledger with content hashes
- Case-study and DOI store
- Impact/M&E store
- Audience and partner registry
- Webhook delivery and published SDKs

## Enforcement

`scripts/check-verified-claims.mjs` reports every page containing an unverified `verified={true}` claim. It becomes a required CI check after the migration reaches zero offenders.

## Measured state — 2026-09-26

| Phase | Groups in scope | Physical routes | Blocking items |
|---|---|---|---|
| Phase 0 | public, trust, developers | public static groups plus `trust` 7 and `developers` 9 | C600-G7 provenance evidence, C600-G8 accessibility coverage |
| Phase 1 | public, developers, AI | public 62 plus `ai` 8 | B6 unmounted LMS router, B10 per-route static-generation decision |
| Phase 2 | gateway registration and seeding | not a page count | B6, B7 unpublished legal text |
| Phase 3 | new stores and APIs | no page exists yet | B8 no benchmark result store |

- The 62 public physical routes split 34 endpoint-bound and 28 static editorial, unchanged from the 2026-09-25 audit.
- 17 of the 82 routes outside the marketplace and public surfaces are in the workspace group; the remaining 65 span admin, research, system, AI, developers, trust, Hydroma, inclusive, auth, and the single-page groups. None has a declared position in the logical catalogue, which is blocker B11 in [`PAGE_GATES.md`](PAGE_GATES.md).
- No phase above is reported complete on the basis of a catalogue count, and the declared 600 logical paths are not evidence that any group migrated.
