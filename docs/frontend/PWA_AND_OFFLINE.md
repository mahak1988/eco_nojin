# PWA and offline behavior

**Status:** Baseline implemented in Wave 4. Broader local-first behavior remains conditional on production Redis, API cache headers, and conflict-resolution contracts.

## Approved design

- Use Serwist for the Next.js app shell and public assets.
- Precache only the app shell, static assets, and public resources.
- Use `NetworkFirst` only for explicitly public `GET` requests.
- Use `StaleWhileRevalidate` only for static public assets.
- Use Dexie for drafts and an explicit outbox, not as a general database.
- Persist TanStack Query data only for public queries, with a `buildHash` and bounded `maxAge`.

## Implemented baseline

- `apps/web/src/app/sw.ts` is the Serwist worker and excludes `/api/*` from runtime caching.
- `apps/web/src/lib/offline/` contains the Dexie draft/outbox schema, allowlist policy, connectivity listener, and flush queue.
- `OfflineProvider` and `OfflineBanner` are mounted by the locale layout.
- `apps/web/tests/offline.spec.ts` verifies a public page after one online visit and an offline reload.
- Generated `apps/web/public/sw.js` is ignored and produced only by the production build.

## Online-only boundaries

The following always require a validated server session and a live request:

- authentication and account changes;
- orders, checkout, payment, escrow, and wallet operations;
- administrative or other privileged operations;
- any response containing private data, a `Set-Cookie` header, or `no-store` semantics.

Do not cache `/api/*` by a broad path rule. Do not put secrets, tokens, payment data, or private PII in IndexedDB. Do not treat an outbox as permission to complete a financial transaction offline.

## Conflict and UX rules

Each queued mutation has a stable idempotency key, an explicit lifecycle (`queued`, `sending`, `acknowledged`, `failed`), and a user-visible retry or discard action. A stale local value is labelled as stale; it never silently overwrites newer server state. The online-only path must remain the source of truth for protected state.

## Release gates

- Service worker scope and cache routes are reviewed in a production build.
- Tests prove that private, financial, and privileged requests never enter caches.
- Offline startup, queue recovery, replay, cancellation, and conflict handling are covered.
- Cache version changes and rollback behavior are documented with the application build.
- A service worker is not enabled while the session boundary is still being stabilized.

The PWA is an offline shell and draft convenience layer, not an offline authorization or ledger system.
