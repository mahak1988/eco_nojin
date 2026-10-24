"""Every runtime-data path must be covered by a .gitignore rule.

Runtime artifacts — connector caches, DuckDB stores, the generated RAG
fallback corpus, the session report directory, and the append-only security
audit log — are recreated by tools and test runs. Committing one is a
repo-size regression and an evidence-hygiene problem: a stale
``data/security/audit.jsonl`` in history is a security lie, and a committed
``data/master/eco_nojin_master.duckdb`` silently pins a build that
``tools/build_master_duckdb.py`` owns outright.

The flip side matters just as much. An over-broad rule would silently remove
genuine source from the commit surface — ``data/model_registry.json``, the
links catalog, the builders themselves — so this module pins both directions:
runtime paths are ignored, source paths are not.

It also pins the invariant that **no tracked file matches a rule**, with one
documented exception: ``data/security/audit.jsonl`` is still in the index and
stays there until the owner executes the decision recorded in
``reports/release/COMMIT-PLAN-2026-10-10.md`` (decision A). An ignore rule
never untracks a file, so the rule can be present while the file is tracked;
any *other* tracked file matching a rule means the rule is wrong.

Matching is verified two independent ways: a small pure-Python gitignore
matcher (the primary check, so nothing is spawned) and, when a ``git`` binary
is available, ``git check-ignore --no-index`` as the authority. ``--no-index``
is load-bearing: plain ``git check-ignore`` answers "is this path ignored
*for the current index*", which reports a tracked file as *not* ignored even
when a rule matches it. Both paths run offline and finish in milliseconds.
"""

from __future__ import annotations

import shutil
import subprocess
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE_PATH = REPO_ROOT / ".gitignore"

#: Runtime artifacts that must never be committable. Directory roots are
#: listed with a trailing slash so directory-only rules are exercised; one
#: representative file inside a few of them is listed too, because "the root
#: is ignored" must imply "everything under it is ignored".
RUNTIME_PATHS = (
    "data/security/audit.jsonl",
    "data/cache/",
    "data/copernicus_cache/",
    "data/motors/",
    "data/maps/",
    "data/master/",
    "data/master/eco_nojin_master.duckdb",
    "data/rag/",
    "data/rag/hydroma_scientific_corpus.json",
    "data/reports/",
    "data/reports/report_0016ae04-6a47-4574-8087-90d4cb0e1d7f.json",
    "data/food_security.duckdb",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
)

#: Genuine source files that must stay on the commit surface. If any of these
#: is ever reported ignored, the rule set has grown too broad.
SOURCE_PATHS = (
    ".env.example",
    "conftest.py",
    "data/model_registry.json",
    "data/links/external_links.json",
    "tools/build_master_duckdb.py",
    "tools/build_food_security_table.py",
    "tools/tests/test_build_food_security_table.py",
    "tools/tests/test_gitignore_covers_runtime_data.py",
    "services/security/audit.py",
    "engine/hydroma/data_pipeline/pipeline.py",
    "engine/models/registry.py",
)

#: The one tracked file that deliberately matches a rule: it stays in the
#: index until the owner runs ``git rm --cached data/security/audit.jsonl``.
TRACKED_IGNORE_EXCEPTION = "data/security/audit.jsonl"

Rule = tuple[str, bool, bool, bool]


def _load_rules() -> list[Rule]:
    """Parse ``.gitignore`` into ``(pattern, anchored, dir_only, negate)``.

    Only the subset this repository needs is implemented: comments, blank
    lines, ``!`` negation, trailing-slash directory-only rules, anchored
    rules (any slash that is not the trailing one) and unanchored basename
    rules. Rules apply in file order, last match wins, as in git.
    """
    rules: list[Rule] = []
    for raw in GITIGNORE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        if negate:
            line = line[1:].strip()
        dir_only = line.endswith("/")
        if dir_only:
            line = line.rstrip("/")
        anchored = line.startswith("/") or "/" in line
        line = line.lstrip("/")
        if line:
            rules.append((line, anchored, dir_only, negate))
    return rules


