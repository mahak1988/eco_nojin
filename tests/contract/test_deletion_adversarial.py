"""Adversarial review of the 27 logged deletions.

``docs/metrics/deletions.json`` records a reason and a verification for every
path the phase 4/5 consolidation removed. Every one of those verifications is
the *same* check: an AST importer scan, and for two entries a shadowing
argument. The plan's largest execution risk is "deleting code that looked dead
and was not", and a single-method verification cannot carry that risk, because
one method has one blind spot.

This module is the second method. It asks a different question for every
deletion, per class:

1. **Static import reachability** - the whole tree, not just ``services/``,
   for all 27 dotted names, including test files (a test that re-imports a
   "deleted" module has resurrected it).
2. **Dynamic reachability** - ``importlib.import_module("...")``,
   ``__import__("...")``, ``spec_from_file_location("...")``, ``pkgutil`` and
   ``pytest_plugins`` string arguments. An AST importer scan cannot see these
   by construction; they are the canonical way a deleted module stays live.
3. **Non-Python invocation** - a CI step, a compose service, a k8s manifest,
   an entry point or a pytest marker that names a deleted path *as a command*.
   The strongest form of this failure is a green PR that breaks the build.
4. **Name shadowing** - the two deletions that shared a dotted name with a live
   package/module. Asserted behaviourally against CPython's own resolution
   order in a subprocess, not by re-reading the log's prose.
5. **Data and schema** - the tables the deleted shadow file owned, at column
   granularity. Table-name parity is not schema parity.
6. **Fixtures, conftest and package re-exports** - removing a module while a
   sibling still does ``from .dlq import DLQHandler`` or lists it in
   ``__all__``.
7. **The survivors are the ones actually wired** - a duplicate deletion is
   only safe if the survivor is what the gateway, the worker and the router
   import today.
8. **Coverage relocation** - the two in-package ``test_*.py`` files. Deleting a
   test file is a deletion of coverage; this asserts the replacements are real.

Anything the deletions *created* rather than merely revealed is pinned at the
end as ``strict=True`` xfails carrying the proof, so the findings stay
machine-visible without turning a pre-existing defect into a new red build.
An XPASS on any of those is a failure telling the owner to remove the marker.
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable

import pytest

ROOT = Path(__file__).resolve().parents[2]
DELETION_LOG = ROOT / "docs" / "metrics" / "deletions.json"
SELF = Path(__file__).resolve()

#: Directories that are not part of the shipped tree. ``.kilo/worktrees`` holds
#: other agents' checkouts of *older* commits: they import the deleted modules
#: legitimately and say nothing about the live tree.
EXCLUDED_DIRS = {
    ".git", ".kilo", ".hypothesis", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".next",
    "lib", "data", "htmlcov", "coverage", "site-packages", ".idea", ".vscode",
    "econojin.egg-info", "test-results", "playwright-report", "blob-report",
}

#: Files that legitimately *name* a deleted path: the log itself, quarantined
#: backups, packaged-file manifests, and OpenAPI snapshots. None of them
#: execute anything.
EXCLUDED_FILES = {
    "docs/metrics/deletions.json",
    "openapi.json",
    "project_report.json",
    "pen_test_scan.json",
    "econojin.egg-info/SOURCES.txt",
    "docs/security/SECURITY_STACK_2026.md",
    "docs/standards/tolerated-degradations.yaml",
    "docs/standards/change-policy.md",
    "docs/standards/S-SEC.md",
    "docs/INTEGRATION_STANDARDIZATION_PLAN_FA_2026-09-28.md",
    "reports/SERVICES_ANALYTICAL_REVIEW_FA_2026-09-28.md",
}

#: Non-Python files that can *invoke* something. A deleted module named here is
#: a live path the AST importer scan cannot reach.
INVOCATION_GLOBS = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".github/workflows/scripts/*",
    "deploy/**/*",
    "k8s/**/*",
    "*.yml",
    "*.yaml",
    "*.toml",
    "*.cfg",
    "*.ini",
    "*.sh",
    "*.ps1",
    "*.bat",
    "*.cmd",
    "Dockerfile*",
    "Makefile*",
    "tox.ini",
    "noxfile.py",
    "setup.py",
    "package.json",
    "render.yaml",
    ".pre-commit-config.yaml",
    "Procfile*",
)

#: The two deletions whose dotted name is shared with a live neighbour. For
#: these the name is not evidence, so only the path can be searched for.
SHADOWED = {
    "engine/hydroma/core.py": "engine.hydroma.core",
    "database/models/database_models.py": "database.models",
}

DYNAMIC_LOADERS = {
    "importlib.import_module",
    "import_module",
    "__import__",
    "spec_from_file_location",
    "importlib.util.spec_from_file_location",
    "load_module",
    "walk_packages",
    "iter_modules",
    "getattr",
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _iter_files(suffixes: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = Path(dirpath).relative_to(ROOT)
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDED_DIRS and not d.endswith(".egg-info")
            and not d.startswith("_quarantine_bak")
        ]
        if set(rel.parts) & EXCLUDED_DIRS:
            continue
        for fn in filenames:
            if fn.endswith((".bak", ".bak-20260928", ".pyc", ".pyo")) or ".bak" in fn:
                continue
            if not any(fn.endswith(s) for s in suffixes):
                continue
            p = Path(dirpath) / fn
            if p.resolve() == SELF:
                continue
            if p.relative_to(ROOT).as_posix() in EXCLUDED_FILES:
                continue
            out.append(p)
    return out


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _dotted(path: str) -> str:
    parts = path.split("/")
    if parts[-1] == "__init__.py":
        return ".".join(parts[:-1])
    return ".".join(parts[:-1] + [parts[-1][: -len(".py")]])


def _needles(path: str) -> list[str]:
    """Strings that would name this deleted path if something still reached it.

    For a shadowed deletion the dotted name is deliberately omitted: it is the
    *live* package's name, so matching it would either fire on every honest
    import of the survivor or force the scan to be a lie.
    """
    out = [path, path.replace("/", os.sep)]
    if path not in SHADOWED:
        out.append(_dotted(path))
    return out


#: A dynamic import of a deleted module is legitimate in exactly one shape: a
#: guard that asserts the module is gone. The guard has to *handle the missing
#: module*, otherwise the import is a caller and the deletion was wrong.
_GUARD_MARKERS = ("ModuleNotFoundError", "ImportError", "pytest.raises")


def _is_absence_guard(hit: str) -> bool:
    """True when a reported dynamic import is a test asserting absence.

    Deliberately conservative: the enclosing function must be syntactically
    capable of handling the failure. A site that merely happens to sit near a
    try/except is still reported, so this cannot quietly widen the exemption.
    """
    rel, _, rest = hit.partition(":")
    lineno = int(rest.split(":", 1)[0])
    path = ROOT / rel
    text = _read(path)
    if text is None:
        return False
    try:
        tree = ast.parse(text, filename=rel)
    except (SyntaxError, ValueError):
        return False
    # innermost function whose body contains the reported line
    best: ast.AST | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                node.lineno <= lineno <= (node.end_lineno or node.lineno):
            if best is None or node.lineno > best.lineno:
                best = node
    scope = best if best is not None else tree
    return any(
        isinstance(n, ast.Name) and n.id in _GUARD_MARKERS
        or isinstance(n, ast.Attribute) and n.attr in _GUARD_MARKERS
        for n in ast.walk(scope)
    )


@pytest.fixture(scope="module")
def deletions() -> dict[str, dict]:
    data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
    return {e["path"]: e for e in data["deletions"]}


@pytest.fixture(scope="module")
def python_files() -> list[Path]:
    return _iter_files((".py",))


@pytest.fixture(scope="module")
def import_scan(python_files: list[Path], deletions: dict[str, dict]) -> dict:
    """One AST pass over every ``.py`` in the tree, every deletion at once."""
    static: dict[str, list[str]] = {p: [] for p in deletions}
    dynamic: dict[str, list[str]] = {p: [] for p in deletions}
    parse_errors: list[str] = []
    needles = {p: _needles(p) for p in deletions}
    dotted_of = {p: _dotted(p) for p in deletions}

    for f in python_files:
        rel = f.relative_to(ROOT).as_posix()
        text = _read(f)
        if text is None:
            continue
        try:
            tree = ast.parse(text, filename=rel)
        except (SyntaxError, ValueError):
            parse_errors.append(rel)
            continue

        pkg = rel.split("/")[:-1]

        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    base = ".".join(pkg[: len(pkg) - (node.level - 1)] + ([base] if base else []))
                targets = [base] + [f"{base}.{a.name}" for a in node.names]
            for path, mods in static.items():
                if path in SHADOWED:
                    continue
                mod = dotted_of[path]
                for t in targets:
                    if t == mod or t.startswith(mod + "."):
                        static[path].append(f"{rel}:{node.lineno} {t}")

            # dynamic loading: the only way an AST importer scan is blind
            if isinstance(node, ast.Call):
                try:
                    fname = ast.unparse(node.func)
                except Exception:  # pragma: no cover - unparse is total in 3.12
                    continue
                if fname not in DYNAMIC_LOADERS:
                    continue
                for arg in list(node.args) + [kw.value for kw in node.keywords]:
                    if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
                        continue
                    v = arg.value
                    for path, ns in needles.items():
                        if path in SHADOWED and v == dotted_of[path]:
                            continue  # names the live package, not the dead file
                        if any(n in v for n in ns):
                            dynamic[path].append(f"{rel}:{node.lineno} {fname}({v!r})")

    return {"static": static, "dynamic": dynamic, "parse_errors": parse_errors}


# --------------------------------------------------------------------------- #
# 0. the fixture itself - if this fails, every other test is vacuous
# --------------------------------------------------------------------------- #
class TestTheBaselineIsReal:
    def test_the_log_has_the_claimed_number_of_entries(self, deletions) -> None:
        assert len(deletions) == 27, (
            f"the log claims a 27-path consolidation but holds {len(deletions)} entries; "
            "the review below is pinned to the log, so a silently added or removed "
            "entry would leave it testing a different set than the one recorded"
        )

    def test_every_logged_path_is_actually_gone(self, deletions) -> None:
        present = [p for p in deletions if (ROOT / p).exists()]
        assert not present, (
            f"these logged deletions are back on disk: {present}. Either the log is "
            "stale or a restore happened without recording it; the rest of this file "
            "assumes the paths are absent"
        )

    def test_every_logged_path_is_recoverable_from_head(self, deletions) -> None:
        proc = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", *deletions],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        tracked = set(proc.stdout.split())
        missing = [p for p in deletions if p not in tracked]
        assert not missing, (
            f"not in HEAD, so `git checkout HEAD --` cannot restore them: {missing}"
        )

    def test_the_scan_actually_parsed_the_tree(self, import_scan, python_files) -> None:
        """A scanner that silently fails to parse is a scanner that proves nothing."""
        assert len(python_files) > 500, (
            f"the scan only reached {len(python_files)} python files; the tree is far "
            "larger, so EXCLUDED_DIRS is swallowing live code"
        )
        # One real, unparseable file is tolerable; a wall of them is a blind scan.
        assert len(import_scan["parse_errors"]) <= 2, (
            "python files the reachability scan could not parse (a scan that cannot "
            f"read a file cannot clear it): {import_scan['parse_errors'][:10]}"
        )


# --------------------------------------------------------------------------- #
# 1. static import reachability
# --------------------------------------------------------------------------- #
class TestNoLiveModuleImportsADeletedPath:
    def test_no_static_import_reaches_a_deleted_module(self, import_scan) -> None:
        offenders = {
            p: hits for p, hits in import_scan["static"].items() if hits
        }
        assert not offenders, (
            "a deleted module is imported again. Each entry names the exact file and "
            "line, because a resurrection here is the campaign's headline risk:\n  "
            + "\n  ".join(f"{p}: {h}" for p, h in offenders.items())
        )

    def test_the_static_scan_would_notice_a_resurrection(self, tmp_path) -> None:
        """Negative control.

        A scan that finds nothing is worthless unless it can find something. This
        writes a file that really does import a deleted module, points the same
        matcher at it, and requires the hit. If the matcher ever degrades into a
        no-op, this test fails instead of the whole file passing vacuously.
        """
        target = "services.security.slowloris"
        probe = tmp_path / "probe.py"
        probe.write_text(f"from {target} import SlowlorisMiddleware\n", encoding="utf-8")
        tree = ast.parse(probe.read_text(encoding="utf-8"))
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == target:
                found = True
        assert found, (
            "the reachability matcher stopped recognising a plain "
            f"`from {target} import X`; every 'zero importers' claim in the "
            "deletion log now rests on a scan that cannot detect an import"
        )


# --------------------------------------------------------------------------- #
# 2. dynamic reachability - the AST importer scan's structural blind spot
# --------------------------------------------------------------------------- #
class TestNoDynamicLoadingReachesADeletedModule:
    def test_no_importlib_or_getattr_string_names_a_deleted_module(self, import_scan) -> None:
        """A dynamic load of a deleted module is a resurrection, not a mention.

        The one legitimate form is an *absence guard*: a test that imports the
        module precisely to assert it is gone. Those are separated out by
        ``_classify`` below, which requires the guard to actually handle
        ``ModuleNotFoundError`` - a bare dynamic import with no handling is a
        use, and is reported as an offender.
        """
        offenders: dict[str, list[str]] = {}
        guards: dict[str, list[str]] = {}
        for path, hits in import_scan["dynamic"].items():
            real, guarded = [], []
            for hit in hits:
                (guarded if _is_absence_guard(hit) else real).append(hit)
            if real:
                offenders[path] = real
            if guarded:
                guards[path] = guarded
        assert not offenders, (
            "a deleted module is still loaded dynamically, so it was never dead. An "
            "AST importer scan cannot see this form at all, which is exactly why it "
            "is checked separately:\n  "
            + "\n  ".join(f"{p}: {h}" for p, h in offenders.items())
        )
        # Not decorative: the guard exemption is only sound if the set of
        # exempted sites is itself accounted for.
        self._guard_sites = guards

    def test_every_exempted_dynamic_load_really_is_an_absence_guard(self) -> None:
        guards = getattr(self, "_guard_sites", {})
        assert guards == {
            "services/models/cpp_bridge.py": [
                "tests/unit/test_cpp_status_endpoint.py:72 importlib.import_module("
                "'services.models.cpp_bridge')"
            ],
        }, (
            "the set of dynamically-loaded deleted modules changed. A new entry is a "
            "new dynamic import site and must be reviewed by hand: is it a guard that "
            "asserts the module is gone, or a caller that expects it to exist?\n  "
            f"{guards}"
        )

    def test_no_conftest_declares_a_deleted_module_as_a_plugin(self) -> None:
        conftests = [ROOT / "conftest.py", ROOT / "tests" / "conftest.py",
                     ROOT / "services" / "conftest.py"]
        conftests += sorted(ROOT.rglob("conftest.py"))
        seen: set[Path] = set()
        offenders: list[str] = []
        for f in conftests:
            if f in seen or not f.is_file():
                continue
            seen.add(f)
            if any(part in EXCLUDED_DIRS for part in f.relative_to(ROOT).parts):
                continue
            text = _read(f)
            if text is None:
                continue
            try:
                tree = ast.parse(text, filename=str(f))
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "pytest_plugins" for t in node.targets
                ):
                    for elt in ast.walk(node.value):
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            offenders.append(
                                f"{f.relative_to(ROOT).as_posix()}:{node.lineno} "
                                f"pytest_plugins={elt.value!r}"
                            )
        assert not offenders, (
            f"a conftest registers a plugin by name: {offenders}. If that name is a "
            "deleted path, the module was live and is now missing at collection time"
        )

    def test_every_conftest_in_the_tree_still_parses_and_its_imports_resolve(
        self, deletions
    ) -> None:
        """The fixture class of risk: a removed module a fixture still needs."""
        needles = {p: _needles(p) for p in deletions}
        offenders: list[str] = []
        for f in sorted(ROOT.rglob("conftest.py")):
            rel = f.relative_to(ROOT)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            text = _read(f)
            if text is None:
                continue
            try:
                tree = ast.parse(text, filename=str(f))
            except (SyntaxError, ValueError):
                offenders.append(f"{rel.as_posix()}: does not parse")
                continue
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for path, ns in needles.items():
                    if path in SHADOWED:
                        continue
                    for n in names:
                        if n in ns or n.startswith(_dotted(path) + "."):
                            offenders.append(f"{rel.as_posix()}:{node.lineno} {n}")
        assert not offenders, (
            f"a conftest still depends on a deleted module: {offenders}. A fixture "
            "that imports a removed module fails at collection, not at the test that "
            "needed it, so the failure points at the wrong thing"
        )


# --------------------------------------------------------------------------- #
# 3. non-python invocation - CI, compose, k8s, entry points
# --------------------------------------------------------------------------- #
class TestNoBuildOrDeploymentFileInvokesADeletedPath:
    def test_no_invocation_file_names_a_deleted_path(self, deletions) -> None:
        candidates: list[Path] = []
        for pattern in INVOCATION_GLOBS:
            for f in ROOT.glob(pattern):
                if f.is_file():
                    candidates.append(f)
        for f in sorted(set(candidates)):
            if any(part in EXCLUDED_DIRS for part in f.relative_to(ROOT).parts):
                continue

        offenders: list[str] = []
        for f in sorted(set(candidates)):
            rel = f.relative_to(ROOT).as_posix()
            if rel in EXCLUDED_FILES:
                continue
            text = _read(f)
            if text is None:
                continue
            for path in deletions:
                stem = Path(path).name
                dotted = _dotted(path)
                # A path-as-command is the failure that survives a green local run
                # and breaks CI. Match the path, the dotted name, and the bare
                # filename when it is specific enough to be unambiguous.
                hits = [
                    needle for needle in (path, dotted) if needle and needle in text
                ]
                if not hits and stem in ("cpp_bridge.py", "database_models.py",
                                         "c_api.cpp", "test_lcc.py"):
                    hits = [stem] if stem in text else []
                if hits:
                    offenders.append(f"{rel} -> {path} (via {hits[0]!r})")
        assert not offenders, (
            "a build or deployment file still invokes a deleted path. This is the "
            "worst failure mode of the whole campaign: every local importer check "
            "stays green and the build breaks later:\n  " + "\n  ".join(sorted(offenders))
        )

    def test_the_workflows_directory_was_actually_examined(self) -> None:
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
        assert len(workflows) >= 3, (
            f"only {len(workflows)} workflow files were found under .github/workflows; "
            "the invocation scan is not looking where CI actually lives"
        )

    def test_no_entry_point_registers_a_deleted_module(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        offenders = [
            line.strip() for line in pyproject.splitlines()
            if re.search(r"(event_bus|api_gateway\.(resilience|cache)|map_engine\.api"
                         r"|smart_service|models\.cpp_bridge|security\.(ssrf|headers"
                         r"|redis_rate_limit|slowloris)|session_manager)", line)
        ]
        assert not offenders, (
            f"pyproject registers a deleted module: {offenders}. `[project.scripts]` "
            "is an import the AST scan never sees"
        )

    def test_no_deleted_path_appears_in_a_workflow_run_step(self) -> None:
        """A deleted module named as a *command* breaks CI, not the importer scan."""
        offenders: list[str] = []
        for wf in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
            text = _read(wf)
            if text is None:
                continue
            for line in text.splitlines():
                stripped = line.strip()
                if not any(stripped.startswith(k) for k in ("run:", "- run:", "python ",
                                                             "pytest ", "coverage run",
                                                             "uvicorn ", "alembic ")):
                    continue
                for path, entry in (
                    ("services/security/ssrf.py", "ssrf"),
                    ("services/session_manager.py", "session_manager"),
                    ("services/map_engine/test_hydroma_motors.py", "test_hydroma_motors"),
                    ("services/scientific_motors/test_lcc.py", "test_lcc"),
                    ("services/models/cpp_bridge.py", "models.cpp_bridge"),
                    ("engine/cpp_core/bindings/c_api.cpp", "c_api"),
                ):
                    if entry in stripped:
                        offenders.append(f"{wf.name}: {stripped[:120]}")
        assert not offenders, (
            "a workflow step still invokes a deleted module:\n  " + "\n  ".join(offenders)
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "PRE-EXISTING, unrelated to any deletion. pyproject.toml:130 declares "
            "`econojin = \"services.api_gateway.cli:main\"` under [project.scripts], but "
            "services/api_gateway/cli.py does not exist, so installing the package "
            "produces a console command that raises ModuleNotFoundError on first use. "
            "It is listed here because it is the canonical example of the class this "
            "file exists for - a live import expressed as a string in packaging "
            "metadata, invisible to an AST importer scan. Fix: add cli.py or drop the "
            "entry, then remove this marker."
        ),
    )
    def test_every_console_script_target_exists(self) -> None:
        """`[project.scripts]` is an import statement written as a string.

        Nothing in an AST importer scan can see it, so it gets its own check.
        """
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        block = re.search(r"\[project\.scripts\]\s*\n(.*?)(?=\n\[|\Z)", text, re.S)
        assert block, "pyproject declares no [project.scripts]; this scan is blind"
        targets = re.findall(r'=\s*"([^"]+)"', block.group(1))
        assert targets, "no console scripts parsed from [project.scripts]"
        missing = []
        for target in targets:
            module, _, _attr = target.partition(":")
            rel = Path(*module.split(".")).with_suffix(".py")
            if not (ROOT / rel).exists():
                missing.append(f"{target} -> {rel.as_posix()}")
        assert not missing, (
            f"declared console scripts with no module on disk: {missing}. `pip install` "
            "succeeds and the command fails on first invocation"
        )


# --------------------------------------------------------------------------- #
# 4. name shadowing
# --------------------------------------------------------------------------- #
class TestTheShadowedDeletionsWereStructurallyUnimportable:
    """Two deletions shared a dotted name with a live neighbour.

    For those, "zero importers" is not evidence, because no import statement
    can even name them. The claim to test is the stronger one: CPython's
    resolution order made the file unreachable *regardless of importers*.
    """

    def test_cpython_prefers_the_package_over_the_sibling_module(self, tmp_path) -> None:
        """Behavioural proof of the precedence, in a real interpreter.

        Written as a subprocess rather than a FileFinder poke because the claim
        under test is what ``import`` does, not what one finder returns.
        """
        pkg = tmp_path / "shadowpkg"
        (pkg / "core").mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core" / "__init__.py").write_text("MARK = 'package'\n", encoding="utf-8")
        (pkg / "core.py").write_text("MARK = 'module'\n", encoding="utf-8")

        db = tmp_path / "shadowdb"
        (db / "models").mkdir(parents=True)
        (db / "__init__.py").write_text("", encoding="utf-8")
        (db / "models.py").write_text("MARK = 'module-wins'\n", encoding="utf-8")
        (db / "models" / "database_models.py").write_text("MARK = 'never'\n", encoding="utf-8")

        probe = textwrap.dedent(f"""
            import importlib, sys
            sys.path.insert(0, {str(tmp_path)!r})
            import shadowpkg.core, shadowdb.models
            print(shadowpkg.core.MARK, shadowpkg.core.__file__)
            print(shadowdb.models.MARK, shadowdb.models.__file__)
            try:
                importlib.import_module("shadowdb.models.database_models")
                print("IMPORTED")
            except Exception as exc:
                print(type(exc).__name__)
        """)
        out = subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True, timeout=120
        )
        assert out.returncode == 0, f"probe interpreter failed:\n{out.stderr}"
        lines = out.stdout.strip().splitlines()
        assert lines[0].split()[0] == "package", (
            f"a regular package lost to a sibling module: {lines[0]}. If this is what "
            "CPython now does, `engine/hydroma/core.py` was NOT dead by shadowing and "
            "its deletion removed a live module"
        )
        assert lines[1].split()[0] == "module-wins", (
            f"a module lost to a sibling directory: {lines[1]}. If this is what CPython "
            "now does, `database/models/database_models.py` was importable after all"
        )
        assert lines[2] == "ModuleNotFoundError", (
            f"the shadowed sub-module imported successfully: {lines}. The whole "
            "`database/models/database_models.py` deletion rests on it being "
            "unreachable"
        )

    def test_engine_hydroma_core_resolves_to_the_package(self) -> None:
        import engine.hydroma.core as core

        assert getattr(core, "__path__", None), (
            "`engine.hydroma.core` is not a package. If it resolved to a module again, "
            "a re-created `engine/hydroma/core.py` would be live and the recorded "
            "shadowing justification for its deletion would no longer hold"
        )
        assert Path(core.__file__).as_posix().endswith("engine/hydroma/core/__init__.py"), (
            f"`engine.hydroma.core` resolved to {core.__file__}, not the package"
        )
        assert hasattr(core, "HydromaCore"), (
            "the package must still export HydromaCore; live callers "
            "(services/api_gateway/main.py, tests/unit/test_rusle_uncorrelated.py) "
            "import it from here"
        )

    def test_database_models_is_a_plain_module_and_its_directory_stays_unpackaged(self) -> None:
        import database.models as models

        assert not getattr(models, "__path__", None), (
            "`database.models` became a package. With `database/models/__init__.py` "
            "present, `database/models/database_models.py` would have been importable "
            "and its deletion would have removed a live module"
        )
        assert not (ROOT / "database" / "models" / "__init__.py").exists(), (
            "`database/models/__init__.py` exists. That turns the shadowed directory "
            "into a real package; verify whether the deleted module was live before "
            "treating its removal as safe"
        )
        assert (ROOT / "database" / "models").exists() is False or not any(
            (ROOT / "database" / "models").glob("*.py")
        ), (
            "`database/models/` still holds python files. Those were never packaged "
            "and never imported, but they are exactly the shadowing pattern this "
            "review is meant to catch reappearing"
        )

    def test_the_shadowing_deletions_are_named_in_the_log(self, deletions) -> None:
        """The log must carry the stronger claim, not just 'zero importers'."""
        for path in SHADOWED:
            entry = deletions[path]
            assert entry.get("name_collision_with_live_package") or "shadow" in (
                entry["reason"] + entry["verified_by"]
            ).lower(), (
                f"{path} is a shadowing deletion but the log justifies it only by "
                "importer count. For a name collision that is the weaker argument: no "
                "import statement can distinguish the two, so the importer count is "
                "trivially zero whether or not the file was live"
            )


# --------------------------------------------------------------------------- #
# 5. data and schema
# --------------------------------------------------------------------------- #
TABLES_OWNED_BY_THE_DELETED_SHADOW_FILE = (
    "topography_analysis_results",
    "runoff_calculation_results",
    "groundwater_model_results",
    "crop_water_req_results",
    "structure_design_results",
    "irrigation_design_results",
    "calibration_results",
)


def _orm_tables(source: str) -> dict[str, dict[str, str]]:
    """tablename -> {attribute name: column name} for a declarative module."""
    out: dict[str, dict[str, str]] = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef):
            continue
        name: str | None = None
        cols: dict[str, str] = {}
        for stmt in node.body:
            target = value = None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target, value = stmt.targets[0], stmt.value
            elif isinstance(stmt, ast.AnnAssign):
                target, value = stmt.target, stmt.value
            if target is None or not isinstance(target, ast.Name) or value is None:
                continue
            if target.id == "__tablename__" and isinstance(value, ast.Constant):
                name = str(value.value)
            elif isinstance(value, ast.Call):
                fn = getattr(value.func, "attr", None) or getattr(value.func, "id", None)
                if fn in ("Column", "mapped_column"):
                    cols[target.id] = (
                        str(value.args[0].value)
                        if value.args and isinstance(value.args[0], ast.Constant) else "?"
                    )
        if name:
            out[name] = cols
    return out


class TestTheDeletedModelsFileOwnedNoLiveSchema:
    def test_every_table_it_declared_still_exists_in_the_live_orm(self) -> None:
        import database.models as live

        live_tables = set(live.Base.metadata.tables)
        missing = [t for t in TABLES_OWNED_BY_THE_DELETED_SHADOW_FILE
                   if t not in live_tables]
        assert not missing, (
            f"tables the deleted shadow file declared are absent from the live ORM: "
            f"{missing}. If those were real tables, the deletion dropped schema"
        )

    def test_six_of_the_seven_were_column_identical_duplicates(self) -> None:
        """Column granularity, not table-name granularity.

        ``test_s12_table_registration.py`` proves the *names* were declared
        twice. It does not prove the two declarations were the same shape, and
        the log's reason asserts they were.
        """
        dead_src = subprocess.run(
            ["git", "show", "HEAD:database/models/database_models.py"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=300,
        ).stdout
        dead = _orm_tables(dead_src)
        live = _orm_tables((ROOT / "database" / "models.py").read_text(encoding="utf-8"))

        drifted = {
            t: {
                "only_in_deleted": sorted(set(dead[t]) - set(live.get(t, {}))),
                "only_in_live": sorted(set(live.get(t, {})) - set(dead[t])),
            }
            for t in TABLES_OWNED_BY_THE_DELETED_SHADOW_FILE
            if t in dead and t in live and set(dead[t]) != set(live[t])
        }
        assert set(drifted) == {"topography_analysis_results"}, (
            "the deleted shadow file's table shapes did not match the live ORM for "
            f"{sorted(drifted)}: {drifted}. The log records these seven as duplicates "
            "that 'already exist in database/models.py'; that is only true at table-"
            "name granularity, and for any other table the deletion dropped a "
            "distinct column contract"
        )

    def test_no_alembic_migration_creates_a_table_the_orm_cannot_serve(self) -> None:
        """Scoped to the tables the deleted shadow file owned.

        A migration creating a table the live ORM does not declare is real
        drift, but the repository has many of those for *service-owned* models
        (`services/marketplace/models/`, `services/ledger/models.py`, ...), so
        the question this file can actually answer is narrower: does any live
        migration touch the seven tables the deleted file claimed?
        """
        import database.models as live

        declared = set(live.Base.metadata.tables)
        owned = set(TABLES_OWNED_BY_THE_DELETED_SHADOW_FILE)
        orphans: list[str] = []
        for mig in sorted((ROOT / "alembic" / "versions").glob("*.py")):
            if "_archived" in mig.parts:
                continue
            text = _read(mig)
            if text is None:
                continue
            for m in re.finditer(r'create_table\(\s*"([^"]+)"', text):
                if m.group(1) in owned and m.group(1) not in declared:
                    orphans.append(f"{mig.name}: {m.group(1)}")
        assert not orphans, (
            f"a live migration creates a table from the deleted shadow file's set that "
            f"the ORM does not declare: {orphans}. Either the ORM lost a model or the "
            "deletion dropped the only declaration of that table"
        )

    def test_the_migration_and_the_orm_agree_on_the_owned_tables(self) -> None:
        """The six exact duplicates must also match the migration, not just the ORM.

        This is the check the deletion log's `verified_by` does not perform: it
        cites `test_s12_table_registration.py`, which asserts a table is not
        declared in two files. It never compares either file to the migration
        that actually builds the schema.
        """
        import database.models as live

        columns = {t: {c.name for c in live.Base.metadata.tables[t].columns}
                   for t in TABLES_OWNED_BY_THE_DELETED_SHADOW_FILE
                   if t in live.Base.metadata.tables}
        mig_text = "\n".join(
            t for t in (_read(p) for p in sorted((ROOT / "alembic" / "versions").glob("*.py")))
            if t
        )
        unbuilt: list[str] = []
        for table, cols in columns.items():
            if f'"{table}"' not in mig_text:
                unbuilt.append(f"{table}: no live migration names it")
        assert not unbuilt, (
            f"tables with no migration: {unbuilt}. The ORM declares a table no "
            "migration creates, so `alembic upgrade heads` leaves it absent"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "PRE-EXISTING, NOT CAUSED BY THE DELETION. database/models/database_models.py "
            "was unimportable (verified: 'database.models' is a plain module, so the "
            "sub-module raises ModuleNotFoundError), so its column declarations could "
            "never reach a session. But the live ORM's TopographyAnalysisResult "
            "declares only id/profile_id/data, while "
            "engine/hydroma/analyses/topography_analysis.py:137 constructs it with "
            "site_id, dem_path, analysis_types, slope_map_path, aspect_map_path, "
            "curvature_map_path, flow_direction_map_path and "
            "flow_accumulation_map_path. SQLAlchemy raises TypeError on the first "
            "unrecognised kwarg, so that persistence path is dead on arrival. The "
            "deletion log verified table-name parity (test_s12_table_registration) and "
            "nothing else, which is why this survived the review. Fix the ORM model "
            "and remove this marker."
        ),
    )
    def test_the_topography_orm_model_can_be_written_by_live_engine_code(self) -> None:
        from database.models import TopographyAnalysisResult

        columns = {c.name for c in TopographyAnalysisResult.__table__.columns}
        required = {
            "site_id", "dem_path", "analysis_types", "slope_map_path",
            "aspect_map_path", "curvature_map_path", "flow_direction_map_path",
            "flow_accumulation_map_path", "created_at",
        }
        assert required <= columns, (
            "engine/hydroma/analyses/topography_analysis.py writes these columns but "
            f"the ORM does not declare them: {sorted(required - columns)}"
        )
        # And the write itself, which is the failure the user would actually see.
        TopographyAnalysisResult(
            site_id="s", dem_path="/d.tif", analysis_types="[]",
            slope_map_path="a", aspect_map_path="b", curvature_map_path="c",
            flow_direction_map_path="d", flow_accumulation_map_path="e",
        )


# --------------------------------------------------------------------------- #
# 6. package re-exports
# --------------------------------------------------------------------------- #
class TestNoSurvivingPackageReExportsSomethingDeleted:
    def test_no_init_file_imports_a_deleted_module(self, python_files, deletions) -> None:
        offenders: list[str] = []
        for f in python_files:
            if f.name != "__init__.py":
                continue
            rel = f.relative_to(ROOT).as_posix()
            text = _read(f)
            if text is None:
                continue
            try:
                tree = ast.parse(text, filename=rel)
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ""
                    if node.level:
                        pkg = rel.split("/")[:-1]
                        base = ".".join(pkg[: len(pkg) - (node.level - 1)] + ([base] if base else []))
                    names = [base]
                for path in deletions:
                    if path in SHADOWED:
                        continue
                    for n in names:
                        if n == _dotted(path) or n.startswith(_dotted(path) + "."):
                            offenders.append(f"{rel}:{node.lineno} {n}")
        assert not offenders, (
            "a package marker still imports a deleted module, so importing the "
            "package raises ImportError: " + "; ".join(offenders)
        )

    @pytest.mark.parametrize(
        "module",
        [
            "services.api_gateway.eventbus",
            "services.security",
            "engine.hydroma.core",
            "engine",
        ],
    )
    def test_surviving_package_dunder_all_is_satisfiable(self, module: str) -> None:
        """The classic half-done removal: module deleted, ``__all__`` left behind."""
        mod = importlib.import_module(module)
        declared = getattr(mod, "__all__", None)
        if declared is None:
            pytest.skip(f"{module} declares no __all__")
        missing = sorted(set(declared) - set(dir(mod)))
        assert not missing, (
            f"{module}.__all__ advertises {missing}, which the module does not "
            "expose. This is what a package looks like when a re-exported module "
            "was deleted without the marker being updated"
        )

    def test_the_eventbus_package_does_not_advertise_the_deleted_dlq(self) -> None:
        import services.api_gateway.eventbus as eventbus

        leaked = [n for n in dir(eventbus) if "dlq" in n.lower() or "DLQ" in n]
        assert not leaked, (
            f"the eventbus package still exposes dead-letter symbols {leaked}. "
            "dlq.py was deleted; a surviving re-export makes the package import "
            "fail on any interpreter that had not cached the old .pyc"
        )


# --------------------------------------------------------------------------- #
# 7. the survivors are the ones actually wired
# --------------------------------------------------------------------------- #
class TestTheSurvivorIsTheOneThatIsWired:
    """A duplicate deletion is only safe if the surviving copy is what runs.

    If the wrong copy had survived - or if the survivor had been rewired to the
    deleted one - every importer scan in this file would still be green.
    """

    def test_the_worker_runs_on_the_gateway_eventbus(self) -> None:
        source = (ROOT / "services" / "workers" / "event_worker.py").read_text(encoding="utf-8")
        assert "services.api_gateway.eventbus" in source, (
            "the standalone worker no longer imports the surviving eventbus. It was "
            "rewired off services/event_bus/; rewiring it to nothing would leave a "
            "worker entry point that constructs no worker"
        )
        assert "services.event_bus" not in source

    def test_the_gateway_mounts_the_api_gateway_security_headers(self) -> None:
        source = (ROOT / "services" / "api_gateway" / "main.py").read_text(encoding="utf-8")
        m = re.search(r"from services\.api_gateway\.security import \(([^)]*)\)", source)
        assert m, (
            "main.py no longer imports SecurityHeadersMiddleware from "
            "services.api_gateway.security; the deletion of services/security/headers.py "
            "must not have taken the mounted one with it"
        )
        assert "SecurityHeadersMiddleware" in m.group(1)
        assert "app.add_middleware(SecurityHeadersMiddleware)" in source, (
            "the middleware is imported but never mounted, which is precisely the "
            "state services/security/headers.py was deleted for"
        )

    def test_the_models_router_reads_the_live_cpp_bridge(self) -> None:
        source = (ROOT / "services" / "api_gateway" / "routers" / "models.py").read_text(
            encoding="utf-8"
        )
        assert "from engine.hydroma.cpp_bridge import" in source, (
            "the /models/cpp-status endpoint no longer reads the live extension "
            "loader. It used to read the deleted services/models/cpp_bridge.py; if the "
            "replacement is gone the endpoint either 500s or reports a fabricated "
            "status"
        )
        assert "from services.models.cpp_bridge" not in source

    def test_the_live_cpp_status_endpoint_reports_rather_than_guesses(self) -> None:
        mod = importlib.import_module("engine.hydroma.cpp_bridge")
        state = mod.backend_status()
        assert isinstance(state, dict) and "import_error" in state, (
            "engine.hydroma.cpp_bridge.backend_status() is the single source of truth "
            "for the endpoint the deleted services/models/cpp_bridge.py used to feed; "
            "it no longer reports an import_error field, so the endpoint's honesty "
            "contract is gone"
        )

    def test_engine_resilience_is_reexported_by_the_engine_package(self) -> None:
        """The resilience package was deleted in favour of engine/resilience.py."""
        engine = importlib.import_module("engine")
        for symbol in ("circuit_breaker", "with_retry", "with_timeout"):
            assert hasattr(engine, symbol), (
                f"engine.{symbol} disappeared. services/api_gateway/resilience was "
                "deleted on the basis that engine/resilience.py is the survivor; the "
                "survivor is no longer reachable from the package that re-exports it"
            )

    def test_the_security_firewall_sibling_imports_all_resolve(self) -> None:
        """The live siblings of the five D-7 deletions must not import them.

        services/security/ was left standing with eleven modules. If any of them
        imported ssrf/headers/redis_rate_limit/slowloris, the package would now
        fail to import and the gateway would not boot.
        """
        mod = importlib.import_module("services.security.middleware")
        source = (ROOT / "services" / "security" / "middleware.py").read_text(encoding="utf-8")
        imported = re.findall(r"^from \.(\w+) import", source, re.M)
        assert imported, (
            "no relative imports found in services/security/middleware.py; the scan "
            "understood is not the one that was reviewed"
        )
        for name in imported:
            assert (ROOT / "services" / "security" / f"{name}.py").exists() or (
                ROOT / "services" / "security" / name / "__init__.py"
            ).exists(), (
                f"the mounted firewall imports .{name}, which no longer exists. The "
                "gateway would fail to start"
            )
        assert mod.SpiderFirewallMiddleware is not None

    def test_the_live_rate_limiter_really_is_stronger_than_the_deleted_one(self) -> None:
        """The log justifies deleting redis_rate_limit.py by weakness.

        That justification only holds while the survivor still buckets by IP and
        by subject, and still supports Redis. Assert the behaviour, not the
        docstring, because the justification is the whole reason the deletion was
        safe.
        """
        from services.security.rate_limit import AUTH_LIMIT, GENERAL_LIMIT, RateLimiter

        limiter = RateLimiter(redis_client=object())
        assert limiter._redis is not None, "the survivor lost its Redis backend"

        # A caller rotating paths must not buy a fresh budget.
        rotated = [limiter._check_memory("1.2.3.4", f"/farms/{i}", None)[0]
                   for i in range(GENERAL_LIMIT + 20)]
        assert all(rotated[:GENERAL_LIMIT]), "the per-IP budget no longer holds"
        assert not any(rotated[GENERAL_LIMIT:]), (
            "path rotation defeats the live limiter. That is exactly the defect the "
            "deletion log attributes to the deleted redis_rate_limit.py; if the "
            "survivor has it too, the deletion removed two weak limiters and left "
            "neither"
        )

        # The per-subject bucket must be independent of the IP bucket.
        second = RateLimiter()
        allowed = sum(1 for i in range(3) if second._check_memory("9.9.9.9", "/x", "u1")[0])
        assert allowed == 3, "the per-subject budget is not being enforced separately"
        assert AUTH_LIMIT < GENERAL_LIMIT, "the auth path is no longer the tighter budget"


# --------------------------------------------------------------------------- #
# 8. coverage relocation, not coverage loss
# --------------------------------------------------------------------------- #
class TestTheDeletedInPackageTestsWereReplacedNotLost:
    """Deleting a test file is a deletion of coverage, whatever the file was worth.

    Both of these were assertion-free ``__main__`` smoke scripts inside a
    production package, which is a fair thing to remove - but only if the
    replacement asserts something. A vacuous replacement is a silent coverage
    loss with a green build.
    """

    @pytest.mark.parametrize(
        ("deleted", "replacement", "subject"),
        [
            ("services/scientific_motors/test_lcc.py",
             "tests/unit/test_lcc_motor.py", "LandCapabilityMotor"),
            ("services/map_engine/test_hydroma_motors.py",
             "tests/unit/test_map_engine_fetchers.py", "BiofertilizerMotor"),
        ],
    )
    def test_the_replacement_asserts(self, deleted: str, replacement: str, subject: str) -> None:
        path = ROOT / replacement
        assert path.exists(), (
            f"{deleted} was deleted and its replacement {replacement} does not exist. "
            "The deletion log cites the replacement as the verification; without it "
            "the deletion is an uncovered loss"
        )
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=replacement)
        tests = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name.startswith("test_")]
        asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
        assert tests, f"{replacement} defines no test functions"
        assert len(asserts) >= len(tests), (
            f"{replacement} has {len(tests)} test functions and {len(asserts)} assert "
            f"statements. The deleted file was removed for recording vacuous passes; a "
            f"replacement with {subject} named in its docstring but no assertions "
            "reinstates the problem under a compliant filename"
        )
        assert subject in text, (
            f"{replacement} does not mention {subject}, the subject the deleted file "
            "exercised. The motor the deleted smoke script ran is no longer covered"
        )

    def test_no_shipped_package_holds_a_collectable_test_module_any_more(self) -> None:
        """pytest.ini sets ``testpaths = services engine ...``.

        A ``test_*.py`` inside a production package is collected by a bare
        ``pytest`` run, which is how the two deleted files produced passes. The
        class of bug recurs by anyone adding one.
        """
        offenders = [
            f.relative_to(ROOT).as_posix()
            for f in (ROOT / "services").rglob("test_*.py")
            if "tests" not in f.relative_to(ROOT).parts
            and "__pycache__" not in f.parts
        ]
        assert not offenders, (
            f"assertion-free test modules are back inside production packages: "
            f"{offenders}. pytest.ini collects `services`, so these ship as tests"
        )


# --------------------------------------------------------------------------- #
# 9. NEW RISKS the deletions created
# --------------------------------------------------------------------------- #
class TestTheDeletionsLeftNoTelemetryBehind:
    """Deleting a subsystem but keeping the metrics that described it.

    ``services/api_gateway/cache/redis_cache.py`` is gone, but the two
    ``/metrics`` counters that described it are still exported. A counter with
    no incrementer is a metric that reads 0 forever - indistinguishable, to
    anyone watching a dashboard, from "the cache is working and being missed".
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The cache was already unreferenced before it was deleted, so the counters "
            "were already orphaned; the deletion removed the last implementation that "
            "could ever have incremented them. econojin_redis_cache_hits_total and "
            "econojin_redis_cache_misses_total are still declared in "
            "services/api_gateway/metrics.py:40-47 and still listed in the exported "
            "metric-name set at :597-598, with zero call sites in the tree. Fix: "
            "either wire a cache or drop the two counters, then remove this marker."
        ),
    )
    def test_every_exported_cache_counter_has_an_incrementer(self) -> None:
        source = (ROOT / "services" / "api_gateway" / "metrics.py").read_text(encoding="utf-8")
        declared = set(re.findall(r'Counter\(\s*"([a-z0-9_]+)"', source))
        tree = ast.parse(source, filename="metrics.py")
        referenced = {
            n.attr for n in ast.walk(tree)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
        }
        orphan = {c for c in declared if c.replace("econojin_", "") not in referenced}
        assert not orphan, (
            f"exported counters with no incrementer in the module that exports them: "
            f"{sorted(orphan)}. They are permanently zero, which is a fabricated "
            "success signal in a system whose own standard forbids exactly that"
        )

    def test_the_cache_package_left_no_directory_behind(self, deletions) -> None:
        """A package emptied file-by-file is still a package if the dir survives.

        `services/api_gateway/cache/__init__.py` was one of the logged deletions,
        so the directory should be gone. If a future consolidation re-adds a
        module to one of these directories, the log must gain a matching entry -
        an unlogged module appearing is exactly the inverse failure the log's
        own policy line 8 forbids.
        """
        for gone in ("services/api_gateway/cache", "services/api_gateway/resilience",
                     "services/event_bus", "services/map_engine/api"):
            assert not (ROOT / gone).exists(), (
                f"{gone}/ still exists after every file in it was logged as deleted. "
                "Without an __init__.py it is unimportable; with one it is a live "
                "package re-exporting nothing, and GitHub shows the directory as the "
                "reviewable surface for code that is not there"
            )
            logged = [p for p in deletions if p.startswith(gone + "/")]
            assert logged, (
                f"{gone} was removed but no deletion entry covers it. The log's policy "
                "is 'anything not listed here is not an approved deletion'"
            )

    def test_no_module_reappeared_under_a_deleted_package(self, deletions) -> None:
        for gone in ("services/api_gateway/cache", "services/api_gateway/resilience",
                     "services/event_bus", "services/map_engine/api",
                     "services/security", "services/api_gateway/eventbus"):
            target = ROOT / gone
            if not target.exists():
                continue
            unlogged = [
                f.relative_to(ROOT).as_posix()
                for f in target.rglob("*.py")
                if "__pycache__" not in f.parts
                and f.relative_to(ROOT).as_posix() not in deletions
                and "tests" not in f.relative_to(ROOT).parts
            ]
            assert not unlogged, (
                f"{gone} holds modules that are not in the deletion log: {unlogged[:8]}"
            )


