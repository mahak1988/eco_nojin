"""Detect vacuous tests: assertions that cannot fail.

A test that asserts on the *text* of the source code is vacuous when it
asserts **containment**. The source it reads contains the string by
construction, so the assertion passes whether or not the behaviour exists:

    source = inspect.getsource(mkt_router.marketplace_stats)
    assert "verified" in source      # passes; proves nothing about the route

That exact shape was the KN-21 test. The scoping code it "proves" compares
``seller.status == "verified"`` -- a value no code path ever writes -- so the
route returns the global revenue aggregate to every caller, and the test stays
green.

A **negative** containment assertion (``assert "commit(" not in source``) is a
different thing: it is a source-level lint with a real failure mode, so it is
not reported here.

The second detector looks for an assertion on a field the database does not
have: a test that assigns and then asserts an attribute that is not a mapped
column proves nothing about persistence, because the attribute was never
persisted in the first place.

Run it standalone::

    python tools/check_vacuous_tests.py --root .
    python tools/check_vacuous_tests.py --root . --strict   # non-zero on findings
"""

from __future__ import annotations

import argparse
import ast
import json
import linecache
import os
import warnings
from pathlib import Path

#: Names a source string is typically bound to. Used to recognise the shape,
#: not to whitelist it -- the receiver is matched by assignment, not by name.
_SOURCE_LIKE_NAMES = {"source", "src", "text", "body", "code", "sources"}

#: Directories walked for model definitions. A model is any class whose base is
#: named ``Base`` -- not just the modules under a ``models/`` directory, because
#: several services define their models in a service file
#: (``services/tourism/incidents.py`` is one).
_MODEL_SCAN_ROOTS = ("services", "database", "adapters")


def _iter_test_files(root: Path) -> list[Path]:
    """Test files worth parsing, with a cheap text pre-filter."""
    skip_dirs = {"__pycache__", ".git", ".venv", "node_modules", ".mypy_cache", "data"}
    scan_roots = [
        root / name
        for name in ("services", "engine", "tests", "database", "tools", "adapters")
        if (root / name).is_dir()
    ]
    found: list[Path] = []
    for base in scan_roots:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for filename in filenames:
                if not (filename.startswith("test_") or filename.endswith("_test.py")):
                    continue
                path = Path(dirpath) / filename
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                # Cheap pre-filter: a file with no assertion cannot hold a
                # vacuous assertion, and parsing every test file in the tree
                # is the difference between seconds and minutes.
                if "assert" not in text:
                    continue
                found.append(path)
    return sorted(found)


