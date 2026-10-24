"""Scenario definition, versioning and comparison for ECO-12 (phase 1).

This module is the definition half of ECO-12. It loads versioned scenario
definitions from YAML, validates their shape, diffs two definitions key by
key, and compares a measured numeric snapshot against the recorded
execution baseline in ``engine/baseline/R18.json``.

ECO-12 phase 1 is definition, versioning and comparison ONLY. Executing a
scenario against the models is phase 2 and is deliberately NOT implemented
here: this module makes no engine call, runs no simulation, and imports
nothing from ``engine``. Wiring a scenario definition to the engine gateway
is a decision for phase 2, and nothing in this file may be read as having
made it.

The comparison against ``engine/baseline/R18.json`` is strictly read-only:
the file is opened for reading, and this module never writes to
``engine/baseline/`` (regenerating a recorded baseline is a separate,
explicit decision owned by ``engine/baseline/capture.py --regenerate``).

Standard library plus PyYAML only.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "REQUIRED_KEYS",
    "SEMVER_PATTERN",
    "compare_against_result_snapshot",
    "list_definitions",
    "load_scenario",
    "scenario_diff",
]

#: Keys every scenario definition must carry. The list is the contract: a
#: definition missing one of these is rejected rather than loaded with a
#: silently absent section.
REQUIRED_KEYS: tuple[str, ...] = (
    "scenario_id",
    "scenario_version",
    "baseline_id",
    "spatial_scope",
    "time_horizon",
    "climate_assumptions",
    "land_management",
    "crop_plan",
    "water_allocation",
    "soil_interventions",
    "economic_assumptions",
    "social_constraints",
    "model_versions",
    "dataset_versions",
    "parameter_set_versions",
    "uncertainty_settings",
    "assumptions",
)

#: The official semver pattern (https://semver.org), kept as data so a
#: version is checked rather than eyeballed. A definition whose
#: ``scenario_version`` does not match is rejected.
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?:[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

#: Repository root, from ``<root>/scenario/engine/baseline_manager.py``.
_REPO_ROOT = Path(__file__).resolve().parents[2]

#: Where the recorded execution baseline is looked for, in order. The
#: repo-root-anchored candidate comes first so the module does not depend on
#: the caller's working directory.
_RECORDED_BASELINE_CANDIDATES: tuple[Path, ...] = (
    _REPO_ROOT / "engine" / "baseline" / "R18.json",
    Path("engine/baseline/R18.json"),
)

#: Keys that belong to the recorded-baseline envelope rather than to the
#: case data, so a bare cases mapping handed in as a snapshot is recognised.
_ENVELOPE_KEYS = frozenset(
    {"schema_version", "baseline_id", "case_names", "rel_tolerance"}
)

#: Default definition directory, resolved against the working directory
#: first and the repository root second (see :func:`_resolve_definitions_dir`).
_DEFAULT_DEFINITIONS_DIR = "scenario/definitions"

#: Fallback tolerance when a recorded baseline does not state one. It is
#: the same value ``engine/baseline`` uses (``REL_TOLERANCE = 1e-9``).
_DEFAULT_REL_TOLERANCE = 1e-9

#: Stand-in path for a container that flattens to a leaf of its own.
_LEAF_ROOT = "<root>"


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def load_scenario(path: str | Path) -> dict[str, Any]:
    """Read and validate one scenario definition.

    A definition is a YAML mapping that carries every key in
    :data:`REQUIRED_KEYS`, whose ``scenario_version`` is a valid semver
    string, and whose ``assumptions`` is a non-empty list (ECO-12 DoD:
    فرض‌ها مستند می‌شوند -- the assumptions are documented, so an
    undocumented scenario is not a scenario).

    Args:
        path: YAML file to read.

    Returns:
        The parsed definition, unchanged.

    Raises:
        ValueError: The file is not valid YAML, the document is not a
            mapping, a required key is missing, ``scenario_version`` is not
            semver, or ``assumptions`` is not a non-empty list.
        OSError: The file cannot be read (propagated, not disguised).
    """
    target = Path(path)
    try:
        raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"{target}: not valid YAML ({exc})") from exc

    if raw is None:
        raise ValueError(f"{target}: the file is empty")
    if not isinstance(raw, dict):
        raise ValueError(
            f"{target}: the document must be a mapping, got {type(raw).__name__}"
        )

    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ValueError(
            f"{target}: missing required key(s): {', '.join(missing)}"
        )

    version = raw["scenario_version"]
    if not isinstance(version, str) or SEMVER_PATTERN.fullmatch(version) is None:
        raise ValueError(
            f"{target}: 'scenario_version' must be a semver string "
            f"(e.g. '1.0.0'), got {version!r}"
        )

    assumptions = raw["assumptions"]
    if not isinstance(assumptions, list) or not assumptions:
        raise ValueError(
            f"{target}: 'assumptions' must be a non-empty list; an "
            f"undocumented scenario cannot be diffed against a baseline"
        )

    return raw


def list_definitions(dir: str | Path = _DEFAULT_DEFINITIONS_DIR) -> list[dict[str, Any]]:
    """Every validated scenario definition in a directory.

    ``*.yaml`` and ``*.yml`` files are loaded through :func:`load_scenario`,
    so an unreadable or invalid definition raises instead of being dropped:
    a broken definition in the directory is a real defect, not a file to
    skip quietly.

    Args:
        dir: Directory to scan. Relative paths are tried against the working
            directory first and the repository root second.

    Returns:
        The loaded definitions, sorted by ``scenario_id`` then
        ``scenario_version``. The definitions are returned as parsed, so a
        caller identifies a file by its ``scenario_id`` rather than by a
        path this function does not attach.

    Raises:
        FileNotFoundError: The directory exists in neither location.
        ValueError: A definition in the directory fails validation.
    """
    directory = _resolve_definitions_dir(dir)
    paths = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
    )
    definitions = [load_scenario(path) for path in paths]
    definitions.sort(
        key=lambda definition: (
            str(definition.get("scenario_id")),
            str(definition.get("scenario_version")),
        )
    )
    return definitions


def _resolve_definitions_dir(directory: str | Path) -> Path:
    """Resolve a definitions directory against cwd, then the repo root."""
    given = Path(directory)
    if given.is_dir():
        return given
    anchored = _REPO_ROOT / directory
    if anchored.is_dir():
        return anchored
    raise FileNotFoundError(
        f"scenario definitions directory not found: {given} "
        f"(also tried {anchored})"
    )


# ---------------------------------------------------------------------------
# Baseline comparison (مقایسه با baseline)
# ---------------------------------------------------------------------------


def scenario_diff(baseline: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    """Structured diff of two scenario definitions.

    The result is machine-checkable rather than a rendered text diff. Every
    top-level key is reported as unchanged, changed, added or removed; a
    changed mapping is walked into changed / added / removed sub-keys, and a
    changed list of ``id``-bearing mappings is walked per id, so "what moved
    between these two scenarios" is answerable without reading the YAML.

    ``model_versions`` is additionally reported on its own, per model id:
    a nested-only comparison could hide a single bumped model inside a
    dict that merely "changed", so the per-id entries are listed explicitly
    (changed / added / removed, plus the ids that were compared).

    Args:
        baseline: The baseline definition (usually the one whose
            ``baseline_id`` is null).
        scenario: The derived definition to compare against it.

    Returns:
        A dict with ``fields`` (per top-level key), ``changed_keys``,
        ``added_keys``, ``removed_keys``, ``model_versions`` (per id),
        ``linkage`` (whether ``scenario`` names this baseline), and a
        ``summary``.

    Raises:
        ValueError: Either argument is not a mapping.
    """
    for name, value in (("baseline", baseline), ("scenario", scenario)):
        if not isinstance(value, dict):
            raise ValueError(
                f"{name} must be a mapping of scenario keys, "
                f"got {type(value).__name__}"
            )

    changed: list[str] = []
    added: list[str] = []
    removed: list[str] = []
    fields: dict[str, Any] = {}

    for key, baseline_value in baseline.items():
        if key not in scenario:
            removed.append(key)
            fields[key] = {"status": "removed", "value": baseline_value}
        elif baseline_value != scenario[key]:
            changed.append(key)
            fields[key] = _field_diff(baseline_value, scenario[key])
        else:
            fields[key] = {"status": "unchanged"}

    for key, scenario_value in scenario.items():
        if key not in baseline:
            added.append(key)
            fields[key] = {"status": "added", "value": scenario_value}

    return {
        "baseline": {
            "scenario_id": baseline.get("scenario_id"),
            "scenario_version": baseline.get("scenario_version"),
        },
        "scenario": {
            "scenario_id": scenario.get("scenario_id"),
            "scenario_version": scenario.get("scenario_version"),
        },
        "fields": fields,
        "changed_keys": changed,
        "added_keys": added,
        "removed_keys": removed,
        "model_versions": _model_versions_diff(
            baseline.get("model_versions"), scenario.get("model_versions")
        ),
        "linkage": {
            "baseline_scenario_id": baseline.get("scenario_id"),
            "scenario_baseline_id": scenario.get("baseline_id"),
            "references_baseline": (
                scenario.get("baseline_id") == baseline.get("scenario_id")
            ),
            "note": (
                "True when the derived scenario names the baseline it is "
                "diffed against; a derived scenario that names another "
                "baseline (or none) must not be read as this comparison."
            ),
        },
        "summary": {
            "changed_keys": changed,
            "added_keys": added,
            "removed_keys": removed,
            "changed_count": len(changed),
            "added_count": len(added),
            "removed_count": len(removed),
            "identical": not (changed or added or removed),
        },
    }


def _field_diff(baseline_value: Any, scenario_value: Any) -> dict[str, Any]:
    """The per-key diff entry for one changed top-level key."""
    if isinstance(baseline_value, dict) and isinstance(scenario_value, dict):
        nested = _mapping_diff(baseline_value, scenario_value)
        return {
            "status": "changed",
            "structure": "mapping",
            "changed": nested["changed"],
            "added": nested["added"],
            "removed": nested["removed"],
        }
    if isinstance(baseline_value, list) and isinstance(scenario_value, list):
        list_part = _list_diff(baseline_value, scenario_value)
        if list_part is not None:
            return {
                "status": "changed",
                "structure": "list_of_id_bearers",
                "changed": list_part["changed"],
                "added": list_part["added"],
                "removed": list_part["removed"],
            }
    return {
        "status": "changed",
        "structure": "value",
        "value_change": {"baseline": baseline_value, "scenario": scenario_value},
    }


def _mapping_diff(
    baseline: dict[str, Any], scenario: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Recursive per-key diff of two mappings.

    Only mappings are recursed into, so a scalar or list change is reported
    as a value change and never as a silently collapsed subtree. A changed
    sub-mapping is itself reported per sub-key, which is what makes the
    ``model_versions`` and ``climate_assumptions`` sections readable as a
    list of names rather than one opaque "dict changed".
    """
    changed: dict[str, Any] = {}
    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}

    for key, baseline_value in baseline.items():
        if key not in scenario:
            removed[key] = baseline_value
        elif baseline_value != scenario[key]:
            if isinstance(baseline_value, dict) and isinstance(scenario[key], dict):
                nested = _mapping_diff(baseline_value, scenario[key])
                if nested["changed"] or nested["added"] or nested["removed"]:
                    changed[key] = nested
            else:
                changed[key] = {"baseline": baseline_value, "scenario": scenario[key]}

    for key, scenario_value in scenario.items():
        if key not in baseline:
            added[key] = scenario_value

    return {"changed": changed, "added": added, "removed": removed}


