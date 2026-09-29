"""S01 — Import integrity and honest-error behaviour of the ENGINE package.

Rationale
---------
A scientific engine is only as trustworthy as its reachability. A module that
cannot be imported is a capability that does not exist, regardless of how good
its source reads. This module walks every ``engine`` package and asserts that
each module is importable, that no module imports a symbol that does not exist,
and that failure paths raise rather than silently return a placeholder.

The engine already documents an honesty contract elsewhere (``formulas/``,
``satellite/``, ``simulation/orchestrator.py``). S01 extends that contract down
to the import layer.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from engine.strict_tests.conftest import ENGINE_ROOT

_EXCLUDED_PARTS = frozenset({"tests", "__pycache__", "cpp_core", "build", "build2", "research"})


def _discover_modules() -> list[str]:
    """Every importable engine module, as dotted paths."""
    found: list[str] = []
    for path in sorted(ENGINE_ROOT.rglob("*.py")):
        rel = path.relative_to(ENGINE_ROOT.parent)
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        if _EXCLUDED_PARTS.intersection(parts):
            continue
        found.append(".".join(parts))
    return found


ENGINE_MODULES = _discover_modules()

# Modules verified not to import under the project interpreter. Each one has a
# dedicated strict-xfail below that names the root cause, so a fix is forced to
# be reflected in this set.
KNOWN_UNIMPORTABLE = {
    # imports engine.hydroma.risk.assessment, a package that does not exist.
    # Fixing it means writing the risk model, which is a decision rather than a
    # repair, so it stays declared here until that decision is made.
    "engine.hydroma.scenarios.scenario_manager",
}
# Removed 27 September 2026:
#   engine.hydroma.biofertilizer.data.seed_data
# It was never dead, only broken: the module bound ``from datetime import
# datetime`` and then called ``datetime.date(...)`` twelve times, which raises on
# the first record. Two tokens of import, and eight strain records plus the
# formulation table became reachable.

# Expression forms that cannot be legitimate statements. A bare ``a + b`` or
# ``x if c else y`` computes a value nobody reads; in a numerical kernel that is
# almost always an abandoned or half-applied formula.
_VALUE_EXPR_NODES = (ast.BinOp, ast.UnaryOp, ast.Compare, ast.IfExp)

# Known dead-arithmetic sites, each verified by reading the surrounding code.
# Kept as data so a fix at one site cannot silently mask a new one elsewhere.
KNOWN_DISCARDED_SITES = {
    "hydroma/config/settings.py": "CORS origin normalisation discarded; the "
    "wildcard-with-credentials guard then substring-matches the raw field",
    "hydroma/infrastructure/channels.py": "iteration velocity discarded, so the "
    "self-cleansing minimum-velocity criterion is never enforced",
    "hydroma/infrastructure/draining.py": "same discarded velocity in the drain depth iteration",
    "hydroma/soil/physics.py": "Schaap & van Genuchten K expression discarded, "
    "immediately followed by a different conductivity formula",
    "land/drainage.py": "cell-area expression discarded, and its comment states a "
    "1000.0 m2-to-ha factor where 10000.0 is correct",
}


def _walk_engine_sources() -> list[Path]:
    """Every engine source file that is neither vendored, generated, nor this suite."""
    out: list[Path] = []
    for path in sorted(ENGINE_ROOT.rglob("*.py")):
        rel = path.relative_to(ENGINE_ROOT)
        if _EXCLUDED_PARTS.intersection(rel.parts):
            continue
        if rel.parts[0] == "strict_tests":  # this suite is not engine source
            continue
        out.append(path)
    return out


def test_module_discovery_sanity() -> None:
    """Guard the guard: if discovery breaks, every other test silently passes."""
    assert len(ENGINE_MODULES) > 150, f"only discovered {len(ENGINE_MODULES)} engine modules"
    assert "engine.hydroma.climate.et_calculator" in ENGINE_MODULES
    assert "engine.land.erosion_risk" in ENGINE_MODULES


class TestImportability:
    """Can each engine module be imported?

    The sweep runs in a **subprocess**, not in this interpreter. Two reasons,
    both learned the hard way:

    1. Correctness. Importing 220 modules in-process mutates shared global
       state, most visibly the SQLAlchemy ``MetaData`` registry. Once one
       module has registered its tables, a later module that shares the same
       ``Base`` fails with ``InvalidRequestError`` even though it is perfectly
       importable on its own. An in-process sweep therefore reports a function
       of test collection order, not of the engine.
    2. Speed. One interpreter, one walk, instead of 220 module objects
       materialised in the test process.

    The subprocess is a fresh interpreter, so the answer it gives is the one a
    caller actually cares about: can this module be imported, in isolation,
    from a clean process.
    """

    _SCRIPT = (
        "import importlib, json, sys, pathlib\n"
        "root = pathlib.Path(sys.argv[1])\n"
        "names = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))\n"
        "sys.path.insert(0, str(root.parent))\n"
        "bad = {}\n"
        "for name in names:\n"
        "    try:\n"
        "        importlib.import_module(name)\n"
        "    except BaseException as exc:\n"
        "        bad[name] = f'{type(exc).__name__}: {exc}'\n"
        "print(json.dumps(bad))\n"
    )

    @staticmethod
    def _sweep(names: list[str]) -> dict[str, str]:
        import json
        import subprocess
        import sys
        import tempfile

        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(names, handle)
            list_path = handle.name
        try:
            result = subprocess.run(
                [sys.executable, "-c", TestImportability._SCRIPT, str(ENGINE_ROOT), list_path],
                capture_output=True,
                text=True,
                cwd=str(ENGINE_ROOT.parent),
            )
        finally:
            Path(list_path).unlink(missing_ok=True)
        if result.returncode != 0:
            pytest.fail(f"import sweep subprocess failed:\n{result.stderr[-2000:]}")
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_every_engine_module_imports_in_a_clean_interpreter(self) -> None:
        """The whole engine, swept once in a fresh process.

        A failure here means the module cannot be imported by a real caller. The
        message names the module and the exception, so no investigation is
        needed to know where to look.
        """
        targets = sorted(set(ENGINE_MODULES) - KNOWN_UNIMPORTABLE)
        assert len(targets) > 200, f"only {len(targets)} targets discovered"
        bad = self._sweep(targets)
        if bad:
            listed = "\n".join(f"  {k}: {v}" for k, v in sorted(bad.items()))
            pytest.fail(f"{len(bad)} engine module(s) are not importable:\n{listed}")

    def test_sweep_is_actually_running_modules(self) -> None:
        """Guards the guard: if the subprocess silently did nothing, the sweep
        above would report a clean engine forever."""
        import importlib

        assert importlib.import_module("engine.hydroma.soil.physics") is not None
        bad = self._sweep(["engine.hydroma.soil.physics", "engine.does.not.exist"])
        assert set(bad) == {"engine.does.not.exist"}, (
            f"the sweep is not discriminating: got {sorted(bad)}"
        )


class TestDanglingAbsoluteImports:
    """An absolute ``from engine.x import y`` must resolve.

    Relative imports are skipped because a missing sibling is caught by
    :class:`TestImportability` anyway; this class targets the specific failure
    mode of an absolute path naming a package that was renamed or never created.
    """

    def test_known_unimportable_modules_are_still_the_only_ones(self) -> None:
        """A new unimportable module is a regression; a fixed one must be removed
        from KNOWN_UNIMPORTABLE so the strict xfails below cannot rot.

        Uses the same subprocess sweep, for the same reason.
        """
        bad = set(TestImportability._sweep(sorted(ENGINE_MODULES)))
        unexpected = bad - KNOWN_UNIMPORTABLE
        assert not unexpected, f"new unimportable engine modules: {sorted(unexpected)}"
        stale = KNOWN_UNIMPORTABLE - bad
        assert not stale, f"these are now importable; update KNOWN_UNIMPORTABLE: {sorted(stale)}"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/scenarios/scenario_manager.py:16 imports "
            "`engine.hydroma.risk.assessment`, and that package does not exist in "
            "the repository. The source comment says '# hypothetical'. The whole "
            "scenario orchestration module is therefore unimportable, so scenario "
            "definition, execution and storage are all dead."
        ),
    )
    def test_scenario_manager_imports(self) -> None:
        importlib.import_module("engine.hydroma.scenarios.scenario_manager")

    def test_biofertilizer_seed_data_imports(self) -> None:
        """Guard for the 27 September 2026 fix.

        The module bound ``from datetime import datetime`` and then called
        ``datetime.date(...)``, which raises TypeError on the first record, so
        the whole file was unreachable. It is a two-token import fix, not a
        deletion, and this keeps it that way.
        """
        module = importlib.import_module("engine.hydroma.biofertilizer.data.seed_data")
        assert module is not None

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The single dangling absolute import in the engine tree is the "
            "`engine.hydroma.risk.assessment` reference above; removing it also "
            "clears this test."
        ),
    )
    def test_dangling_absolute_imports_resolve(self) -> None:
        offenders: list[str] = []
        for path in sorted(ENGINE_ROOT.rglob("*.py")):
            if _EXCLUDED_PARTS.intersection(path.relative_to(ENGINE_ROOT).parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError as exc:
                offenders.append(f"{path}: SyntaxError {exc}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    if not node.module.startswith(("engine", "database", "services", "shared")):
                        continue
                    try:
                        importlib.import_module(node.module)
                    except BaseException:
                        for alias in node.names:
                            if alias.name == "*":
                                continue
                            try:
                                importlib.import_module(f"{node.module}.{alias.name}")
                            except BaseException:
                                try:
                                    target = getattr(
                                        importlib.import_module(node.module), alias.name
                                    )
                                except BaseException as inner:
                                    offenders.append(
                                        f"{path.relative_to(ENGINE_ROOT)}:{node.lineno} "
                                        f"from {node.module} import {alias.name} "
                                        f"-> {type(inner).__name__}: {inner}"
                                    )
                                    del target
        assert not offenders, "unresolvable engine-targeted imports:\n" + "\n".join(offenders)


class TestNoDeadBranches:
    """Expression statements whose value is discarded are leftovers.

    ``foo()`` as a statement is legitimate (``logger.info(...)``, ``g.append(...)``);
    ``a + b`` as a statement is dead code, and in a numerical kernel dead
    arithmetic is usually a half-finished formula whose omission changes results.
    """

    @staticmethod
    def _discarded_sites(path: Path) -> list[str]:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return [
            str(node.lineno)
            for node in ast.walk(tree)
            if isinstance(node, ast.Expr) and isinstance(node.value, _VALUE_EXPR_NODES)
        ]

    @pytest.mark.parametrize(
        "path",
        [
            p
            for p in _walk_engine_sources()
            if p.relative_to(ENGINE_ROOT).as_posix() not in KNOWN_DISCARDED_SITES
        ],
        ids=lambda p: p.relative_to(ENGINE_ROOT).as_posix(),
    )
    def test_no_discarded_arithmetic(self, path: Path) -> None:
        """No engine source file outside the recorded set may discard arithmetic."""
        hits = self._discarded_sites(path)
        assert not hits, (
            f"{path.relative_to(ENGINE_ROOT).as_posix()} discards arithmetic on "
            f"line(s) {', '.join(hits)}"
        )

    def test_known_discarded_sites_are_still_reported(self) -> None:
        """Detects a *new* dead-arithmetic site without failing on the known set.

        A new offender is a regression and must fail; a recorded site that
        disappears means a defect was fixed and KNOWN_DISCARDED_SITES must be
        updated so the audit stays honest.
        """
        actual: dict[str, list[str]] = {}
        for path in _walk_engine_sources():
            hits = self._discarded_sites(path)
            if hits:
                actual[path.relative_to(ENGINE_ROOT).as_posix()] = hits
        assert set(actual) == set(KNOWN_DISCARDED_SITES), (
            "the set of files with discarded arithmetic changed.\n"
            f"  newly clean (update KNOWN_DISCARDED_SITES): "
            f"{sorted(set(KNOWN_DISCARDED_SITES) - set(actual))}\n"
            f"  newly dirty (add to KNOWN_DISCARDED_SITES): "
            f"{sorted(set(actual) - set(KNOWN_DISCARDED_SITES))}"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "watershed/calculator.py:119 drops the trapezoidal-storage "
            "rearrangement and line 400 drops the node-list lookup. Line 119 sits "
            "inside the check-dam height solve and is the visible remains of an "
            "abandoned formulation of the same equation computed on the next line."
        ),
    )
    def test_no_discarded_value_access(self) -> None:
        """Targeted: values computed and thrown away in the watershed designer.

        ``watershed/calculator.py`` keeps two statements whose result is dropped:
        the trapezoidal-storage rearrangement at line 119 and the node-list
        lookup at line 400. The first is a half-written height formula, which is
        a maintenance trap for a safety-critical structure sizing routine.
        """
        import inspect

        from engine.hydroma.watershed import calculator as ws

        offenders: list[str] = []
        for name in ("design_check_dam", "calculate_strahler_order"):
            tree = ast.parse(inspect.getsource(getattr(ws, name)))
            for node in ast.walk(tree):
                if isinstance(node, ast.Expr) and not isinstance(
                    node.value, (ast.Constant, ast.Name, ast.Attribute)
                ):
                    offenders.append(f"{name}:{node.lineno} discarded expression")
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    func = node.value.func
                    if isinstance(func, ast.Attribute) and func.attr not in {"copy"}:
                        offenders.append(f"{name}:{node.lineno} discarded call {func.attr}()")
        assert not offenders, "discarded results:\n" + "\n".join(offenders)


class TestSelfDocumentedClaims:
    """Docstrings that assert a property must be true of the code.

    ``design_check_dam`` states "all inputs are used; none is decorative". That
    is a testable claim and it is currently false. A reviewer reading only the
    docstring would assume the design responds to slope, so the claim is pinned.
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/watershed/calculator.py:82 docstring claims 'all "
            "inputs are used; none is decorative', but slope_pct is accepted and "
            "never referenced in the body, so a check dam sized on a 2 % slope is "
            "identical to one on a 60 % slope. design_half_moon ignores both "
            "slope_pct and rainfall_mm; design_terrace ignores terrace_width_m and "
            "instead hard-codes channel_volume_per_m = 0.135 m3/m."
        ),
    )
    def test_design_functions_use_every_parameter(self) -> None:
        import inspect
        import re

        from engine.hydroma.watershed.calculator import (
            design_check_dam,
            design_contour_trench,
            design_gully_plug,
            design_half_moon,
            design_terrace,
        )

        unused: list[str] = []
        for func in (
            design_check_dam,
            design_contour_trench,
            design_half_moon,
            design_terrace,
            design_gully_plug,
        ):
            body = inspect.getsource(func).split('"""', 2)[-1]
            for name in inspect.signature(func).parameters:
                if not re.search(rf"\b{re.escape(name)}\b", body):
                    unused.append(f"{func.__name__}({name})")
        assert not unused, f"accepted but never used: {unused}"

    def test_check_dam_claim_is_still_present(self) -> None:
        """The xfail above is only meaningful while the claim is in the source."""
        import inspect

        from engine.hydroma.watershed.calculator import design_check_dam

        assert "none is decorative" in inspect.getsource(design_check_dam)
