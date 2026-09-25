# ADR 0005: Release governance and promotion

- **Status:** Accepted
- **Date:** 2026-09-25
- **Scope:** Branching, CI, publishing, and deployment gates

## Context

The current repository has a GitHub-only remote, `main` as the available integration branch, no `develop` branch, and no proven green deployment/release baseline. Publishing from a normal branch push would make unreviewed or untested code releasable.

## Decision

- The current remote is GitHub only. Do not assume a second remote or an alternative CI/deployment control plane.
- Use `main` as the integration branch because `develop` does not exist.
- Start work on a feature branch and propose it through a pull request to `main`.
- Keep deployment disabled until the required checks are green and an explicit decision gate is recorded.
- Publish or release only from an immutable semantic-version tag `vX.Y.Z`. Do not move, rewrite, or reuse a release tag.
- Build once from the reviewed commit, retain the artifact and digest, and promote that exact build without rebuilding for another environment.
- Branch builds, pull-request builds, and manual-dispatch builds are test/evidence runs only and must not publish a package or deploy.

## Enforcement

The C++ workflow listens for `v*` tag pushes and restricts its publishing job to `refs/tags/v*`. The release validation accepts only the `vX.Y.Z` shape. Required tests, contract drift checks, security checks, artifact verification, and the decision gate must all be green before promotion.

## Consequences

- A release has one reviewable commit, one build identity, and an auditable promotion path.
- A failed candidate is not patched in place. Fix it through a new review and version tag.
- Rollback selects a previously verified immutable artifact or creates a new version; it does not rebuild a released tag.
- Environment configuration and secrets stay outside the repository. This ADR does not assert that any environment, registry, or administrative access exists.
