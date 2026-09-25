# Authentication and RBAC

**Decision:** Adopt the same-origin BFF/session boundary from [`../adr/0002-auth-bff.md`](../adr/0002-auth-bff.md).

## Browser flow

1. The browser calls a Next.js BFF route handler under the same origin.
2. The BFF authenticates with the server-side session service and calls the API gateway.
3. The API gateway evaluates the resource policy and returns a typed response.
4. The BFF maps the response to a browser DTO; backend tokens and secrets never cross into browser storage.

The session cookie is named `__Host-eco_session` and has `HttpOnly`, `Secure`, `SameSite=Lax`, and `Path=/`, with no `Domain` attribute. Session data is server-side. Login and role changes rotate the session. Logout invalidates the session and removes sensitive local data.

## Authorization rules

- Enforce RBAC in the data-access layer or the handler closest to the data. Middleware alone is not authorization.
- Check the authenticated principal, tenant/resource scope, action, and object state for every protected operation.
- Treat object identifiers from the browser as untrusted and re-check ownership or membership server-side.
- Reject state changes on `GET`. Mutating requests must validate session intent, `Origin`, and `Sec-Fetch-Site` where the BFF supports them.
- Use same-origin requests with credentials included only where the browser client needs the BFF cookie.

## Prohibited patterns

- Bearer tokens in `localStorage` or `sessionStorage`.
- A browser-supplied `Authorization` header as the normal authentication path.
- `SameSite=None`, a cookie `Domain`, or wildcard CORS combined with credentials.
- Treating a route guard, UI visibility check, or cached response as proof of authorization.
- Caching private, cookie-bearing, or financial responses in a service worker.

## Required tests

- Login, session rotation, logout, expired session, and fixation defenses.
- Cross-origin and missing-origin mutation attempts.
- Role and object-scope allow/deny cases for each protected capability.
- Concurrent tab behavior and cache isolation between users.
- No token or secret appears in browser storage, HTML, logs, or analytics events.

## Implemented routes

- `/[locale]/auth/login`, `/[locale]/auth/signup`, and `/[locale]/account/session`
- `SessionMenu` in the site navigation
- `/api/auth/login`, `/api/auth/signup`, `/api/auth/refresh`, `/api/auth/logout`, and `/api/auth/session`
- `/api/[...path]` for same-origin public and authenticated gateway calls
- `/health` and `/ready` for deployment probes
- `requireRole()` in `apps/web/src/lib/auth/require-role.ts`

The UI forms use message keys from all 14 catalogues, localized validation, labelled consent controls, accessible password toggles, and an Escape/focus-safe session menu.

`REDIS_URL` is required in production and `SESSION_SECRET` must contain at least 32 characters. In development, tests may use the in-memory session fallback.
