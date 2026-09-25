# Frontend architecture

**Status:** Wave 0/1/2 baseline plus Wave 4 PWA shell implemented. Remaining gates cover UI session screens, production Redis promotion, additional domains, and deployment administration.

## Layers

```text
apps/web (Next.js 15 App Router, React 19, TypeScript)
        │ same-origin BFF route handlers
        ▼
services/api_gateway (FastAPI)
        ├── scientific services and HyDroMa engine
        ├── C++20 numerical core through the existing bridge
        └── persistence and event integrations
```

- `apps/web` owns presentation, routing, accessible interaction, and the same-origin BFF boundary.
- The BFF owns browser-facing session and DTO mapping. The browser does not receive bearer tokens or backend secrets.
- `services/api_gateway` owns API authentication, authorization checks, typed responses, and service orchestration.
- `engine/hydroma` and `engine/cpp_core` own scientific computation. UI code must not reimplement model logic.
- Configuration is read through `engine/hydroma/config/settings.py` and the repository settings boundary; secrets are not source files.

## Data and trust boundaries

- Public, cacheable reads may be reused by a public shell when the PWA gates are met.
- Authenticated, private, administrative, order, payment, and escrow data remain online and server-owned.
- Browser storage is limited to non-sensitive drafts and an explicit outbox. It is not an authorization boundary.
- State-changing requests go through the BFF and are checked for same-origin intent, session validity, and authorization at the data boundary.

## API contract

There is one canonical OpenAPI source. Generated clients must be checked for drift; hand-written DTOs may not silently introduce a second contract. Every new endpoint requires a response model, status codes, and a typed error envelope. The BFF maps backend responses to stable browser-facing DTOs.

The contract and generation rules are recorded in [`../adr/0003-api-contract.md`](../adr/0003-api-contract.md).

## Security headers

Apply the baseline security headers to every route. Use a report-only CSP rollout on the production build, then enforce a strict CSP with nonces only on dynamic, authentication, account, checkout, administrative, and BFF routes. A global nonce and production `unsafe-inline`/`unsafe-eval` are not part of this decision.

## Delivery order

1. **Wave 0:** baseline, decision records, and green checks.
2. **Wave 1:** environment, BFF/session, and API contract gates.
3. **Wave 2:** design tokens, i18n parity, RTL, and accessibility.
4. **Later waves:** PWA/local-first, additional domains, and deployment only after their dependencies are green.

Shared domain routes are declared in `apps/web/src/lib/domains/registry.ts`. Hydroma tool pages are generated from the 52-tool registry, Admin is deny-by-default against the opaque server session, and Research/System capabilities remain explicitly `unavailable` until a real endpoint exists.

PWA shell behavior is implemented with private/financial data excluded from cache. Production deployment remains gated on the deployment contract and reviewer configuration; see [`PWA_AND_OFFLINE.md`](PWA_AND_OFFLINE.md) and [`DEPLOYMENT.md`](DEPLOYMENT.md).

## Non-goals and prohibited shortcuts

- No client-side model substitution for a scientific result.
- No second API schema or hidden fallback chain.
- No service worker for authenticated or financial requests.
- No deploy or package publication from a normal branch build.
- No new route or cache policy without its contract, ownership, and test.
