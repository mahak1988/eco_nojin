# Deployment and release

**Status:** Deployment is intentionally disabled until the green quality and decision gates are complete. This document does not claim that a cluster, environment, package registry, or administrative account is available.

## Current source-of-truth decisions

- The current remote is GitHub only. No second remote or alternative hosting control plane is assumed.
- `main` is the integration branch because `develop` does not exist in the current remote.
- Work starts on a feature branch and is proposed through a pull request to `main`.
- Branch, pull-request, and manual workflow builds are build/test evidence only. They must not publish a package or deploy an environment.
- Deployment stays off until required checks are green and an explicit deployment decision gate is recorded.
- A release is created only from an immutable semantic-version tag named `vX.Y.Z`.
- The release build happens once. Promotion uses that exact artifact or image digest; it does not rebuild for another environment.

These decisions are captured in [`../adr/0005-release-governance.md`](../adr/0005-release-governance.md).

## Release sequence

1. Create a feature branch from `main` and make the smallest reviewable change.
2. Open a pull request to `main`; run the required checks from [`TESTING.md`](TESTING.md).
3. Resolve review findings and verify the decision gate. Do not use a failed or skipped check as a waiver.
4. Merge only the reviewed commit, then record the exact commit and build provenance.
5. Build once from that commit and retain the immutable artifact and digest.
6. Create the immutable `vX.Y.Z` tag. Do not move, rewrite, or reuse a release tag.
7. Promote the already-built artifact through staging and, after a separate decision, production. Promotion must not invoke a second build.
8. Record the tag, commit, checks, digest, and promotion result as release evidence.

The C++ workflow listens for `v*` tags. Its publishing job is restricted to `refs/tags/v*`; ordinary branch and manual-dispatch runs remain non-publishing.

## Gates and rollback

A promotion is blocked when a check, artifact verification, digest comparison, or environment decision is missing. A failed candidate is not patched in place. Select a previously verified immutable artifact for rollback, or create a new version tag after the fix; never rebuild a released version under the same tag.

Deployment configuration may be prepared locally, but preparation is not activation. Secrets, registry credentials, and environment values remain outside the repository.

## Required frontend secret contract

The Kubernetes frontend Deployment references a non-committed `frontend-secrets` Secret:

- `REDIS_URL`: Redis connection URL for the shared session store

These keys must be supplied by External Secrets Operator, a sealed secret, or an equivalent cluster secret mechanism. A missing key intentionally keeps the pod in `CreateContainerConfigError` rather than starting without sessions or caching.

The Helm values `frontend.sessionSecret.existingSecret` and `existingSecretRedisUrlKey` allow the Redis Secret name and key to be overridden without putting values in Git.

## Ownership boundary

This document defines process and gates, not permissions. It grants no administrative access and makes no claim about access to an external environment.