def _rule_matches(rule: Rule, parts: tuple[str, ...], is_dir: bool) -> bool:
    pattern, anchored, dir_only, _negate = rule
    if anchored:
        for end in range(1, len(parts) + 1):
            prefix_is_dir = end < len(parts) or is_dir
            if dir_only and not prefix_is_dir:
                continue
            candidate = PurePosixPath(*parts[:end]).as_posix()
            if fnmatchcase(candidate, pattern):
                return True
        return False
    for index, component in enumerate(parts):
        component_is_dir = index < len(parts) - 1 or is_dir
        if dir_only and not component_is_dir:
            continue
        if fnmatchcase(component, pattern):
            return True
    return False


def _is_ignored(rules: list[Rule], path: str) -> bool:
    parts = PurePosixPath(path).parts
    is_dir = path.endswith("/")
    ignored = False
    for rule in rules:
        if _rule_matches(rule, parts, is_dir):
            ignored = not rule[3]
    return ignored


def _require_git() -> str:
    git = shutil.which("git")
    if git is None:  # pragma: no cover - git ships with every dev checkout
        pytest.skip("git binary unavailable; the pure-Python matcher still guards the rules")
    return git


def _git_ignores(git: str, path: str) -> bool:
    """``git check-ignore --no-index`` for one path (True means ignored)."""
    result = subprocess.run(
        [git, "check-ignore", "--no-index", "-q", "--", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    pytest.fail(f"git check-ignore failed for {path}: {result.stderr.strip()}")


def test_gitignore_covers_every_runtime_path() -> None:
    """The local matcher must ignore every runtime path from the audit."""
    rules = _load_rules()
    uncovered = [path for path in RUNTIME_PATHS if not _is_ignored(rules, path)]
    assert uncovered == [], (
        "runtime paths not covered by any .gitignore rule "
        f"(see reports/release/COMMIT-PLAN-2026-10-10.md): {uncovered}"
    )


def test_git_agrees_every_runtime_path_is_ignored() -> None:
    """``git check-ignore --no-index`` must ignore every runtime path too."""
    git = _require_git()
    uncovered = [path for path in RUNTIME_PATHS if not _git_ignores(git, path)]
    assert uncovered == [], f"git check-ignore does not ignore: {uncovered}"


def test_gitignore_keeps_source_paths_committable() -> None:
    rules = _load_rules()
    wrongly_ignored = [path for path in SOURCE_PATHS if _is_ignored(rules, path)]
    assert wrongly_ignored == [], f"source paths wrongly ignored: {wrongly_ignored}"


def test_git_agrees_source_paths_are_not_ignored() -> None:
    git = _require_git()
    wrongly_ignored = [path for path in SOURCE_PATHS if _git_ignores(git, path)]
    assert wrongly_ignored == [], f"source paths wrongly ignored: {wrongly_ignored}"


def test_no_tracked_file_matches_a_rule_beyond_the_documented_exception() -> None:
    """Only ``data/security/audit.jsonl`` may be tracked *and* matched.

    The exception exists on purpose: the runtime security log is still in the
    index and the owner has not yet decided whether to untrack it. Every
    other tracked file matching a rule would mean the rule silently swallows
    a source file that ``git add`` is expected to stage.
    """
    git = _require_git()
    listed = subprocess.run(
        [git, "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    tracked = [path for path in listed.split("\0") if path]
    assert tracked, "git ls-files returned no tracked files; is this a git repository?"

    probe = subprocess.run(
        [git, "check-ignore", "--no-index", "--stdin", "-z", "-v"],
        cwd=REPO_ROOT,
        input="\0".join(tracked),
        capture_output=True,
        text=True,
    )
    if probe.returncode == 1:
        pytest.fail(
            "no tracked file matches a rule, but "
            f"{TRACKED_IGNORE_EXCEPTION} is expected to match "
            "(its rule documents the pending untrack decision)"
        )
    if probe.returncode != 0:
        pytest.fail(f"git check-ignore failed: {probe.stderr.strip()}")

    fields = [field for field in probe.stdout.split("\0") if field]
    matched_paths = {fields[index + 3] for index in range(0, len(fields) - 3, 4)}
    unexpected = sorted(matched_paths - {TRACKED_IGNORE_EXCEPTION})
    assert unexpected == [], (
        "tracked files that match an ignore rule and are not the documented "
        f"exception: {unexpected}; the rule set has grown too broad"
    )
    assert TRACKED_IGNORE_EXCEPTION in matched_paths
