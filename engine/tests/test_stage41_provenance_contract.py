"""Stage 41 — provenance contract regression for the Stage 40/41 result types.

The repository requires every result dataclass to be able to say where
its numbers came from (``engine/strict_tests/test_s15_provenance.py``).
The Stage 40 and Stage 41 result types were added without that field and
were failing the sweep; this test pins the fix so the contract cannot
regress silently.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

from engine.hydroma.eval.identifiability_calibration import (  # noqa: E402
    FoldResult,
    SeasonProfile,
)
from engine.hydroma.eval.resumable_benchmark_runner import (  # noqa: E402
    RecordResult,
)
from engine.hydroma.eval.seasonal_predictor import OperationalReport  # noqa: E402

#: The Stage 40/41 result types and the label each one carries.
RESULT_TYPES = (
    SeasonProfile,
    FoldResult,
    RecordResult,
    OperationalReport,
)


@pytest.mark.parametrize("cls", RESULT_TYPES, ids=lambda c: c.__name__)
def test_result_type_declares_a_data_source(cls) -> None:
    """Every Stage 40/41 result type must be able to say where it came from."""
    import dataclasses

    fields = {f.name: f for f in dataclasses.fields(cls)}
    assert "data_source" in fields, (
        f"{cls.__name__} returns numbers but cannot say where they came from"
    )
    assert fields["data_source"].type in (str, "str")


@pytest.mark.parametrize("cls", RESULT_TYPES, ids=lambda c: c.__name__)
def test_data_source_is_truthful_not_a_placeholder(cls) -> None:
    """The label must name the real origin, not a generic placeholder."""
    import dataclasses

    default = next(
        f.default for f in dataclasses.fields(cls) if f.name == "data_source"
    )
    assert isinstance(default, str)
    assert default and default not in ("simulated", "unknown", "test", "n/a")
    assert "cimmyt" in default or "engine" in default, (
        f"{cls.__name__}.data_source = {default!r} does not name the origin"
    )


def test_season_profile_default_names_the_cimmyt_field_season() -> None:
    assert SeasonProfile.__dataclass_fields__["data_source"].default == (
        "cimmyt_wheat_field_season"
    )


def test_fold_result_default_names_the_development_districts() -> None:
    assert FoldResult.__dataclass_fields__["data_source"].default == (
        "cimmyt_wheat_development_districts"
    )


def test_record_result_default_names_the_test_districts() -> None:
    assert RecordResult.__dataclass_fields__["data_source"].default == (
        "cimmyt_wheat_test_districts"
    )


def test_provenance_sweep_finds_no_stage40_or_41_result_type() -> None:
    """The repository sweep must not flag any Stage 40/41 result type.

    This is the same check ``engine/strict_tests/test_s15_provenance.py``
    performs, restricted to the modules this stage owns.
    """
    import ast

    owned = (
        "engine/hydroma/eval/identifiability_calibration.py",
        "engine/hydroma/eval/resumable_benchmark_runner.py",
        "engine/hydroma/eval/seasonal_predictor.py",
    )
    root = Path("D:/HyDroMA")
    flagged: list[str] = []
    for rel in owned:
        tree = ast.parse((root / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            body = ast.get_source_segment((root / rel).read_text(encoding="utf-8"), node)
            if body is None:
                continue
            if not re.search(r"@dataclass", body):
                continue
            has_field = bool(re.search(r"^\s+data_source\s*:", body, re.M))
            has_base = bool(
                re.search(
                    r"class\s+\w+\s*\(\s*(?:Result|Simulation)Provenance\s*,", body
                )
            )
            has_carrier = bool(
                re.search(r"class\s+\w+\s*\(\s*ProvenanceCarrier\s*\)", body)
            )
            if not (has_field or has_base or has_carrier):
                flagged.append(f"{rel}::{node.name}")

    assert not flagged, f"result types without a provenance field: {flagged}"
