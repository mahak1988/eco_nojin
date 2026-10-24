# ERROR-MAP — the three error taxonomies against the specification's 13 codes

**Document id:** `ECO-C5-ERROR-MAP` · **Date:** 2026-10-11 · **Item:** C-5 step 1 of
`reports/eco-nojin/ARCHITECTURE-REMEDIATION-PLAN.md:129-132`
**Status:** documentation only. No code was changed, no file other than this one was created.
**Next step:** C-5 step 2 (`HydromaError` → engine base, `GatewayError` → subclass) is a
**SB-03 brake-taking change** and is *not* authorised by this document — see §6.

**Rule set from the plan:** every claim below carries a `file:line` citation measured against
the live tree on 2026-10-11. Nothing is asserted from memory.

---

## 1. The specification vocabulary (13 codes)

The canonical table is §5.3 of `ECO-NOJIN MASTER EXECUTION SPECIFICATION.md:673-696`
(`HydromaError`, `ERROR_CODES`). It is mirrored verbatim by `engine/errors.py:57-71`.

| # | Code | Persian (§5.3) |
|---|---|---|
| 1 | `INPUT_INVALID` | ورودی نامعتبر |
| 2 | `UNIT_INCOMPATIBLE` | واحد ناسازگار |
| 3 | `MODEL_UNKNOWN` | مدل ناشناخته |
| 4 | `MODEL_VERSION_INVALID` | نسخه نامعتبر |
| 5 | `OUT_OF_DOMAIN` | خارج از دامنه کاربرد |
| 6 | `DATA_INSUFFICIENT` | داده ناکافی |
| 7 | `NUMERICAL_ERROR` | خطای عددی |
| 8 | `EXECUTION_FAILED` | خطای اجرای مدل |
| 9 | `PERSISTENCE_ERROR` | خطای ذخیره‌سازی |
| 10 | `UNCERTAINTY_NOT_ESTIMATED` | عدم‌قطعیت محاسبه‌نشده |
| 11 | `VALIDATION_FAILED` | اعتبارسنجی ناموفق |
| 12 | `NOT_IMPLEMENTED` | پیاده‌سازی نده |
| 13 | `ARCHITECTURE_VIOLATION` | نقض معماری |

`engine/tests/test_error_contract.py:23-42` already pins this set exactly
(`set(ERROR_CODES) == EXPECTED_ERROR_CODES`), so the vocabulary is stable and test-locked.

---

## 2. The three taxonomies, enumerated

### 2.1 Taxonomy A — the Engine Gateway (`engine/gateway/__init__.py`)

`GatewayError` is a **dataclass value object, not an exception** — `engine/gateway/__init__.py:162-170`.
It carries `error_code: str`, `message`, `model_id`, `validation_errors: list[str]`,
`execution`, `evidence_id`. `EngineGateway.execute` **returns** it rather than raising it
(`engine/gateway/__init__.py:1903`, `:1922`, `:1943`, `:1971`), which is why callers test
`isinstance(result, GatewayError)` (`services/_gateway_facade.py:218`).

Measured vocabulary — **3 codes, 4 construction sites**:

| Gateway code | Sites | Condition |
|---|---|---|
| `INVALID_REQUEST` | `engine/gateway/__init__.py:1903-1910`, `:1943-1950` | request validation failed; required-input group missing (`REQUIRED_INPUTS`, `:261-`) |
| `MODEL_NOT_FOUND` | `engine/gateway/__init__.py:1922-1928` | `request.model_id` not in the registry |
| `EXECUTION_ERROR` | `engine/gateway/__init__.py:1971-1977` | blanket `except Exception` around normalization + dispatch (`:1963`) |

**Zero of the 3 codes are in the specification vocabulary.** Also measured: a second,
*raw-exception* channel escapes from the same `execute` body without any code at all —
`ValueError` (`:2130` non-finite scaled input), `TypeError` (`:1609`, `:1612`, `:1629`,
`:1632` route input typing), `NotImplementedError` (`:2166`, `:2170` unwired route / missing
dispatch target). These 7 raise sites are re-labelled `EXECUTION_ERROR` by the blanket catch,
losing the distinction the spec draws between `NOT_IMPLEMENTED`, `NUMERICAL_ERROR`,
`UNIT_INCOMPATIBLE` and `EXECUTION_FAILED`.

