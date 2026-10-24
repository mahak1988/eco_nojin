#!/usr/bin/env python3
"""Phantom test-path check (honesty contract 3).

Walks the repository from this file's parent directory's parent (the repo root)
and collects every cited ``tests/unit|models|contract/*.py`` path from the text
files a human actually reads (``*.md``, ``*.yaml``, ``*.py``, ``*.json``,
``*.toml``, ``*.txt``). Any cited path that does not exist on disk is a phantom:
a citation that promises evidence which is not in the tree.

Excluded by design, and why:
  * ``.git``, ``.venv``, ``__pycache__``, ``.hypothesis``, ``.pytest_cache``,
    ``site-packages`` -- VCS and environment noise; never evidence.
  * ``reports/`` (every directory with that name, at any depth) -- the
    cited-phantom families themselves live outside ``reports/``. Reports quote
    other things' paths; scanning them would add no phantom and would make the
    check depend on documents about the problem rather than the problem.

Usage:
    python tools/phantom_path_check.py

Exit code:
    1 when at least one cited path is missing, 0 otherwise.

Stdlib only; safe to import (``importlib.util.spec_from_file_location``) or run
as a script. The scan entry point is ``scan_missing(root)``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: Directories never walked (matched by name, at any depth).
SKIP_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".hypothesis",
        ".pytest_cache",
        "site-packages",
        "reports",
    }
)

#: File extensions treated as citable text.
TEXT_SUFFIXES = frozenset({".md", ".yaml", ".py", ".json", ".toml", ".txt"})

#: Maximum size of a file whose contents are scanned (bytes).
MAX_FILE_BYTES = 2 * 1024 * 1024

#: The phantom families. A path under one of these prefixes that does not exist
#: on disk is a phantom, not merely a differently-located test.
PHANTOM_PREFIXES = ("tests/unit/", "tests/models/", "tests/contract/")

_INLINE_RE = re.compile(r"(tests/(?:unit|models|contract)/[\w./-]+\.py)")

_FIELD_RE = re.compile(
    r"(?:^|\n)\s*(?:parity_tests|unit_tests|test_file|test_file)\s*:\s*\[?\s*[\"']?"
    r"(tests/(?:unit|models|contract)/[\w./-]+\.py)"
)

_LIST_ITEM_RE = re.compile(
    r"(?:^|\n)\s{2,}(?:-\s+)?[\"']?(tests/(?:unit|models|contract)/[\w./-]+\.py)"
)


def _normalise(raw: str) -> str:
    """Drop a trailing ``::test_name`` suffix and any stray quote characters."""
    path = raw.split("::", 1)[0].strip()
    return path.strip("\"'\u201c\u201d \t,")


def _repo_root() -> Path:
    """Repo root, derived from this file's location: <root>/tools/this_file."""
    return Path(__file__).resolve().parent.parent


def _candidate_files(root: Path) -> list[Path]:
    """Every citable text file under ``root``, skipping excluded directories."""
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except (OSError, PermissionError):
            continue
        for entry in entries:
            try:
                is_dir = entry.is_dir()
            except OSError:
                continue
            if is_dir:
                if entry.name in SKIP_DIRS:
                    continue
                stack.append(entry)
                continue
            if entry.suffix in TEXT_SUFFIXES:
                try:
                    if entry.stat().st_size < MAX_FILE_BYTES:
                        found.append(entry)
                except OSError:
                    continue
    return found


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""


def _cited_paths(text: str) -> set[str]:
    """All distinct cited ``tests/...`` paths in ``text`` (normalised)."""
    paths: set[str] = set()
    for regex in (_INLINE_RE, _FIELD_RE, _LIST_ITEM_RE):
        for match in regex.finditer(text):
            normalised = _normalise(match.group(1))
            if normalised:
                paths.add(normalised)
    return paths


#: Every citation regex below contains the literal ``tests/``, so a file that
#: does not contain that byte sequence cannot contribute a path. Purely an
#: optimisation: it never changes what is collected.
_CITATION_FINGERPRINT = b"tests/"


def scan_missing(root: Path) -> list[str]:
    """Return the sorted cited paths under ``root`` that do not exist on disk."""
    root = Path(root).resolve()
    missing: set[str] = set()
    for path in _candidate_files(root):
        raw = _read_bytes(path)
        if _CITATION_FINGERPRINT not in raw:
            continue
        for cited in _cited_paths(raw.decode("utf-8", errors="replace")):
            if cited.startswith(PHANTOM_PREFIXES) and not (root / cited).exists():
                missing.add(cited)
    return sorted(missing)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(argv[0]).resolve() if argv else _repo_root()
    missing = scan_missing(root)
    for path in missing:
        print(f"MISSING {path}")
    families = len({str(Path(path).parent) for path in missing})
    print(f"SUMMARY missing={len(missing)} families={families}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
