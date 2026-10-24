"""Dependency-graph tests (remediation item B-6 / ECO-02 DoD / C-4 step 5).

Pins what ``tools/dependency_graph.py`` and ``tools/check_service_boundaries.py``
measure about the real tree:

* the committed ``architecture/dependency-graph.md`` artefact is regenerable
  and matches a fresh scan (``--check`` exits 0), so CI can keep it fresh;
* the generator is deterministic - two scans of the same tree render identical
  markdown;
* the cross-area families that matter architecturally are reported with
  non-empty counts - ``services → engine`` (the ``_gateway_facade`` bridge is
  sanctioned, so this must be > 0 to stay visible) and ``engine → database``
  (the two sanctioned persistence-bridge modules), while ``engine → services``
  must stay empty (guard rule ENGINE_NO_SERVICES);
* a services-subpackage edge that the policy does not declare fails the
  boundary check (proved negatively with a temporary policy in ``tmp_path``).

The tree is edited live (C-1), so the freshness assertions are guarded by a
tree signature: when a file lands mid-scan the test skips instead of reporting
a false failure. Genuine drift still fails.

The tools are loaded by file path / run as subprocesses (``tools/`` is not a
package), so no rule table is duplicated here.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEPENDENCY_GRAPH = PROJECT_ROOT / "tools" / "dependency_graph.py"
CHECK_SERVICE_BOUNDARIES = PROJECT_ROOT / "tools" / "check_service_boundaries.py"
BOUNDARY_POLICY = PROJECT_ROOT / "tools" / "service_boundary_policy.json"
GRAPH_MARKDOWN = PROJECT_ROOT / "architecture" / "dependency-graph.md"

#: ``### services → engine (47 edges)`` style headings of the family rollup.
FAMILY_HEADING = re.compile(r"^### (?P<from>\S+) → (?P<to>\S+) \((?P<count>\d+) edges\)$", re.M)

#: Marker printed by ``dependency_graph.py --check`` when the artefact drifted.
DRIFT_MARKER = "DRIFT"


def _load_dependency_graph() -> Any:
    """Import the generator by file path (``tools/`` is not a package)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("dependency_graph_under_test", DEPENDENCY_GRAPH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {DEPENDENCY_GRAPH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dependency_graph = _load_dependency_graph()


def _run(tool: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(tool), *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def _tree_signature() -> str:
    """Fingerprint of the scanned production tree (file set + size + mtime)."""
    entries = []
    files, _ = dependency_graph.iter_source_files(PROJECT_ROOT, include_tests=False)
    for rel in files:
        stat = (PROJECT_ROOT / rel).stat()
        entries.append(f"{rel.as_posix()}:{stat.st_size}:{stat.st_mtime_ns}")
    payload = "\n".join(entries)
    return f"{len(entries)}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


@pytest.fixture(scope="module")
def family_edges() -> dict[str, int]:
    """Cross-area edge counts by top-level family, parsed from the artefact."""
    text = GRAPH_MARKDOWN.read_text(encoding="utf-8")
    section = text.split("## Cross-area edges by top-level family", 1)[1]
    section = section.split("## Cross-area edges (module level)", 1)[0]
    heading = "## Cross-area edges by top-level family\n" + section
    return {f"{m['from']} → {m['to']}": int(m["count"]) for m in FAMILY_HEADING.finditer(heading)}


def test_graph_is_regenerable_and_matches():
    """B-6 done: a fresh scan reproduces the committed artefact byte for byte.

    The CI contract is ``dependency_graph.py --check`` exiting 0. The tree is
    being edited live (C-1), so a file landing between the artefact's last
    regeneration and this scan would make the comparison meaningless; the
    signature probe either side of the run detects that and skips instead of
    reporting a false failure. Genuine drift still fails the test.
    """
    assert GRAPH_MARKDOWN.exists(), f"{GRAPH_MARKDOWN} missing - run dependency_graph.py --out"

    before = _tree_signature()
    result = _run(DEPENDENCY_GRAPH, "--check")
    after = _tree_signature()
    if before != after:
        pytest.skip(
            "the working tree changed while the scan ran (live tree, C-1): "
            "freshness is not decidable for a moving target"
        )

    assert result.returncode == 0, (
        f"dependency_graph.py --check exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert DRIFT_MARKER not in result.stdout


def test_generator_is_deterministic():
    """Two scans of the same tree must render identical markdown (regenerable)."""
    first = dependency_graph.render_markdown(dependency_graph.build_graph(PROJECT_ROOT))
    second = dependency_graph.render_markdown(dependency_graph.build_graph(PROJECT_ROOT))
    assert first == second
    assert "## Per-area summary" in first
    assert "## Cross-area edges by top-level family" in first
    assert "## Top-20 most-imported internal modules" in first


def test_cross_area_edges_are_reported(family_edges):
    """The architecturally load-bearing cross-area families are measured, not assumed."""
    assert family_edges, "no cross-area family sections found in the artefact"

    # services → engine: the sanctioned _gateway_facade bridge plus the
    # config-settings reads tracked by tools/import_guard_policy.json.
    assert family_edges.get("services → engine", 0) > 0, (
        f"services → engine must be reported with a non-empty count, got {family_edges}"
    )

    # engine → database: exactly the two sanctioned persistence-bridge modules.
    assert family_edges.get("engine → database", 0) > 0, (
        f"engine → database must be reported with a non-empty count, got {family_edges}"
    )

    # engine → services: the engine tier must not reach into the services tier.
    assert family_edges.get("engine → services", 0) == 0, (
        f"engine → services must be empty (guard rule ENGINE_NO_SERVICES), got {family_edges}"
    )

    assert family_edges.get("tools → engine", 0) > 0, (
        f"tools → engine must be reported with a non-empty count, got {family_edges}"
    )


def test_no_new_services_to_services_edge_without_policy(tmp_path):
    """A-3: an undeclared services-subpackage edge fails the boundary check.

    Positive: the committed policy covers every measured edge (exit 0).
    Negative: the same policy with one measured edge removed is rejected
    (exit 1) and names the offending edge.
    """
    before = _tree_signature()
    clean = _run(CHECK_SERVICE_BOUNDARIES)
    quiet = _tree_signature() == before
    if clean.returncode != 0:
        if quiet:
            pytest.fail(
                f"check_service_boundaries.py exited {clean.returncode} on a quiet tree\n"
                f"stdout: {clean.stdout}\nstderr: {clean.stderr}"
            )
        pytest.skip(
            "the working tree changed while the boundary check ran (live tree, C-1): "
            "a new services edge may need a policy entry"
        )
    assert clean.returncode == 0
    assert "VIOLATION" not in clean.stdout, clean.stdout

    policy = json.loads(BOUNDARY_POLICY.read_text(encoding="utf-8"))
    assert policy["allowed_edges"], "the boundary policy must declare today's edges"

    dropped = policy["allowed_edges"].pop()
    trimmed = tmp_path / "service_boundary_policy.json"
    trimmed.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    failing = _run(CHECK_SERVICE_BOUNDARIES, "--policy", str(trimmed))
    assert failing.returncode == 1, (
        f"a policy missing {dropped['from']} -> {dropped['to']} must fail, got "
        f"{failing.returncode}\nstdout: {failing.stdout}"
    )
    expected = f"VIOLATION {dropped['from']} -> {dropped['to']}"
    assert expected in failing.stdout, (
        f"expected {expected!r} in the report, got:\n{failing.stdout}"
    )