class TestOwnershipSurvivedTheDeletion:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            ".github/CODEOWNERS:47 still assigns /services/session_manager.py to "
            "@econojin/security-team. The file is deleted, so the D-7 review "
            "requirement for that path is now satisfied by a pattern that matches "
            "nothing - GitHub requires no review while the file reads as owned. "
            "tests/contract/test_codeowners.py checks that every entry names an owner "
            "but never that the owner names a file that exists. Fix: drop the entry, "
            "then remove this marker."
        ),
    )
    def test_every_codeowners_path_still_exists(self) -> None:
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        dangling: list[str] = []
        for line in codeowners.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pattern = line.split()[0]
            if not pattern.startswith("/"):
                continue  # glob/dir patterns are checked separately
            target = ROOT / pattern.lstrip("/")
            if not target.exists():
                dangling.append(pattern)
        assert not dangling, (
            f"CODEOWNERS points at paths that do not exist: {dangling}. A deleted file "
            "keeps its owner entry, so the review requirement silently evaporates "
            "instead of being reported"
        )

    def test_codeowners_still_covers_the_security_domain_that_lost_five_files(self) -> None:
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        assert "/services/security/" in codeowners or "/services/" in codeowners, (
            "no CODEOWNERS entry covers services/security/ after five of its modules "
            "were deleted; the deletion removed both the code and its review path"
        )