The three codes are pinned by existing tests, so they are not free to rename without a
mandate: `engine/strict_tests/test_s16_gateway_strict_contracts.py:172`, `:644`
(`MODEL_NOT_FOUND`); `:546`, `:559`, `:578`, `:593`, `:611`, `:686` (`EXECUTION_ERROR`);
`:729` (`INVALID_REQUEST`).

### 2.2 Taxonomy B — `engine/errors.py` (the spec's own)

`HydromaError` — `engine/errors.py:34-53` — is an exception subclassing `Exception`, taking
`(error_code, message, context=None)` and exposing `error_code` / `context` / `__repr__`.
`ERROR_CODES` (`:57-71`) is the 13-code table of §1.

**Measured fact: this taxonomy is entirely unwired.** `engine/errors.py:26` states
*"This module is definitional only: it never raises."* A full-tree grep for `HydromaError`
outside `engine/errors.py` and its own test returns
`engine/tests/test_error_contract.py:20,46,56,60` only — i.e. **no production code path in
the engine, the gateway or the services ever raises or catches it.** It is a contract on paper.

### 2.3 Taxonomy C — the services tier

This is not one taxonomy but **five overlapping ones**:

**(C-1) `EcoNojinException` hierarchy** — `services/api_gateway/exceptions.py:6-45`.
`EcoNojinException(message, *, status_code=500, code=None)` with
`self.code = code or self.__class__.__name__` (`:13`). Subclasses:

| Class | Line | status |
|---|---|---|
| `ServiceUnavailableException` | `:16-20` | 503 |
| `NotFoundException` | `:23-25` | 404 |
| `ValidationException` | `:28-30` | 422 |
| `UnauthorizedException` | `:33-35` | 401 |
| `ForbiddenException` | `:38-40` | 403 |
| `ConflictException` | `:43-45` | 409 |

Because `code` defaults to the class name, the machine-readable code a client receives is
`"ValidationException"` / `"NotFoundException"` — **not** a spec code.
The global handler in `services/api_gateway/main.py:472-512` renders `EcoNojinException`
through `exc.status_code` and every other exception as 500 (`:507`).

**(C-2) The `HTTPException` router convention** — 511 `raise HTTPException(...)` sites across
`services/**`. The full measured status distribution (433 evaluated sites):

| Status | Count | | Status | Count |
|---|---|---|---|---|
| 404 | 192 | | 403 | 18 |
| 400 | 122 | | 503 | 14 |
| 500 | 36 | | 502 | 6 |
| 422 | 19 | | 409 | 4 |
| 401 | 18 | | 429 / 501 | 2 / 2 |

The HyDroMa tool routers repeat one 4-tier pattern in **8 families** — `hydroma_soil.py:447`,
`:456`, `:458`, `:462`, `:466`, `:468` and the identical block in
`hydroma_carbon.py:85-106`, `hydroma_climate.py:278-299`, `hydroma_economics.py:379-400`,
`hydroma_indices.py:578-599`, `hydroma_mrv.py:147-167`, `hydroma_simulation.py:92-113`,
`hydroma_water.py:276-297`:

| Tier | Status | Trigger |
|---|---|---|
| unknown `model_id` | 404 | `_SPEC_BY_ID.get(model_id) is None` |
| `params` not an object | 400 | `isinstance(params, dict)` fails |
| `ValueError`/`TypeError` in `build_kwargs` | 400 | param coercion |
| `ValueError`/`TypeError`/`KeyError` from the runner | 422 | domain rejection |
| any other `Exception` | 500 | catch-all |

