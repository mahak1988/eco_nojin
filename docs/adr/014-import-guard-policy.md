# ADR-014 — Import-Guard Policy as a Versioned Data File

* **Status:** Accepted (Track C2 deliverable, ECO-02)
* **Date:** 2026-10-09
* **ECO alignment:** ECO-04 §11 boundary (engine must reach computation through the Gateway; services must not import engine internals directly). INV-003: hard-coded allow-lists are unreviewable and drift silently.

## Context

`tools/detect_imports.py` enforced the `SERVICES_NO_ENGINE_INTERNALS` rule with a
hard-coded Python list of sanctioned engine imports. Two problems:

1. The allow-list was buried inside imperative code — invisible in diffs, not
   version-controlled as data, and every edit required parsing Python.
2. Each entry lacked a **rationale**, so reviewers could not tell at a glance
   whether an exception was intentional debt or a regression.

## Decision

Extract the allow-list and the sanctioned-facade whitelist into a single
versioned data file: **`tools/import_guard_policy.json`** (structure
`rules.<RULE_NAME>.{allowed_imports, facade_files}`, each entry carrying a
`rationale`). `detect_imports.py` now loads this file via
`load_import_policy(path) / _embedded_policy()`:

* If `--policy=<file>` is passed, the rules are read from that JSON.
* If omitted, the tool falls back to the embedded copy (identical values) so
  CI stays green without a path argument.

The data file is the **source of truth**; the embedded copy is a safety mirror.
Removing a sanctioned import from the data file turns that import into a live
violation; **adding** one requires an ADR first (this file is the policy, not a
scratchpad).

## Sanctioned imports (current policy)

| Module | Rationale |
|---|---|
| `engine.hydroma.config.settings` | read-only `get_settings`; no computation |
| `engine.hydroma.config.rules` | read-only rule tables; no computation |
| `engine.hydroma.biofertilizer.models` | Pydantic result contracts, not computation |
| `engine.hydroma.core.models` | ORM result contracts (`Plant`/`Material`/`SoilProfile`), not computation |
| `engine.hydroma.carbon.calculator` | **POLICY GAP** — computation module; should be reached through the Gateway `CARBON_SEQ` handler, not imported directly. Retained only so the guard does not regress while the migration is pending (Track C2 follow-up). |
| `engine.hydroma.cpp_bridge` | capability probe `is_cpp_available`; not a computation call |

## Sanctioned facades

| Path | Rationale |
|---|---|
| `services/_gateway_facade.py` | sanctioned service↔engine bridge; `_execute()` delegates to `EngineGateway`. The direct `engine.hydroma` imports it still holds (`soil.chemistry`, `engine.hydroma.models`, `cpp_bridge`) are remaining migration debt tracked by Track C2. |
| `services/api_gateway/routers/hydroma_common.py` | shared API-Gateway helpers forwarding to the facade / Gateway |

## Consequences

* **Positive:** allow-list is reviewable, versioned, and auditable; every
  exception carries an explicit rationale; POLICY GAPs are visible in the data
  file rather than silent.
* **Risk:** the data file must not drift from the embedded copy. `load_import_policy`
  asserts the two are structurally equal and fails fast if they diverge.
* **Migration debt (NOT resolved by this ADR):**
  1. `engine.hydroma.carbon.calculator` — route through `CARBON_SEQ` handler.
  2. `services/_gateway_facade.py` still imports `soil.chemistry` and
     `engine.hydroma.models` directly — migrate to `EngineGateway` dispatch.

## Verification

* Recorded at ADR acceptance (2026-10-09): `python
  tools/detect_imports.py --policy=tools/import_guard_policy.json --format=json`
  → `status: PASS`, 0 violations (969 files scanned).
* Default run (no flag) → `status: PASS`, 0 violations; embedded fallback is
  structurally identical to the data file.

**Re-measured 2026-10-11 (live tree):** the default run now reports
`Violations found: 16`, all `SERVICES_NO_ENGINE_INTERNALS`, all inside the
untracked in-flight package `services/_gateway_facade_adapters/`
(`carbon.py`, `climate.py`, `economics.py`, `groundwater.py`, `soil.py`) against
1192 files scanned. That regression was **not** introduced by the sanctioned
policy above — it is new untracked code importing `engine.hydroma.*` directly,
and it needs an owner under `services/**`. The embedded-fallback structural
equality assertion (`load_import_policy`) is unaffected.

## Note on the core/database shim (ECO-04 §11)

`engine/hydroma/core/database.py` is the engine↔database **compatibility shim**.
It must NOT import `database.base` directly (that would cross the ECO-04 §11
boundary and trip `ENGINE_NO_DATABASE`). The current (in-progress) version
resolves `Base`/`SessionLocal` lazily through
`engine.ports.PersistencePort` (`port.get_base()`), which is the contract the
engine is permitted to depend on. This keeps the guard green while preserving
backwards compatibility for `from engine.hydroma.core.database import Base`.

## Related

* ECO-00 invariant: single `Base` object — see `test_shared_base_is_a_single_object`.
* INV-003: import-guard policy must be data, not code.
* Track C2 follow-ups: carbon.calculator migration; facade direct-import cleanup.