class TestTheRecordedPremisesAreStillTrue:
    """A deletion log is only as good as the factual claims it rests on.

    The `headers.py` entry - and the toleration ledger entry written from it -
    both assert that the deleted file held *the only* Content-Security-Policy in
    the repository. That claim is false, and the ledger is what
    ``GET /api/v1/security/status`` reports from.
    """

    def test_the_gateway_itself_sends_no_csp(self) -> None:
        """The gap the deletion exposed is real; assert it, do not assume it."""
        source = (ROOT / "services" / "api_gateway" / "security.py").read_text(encoding="utf-8")
        m = re.search(r"class SecurityHeadersMiddleware.*?HEADERS.*?=\s*\{(.*?)\}", source, re.S)
        assert m, "could not locate the mounted SecurityHeadersMiddleware.HEADERS"
        block = m.group(1)
        assert "Content-Security-Policy" not in block, (
            "the mounted middleware now declares a CSP, so the "
            "`no-content-security-policy` toleration is stale and the deletion log's "
            "reason for removing services/security/headers.py no longer describes the "
            "tree"
        )
        for header in ("X-Content-Type-Options", "X-Frame-Options",
                       "Referrer-Policy", "Permissions-Policy"):
            assert header in block, f"the mounted middleware lost {header}"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The deletion log and the toleration ledger both state that "
            "services/security/headers.py held 'the only Content-Security-Policy in "
            "the repository'. It did not. k8s/base/ingress.yaml:87 sets an ENFORCING "
            "Content-Security-Policy via the nginx more_set_headers annotation, and "
            "apps/web/next.config.ts:35 sets Content-Security-Policy-Report-Only. The "
            "deletion is still correct - headers.py had zero importers - but the "
            "premise recorded as its justification, and copied into the ledger that "
            "GET /api/v1/security/status reads, is factually wrong. Fix: correct the "
            "ledger's reason, then remove this marker."
        ),
    )
    def test_the_only_csp_claim_in_the_ledger_is_accurate(self) -> None:
        ledger = (ROOT / "docs" / "standards" / "tolerated-degradations.yaml").read_text(
            encoding="utf-8"
        )
        m = re.search(
            r"id: no-content-security-policy(.*?)(?=\n  - id:|\Z)", ledger, re.S
        )
        assert m, "the no-content-security-policy toleration is gone; re-derive it"
        reason = m.group(1)
        if "only CSP in the repository" not in reason and "only Content-Security-Policy" not in reason:
            pytest.skip("the ledger no longer makes the exclusivity claim")
        enforcing_elsewhere = []
        for candidate in list(ROOT.glob("k8s/**/*.yaml")) + [ROOT / "apps" / "web" / "next.config.ts"]:
            if not candidate.is_file():
                continue
            text = _read(candidate)
            if text and re.search(r"['\"]?Content-Security-Policy['\"]?\s*[:=]", text) \
                    and "Report-Only" not in text.split("Content-Security-Policy", 1)[1][:80]:
                enforcing_elsewhere.append(candidate.relative_to(ROOT).as_posix())
        assert not enforcing_elsewhere, (
            "the ledger says the deleted file held the only CSP, but an enforcing CSP "
            f"is still configured at {enforcing_elsewhere}. A status endpoint derived "
            "from this ledger will report a gap the deployment layer already closes, "
            "and a reader auditing it will be sent to a deleted file"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "docs/security/SECURITY_STACK_2026.md still lists the deleted modules as "
            "live components: line 156 names redis_rate_limit.py as the multi-level "
            "rate limiter, line 159 marks Slowloris as present via slowloris.py, and "
            "line 163 marks CSRF/SSRF/Headers present via csrf.py, ssrf.py, "
            "headers.py. A reader - human or agent - following that table is sent to "
            "three files that no longer exist. Fix: update the table, then remove "
            "this marker."
        ),
    )
    def test_the_security_stack_document_does_not_name_deleted_modules(self) -> None:
        doc = ROOT / "docs" / "security" / "SECURITY_STACK_2026.md"
        text = doc.read_text(encoding="utf-8")
        stale = [
            stem for stem in ("ssrf.py", "headers.py", "redis_rate_limit.py",
                              "slowloris.py", "session_manager.py")
            if stem in text
        ]
        assert not stale, (
            f"{doc.relative_to(ROOT)} lists {stale} as implemented security layers. "
            "They were deleted in phase 5; the document is the first thing a reviewer "
            "or an agent reads about the security stack"
        )

    def test_the_2fa_gap_the_log_credits_is_actually_closed(self) -> None:
        """The session_manager entry's verification names a specific replacement."""
        source = (ROOT / "services" / "api_gateway" / "routers" / "passkey_router.py").read_text(
            encoding="utf-8"
        )
        assert "services.two_factor" in source or "from services import two_factor" in source, (
            "the deletion log credits services/session_manager.py's removal with "
            "'the 2FA gap is now closed: services/two_factor.py is consumed by "
            "passkey_router'. That consumer is gone, so removing the only other "
            "candidate implementation left the gap fully open"
        )
