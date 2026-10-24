"""Governance record of the Decision Engine's default weights (ECO-13, brake 8).

Covers ``decision/weights.yaml`` and the additive loader
``engine/tasmimyar/weights_loader.py``:

* ``test_yaml_loads_and_validates`` -- the record loads, carries schema
  version "1.0.0", and holds exactly the three criteria with numeric
  weight/threshold and a direction string;
* ``test_matches_engine_defaults`` -- the record faithfully describes the
  engine's *current* hardcoded defaults, so brake 8's tripwire
  (``matches_engine_defaults``) is True on a clean tree;
* ``test_drift_detected`` -- moving ``evidence_count`` to weight 0.9 in a
  temp YAML breaks that agreement (brake 8: "تغییر وزن‌های تصمیم‌یار بدون
  مجوز صریح ممنوع");
* ``test_verdict_bands_present`` -- the four verdict bands are documented,
  with the note that the threshold gate is enforced only in engine code.

The Decision Engine (``engine/tasmimyar/__init__.py``) is never edited or
patched here; it is imported only to *read* its defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]  # PyYAML ships no type hints in this env

from engine.tasmimyar.weights_loader import (
    EXPECTED_CRITERIA,
    default_criteria,
    load_weights,
    matches_engine_defaults,
)


def _engine_criteria() -> list[Any]:
    """The Decision Engine's current hardcoded defaults (read-only)."""
    from engine.tasmimyar import DecisionEngine

    return list(DecisionEngine()._default_criteria)


def _compare(recorded: list[dict[str, Any]], engine: list[Any]) -> bool:
    """Inline record-vs-engine comparison, mirroring the loader's tripwire."""
    if len(recorded) != len(engine):
        return False
    for y, e in zip(recorded, engine, strict=True):
        if (
            y["name"] != e.name
            or float(y["weight"]) != float(e.weight)
            or float(y["threshold"]) != float(e.threshold)
            or y["direction"] != e.direction
        ):
            return False
    return True


def test_yaml_loads_and_validates() -> None:
    data = load_weights()
    assert data["schema_version"] == "1.0.0"
    assert data["owner"] == "Tasmimyar / Decision Engine"

    criteria = data["default_criteria"]
    assert isinstance(criteria, list)
    assert [c["name"] for c in criteria] == list(EXPECTED_CRITERIA)

    for criterion in criteria:
        assert set(criterion) == {"name", "weight", "threshold", "direction"}
        assert isinstance(criterion["name"], str)
        assert isinstance(criterion["weight"], (int, float))
        assert not isinstance(criterion["weight"], bool)
        assert isinstance(criterion["threshold"], (int, float))
        assert not isinstance(criterion["threshold"], bool)
        assert isinstance(criterion["direction"], str)


def test_matches_engine_defaults() -> None:
    """The YAML faithfully records the engine's current behaviour.

    If this ever fails, someone changed a weight on one side only: per
    brake 8, STOP and reconcile with an explicit user mandate.
    """
    assert matches_engine_defaults() is True
    assert _compare(default_criteria(), _engine_criteria()) is True


def test_drift_detected(tmp_path: Path) -> None:
    drifted = load_weights()
    criteria = [dict(c) for c in drifted["default_criteria"]]
    assert criteria[0]["name"] == "evidence_count"
    criteria[0]["weight"] = 0.9  # the engine records 0.3; changing it needs a mandate
    drifted["default_criteria"] = criteria

    drifted_path = tmp_path / "weights.yaml"
    drifted_path.write_text(yaml.safe_dump(drifted, allow_unicode=True), encoding="utf-8")

    # The same comparison still agrees on the untouched record ...
    assert _compare(default_criteria(), _engine_criteria()) is True
    # ... but the drifted record no longer does, inline and via the tripwire.
    assert _compare(criteria, _engine_criteria()) is False
    assert matches_engine_defaults(str(drifted_path)) is False


def test_verdict_bands_present() -> None:
    bands = load_weights()["verdict_bands"]
    assert bands["insufficient_evidence"]["condition"] == "confidence < 0.2"
    assert bands["recommend"]["condition"] == "score >= 0.7"
    assert bands["caution"]["condition"] == "score >= 0.4"
    assert bands["reject"]["condition"] == "otherwise"

    note = bands["threshold_gate"]["note"].lower()
    assert "enforced only" in note
