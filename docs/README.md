# Eco Nojin documentation

This directory is the new canonical documentation set. The deleted legacy documents are not restored; the required ADR paths below are newly authored replacements, and the remaining deleted files stay deleted. The repository-wide principles in [`AGENTS.md`](../AGENTS.md) remain the baseline; the Decision Freeze records the gates for this rollout.

## Status

- **Decision Freeze:** Wave 0 research and documentation baseline.
- **Application:** Next.js 15, React 19, and TypeScript in `apps/web`.
- **Scientific engine:** Python/HyDroMa with the C++20 core under `engine/cpp_core`.
- **Current integration branch:** `main`. A `develop` branch does not exist in the current remote; GitHub is the only configured remote, with no GitLab or other remote assumed.
- **Working model:** create a feature branch, open a pull request to `main`, and require the green decision gate before merge.
- **Deployment:** disabled until the required checks and the explicit deployment decision gate are green.
- **Release:** only an immutable `vX.Y.Z` semver tag, with one build and promotion of the same artifact without rebuilding.
- **Secrets:** values belong in the configured environment/settings source, never in this documentation or in a committed file.

## Canonical map

| Area | Document |
|---|---|
| Frontend boundaries and layers | [`frontend/ARCHITECTURE.md`](frontend/ARCHITECTURE.md) |
| Authentication and authorization | [`frontend/AUTH_AND_RBAC.md`](frontend/AUTH_AND_RBAC.md) |
| Internationalization and RTL | [`frontend/I18N_AND_RTL.md`](frontend/I18N_AND_RTL.md) |
| PWA and offline boundaries | [`frontend/PWA_AND_OFFLINE.md`](frontend/PWA_AND_OFFLINE.md) |
| Content truthfulness and demo migration | [`frontend/CONTENT_MIGRATION_MATRIX.md`](frontend/CONTENT_MIGRATION_MATRIX.md) |
| Quality gates and test strategy | [`frontend/TESTING.md`](frontend/TESTING.md) |
| Deployment and release runbook | [`frontend/DEPLOYMENT.md`](frontend/DEPLOYMENT.md) |
| Architecture decisions | [`adr/0001-language-strategy.md`](adr/0001-language-strategy.md), [`adr/0002-auth-bff.md`](adr/0002-auth-bff.md), [`adr/0003-api-contract.md`](adr/0003-api-contract.md), [`adr/0004-pwa-local-first.md`](adr/0004-pwa-local-first.md), [`adr/0005-release-governance.md`](adr/0005-release-governance.md), [`adr/0006-observability-and-csp.md`](adr/0006-observability-and-csp.md) |

## Reading order

1. Read the Decision Freeze referenced by the ADR set before changing a boundary.
2. Read the relevant frontend guide and its ADR.
3. Run the smallest relevant test, then the full quality gate in [`frontend/TESTING.md`](frontend/TESTING.md).
4. Do not enable deployment or publishing until the release gates in [`frontend/DEPLOYMENT.md`](frontend/DEPLOYMENT.md) are satisfied.
