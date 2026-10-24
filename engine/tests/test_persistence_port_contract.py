"""Contract tests for the spec §4.5 ``PersistencePort`` ABC.

Locks in the W3-3 deliverable: the abstract persistence contract from
section ۴.۵ of ``docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`` now lives at
its spec-mandated path, ``engine/ports/persistence_port.py``.

Covered:

* the ABC declares exactly the eleven spec abstract methods,
* it cannot be instantiated directly,
* the Wave-2 SQLite adapter (``adapters.persistence.sqlite_persistence``)
  satisfies the spec ABC and round-trips a dataset and an evidence item,
* the pre-existing production ``Protocol`` in ``engine.ports.persistence``
  still imports and still accepts the in-memory implementation — the two
  contracts coexist,
* the import-guard entry point (``import engine``) stays clean.

Every test uses a temporary database (``tmp_path``) — never the
repository's ``data/`` directory.
"""

from __future__ import annotations

import importlib
from abc import ABCMeta

import pytest

from adapters.persistence.sqlite_persistence import SQLitePersistence
from engine.ports.persistence_port import PersistencePort

SPEC_METHODS = (
    "save_dataset",
    "get_dataset",
    "save_model_run",
    "get_model_run",
    "save_evidence",
    "get_evidence",
    "save_claim",
    "link_evidence_to_claim",
    "get_claim_evidence",
    "save_scenario",
    "save_decision",
)


# ── the ABC itself ───────────────────────────────────────────────────────────


def test_abc_has_spec_methods():
    """The ABC declares exactly the eleven spec §4.۵ abstract methods."""
    assert isinstance(PersistencePort, ABCMeta)

    abstract = set(PersistencePort.__abstractmethods__)
    assert abstract == set(SPEC_METHODS)

    for name in SPEC_METHODS:
        assert getattr(PersistencePort, name).__isabstractmethod__ is True


def test_abc_cannot_instantiate():
    """An ABC whose methods are all abstract cannot be instantiated."""
    with pytest.raises(TypeError):
        PersistencePort()


# ── the adapter satisfies the spec port ──────────────────────────────────────


def test_adapter_satisfies_spec_port(tmp_path):
    adapter = SQLitePersistence(str(tmp_path / "spec-port.db"))

    assert isinstance(adapter, PersistencePort)

    dataset_id = adapter.save_dataset(
        {
            "dataset_id": "ds-port-test",
            "dataset_version": "v1",
            "source_id": "src-port-test",
            "variable": "precipitation",
            "unit": "mm",
        }
    )
    assert dataset_id == "ds-port-test"
    dataset = adapter.get_dataset(dataset_id)
    assert dataset is not None
    assert dataset["dataset_id"] == dataset_id
    assert dataset["dataset_version"] == "v1"
    assert dataset["variable"] == "precipitation"
    assert dataset["unit"] == "mm"

    evidence_id = adapter.save_evidence(
        {
            "evidence_id": "ev-port-test",
            "evidence_type": "MEASUREMENT",
            "source_dataset_id": dataset_id,
            "value": 42.0,
            "unit": "mm",
        }
    )
    assert evidence_id == "ev-port-test"
    evidence = adapter.get_evidence(evidence_id)
    assert evidence is not None
    assert evidence["evidence_id"] == evidence_id
    assert evidence["evidence_type"] == "MEASUREMENT"
    assert evidence["value"] == pytest.approx(42.0)
    assert evidence["source_dataset_id"] == dataset_id

    assert adapter.get_dataset("ds-missing") is None
    assert adapter.get_evidence("ev-missing") is None


# ── coexistence with the pre-existing production Protocol ────────────────────


def test_coexist_old_protocol():
    from engine.ports.persistence import PersistencePort as LegacyPort
    from engine.ports.persistence_impl import InMemoryPersistence

    # The legacy production contract still imports ...
    assert LegacyPort.__name__ == "PersistencePort"
    # ... and is a runtime_checkable Protocol the in-memory impl satisfies.
    assert isinstance(InMemoryPersistence(), LegacyPort)

    # The two contracts coexist: same class name, different objects and
    # different method surfaces, each in its own module.
    assert LegacyPort is not PersistencePort
    assert hasattr(LegacyPort, "get_sqlite")
    assert not hasattr(PersistencePort, "get_sqlite")
    assert hasattr(PersistencePort, "save_dataset")
    assert not hasattr(LegacyPort, "save_dataset")


# ── import guard ─────────────────────────────────────────────────────────────


def test_import_guard_clean():
    """The module-level scan entry point (``python -c "import engine"``)."""
    assert importlib.import_module("engine") is not None
    assert importlib.import_module("engine.ports") is not None
    assert importlib.import_module("engine.ports.persistence") is not None
    assert importlib.import_module("engine.ports.persistence_port") is not None

    # The new module exposes exactly the spec ABC and nothing else.
    assert importlib.import_module("engine.ports.persistence_port").__all__ == [
        "PersistencePort"
    ]
