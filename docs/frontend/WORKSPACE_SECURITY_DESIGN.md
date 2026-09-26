# Professional workspace security and page design

**Date:** 2026-09-25
**Route:** `/{locale}/workspace`
**Separation:** consumer marketplace `/market`; platform administration `/admin`; professional work `/workspace`.

## References

- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [Next.js Authentication guide](https://nextjs.org/docs/15/app/guides/authentication)
- [Carbon data tables](https://carbondesignsystem.com/components/data-table/usage)
- [Shopify Polaris patterns](https://polaris.shopify.com/patterns)
- [GitHub Primer navigation](https://primer.style/product/ui-patterns/navigation)

## Roles

Proposed backend roles: `advisor`, `operator`, `support`, `analyst`, `content_editor`, `auditor`, `manager`.

Existing platform roles that may be recognized today: `admin`, `security_admin`, `content_admin`, `user_admin`.

The frontend registry is descriptive only. It must never be treated as authorization authority. Until the backend issues a proposed role, no such user can enter a professional-only page.

## Enforcement model

1. The workspace layout reads the opaque server session.
2. The role must be in the server-side workspace allowlist.
3. Unknown, missing or inactive sessions are denied.
4. Child pages do not repeat or weaken the layout guard.
5. BFF upstream calls carry the server session, not browser-supplied role headers.
6. No role, user, job, KPI, audit record or customer record is stored in localStorage.
7. Every page without a registered endpoint renders `unavailable` and makes no synthetic record.
8. MFA requirements are reported as unavailable until the backend enforces them; the frontend never claims MFA succeeded.

## Page map

- `/workspace/overview`
- `/workspace/assignments`
- `/workspace/cases`
- `/workspace/knowledge`
- `/workspace/reports`
- `/workspace/team`
- `/workspace/approvals`
- `/workspace/targets`
- `/workspace/audit`
- `/workspace/operations`
- `/workspace/operations/jobs`
- `/workspace/operations/events`
- `/workspace/operations/health`
- `/workspace/settings`
- `/workspace/settings/notifications`
- `/workspace/settings/access`

## UI requirements

- Persistent workspace shell with role-filtered navigation.
- Clear organization/team context only when provided by the backend.
- Resource tables use captions, stable headers, keyboard sorting and distinct action targets.
- Breadcrumbs expose parent return and current location.
- Status updates use semantic status regions.
- 320 CSS pixel reflow and 44 pixel touch targets.
- Help path is consistent and points to a registered endpoint.
- Empty/unavailable state explains which backend capability is missing without exposing internals.

## Data and audit rules

- Professional records are never added to `/public` or `/market` payloads.
- Exports are disabled until a registered, role-gated export endpoint exists.
- Audit events must be produced by the backend; the frontend can only display them.
- PII, financial and customer data require an explicit scope in the backend response.

## Acceptance

- Server-side deny-by-default for consumer roles.
- No `MISSING_MESSAGE` in fa/en smoke tests.
- No fabricated records.
- Biome, type-check, unit tests, build, WCAG 2.2 AA and 14-locale parity pass.

## Execution result — 2026-09-25

- All 16 workspace routes and the central domain-registry entry are implemented.
- The layout resolves access from the opaque server session; missing, inactive and non-allowlisted roles receive distinct deny states.
- The role registry marks proposed roles as `issuedByGateway: false`; the frontend does not present them as active access.
- The workspace reads only registered organizations, content, sync and health capabilities. Unimplemented jobs, cases, assignments, reports, approvals, targets and exports remain unavailable.
- No role, session, professional record, export, MFA result or audit row is stored in the browser.
- Tier 0 smoke, WCAG 2.2 AA, 320-pixel reflow, 14-locale parity and the aggregate quality gate pass.

## Inventory note — 2026-09-26

- The surface measures 17 physical `page.tsx` routes today, against the 16 listed in the page map above. The 16 listed paths are the workspace's documented map; the extra physical route is not yet assigned to a listed path, and the difference is stated here rather than resolved by editing the map.
- These are physical routes. The declared 600 logical page paths are a separate inventory, and no workspace route has a declared position in it. That is blocker B11 in [`PAGE_GATES.md`](PAGE_GATES.md) and open item R-3 in [`PAGE_CHECKLIST_600.md`](PAGE_CHECKLIST_600.md).
- The checklist records the workspace group as `capability` state, `role` auth, and `response-bound` provenance, with accessibility evidence from the named specs and `not-covered` for every route without one. A role-gated route is never counted as a public route, and the frontend registry is never the authorization authority for this group.
- Nothing in this note changes an enforcement rule, an acceptance criterion, a role, or a page status. The design above stands as recorded on 2026-09-25.