def _list_diff(
    baseline: list[Any], scenario: list[Any]
) -> dict[str, Any] | None:
    """Per-id diff of two lists of ``id``-bearing mappings, else ``None``.

    ``None`` tells the caller to fall back to a whole-value change: a list
    of scalars (or a list whose entries carry no stable id) has no safe
    per-entry alignment, and inventing a positional one would report moves
    that never happened.
    """
    if not _all_id_bearers(baseline) or not _all_id_bearers(scenario):
        return None

    baseline_by_id = {entry["id"]: entry for entry in baseline}
    scenario_by_id = {entry["id"]: entry for entry in scenario}

    changed: dict[str, Any] = {}
    for identifier in sorted(set(baseline_by_id) & set(scenario_by_id)):
        left = baseline_by_id[identifier]
        right = scenario_by_id[identifier]
        if left != right:
            nested = _mapping_diff(left, right)
            changed[str(identifier)] = {
                "baseline": left,
                "scenario": right,
                **{
                    name: value
                    for name, value in nested.items()
                    if value
                },
            }

    added = {
        str(entry["id"]): entry
        for entry in scenario
        if entry["id"] not in baseline_by_id
    }
    removed = {
        str(entry["id"]): entry
        for entry in baseline
        if entry["id"] not in scenario_by_id
    }
    return {"changed": changed, "added": added, "removed": removed}


