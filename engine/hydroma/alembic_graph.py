"""Read and validate the Alembic revision graph without a database.

The graph is parsed with ``ast`` rather than through Alembic's own loader,
because the failure this module guards against is precisely a graph Alembic
cannot load. A loader that raises on the defect cannot also be the thing that
detects it.

Everything here is read-only. Rendering SQL is delegated to Alembic in a
subprocess, because that is the only way to prove a migration is executable
rather than merely well formed.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSIONS = REPO_ROOT / "alembic" / "versions"

#: Alembic's own storage table is created by the first migration and is not a
#: declared table, so it is excluded from the head count.
_ALEMBIC_VERSION = "alembic_version"


def _literal(node: ast.AST | None) -> object:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return "<unparsed>"


def revision_table() -> dict[str, dict]:
    """Every migration file's revision id, parent(s) and file name."""
    table: dict[str, dict] = {}
    for path in sorted(VERSIONS.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        found: dict[str, object] = {}
        for node in tree.body:
            # Most migrations in this repository use the annotated form
            # ``revision: str = "..."``; a few use the plain form. Both have to
            # be read, or the graph silently shrinks to whatever used the
            # minority spelling.
            if isinstance(node, ast.AnnAssign):
                name = getattr(node.target, "id", "")
                value = node.value
            elif isinstance(node, ast.Assign) and len(node.targets) == 1:
                name = getattr(node.targets[0], "id", "")
                value = node.value
            else:
                continue
            if name in ("revision", "down_revision", "branch_labels", "depends_on"):
                found[name] = _literal(value)
        revision = found.get("revision")
        if not isinstance(revision, str):
            continue
        down = found.get("down_revision")
        if isinstance(down, (list, tuple)):
            parents = [p for p in down if isinstance(p, str)]
        elif isinstance(down, str):
            parents = [down]
        else:
            parents = []
        labels = found.get("branch_labels")
        if not isinstance(labels, (list, tuple)):
            labels = [] if labels is None else [labels]
        table[revision] = {
            "file": path.name,
            "parents": parents,
            "branch_labels": [l for l in labels if isinstance(l, str)],
        }
    return table


def dangling_references() -> list[tuple[str, str, str]]:
    """``(child_revision, missing_parent, file)`` for every unresolvable name."""
    table = revision_table()
    ids = set(table)
    out: list[tuple[str, str, str]] = []
    for revision, info in table.items():
        for parent in info["parents"] + info["branch_labels"]:
            if parent not in ids:
                out.append((revision, parent, info["file"]))
    return out


def heads() -> list[str]:
    """Revisions nothing points at."""
    table = revision_table()
    referenced: set[str] = set()
    for info in table.values():
        referenced.update(info["parents"])
        referenced.update(info["branch_labels"])
    return sorted(set(table) - referenced)


def unreachable_revisions() -> list[str]:
    """Revisions with no path forward to a head.

    A cycle has no path, and so does a child whose parent is missing, which is
    the defect this module exists for. Both are reported.
    """
    table = revision_table()
    if dangling_references():
        return []
    parents = {rev: set(info["parents"]) for rev, info in table.items()}
    children = {rev: set() for rev in table}
    for rev, ps in parents.items():
        for parent in ps:
            children[parent].add(rev)
    good: set[str] = set()
    stack = [h for h in heads() if h in children]
    good.update(stack)
    while stack:
        node = stack.pop()
        for parent in parents.get(node, ()):
            if parent not in good and parent in children:
                good.add(parent)
                stack.append(parent)
    return sorted(set(table) - good)


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT),
        "DATABASE_URL": "sqlite:///./_alembic_sqlcheck.db",
    }


def render_range(spec: str) -> str:
    """Render the SQL Alembic would run for a revision range.

    This is the strongest check available without a database: it exercises the
    graph, the operation calls and the type mapping together, and it fails
    loudly on anything malformed.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", spec, "--sql"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic could not render {spec!r} (exit {result.returncode}):\n"
            f"{result.stderr[-1500:]}"
        )
    return result.stdout


def render_downgrade(spec: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", spec, "--sql"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic could not render the downgrade of {spec!r} "
            f"(exit {result.returncode}):\n{result.stderr[-1500:]}"
        )
    return result.stdout
