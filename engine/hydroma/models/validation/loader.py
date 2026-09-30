"""Loader for the shipped validation corpus.

``engine/hydroma/models/validation/`` contains 10 YAML case files and 18 ``.npy``
reference values that were written with citations but never wired to anything --
``__init__.py`` was a single docstring line and no module imported
``reference_data``, read a YAML file, or loaded a ``.npy``.

This module is the missing loader. It deliberately does *not* report a single
pass/fail verdict, because a number of the stored expectations are internally
inconsistent. Running them against the implementations and reporting only a
boolean would invite the wrong response: changing a correct implementation to
match an expectation that cannot be satisfied.

Two distinct verdicts are therefore separated:

``match``
    The implementation agrees with a value that is itself reproducible from a
    cited equation.
``inconsistent_case``
    The case's own inputs and expected intermediates contradict each other, so
    no correct implementation can satisfy it. Reported with the contradiction,
    not as a code failure.

See ``runner.py`` for the comparison itself.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

VALIDATION_DIR = Path(__file__).resolve().parent
CASE_DIR = VALIDATION_DIR / "test_cases"
REFERENCE_DIR = VALIDATION_DIR / "reference_profiles"


@dataclass(frozen=True)
class ValidationCase:
    """One case from a YAML file, with its file-level metadata."""

    model: str
    name: str | None = None
    description: str | None = None
    inputs: dict[str, Any] | None = None
    expected: dict[str, Any] | None = None
    tolerances: dict[str, Any] | None = None
    reference: str | None = None
    language: str | None = None
    status: str | None = None
    source: Path | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@functools.lru_cache(maxsize=1)
def _case_files() -> tuple[Path, ...]:
    return tuple(sorted(CASE_DIR.glob("*.yaml")))


@functools.lru_cache(maxsize=1)
def load_all_cases() -> tuple[ValidationCase, ...]:
    """Every case in the corpus, flattened across files."""
    cases: list[ValidationCase] = []
    for path in _case_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        meta = {
            "model": doc.get("model", path.stem),
            "tolerances": doc.get("tolerances", {}) or {},
            "reference": doc.get("reference", ""),
            "language": doc.get("language", ""),
            "status": doc.get("status", ""),
        }
        for case in doc.get("cases", []) or []:
            cases.append(
                ValidationCase(
                    model=meta["model"],
                    name=case.get("name", "unnamed"),
                    description=case.get("description", ""),
                    inputs=case.get("inputs", {}) or {},
                    expected=case.get("expected", {}) or {},
                    tolerances=meta["tolerances"],
                    reference=meta["reference"],
                    language=meta["language"],
                    status=meta["status"],
                    source=path,
                    raw=case,
                )
            )
    return tuple(cases)


def load_cases(model: str) -> tuple[ValidationCase, ...]:
    return tuple(c for c in load_all_cases() if c.model == model)


def case_names() -> tuple[str, ...]:
    return tuple(f"{c.model}/{c.name}" for c in load_all_cases())


@functools.lru_cache(maxsize=1)
def available_references() -> dict[str, Path]:
    """The ``.npy`` reference values, by stem.

    The directory is named ``reference_profiles`` but these are scalars or short
    series, not profiles. The loader reports the real shape so a caller is not
    misled by the name.
    """
    return {p.stem: p for p in sorted(REFERENCE_DIR.glob("*.npy"))}


def load_reference(name: str) -> np.ndarray:
    """Load one reference value by stem. Returns a 1-D array."""
    path = available_references().get(name)
    if path is None:
        raise KeyError(f"no reference named {name!r}; have {sorted(available_references())}")
    return np.load(path).ravel()


def reference_metadata() -> dict[str, dict[str, Any]]:
    """Shape/dtype/range for every stored reference, for reporting."""
    out: dict[str, dict[str, Any]] = {}
    for name, path in available_references().items():
        arr = np.load(path)
        out[name] = {
            "shape": tuple(arr.shape),
            "size": int(arr.size),
            "dtype": str(arr.dtype),
            "min": float(arr.min()),
            "max": float(arr.max()),
        }
    return out


def corpus_summary() -> dict[str, Any]:
    cases = load_all_cases()
    return {
        "case_files": len(_case_files()),
        "cases": len(cases),
        "references": len(available_references()),
        "by_model": {
            model: sum(1 for c in cases if c.model == model)
            for model in sorted({c.model for c in cases})
        },
        "claimed_status": {
            status: sum(1 for c in cases if c.status == status)
            for status in sorted({c.status for c in cases})
        },
    }


def expand_repeats(value: Any) -> Any:
    """Expand the corpus's compact constant-series form into a list.

    Two of the case files were written with Python slice syntax
    (``et0_mm: [3.5]*226``), which is not valid YAML and made the whole file
    unparseable -- the most likely reason the corpus was never loaded. Those lines
    are now ``{value: 3.5, repeat: 226}``, which is valid and self-describing.
    This turns it back into the list the case author meant.
    """
    if isinstance(value, dict):
        if "value" in value and "repeat" in value:
            return [value["value"]] * int(value["repeat"])
        return {k: expand_repeats(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_repeats(v) for v in value]
    return value


def expand_case(case: ValidationCase) -> ValidationCase:
    """A copy of ``case`` with compact series expanded in both inputs and expected."""
    return ValidationCase(
        model=case.model,
        name=case.name,
        description=case.description,
        inputs=expand_repeats(case.inputs),
        expected=expand_repeats(case.expected),
        tolerances=case.tolerances,
        reference=case.reference,
        language=case.language,
        status=case.status,
        source=case.source,
        raw=expand_repeats(case.raw),
    )
