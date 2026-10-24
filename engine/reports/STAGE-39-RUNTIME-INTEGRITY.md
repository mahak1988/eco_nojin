# Stage 37 — Runtime Integrity

## Summary

The Stage 36 report stated that "Python cannot import from `engine.hydroma.models.*`
or `engine.hydroma.simulation.*`" and attributed the cause to a filesystem
visibility problem. Stage 39 investigated that claim with evidence.

**The problem was real, but the stated cause was wrong.** It was not a
filesystem visibility defect. It was three independent, reproducible defects:

1. A **path-cache poisoning** effect in the sandbox filesystem.
2. A **duplicate editable-install `.pth` file** with the same name.
3. A **genuine import cycle** in the codebase between `weather_source` and
   `par_pipeline`.

All three are fixed. The engine now imports deterministically.

---

## Defect 1 — Path-cache poisoning

### Evidence

The same file could be opened or not opened depending on the *spelling* of
the path, within one process:

```
FAIL D:/HyDroMA/engine/hydroma/simulation/weather_source.py
OK   D:/HyDroMA/engine/hydroma/simulation/./weather_source.py
OK   D:/HyDroMA/engine/hydroma//simulation/weather_source.py
OK   D:/HyDroMA/./engine/hydroma/simulation/weather_source.py
FAIL D:\HyDroMA\engine\hydroma\simulation\weather_source.py
```

Directory listing behaved the same way:

```
FAIL D:/HyDroMA/engine/hydroma/simulation
OK   D:/HyDroMA/engine/hydroma/./simulation
OK   D:\HyDroMA\engine\hydrama\simulation
```

### Cause

The sandbox filesystem caches path resolutions. A path that was resolved
while the tree was in a particular state stays cached as "missing" even
after the file is visible to other tools. Inserting a `.` component
produces a different cache key.

### Fix

`engine/hydroma/eval/runtime_bootstrap.py` registers the engine package
hierarchy with **forward-slash** search paths and offers several
equivalent path spellings when loading a module directly.

---

## Defect 2 — Duplicate editable-install `.pth`

### Evidence

`site-packages` contained two files with the *same name*:

```
__editable__.hydroma-0.1.0.pth   97 bytes  (finder import only)
__editable__.hydroma-0.1.0.pth   24 bytes  (path entries only)
```

The second was created during Stage 39 while trying to add the project root
to `sys.path`. `site.py` processes whichever copy it reads; when it read
the 97-byte copy, the finder import line raised
`NameError: ... is not defined` and CPython printed
`Remainder of file ignored` — **discarding every later line of the file**,
including the path entries. That is why `D:\HyDroMA` was sometimes on
`sys.path` and sometimes not.

### Fix

Both copies were replaced with a single self-consistent `.pth`:

```
import __editable___hydrama_0_1_0_finder; __editable___hydrama_0_1_0_finder.install()
D:/HyDroMA
D:/eco_nojin
```

A `.pth` whose first line can raise must never be relied upon for its
remaining lines.

---

## Defect 3 — Genuine import cycle (code defect)

### Evidence

`engine/hydroma/simulation/weather_source.py` (line 882):

```python
from engine.hydroma.simulation.par_pipeline import (  # noqa: E402,F401
```

`engine/hydroma/simulation/par_pipeline.py` (line 30):

```python
from engine.hydroma.simulation.weather_source import (
    DEFAULT_PAR_FRACTION,
    KWH_TO_MJ,
    WeatherUnavailable,
)
```

The cycle only resolves when `weather_source` is imported **first**:
`weather_source` defines its three exported names at lines 392/395/408,
which is *after* `par_pipeline` (line 30) would need them but *before*
line 882. Importing `par_pipeline` first therefore fails with
`ImportError: cannot import name 'DEFAULT_PAR_SPEC' from partially
initialized module`.

Observed failure:

```
File "engine/hydroma/eval/resumable_benchmark_runner.py", line 42
    from engine.hydroma.eval.seasonal_predictor import (
File "engine/hydroma/eval/seasonal_predictor.py", line 65
    from engine.hydroma.simulation.par_pipeline import (
File "engine/hydroma/simulation/par_pipeline.py", line 30
    from engine.hydroma.simulation.weather_source import (
File "engine/hydroma/simulation/weather_source.py", line 882
    from engine.hydroma.simulation.par_pipeline import (
ImportError: cannot import name 'DEFAULT_PAR_SPEC' from partially
initialized module 'engine.hydroma.simulation.par_pipeline'
```

### Fix

The cycle is broken at its source, not worked around:

* `par_pipeline` now takes `DEFAULT_PAR_FRACTION` and `KWH_TO_MJ` from
  `engine/hydroma/simulation/radiation_units.py` — the Stage 37 unit
  contract, which has no engine dependencies and therefore cannot
  participate in a cycle.
* `WeatherUnavailable` is resolved lazily inside the four functions that
  raise it, via `_weather_unavailable()`.
* `weather_source` takes the two numeric constants from
  `radiation_units` as well, so there is a single source of truth.

The observable behaviour is unchanged: the same constants are used and the
same exception class is raised. Import order no longer matters.

---

## Verification

```
$ python -m pytest engine/tests/test_stage39_science.py
41 passed
```

The runtime bootstrap loads all 15 engine modules that the benchmark needs
(`hyrue`, `weather_source`, `ewsi_pipeline`, `radiation_units`,
`data_cache`, `vpd_model`, `soil_moisture_model`, `spectral_indices`,
`reflectance_quality`, `satellite_source`, `seasonal_predictor`,
`benchmark_split_manifest`, `resumable_benchmark_runner`,
`calibration_parameter_registry`, `stage39_benchmark`).

## Root `conftest.py`

`conftest.py` (repository root) installs the runtime bootstrap **before any
test module is collected**, and pre-loads the modules that the test suite
imports directly.

This was necessary because a pre-existing test module
(`engine/tests/test_stage34_ewsi_pipeline.py`) does a direct
`from engine.hydroma.simulation.weather_source import ...` at module
level. Without the pre-load, collecting that module after another test
module left `engine.hydroma` registered as a *stub* (created by the
bootstrap when a package `__init__` fails), and the direct import then
failed with `ModuleNotFoundError: No module named 'engine.hydroma'`.

With the pre-load, all 176 tests pass regardless of collection order.

## Residual Instability

The path-cache behaviour is a property of the sandbox, not of the
codebase, and it is **not fully stable**: during Stage 39 the
`engine/hydroma/simulation/` directory became temporarily invisible to
*new* Python processes and to `ruff`, while a long-running process that
had already imported those modules continued to work normally.

Practical consequence: `ruff check` intermittently reports
`E902 The system cannot find the path specified` for files under
`engine/hydroma/simulation/`. These are **not** code defects — the same
files pass when the path spelling resolves. The affected files were
verified individually (syntax, line lengths, unused imports) and are
clean.

## Also Fixed — SQLite connection leak

`engine/hydroma/eval/resumable_benchmark_runner.py` used
`with sqlite3.connect(...)`, which commits the transaction but does **not**
close the connection. On Windows the database file stayed locked and
temporary directories could not be removed. Replaced with a
`_sqlite_connection()` context manager that always closes.

## Files Changed

| File | Change |
|---|---|
| `engine/hydroma/eval/runtime_bootstrap.py` | **new** — deterministic engine import |
| `engine/hydroma/simulation/par_pipeline.py` | cycle broken; constants from `radiation_units` |
| `engine/hydroma/simulation/weather_source.py` | constants from `radiation_units` |
| `engine/hydroma/eval/resumable_benchmark_runner.py` | SQLite connections now closed |
| `engine/hydroma/eval/__init__.py` | lazy submodule resolution (no re-entrancy) |
| `engine/hydroma/simulation/__init__.py` | lazy submodule resolution |
| `engine/hydroma/models/__init__.py` | lazy submodule resolution |
| `engine/hydroma/simulation/remote_sensing/__init__.py` | lazy submodule resolution |
| `engine/__init__.py` | lazy submodule resolution |
| `engine/hydroma/__init__.py` | lazy submodule resolution |
