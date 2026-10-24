"""Contract tests for the raw-data sidecar contract (spec §4.2 / §4.6).

The contract itself lives in ``engine/data/meta_contract.py``; these tests pin
the three properties that make it a contract rather than a suggestion: a
missing *required* field blocks, a missing *recommended* field does not, and a
checksum is checked for shape rather than trusted. ``test_example_*`` reads the
committed example sidecar ``tests/reference_data/fao56_examples.meta.json`` and
compares its recorded checksum against the real bytes of
``fao56_examples.csv``, so the example cannot drift from the file it describes.

The published reference values themselves are not re-derived here — that is
``engine/tests/test_fao56_example18.py``, which reads the same CSV.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.data.meta_contract import (
    build_meta,
    meta_path_for,
    sha256_of,
    validate_meta,
    validate_meta_detailed,
)

REFERENCE_DIR = Path(__file__).resolve().parents[2] / "tests" / "reference_data"
REPO_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = REFERENCE_DIR / "fao56_examples.csv"
META_PATH = REFERENCE_DIR / "fao56_examples.meta.json"

#: Format-valid stand-in for a real content hash in synthetic records.
_SHA256_PLACEHOLDER = "a" * 64


def _minimal_meta(**overrides: Any) -> dict[str, Any]:
    """A record carrying every §4.6 required field and nothing else."""
    meta: dict[str, Any] = {
        "dataset_id": "fao56_examples",
        "dataset_version": "1.0",
        "source_id": "FAO56_EXAMPLE18",
        "variable": "reference_evapotranspiration_inputs",
        "unit": "mm/day",
        "content_hash": _SHA256_PLACEHOLDER,
    }
    meta.update(overrides)
    return meta


def test_required_fields_enforced() -> None:
    """A missing required field is an error, and it names the field."""
    meta = _minimal_meta()
    del meta["unit"]

    problems = validate_meta(meta)

    assert len(problems) == 1
    assert "unit" in problems[0]


def test_required_field_with_none_value_is_an_error() -> None:
    """A required field present but null is still a broken record."""
    problems = validate_meta(_minimal_meta(variable=None))

    assert len(problems) == 1
    assert "variable" in problems[0]


def test_recommended_missing_is_warning_not_error() -> None:
    """Omitting recommended fields yields no errors, only warnings."""
    meta = _minimal_meta()

    assert validate_meta(meta) == []

    detailed = validate_meta_detailed(meta)
    assert detailed, "a record with no recommended fields should still be reported"
    assert all(problem.severity == "warn" for problem in detailed)
    assert any(problem.field == "license" for problem in detailed)


def test_checksum_format() -> None:
    """A content hash that is not 64 lowercase hex characters is an error."""
    problems = validate_meta(_minimal_meta(content_hash="not-a-sha256"))
    assert len(problems) == 1
    assert "content_hash" in problems[0]

    uppercase = validate_meta(_minimal_meta(content_hash="A" * 64))
    assert len(uppercase) == 1
    assert "content_hash" in uppercase[0]


def test_sidecar_naming() -> None:
    """The documented convention is ``<path>.meta.json``, idempotently."""
    assert meta_path_for("data/raw/climate/x.tif") == Path(
        "data/raw/climate/x.tif.meta.json"
    )
    assert meta_path_for(Path("data/raw/soil/y.csv")).name == "y.csv.meta.json"
    assert meta_path_for("data/raw/climate/x.tif.meta.json") == Path(
        "data/raw/climate/x.tif.meta.json"
    )


def test_example_file_validates() -> None:
    """The committed example sidecar has no blocking problems."""
    with META_PATH.open(encoding="utf-8") as handle:
        meta = json.load(handle)

    assert validate_meta(meta) == []


def test_example_sidecar_checksum_matches_the_reference_csv() -> None:
    """The example records the real sha256 of the file it describes."""
    with META_PATH.open(encoding="utf-8") as handle:
        meta = json.load(handle)

    assert meta["checksum_sha256"] == sha256_of(CSV_PATH)
    assert meta["local_path"] == CSV_PATH.relative_to(REPO_ROOT).as_posix()


def test_build_meta_omits_fields_the_caller_did_not_supply() -> None:
    """Nothing is invented: unset optional fields stay out of the record."""
    meta = build_meta(
        dataset_id="fao56_examples",
        source="FAO56_EXAMPLE18",
        variable="reference_evapotranspiration_inputs",
        unit="mm/day",
        content_hash=_SHA256_PLACEHOLDER,
    )

    assert meta["source_id"] == "FAO56_EXAMPLE18"
    assert "license" not in meta
    assert "retrieved_at" not in meta
    assert "temporal_resolution" not in meta

    problems = validate_meta(meta)
    assert len(problems) == 1
    assert "dataset_version" in problems[0]


def test_build_meta_validates_when_the_required_version_is_supplied() -> None:
    """With ``dataset_version`` supplied the record validates error-free."""
    meta = build_meta(
        dataset_id="fao56_examples",
        source="FAO56_EXAMPLE18",
        variable="reference_evapotranspiration_inputs",
        unit="mm/day",
        content_hash=_SHA256_PLACEHOLDER,
        dataset_version="1.0",
        temporal_resolution="daily",
        license=None,
    )

    assert meta["temporal_resolution"] == "daily"
    assert "license" not in meta, "a None value must be dropped, not written"
    assert validate_meta(meta) == []
