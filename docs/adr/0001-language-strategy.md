# ADR 0001: Language strategy

- **Status:** Accepted
- **Date:** 2026-09-25
- **Scope:** Runtime and numerical-kernel boundaries

## Context

Eco Nojin combines scientific computation, API orchestration, offline-capable clients, and performance-sensitive kernels. A single language would make ownership, testing, and deployment less clear. `AGENTS.md` establishes Python, Go, Rust, TypeScript, and C++20 as the project strategy; this ADR makes the boundary explicit.

## Decision

| Language | Owns | Boundary |
|---|---|---|
| Python | Business logic, AI/ML, scientific orchestration, and model services | Calls the C++/Rust kernels through explicit interfaces. |
| Go | Gateway, event-bus, webhook, and gRPC concurrency concerns | Owns network-facing service behavior, not scientific numerics. |
| Rust | Offline sync, geospatial utilities, and memory-safe hot paths | Exchanges versioned, typed data at service boundaries. |
| TypeScript | Next.js frontend, BFF route handlers, shared types, and edge functions | Consumes one API contract and never re-implements model logic. |
| C++20 | Performance-critical numerical kernels through the existing pybind11 bridge | Remains independently testable with CTest and parity tests. |

## Consequences

- Each module has a clear owner, test command, and deployment unit.
- Cross-language boundaries require schemas, versioning, and error mapping.
- Scientific changes include numerical regression and provenance evidence.
- A new language or runtime boundary requires an ADR and a migration/rollback plan.
- The current release integration branch is `main`; the absence of `develop` is a repository-state fact, not a new language dependency.

## Boundaries

This ADR does not grant access to any environment, publish a package, or restore a deleted document. Secrets and environment values remain in the configured settings source.
