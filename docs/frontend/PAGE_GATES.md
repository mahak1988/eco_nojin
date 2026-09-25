# Page gates

**Status:** Recorded from the repository at commit `2177450` on 2026-09-25. This document is the gate contract for the two page surfaces described in [`MARKETPLACE_IMPLEMENTATION.md`](MARKETPLACE_IMPLEMENTATION.md) and [`PUBLIC_PAGES_EXECUTION.md`](PUBLIC_PAGES_EXECUTION.md). It does not report a gate as passed. No gate in this document has been executed against a running gateway in this record.

## Surface under the gate

| Surface | Scope | Routes |
|---|---|---|
| Marketplace | `apps/web/src/app/[locale]/market/**` | 73 page files, plus 444 catch-all template routes |
| Public | `apps/web/src/app/[locale]/public/**` | 62 page files |
| Total | | 579 page files plus 444 generated routes |

## Gate index

| Gate | Subject | Owner |
|---|---|---|
| MKT-G1 | Catalog, compare, and public read surfaces render response data only | `marketplace-web` |
| MKT-G2 | Product detail binds to the product and trace endpoints | `marketplace-web` |
| MKT-G3 | Cart is connected to product add, persists writes, and empties on submit | `marketplace-web` |
| MKT-G4 | Cart to order to payment to escrow completes with matching amounts | `marketplace-web`, `payments-api` |
| MKT-G5 | Bazaar wizard submits once and is idempotent | `marketplace-web` |
| MKT-G6 | Unavailable routes stay unavailable and indexable-free | `marketplace-web` |
| MKT-G7 | Checkout confirmation asserts nothing it was not given | `marketplace-web` |
| MKT-G8 | Wallet is truthful about currency, available balance, and withdrawal | `marketplace-web`, `wallet-api` |
| MKT-G9 | Declared endpoints match `openapi.json` | `platform-web` |
| PUB-G1 | Endpoint-bound pages render response data only | per-surface web owner |
| PUB-G2 | Benchmarks page does not promise benchmark outcomes | `science-web` |
| PUB-G3 | Legal pages show text only when published | `content-web` |
| PUB-G4 | Static pages assert no unbacked figure | `content-web` |
| PUB-G5 | All 14 catalogs resolve on all 62 public pages | `i18n` |
| PUB-G6 | Canonical and alternate metadata is set; stamps reflect the call | `platform-web` |
| GATE-G1 | Session and Redis behave correctly for every authenticated route | `bff`, `platform-operations` |
| GATE-G2 | No page hard-codes a number that an endpoint owns | all page owners |
| GATE-G3 | Contract drift is zero | `platform-web` |
| GATE-G4 | Security findings on the commerce surface are closed or accepted | security owner |

## Acceptance criteria by group

The full text of each criterion is in its owning document. The group-level rule is that a gate is satisfied only when every criterion in it is satisfied on the same commit.

| Group | Gates | Rule |
|---|---|---|
| Live reads | MKT-G1, PUB-G1 | Every rendered figure is present in the response that produced it. A failed request renders `unavailable` and the error, and no figure. |
| Product and cart | MKT-G2, MKT-G3 | Add to cart performs a write. Quantity and removal persist across a reload. The submitted cart is emptied. The displayed total is server-computed or labelled an estimate. |
| Money and escrow | MKT-G4 | A payment is created with a gateway the service accepts, the confirm call runs, the escrow ledger contains the hold, the held amount equals the displayed amount, and the dispute and settle controls are reachable and return the documented codes. |
| Creation flows | MKT-G5 | The wizard submits once; a repeated submit with the same idempotency key does not create a second record. |
| Honest absence | MKT-G6, MKT-G7, PUB-G4 | No number, date, identifier, window, currency, or partner claim without a source. `robots: noindex` on template routes. |
| Content binding | PUB-G2, PUB-G3 | A heading matches the response. Legal text renders only when `status === 'published'`. |
| Locale | PUB-G5 | All 14 catalogs resolve on all 62 public pages with no missing-translation error. |
| Contract | MKT-G9, GATE-G3 | Every endpoint string in the web layer appears in `openapi.json` with the same path template. `openapi.json` is regenerated and the generated client drift check passes. |
| Session | GATE-G1 | See the session and Redis section below. |
| Security | GATE-G4 | B1 and B2 are fixed or accepted in writing. |

## Session and Redis dependency

Every authenticated route on both surfaces depends on the same BFF session. The chain is:

```text
browser cookie  ->  apps/web/src/app/api/[...path]/route.ts
                ->  apps/web/src/lib/session/store.ts (Redis, or an in-process Map)
                ->  services/api_gateway with Authorization: Bearer <accessToken>
```

### What the session is

