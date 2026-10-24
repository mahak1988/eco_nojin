"""Service-boundary tests (remediation item A-3 / ECO-02 DoD / C-4 step 5).

Pins ``tools/check_service_boundaries.py`` and
``tools/service_boundary_policy.json`` against the real tree:

* every cross-subpackage services edge measured today is declared in the
  policy (the allowlist is additive and honest, not aspirational);
* every declared edge carries a rationale and dated review fields, mirroring
  the expiry mechanism of ``tools/import_guard_policy.json``;
* the tool rejects a policy that stops knowing a measured edge, and a policy
  entry that lost its rationale;
* the measured ``engine → database`` edges are exactly the sanctioned
  persistence bridge read from ``tools/import_guard_policy.json`` (falling
  back to the rule table in ``tools/detect_imports.py``, where the
  ``ENGINE_NO_DATABASE`` exception is also published).

Measured today (2026-10-11, production files only - test modules are excluded
by the graph): engine → database is exactly
``engine.hydroma.biofertilizer.calibration → database.config`` and
``engine.hydroma.biofertilizer.models → database.base``, i.e. the two modules
the guard sanctions as the persistence bridge pending the B-2 port injection.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEPENDENCY_GRAPH = PROJECT_ROOT / "tools" / "dependency_graph.py"
CHECK_SERVICE_BOUNDARIES = PROJECT_ROOT / "tools" / "check_service_boundaries.py"
BOUNDARY_POLICY = PROJECT_ROOT / "tools" / "service_boundary_policy.json"
GUARD_POLICY = PROJECT_ROOT / "tools" / "import_guard_policy.json"


def _load_module(path: Path, name: str) -> Any:
    """Import a ``tools/`` script by file path (``tools/`` is not a package)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SERVICE_BOUNDARIES), *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


dependency_graph = _load_module(DEPENDENCY_GRAPH, "dependency_graph_for_boundary_tests")
boundary_checker = _load_module(CHECK_SERVICE_BOUNDARIES, "check_service_boundaries_under_test")


@pytest.fixture(scope="module")
def graph() -> Any:
    """The measured dependency graph over the real tree (production files)."""
    return dependency_graph.build_graph(PROJECT_ROOT, include_tests=False)


@pytest.fixture(scope="module")
def measured_service_edges(graph) -> set[tuple[str, str]]:
    """Cross-subpackage services edges measured by the graph."""
    measured: set[tuple[str, str]] = set()
    for (from_area, to_area) in dependency_graph.cross_area_edges(graph):
        if from_area.split(".", 1)[0] != "services" or to_area.split(".", 1)[0] != "services":
            continue
        if from_area == to_area:
            continue
        measured.add((from_area, to_area))
    return measured


@pytest.fixture(scope="module")
def policy() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(BOUNDARY_POLICY.read_text(encoding="utf-8"))
    return loaded


def test_policy_covers_every_current_edge(measured_service_edges, policy):
    """A-3 honesty: the allowlist is a superset of what the tree does today."""
    declared = {(entry["from"], entry["to"]) for entry in policy["allowed_edges"]}
    missing = sorted(measured_service_edges - declared)
    assert not missing, (
        f"{len(missing)} measured service-subpackage edge(s) are not declared in "
        f"{BOUNDARY_POLICY.name}: {missing}"
    )
    extra = sorted(declared - measured_service_edges)
    assert not extra, (
        f"{len(extra)} declared edge(s) no longer exist and should be pruned: {extra}"
    )


def test_every_policy_edge_has_rationale_and_expiry(policy):
    """Every declared edge is dated and explained, like the import-guard exceptions."""
    entries = policy["allowed_edges"]
    assert entries, "the boundary policy must declare at least one edge"
    for entry in entries:
        label = f"{entry.get('from')} -> {entry.get('to')}"
        assert entry.get("rationale", "").strip(), f"{label} has no rationale"
        for field in ("expires", "next_review"):
            raw = entry.get(field)
            assert raw, f"{label} has no {field}"
            date.fromisoformat(raw)
        assert entry["next_review"] < entry["expires"], (
            f"{label}: next_review must precede expires"
        )
    assert policy["expires"] and policy["next_review"], "the policy itself must be dated"


