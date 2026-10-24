"""Workspace pruner â€” removes generated, cached and scratch artefacts (dry-run by default).

Categories (each independently selectable):

  caches     ``__pycache__``, ``.ruff_cache``, ``.pytest_cache``, ``.hypothesis``,
             ``.mypy_cache``, ``.benchmarks`` â€” safe to delete any time.
  logs       ``*.log`` at any depth (``run.log``, hook logs).
  scratch    ``temp_*.py``, ``tmp_*.py``, ``_scratch*``, ``*.orig``, ``*.rej``,
             ``*.bak-*`` â€” editor/agent leftovers.
  editors    ``.vscode/``, ``.idea/`` at the root only.
  generated  the runtime data trees that ``.gitignore`` already declares:
             ``data/security/`` (the audit log), ``data/rag/``, ``data/master/``,
             ``data/reports/``, ``data/cache*``, ``data/maps/``, ``data/motors/``,
             ``outputs/`` â€” deletable but NOT by default (see ``--include-generated``).
  trackers   files that are tracked by git but ignored by ``.gitignore`` â€” the
             script lists them and, with ``--untrack``, runs ``git rm --cached``
             (the working file stays; this is the 36 MB saving).

Usage:
    python tools/prune_workspace.py                 # dry-run, prints the plan
    python tools/prune_workspace.py --json          # machine-readable
    python tools/prune_workspace.py --apply         # delete caches/logs/scratch/editors
    python tools/prune_workspace.py --apply --include-generated
    python tools/prune_workspace.py --untrack       # git rm --cached for ignored-but-tracked files

Exit codes: 0 ok آ· 1 a deletion failed آ· 2 usage error. The tool never touches
``.git/``, the venv (``.venv``), or any file under ``engine/``, ``services/``,
``database/``, ``adapters/``, ``runtime/``, ``scenario/``, ``decision/``,
``tools/``, ``architecture/``, ``.githooks/`` or ``.github/``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CACHE_DIRS = {
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".hypothesis",
    ".mypy_cache",
    ".benchmarks",
}
EDITOR_DIRS = {".vscode", ".idea"}
GENERATED_DIRS = {
    "data/security",
    "data/rag",
    "data/master",
    "data/reports",
    "data/cache",
    "data/copernicus_cache",
    "data/maps",
    "data/motors",
    "outputs",
}
PROTECTED_PREFIXES = (
    ".git",
    ".venv",
    "engine",
    "services",
    "database",
    "adapters",
    "runtime",
    "scenario",
    "decision",
    "tools",
    "architecture",
    ".githooks",
    ".github",
)


def _iter_nodes(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.exists():
            continue
        relative = path.relative_to(root)
        if any(part in (".git", ".venv", "__pycache__") for part in relative.parts[:-1]):
            continue
        yield path, relative


def _size(path: Path) -> int:
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def _is_protected(relative: Path) -> bool:
    if not relative.parts:
        return True
    return relative.parts[0] in PROTECTED_PREFIXES


def classify(root: Path = REPO_ROOT) -> dict[str, list[tuple[Path, Path, int]]]:
    """Return {category: [(absolute, relative, size)]} for every candidate."""
    found: dict[str, list[tuple[Path, Path, int]]] = {
        "caches": [],
        "logs": [],
        "scratch": [],
        "editors": [],
        "generated": [],
    }
    for path, relative in _iter_nodes(root):
        name = path.name
        if path.is_dir():
            if name in CACHE_DIRS:
                found["caches"].append((path, relative, _size(path)))
                continue
            if name in EDITOR_DIRS and len(relative.parts) == 1:
                found["editors"].append((path, relative, _size(path)))
                continue
            if relative.as_posix() in GENERATED_DIRS:
                found["generated"].append((path, relative, _size(path)))
                continue
        if path.is_file():
            if name.endswith(".log"):
                found["logs"].append((path, relative, _size(path)))
            elif (
                name.startswith(("temp_", "tmp_"))
                or name.startswith("_scratch")
                or name.endswith((".orig", ".rej"))
                or ".bak-" in name
            ):
                found["scratch"].append((path, relative, _size(path)))
    # de-duplicate: a child of an already-listed directory is covered by it
    for category, rows in found.items():
        rows.sort(key=lambda row: len(row[1].parts))
        kept: list[tuple[Path, Path, int]] = []
        seen: list[Path] = []
        for absolute, relative, size in rows:
            if any(relative == s or s in relative.parents for s in seen):
                continue
            seen.append(relative)
            kept.append((absolute, relative, size))
        found[category] = kept
    return found


def _split_z(text: str) -> list[str]:
    """``git -z`` output is NUL-separated and never quoted — use that."""
    return [entry for entry in text.split("\0") if entry.strip()]


def tracked_relpaths(root: Path = REPO_ROOT) -> set[str]:
    """Repo-relative POSIX paths git tracks (SEC-12).

    The prune tool used to delete by prefix rules only, so ``*.log`` files
    that are *tracked* (``run.log`` is one) lost their working copy on
    ``--apply``. Tracked paths are now excluded from deletion, and a failure
    to read the index is an error rather than an empty set — an empty set
    would disable the guard exactly when git is unavailable.
    """
    process = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return set(_split_z(process.stdout))


def ignored_but_tracked(root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    """Tracked files that ``.gitignore`` already covers — the 36 MB class."""
    try:
        tracked_process = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    tracked = _split_z(tracked_process.stdout)
    if not tracked:
        return []
    ignored_process = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        cwd=str(root),
        input="\0".join(tracked),
        capture_output=True,
        text=True,
        timeout=60,
    )
    ignored = _split_z(ignored_process.stdout)
    sizes: list[tuple[str, int]] = []
    for relative in ignored:
        path = root / relative
        try:
            sizes.append((relative, _size(path) if path.exists() else 0))
        except OSError:
            continue
    return sorted(sizes, key=lambda row: -row[1])


def _delete(rows: list[tuple[Path, Path, int]], apply: bool) -> tuple[int, int]:
    freed = 0
    failures = 0
    for absolute, relative, size in rows:
        if not apply:
            print(f"  would remove {relative.as_posix()} ({size / 1024:.0f} KB)")
            continue
        try:
            if absolute.is_dir():
                shutil.rmtree(absolute)
            else:
                absolute.unlink()
            print(f"  removed {relative.as_posix()} ({size / 1024:.0f} KB)")
            freed += size
        except OSError as exc:
            print(f"  FAILED {relative.as_posix()}: {exc}")
            failures += 1
    return freed, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="prune_workspace", description=__doc__)
    parser.add_argument("--apply", action="store_true", help="delete (default: dry-run)")
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="also delete the generated data/ trees (off by default: they are rebuildable but expensive)",
    )
    parser.add_argument(
        "--untrack",
        action="store_true",
        help="git rm --cached the ignored-but-tracked files (keeps the working copy)",
    )
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    # SEC-12: ``--root`` used to be able to point at the filesystem root, and
    # the classifier then walked it (an operator typo — ``--root ..`` — walked
    # the whole drive until it was killed). The workspace pruner is a repo
    # tool: the root must be the repository or a subtree of it.
    repo_root = REPO_ROOT.resolve()
    if root != repo_root and repo_root not in root.parents:
        print(f"ERROR: --root must be inside the repository ({repo_root}); got {root}")
        return 2
    found = classify(root)

    selected = ["caches", "logs", "scratch", "editors"]
    if args.include_generated:
        selected.append("generated")

    print(f"workspace prune — {root}  ({'APPLY' if args.apply else 'DRY-RUN'})")
    total = 0
    failures = 0
    # SEC-12: the tracked-file guard. Deleting a tracked file's working copy
    # is data loss the repo does not notice until the next checkout, so the
    # guard is read before any deletion and honored in dry-run and apply
    # alike. If the index cannot be read, --apply is refused (fail closed).
    tracked: set[str] | None = None
    try:
        tracked = tracked_relpaths(root)
    except (OSError, subprocess.SubprocessError) as exc:
        if args.apply:
            print(f"ERROR: cannot read the git index ({exc}); refusing to apply.")
            return 2
        print(f"NOTE: cannot read the git index ({exc}); the tracked-file guard is off.")
    skipped_tracked = 0
    if not args.json:
        for category in selected:
            rows = [row for row in found[category] if not _is_protected(row[1])]
            if tracked is not None:
                keep = [row for row in rows if row[1].as_posix() not in tracked]
                skipped_tracked += len(rows) - len(keep)
                rows = keep
            if not rows:
                continue
            print(f"{category}: {len(rows)} item(s), {sum(r[2] for r in rows) / 1024:.0f} KB")
            freed, failed = _delete(rows, args.apply)
            total += freed
            failures += failed
    if skipped_tracked:
        print(
            f"skipped {skipped_tracked} tracked file(s) — the guard keeps their "
            "working copy (run 'git rm' for a real removal)"
        )

    stale = ignored_but_tracked(root)
    if stale:
        print(f"\nignored-but-tracked ({len(stale)} file(s), "
              f"{sum(size for _, size in stale) / 1048576:.1f} MB in git):")
        for relative, size in stale:
            print(f"  {relative} ({size / 1048576:.1f} MB)")
        if args.untrack:
            for relative, _size in stale:
                result = subprocess.run(
                    ["git", "rm", "--cached", "--quiet", relative],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                )
                print(f"  untracked {relative} (exit {result.returncode})")
                if result.returncode != 0:
                    failures += 1
        else:
            print("  (run with --untrack to remove them from the index; the working copy stays)")

    if args.json:
        def _visible(rows):
            if tracked is None:
                return [row for row in rows if not _is_protected(row[1])]
            return [
                row
                for row in rows
                if not _is_protected(row[1]) and row[1].as_posix() not in tracked
            ]

        payload = {
            "categories": {
                category: [
                    {"path": relative.as_posix(), "bytes": size}
                    for _absolute, relative, size in _visible(found[category])
                ]
                for category in selected
            },
            "ignored_but_tracked": [
                {"path": relative, "bytes": size} for relative, size in stale
            ],
            "apply": args.apply,
        }
        print(json.dumps(payload, indent=2))

    print(f"\nSUMMARY categories={','.join(selected)} "
          f"freed_kb={total / 1024:.0f} untrack_candidates={len(stale)} apply={args.apply}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