- The cookie holds an opaque identifier only. `randomBytes(32).toString('base64url')` is generated in `apps/web/src/lib/session/store.ts:54` and stored as the cookie value.
- The access token, refresh token, and user record live server-side under the key prefix `eco:session:`. The browser never receives a bearer token.
- The cookie is `httpOnly`, `sameSite=lax`, `path=/`, and named `__Host-eco_session` over HTTPS, `eco_session` otherwise.
- `SESSION_TTL_SECONDS` defaults to 28 800 seconds and drives both the cookie `maxAge` and the Redis `EX`.

### Redis is a hard production requirement

`getRedisUrl()` in `apps/web/src/lib/config/server-env.ts:26` returns `null` when `REDIS_URL` is unset and **throws in production**. Outside production it returns `null`, and `store.ts` falls back to a `Map` on `globalThis`.

The consequence of the fallback is precise and it is not limited to development ergonomics:

- Sessions are not shared between processes. A second Next.js process, or a restarted one, cannot resolve an existing cookie, and the BFF treats the request as unauthenticated.
- Sessions do not survive a restart.
- With more than one replica behind a load balancer, the cart and checkout routes fail intermittently depending on which replica answers.

Therefore: **a two-replica deployment without `REDIS_URL` is not a degraded mode, it is a broken one.** In production the process refuses to start, which is the intended behaviour and matches the `frontend-secrets` contract in [`DEPLOYMENT.md`](DEPLOYMENT.md).

### Refresh and failure handling

On a `401` from the gateway the BFF calls `refreshSession` once, retries the original request, and on failure clears the cookie and returns `401`. The retry happens once; a second `401` is returned to the caller. Mutations are protected by `assertBffRequest`, which requires a matching `Origin`, the `X-CSRF-Intent: 1` header that `apiPost`/`apiPatch`/`apiDelete` set, and a `Sec-Fetch-Site` of `same-origin` when the browser sends it.

### Two contract observations

1. **`SESSION_SECRET` has been removed from the active contract.** The session identifier is a 32-byte random value stored in Redis, and the unread `getSessionSecret()` helper was removed. Production requires `REDIS_URL`; Helm and Kubernetes no longer request a signing secret.
2. **`/api/v1/auth/**` is excluded from the generic proxy.** `api/[...path]/route.ts:50` returns `404` for that prefix, so authentication must go through the dedicated `/api/auth/*` route handlers. All four backend calls the BFF makes are present in `openapi.json`: `POST /api/v1/auth/login`, `/register`, `/refresh`, `/logout`, and `GET /api/v1/auth/me`. The session chain is contract-complete; the dependency is Redis, not the auth contract.

### Gate GATE-G1

Satisfied when, against a gateway and a Redis instance:

1. A login through `/api/auth/login` issues a cookie whose value is not a token and whose record exists in Redis under `eco:session:`.
2. `GET /api/v1/marketplace/cart` returns `200` with that cookie and `401` without it.
3. Killing the Redis connection produces a visible, non-silent failure on the cart route rather than an empty cart presented as an empty basket.
4. A `401` from the gateway triggers exactly one refresh and one retry.
5. A cross-origin `POST` is rejected with `403` before the request reaches the gateway.
6. The same session resolves correctly from two separate application processes.

Item 3 matters because the cart page renders the same empty state for "no items" and "not signed in" (`market/cart/page.tsx:62`), so a session-store outage is currently indistinguishable from an empty basket.

## Work that needs no backend change

| Surface | Items |
|---|---|
| Marketplace | Product add-to-cart write; cart clearing; idempotent retry; payment selector aligned to the accepted gateway list; the escrow confirm call; the escrow page order id; fee model labelling; wallet currency, available-balance and withdrawal truthfulness; binding the twelve product sub-pages to the existing product and trace endpoints; binding search to the existing search and product endpoints; registry path-template drift |
| Public | Benchmarks heading; verified stamps driven by the response; locale parity test coverage; moving inline `TITLES`/`DESCRIPTIONS` into the catalogs; error surfacing; documenting the live/static split |

Full lists with evidence are in the two companion documents under "Completable without a backend change".

## Work that needs a new or changed API

| Surface | Items |
|---|---|
| Marketplace | Gateway allow-list and a `payment_method` enum; server-computed escrow amount; one order per checkout; escrow model unification; consistent release authority; wallet ownership from the session; wallet withdrawal; bazaar, store, and category reads; a buyer-scoped order list; an authoritative fee schedule |
| Public | Benchmark results; the unmounted LMS router; audience, goal, and impact stores; per-dataset DOI binding; a public service-health roll-up; a public dispute projection; published governance, accessibility, and licensing text; a media store; a bundled offline tool manifest |

Full lists with evidence are in the two companion documents under "Requires a new or changed backend API".

