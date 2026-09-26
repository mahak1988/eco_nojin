# World-class page benchmark and implementation decision

**Date:** 2026-09-25
**Scope:** frontend pages in `apps/web`
**Method:** compare repository routes and states with official design systems and standards, not with screenshots or marketing pages.

## 1. Official references

| Area | Reference | Evidence used |
|---|---|---|
| Data-heavy admin | [IBM Carbon data table](https://carbondesignsystem.com/components/data-table/usage) | toolbar, caption, search/filter, pagination, selection, batch actions, keyboard sorting, `aria-sort` |
| Admin shell | [Carbon component overview](https://carbondesignsystem.com/components/overview/components) and [UI shell](https://carbondesignsystem.com/components/ui-shell/usage) | consistent shell, header, side navigation, loading, error and notification regions |
| Commerce admin | [Shopify Polaris patterns](https://polaris.shopify.com/patterns) and [description lists](https://polaris.shopify.com/components/lists/description-list) | resource index, primary action placement, clear resource state, structured definitions |
| Product navigation | [GitHub Primer navigation](https://primer.style/product/ui-patterns/navigation) and [breadcrumbs](https://primer.style/product/components/breadcrumbs/accessibility) | orientation, minimal navigation, parent return path, `aria-current` |
| Accessibility | [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) | AA, reflow at 320 CSS px, focus visibility, status messages, accessible authentication, target size |
| Status messages | [WCAG 2.2 Understanding 4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) | results and errors must be announced without stealing focus |
| Accessibility engineering | [Primer accessibility](https://primer.style/accessibility/introduction) | keyboard model, unique links, meaningful labels, contrast, automated plus manual checkpoints |
| PWA | [web.dev PWA](https://web.dev/learn/pwa/getting-started), [install criteria](https://web.dev/articles/install-criteria), [update lifecycle](https://web.dev/learn/pwa/update) | installable manifest, custom offline page, incremental scope, update flow that does not block rendering |
| Performance | [web.dev Web Vitals](https://web.dev/articles/vitals) and [INP](https://web.dev/articles/inp) | LCP, INP, CLS measured in the field |

## 2. Current strengths

- `statusLine` and `market.template` provide a consistent honest-state vocabulary.
- Public pages use a shared `EndpointForm` and `data-states` model.
- Marketplace cart, checkout, wallet and escrow pages are session-aware and use real API clients.
- Bazaar list, detail and authenticated creation pages are implemented against the registered marketplace contract.
- WCAG 2.2 AA automated tests run against representative fa/en routes.
- Reflow, focus, skip-link and status regions have automated coverage.
- i18n parity and a provenance guard are enforced in CI.

## 3. Gap analysis against the reference models

| Gap | Reference baseline | Current state | Reason / consequence |
|---|---|---|---|
| Admin shell | Carbon UI shell, Polaris resource index, Primer navigation | one capability page and a deny-by-default layout | operators cannot orient, filter, scan or navigate an operational system |
| Admin tables | Carbon data table with toolbar, caption, pagination, selection and batch actions | no shared admin data-table surface | health, queues, users and translation records cannot be operated safely |
| Research workspace | workspace-first product pattern used by research and data platforms | index and layout render an unavailable state | no place to inspect runs, datasets, validation or provenance |
| System status | calm status hierarchy, health, dependencies, last check and recovery guidance | two route entries exist but no aggregate index | operators cannot determine whether the system is usable in one view |
| PWA update | install, offline and update lifecycle | service worker and offline shell work; update page remains unavailable | installed users cannot understand when an update is ready |
| Public trust | transparent methodology, immutable evidence, honest data status | most pages are honest but several capabilities are unavailable | project credibility depends on finishing provenance-backed public datasets |
| Manual accessibility | automated plus screen-reader, keyboard, zoom and cognitive review | strong automation, limited manual evidence | AA cannot be claimed from automated tests alone |
| Consistent help | WCAG 3.2.6 and a documented help location | no global help/support entry | users cannot find the same help path across pages |
| Bilingual research/data UX | documented source, unit, quality label and download | data cards show status/source but not uniform research metadata | external users cannot compare values responsibly |

## 4. Tier 0 pages to create now

These pages are essential for the platform to feel coherent and trustworthy:

1. `/[locale]/admin` — operational overview with live health, navigation and last-check state.
2. `/[locale]/admin/system/health` — service health matrix and failure detail.
3. `/[locale]/admin/jobs` — queue/job index; explicit unavailable if no registered endpoint.
4. `/[locale]/admin/localization/translations` — locale coverage and machine-translation status.
5. `/[locale]/admin/feature-flags` — capability/flag index without invented values.
6. `/[locale]/admin/security` — security audit entry; role-gated upstream.
7. `/[locale]/admin/content` — published-content index.
8. `/[locale]/admin/users` — user administration entry; role-gated upstream.
9. `/[locale]/admin/design-tokens` — real local token inventory and states.
10. `/[locale]/research` — research capability and evidence index.
11. `/[locale]/research/workspace/[experimentId]` — experiment workspace shell with provenance and unavailable state.
12. `/[locale]/system` — aggregate system health and recovery links.
13. `/[locale]/system/pwa-update` — service-worker update lifecycle UI.
14. `/[locale]/system/locale-fallback` — requested → English fallback explanation and live locale selector.
15. `/[locale]/help` — one consistent help/support location across pages.

## 5. Why these pages come first

- **Orientation:** Carbon, Polaris and Primer all treat persistent navigation and clear resource context as core product behavior.
- **Safe operation:** Carbon data tables require keyboard sorting, captions, distinct targets and predictable focus; these are prerequisites for admin pages.
- **Trust:** the marketplace and public data surfaces are only useful when their provenance and limitations remain visible.
- **Recovery:** system and PWA pages need one canonical place to explain degraded state, reconnect and update.
- **Accessibility:** the reference systems require consistent landmarks, headings, help, error recovery and status announcements, not only compliant colors.
- **Cost control:** these pages use shared layouts and data-state components, so later admin/research pages can be added without duplicating architecture.

## 6. Out of scope without a registered backend

- Invented queue, user, feature-flag or audit records.
- Synthetic data that can be mistaken for live evidence.
- Offline payment, escrow or order writes.
- New backend endpoints inside this frontend workstream.

## 7. Acceptance gates

- `pnpm -C apps/web quality`
- `pnpm -C apps/web build`
- Playwright route smoke for all new Tier 0 pages
- WCAG 2.2 AA automated run
- 14-locale parity
- `node scripts/check-verified-claims.mjs`
- No `MISSING_MESSAGE` in page smoke tests
- Every data-bearing page shows a real source or `unavailable`

## 8. Execution result — 2026-09-25

- All 15 Tier 0 pages in this document are implemented, plus the separate professional `/workspace` surface defined in `WORKSPACE_SECURITY_DESIGN.md`.
- Admin uses a persistent shell, real local token inventories and registered gateway capabilities; jobs, flags, security, users and content remain honest when the upstream contract is absent or broken.
- Research uses the actual science dataset, citation and Zenodo status endpoints; experiment capabilities remain `endpoint: null` and therefore unavailable.
- System aggregates live health, implements a real service-worker update lifecycle, documents the requested→English fallback chain and provides one help/support path.
- Site navigation exposes Help, mobile labels collapse without losing accessible names, and 320 CSS pixel reflow is enforced by Playwright.
- The final frontend gate passed 402 source files, 31 unit-test files / 220 tests, 14-locale parity, production build, 16 WCAG 2.2 AA routes, 10 Tier 0 smoke routes and 8 responsive routes.

Residual blockers are external: proposed professional roles are not yet issued by the gateway, admin user/content responses need backend datetime fixes, and deployment environments still require administrator access.

## Inventory note — 2026-09-26

- The 15 Tier 0 pages in section 4 are **physical routes** in `apps/web/src/app/[locale]`, and the `/workspace` surface in [`WORKSPACE_SECURITY_DESIGN.md`](WORKSPACE_SECURITY_DESIGN.md) adds 17 more. They are not a share of the declared 600 logical page paths, and creating them did not change that declared total. A logical path, a physical route, a catalog fallback, and a data-bearing page are four different counts; the definitions are in [`PAGE_CHECKLIST_600.md`](PAGE_CHECKLIST_600.md).
- The Tier 0 pages resolve their capability state from the shared domain registry, so a capability with `endpoint: null` renders `unavailable` by rule. That is the intended state and is recorded as `unavailable` in the checklist, not as a pass.
- Blocker B11 in [`PAGE_GATES.md`](PAGE_GATES.md) is open: none of the 82 physical routes outside the marketplace and public surfaces, which includes all 15 Tier 0 pages and the workspace surface, has a declared position in the logical catalogue.
- Nothing in this note changes a gap analysis, an acceptance gate, or a page status. The sections above stand as recorded on 2026-09-25.
