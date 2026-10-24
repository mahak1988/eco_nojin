# HYDROMA ARCHITECTURE DECISIONS

**Generated**: 2026-10-09  
**Purpose**: Record architecture decisions log (ADR) for HyDroMA

---

## ADR-001: Engine Gateway Facade Pattern

**Status**: ACCEPTED  
**Context**: Services were importing directly from `engine.hydroma` (125 violations, INV-003).  
**Decision**: Create `services/_gateway_facade.py` as the single approved access point. All scientific computation must go through this facade, which uses EngineGateway.execute().  
**Consequences**: 
- Services now have 0 direct imports to engine internals
- All computation results carry provenance
- New models must register in ModelRegistry to be accessible

---

## ADR-002: C++ Bridge Direct Loading

**Status**: ACCEPTED  
**Context**: No C++ compiler available to rebuild `.pyd`; pre-built binary loads from external path.  
**Decision**: Use `importlib.util.spec_from_file_location` to load `hydroma_core.cp312-win_amd64.pyd` directly. Scientific verification uses C++ symbols directly bypassing numpy dependency.  
**Consequences**:
- 61 C++ symbols verified working
- Facade returns graceful error for numpy-dependent full engine imports
- Scientific tests pass via direct bridge access

---

## ADR-003: Model Registry as Single Source of Truth

**Status**: ACCEPTED  
**Context**: Multiple model definitions scattered across engine codebase.  
**Decision**: Central `ModelRegistry` in `engine/models/registry.py` with 68 registered models. Gateway uses registry to validate model IDs before dispatch.  
**Consequences**:
- All model discovery goes through registry
- ModelSpec contains documentation, limitations, implementation status

---

## ADR-004: Evidence-First Architecture

**Status**: ACCEPTED  
**Context**: HYDROMA-MASTER.md requires evidence-provenance chain.  
**Decision**: Every computation through ScientificVerifier generates an Evidence item. EvidenceEngine collects and validates. Knowledge Engine consumes Facts derived from Evidence.  
**Consequences**:
- 5 evidence items collected during verification
- Full provenance chain from input to decision

---

## ADR-005: Decision Engine Separation

**Status**: ACCEPTED  
**Context**: HYDROMA-MASTER.md §266-268 questions relationship between Decision Engine and Tasmimyar.  
**Decision**: 
- `engine/tasmimyar/` — DecisionEngine (computational logic)
- `services/tasmimyar/` — TasmimyarService (API wrapper, FastAPI router)  
The Decision Engine makes decisions; Tasmimyar service is the API gateway.  
**Consequences**:
- Clear separation: Tasmimyar depends on DecisionEngine, not vice versa
- No duplicate decision logic

---

## ADR-006: Virtual Environment Reuse

**Status**: ACCEPTED  
**Context**: Cannot install numpy/pytest in system Python (no PyPI access). A pre-existing venv at `D:\eco_nojin\.venv` has all required packages.  
**Decision**: Use the existing venv at `D:\eco_nojin\.venv` with PYTHONPATH=D:\HyDroMA;D:\eco_nojin.  
**Consequences**:
- 217 pytest tests execute successfully
- Environment is reproducible if venv is preserved

---

## ADR-007: PersistencePort as Interface

**Status**: ACCEPTED  
**Context**: HYDROMA-MASTER.md requires Persistence contract but full database backend not needed yet.  
**Decision**: Define `PersistencePort` ABC with `InMemoryPersistence` and `FileBackedPersistence` implementations. Database-backed implementation deferred.  
**Consequences**:
- Tests pass without external database
- Easy to swap storage backend later