# ADR 0004: PWA and local-first boundaries

- **Status:** Conditional
- **Date:** 2026-09-25
- **Scope:** Offline shell, local data, and synchronization

## Context

Offline access is valuable for public information and drafts in low-connectivity settings. It is unsafe to treat a browser cache or outbox as an authorization, payment, or ledger boundary.

## Decision

- Use Serwist after the BFF/session and API contract gates are green.
- Precache the application shell and public static assets only.
- Use network-first behavior only for explicitly public `GET` resources.
- Use Dexie for drafts and an explicit, idempotent outbox.
- Persist query data only for public data with a build hash and bounded age.
- Keep authentication, account, order, payment, escrow, wallet, and privileged operations online.

## Data rules

No secret, token, private PII, financial state, or cookie-bearing response belongs in a service-worker cache or IndexedDB. An outbox item has a stable idempotency key, lifecycle, retry policy, and user-visible conflict resolution. It never completes a protected transaction without a fresh server decision.

## Consequences and gates

Offline startup and recovery must be tested in a production build. Cache scope, version rollback, replay, cancellation, and stale-data behavior are review items. A service worker is not enabled merely because a manifest exists.

The PWA is a convenience layer for public content and drafts, not an offline authorization system, payment system, or financial ledger.
