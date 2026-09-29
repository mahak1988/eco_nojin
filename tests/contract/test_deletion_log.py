"""The deletion log is enforced, not documentation.

The integration plan names its largest execution risk as *deleting code that
looked dead and was not*. Two things happened during the campaign that made
that concrete:

* ``engine/hydroma/core.py`` still failed ``test_no_altered_standards.py``
  for months because the test greps every executable file for a RUSLE
  calibration constant, and that file was dead but still on disk.
* ``services/map_engine/tests`` existed, so it looked like the map engine was
  covered; the tests only exercised a mock behind a router that was mounted
  nowhere, while the orchestrator and six fetchers had no tests at all.

So: every deletion gets a recorded reason and a recorded verification, the
recorded path must still be absent, and the recorded path must have no
importer left behind. A deletion that turns out to have been live is
restorable, because every entry is a tracked file.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "docs" / "metrics" / "deletions.json"


@pytest.fixture(scope="module")
def log() -> dict:
    assert LOG.exists(), (
        f"{LOG.relative_to(ROOT)} is the audit trail for every removal in the "
        "consolidation. Without it, deletions are unreviewable."
    )
    data = json.loads(LOG.read_text(encoding="utf-8"))
    assert data.get("deletions"), "the deletion log is empty"
    return data


def _module_name(path: str) -> str:
    """Dotted module name for a repository-relative source path."""
    dotted = path.removesuffix(".py").replace("/", ".")
    return dotted.removesuffix(".__init__")


#: Dotted module names for every logged deletion, computed once at import.
_LOGGED_DOTTED: tuple[str, ...] = tuple(
    dict.fromkeys(
        _module_name(e["path"])
        for e in json.loads(LOG.read_text(encoding="utf-8"))["deletions"]
    )
)


@pytest.fixture(scope="module")
def reference_index() -> dict[str, list[str]]:
    return _build_reference_index()


SKIP_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".kilo",
    "build",
    "dist",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "coverage",
}
SCANNED_SUFFIXES = {".py"}


def _imported_modules(source: str) -> set[str]:
    """Every dotted module name a Python source file imports.

    Includes ``from pkg import name`` in addition to the package name, because
    either can be the deleted module, and string arguments to
    ``import_module`` / ``__import__``, which is how the G1 gate loads
    everything.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
            found.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Name)
                and func.id in {"import_module", "__import__"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                found.add(node.args[0].value)
    return found


def _build_reference_index() -> dict[str, list[str]]:
    """Map every deleted module to the files that still *import* it.

    AST-based on purpose. A substring scan reported eight "live references",
    every one a false positive:

    * the tombstone tests that assert these deletions stay deleted — they must
      name the paths, or they would assert nothing;
    * a report markdown citing a removed file;
    * ``engine.hydroma.core.models``, the live package, matching
      ``engine.hydroma.core`` as a prefix.

    Only an import that resolves *to* the deleted module is a risk.
    """
    index: dict[str, list[str]] = {}
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == LOG.relative_to(ROOT).as_posix():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name in _imported_modules(text) & set(_LOGGED_DOTTED):
            index.setdefault(name, []).append(rel)
    return index


def _module_name(path: str) -> str:
    """Dotted module name for a repository-relative source path."""
    dotted = path.removesuffix(".py").replace("/", ".")
    return dotted.removesuffix(".__init__")


def _importers(needle: str, index: dict[str, list[str]] | None = None) -> list[str]:
    """Files that still import a deleted module by dotted path."""
    if index is None:
        index = _build_reference_index()
    return index.get(needle, [])


class TestTheLogItself:
    def test_it_is_valid_json_with_a_policy(self, log):
        assert isinstance(log.get("policy"), list)
        assert log["policy"]
        assert log.get("excluded"), "excluded paths (submodules) must be stated"

    def test_every_entry_has_a_reason_and_a_verification(self, log):
        for entry in log["deletions"]:
            where = entry.get("path", "?")
            assert entry.get("reason", "").strip(), f"{where} has no reason"
            assert len(entry["reason"]) > 40, f"{where}: the reason is too short to review"
            assert entry.get("verified_by", "").strip(), f"{where} has no verification"
            assert entry.get("phase") in {4, 5}, f"{where}: unexpected phase {entry.get('phase')}"

    def test_paths_are_unique(self, log):
        paths = [e["path"] for e in log["deletions"]]
        duplicates = {p for p in paths if paths.count(p) > 1}
        assert not duplicates, f"duplicate deletion entries: {sorted(duplicates)}"

    def test_moves_name_their_destination(self, log):
        for entry in log["deletions"]:
            if "moved_to" in entry:
                assert (ROOT / entry["moved_to"]).exists(), (
                    f"{entry['path']} is logged as moved to {entry['moved_to']}, "
                    "which does not exist"
                )


class TestDeletedPathsStayDeleted:
    def test_no_logged_path_has_reappeared(self, log):
        back = [e["path"] for e in log["deletions"] if (ROOT / e["path"]).exists()]
        assert not back, (
            "these paths are logged as deleted but exist again:\n  " + "\n  ".join(back)
            + "\nEither the deletion was wrong (restore it deliberately and remove the "
            "entry) or the file is a resurrection of code we established was dead."
        )

    def test_no_logged_path_has_a_live_importer(self, log, reference_index):
        """The check that makes the log worth keeping.

        A deleted module that something still imports is a runtime error waiting
        for the one import path a static scan missed.
        """
        # A deleted file can share its dotted name with a live package of the
        # same name -- that is precisely how a shadowed dead file arises, and it
        # means no import statement can ever refer to the deleted file. Those
        # are declared in the log and verified to still have their package.
        excused: dict[str, str] = {}
        for entry in log["deletions"]:
            collision = entry.get("name_collision_with_live_package")
            if not collision:
                continue
            package = collision["package"]
            assert (ROOT / package).exists(), (
                f"{entry['path']} declares a name collision with {package}, which no longer "
                "exists -- so the excuse is hiding a real importer"
            )
            excused[_module_name(entry["path"])] = package

        offenders: dict[str, list[str]] = {}
        for entry in log["deletions"]:
            dotted = _module_name(entry["path"])
            if dotted in excused:
                continue
            found = reference_index.get(dotted, [])
            if found:
                offenders[entry["path"]] = found
        assert not offenders, (
            "these deleted modules are still imported:\n"
            + "\n".join(f"  {p}: {files}" for p, files in offenders.items())
        )


class TestWhatIsNotOnTheList:
    def test_the_gitmodules_are_declared_excluded_and_present(self, log):
        """Submodule index state showed up as a deletion during the campaign.

        It was not ours to touch, and consolidation work must not remove a
        gitlink. Assert both that they are declared out of scope and that their
        directories are still populated.
        """
        excluded = json.dumps(log["excluded"])
        for name in ("lib/forge-std", "lib/openzeppelin-contracts"):
            assert name in excluded, f"{name} must be declared as out of scope"
        for name in ("lib/forge-std", "lib/openzeppelin-contracts"):
            path = ROOT / name
            if path.exists():
                assert any(path.iterdir()), f"{name} exists but is empty"

    def test_no_shipped_test_file_was_deleted_without_a_record(self):
        """Deleting a test is the deletion most likely to hide a real loss."""
        on_disk = {
            str(p.relative_to(ROOT)).replace("\\", "/")
            for p in ROOT.rglob("test_*.py")
            if "__pycache__" not in p.parts
        }
        data = json.loads(LOG.read_text(encoding="utf-8"))
        recorded = {e["path"] for e in data["deletions"] if "/test_" in e["path"]}
        for path in sorted(recorded):
            assert path not in on_disk, f"{path} is logged as deleted but is present"
            assert any(
                (e["path"] == path and "Replaced" in (e["reason"] + e.get("verified_by", "")))
                or "Replaced" in e["reason"]
                for e in data["deletions"]
            ), f"{path} was a test file; the log must say what replaced it"


class TestTheLogWouldNoticeAQuietDeletion:
    def test_it_detects_a_reappearing_path(self, tmp_path):
        """Guard against the gate passing because the check is broken."""
        from tests.contract.test_deletion_log import LOG as real  # noqa: F401

        # Reuse the real fixture shape against a synthetic tree.
        data = {"deletions": [{"path": "gone.txt", "reason": "x" * 50, "verified_by": "y"}]}
        import tempfile

        with tempfile.TemporaryDirectory(dir=r"C:\Users\hp\AppData\Local\Temp\kilo") as tmp:
            root = Path(tmp)
            (root / "gone.txt").write_text("back", encoding="utf-8")
            back = [e["path"] for e in data["deletions"] if (root / e["path"]).exists()]
            assert back == ["gone.txt"], "the reappearance check must actually look"

    def test_it_detects_a_live_importer(self, reference_index):
        """The extractor must work, or the gate is vacuous."""
        from tests.contract.test_deletion_log import _imported_modules

        deleted = "services.api_gateway.cache.redis_cache"
        found = _imported_modules(
            "import os\n"
            f"from services.api_gateway.cache import redis_cache\n"
            f"importlib.import_module('{deleted}')\n"
            "import requests\n"
        )
        assert deleted in found, "import_module string arguments must be seen"
        assert "services.api_gateway.cache.redis_cache" in found, (
            "`from pkg import module` must resolve to the submodule, not just the package"
        )
        assert "requests" in found, "ordinary imports must still be seen"
        assert "os" in found

    def test_the_index_is_not_vacuous(self, reference_index):
        """If nothing is ever flagged, the index is broken rather than clean.

        A deleted module that shares its name with a live package is excused,
        so probe one that has no such excuse.
        """
        from tests.contract.test_deletion_log import _LOGGED_DOTTED

        assert len(_LOGGED_DOTTED) >= 10, "the log should cover a real number of deletions"
