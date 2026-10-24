#!/usr/bin/env python3
"""ECO-02 DoD / remediation item A-3: services subpackage boundary checker.

Lists every cross-subpackage import inside the services tier -
``services.<a>`` importing ``services.<b>`` where ``a != b`` - as measured by
``tools/dependency_graph.py`` (imported by file path; ``tools/`` is not a
package, and this tool never imports engine or service code) and gates each
edge against the allowlist published as data in
``tools/service_boundary_policy.json``.

Output is one line per edge, ``OK <from> -> <to>`` or
``VIOLATION <from> -> <to> (<reason>)``, plus a summary. The exit status is 1
when any edge is not in the policy, when any policy entry is missing its
``rationale``/``expires``/``next_review``, or when the measured edge count
exceeds the policy's ratchet; 0 otherwise.

The policy is deliberately additive and dated: it records the edges that exist
today (measured 2026-10-11) with a per-edge rationale, an ``expires`` date and
a ``ratchet`` ceiling, so the boundary is honest about the current coupling
while giving the A-2 gateway/service split a measurable target to shrink
towards. Nothing here changes engine or service behaviour.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY_GRAPH_PATH = REPO_ROOT / "tools" / "dependency_graph.py"
DEFAULT_POLICY_PATH = REPO_ROOT / "tools" / "service_boundary_policy.json"

#: Fields every policy edge must carry (mirrors tools/import_guard_policy.json).
REQUIRED_EDGE_FIELDS = ("from", "to", "rationale", "expires", "next_review")


def _load_dependency_graph():
    """Import tools/dependency_graph.py by file path (tools/ is not a package)."""
    name = "dependency_graph_under_test"
    spec = importlib.util.spec_from_file_location(name, DEPENDENCY_GRAPH_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {DEPENDENCY_GRAPH_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_policy(policy_path: Path) -> dict[str, Any]:
    """Load the boundary policy (data, not code)."""
    policy: dict[str, Any] = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy.get("allowed_edges"), list):
        raise ValueError(f"{policy_path} must declare an 'allowed_edges' list")
    return policy


def services_cross_edges(dependency_graph: Any) -> dict[tuple[str, str], list[tuple[str, str]]]:
    """Cross-subpackage services edges keyed by ``(from_area, to_area)``."""
    measured: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for (from_area, to_area), pairs in dependency_graph.cross_area_edges(
        dependency_graph.build_graph(REPO_ROOT, include_tests=False)
    ).items():
        if from_area.split(".", 1)[0] != "services" or to_area.split(".", 1)[0] != "services":
            continue
        if from_area == to_area:
            continue
        measured[(from_area, to_area)] = pairs
    return measured


def policy_edge_keys(policy: dict[str, Any]) -> set[tuple[str, str]]:
    """The ``(from, to)`` pairs declared by the policy."""
    return {(entry.get("from"), entry.get("to")) for entry in policy["allowed_edges"]}


def check_policy(path: Path = DEFAULT_POLICY_PATH) -> tuple[list[str], int]:
    """Run the boundary check; returns the report lines and the exit status."""
    dependency_graph = _load_dependency_graph()
    policy = load_policy(path)
    allowed = policy_edge_keys(policy)
    measured = services_cross_edges(dependency_graph)

    lines: list[str] = []
    violations = 0

    stale = sorted(
        f"{entry.get('from')} -> {entry.get('to')}"
        for entry in policy["allowed_edges"]
        if (entry.get("from"), entry.get("to")) not in measured
    )

    for (from_area, to_area), pairs in sorted(measured.items()):
        if (from_area, to_area) in allowed:
            lines.append(f"OK {from_area} -> {to_area} ({len(pairs)} module edges)")
            continue
        violations += 1
        lines.append(f"VIOLATION {from_area} -> {to_area} (not declared in {path.name})")

    for entry in policy["allowed_edges"]:
        missing = [field for field in REQUIRED_EDGE_FIELDS if not entry.get(field)]
        if missing:
            violations += 1
            label = f"{entry.get('from')} -> {entry.get('to')}"
            lines.append(f"VIOLATION policy entry {label} missing {', '.join(missing)}")

    ratchet = policy.get("ratchet", {})
    max_edges = ratchet.get("max")
    if isinstance(max_edges, int) and len(measured) > max_edges:
        violations += 1
        lines.append(
            f"VIOLATION ratchet: {len(measured)} service-subpackage edges exceed "
            f"the policy maximum of {max_edges}"
        )

    for label in stale:
        lines.append(f"INFO stale policy entry {label} (no longer imported)")

    lines.append(
        f"Summary: {len(measured)} measured service-subpackage edge(s), "
        f"{len(allowed)} policy entry/entries, {violations} violation(s), "
        f"{len(stale)} stale entry/entries."
    )
    return lines, (1 if violations else 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="A-3: services subpackage boundary check against the published policy."
    )
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY_PATH),
        help="Policy file (default: tools/service_boundary_policy.json)",
    )
    args = parser.parse_args(argv)

    lines, status = check_policy(Path(args.policy))
    for line in lines:
        print(line)
    if status:
        print("Status: FAIL — undeclared or undocumented services boundary edge(s)")
    else:
        print("Status: PASS — every service-subpackage edge is declared and dated")
    return status


if __name__ == "__main__":
    sys.exit(main())
