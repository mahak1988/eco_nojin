# ADR 0002: Same-origin BFF and session

- **Status:** Accepted
- **Date:** 2026-09-25
- **Scope:** Browser authentication and authorization

## Context

A browser must not hold long-lived bearer credentials while the API gateway remains the policy enforcement point. Direct cross-origin calls also make CSRF, tenant scope, and response shaping harder to reason about.

## Decision

- Use Next.js Route Handlers under `/api/*` as a same-origin BFF.
- Keep the session server-side and set only `__Host-eco_session` in the browser, with `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`, and no `Domain`.
- Rotate the session on login and role changes; invalidate it on logout and expiry.
- Enforce RBAC in the data-access layer or nearest handler, including resource ownership and object state.
- Validate same-origin intent for mutations. No state change is allowed through `GET`.
- Map backend responses to stable browser DTOs; do not expose backend credentials or raw internal errors.

## Rejected patterns

- Tokens in `localStorage` or `sessionStorage`.
- Browser-managed `Authorization: Bearer` as the normal path.
- Wildcard CORS with credentials, broad cookie domains, or `SameSite=None`.
- UI route guards or middleware used as the only authorization check.

## Consequences and gates

The browser has one origin boundary, mutations are easier to audit, and logout can clear both server and sensitive client state. The final session implementation must keep opaque state server-side so revocation, absolute expiry, and concurrent refresh behavior are enforceable; a self-contained token cookie is not the final design. Tests must cover session rotation, fixation, expiry, origin/CSRF checks, role and object-scope decisions, and cross-user cache isolation. PWA caching of private or cookie-bearing responses remains prohibited.

This ADR defines policy only. It does not create an account, grant an administrative role, or claim access to an environment.
