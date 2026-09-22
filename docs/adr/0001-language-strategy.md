# ADR 0001: Multi-Language Strategy

## Status
Accepted

## Context
Eco Nojin is a complex platform requiring:
- High-performance numerical computing (hydrology, erosion, carbon modeling)
- Real-time event streaming (SSE, WebSocket, CRDT collaboration)
- Offline-first mobile capabilities (PWA, IndexedDB, background sync)
- AI/ML pipeline (RAG, embeddings, multi-agent orchestration)
- Type-safe frontend with 14 languages and RTL support
- Event-driven microservices architecture
- Scientific rigor with peer-reviewed methodologies

A single language cannot optimally address all these requirements.

## Decision
Adopt a **multi-language strategy** with clear domain boundaries:

| Language | Domain | Rationale |
|----------|--------|-----------|
| **Python** | Business logic, AI/ML, scientific computing, orchestration | Rich ecosystem (NumPy, Pandas, SciPy, PyTorch, LangChain), team expertise, rapid prototyping |
| **Go** | API Gateway, Event Bus, Webhooks, gRPC Gateway | Native concurrency, fast startup, single binary, excellent for network services |
| **Rust** | Offline sync engine, Geospatial processing, High-perf kernels | Memory safety, zero-cost abstractions, WASM for frontend, no GC pauses |
| **TypeScript** | Frontend, Shared types, Edge functions | Type safety across stack, shared schemas (OpenAPI → TS), excellent tooling |
| **C++20** | Numerical kernels (existing via pybind11) | Performance-critical numerics, existing investment |

## Consequences

### Positive
- **Right tool for each job** — Optimal performance per domain
- **Team specialization** — Engineers can deepen expertise
- **Hiring flexibility** — Can recruit from multiple language communities
- **Performance where needed** — Rust/Go for hot paths, Python for productivity
- **Type safety across boundary** — OpenAPI → TypeScript codegen

### Negative
- **Increased complexity** — Multiple build systems, deployment artifacts
- **Cross-language debugging** — Harder to trace issues across boundaries
- **Operational overhead** — Multiple runtimes, monitoring, CI/CD pipelines
- **Team coordination** — Need clear interfaces, contract testing
- **Learning curve** — Team needs proficiency in multiple languages

### Risks
- **Interface drift** — Python ↔ Go ↔ Rust contracts may diverge
- **Build complexity** — Multi-language CI/CD pipelines
- **Debugging difficulty** — Distributed tracing required
- **Team fragmentation** — Knowledge silos per language

## Mitigations
- **Contract testing** — schemathesis (OpenAPI) + Pact (consumer-driven) for all service boundaries
- **Schema registry** — Avro/Protobuf with compatibility checks (BACKWARD)
- **Distributed tracing** — OpenTelemetry across all services
- **Shared types** — OpenAPI → TypeScript codegen, Python Pydantic models
- **Documentation** — ADRs for all cross-language decisions
- **Pair programming** — Cross-language pairing during onboarding

## Implementation Plan
1. **Phase 1 (Month 1-2)**: Python monolith with FastAPI, introduce Go for API Gateway
2. **Phase 2 (Month 3-4)**: Go Event Bus (NATS), Go Webhook Dispatcher
3. **Phase 3 (Month 4-6)**: Rust Offline Sync Engine, Rust Geospatial Engine
4. **Phase 4 (Month 6-8)**: Go gRPC Gateway, TypeScript shared types via codegen
5. **Ongoing**: Contract testing for all boundaries, distributed tracing

## Alternatives Considered
1. **Python-only** — Simpler ops, but cannot meet performance requirements for real-time/offline/geospatial
2. **Go-only** — Great for services, poor ecosystem for scientific computing/AI
3. **Rust-only** — Maximum performance, but steep learning curve, slow development velocity
4. **TypeScript-only (Node.js)** — Good for web, poor for numerical computing

## Related
- ADR 0002: Event-Driven Architecture with NATS JetStream
- ADR 0003: Offline-First Architecture with CRDT
- ADR 0004: API Gateway Pattern with Go

## References
- [Google's Multi-Language Guidance](https://google.github.io/styleguide/)
- [Uber's Go + Python Architecture](https://eng.uber.com/)
- [Discord's Rust + Go Migration](https://discord.com/blog/)