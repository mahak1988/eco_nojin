"""G1 — import smoke gate.

Every production module under ``services/`` must import cleanly.

Why this gate exists, concretely: ``services/satellite/sentinel2_provider.py``
declared ``class SafeUnpickler(pickle.Unpickler)`` with ``import pickle``
scoped to a function, so the module raised ``NameError`` at import time. That
transitively broke ``scientific_motors/satellite_integration.py`` and
``mrv_system.py``, and ``telegram_bot/integration.py`` swallowed the failure
into ``{"error": "Motors not available"}`` for five motors. 1,026 lines of
Sentinel-2 handling never ran, and nothing noticed.

The gap was not subtle — it was one missing import line — but no test in the
repository imported these modules. This gate closes it.

Modules are imported in batches inside a subprocess rather than one subprocess
per module: the detection is identical (a module-level ``NameError`` fails
that module's import and the loop continues to the next), but it costs
seconds instead of tens of minutes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: Modules that cannot import in this environment, with the reason.
#:
#: These are excuses for *environment* faults, not code faults, and each is
#: conditional: the excuse only applies while its cause is still true, so a
#: fixed dependency stops being masked automatically. See
#: :func:`_still_broken`.
ENVIRONMENT_EXCUSES: dict[str, str] = {
    # passlib 1.7.4's context.py carries `from __future__ import with_statement`,
    # which Python 3.12 rejects outright. The only consumer is
    # services/auth/main.py, which nothing imports (the live auth path is
    # services/api_gateway/auth.py).
    "services.auth.main": "passlib.context",
    # pyRothC is installed but exposes no `rothc` symbol in this environment.
    "services.carbon.rothc_service": "pyRothC.rothc",
    # python-telegram-bot is not a declared dependency of the API service.
    "services.telegram_bot.main": "telegram",
    "services.telegram_bot.handlers": "telegram",
}

BATCH_SIZE = 40


def _still_broken(module: str) -> bool:
    """True while the named module is genuinely unimportable in this environment.

    Probes the exact submodule that is broken, not the top-level package:
    ``import passlib`` succeeds even though ``import passlib.context`` is a
    SyntaxError, so probing the package would have masked the real fault.
    """
    import importlib
    import importlib.util

    try:
        if importlib.util.find_spec(module) is None:
            return True
    except (ImportError, ValueError, ModuleNotFoundError):
        return True
    try:
        importlib.import_module(module)
    except BaseException:
        return True
    return False


def _excused() -> dict[str, str]:
    return {
        module: reason for module, reason in ENVIRONMENT_EXCUSES.items() if _still_broken(reason)
    }


def _production_modules() -> list[str]:
    modules: list[str] = []
    for path in sorted((ROOT / "services").rglob("*.py")):
        if any(part in {"__pycache__", ".venv", "node_modules"} for part in path.parts):
            continue
        rel = path.relative_to(ROOT).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.append(".".join(parts))
    return modules


def _import_batch(batch: list[str]) -> dict[str, str]:
    """Import each module in its own namespace; return {module: error}."""
    script = (
        "import importlib, json, sys\n"
        "out = {}\n"
        "for name in json.loads(sys.argv[1]):\n"
        "    try:\n"
        "        importlib.import_module(name)\n"
        "    except BaseException as exc:\n"
        "        out[name] = f'{type(exc).__name__}: {exc}'[:300]\n"
        "print('<<<G1>>>' + json.dumps(out))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script, json.dumps(batch)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("<<<G1>>>"):
            return json.loads(line[len("<<<G1>>>") :])
    return dict.fromkeys(batch, f"worker produced no report (exit {proc.returncode})")


@pytest.fixture(scope="module")
def import_failures() -> dict[str, str]:
    modules = _production_modules()
    assert modules, "no production modules discovered under services/"
    failures: dict[str, str] = {}
    for start in range(0, len(modules), BATCH_SIZE):
        failures.update(_import_batch(modules[start : start + BATCH_SIZE]))
    return failures


@pytest.fixture(scope="module")
def excused() -> dict[str, str]:
    return _excused()


def test_every_production_module_was_checked(import_failures):
    """Guards against the scanner silently finding nothing."""
    assert len(_production_modules()) > 400


def test_no_production_module_fails_to_import(import_failures, excused):
    unexpected = {
        module: error for module, error in import_failures.items() if module not in excused
    }
    if unexpected:
        listed = "\n".join(f"  - {m}: {e}" for m, e in sorted(unexpected.items()))
        pytest.fail(
            "G1: these production modules fail to import. A module-level error means the\n"
            "module has never run in production.\n" + listed,
            pytrace=False,
        )


def test_excuses_are_still_needed(import_failures, excused):
    """An excuse whose dependency is fixed must be removed, not left behind."""
    stale = [
        f"{module}: {ENVIRONMENT_EXCUSES[module]}"
        for module in ENVIRONMENT_EXCUSES
        if module not in excused
    ]
    if stale:
        pytest.fail(
            "G1: these dependencies now import cleanly — remove them from "
            "ENVIRONMENT_EXCUSES:\n  " + "\n  ".join(stale),
            pytrace=False,
        )


def test_excused_modules_still_actually_fail(import_failures, excused):
    """The converse: an excuse must not cover a module that is now fine."""
    covered_but_working = [m for m in excused if m not in import_failures]
    if covered_but_working:
        pytest.fail(
            "G1: excused but importing cleanly, so the excuse is hiding a real fix:\n  "
            + "\n  ".join(covered_but_working),
            pytrace=False,
        )
