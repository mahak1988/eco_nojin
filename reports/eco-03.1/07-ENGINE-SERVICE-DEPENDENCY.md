# ECO-03.1: Engine→Service Dependency — Report 07

## Complete audit of all services imports in engine/

---

## Methodology

Full repository scan for any import of `services` from within `engine/`:
- `from services...`
- `import services...`

All occurrences in `engine/` code examined.

---

## Production Code Results

**Command**: `grep -rn "from services\|import services" engine/ --include="*.py"`

### Matches Found: 0 in production code

The only match was in a **test file**:

| File | Line | Import | Classification |
|------|------|--------|----------------|
| `engine/strict_tests/test_s12_table_registration.py` | 234 | `import services.models.land_models` | TEST_ONLY |
| `engine/strict_tests/test_s12_table_registration.py` | 331 | `import services.models.land_models` | TEST_ONLY |

### B-001 Status: FIXED_AND_VERIFIED

The `engine/hydroma/generative_ai/` module (which contained the violation) has been:
1. **Removed** from `engine/hydroma/`
2. **Moved** to `services/ai/generative_ai/`
3. **Verified** that no production code in `engine/` imports from `services/`

**Verification command**:
```powershell
grep -rn "from services\|import services" engine/ --include="*.py" | grep -v "test_"
```
Result: No matches (excluding test files).

**Import test**:
```powershell
python -c "import engine; print('OK')"
```
Result: OK (no ImportError, no circular dependency)

---

## Test Code Results

| File | Line | Import | Classification | Reason |
|------|------|--------|----------------|--------|
| `engine/strict_tests/test_s12_table_registration.py` | 234 | `import services.models.land_models` | TEST_ONLY | Test verifies model registration |
| `engine/strict_tests/test_s12_table_registration.py` | 331 | `import services.models.land_models` | TEST_ONLY | Test verifies model registration |

**Assessment**: Test-only imports are acceptable for verification purposes. These do not violate the architectural invariant since they are not part of production code paths.

---

## Engine→Service Boundary

| Direction | Allowed? | Evidence |
|-----------|---------|----------|
| Engine → Services | NO | 0 production imports (violation FIXED) |
| Services → Engine | YES | 100+ imports found (services depend on engine) |
| AI → Engine internals | NO | 0 imports found (isolation verified) |

---

## Conclusion

**B-001 (Engine→Services violation)**: FIXED_AND_VERIFIED

- The `generative_ai` module has been removed from the engine
- No production code in `engine/` imports from `services/`
- The only `services` imports in `engine/` are in test files, which is acceptable

**Remaining concern**: The service→engine dependency (100+ imports) is **by design** — services depend on the engine, not vice versa. This is the correct dependency direction in hexagonal/clean architecture.

---

*Report generated: 2026-10-08*
*Status: B-001 FIXED_AND_VERIFIED*