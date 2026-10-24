# HyDroMA Phase A: Knowledge Engine Implementation Report

**Generated**: 2026-10-09
**Status**: IMPLEMENTED — Knowledge Engine expanded + Persistence Port complete

---

## 1. Summary

Phase A of the HyDroMA Knowledge Engine implements structured knowledge
representation with forward-chaining inference, provenance tracking, and a
pluggable persistence port. The Evidence Engine is integrated so that
`EvidenceEngine.to_fact()` asserts Facts directly into the `KnowledgeEngine`.

---

## 2. Knowledge Engine (`engine/knowledge/__init__.py`)

### 2.1 `Fact` dataclass

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Stable identifier |
| `statement` | `str` | Human-readable knowledge claim |
| `source_id` | `str` | Evidence source identifier |
| `confidence` | `float` | Calibration confidence `[0, 1]` |
| `timestamp` | `datetime` | Assertion time |
| `provenance_chain` | `list[str]` | Ordered chain of fact IDs / source IDs |
| `metadata` | `dict[str, Any]` | Additional context |

`assert_fact()` seeds `provenance_chain` with `[source_id]` when it is empty,
ensuring every Fact has a traceable origin.

### 2.2 `Rule` dataclass (new)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Stable rule identifier |
| `premise` | `list[str]` | Statement patterns or fact IDs to match |
| `conclusion` | `str` | Statement of the derived Fact |
| `confidence_boost` | `float` | Multiplicative confidence boost |
| `metadata` | `dict[str, Any]` | Rule author, references, etc. |

### 2.3 `KnowledgeEngine` class

| Method | Signature | Description |
|--------|-----------|-------------|
| `assert_fact` | `(Fact) -> None` | Register Fact; seed provenance chain |
| `register_fact` | `(Fact) -> None` | Backward-compatible alias → `assert_fact` |
| `add_rule` | `(Rule) -> None` | Register an inference rule |
| `query_by_source` | `(source_id: str) -> list[Fact]` | Filter by `source_id` |
| `query_by_statement` | `(pattern: str) -> list[Fact]` | Case-insensitive substring match |
| `derive` | `() -> list[Fact]` | Forward-chaining inference to fixpoint |
| `get_provenance_chain` | `(fact_id: str) -> list[str]` | Return provenance chain for a Fact |
| `get_fact` | `(fact_id: str) -> Optional[Fact]` | Retrieve by ID |
| `get_claim` | `(claim_id: str) -> Optional[Claim]` | Retrieve claim by ID |
| `all_facts` | `() -> list[Fact]` | All registered facts |
| `all_claims` | `() -> list[Claim]` | All registered claims |

### 2.4 Forward-chaining derivation (`derive()`)

1. For each registered `Rule`, check if every premise entry matches an existing
   Fact — by exact fact-ID match or case-insensitive statement substring.
2. If all premises match, derive a new `Fact` whose `confidence` is
   `min(premise confidences) × (1 + confidence_boost)`, clamped to `[0, 1]`.
3. The derived Fact's `provenance_chain` = premise fact IDs + rule ID.
4. Repeat until no new Facts are produced (fixpoint).
5. Returns the list of all Facts derived across iterations.

A conclusion already present in the knowledge base is not re-derived.

### 2.5 Provenance (`get_provenance_chain`)

- **Asserted facts**: returns `[source_id]` (or the explicit chain if set).
- **Derived facts**: returns premise fact IDs followed by the rule ID.
- **Unknown IDs**: returns `[]`.

### 2.6 EvidenceEngine integration (`engine/evidence/__init__.py`)

`EvidenceEngine.__init__` now accepts an optional `knowledge_engine` parameter.
`to_fact()` accepts an optional per-call `knowledge_engine` argument. When a
KnowledgeEngine is available, `to_fact()` calls `engine.assert_fact(fact)` so
the generated Fact is immediately registered in the knowledge base with its
provenance chain populated from `Evidence.provenance`.

The `EngineGateway` (Section 3 below) wires the two engines together by
default.

### 2.7 Backward compatibility

- `register_fact` delegates to `assert_fact`.
- `register_claim`, `get_fact`, `get_claim`, `all_facts`, `all_claims`,
  `evaluate_claim` are unchanged.
- `Claim`, `ClaimStatus`, and `_aggregate_confidence` are unchanged.

---

## 3. Engine Gateway wiring (`engine/gateway/__init__.py`)

The `EngineGateway.__init__` was reordered so that the KnowledgeEngine is
created/injected **before** the EvidenceEngine. When both are auto-created,
the KnowledgeEngine reference is passed to the EvidenceEngine, enabling
`to_fact()` to assert Facts automatically.

---

## 4. Persistence Port (`engine/ports/`)

### 4.1 `PersistencePort` Protocol (`engine/ports/persistence.py`)

The existing `PersistencePort` Protocol (DB connections: `get_duckdb`,
`get_sqlite`, pooling) was extended with domain-persistence methods:

| Method | Signature | Description |
|--------|-----------|-------------|
| `save_evidence` | `(Evidence) -> str` | Persist Evidence, return ID |
| `load_evidence` | `(id: str) -> Evidence \| None` | Load by ID |
| `save_fact` | `(Fact) -> str` | Persist Fact, return ID |
| `load_fact` | `(id: str) -> Fact \| None` | Load by ID |
| `save_decision` | `(Decision) -> str` | Persist Decision, return ID |
| `load_decision` | `(id: str) -> Decision \| None` | Load by ID |
| `list_evidence` | `(filters: dict) -> list[Evidence]` | Filtered listing |

The `_MissingPersistencePort` stub now implements all domain methods
(raising the same `RuntimeError` as the DB methods).

### 4.2 `InMemoryPersistence` (`engine/ports/persistence_impl.py`)

Dict-backed, transient implementation. Stores Evidence, Fact, and Decision
in separate dicts keyed by primary ID. `list_evidence(filters)` matches
metadata key/value pairs. Database-connection methods (`get_duckdb`, etc.)
raise `NotImplementedError`.

### 4.3 `FileBackedPersistence` (`engine/ports/persistence_impl.py`)

JSON-file-backed, durable implementation. Stores all domain objects in a
single JSON document with `evidence`, `facts`, and `decisions` sections.
Uses custom serialization helpers:

- `datetime` → ISO 8601 string (and back).
- `str, Enum` members serialize as their string value.
- Nested dataclasses (`DecisionTrace`, `DecisionCriterion`) use
  `dataclasses.asdict()` / constructor reconstruction.
- Writes are atomic (write to `.tmp`, then `replace`).

Database-connection methods raise `NotImplementedError`.

### 4.4 Import-safe design

`persistence_impl.py` uses `TYPE_CHECKING` guards and lazy imports for
`Evidence`, `Fact`, and `Decision` types, avoiding circular dependencies
between `engine.ports` and the domain modules.

---

## 5. Test Suite (`engine/tests/test_knowledge_engine.py`)

**Command**:
```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
D:\eco_nojin\.venv\Scripts\python.exe -m pytest engine/tests/test_knowledge_engine.py -v
```

**Results**: 39 passed

| Test Class | Tests | Coverage |
|-----------|-------|----------|
| `TestFactAssertion` | 8 | `assert_fact`, `query_by_source`, `query_by_statement`, backward-compat |
| `TestForwardChaining` | 7 | `Rule`, `derive()`, confidence clamping, chained rules, fixpoint |
| `TestProvenanceChain` | 4 | `get_provenance_chain` for asserted, derived, unknown, fallback |
| `TestEvidenceEngineIntegration` | 3 | `to_fact()` → `assert_fact()` integration paths |
| `TestPersistenceRoundTrip` | 13 | `InMemoryPersistence` + `FileBackedPersistence` round-trips |
| `TestEndToEndIntegration` | 1 | Full pipeline via Gateway |

---

## 6. Files Changed

| File | Action |
|------|--------|
| `engine/knowledge/__init__.py` | Expanded: `Fact.provenance_chain`, `Rule`, `assert_fact`, `query_by_source`, `query_by_statement`, `add_rule`, `derive`, `get_provenance_chain`, `resolve_provenance` |
| `engine/evidence/__init__.py` | Modified: `to_fact()` now accepts `knowledge_engine` and calls `assert_fact()` |
| `engine/ports/persistence.py` | Extended: `PersistencePort` Protocol + `_MissingPersistencePort` gain domain methods |
| `engine/ports/persistence_impl.py` | **New**: `InMemoryPersistence`, `FileBackedPersistence` + serialization helpers |
| `engine/ports/__init__.py` | Updated: exports `InMemoryPersistence`, `FileBackedPersistence` |
| `engine/gateway/__init__.py` | Modified: KnowledgeEngine created before EvidenceEngine, wired together |
| `engine/tests/__init__.py` | **New**: test package marker |
| `engine/tests/test_knowledge_engine.py` | **New**: 39 tests |
| `reports/hydroma/HYDROMA_KNOWLEDGE_ENGINE.md` | **New**: this report |

---

## 7. Known Pre-existing Issues (not introduced by this work)

- `engine.hydroma.core.models` is not importable in a clean subprocess because
  `engine.hydroma.core.database` resolves `Base` via `PersistencePort.__getattr__`
  and the default stub (`_MissingPersistencePort`) does not implement
  `get_base`. This predates Phase A and is outside the scope of the Knowledge
  Engine / Persistence Port work.

---

## 8. Next Steps (Phase B)

- Wire `PersistencePort` domain methods to a database-backed adapter.
- Add probabilistic confidence aggregation to `evaluate_claim`.
- Implement rule authoring DSL with temporal/causal semantics.
- Integrate `Decision` persistence with services layer.