def _all_id_bearers(entries: list[Any]) -> bool:
    """Whether every entry is a mapping carrying a non-empty ``id``."""
    if not entries:
        return False
    return all(
        isinstance(entry, dict) and entry.get("id") not in (None, "")
        for entry in entries
    )


def _model_versions_diff(baseline: Any, scenario: Any) -> dict[str, Any]:
    """Explicit per-model-id diff of the two ``model_versions`` sections.

    Kept separate from the generic mapping walk so the report names every
    model that was compared and every model whose version moved, instead of
    folding them into a single nested flag a reader has to open to trust.
    """
    if not isinstance(baseline, dict) or not isinstance(scenario, dict):
        return {
            "status": "not_comparable",
            "compared_ids": [],
            "changed": {},
            "added": {},
            "removed": {},
            "baseline": baseline,
            "scenario": scenario,
            "note": (
                "model_versions must be a mapping of model id to version; "
                "these values are not, so no per-model comparison was made."
            ),
        }

    baseline_ids = set(baseline)
    scenario_ids = set(scenario)
    changed = {
        model_id: {"baseline": baseline[model_id], "scenario": scenario[model_id]}
        for model_id in sorted(baseline_ids & scenario_ids)
        if baseline[model_id] != scenario[model_id]
    }
    added = {model_id: scenario[model_id] for model_id in sorted(scenario_ids - baseline_ids)}
    removed = {model_id: baseline[model_id] for model_id in sorted(baseline_ids - scenario_ids)}

    return {
        "status": "changed" if (changed or added or removed) else "unchanged",
        "compared_ids": sorted(baseline_ids & scenario_ids),
        "changed": changed,
        "added": added,
        "removed": removed,
        "note": (
            "Listed per model id by design: a nested-only comparison could "
            "hide one bumped model inside a section that merely 'changed'."
        ),
    }