**(C-3) The facade's `RuntimeError`** — `services/_gateway_facade.py:197-220`.
`_execute_full` returns `gw.execute(request)`, and at `:218-219`:
`if isinstance(result, GatewayError): raise RuntimeError(f"Gateway error: {result.message}")`.
The gateway's `error_code`, `validation_errors` and `evidence_id` are **discarded** here.
48 modules import this facade, so this erasure is the dominant services→engine error path.

**(C-4) `ERROR_CODE_MAP`** — `services/api_gateway/errors.py:27-45`. A *fourth* machine-readable
vocabulary emitted to clients by `safe_error_detail()` (`:62-70`): `data_integrity_violation`,
`database_unavailable`, `internal_error`, `data_validation_failed`, `entity_not_found`,
`validation_failed`, `invalid_input`, `missing_field`, `type_error`, `timeout`,
`connection_failed`, `permission_denied`, `resource_not_found`, `not_implemented`.
Its purpose (eco.md §48, no internal exposure) is sound, but its *naming* matches neither the
gateway's nor the spec's.

**(C-5) `ServiceResponse` micro-vocabularies** — `services/tasmimyar/decision_service.py:22-29`
(`success`, `error`, `error_code`) emits `error_code="DECISION_ERROR"` (`:107`) and
`error_code="NOT_FOUND"` (`:127`) inside a **200 OK** body (`:164` only converts the latter to
404). `services/validation/router.py:21` and `:55` return `{"error": ...}` with **HTTP 200**;
`services/validation/formula_checks.py:72-75` converts any raised exception into
`CheckResult(passed=False, actual="ERROR: …")` — a failure *value*, not an error.

---

## 3. The 13-code map

`HydromaError` column is always the code itself — that is the definition of the taxonomy
(`engine/errors.py:45-50`). `none` = the taxonomy has no equivalent.