def _parse_source(path: Path) -> ast.Module | None:
    """Parse a file, ignoring syntax warnings raised by its own content."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return None


def _is_source_producing_call(node: ast.Call) -> bool:
    """True for ``inspect.getsource(...)`` / ``path.read_text()`` style calls."""
    func = node.func
    name = getattr(func, "attr", "") or getattr(func, "id", "")
    if name == "getsource":
        return True
    if name == "read_text":
        return True
    return False


def _assigned_source_names(func: ast.FunctionDef) -> set[str]:
    """Local names bound to the text of some source file."""
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not _is_source_producing_call(node.value):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def _positive_source_asserts(func: ast.FunctionDef, path: Path) -> list[tuple[int, str]]:
    """(line, source text) of assertions that assert a source string CONTAINS."""
    source_names = _assigned_source_names(func)
    if not source_names:
        return []
    hits: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Assert):
            continue
        test = node.test
        # `x in source` is vacuous; `x not in source` is a lint -- skip it.
        if not isinstance(test, ast.Compare):
            continue
        if not any(isinstance(op, ast.In) for op in test.ops):
            continue
        if any(
            isinstance(node_, ast.Name) and node_.id in source_names
            for node_ in ast.walk(test)
        ):
            hits.append((node.lineno, _source_line(path, node.lineno)))
    return hits


def _source_line(path: Path, lineno: int) -> str:
    """The stripped text of a line, used as a stable key across edits.

    Keying the baseline on the line *number* breaks as soon as an unrelated
    edit shifts the file; keying on the text of the line does not.
    """
    try:
        return linecache.getline(str(path), lineno).strip()
    except Exception:  # pragma: no cover - defensive
        return f"line {lineno}"


def _mapped_attributes(root: Path) -> set[str]:
    """Every attribute name declared on a model class in the repository.

    A model is any class whose base is named ``Base`` -- the SQLAlchemy
    declarative base, whether it is imported from ``database.base`` or aliased.
    """
    skip_dirs = {"__pycache__", ".git", ".venv", "node_modules", ".mypy_cache", "data"}
    attributes: set[str] = set()
    for name in _MODEL_SCAN_ROOTS:
        base_dir = root / name
        if not base_dir.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base_dir):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                tree = _parse_source(Path(dirpath) / filename)
                if tree is None:
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ClassDef):
                        continue
                    if not _is_model_class(node):
                        continue
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                            attributes.add(stmt.target.id)
                        elif isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    attributes.add(target.id)
    return attributes


def _is_model_class(node: ast.ClassDef) -> bool:
    """True when the class derives from the declarative ``Base``."""
    for base in node.bases:
        name = getattr(base, "id", None) or getattr(base, "attr", None)
        if name == "Base":
            return True
    return False


def _unpersisted_field_asserts(
    func: ast.FunctionDef, mapped: set[str], path: Path
) -> list[tuple[int, str, str]]:
    """Assertions on an attribute that is not a mapped column anywhere."""
    assigned: dict[str, set[str]] = {}
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                assigned.setdefault(target.value.id, set()).add(target.attr)

    hits: list[tuple[int, str, str]] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Assert):
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Attribute):
                continue
            if not isinstance(child.value, ast.Name):
                continue
            owner = child.value.id
            attr = child.attr
            if attr.startswith("_"):
                continue  # a private attribute of a plain object, not a column
            if attr in mapped:
                continue
            if attr not in assigned.get(owner, set()):
                continue
            hits.append((node.lineno, f"{owner}.{attr}", _source_line(path, node.lineno)))
    return hits


def scan(root: Path) -> list[tuple[str, int, str, str]]:
    """Return (file, line, reason, source text) for every vacuous assertion."""
    mapped = _mapped_attributes(root)
    findings: list[tuple[str, int, str, str]] = []
    for path in _iter_test_files(root):
        tree = _parse_source(path)
        if tree is None:
            continue
        rel = path.relative_to(root)
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not func.name.startswith("test_"):
                continue
            for lineno, snippet in _positive_source_asserts(func, path):
                findings.append(
                    (str(rel), lineno, "positive containment assert on source text", snippet)
                )
            for lineno, attr, snippet in _unpersisted_field_asserts(func, mapped, path):
                findings.append(
                    (
                        str(rel),
                        lineno,
                        f"assert on a field the database does not have: {attr}",
                        snippet,
                    )
                )
    return findings


def _load_baseline(root: Path) -> set[tuple[str, str]]:
    """Known findings, so the tool can be used as a ratchet.

    Keyed on (file, source text of the offending line) -- NOT on the line
    number, which any unrelated edit would shift.
    """
    path = root / "tools" / "vacuous_test_baseline.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    return {
        (entry["file"], entry["source"])
        for entry in payload.get("findings", [])
        if "file" in entry and "source" in entry
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repo root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when a NEW vacuous assertion is found (baseline is allowed)",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="rewrite tools/vacuous_test_baseline.json with the current findings",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    findings = scan(root)

    if args.write_baseline:
        payload = {
            "version": "1.1.0",
            "updated": "2026-10-20",
            "note": (
                "Known source-text / unpersisted-field assertions. They are not "
                "behaviour tests; each needs either a behavioural replacement or a "
                "recorded reason to stay. Keyed on the source text of the line, "
                "not the line number. New findings must not be added here."
            ),
            "findings": [
                {"file": file, "line": lineno, "reason": reason, "source": snippet}
                for file, lineno, reason, snippet in findings
            ],
        }
        (root / "tools" / "vacuous_test_baseline.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"baseline written: {len(findings)} finding(s)")
        return 0

    if not findings:
        print("vacuous-test scan: OK (no vacuous assertions)")
        return 0

    baseline = _load_baseline(root)
    known = [f for f in findings if (f[0], f[3]) in baseline]
    new = [f for f in findings if (f[0], f[3]) not in baseline]

    print(f"vacuous-test scan: {len(findings)} finding(s) "
          f"({len(known)} known, {len(new)} new)")
    for file, lineno, reason, _snippet in new:
        print(f"  NEW {file}:{lineno}: {reason}")

    if args.strict and new:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
