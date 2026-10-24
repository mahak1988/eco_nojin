"""Port injection for the biofertilizer calibration entry points (remediation B-2).

``engine/hydroma/biofertilizer/calibration.py`` used to import ``SessionLocal``
from ``database.config`` at module scope, so the engine's calibration path
reached the database implementation directly. B-2 replaces that with the
existing persistence-port abstraction: the entry points take an injected port
(:class:`~engine.hydroma.biofertilizer.persistence_bridge.CalibrationPersistencePort`)
and default to an in-process, database-free adapter.

What this module pins
---------------------
1. **Numerical parity.** The calibration optimiser is a plain BFGS least
   squares over the trial rows; the "before" numbers were captured by running
   the *pre-injection* code over the fixed input set below (the ORM classes
   came from a recording port and the session from a session factory, the only
   way that code could be executed at all - see
   ``reports/eco-nojin/REMEDIATION-B2-REPORT.md`` section 3). The after-injection
   run must reproduce them bit for bit.
2. **The port is the collaborator.** A SQLAlchemy-free fake port records every
   call; the module must get its row classes, its session factory and its
   reads/writes from it and from nothing else.
3. **Import cleanliness.** Neither ``calibration.py`` nor ``persistence_bridge.py``
   contains a ``database`` import, and importing ``calibration`` adds no
   ``database`` module to ``sys.modules`` beyond what the parent package
   already imported (the package ``__init__`` -> ``.models`` ->
   ``database.base`` edge belongs to the second bridge entry and is pinned as
   known state by :func:`test_fresh_interpreter_import_still_reports_the_models_bridge`).
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from engine.hydroma.biofertilizer import calibration
from engine.hydroma.biofertilizer.persistence_bridge import (
    CalibrationPersistencePort,
    InProcessCalibrationPort,
    default_calibration_port,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = (
    PROJECT_ROOT / "engine" / "hydroma" / "biofertilizer" / "calibration.py"
)
BRIDGE_PATH = (
    PROJECT_ROOT / "engine" / "hydroma" / "biofertilizer" / "persistence_bridge.py"
)

# ── the fixed input set ──────────────────────────────────────────────────────
# Ten trials (more rows than the eight optimised parameters) so the BFGS least
# squares converges. Fixed literals, never generated at runtime, so the pinned
# numbers below are reproducible.

FORMULATION_ID = "FORM-ALPHA"
MODEL_VERSION = "v1"
TRIAL_IDS = [f"T-{index}" for index in range(1, 11)]

TRIAL_ROWS: list[dict[str, Any]] = [
    {
        "id": "T-1",
        "application_plan_id": "PLAN-1",
        "trial_location": "31.4,34.3",
        "crop_type": "wheat",
        "dosage_kg_ha": 12.5,
        "baseline_data": {
            "soil_ph": 7.8,
            "soil_om_pct": 2.1,
            "soil_n_kg_ha": 110,
            "soil_p_kg_ha": 45,
            "soil_k_kg_ha": 190,
        },
        "post_application_data": {"yield_t_ha": 4.6, "notes": "season 1"},
        "yield_response": 0.82,
        "statistical_analysis": {"p_value": 0.01, "n": 4},
    },
    {
        "id": "T-2",
        "application_plan_id": "PLAN-2",
        "trial_location": "29.5,34.9",
        "crop_type": "maize",
        "dosage_kg_ha": 18.0,
        "baseline_data": {
            "soil_ph": 6.4,
            "soil_om_pct": 1.3,
            "soil_n_kg_ha": 78,
            "soil_p_kg_ha": 22,
            "soil_k_kg_ha": 96,
        },
        "post_application_data": {"yield_t_ha": 6.1, "notes": "season 1"},
        "yield_response": 1.24,
        "statistical_analysis": {"p_value": 0.03, "n": 4},
    },
    {
        "id": "T-3",
        "application_plan_id": "PLAN-3",
        "trial_location": "32.1,35.2",
        "crop_type": "barley",
        "dosage_kg_ha": 9.75,
        "baseline_data": {
            "soil_ph": 7.1,
            "soil_om_pct": 3.4,
            "soil_n_kg_ha": 145,
            "soil_p_kg_ha": 61,
            "soil_k_kg_ha": 240,
        },
        "post_application_data": {"yield_t_ha": 3.9, "notes": "season 2"},
        "yield_response": 0.41,
        "statistical_analysis": {"p_value": 0.04, "n": 4},
    },
    {
        "id": "T-4",
        "application_plan_id": "PLAN-4",
        "trial_location": "30.9,34.8",
        "crop_type": "wheat",
        "dosage_kg_ha": 15.25,
        "baseline_data": {
            "soil_ph": 7.5,
            "soil_om_pct": 2.8,
            "soil_n_kg_ha": 122,
            "soil_p_kg_ha": 52,
            "soil_k_kg_ha": 210,
        },
        "post_application_data": {"yield_t_ha": 5.2, "notes": "season 2"},
        "yield_response": 0.95,
        "statistical_analysis": {"p_value": 0.02, "n": 4},
    },
    {
        "id": "T-5",
        "application_plan_id": "PLAN-5",
        "trial_location": "28.7,35.1",
        "crop_type": "maize",
        "dosage_kg_ha": 21.5,
        "baseline_data": {
            "soil_ph": 6.1,
            "soil_om_pct": 1.1,
            "soil_n_kg_ha": 64,
            "soil_p_kg_ha": 18,
            "soil_k_kg_ha": 82,
        },
        "post_application_data": {"yield_t_ha": 6.8, "notes": "season 3"},
        "yield_response": 1.51,
        "statistical_analysis": {"p_value": 0.01, "n": 4},
    },
    {
        "id": "T-6",
        "application_plan_id": "PLAN-6",
        "trial_location": "31.8,34.6",
        "crop_type": "barley",
        "dosage_kg_ha": 8.5,
        "baseline_data": {
            "soil_ph": 7.3,
            "soil_om_pct": 3.9,
            "soil_n_kg_ha": 158,
            "soil_p_kg_ha": 70,
            "soil_k_kg_ha": 265,
        },
        "post_application_data": {"yield_t_ha": 3.6, "notes": "season 3"},
        "yield_response": 0.33,
        "statistical_analysis": {"p_value": 0.05, "n": 4},
    },
    {
        "id": "T-7",
        "application_plan_id": "PLAN-7",
        "trial_location": "30.2,35.4",
        "crop_type": "wheat",
        "dosage_kg_ha": 14.0,
        "baseline_data": {
            "soil_ph": 7.6,
            "soil_om_pct": 2.4,
            "soil_n_kg_ha": 116,
            "soil_p_kg_ha": 48,
            "soil_k_kg_ha": 200,
        },
        "post_application_data": {"yield_t_ha": 4.9, "notes": "season 1"},
        "yield_response": 0.88,
        "statistical_analysis": {"p_value": 0.02, "n": 4},
    },
    {
        "id": "T-8",
        "application_plan_id": "PLAN-8",
        "trial_location": "29.9,34.7",
        "crop_type": "maize",
        "dosage_kg_ha": 19.75,
        "baseline_data": {
            "soil_ph": 6.6,
            "soil_om_pct": 1.6,
            "soil_n_kg_ha": 88,
            "soil_p_kg_ha": 27,
            "soil_k_kg_ha": 108,
        },
        "post_application_data": {"yield_t_ha": 6.4, "notes": "season 2"},
        "yield_response": 1.37,
        "statistical_analysis": {"p_value": 0.01, "n": 4},
    },
    {
        "id": "T-9",
        "application_plan_id": "PLAN-9",
        "trial_location": "32.4,34.9",
        "crop_type": "barley",
        "dosage_kg_ha": 10.5,
        "baseline_data": {
            "soil_ph": 7.0,
            "soil_om_pct": 3.1,
            "soil_n_kg_ha": 138,
            "soil_p_kg_ha": 58,
            "soil_k_kg_ha": 228,
        },
        "post_application_data": {"yield_t_ha": 4.1, "notes": "season 3"},
        "yield_response": 0.52,
        "statistical_analysis": {"p_value": 0.03, "n": 4},
    },
    {
        "id": "T-10",
        "application_plan_id": "PLAN-10",
        "trial_location": "31.1,35.0",
        "crop_type": "wheat",
        "dosage_kg_ha": 16.5,
        "baseline_data": {
            "soil_ph": 7.4,
            "soil_om_pct": 2.6,
            "soil_n_kg_ha": 119,
            "soil_p_kg_ha": 50,
            "soil_k_kg_ha": 205,
        },
        "post_application_data": {"yield_t_ha": 5.0, "notes": "season 1"},
        "yield_response": 0.91,
        "statistical_analysis": {"p_value": 0.02, "n": 4},
    },
]

# ── the pinned "before" values ───────────────────────────────────────────────
# Captured 2026-10-11 by running the pre-injection ``calibrate_formulation_model``
# / ``load_calibrated_model`` (git HEAD state of the file) over the fixed input
# set above; bit-stable across repeated runs and fresh processes.

PINNED_PARAMETERS = [
    0.049210098922863856,
    0.15906516268421791,
    0.10319220210912364,
    -0.009237108393231684,
    0.02742129627839057,
    -0.008327059218237669,
    0.05141716842490017,
    0.04921009892286387,
]
PINNED_QUALITY_SCORE = 0.9993625553687174


# ── a SQLAlchemy-free fake port ───────────────────────────────────────────────
# The module must not care what ORM it is handed, so the fake speaks the
# smallest surface ``calibration.py`` actually uses: class-level "columns" that
# support ``in_`` / ``==`` / ``desc``, instance attributes carrying the data,
# and a session whose queries filter, order, add, commit and close.


class _FakeColumn:
    """Stand-in for a mapped column: only the comparisons calibration makes."""

    def __init__(self, name: str) -> None:
        self.name = name

    def in_(self, values: Any) -> tuple[str, str, tuple[Any, ...]]:
        return ("in", self.name, tuple(values))

    def desc(self) -> tuple[str, str]:
        return ("desc", self.name)

    def __eq__(self, other: Any) -> tuple[str, str, Any]:  # type: ignore[override]
        # Deliberately not a bool: the call under test is the ``==`` in
        # ``calibration_record_db.formulation_id == formulation_id``, and the
        # fake records the comparison instead of evaluating it.
        return ("eq", self.name, other)

    def __hash__(self) -> int:
        return hash(("_FakeColumn", self.name))


class _FakeRow:
    """Row base: class attributes are "columns", instance attributes are data."""

    def __init__(self, **fields: Any) -> None:
        for name, value in fields.items():
            setattr(self, name, value)


class FakeTrialRow(_FakeRow):
    id = _FakeColumn("id")
    formulation_id = _FakeColumn("formulation_id")


class FakeCalibrationRecordRow(_FakeRow):
    id = _FakeColumn("id")
    formulation_id = _FakeColumn("formulation_id")
    calibration_date = _FakeColumn("calibration_date")


class _FakeQuery:
    def __init__(self, session: FakeSession, model: type) -> None:
        self._session = session
        self._model = model
        self._predicates: list[tuple[str, str, Any]] = []
        self._order: tuple[str, str] | None = None

    def filter(self, predicate: tuple[str, str, Any]) -> _FakeQuery:
        self._predicates.append(predicate)
        return self

    def order_by(self, criterion: tuple[str, str]) -> _FakeQuery:
        self._order = criterion
        return self

    def all(self) -> list[Any]:
        return self._matching()

    def first(self) -> Any | None:
        rows = self._matching()
        if not rows:
            return None
        if self._order is not None and self._order[0] == "desc":
            field = self._order[1]
            rows = sorted(rows, key=lambda row: getattr(row, field), reverse=True)
        return rows[0]

    def _matching(self) -> list[Any]:
        rows = self._session.rows_for(self._model)
        # Ordered by ``id``, the way the production store returns them: the
        # ORM rows carry a text primary key, so SQLite serves the ``IN``
        # filter from that key's unique index in key order, not insertion
        # order. Row order feeds the optimiser's summation order, so the fake
        # must reproduce it to pin the same floats.
        return sorted(
            (row for row in rows if self._matches(row)),
            key=lambda row: str(getattr(row, "id", "")),
        )

    def _matches(self, row: Any) -> bool:
        for kind, field, value in self._predicates:
            actual = getattr(row, field)
            if kind == "in":
                if actual not in value:
                    return False
            elif kind == "eq":
                if actual != value:
                    return False
        return True


class FakeSession:
    def __init__(self, store: dict[type, list[Any]], calls: list[tuple[Any, ...]]) -> None:
        self._store = store
        self._calls = calls
        self._pending: list[Any] = []

    def rows_for(self, model: type) -> list[Any]:
        return self._store.setdefault(model, [])

    def query(self, model: type) -> _FakeQuery:
        self._calls.append(("query", model.__name__))
        return _FakeQuery(self, model)

    def add(self, record: Any) -> None:
        self._calls.append(("add", type(record).__name__))
        self._pending.append(record)

    def commit(self) -> None:
        self._calls.append(("commit",))
        for record in self._pending:
            self.rows_for(type(record)).append(record)
        self._pending.clear()

    def close(self) -> None:
        self._calls.append(("close",))


class RecordingPersistencePort:
    """The injected port: records every call calibration makes through it."""

    def __init__(self) -> None:
        self.store: dict[type, list[Any]] = {}
        self.calls: list[tuple[Any, ...]] = []
        self._models = {
            ("models", "NojinFieldTrialDB"): FakeTrialRow,
            ("models", "NojinCalibrationRecordDB"): FakeCalibrationRecordRow,
        }

    def get_session_factory(self) -> Any:
        self.calls.append(("get_session_factory",))
        return lambda: FakeSession(self.store, self.calls)

    def get_model_attr(self, module: str, name: str) -> Any:
        self.calls.append(("get_model_attr", module, name))
        return self._models[(module, name)]

    def seed_trials(self, rows: list[dict[str, Any]]) -> None:
        """Load trial rows straight into the store (not part of the port API)."""
        session = FakeSession(self.store, [])
        for row in rows:
            session.add(FakeTrialRow(**row))
        session.commit()


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{PROJECT_ROOT}{os.pathsep}{existing}" if existing else str(PROJECT_ROOT)
    )
    env.setdefault("SECRET_KEY", "test-secret-key")
    return env


# ── numerical parity ──────────────────────────────────────────────────────────


def test_calibration_numbers_match_the_pre_injection_baseline():
    """The optimiser output is pinned to the pre-injection run, bit for bit."""
    port = RecordingPersistencePort()
    port.seed_trials(TRIAL_ROWS)

    result = calibration.calibrate_formulation_model(
        FORMULATION_ID,
        TRIAL_IDS,
        MODEL_VERSION,
        port=port,
    )

    assert result["updated_parameters"] == PINNED_PARAMETERS
    assert result["calibration_quality_score"] == PINNED_QUALITY_SCORE
    assert result["formulation_id"] == FORMULATION_ID
    assert result["model_version"] == MODEL_VERSION
    assert result["trial_ids_used"] == TRIAL_IDS


def test_load_calibrated_model_round_trips_the_pinned_baseline():
    """The read-back path reproduces what was written, unchanged by the port."""
    port = RecordingPersistencePort()
    port.seed_trials(TRIAL_ROWS)

    calibration.calibrate_formulation_model(
        FORMULATION_ID,
        TRIAL_IDS,
        MODEL_VERSION,
        port=port,
    )
    loaded = calibration.load_calibrated_model(FORMULATION_ID, port=port)

    assert loaded["parameters"] == PINNED_PARAMETERS
    assert loaded["quality_score"] == PINNED_QUALITY_SCORE
    assert loaded["model_version"] == MODEL_VERSION


def test_legacy_session_factory_argument_still_works():
    """A caller that injects only a session factory keeps the same result."""
    port = RecordingPersistencePort()
    port.seed_trials(TRIAL_ROWS)
    port_factory = port.get_session_factory()

    used: list[int] = []

    def counting_factory() -> Any:
        used.append(1)
        return port_factory()

    result = calibration.calibrate_formulation_model(
        FORMULATION_ID,
        TRIAL_IDS,
        MODEL_VERSION,
        session_factory=counting_factory,
        port=port,
    )

    assert used, "the caller's session factory must produce the session"
    assert result["updated_parameters"] == PINNED_PARAMETERS
    assert result["calibration_quality_score"] == PINNED_QUALITY_SCORE


def test_default_port_is_the_in_process_adapter():
    """No port injected: the in-process default reproduces the pinned numbers."""
    port = default_calibration_port()
    factory = port.get_session_factory()
    trial_row = port.get_model_attr("models", "NojinFieldTrialDB")

    session = factory()
    for row in TRIAL_ROWS:
        session.add(trial_row(**row))
    session.commit()
    session.close()

    result = calibration.calibrate_formulation_model(
        "FORM-DEFAULT",
        TRIAL_IDS,
        MODEL_VERSION,
    )
    loaded = calibration.load_calibrated_model("FORM-DEFAULT")

    assert result["updated_parameters"] == PINNED_PARAMETERS
    assert result["calibration_quality_score"] == PINNED_QUALITY_SCORE
    assert loaded["parameters"] == PINNED_PARAMETERS
    assert loaded["quality_score"] == PINNED_QUALITY_SCORE


# ── the port is the only persistence collaborator ─────────────────────────────


def test_injected_port_receives_every_persistence_call():
    """Row classes, session factory, reads, the write and the commit."""
    port = RecordingPersistencePort()
    port.seed_trials(TRIAL_ROWS)

    calibration.calibrate_formulation_model(
        FORMULATION_ID,
        TRIAL_IDS,
        MODEL_VERSION,
        port=port,
    )
    calibration.load_calibrated_model(FORMULATION_ID, port=port)

    assert ("get_model_attr", "models", "NojinFieldTrialDB") in port.calls
    assert ("get_model_attr", "models", "NojinCalibrationRecordDB") in port.calls
    assert ("get_session_factory",) in port.calls
    assert ("query", "FakeTrialRow") in port.calls
    assert ("query", "FakeCalibrationRecordRow") in port.calls
    assert ("add", "FakeCalibrationRecordRow") in port.calls
    assert ("commit",) in port.calls
    assert ("close",) in port.calls


def test_port_protocol_is_structural():
    """The protocol is satisfied by the in-process adapter and the fake port."""
    assert isinstance(RecordingPersistencePort(), CalibrationPersistencePort)
    assert isinstance(InProcessCalibrationPort(), CalibrationPersistencePort)


def test_default_port_is_cached_and_rejects_unknown_names():
    assert default_calibration_port() is default_calibration_port()

    port = InProcessCalibrationPort()
    with pytest.raises(AttributeError):
        port.get_model_attr("models", "NojinUnknownRecordDB")
    with pytest.raises(AttributeError):
        port.get_model_attr("hub", "NojinFieldTrialDB")


# ── behaviour the refactor must not change ────────────────────────────────────


def test_no_trial_data_raises_value_error():
    port = RecordingPersistencePort()

    with pytest.raises(ValueError, match="No trial data found"):
        calibration.calibrate_formulation_model(
            "FORM-EMPTY",
            ["T-MISSING"],
            MODEL_VERSION,
            port=port,
        )


def test_insufficient_data_after_filtering_raises_value_error():
    """Trials with no statistical_analysis / post_application_data are dropped.

    The columns are present but NULL - the shape a mapped row has when the
    service never filled them - which is falsy and therefore filtered out by
    the same branch as before.
    """
    port = RecordingPersistencePort()
    port.seed_trials(
        [
            {
                "id": "T-BARE",
                "dosage_kg_ha": 10.0,
                "baseline_data": {"soil_ph": 7.0},
                "yield_response": 1.0,
                "statistical_analysis": None,
                "post_application_data": None,
            }
        ]
    )

    with pytest.raises(ValueError, match="Insufficient data"):
        calibration.calibrate_formulation_model(
            "FORM-BARE",
            ["T-BARE"],
            MODEL_VERSION,
            port=port,
        )


def test_load_returns_defaults_when_no_record_exists():
    port = RecordingPersistencePort()

    loaded = calibration.load_calibrated_model("FORM-NEVER-CALIBRATED", port=port)

    assert loaded == {
        "formulation_id": "FORM-NEVER-CALIBRATED",
        "model_version": "default",
        "parameters": None,
        "quality_score": 0.0,
        "last_calibration_date": None,
    }


# ── import cleanliness ────────────────────────────────────────────────────────


def test_engine_calibration_modules_do_not_import_database():
    """No ``database`` import statement, module-level or deferred, in either."""
    for path in (CALIBRATION_PATH, BRIDGE_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders.extend(
                    alias.name
                    for alias in node.names
                    if alias.name.split(".")[0] == "database"
                )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] == "database":
                    offenders.append(node.module)
        assert offenders == [], f"{path.name} still imports database.*: {offenders}"


def test_importing_calibration_adds_no_database_module():
    """B-2's import-cleanliness claim, measured as a delta in a subprocess.

    The parent package is imported first, so the delta isolates this module's
    own contribution: importing ``engine.hydroma.biofertilizer.calibration``
    (and with it ``persistence_bridge``) must not add a single ``database``
    module to ``sys.modules``.
    """
    code = (
        "import sys\n"
        "import engine.hydroma.biofertilizer\n"
        "before = set(sys.modules)\n"
        "import engine.hydroma.biofertilizer.calibration\n"
        "new = sorted(\n"
        "    m for m in set(sys.modules) - before\n"
        "    if m.split('.')[0] == 'database'\n"
        ")\n"
        "print(','.join(new))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=_subprocess_env(),
        check=False,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "", (
        "importing calibration pulled in database modules: " f"{out.stdout.strip()}"
    )


def test_fresh_interpreter_import_still_reports_the_models_bridge():
    """Known state: a fresh interpreter prints ``True`` for ``database`` in
    ``sys.modules`` - and the reason is not this module.

    ``import engine.hydroma.biofertilizer.calibration`` first executes the
    package ``__init__``, which imports ``.models``, whose module-scope
    ``from database.base import Base`` is the second ``ENGINE_NO_DATABASE``
    bridge entry (the one B-2 marks ``pending-removal`` but must not delete
    yet). This pin records that measured state so removing it later - when
    ``models`` is port-injected too - is a deliberate, visible edit that fails
    here until the expectation is updated to ``"False"``.
    """
    code = (
        "import sys; "
        "import engine.hydroma.biofertilizer.calibration as c; "
        'print("database" in sys.modules)'
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=_subprocess_env(),
        check=False,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "True"
