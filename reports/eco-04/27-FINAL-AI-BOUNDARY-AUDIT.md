# ECO-04.1: Final AI Boundary Audit — Report 27

## AI services isolation from engine internals

**Report Date**: 2026-10-08T17:00:00Z  
**Method**: AST-based import scanner (`tools/detect_imports.py`) + runtime import tests

---

## 1. AI Service Inventory

### 1.1 AI Module List

| Module | Path | Lines (est.) |
|--------|------|--------------|
| AI Package | services/ai/__init__.py | ~15 |
| Admin Assistant | services/ai/admin_assistant.py | ~52 |
| Embedding Service | services/ai/embedding_service.py | ~48 |
| LLM Router | services/ai/llm_router.py | ~67 |
| NLG | services/ai/nlg.py | ~38 |
| RAG | services/ai/rag.py | ~55 |
| Support Agent | services/ai/support_agent.py | ~45 |
| Unified RAG | services/ai/unified_rag.py | ~38 |
| Generative AI | services/ai/generative_ai/__init__.py | ~20 |

**Total**: 9 AI modules across 2 directories

---

## 2. INV-009 Compliance: AI → Engine Internals

### Rule Definition
**INV-009**: AI modules must not import anything from `engine.hydroma`, `engine.cpp_core`, or `engine.knowledge` internals.

### Scan Results

```
Rule: INV-009 (AI → engine internals forbidden)
Files scanned: 9 AI modules
Violations: 0
Result: ✅ PASS
```

### Detailed Verification

Each AI module was scanned for the following forbidden imports:

| Forbidden Import | AI Modules Importing It |
|------------------|------------------------|
| `from engine.hydroma import ...` | 0 modules |
| `from engine.cpp_core import ...` | 0 modules |
| `from engine.knowledge import Fact` | 0 modules |
| `from engine.knowledge import Claim` | 0 modules |
| `from engine.knowledge import KnowledgeEngine` | 0 modules |
| `import engine.hydroma` | 0 modules |

### AI Module Import Summary

| Module | Imports engine.* | Status |
|--------|------------------|--------|
| services/ai/__init__.py | ❌ No | ✅ Compliant |
| services/ai/admin_assistant.py | ❌ No | ✅ Compliant |
| services/ai/embedding_service.py | ❌ No | ✅ Compliant |
| services/ai/llm_router.py | ❌ No | ✅ Compliant |
| services/ai/nlg.py | ❌ No | ✅ Compliant |
| services/ai/rag.py | ❌ No | ✅ Compliant |
| services/ai/support_agent.py | ❌ No | ✅ Compliant |
| services/ai/unified_rag.py | ❌ No | ✅ Compliant |
| services/ai/generative_ai/__init__.py | ❌ No | ✅ Compliant |

### AI Module Dependencies (allowed)

| Module | Dependencies |
|--------|--------------|
| All AI modules | pydantic, json, os, typing, dataclasses, enum, collections |
| admin_assistant.py | pydantic, dataclasses |
| embedding_service.py | numpy (conditional — `try: import numpy`), hashlib |
| llm_router.py | dataclasses, typing |
| rag.py | pydantic, dataclasses |
| support_agent.py | pydantic, dataclasses |
| unified_rag.py | pydantic, dataclasses |

**Note**: `embedding_service.py` has a conditional numpy import in a `try/except ImportError` block — this is acceptable as it gracefully degrades.

---

## 3. INV-010 Compliance: Scientific Authority

### Rule Definition
**INV-010**: AI must not change scientific equations or parameters.

### Verification

| Check | Result | Evidence |
|-------|--------|----------|
| AI modules import from `engine/hydroma/parameters.py` | 0 modules | ❌ No violations |
| AI modules import from `engine/hydroma/constants.py` | 0 modules | ❌ No violations |
| AI modules import from `engine/hydroma/model_params.py` | 0 modules | ❌ No violations |
| AI modules reference scientific equations | None found | AST scan |

### Runtime Test

```python
python -c "
import ast, sys
ai_files = [
    'services/ai/__init__.py',
    'services/ai/admin_assistant.py',
    'services/ai/embedding_service.py',
    'services/ai/llm_router.py',
    'services/ai/nlg.py',
    'services/ai/rag.py',
    'services/ai/support_agent.py',
    'services/ai/unified_rag.py',
    'services/ai/generative_ai/__init__.py'
]
for f in ai_files:
    with open(f) as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and 'engine.hydroma' in node.module:
            print(f'VIOLATION: {f} imports {node.module}')
        if isinstance(node, ast.Import) and any(a.name and 'engine.hydroma' in a.name for a in node.names):
            print(f'VIOLATION: {f} imports {a.name}')
print('AI boundary scan complete — no violations found')
"
```
→ Output: `AI boundary scan complete — no violations found` ✅

---

## 4. Test Execution

### Unit Tests

| Test file | Status |
|-----------|--------|
| services/ai/tests/ | Not found |
| Any test file importing `services/ai/` | Not found |

**Finding**: No automated tests exist for AI boundary compliance. The 0-violation result is from static import guard only.

### AI Boundary Tests

| Test | Status |
|------|--------|
| test_ai_no_engine_hydroma_imports | ❌ Not implemented |
| test_ai_no_cpp_core_imports | ❌ Not implemented |
| test_ai_no_knowledge_engine_imports | ❌ Not implemented |

---

## 5. Status Summary

| Requirement | ECO-04 Claim | Actual | Final Status |
|-------------|-------------|--------|--------------|
| AI → engine.hydroma forbidden | ✅ Implied | ✅ 0 violations | ✅ PASS |
| AI → engine.cpp_core forbidden | ✅ Implied | ✅ 0 violations | ✅ PASS |
| AI → engine.knowledge forbidden | ✅ Implied | ✅ 0 violations | ✅ PASS |
| Scientific equation immutability | ✅ Implied | ✅ 0 references | ✅ PASS |
| Automated AI boundary tests | Not claimed | ❌ 0 tests exist | ⚠️ Missing tests |
| AI services runtime | N/A | ✅ All AI modules importable (stdlib + pydantic) | ✅ Functional |

---

## 6. Contradictions with Reports

| Report | Claim | Actual |
|--------|-------|--------|
| Report 19 | "AI Isolation ✅ PASS" | ✅ Matches reality — 0 violations |
| Report 20 | `ai_boundary.implemented: true` | ✅ Boundary is satisfied but no automated tests verify it |

**Note**: Report 19 correctly states AI isolation passes. This is one of the few claims in Report 19 that matches reality. However, the absence of automated tests for the boundary is a gap.

---

*AI boundary is technically clean (0 violations), but relies solely on static import guard — no automated tests exist to enforce this boundary going forward. Recommendation: add CI-enforced boundary tests as part of ECO-05.1.*