def test_boundary_tool_rejects_an_unknown_edge(tmp_path, policy):
    """An edge the policy stops knowing is a violation, not a silent pass."""
    trimmed = tmp_path / "service_boundary_policy.json"
    policy["allowed_edges"] = policy["allowed_edges"][:-1]
    trimmed.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    result = _run("--policy", str(trimmed))
    assert result.returncode == 1, f"an undeclared edge must fail the check, got:\n{result.stdout}"
    assert "VIOLATION" in result.stdout

    stripped = tmp_path / "service_boundary_policy_no_rationale.json"
    policy["allowed_edges"] = [
        {key: value for key, value in entry.items() if key != "rationale"}
        for entry in policy["allowed_edges"]
    ]
    stripped.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    no_rationale = _run("--policy", str(stripped))
    assert no_rationale.returncode == 1, (
        f"a policy entry without a rationale must fail the check, got:\n{no_rationale.stdout}"
    )
    assert "missing rationale" in no_rationale.stdout


def test_engine_to_database_edges_are_exactly_the_sanctioned_ones(graph):
    """The engine tier reaches ``database`` only through the sanctioned bridge.

    Measured after the B-2 port injection (2026-10-11, re-measured 2026-10-14):
    only ``engine.hydroma.biofertilizer.models → database.base`` remains - the
    ``calibration → database.config`` edge was removed when the engine started
    taking an injected port. The policy carries both entries as
    ``pending-removal`` (removal_target 2026-12-31), and a ``pending-removal``
    entry is no longer sanctioned-in-fact, so it is excluded from the
    sanctioned-in-fact set here: the remaining edge must keep *retiring*, never
    quietly sanctioned again. When the last importer is port-injected the
    measured set (and the sanctioned-in-fact set) is empty — that is the end
    state this test steers towards, not a failure.
    """
    measured = {
        (src, dst)
        for (from_area, to_area), pairs in dependency_graph.cross_area_edges(graph).items()
        if from_area == "engine" and to_area == "database"
        for src, dst in pairs
    }
    targets = {dst for _, dst in measured}

    sanctioned: set[str] = set()
    retiring: set[str] = set()
    try:
        guard = json.loads(GUARD_POLICY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # pragma: no cover - defensive
        guard = {}
    for entry in guard.get("rules", {}).get("ENGINE_NO_DATABASE", {}).get("allowed_imports", []):
        if isinstance(entry, dict):
            if entry.get("status") == "pending-removal":
                retiring.add(entry["module"])
            else:
                sanctioned.add(entry["module"])
        elif isinstance(entry, str):
            sanctioned.add(entry)

    # Every engine->database target must be declared in the policy (either
    # still sanctioned or explicitly retiring).
    assert targets <= (sanctioned | retiring), (
        f"engine -> database targets {sorted(targets)} are not declared in the "
        f"policy (sanctioned={sorted(sanctioned)}, retiring={sorted(retiring)})"
    )
    # ... and none of them may sit in the sanctioned-in-fact set while the B-2
    # retirements are pending: re-marking a retired bridge as sanctioned would
    # otherwise silently re-open the engine -> implementation coupling.
    assert not (targets & sanctioned), (
        f"engine -> database targets {sorted(targets)} overlap the "
        f"sanctioned-in-fact set {sorted(sanctioned)}"
    )
    assert measured == {
        ("engine.hydroma.biofertilizer.models", "database.base")
    }, f"the B-2 remainder moved: {sorted(measured)}"


def test_engine_has_no_production_edge_to_services(graph):
    """Guard rule ENGINE_NO_SERVICES, measured independently of detect_imports.py."""
    offenders = [
        (src, dst)
        for (from_area, to_area), pairs in dependency_graph.cross_area_edges(graph).items()
        if from_area == "engine" and to_area.startswith("services")
        for src, dst in pairs
    ]
    assert offenders == [], f"engine imports services modules in production code: {offenders}"