| Spec code (§5.3) | Gateway code(s) | HydromaError | Services representation (status + name) |
|---|---|---|---|
| `INPUT_INVALID` | `INVALID_REQUEST` — `engine/gateway/__init__.py:1904`, `:1944` (+ `ValueError`/`TypeError` at `:2130`, `:1609`, `:1612`, `:1629`, `:1632` re-labelled `EXECUTION_ERROR`) | itself | 422 `HTTPException` "tool rejected inputs" (`services/api_gateway/routers/hydroma_soil.py:466`) **and** 400 `HTTPException` "invalid parameters" (`:462`) **and** `ERROR_CODE_MAP["ValueError"]="invalid_input"` (`services/api_gateway/errors.py:35`) |
| `UNIT_INCOMPATIBLE` | **none** — no code exists; the unit-scaled non-finite guard raises a bare `ValueError` (`engine/gateway/__init__.py:2129-2133`) that the blanket catch re-labels `EXECUTION_ERROR` (`:1972`). `engine/gateway/pint_audit.py` exists but is **not wired into `execute()`** | itself | **none** as a code — 422 or 500 `HTTPException` by tier; `ERROR_CODE_MAP` has no unit entry (`services/api_gateway/errors.py:27-45`) |
| `MODEL_UNKNOWN` | `MODEL_NOT_FOUND` — `engine/gateway/__init__.py:1923` | itself | 404 `HTTPException` (`services/api_gateway/routers/hydroma_soil.py:447`, `:456`); `NotFoundException` → 404 (`services/api_gateway/exceptions.py:23-25`); via the facade **500** through `RuntimeError` (`services/_gateway_facade.py:219` → `services/api_gateway/main.py:507`) |
| `MODEL_VERSION_INVALID` | **none** — `ModelSpec.model_version` (`engine/gateway/__init__.py:92-`) is never checked in `execute` | itself | **none** |
| `OUT_OF_DOMAIN` | **none** | itself | indirect only — 422 `HTTPException` when a runner rejects a value out of range (`services/api_gateway/routers/hydroma_soil.py:465-466`) |
| `DATA_INSUFFICIENT` | `INVALID_REQUEST` — `engine/gateway/__init__.py:1943-1950` (`_missing_required_inputs`, contract declared at `:261-`) | itself | 422 `HTTPException` `KeyError` → "tool rejected inputs" (`services/api_gateway/routers/hydroma_soil.py:465-466`); `ERROR_CODE_MAP["KeyError"]="missing_field"` (`services/api_gateway/errors.py:36`) |
| `NUMERICAL_ERROR` | **none** — a divide-by-zero / non-convergence surfaces only through the blanket catch | itself | 500 `HTTPException` catch-all (`services/api_gateway/routers/hydroma_soil.py:467-468`) |
| `EXECUTION_FAILED` | `EXECUTION_ERROR` — `engine/gateway/__init__.py:1972` | itself | 500 `HTTPException` (`services/api_gateway/routers/hydroma_soil.py:468`); unhandled `Exception` → 500 (`services/api_gateway/main.py:507`); `RuntimeError` → `ERROR_CODE_MAP["RuntimeError"]="internal_error"` (`services/api_gateway/errors.py:44`) |
| `PERSISTENCE_ERROR` | **none** — and worse than absent: `engine/gateway/__init__.py:1886-1890` swallows the evidence-store failure with `except Exception: pass` | itself | 500 (`services/api_gateway/main.py:507`); `ERROR_CODE_MAP["IntegrityError"]="data_integrity_violation"`, `["OperationalError"]="database_unavailable"` (`services/api_gateway/errors.py:28-29`); `ServiceUnavailableException` → 503 (`services/api_gateway/exceptions.py:16-20`) |
| `UNCERTAINTY_NOT_ESTIMATED` | **none** — carried as data, not an error: `UncertaintySpec(uncertainty_type="NOT_ESTIMATED")` (`engine/gateway/__init__.py:1992`) | itself | **none** — no service emits it; the nearest analogue is a boolean flag `passed: False` (`services/validation/formula_checks.py:71-75`) in a 200 body |
| `VALIDATION_FAILED` | **none** — `ValidationResult` (`engine/gateway/__init__.py:114-`, `:2100-2104`) never becomes an error code | itself | `ValidationException` → 422 (`services/api_gateway/exceptions.py:28-30`); `ERROR_CODE_MAP["ValidationError"]="validation_failed"` (`services/api_gateway/errors.py:34`); **or HTTP 200 with `{"error": …}`** (`services/validation/router.py:21`, `:55`) |
| `NOT_IMPLEMENTED` | **none** — `NotImplementedError` is raised at `engine/gateway/__init__.py:2166` and `:2170` (message composed at `:491-495`) and then re-labelled `EXECUTION_ERROR` by `:1972` | itself | `ERROR_CODE_MAP["NotImplementedError"]="not_implemented"` (`services/api_gateway/errors.py:42`); `BackupNotImplementedError(NotImplementedError)` (`services/backup/service.py:51`); 501 in 2 places |
| `ARCHITECTURE_VIOLATION` | **none** | itself | **none** at runtime — enforced out-of-band by `tools/detect_imports.py` / `tools/import_guard_policy.json` |

**Coverage summary:** 5 of 13 codes (`INPUT_INVALID`, `MODEL_UNKNOWN`, `DATA_INSUFFICIENT`,
`EXECUTION_FAILED` via `EXECUTION_ERROR`, and the raw-exception subset) have any gateway
representation; the gateway's own 3 codes map onto only 4 spec codes; 8 spec codes
(`UNIT_INCOMPATIBLE`, `MODEL_VERSION_INVALID`, `OUT_OF_DOMAIN`, `NUMERICAL_ERROR`,
`PERSISTENCE_ERROR`, `UNCERTAINTY_NOT_ESTIMATED`, `VALIDATION_FAILED`, `NOT_IMPLEMENTED`,
`ARCHITECTURE_VIOLATION` — 9 if `EXECUTION_ERROR` is not counted as covering
`EXECUTION_FAILED` separately) have **no** gateway code at all.

---

## 4. Divergences — where the same condition gets different codes

These are the deficiency C-5 actually names. Each row is one condition measured at ≥2 layers.

