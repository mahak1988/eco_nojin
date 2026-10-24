#!/usr/bin/env python3
"""ECO-02 DoD / remediation item B-6: the architecture dependency graph.

AST-scans the in-repo source areas (``engine``, ``services``, ``adapters``,
``runtime``, ``scenario``, ``decision``, ``database``, ``tools``) and builds a
module -> imports graph. It writes ``architecture/dependency-graph.md``
containing

* a per-area summary (files, internal edges, external-to-area edges),
* the cross-area edge list (area -> area with the module pairs),
* the top-20 most-imported internal modules,

and can emit the raw graph as JSON (``--json``) or regenerate the committed
markdown and compare it (``--check``, exit 1 on drift) so CI keeps the artefact
fresh.

Design notes
------------
* stdlib only. The tool never imports engine or service code: it parses it.
* Deterministic output - no timestamps, no absolute paths, every list sorted,
  so ``--check`` is a pure content comparison and the artefact is diffable.
* Test files (``tests``/``*_tests`` directories, ``conftest.py``,
  ``test_*.py``/``*_test.py``) are excluded from the production-boundary view
  and counted as ``test_files_excluded``; ``--include-tests`` measures them
  too. Remediation item A-3 is about the production boundary, so the
  committed artefact is the production view.
* "Area" is the top-level package (``engine``, ``database``, ``tools``, ...),
  except inside ``services/`` where it is the subpackage
  (``services.api_gateway``, ``services._gateway_facade``, ...) so the
  services-internal boundaries measured by ``tools/check_service_boundaries.py``
  are visible in this graph as well.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

#: Source areas scanned by the graph (top-level packages only).
SCAN_AREAS: tuple[str, ...] = (
    "engine",
    "services",
    "adapters",
    "runtime",
    "scenario",
    "decision",
    "database",
    "tools",
)

#: Directory names never scanned (caches, virtualenvs, build artefacts).
EXCLUDED_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "build",
        "dist",
        ".eggs",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".hypothesis",
        ".benchmarks",
        ".snapshots",
        ".cache",
        ".ipynb_checkpoints",
    }
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKDOWN = REPO_ROOT / "architecture" / "dependency-graph.md"
GUARD_POLICY_PATH = REPO_ROOT / "tools" / "import_guard_policy.json"

TOP_IMPORTED_LIMIT = 20


# --------------------------------------------------------------------------- #
# file / module naming
# --------------------------------------------------------------------------- #
def module_name(rel: PurePosixPath) -> str:
    """Dotted module name of a repo-relative path (``pkg/__init__.py`` -> ``pkg``)."""
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def package_of(rel: PurePosixPath) -> str:
    """Package a file belongs to (its own package when it is an ``__init__``)."""
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    else:
        parts.pop()
    return ".".join(parts)


def is_test_path(rel: PurePosixPath) -> bool:
    """True for test modules: ``tests`` dirs, ``conftest.py``, ``test_*.py``."""
    if any(part == "tests" or part.endswith("_tests") for part in rel.parts):
        return True
    stem = rel.stem
    return stem == "conftest" or stem.startswith("test_") or stem.endswith("_test")


def area_of(module: str) -> str:
    """Graph area of a module: ``services.<subpackage>`` inside the services tier."""
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "services":
        return f"services.{parts[1]}"
    return parts[0]


def family_of(area: str) -> str:
    """Top-level family of an area (``services.api_gateway`` -> ``services``)."""
    return area.split(".", 1)[0]


def iter_source_files(root: Path, include_tests: bool) -> tuple[list[PurePosixPath], int]:
    """Repo-relative posix paths of the scanned files plus the excluded test count."""
    files: list[PurePosixPath] = []
    excluded = 0
    for area in SCAN_AREAS:
        base = root / area
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = PurePosixPath(path.relative_to(root).as_posix())
            if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
                continue
            if not include_tests and is_test_path(rel):
                excluded += 1
                continue
            files.append(rel)
    return files, excluded


# --------------------------------------------------------------------------- #
# import extraction
# --------------------------------------------------------------------------- #
def _relative_base(pkg: str, level: int) -> str:
    """Package an ``ImportFrom`` with ``level`` dots above ``pkg`` resolves against."""
    if level <= 0:
        return ""
    base = pkg
    for _ in range(level - 1):
        base = base.rpartition(".")[0]
    return base


def raw_imports(tree: ast.AST, pkg: str) -> list[tuple[str, list[str]]]:
    """``(module, imported_names)`` pairs of every import statement in a tree.

    Module-level and function-level imports are both collected (``ast.walk``).
    Relative imports are resolved against the file's package, so they become
    internal edges like any absolute import.
    """
    found: list[tuple[str, list[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, [alias.asname or alias.name]))
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            if node.level:
                base = _relative_base(pkg, node.level)
                if node.module:
                    found.append((f"{base}.{node.module}" if base else node.module, names))
                elif base:
                    found.append((base, names))
            elif node.module:
                found.append((node.module, names))
    return found


def resolve_targets(target: str, names: list[str], modules: set[str]) -> set[str]:
    """Modules a single import statement actually refers to.

    ``from engine.hydroma import soil`` resolves to both ``engine.hydroma`` and
    the submodule ``engine.hydroma.soil`` when that submodule exists in the
    scanned set.
    """
    resolved = set()
    if target in modules:
        resolved.add(target)
    for name in names:
        sub = f"{target}.{name}"
        if sub in modules:
            resolved.add(sub)
    return resolved


# --------------------------------------------------------------------------- #
# graph
# --------------------------------------------------------------------------- #
@dataclass
class DependencyGraph:
    """The measured module -> imports graph over the in-repo source areas."""

    files_scanned: int = 0
    test_files_excluded: int = 0
    parse_errors: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    module_area: dict[str, str] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    files_per_area: dict[str, int] = field(default_factory=dict)


def build_graph(root: Path, include_tests: bool = False) -> DependencyGraph:
    """Scan ``root`` and return the measured dependency graph."""
    rel_files, test_excluded = iter_source_files(root, include_tests)
    graph = DependencyGraph(files_scanned=len(rel_files), test_files_excluded=test_excluded)

    modules = {module_name(rel) for rel in rel_files}
    graph.modules = sorted(modules)
    graph.module_area = {module: area_of(module) for module in graph.modules}
    for module in graph.modules:
        area = graph.module_area[module]
        graph.files_per_area[area] = graph.files_per_area.get(area, 0) + 1

    edges: set[tuple[str, str]] = set()
    for rel in rel_files:
        src = module_name(rel)
        try:
            source = (root / rel).read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
        except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
            graph.parse_errors.append(rel.as_posix())
            continue
        pkg = package_of(rel)
        for target, names in raw_imports(tree, pkg):
            for resolved in resolve_targets(target, names, modules):
                if resolved != src:
                    edges.add((src, resolved))

    graph.parse_errors.sort()
    graph.edges = sorted(edges)
    return graph


def cross_area_edges(graph: DependencyGraph) -> dict[tuple[str, str], list[tuple[str, str]]]:
    """Edges that leave their area, keyed by ``(from_area, to_area)``."""
    grouped: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for src, dst in graph.edges:
        from_area = graph.module_area[src]
        to_area = graph.module_area[dst]
        if from_area == to_area:
            continue
        grouped.setdefault((from_area, to_area), []).append((src, dst))
    return {key: sorted(value) for key, value in sorted(grouped.items())}


def family_cross_area_edges(graph: DependencyGraph) -> dict[tuple[str, str], int]:
    """Cross-area edge counts rolled up to top-level families (``services`` -> ``engine``)."""
    counts: dict[tuple[str, str], int] = {}
    for (from_area, to_area), pairs in cross_area_edges(graph).items():
        key = (family_of(from_area), family_of(to_area))
        counts[key] = counts.get(key, 0) + len(pairs)
    return dict(sorted(counts.items()))


def top_imported(graph: DependencyGraph, limit: int = TOP_IMPORTED_LIMIT) -> list[tuple[str, int]]:
    """The most-imported internal modules, by number of distinct importers."""
    importers: dict[str, set[str]] = {}
    for src, dst in graph.edges:
        importers.setdefault(dst, set()).add(src)
    ranked = sorted(importers.items(), key=lambda item: (-len(item[1]), item[0]))
    return [(module, len(sources)) for module, sources in ranked[:limit]]


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _allowed_module_names(entries: Any) -> set[str]:
    """Module names of an ``allowed_imports`` list.

    Both shapes occur in this repo: plain strings (the rule table in
    ``tools/detect_imports.py``) and ``{"module": ..., "rationale": ...}``
    dicts (``tools/import_guard_policy.json``).
    """
    names: set[str] = set()
    if not isinstance(entries, list):
        return names
    for entry in entries:
        if isinstance(entry, str):
            names.add(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("module"), str):
            names.add(entry["module"])
    return names


def sanctioned_engine_database_modules() -> set[str]:
    """The ``database.*`` modules the import guard sanctions for engine code.

    Read from ``tools/import_guard_policy.json`` when it carries an
    ``ENGINE_NO_DATABASE`` rule, otherwise from the rule table published by
    ``tools/detect_imports.py:get_rules()`` (where that exception lives today).
    Used only to annotate the markdown; the graph itself measures everything.
    """
    import importlib.util

    allowed: set[str] = set()
    try:
        policy = json.loads(GUARD_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        policy = {}
    rule = policy.get("rules", {}).get("ENGINE_NO_DATABASE", {})
    allowed.update(_allowed_module_names(rule.get("allowed_imports", [])))
    if not allowed:
        guard_path = REPO_ROOT / "tools" / "detect_imports.py"
        try:
            spec = importlib.util.spec_from_file_location("detect_imports_guard", guard_path)
            if spec is not None and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for candidate in module.get_rules():
                    if candidate.id == "ENGINE_NO_DATABASE":
                        allowed.update(candidate.allowed_imports)
        except (OSError, AttributeError):
            return set()
    return allowed


def _edge_line(src: str, dst: str, sanctioned: set[str] | None = None) -> str:
    note = ""
    if sanctioned is not None and (dst in sanctioned or any(
        dst.startswith(f"{module}.") for module in sanctioned
    )):
        note = " — sanctioned persistence bridge (ENGINE_NO_DATABASE)"
    return f"- `{src}` → `{dst}`{note}"


def render_markdown(graph: DependencyGraph) -> str:
    """Render the committed ``architecture/dependency-graph.md`` artefact."""
    lines: list[str] = []
    add = lines.append

    add("# Architecture Dependency Graph")
    add("")
    add("> Generated by `tools/dependency_graph.py` (remediation item B-6, ECO-02 DoD output).")
    add("> Do not edit by hand - regenerate with:")
    add(">")
    add("> ```powershell")
    add("> python tools/dependency_graph.py --out architecture/dependency-graph.md")
    add("> ```")
    add(">")
    add("> CI keeps this artefact fresh with `python tools/dependency_graph.py --check`")
    add("> (exit 1 on drift). Cross-subpackage services edges are gated by")
    add("> `tools/check_service_boundaries.py` against `tools/service_boundary_policy.json`.")
    add("")
    add("## Scope")
    add("")
    add("| Metric | Value |")
    add("| --- | --- |")
    add(f"| Areas scanned | {', '.join(f'`{area}`' for area in SCAN_AREAS)} |")
    add(f"| Python files scanned | {graph.files_scanned} |")
    add(f"| Test files excluded | {graph.test_files_excluded} |")
    add(f"| Modules in graph | {len(graph.modules)} |")
    add(f"| Import edges (module to module) | {len(graph.edges)} |")
    add(f"| Parse errors | {len(graph.parse_errors)} |")
    add("")
    if graph.test_files_excluded:
        add(
            "Test modules (`tests`/`*_tests` directories, `conftest.py`, `test_*.py`) are "
            "excluded from this production-boundary view; re-run with `--include-tests` to "
            "measure them."
        )
        add("")
    if graph.parse_errors:
        add("Unparseable files (recorded, not counted as edges):")
        add("")
        for item in graph.parse_errors:
            add(f"- `{item}`")
        add("")

    add("## Per-area summary")
    add("")
    add("| Area | Files | Internal edges | Edges to other areas | Edges from other areas |")
    add("| --- | --- | --- | --- | --- |")
    internal: dict[str, int] = {}
    outgoing: dict[str, int] = {}
    incoming: dict[str, int] = {}
    for src, dst in graph.edges:
        from_area = graph.module_area[src]
        to_area = graph.module_area[dst]
        if from_area == to_area:
            internal[from_area] = internal.get(from_area, 0) + 1
        else:
            outgoing[from_area] = outgoing.get(from_area, 0) + 1
            incoming[to_area] = incoming.get(to_area, 0) + 1
    for area in sorted(graph.files_per_area):
        add(
            f"| `{area}` | {graph.files_per_area[area]} | {internal.get(area, 0)} | "
            f"{outgoing.get(area, 0)} | {incoming.get(area, 0)} |"
        )
    add("")

    add("## Cross-area edges by top-level family")
    add("")
    family_pairs = family_cross_area_edges(graph)
    if not family_pairs:
        add("_No cross-area edges measured._")
        add("")
    for (from_family, to_family), count in family_pairs.items():
        add(f"### {from_family} → {to_family} ({count} edges)")
        add("")
        for (from_area, to_area), pairs in cross_area_edges(graph).items():
            if family_of(from_area) != from_family or family_of(to_area) != to_family:
                continue
            add(f"- `{from_area}` → `{to_area}` ({len(pairs)} edges)")
        add("")

    add("## Cross-area edges (module level)")
    add("")
    grouped = cross_area_edges(graph)
    if not grouped:
        add("_No cross-area edges measured._")
        add("")
    for (from_area, to_area), pairs in grouped.items():
        add(f"### {from_area} → {to_area} ({len(pairs)} edges)")
        add("")
        sanctioned = (
            sanctioned_engine_database_modules()
            if from_area == "engine" and to_area == "database"
            else None
        )
        for src, dst in pairs:
            add(_edge_line(src, dst, sanctioned))
        add("")

    add(f"## Top-{TOP_IMPORTED_LIMIT} most-imported internal modules")
    add("")
    add("| Rank | Module | Distinct importers |")
    add("| --- | --- | --- |")
    for rank, (module, count) in enumerate(top_imported(graph), start=1):
        add(f"| {rank} | `{module}` | {count} |")
    add("")
    return "\n".join(lines)


def graph_to_dict(graph: DependencyGraph) -> dict[str, Any]:
    """The raw graph as JSON-serialisable data (stable ordering, no timestamps)."""
    return {
        "tool": "tools/dependency_graph.py",
        "remediation_item": "B-6",
        "areas_scanned": list(SCAN_AREAS),
        "files_scanned": graph.files_scanned,
        "test_files_excluded": graph.test_files_excluded,
        "parse_errors": graph.parse_errors,
        "modules": graph.modules,
        "module_area": {module: graph.module_area[module] for module in graph.modules},
        "edges": [[src, dst] for src, dst in graph.edges],
        "cross_area_edges": {
            f"{from_area} → {to_area}": [[src, dst] for src, dst in pairs]
            for (from_area, to_area), pairs in cross_area_edges(graph).items()
        },
        "family_cross_area_edges": {
            f"{from_family} → {to_family}": count
            for (from_family, to_family), count in family_cross_area_edges(graph).items()
        },
        "top_imported": [
            {"module": module, "importers": count}
            for module, count in top_imported(graph)
        ],
    }


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ECO-02 DoD / B-6: architecture dependency graph generator."
    )
    parser.add_argument("--root", default=str(REPO_ROOT), help="Project root (default: repo root)")
    parser.add_argument(
        "--out",
        default=str(DEFAULT_MARKDOWN),
        help="Markdown artefact path (default: architecture/dependency-graph.md)",
    )
    parser.add_argument("--json", action="store_true", help="Emit the raw graph as JSON")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate the markdown and compare it with --out (exit 1 on drift)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Also scan test modules (excluded by default)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    graph = build_graph(root, include_tests=args.include_tests)

    if args.json:
        print(json.dumps(graph_to_dict(graph), indent=2))
        return 0

    markdown = render_markdown(graph)
    out_path = Path(args.out)

    if args.check:
        if not out_path.exists():
            print(f"DRIFT: {out_path} is missing - run with --out to generate it.")
            return 1
        current = out_path.read_text(encoding="utf-8")
        if current != markdown:
            print(f"DRIFT: {out_path} does not match a fresh scan.")
            print("Regenerate it with:")
            print(f"  python {Path(__file__).name} --out {out_path}")
            return 1
        print(f"OK: {out_path} matches a fresh scan ({graph.files_scanned} files, "
              f"{len(graph.edges)} edges).")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {out_path} ({graph.files_scanned} files, {len(graph.edges)} edges).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