The rule that governs both lists: a page is not connected to an endpoint that exists but is unauthenticated, and a page is not connected to a placeholder that returns hard-coded counters. `apps/web/src/lib/domains/registry.ts:145` already records the second case for `/api/v1/admin/overview`; the same rule applies to every entry in the new-API tables.

## External blockers

Consolidated from both companion documents. None of these is resolved by a change in `apps/web`.

| ID | Blocker | Owner | Blocks |
|---|---|---|---|
| B1 | `GET /marketplace/orders` and `GET /marketplace/orders/{order_id}/track` have no authentication | `marketplace-api`, security owner | GATE-G4, MKT-G6 |
| B2 | `GET /ecowallet/wallet/{user_id}` and `GET /ecowallet/earnings` accept an unauthenticated arbitrary user id | `wallet-api`, security owner | GATE-G4, MKT-G8 |
| B3 | Two escrow implementations read different tables, so `orders/{order_id}/settle` and `/complete` cannot succeed for a marketplace payment | `payments-api` | MKT-G4 |
| B4 | `zarinpal` requires `ZARINPAL_MERCHANT_ID` and `international` requires `INTL_PAYMENT_CHECKOUT_URL`; neither is in the repository, so only `bank` is reachable | `platform-operations` | MKT-G4 |
| B5 | `REDIS_URL` must come from a cluster secret in production; no value is in the repository | `platform-operations` | GATE-G1 |
| B6 | `services/api_gateway/routers/lms.py` is neither imported nor included in `main.py`, so `/api/v1/lms/courses` does not exist | `platform-web`, `content-web` | PUB-G4 |
| B7 | `/api/v1/legal-texts` returns only registered slugs, so governance, accessibility, and licensing text must be published before those pages can bind | `content-web` | PUB-G4 |
| B8 | No benchmark result store is published | `science-web` | PUB-G2 |
| B9 | Resolved: all page/metadata code reads the shared `apps/web/src/config/site.ts`; `scripts/check-site-url.mjs` fails on placeholder origins or inline environment reads | `platform-web` | PUB-G6 |
| B10 | Public server-side `GET` requests now use a 60-second revalidation window; browser requests and mutations remain `no-store`. A per-route ISR decision is still required for any page that must be statically generated | `platform-web` | PUB-G5, GATE-G1 |

## Definition of Done

A page group is done when all of the following hold on one commit.

1. Every route in the group has a status in its matrix that matches what the code renders, and every `live-partial` entry has become `live` or moved to the new-API table with a named owner.
2. Every acceptance criterion in the group's gates is satisfied, verified by reading the page and the response together rather than by appearance.
3. No page hard-codes a currency, fee rate, escrow window, currency amount, transaction identifier, or dataset figure that an endpoint owns.
4. `openapi.json` is regenerated, the generated client drift check passes, and no endpoint string in the web layer is absent from it.
5. The full quality gate in [`TESTING.md`](TESTING.md) is green: Biome, type-check, unit tests at the agreed threshold, 14-locale parity and i18n compilation, API generation with the Orval drift check, the production build, end-to-end tests against `next start`, the web-vitals and security scan, and the backend unit, integration, contract, and scientific checks.
6. Auth, money, and state-machine branches have targeted coverage above the global threshold, as required by [`TESTING.md`](TESTING.md).
7. GATE-G1 is satisfied against a real Redis instance and more than one application process.
8. B1 and B2 are fixed or accepted in writing by the security owner. The commerce surface is not declared done while they are open.
9. Deployment remains disabled until the release gates in [`DEPLOYMENT.md`](DEPLOYMENT.md) are satisfied. A green page gate is evidence for a decision, not the decision.

## Enforcement

| Check | Command |
|---|---|
| Unverified claims | `node scripts/check-verified-claims.mjs` |
| Frontend quality gate | `pnpm -C apps/web quality` |
| Locale and i18n | `pnpm -C apps/web i18n:compile` |
| Contract generation and drift | `pnpm -C apps/web generate:api` |
| Production build | `pnpm -C apps/web build` |
| End-to-end against production | `pnpm -C apps/web test:e2e` |
| Backend unit | `python -m pytest tests/unit -q` |
| Backend contract | `python -m pytest tests/contract -q` |
| Database migrations | `python -m pytest tests/integration/test_sqlite_migrations.py -q` |

A failing, skipped, or unavailable required check blocks the gate. It is not a waiver.

## Execution result — 2026-09-25

- marketplace, public, developer, trust, AI, and direct informational pages were executed against the registered OpenAPI surface.
- the provenance guard, Biome, type-check, unit tests, 14-locale parity, production build, and the i18n/a11y/offline/auth/security/page/marketplace E2E suites are green.
- B1–B10 remain external and are not marked complete by frontend evidence.