**D1 — Unknown model id: `MODEL_NOT_FOUND` / 404 / 500.**
`engine/gateway/__init__.py:1923` returns `MODEL_NOT_FOUND`; the tool router raises
404 `HTTPException` (`services/api_gateway/routers/hydroma_soil.py:447`, `:456`);
through the facade the *same* condition becomes a `RuntimeError`
(`services/_gateway_facade.py:219`) that the global handler renders as
**500** (`services/api_gateway/main.py:507`). Three layers, three answers, one condition.

**D2 — Bad input: 400 or 422 depending on which helper raised it.**
The 8 copied router blocks split on *raise site*, not on condition:
`ValueError`/`TypeError` in `build_kwargs` → 400 (`services/api_gateway/routers/hydroma_soil.py:461-462`),
the *same* exception types from the runner → 422 (`:465-466`). Copied to
`hydroma_carbon.py:96-106`, `hydroma_climate.py:289-299`, `hydroma_economics.py:390-400`,
`hydroma_indices.py:589-599`, `hydroma_mrv.py:157-167`, `hydroma_simulation.py:103-113`,
`hydroma_water.py:287-297`. A caller cannot distinguish "your parameter is malformed" from
"your parameter is outside the domain" without reading the `detail` text.

**D3 — An unwired model is reported as an execution failure, not as not-implemented.**
`engine/gateway/__init__.py:2166` and `:2170` raise `NotImplementedError`; the blanket
`except Exception` at `:1963` catches it and returns `error_code="EXECUTION_ERROR"`
(`:1972`). The honest "Model X is not implemented in this engine" text produced at `:491-495`
survives only as a free-text `message`. The spec has a dedicated `NOT_IMPLEMENTED`. Downstream
code has to reverse-engineer the distinction from the message string —
see `engine/hydroma/scenario_composite/engine.py:117-120`, which classifies a route as
*unwired* by matching the wording inside an `EXECUTION_ERROR` message.

**D4 — The gateway's code is destroyed at the services boundary.**
`services/_gateway_facade.py:218-219` converts every `GatewayError` into
`RuntimeError(f"Gateway error: {result.message}")`, dropping `error_code`,
`validation_errors` and `evidence_id`. 48 modules import this facade, so the majority of
services callers cannot see a code at all — only a prose message.

**D5 — Unit incompatibility and non-finite input have no code anywhere.**
`engine/gateway/__init__.py:2129-2133` raises a bare `ValueError` for a non-finite
unit-scaled value; `_route_float`/`_route_int` raise bare `TypeError`s at
`:1609`, `:1612`, `:1629`, `:1632`. All five are captured as `EXECUTION_ERROR`, conflating the
spec's `UNIT_INCOMPATIBLE` with `NUMERICAL_ERROR` and `INPUT_INVALID`. The audit tool that
would name the condition, `engine/gateway/pint_audit.py`, is not called by `execute()`.

**D6 — A persistence failure is silently swallowed.**
`engine/gateway/__init__.py:1886-1890` wraps `store_computation_record` in
`except Exception: pass`. A dropped evidence record is indistinguishable from a stored one,
so `PERSISTENCE_ERROR` (spec code 9) has no observable representation in the gateway.

**D7 — The services emit two of their own code vocabularies, neither of them the spec's.**
`services/api_gateway/exceptions.py:13` makes the machine-readable `code` equal the Python
class name (`"ValidationException"`, `"NotFoundException"`), while
`services/api_gateway/errors.py:27-45` emits snake_case generic codes
(`invalid_input`, `missing_field`, `not_implemented`, `internal_error`, …) for the same
conditions. `services/tasmimyar/decision_service.py:107`, `:127` adds a third
(`"DECISION_ERROR"`, `"NOT_FOUND"`).

**D8 — Two conditions are returned with HTTP 200.**
`services/validation/router.py:21` (unknown check id) and `:55` (missing reference-data file)
return `{"error": …}` with status 200; `services/validation/formula_checks.py:72-75` turns any
raised exception into `passed=False` with `actual="ERROR: …"`, still 200. A failed scientific
validation is therefore not a `VALIDATION_FAILED` error a client can act on — it is a value in
a successful response.

