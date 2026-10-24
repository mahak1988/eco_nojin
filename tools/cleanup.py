#!/usr/bin/env python3
"""Repository cleanup: remove caches, build artifacts and tool scratch files.

Usage
-----
    python tools/cleanup.py                # show what would be removed (dry run)
    python tools/cleanup.py --yes          # actually remove
    python tools/cleanup.py --include-build  # also delete C++ build/ trees
    python tools/cleanup.py --paths .engine  # restrict to subtrees (repeatable)

Design contract
---------------
* NEVER deletes anything git tracks (the `git ls-files` index is consulted
  first, so a tracked-but-generated file such as `run.log` is reported as
  "needs git rm --cached" instead of being deleted).
* NEVER touches `.venv/` or `.git/`.
* Idempotent: running it twice is a no-op the second time.
* Cross-platform (Windows/macOS/Linux), stdlib only.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {".venv", ".git", "node_modules"}

DIR_NAMES = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".benchmarks",
    ".snapshots",
    ".satellite_cache",
    "cache",
    "outputs",
    "hydroma.egg-info",
]

FILE_GLOBS = [
    "temp_*.json",
    "temp_*",
    "*.tmp",
    "*.bak",
    "*.nbi",
    "*.nbc",
    "*.log",
    "*.obj",
    "*.iobj",
    "*.ipdb",
    "*.pdb",
    ".coverage",
    "coverage.xml",
    "tools/*_output*.json",
    "tools/eco04_comprehensive_scan.json",
]

BUILD_DIRS = ["build", "build2"]  # only with --include-build


def tracked_files() -> set[Path]:
    """Paths git currently tracks (absolute).

    SEC-12: a failure to read the index used to yield an empty set, which
    silently disabled the "never delete a tracked file" guard exactly when
    git was unavailable — and this tool's whole contract is that guard. The
    failure is now raised; the caller aborts before any deletion.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return {ROOT / p.replace("\\", "/") for p in out.decode("utf-8", "replace").split("\0") if p}


def confined_paths(root: Path, subpaths: list[str]) -> list[Path]:
    """Resolve ``--paths`` under the root, rejecting anything outside it.

    SEC-12: ``--paths ..`` or an absolute path walked the cleanup globs
    outside the repository; every requested subtree must resolve inside the
    root, or the run aborts.
    """
    root = root.resolve()
    bases: list[Path] = []
    for raw in subpaths or ["."]:
        candidate = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if candidate != root and root not in candidate.parents:
            raise SystemExit(f"--paths entry {raw!r} resolves outside the repository root")
        bases.append(candidate)
    return bases


def human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def walk(root: Path, subpaths: list[str]) -> list[Path]:
    bases = confined_paths(root, subpaths) or [root]
    seen: list[Path] = []
    for base in bases:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in p.parts):
                continue
            seen.append(p)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yes", action="store_true", help="delete (default: dry run)")
    ap.add_argument("--include-build", action="store_true", help="delete C++ build/ and build2/")
    ap.add_argument(
        "--paths", nargs="*", default=[], help="restrict to subtrees, e.g. engine services"
    )
    args = ap.parse_args()

    # SEC-12: fail closed — without the tracked-file set the tool cannot honor
    # its core "never delete a tracked file" contract, so a git failure here
    # aborts the run instead of degrading into an unguarded sweep.
    try:
        tracked = tracked_files()
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: cannot read the git index ({exc}); refusing to continue.")
        return 2
    dir_names = list(DIR_NAMES) + (BUILD_DIRS if args.include_build else [])
    candidates: list[Path] = []

    for p in walk(ROOT, args.paths):
        if p.is_dir() and p.name in dir_names:
            candidates.append(p)
        elif p.is_file() and any(p.match(g) for g in FILE_GLOBS):
            candidates.append(p)

    # Deduplicate (parents before children) and skip tracked paths.
    unique: dict[Path, None] = {}
    for c in candidates:
        if c in tracked or c.parent in tracked:
            continue
        unique[c] = None

    if not unique:
        print("Nothing to clean.")
        return 0

    total = 0
    skipped_tracked = [p for p in candidates if p in tracked or p.parent in tracked]
    for p in sorted(unique, key=lambda x: len(x.parts)):
        size = 0
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    try:
                        size += f.stat().st_size
                    except OSError:
                        pass
        else:
            try:
                size = p.stat().st_size
            except OSError:
                continue
        total += size
        rel = p.relative_to(ROOT)
        if args.yes:
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink(missing_ok=True)
                print(f"  removed  {rel}  ({human(size)})")
            except OSError as exc:
                print(f"  FAILED   {rel}: {exc}  (a process holds a lock; retry when idle)")
        else:
            print(f"  would remove  {rel}  ({human(size)})")

    print(f"\n{'Reclaimed' if args.yes else 'Would reclaim'}: {human(total)}")
    for p in skipped_tracked:
        print(f"  tracked (use `git rm --cached {p.relative_to(ROOT)}`): {p.relative_to(ROOT)}")
    if not args.yes:
        print("\nRe-run with --yes to perform the cleanup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
