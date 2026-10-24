#!/usr/bin/env python
"""Collection-stability check: BOM bytes and missing package markers.

Two defects repeatedly broke the *whole* pytest collection rather than a
single test:

* a UTF-8 BOM (U+FEFF) at the start of a ``.py`` file — ``ast.parse`` rejects
  it with ``SyntaxError: invalid non-printable character U+FEFF``, so every
  test that parses the file dies;
* a directory under ``services/`` without an ``__init__.py`` — it resolves as
  a PEP 420 namespace package and pytest can no longer import a module
  beneath it.

Both are cheap to detect statically, so this check runs in CI and fails fast
instead of surfacing as a mysterious collection error.

Usage:
    python tools/check_collection_stability.py --root .
Exit code 0 = clean, 1 = findings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BOM = b"\xef\xbb\xbf"
SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}


def _iter_python_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        out.append(path)
    return out


def find_bom_files(root: Path) -> list[Path]:
    """Files that start with a UTF-8 BOM."""
    return [p for p in _iter_python_files(root) if p.read_bytes().startswith(BOM)]


def find_missing_markers(root: Path) -> list[Path]:
    """Service directories that lack an ``__init__.py``."""
    services = root / "services"
    if not services.is_dir():
        return []
    missing: list[Path] = []
    for path in sorted(services.iterdir()):
        if not path.is_dir() or path.name.startswith("_") or path.name == "tests":
            continue
        if not (path / "__init__.py").exists():
            missing.append(path)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    bom = find_bom_files(root)
    markers = find_missing_markers(root)

    print("=" * 70)
    print("COLLECTION STABILITY CHECK")
    print("=" * 70)
    print(f"Root: {root}")
    print()

    if bom:
        print(f"BOM files ({len(bom)}):")
        for path in bom:
            print(f"  - {path.relative_to(root)}")
        print("  -> a BOM makes ast.parse() fail; the whole collection breaks.")
        print()
    else:
        print("BOM files: 0 (clean)")

    if markers:
        print(f"Missing package markers ({len(markers)}):")
        for path in markers:
            print(f"  - {path.relative_to(root)}")
        print("  -> a directory without __init__.py resolves as a PEP 420")
        print("     namespace package and pytest cannot import beneath it.")
        print()
    else:
        print("Missing package markers: 0 (clean)")

    print("=" * 70)
    if bom or markers:
        print("Status: FAIL")
        return 1
    print("Status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
