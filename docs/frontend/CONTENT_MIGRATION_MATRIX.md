# Content migration matrix

This matrix records the public-page truthfulness audit completed on 2026-09-25. The rule is: no number, DOI, date, status, or partner claim may be shown with `verified={true}` unless it comes from a live backend response or a controlled editorial source.

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
