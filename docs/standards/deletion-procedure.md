# Removing code

Deleting a file that is alive is the most expensive mistake in a consolidation.
It fails at runtime, on a path nobody exercised, and the traceback points
somewhere else. The integration plan names it as a medium-probability,
medium-impact risk and specifies a three-step mitigation. Two of the three are
automated. This is the third, written down so the ordering is followed by
default rather than remembered.

## The three steps

### 1. Establish that nothing can reach it

```powershell
python scripts/verify_consolidation.py --skip-contract
```

Green output means: every production module parses, all twelve critical
modules import, and no ratchet metric regressed. Run this **before** the
deletion and keep the output — it is what a reviewer asks to see.

Two other checks must also be clean:

- **Whole-repository importer search.** Not "does it import anything", but
  "does anything import it", including strings, `importlib.import_module`
  arguments, and configuration files. A module reached only dynamically will
  not appear in an IDE's "find usages".
- **vulture at 90% confidence**, for definitions rather than modules. A module
  nothing names will not be reported by `--min-confidence 90`; that is expected,
  and it is why step 1 also needs the importer search.

### 2. Get a second opinion, and treat "it looked dead" as a claim

If the evidence is not clean — the importer search is ambiguous, the module
sits behind a namespace package, or a name collides with a live one — a
**human reviewer decides**. Do not resolve an ambiguous deletion with a
heuristic.

Two real cases from the phase 4/5 campaign, both of which a heuristic would
have got wrong:

- `engine/hydroma/core.py` and the `engine/hydroma/core/` package share a
  module name. Python always resolves the package, so the file was
  unreachable — and equally, no import statement can name the file, so an
  importer search reports every `from engine.hydroma.core import X` as a live
  reference. The collision is recorded in the deletion log.
- `services/map_engine/tests/` existed, so the package looked covered. Its
  tests exercised only a mock behind a router mounted nowhere, while the
  orchestrator and six fetchers had no tests at all. "There are tests next to
  it" is not "it is tested".

### 3. Delete, then prove the suite was already green

```powershell
python scripts/measure_baseline.py --check      # ratchet must not have moved
python -m pytest tests/contract -q              # the gates must still pass
python -m pytest services -q -n 4               # the affected lane
```

If any of these fail *because of* the deletion, restore it (below) and record
why. A deletion that requires a new test to pass is a deletion that was wrong.

## Recording it

Every deletion goes in `docs/metrics/deletions.json` with:

| field | meaning |
|---|---|
| `path` | the deleted file, repository-relative |
| `reason` | why it was dead — specific enough to review, not "unused" |
| `verified_by` | what was actually run, so a reviewer can repeat it |
| `phase` | which phase authorised it |
| `owner_domain` | the D-id from the ownership table, so the deletion has a reviewer |
| `moved_to` | set when the content was moved rather than lost |
| `name_collision_with_live_package` | set when a live package shadows the deleted file's name |

`tests/contract/test_deletion_log.py` enforces all of it. An entry without a
reason or a verification fails the build, and a path that reappears fails it
too.

## Undo

Every logged deletion is a file tracked in git, which
`tests/contract/test_deletion_safety.py` verifies. Restoring is one command:

```powershell
git checkout HEAD -- <path>
```

Then remove the entry from the log. This is why the log exists: a deletion that
is recorded, attributed and verified is a decision someone can review and
reverse. One that happened in a hurry is neither.

## What this does not cover

Deleting a *behaviour* rather than a file — changing what a function does
rather than whether it exists. The S-HONEST ledger
(`docs/standards/tolerated-degradations.yaml`) covers that: a path whose
recorded defect is fixed must have its entry removed, and the G2 gate fails if
a fabrication is replaced with a new one.