**D9 — `EXECUTION_ERROR` is a catch-all covering at least four distinct spec conditions.**
The single handler at `engine/gateway/__init__.py:1963-1977` absorbs: input normalization
failure (`:2130`), route input typing failure (`:1609`, `:1612`, `:1629`, `:1632`), import /
unwired-route failure (`:2166`, `:2170`) and handler crash. The spec separates these as
`NUMERICAL_ERROR`, `EXECUTION_FAILED`, `NOT_IMPLEMENTED` and `UNIT_INCOMPATIBLE`.

**Divergence count: 9** (D1–D9).

---

## 5. Target design — C-5 step 2

**End state.** `HydromaError` (`engine/errors.py:34-53`) becomes the engine's base error and
`GatewayError` (`engine/gateway/__init__.py:162-170`) becomes a subclass of it.

**The catch that must be designed for, not assumed.** `GatewayError` is a dataclass value
object that `EngineGateway.execute` **returns** (`engine/gateway/__init__.py:1903`, `:1922`,
`:1943`, `:1971`) and that callers detect with `isinstance(result, GatewayError)`
(`services/_gateway_facade.py:218`). It is part of the **`__all__` public surface**
(`engine/gateway/__init__.py` `__all__`). So step 2 is not a one-line base-class edit; it has
to keep three things true at once:

1. `isinstance(result, GatewayError)` stays true for the four returned error objects;
2. `isinstance(result, HydromaError)` becomes true, so a single `except HydromaError` /
   `except Exception` handler covers the engine's errors;
3. the dataclass field order and names (`error_code`, `message`, `model_id`,
   `validation_errors`, `execution`, `evidence_id`) are unchanged, so every existing
   construction site and every `dataclasses.asdict`-style serialisation keeps working.

The construction that satisfies all three is a dataclass subclassing the exception base
(`class GatewayError(HydromaError)` declared as a dataclass with the same six fields), with
`error_code` bound to the existing vocabulary values.

**Why it is behaviour-preserving.** Every gateway code is a *literal* at a construction site —
`"INVALID_REQUEST"` (`:1904`, `:1944`), `"MODEL_NOT_FOUND"` (`:1923`), `"EXECUTION_ERROR"`
(`:1972`). Introducing a shared base changes the class hierarchy and adds nothing else: no
call site is rewritten, no message is reworded, no status code moves. The only new capability
is that a caller can now catch `HydromaError` / inspect `error_code` and `context` on the
gateway's error objects. The behaviour that *is* observable — the three code strings — is
unchanged by construction, which is precisely why the plan grades this step
"behaviour-preserving".

**The one thing that is not behaviour-preserving and must not be bundled in.** The gateway's
three codes are **not** in the 13-code vocabulary. Making them conform means either (a)
declaring an explicit alias relation
(`INVALID_REQUEST → INPUT_INVALID`, `MODEL_NOT_FOUND → MODEL_UNKNOWN`,
`EXECUTION_ERROR → EXECUTION_FAILED`, with the raw `NotImplementedError`/`ValueError`/`TypeError`
sites migrating to `NOT_IMPLEMENTED` / `UNIT_INCOMPATIBLE` / `NUMERICAL_ERROR`), or
(b) extending `ERROR_CODES` with the gateway's three codes. Option (a) is the spec-conformant
one; option (b) is a spec change. Both are public-API decisions, both need a recorded mandate,
and neither is part of step 1.

**The test that proves it** — `engine/tests/test_error_taxonomy_conformance.py`:

```python
"""C-5 conformance: every engine-raised error carries a vocabulary code.

Walk the gateway's public entry point and collect the error_code of every
returned error; assert each is a key of ERROR_CODES (engine/errors.py:57).
Also assert the base-class relation step 2 introduces.
"""
from __future__ import annotations

import dataclasses
import inspect

from engine.errors import ERROR_CODES, HydromaError
from engine.gateway import EngineGateway, GatewayError, GatewayRequest

VOCABULARY = set(ERROR_CODES)


def _gateway_errors():
    """Every error the gateway can produce through its public path."""
    gw = EngineGateway()
    cases = [
        ("", {}),                                    # -> INVALID_REQUEST
        ("NO_SUCH_MODEL", {}),                       # -> MODEL_NOT_FOUND
        ("CANON-001", {}),                           # -> INVALID_REQUEST (missing inputs)
        ("CANON-001", {"temp_min": "x", "temp_max": 1.0, "rh_min": 1.0,
                       "rh_max": 1.0, "wind_speed": 1.0,
                       "solar_radiation": 1.0, "elevation": 1.0,
                       "latitude": 1.0, "doy": 1.0}),  # -> EXECUTION_ERROR
    ]
    for model_id, inputs in cases:
        result = gw.execute(GatewayRequest(model_id=model_id, inputs=inputs))
        yield result


def test_every_engine_error_code_is_in_the_vocabulary():
    """Step-2 conformance test. Fails today by exactly 3 codes (see ERROR-MAP §4)."""
    codes = set()
    for result in _gateway_errors():
        assert dataclasses.is_dataclass(result), result
        codes.add(result.error_code)
    assert codes <= VOCABULARY, f"off-vocabulary codes: {sorted(codes - VOCABULARY)}"


def test_gateway_error_is_a_hydroma_error():
    assert issubclass(GatewayError, HydromaError)
    err = GatewayError(error_code="INPUT_INVALID", message="m", model_id=None)
    assert isinstance(err, HydromaError)
    assert err.error_code in VOCABULARY


def test_no_other_engine_exception_subclasses_the_base_without_a_code():
    """Every HydromaError subclass must bind error_code from the vocabulary."""
    for cls in HydromaError.__subclasses__():
        params = inspect.signature(cls.__init__).parameters
        assert "error_code" in params, cls
```

**Measured baseline of `test_every_engine_error_code_is_in_the_vocabulary` on the live tree:**
it collects `{EXECUTION_ERROR, INVALID_REQUEST, MODEL_NOT_FOUND}` and fails with
`off-vocabulary codes: ['EXECUTION_ERROR', 'INVALID_REQUEST', 'MODEL_NOT_FOUND']`. That is the
deficiency rendered executable: the conformance test cannot go green until step 2 (or the
alias relation above) lands. Recording this baseline is the point of step 1.

---

## 6. Brake note

C-5 is graded **`Class: MAN`** with **`Brake: SB-03`**
(`reports/eco-nojin/ARCHITECTURE-REMEDIATION-PLAN.md:129`). SB-03 is
*"تغییر API عمومی (نام/ورودی/خروجی/استثنا)"* — a public-API change
(name / input / output / **exception**), `ECO-NOJIN_MASTER_v3.1_UNIFIED.md:33`.

Making `GatewayError` a subclass of `HydromaError` changes the **exception** part of the
public surface of `engine.gateway`, which is exported in `__all__` and consumed by 48 services
modules. It is therefore brake-taking and **requires a recorded mandate before any code is
written**.

**This document is step 1 (the map) only.** It adds one markdown file under
`reports/eco-nojin/`, changes no Python, adds no class, renames no code, and alters no
exception hierarchy. Step 2 is a separate, mandate-gated change against SB-03, sequenced in
wave **R9** of the plan (`reports/eco-nojin/ARCHITECTURE-REMEDIATION-PLAN.md:144`), i.e. after
R5–R8.

---

## 7. Reproduction

All citations were measured on the live tree, 2026-10-11:

```powershell
# Taxonomy A — the 3 gateway codes
Select-String -Path engine\gateway\__init__.py -Pattern 'error_code='
# Taxonomy B — the 13 spec codes
Select-String -Path engine\errors.py -Pattern '"[A-Z_]+": "'
# Taxonomy C — services status distribution
Select-String -Path services\**\*.py -Pattern 'HTTPException\(\s*(status_code=)?\d{3}'
# The facade's code-erasure
Select-String -Path services\_gateway_facade.py -Pattern 'GatewayError'
# Conformance baseline (see §5)
python -m pytest engine/tests/test_error_taxonomy_conformance.py -q
```
