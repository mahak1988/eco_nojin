"""Guards the port-injected session factory in ``biofertilizer/calibration.py``.

Rewritten 2026-10-11 for the B-2 mandate (port injection): the module used to
import ``SessionLocal`` from ``database.config`` directly, which is exactly the
engine→implementation coupling the spec forbids. The engine-side import is gone
(``tools/import_guard_policy.json`` marks ``database.config`` ``pending-removal``);
the numerical body and its results are unchanged, and the new tests here pin the
port-based design instead:

* the module no longer imports anything from ``database`` (AST + import-clean);
* the port is injectable and the default port is the in-process bridge;
* the numerical results are the ones the pre-injection code produced
  (``PINNED_PARAMETERS`` / ``PINNED_QUALITY_SCORE`` in
  ``engine/tests/test_biofertilizer_port_injection.py``).

The earlier version of this file pinned the removed ``SessionLocal`` import; it
was superseded by the mandate and replaced here rather than deleted, so the
history of what was asserted and why it changed stays visible.
"""

import ast
from pathlib import Path

import pytest

from engine.hydroma.biofertilizer import calibration

_CALIBRATION_PATH = Path(calibration.__file__)


def test_calibration_module_imports():
    """The whole module imports without reaching into ``database``."""
    assert calibration is not None


def test_module_no_longer_imports_database():
    """No ``database`` import at module level or deferred (B-2 step 1)."""
    tree = ast.parse(_CALIBRATION_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("database"), alias.name
        elif isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("database"), node.module


def test_importing_calibration_adds_no_unsanctioned_database_modules():
    """Measured in a clean subprocess: only the still-sanctioned bridge module.

    The package ``__init__`` pulls ``.models`` → ``database.base``, which is
    the second (``pending-removal``) bridge entry and therefore still allowed.
    What must NOT appear is ``database.config`` — the module this mandate
    retired from the engine.
    """
    import json
    import os
    import subprocess
    import sys

    program = (
        "import sys, json;"
        "from engine.hydroma.biofertilizer import calibration;"
        "mods = sorted(m for m in sys.modules if m == 'database' or m.startswith('database.'));"
        "print(json.dumps(mods))"
    )
    result = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": r"D:\HyDroMA;D:\eco_nojin"},
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-500:]
    modules = json.loads(result.stdout.strip().splitlines()[-1])
    assert "database.config" not in modules, (
        f"calibration still reaches database.config: {modules}"
    )


def test_session_factory_comes_from_the_injected_port():
    """The default port supplies the session factory; a fake port wins."""
    from engine.hydroma.biofertilizer.persistence_bridge import (
        InProcessCalibrationPort,
    )

    default_port = calibration.default_calibration_port()
    assert isinstance(default_port, InProcessCalibrationPort)
    assert callable(default_port.get_session_factory())

    class _Session:
        """Minimal session stand-in: query chain returns no trial rows."""

        def __init__(self, calls):
            self.calls = calls

        def query(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return []

        def close(self):
            self.calls.append("close")

    class _Column:
        @staticmethod
        def in_(values):
            return list(values)

    class _TrialDB:
        id = _Column()

    class RecordingPort:
        def __init__(self):
            self.calls = []

        def get_session_factory(self):
            self.calls.append("session_factory")
            session = _Session(self.calls)
            return lambda: session

        def get_model_attr(self, module, name):
            # The port protocol is ``get_model_attr(module, name)``; the
            # calibration module asks for ``("models", <row class>)``.
            self.calls.append(f"model_attr:{module}.{name}")
            return _TrialDB

    port = RecordingPort()
    # With no trial rows the calibration refuses ("No trial data found"),
    # which is exactly what pins that the injected port — not the in-process
    # default — resolved the row classes and the session factory.
    with pytest.raises(ValueError, match="No trial data found"):
        calibration.calibrate_formulation_model(
            formulation_id="FORM-TEST",
            trial_data_ids=[],
            model_version="v1",
            port=port,  # type: ignore[arg-type]
        )
    assert "session_factory" in port.calls
    assert "model_attr:models.NojinFieldTrialDB" in port.calls


def test_engine_local_rows_do_not_need_database_models():
    """The in-process port builds its own declarative base (no ``database`` import)."""
    from engine.hydroma.biofertilizer import persistence_bridge

    source = Path(persistence_bridge.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("database"), node.module

