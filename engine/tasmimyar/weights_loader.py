"""Governance loader for ``decision/weights.yaml`` (spec ECO-13, brake 8).

The Decision Engine's default criteria weights are hardcoded in
``engine/tasmimyar/__init__.py`` (``DecisionEngine._default_criteria``:
evidence_count 0.3 / evidence_quality 0.4 / confidence 0.3, thresholds
0.5 / 0.6 / 0.5, direction maximize). This module is purely additive: it
READS the governance record those values now live in (``decision/
weights.yaml``) and provides the brake-8 drift tripwire. It does not
replace, wrap, or monkey-patch the DecisionEngine defaults, and it changes
nothing about the engine's behaviour or public API.

``decision/weights.yaml`` is now the governance record of the weights. Any
change to those weights -- here or in the engine -- requires an explicit
user mandate: "تغییر وزن‌های تصمیم‌یار بدون مجوز صریح ممنوع" (spec brake 8:
"اگر وزن‌های Tasmimyar تغییر می‌کند، متوقف شو."). ``matches_engine_defaults``
is the mechanical tripwire for that brake: it returns ``False`` the moment
the YAML record and the engine's hardcoded defaults disagree in any field.

Migrating the DecisionEngine to consume this loader is a Wave-3 decision
(brake 2/8); nothing in this module performs that migration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]  # PyYAML ships no type hints in this env

#: Default location of the governance record, relative to the repository root.
DEFAULT_WEIGHTS_PATH = "decision/weights.yaml"

#: The only schema version this loader accepts.
SUPPORTED_SCHEMA_VERSION = "1.0.0"

#: The exact criterion names the Decision Engine hardcodes today, in order.
EXPECTED_CRITERIA: tuple[str, ...] = (
    "evidence_count",
    "evidence_quality",
    "confidence",
)

#: The four documented verdict bands.
VERDICT_BANDS: tuple[str, ...] = (
    "insufficient_evidence",
    "recommend",
    "caution",
    "reject",
)


def _resolve_weights_path(path: str | Path) -> Path:
    """Resolve *path* against the repository root.

    A relative path is walked up from this file (``engine/tasmimyar/``)
    until a directory containing it is found, so the resolution works for
    any checkout layout -- no drive letters are hardcoded. Absolute paths
    are used as-is; a relative path that is not found anywhere above this
    file falls back to the current working directory before failing.
    """
    given = Path(path)
    if given.is_absolute():
        if given.is_file():
            return given
        raise FileNotFoundError(f"weights file not found: {given}")

    here = Path(__file__).resolve()
    for base in here.parents:
        candidate = base / given
        if candidate.is_file():
            return candidate

    from_cwd = Path.cwd() / given
    if from_cwd.is_file():
        return from_cwd

    searched = " > ".join(str(base) for base in here.parents)
    raise FileNotFoundError(
        f"weights file {given} not found: searched {searched} and the working "
        f"directory {Path.cwd()}"
    )


def _validate(data: Any) -> dict[str, Any]:
    """Validate the parsed record; raise ``ValueError`` on any drift.

    Drift means: an unsupported schema version, criterion names or counts
    that no longer match the engine's three default criteria, wrong field
    types, or missing verdict bands. The record is only trustworthy if it
    keeps describing the engine exactly.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"{DEFAULT_WEIGHTS_PATH}: top level must be a mapping, "
            f"got {type(data).__name__}"
        )

    version = data.get("schema_version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"{DEFAULT_WEIGHTS_PATH}: unsupported schema_version {version!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION!r}"
        )

    criteria = data.get("default_criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError(
            f"{DEFAULT_WEIGHTS_PATH}: 'default_criteria' must be a non-empty list"
        )

    names = [c.get("name") if isinstance(c, dict) else None for c in criteria]
    if names != list(EXPECTED_CRITERIA):
        raise ValueError(
            f"{DEFAULT_WEIGHTS_PATH}: 'default_criteria' names {names} do not "
            f"match the engine's criteria {list(EXPECTED_CRITERIA)}"
        )

    for criterion in criteria:
        for field_name in ("weight", "threshold"):
            value = criterion.get(field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"{DEFAULT_WEIGHTS_PATH}: criterion {criterion.get('name')!r} "
                    f"field {field_name!r} must be a number, got {value!r}"
                )
        direction = criterion.get("direction")
        if not isinstance(direction, str) or not direction:
            raise ValueError(
                f"{DEFAULT_WEIGHTS_PATH}: criterion {criterion.get('name')!r} "
                f"field 'direction' must be a non-empty string, got {direction!r}"
            )

    bands = data.get("verdict_bands")
    if not isinstance(bands, dict):
        raise ValueError(f"{DEFAULT_WEIGHTS_PATH}: 'verdict_bands' must be a mapping")
    missing = [band for band in VERDICT_BANDS if band not in bands]
    if missing:
        raise ValueError(f"{DEFAULT_WEIGHTS_PATH}: 'verdict_bands' is missing {missing}")

    return data


def load_weights(path: str | Path = DEFAULT_WEIGHTS_PATH) -> dict[str, Any]:
    """Load and validate the governance record of the decision weights.

    Args:
        path: Location of the YAML record, relative to the repository root
            (resolved by walking up from this file) or absolute.

    Returns:
        The parsed and validated YAML mapping.

    Raises:
        FileNotFoundError: The record cannot be found.
        ValueError: The record does not match the supported schema, the
            three expected criterion names, or their field types -- i.e.
            the file has drifted from the engine's default criteria.
    """
    resolved = _resolve_weights_path(path)
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    return _validate(data)


def default_criteria(path: str | Path = DEFAULT_WEIGHTS_PATH) -> list[dict[str, Any]]:
    """Return the governance-recorded default criteria.

    Each entry carries exactly the four fields the engine's
    ``DecisionCriterion`` uses: ``name``, ``weight``, ``threshold`` and
    ``direction``.
    """
    criteria: list[dict[str, Any]] = load_weights(path)["default_criteria"]
    return criteria


def _criteria_agree(
    recorded: list[dict[str, Any]],
    engine_criteria: list[Any],
) -> bool:
    """Exact field-by-field comparison of the YAML criteria against the engine's."""
    if len(recorded) != len(engine_criteria):
        return False
    for y, actual in zip(recorded, engine_criteria, strict=True):
        if (
            y.get("name") != actual.name
            or float(y.get("weight", 0.0)) != float(actual.weight)
            or float(y.get("threshold", 0.0)) != float(actual.threshold)
            or y.get("direction") != actual.direction
        ):
            return False
    return True


def matches_engine_defaults(path: str | Path = DEFAULT_WEIGHTS_PATH) -> bool:
    """Brake-8 tripwire: does the record match the engine's current defaults?

    Reads the criteria the Decision Engine *currently* hardcodes
    (``engine.tasmimyar.DecisionEngine._default_criteria``) at runtime by
    importing and instantiating the engine -- that is a read; the engine is
    never edited, wrapped or patched -- and compares them field by field
    with the governance record.

    Returns True only on exact agreement of name, weight, threshold and
    direction. A weight changed in the engine without updating
    ``decision/weights.yaml`` (or vice versa) makes this return False, and
    per spec brake 8 ("تغییر وزن‌های تصمیم‌یار بدون مجوز صریح ممنوع") that
    is a stop condition: obtain an explicit user mandate first.
    """
    recorded = default_criteria(path)

    from engine.tasmimyar import DecisionEngine  # local import: read-only use

    return _criteria_agree(recorded, DecisionEngine()._default_criteria)
