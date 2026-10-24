# ECO-02: Boundary Violation Analysis

## ECO-LEGACY-001 and Import Guard

---

## Source Evidence
- ECO-01/22-LEGACY-DEPENDENCY-STRATEGY.md (ECO-LEGACY-001 critical)
- ECO-01/24-UNKNOWN-AND-CONFLICTS.md
- reports/engine-services/DEPENDENCY-MAP.md (4-layer visual)

---

## Critical Violation: ECO-LEGACY-001

### The Problem
Per ECO-01/22: Services must NOT import from `engine/` package. This creates tight coupling and breaks the layered architecture.

### Current Violation Pattern
```python
# VIOLATION (in services/):
from hydroma.scientific.et import compute_penman_monteith

# CORRECT path:
# services/ → Domain Service → Engine Gateway → Scientific Engine
```

### Impact
- Prevents engine as standalone library
- Creates circular dependencies
- Makes testing difficult
- Breaks Evidence Engine provenance chain

---

## Boundary Rules

### Rule 1: Import Direction
```
ALLOWED: services/ → engine/       (for computation)
VIOLATION: engine/ → services/     (must be removed)
ALLOWED: ai/ → evidence/           (through evidence chain only)
VIOLATION: ai/ → engine/           (direct AI to scientific core)
```

### Rule 2: Data Flow Direction
```
Product Experience
    → Application Orchestration
    → Decision (Tasmimyar)
    → Evidence Engine (provenance)
    → Domain Services (Hydroma)
    → Engine Gateway (C++ boundary)
    → Scientific Engine (computation)
    → C++ Kernels (numerical)
```

### Rule 3: AI Isolation
```
AI Layer (RESEARCH)
    → Evidence Engine (validated data only)
    → Decision Engine (policy evaluation)
    ↛ Scientific Engine (direct access blocked)
```

---

## Import Guard Implementation

### Python Guard (recommended)
```python
# In services/, add import guard
import sys
import os

# Prevent engine/ imports from services/
def _guard_imports():
    """Block forbidden imports per ECO-LEGACY-001"""
    frame = sys._getframe(1)
    module = frame.f_globals.get('__name__', '')
    if 'services' in module:
        # Log and block
        raise ImportError(f"ECO-LEGACY-001: Services cannot import from engine")

# Applied at module load
_guard_imports()
```

### AST-based Detection Script
```python
# detect_violations.py
import ast
import os

forbidden_patterns = [
    ('services', 'engine'),
    ('ai', 'engine'),
]

def check_file(path):
    with open(path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:  # Relative import
                continue
            for pattern_from, pattern_to in forbidden_patterns:
                # Check if importing pattern_to from pattern_from
```

---

## Dependency Map (4-Layer)

From reports/engine-services/DEPENDENCY-MAP.md:

```
Layer 4: Product Experience (UI, reporting)
    ↑
Layer 3: Application Services (orchestration, API)
    ↑
Layer 2: Domain Services (Hydroma, science interfaces)
    ↑
Layer 1: Engine & Infrastructure (C++ kernels, database)
```

### Violations in Current Code
| File | Violation | Severity |
|------|-----------|----------|
| services/et_service.py | imports from engine.hydroma.scientific | HIGH |
| services/policy.py | imports from engine.models | HIGH |
| ai/recommendation.py | imports from engine.hydroma | CRITICAL |
| services/consolidated.py | imports from services.et_service | MEDIUM |

---

## Remediation Plan

### Phase 1: Detection (P0)
1. Run AST-based scanner on all Python files
2. Catalog all violations
3. Classify by severity

### Phase 2: Blocking (P0)
1. Add import guards in services/
2. Add import guards in ai/
3. CI/CD check blocks new violations

### Phase 3: Remediation (P1)
1. Redirect engine/ imports through Engine Gateway
2. Move AI to Evidence Engine integration only
3. Verify no new violations

---

## Verification Commands

```bash
# Detect violations
python tools/detect_imports.py --root services/ --forbidden engine/

# Verify boundary
python tools/check_boundary.py --layer services --cannot-import-from engine

# AI isolation check
python tools/check_boundary.py --layer ai --cannot-import-from engine
```

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/22*