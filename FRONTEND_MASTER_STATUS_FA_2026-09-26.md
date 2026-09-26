# Master status dashboard — Eco Nojin frontend

**Snapshot date:** 2026-09-26
**Repository:** `mahak1988/eco_nojin`
**Branch:** `main`
**Local HEAD:** this dashboard's commit (`90843e5` and its successors)
**Remote state:** `main` is ahead of `origin/main`; exact count must be re-read with `git rev-list --left-right --count origin/main...main` before push. No push has been performed.
**Working tree:** 144 unstaged/untracked changes remain, primarily owned by other workstreams.

This is the single handoff page for the current frontend programme. Detailed gates and page evidence are in [`docs/frontend/PAGE_CHECKLIST_600.md`](docs/frontend/PAGE_CHECKLIST_600.md).

## Executive status

| Area | State | Evidence |
|---|---|---|
| Build hygiene and CI | Green for the committed frontend scope | 402 source files, quality gate green |
| Auth/BFF | Implemented and committed | opaque Redis session, login/signup/logout/refresh, RBAC helper |
| PWA | Baseline implemented | Serwist, Dexie outbox, offline route |
| Public pages | 34 endpoint-bound; 28 honest unavailable/static | 62 physical public pages |
| Marketplace | 10 baseline + 14 Group-A routes live/capability; 22 mapping; 27 no endpoint | `3683725`, Group-A tests |
| Catalog | 600 logical entries declared and generated | 132 live, 59 capability, 255 planned, 154 unavailable |
| Admin | Tier-0 shell and 9 pages | capability registry, local token inventory |
| Research | Index and experiment workspace | live science endpoints; experiment writes unavailable |
| System/Help | Health, PWA update, fallback, help | system health aggregation and 37 catalog entries |
| Workspace | 16 professional routes | server deny-by-default; proposed roles not issued by gateway |
| Site URL | Resolved | shared config + `check-site-url` guard |
| GitHub governance | Runbook prepared, not executed | `docs/operations/GITHUB_RELEASE_RUNBOOK.md` |
| Backend/engine work | Owned by other workstream | not modified here |

## Page model and counts

The programme distinguishes four different counts:

1. **Physical route:** a `page.tsx` or `route.ts` on disk.
2. **Logical path:** a declared addressable product path.
3. **Catalog fallback:** a logical path resolved by a catch-all route.
4. **Data-bearing capability:** a request bound to an endpoint in `openapi.json`.

Current measured inventory:

- 218 physical `page.tsx` files.
- 216 routable physical pages plus root/not-found.
- 74 physical Marketplace pages.
- 62 physical Public pages.
- 17 physical Workspace pages.
- 444 declared Marketplace fallback paths.
- 600 logical catalog entries.
- 132 catalog entries marked `live` by rule.
- 59 marked `capability`.
- 255 marked `planned`.
- 154 marked `unavailable`.
- 191 catalog entries are indexable under the catalog rule.

The sum `218 + 444 = 662` is intentionally not presented as 600. The join rule and 82-route coverage reconciliation are tracked as `R-1`, `R-2` and `R-3` in the checklist.

## Frontend commits ready for review

```text
2b497b0  Wave 0: build hygiene, CI, OpenAPI and typed client
758b45e  Auth/BFF, domain routes, PWA, Design System and truthful content
e98d706  Refresh rotation, revoke and canonical OpenAPI
16b32ab  Dockerfile and Kubernetes/Helm frontend base
5088ef5  Main-branch release policy and quality gates
cbd7bd8  Canonical docs replacing legacy reports
2177450  Final integration status
21673b7  Marketplace and 62 Public pages bound to live contracts
ee0a363  Live page integration documentation
3c1d641  Admin, Research, System and Workspace surfaces
4e0ee59  Tier 0 completion status
d81c34a  Shared canonical site URL and placeholder guard
3683725  Marketplace Group A orphan routes
```

## Validation history

The following gates were run during the programme:

- `pnpm -C apps/web quality`
- `pnpm -C apps/web type-check`
- `pnpm -C apps/web build`
- `pnpm check:site-url`
- `node scripts/check-verified-claims.mjs`
- Playwright i18n, a11y, offline, auth, security, page, marketplace, Tier 0 and responsive suites.

Last recorded aggregate results before the final catalog work:

- 402 source files
- 225 unit tests in 32 files
- 14-locale parity
- 67 Playwright route tests
- 16 WCAG 2.2 AA routes
- 10 Tier 0 smoke routes
- 8 responsive 320px routes
- zero unsupported verified claims
- zero Site URL placeholder reads

## Agents

All Agent Manager sessions created for the current wave were stopped at the user's request:

- Marketplace Group B worktree: stopped.
- Public/Trust capability worktree: stopped.
- Release Audit worktree: stopped.

The worktree sessions were removed from Agent Manager. Any partial worktree output is not part of `main` until explicitly reviewed and merged.

## Open blockers

| ID | Blocker | Owner | State |
|---|---|---|---|
| B1 | Marketplace orders endpoints lack explicit auth in the contract | `marketplace-api` / security | open |
| B2 | Wallet endpoints accept arbitrary user id without auth | `wallet-api` / security | open |
| B3 | Two escrow models read different tables | `payments-api` | open |
| B4 | Payment gateway credentials are not in the repository | `platform-operations` | open |
| B5 | Production `REDIS_URL` cluster secret required | `platform-operations` | open |
| B6 | LMS router is not mounted | `platform-web` | open |
| B7 | Legal slugs require published content | `content-web` | open |
| B8 | No benchmark result store | `science-web` | open |
| B9 | Site URL placeholder | resolved by `d81c34a` | closed |
| B10 | Per-route ISR decision still needed for some public pages | `platform-web` | open |
| B11 | 600 catalog join rule and 82-route coverage not reconciled | `platform-web` | open |
| R-1 | 218 + 444 = 662 versus 600 | catalog owner | open |
| R-2 | 74th Marketplace page needs a bucket assignment | catalog owner | open |
| R-3 | 82 non-marketplace/public physical routes need coverage status | catalog owner | open |
| R-4 | `live-partial` versus `capability` mapping needs to be written | docs owner | open |

## Safe publishing procedure

Do not run `git add .` in the shared worktree. To publish only reviewed commits:

```powershell
git fetch origin
git rev-list --left-right --count origin/main...main
git diff --check origin/main..HEAD
git push origin main
```

To publish a new reviewed batch, stage explicit paths, run the required gates, commit with a descriptive message, and update the execution log in `PAGE_CHECKLIST_600.md`.

## Next action

The next single owner must update `docs/frontend/PAGE_CHECKLIST_600.md` with the catalog result, then run the final quality/build/E2E suite and prepare an explicit staging manifest. No automatic push or broad `git add .` is permitted.