# ---------------------------------------------------------------------------
# Measured snapshot vs the recorded execution baseline
# ---------------------------------------------------------------------------


def compare_against_result_snapshot(
    scenario: dict[str, Any],
    snapshot: dict[str, Any],
    stored_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare a measured numeric snapshot against the recorded baseline.

    The recorded baseline is ``engine/baseline/R18.json``: a recorded
    execution of the engine's deterministic cases, with the envelope
    ``schema_version`` / ``baseline_id`` / ``case_names`` /
    ``rel_tolerance`` and the per-group, per-case numeric values under
    ``cases``. That file is read here and never written: this module opens
    it read-only, and regenerating it stays an explicit decision for
    ``engine/baseline/capture.py --regenerate``.

    Args:
        scenario: The scenario definition the snapshot belongs to. It is not
            executed and not validated here; its identifiers and pinned
            model versions are echoed into the report so a delta can always
            be attributed to a specific definition plus model versions.
        snapshot: The measured snapshot, in the R18 shape (a mapping with a
            ``cases`` key). A bare cases mapping is also accepted.
        stored_path: Optional override for the recorded baseline file.

    Returns:
        A dict with the scenario header, the stored baseline identity and
        tolerance, ``cases`` (per group, per case: status plus per-path
        stored / measured / delta / relative / within_tolerance entries),
        ``extra_case_groups``, and a ``summary``. When the recorded baseline
        cannot be read, ``status`` is ``stored_baseline_unavailable`` and
        ``reason`` says why, instead of an exception eating the comparison.

    Raises:
        ValueError: ``scenario`` or ``snapshot`` is not a mapping.
    """
    if not isinstance(scenario, dict):
        raise ValueError(
            f"scenario must be a mapping, got {type(scenario).__name__}"
        )
    if not isinstance(snapshot, dict):
        raise ValueError(
            f"snapshot must be a mapping, got {type(snapshot).__name__}"
        )

    header: dict[str, Any] = {
        "scenario_id": scenario.get("scenario_id"),
        "scenario_version": scenario.get("scenario_version"),
        "model_versions": scenario.get("model_versions"),
    }
    empty_summary: dict[str, Any] = {
        "case_groups": 0,
        "cases": 0,
        "values_matching": 0,
        "values_differing": 0,
        "values_missing_in_snapshot": 0,
        "values_only_in_snapshot": 0,
        "stored_values": 0,
        "max_relative_delta": None,
        "all_values_within_tolerance": True,
    }

    path, stored, reason = _load_recorded_baseline(stored_path)
    if stored is None:
        return {
            **header,
            "status": "stored_baseline_unavailable",
            "reason": reason,
            "stored_path": str(path) if path is not None else None,
            "cases": {},
            "extra_case_groups": [],
            "summary": empty_summary,
        }

    rel_tolerance = stored.get("rel_tolerance")
    if not isinstance(rel_tolerance, (int, float)) or isinstance(rel_tolerance, bool):
        rel_tolerance = _DEFAULT_REL_TOLERANCE

    measured_cases = _snapshot_cases(snapshot)
    stored_cases = stored.get("cases")
    if not isinstance(stored_cases, dict):
        stored_cases = {}

    cases: dict[str, Any] = {}
    summary = dict(empty_summary)
    max_relative: float | None = None

    for group in sorted(stored_cases):
        stored_group = stored_cases[group] or {}
        measured_group = measured_cases.get(group) or {}
        if not isinstance(stored_group, dict) or not isinstance(measured_group, dict):
            continue
        group_cases: dict[str, Any] = {}
        for case_name in sorted(set(stored_group) | set(measured_group)):
            entry = _case_entry(
                stored_group.get(case_name),
                measured_group.get(case_name),
                rel_tolerance,
            )
            group_cases[case_name] = entry
            summary["cases"] += 1
            for kind in (
                "values_matching",
                "values_differing",
                "values_missing_in_snapshot",
                "values_only_in_snapshot",
            ):
                summary[kind] += entry["counts"][kind]
            summary["stored_values"] += (
                entry["counts"]["values_matching"]
                + entry["counts"]["values_differing"]
                + entry["counts"]["values_missing_in_snapshot"]
            )
            if entry["max_relative_delta"] is not None:
                if max_relative is None or entry["max_relative_delta"] > max_relative:
                    max_relative = entry["max_relative_delta"]
        if group_cases:
            cases[group] = group_cases
        summary["case_groups"] += 1

    extra_case_groups = sorted(set(measured_cases) - set(stored_cases))
    summary["max_relative_delta"] = max_relative
    summary["all_values_within_tolerance"] = summary["values_differing"] == 0

    return {
        **header,
        "status": "compared",
        "stored_path": str(path),
        "stored_baseline_id": stored.get("baseline_id"),
        "stored_schema_version": stored.get("schema_version"),
        "rel_tolerance": rel_tolerance,
        "cases": cases,
        "extra_case_groups": extra_case_groups,
        "summary": summary,
        "note": (
            "Stored values come from the recorded execution baseline and "
            "are read-only; a delta is a difference between a measured "
            "snapshot and that record, not a statement about the scenario "
            "being physically correct."
        ),
    }


def _load_recorded_baseline(
    stored_path: str | Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None, str | None]:
    """Open the recorded baseline read-only.

    Returns ``(path, payload, reason)``: exactly one of ``payload`` and
    ``reason`` is not ``None``.
    """
    if stored_path is not None:
        candidates: tuple[Path, ...] = (Path(stored_path),)
    else:
        candidates = _RECORDED_BASELINE_CANDIDATES

    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        searched = ", ".join(str(candidate) for candidate in candidates)
        return None, None, f"no recorded baseline file found (searched: {searched})"

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return path, None, f"{type(exc).__name__}: {exc}"

    if not isinstance(payload, dict):
        return path, None, f"{path}: expected a JSON object"
    return path, payload, None


def _snapshot_cases(snapshot: dict[str, Any]) -> dict[str, Any]:
    """The cases mapping of a measured snapshot, in either accepted shape."""
    cases = snapshot.get("cases")
    if isinstance(cases, dict):
        return cases
    return {key: value for key, value in snapshot.items() if key not in _ENVELOPE_KEYS}


def _case_entry(
    stored_case: Any, measured_case: Any, rel_tolerance: float
) -> dict[str, Any]:
    """Per-case comparison of one recorded case against its measurement.

    Three shapes are reported: ``missing_in_measured`` (the recorded case
    has no measurement), ``only_in_measured`` (the snapshot carries a case
    the record does not), and the value-by-value comparison for a case
    present on both sides.

    A recorded case is not always a mapping: in ``engine/baseline/R18.json``
    a case value can be a mapping, a list of numbers, or a bare number.
    Whatever it is, it is flattened to dotted paths first, so a list-valued
    case is still compared value by value. Only a case that is absent on
    both sides is ``not_comparable``.
    """
    metrics: dict[str, Any]
    counts: dict[str, int]

    if stored_case is None and measured_case is None:
        return {
            "status": "not_comparable",
            "metrics": {},
            "counts": _empty_counts(),
            "max_relative_delta": None,
        }

    if measured_case is None:
        metrics = {
            path: _value_entry(value, None, kind="missing")
            for path, value in sorted(_flatten(stored_case).items())
        }
        counts = _empty_counts()
        counts["values_missing_in_snapshot"] = len(metrics)
        return {
            "status": "missing_in_measured",
            "metrics": metrics,
            "counts": counts,
            "max_relative_delta": None,
        }

    if stored_case is None:
        metrics = {
            path: _value_entry(None, value, kind="only_in_snapshot")
            for path, value in sorted(_flatten(measured_case).items())
        }
        counts = _empty_counts()
        counts["values_only_in_snapshot"] = len(metrics)
        return {
            "status": "only_in_measured",
            "metrics": metrics,
            "counts": counts,
            "max_relative_delta": None,
        }

    flat_stored = _flatten(stored_case)
    flat_measured = _flatten(measured_case)
    metrics = {}
    counts = _empty_counts()
    structural: list[str] = []
    max_relative: float | None = None

    for path in sorted(set(flat_stored) | set(flat_measured)):
        if path not in flat_measured:
            metrics[path] = _value_entry(
                flat_stored[path], None, kind="missing"
            )
            counts["values_missing_in_snapshot"] += 1
            structural.append(path)
            continue
        if path not in flat_stored:
            metrics[path] = _value_entry(
                None, flat_measured[path], kind="only_in_snapshot"
            )
            counts["values_only_in_snapshot"] += 1
            structural.append(path)
            continue

        entry = _value_entry(flat_stored[path], flat_measured[path], rel_tolerance)
        metrics[path] = entry
        if entry["within_tolerance"]:
            counts["values_matching"] += 1
        else:
            counts["values_differing"] += 1
        if entry["relative"] is not None:
            if max_relative is None or entry["relative"] > max_relative:
                max_relative = entry["relative"]

    if structural:
        status = "structural"
    elif counts["values_differing"]:
        status = "differs"
    else:
        status = "match"

    return {
        "status": status,
        "metrics": metrics,
        "counts": counts,
        "max_relative_delta": max_relative,
    }


def _empty_counts() -> dict[str, int]:
    """A fresh per-case counter block."""
    return {
        "values_matching": 0,
        "values_differing": 0,
        "values_missing_in_snapshot": 0,
        "values_only_in_snapshot": 0,
    }


def _value_entry(
    stored: Any,
    measured: Any,
    rel_tolerance: float = 0.0,
    kind: str | None = None,
) -> dict[str, Any]:
    """One leaf comparison: stored vs measured, with a numeric delta.

    Booleans are tested before numbers because ``bool`` is an ``int``
    subclass in Python, and ``NaN`` is reported as a failed comparison
    rather than quietly comparing unequal to itself. The relative delta
    uses the stored value as the denominator, falling back to the measured
    one when the stored value is zero -- the same convention
    ``engine/baseline/capture.py`` uses, so the two reports agree.
    """
    entry = {
        "stored": stored,
        "measured": measured,
        "delta": None,
        "relative": None,
        "within_tolerance": False,
    }

    if kind == "missing":
        entry["kind"] = "missing"
        return entry
    if kind == "only_in_snapshot":
        entry["kind"] = "only_in_snapshot"
        return entry

    if isinstance(stored, bool) or isinstance(measured, bool):
        entry["kind"] = "bool"
        entry["within_tolerance"] = stored == measured
        return entry

    if isinstance(stored, (int, float)) and isinstance(measured, (int, float)):
        if math.isnan(measured) or math.isnan(stored):
            entry["kind"] = "nan"
            return entry
        delta = measured - stored
        denominator = abs(stored) if stored != 0 else abs(measured)
        relative = abs(delta) / denominator if denominator else 0.0
        entry["kind"] = "numeric"
        entry["delta"] = delta
        entry["relative"] = relative
        entry["within_tolerance"] = relative <= rel_tolerance
        return entry

    entry["kind"] = "value"
    entry["within_tolerance"] = stored == measured
    return entry


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested capture into dotted paths, so a diff names one number.

    Containers are walked; a container that is empty becomes a leaf of its
    own rather than vanishing, so a case that turns into an empty mapping
    is still reported as a structural difference.
    """
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        if not value:
            out[prefix or _LEAF_ROOT] = value
            return out
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(item, child))
    elif isinstance(value, (list, tuple)):
        if not value:
            out[prefix or _LEAF_ROOT] = value
            return out
        for index, item in enumerate(value):
            out.update(_flatten(item, f"{prefix}[{index}]"))
    else:
        out[prefix or _LEAF_ROOT] = value
    return out
