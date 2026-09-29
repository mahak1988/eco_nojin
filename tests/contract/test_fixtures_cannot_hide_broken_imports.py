"""A fixture may not silently skip because of a broken import.

The failure mode this gate exists for appeared four times during the phase 4/5
work, each time in a different place:

* ``services/conftest.py`` had **20** fixtures importing
  ``services.<package>.service`` — a module that does not exist in any of
  those packages. Each raised ``ImportError``, caught it, and called
  ``pytest.skip``. No test ever requested any of them, so they were 20 pieces
  of decoration that looked like infrastructure.
* ``services/conftest.py::ecowallet_service`` imported ``EcowalletService``,
  a class that was never defined in the module it was importing from.
* ``services/conftest.py::scientific_motors_service`` imported
  ``services.scientific_motors.service``, which does not exist.
* ``tests/test_finance.py`` imported a ``LedgerService`` that had been
  consolidated away — and because it was a *collection* error, it aborted a
  bare ``pytest`` before any test ran.

The shared shape: a typo or a refactor leaves an import that raises, the
``ImportError`` is swallowed by a ``pytest.skip``, and the suite reports
success. Nothing is red. The coverage simply is not there.

The check below resolves every module-level import inside every fixture body
and fails if one cannot be imported. It is deliberately cheap: it does not
execute fixtures, it only resolves imports.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CONFTESTS = [
    path
    for path in sorted(ROOT.glob("**/conftest.py"))
    if not any(part in {"node_modules", ".venv", "__pycache__", ".kilo", "build", "dist"} for part in path.parts)
]


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _unresolvable_imports(path: Path) -> list[tuple[int, str]]:
    """Return (lineno, dotted_name) for imports inside fixtures that cannot resolve."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, ValueError):
        return []

    broken: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.ImportFrom) and sub.module and not sub.level):
                continue
            try:
                importlib.import_module(sub.module)
            except BaseException:
                broken.append((sub.lineno, sub.module))
    return broken


class TestNoFixtureHidesABrokenImport:
    def test_conftests_exist(self):
        assert CONFTESTS, "the glob found no conftest; the gate would pass vacuously"

    @pytest.mark.parametrize("conftest", CONFTESTS, ids=_relative)
    def test_every_fixture_import_resolves(self, conftest: Path):
        broken = _unresolvable_imports(conftest)
        assert not broken, (
            f"{_relative(conftest)} has fixture imports that cannot be resolved; the "
            "fixture will catch the ImportError and silently skip, so the tests "
            "requesting it never run:\n"
            + "\n".join(f"  line {line}: {name}" for line, name in broken)
        )

    def test_the_scan_detects_a_planted_broken_import(self, tmp_path):
        """Guard against the gate passing because the scan is broken."""
        planted = tmp_path / "conftest.py"
        planted.write_text(
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def thing():\n"
            "    try:\n"
            "        from services.definitely_not_a_real_module import Thing\n"
            "    except ImportError:\n"
            "        pytest.skip('nope')\n"
            "    return Thing\n",
            encoding="utf-8",
        )
        found = _unresolvable_imports(planted)
        assert [name for _, name in found] == ["services.definitely_not_a_real_module"], found

    def test_a_legitimate_submodule_import_is_not_reported(self, tmp_path):
        """``from pkg import submodule`` is valid but invisible to hasattr."""
        planted = tmp_path / "conftest.py"
        planted.write_text(
            "import pytest\n"
            "\n"
            "@pytest.fixture\n"
            "def thing():\n"
            "    from database.config import init_db\n"
            "    return init_db\n",
            encoding="utf-8",
        )
        assert _unresolvable_imports(planted) == []


class TestNoFixtureHidesABrokenSymbol:
    """A resolvable module can still lack the name being imported."""

    def test_named_imports_exist_on_their_module(self) -> None:
        broken: list[str] = []
        for conftest in CONFTESTS:
            try:
                tree = ast.parse(conftest.read_text(encoding="utf-8", errors="ignore"))
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                for sub in ast.walk(node):
                    if not (isinstance(sub, ast.ImportFrom) and sub.module and not sub.level):
                        continue
                    try:
                        module = importlib.import_module(sub.module)
                    except BaseException:
                        continue  # reported by the test above
                    for alias in sub.names:
                        if alias.name == "*":
                            continue
                        if hasattr(module, alias.name):
                            continue
                        # ``from pkg import submodule`` is legal but
                        # ``hasattr(pkg, "submodule")`` is False until the
                        # submodule is actually imported. Try it before
                        # reporting, or the gate cries wolf.
                        try:
                            importlib.import_module(f"{sub.module}.{alias.name}")
                        except BaseException:
                            broken.append(
                                f"{_relative(conftest)}:{sub.lineno} "
                                f"{sub.module}.{alias.name} does not exist"
                            )
        assert not broken, (
            "these fixture imports name a symbol the module does not define, so the "
            "ImportError is swallowed and the fixture always skips:\n  "
            + "\n  ".join(broken)
        )
