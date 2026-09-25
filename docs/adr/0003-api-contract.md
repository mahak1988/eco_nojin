# ADR 0003: One canonical API contract

- **Status:** Accepted
- **Date:** 2026-09-25
- **Scope:** Backend, BFF, and generated clients

## Context

The frontend, BFF, and external consumers need one stable meaning for each endpoint. Parallel hand-maintained schemas and mock DTOs can drift silently, especially for errors and status codes.

## Decision

- Maintain one canonical OpenAPI source; generated schema files are outputs, not independent contracts.
- Require a response model, explicit status codes, and a typed error envelope for every new endpoint.
- Generate the TypeScript client with Orval using `validate: true`, `clean: true`, and deterministic output.
- Make the BFF map backend responses to stable browser DTOs; it does not invent alternate endpoint semantics.
- Run generation and a diff/drift check in CI. A generated change is reviewed with its schema change.
- Contract tests cover success, validation failure, authorization failure, and compatibility-sensitive fields.

## Consequences

- There is one place to review an API change and one client generation path.
- Breaking changes require an explicit version/decision and migration plan.
- Unavailable or disabled endpoints are not kept alive with an undocumented mock contract.
- Frontend and backend changes remain independently testable while sharing the same schema.

## Prohibited shortcuts

- Maintaining two accepted OpenAPI schemas.
- Silently falling back through multiple incompatible payloads.
- Adding an endpoint without a response model or error envelope.
- Treating a frontend-only DTO as evidence that a backend endpoint exists.

This ADR records a contract decision only; it does not publish a package, deploy an environment, or grant access to one.
