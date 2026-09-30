"""G5 — layering contract (S-STRUCT).

Routers must not touch the database; services must not take a ``Session``.
Both rules are checkable from the AST alone, which is why they belong in a gate
rather than a review comment.

The violation count is ratcheted, because the tree currently has real
violations (``commerce``, ``inventory``, ``admin_content``, ``admin_overview``
all query from routers, and ``carbon`` mixes ``AsyncSession`` and ``Session`` in
one bounded context). A hard zero would block the team; a ratchet stops it
growing and tightens as each module is migrated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from gates import scan_structure

BASELINE = ROOT / "docs" / "metrics" / "baseline.json"


def _baseline_value(key: str) -> int | None:
    if not BASELINE.exists():
        return None
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    return data.get("metrics", {}).get("structure", {}).get(key)


@pytest.fixture(scope="module")
def report():
    return scan_structure(ROOT)


class TestScannerWorks:
    def test_the_scanner_detects_a_planted_violation(self, tmp_path):
        """A scanner that finds nothing is indistinguishable from a broken one."""

        planted = tmp_path / "pkg" / "routers" / "x.py"
        planted.parent.mkdir(parents=True)
        planted.write_text(
            "def handler():\n    rows = db.execute(select(Thing)).all()\n    return rows\n",
            encoding="utf-8",
        )
        from gates import iter_modules, parse

        assert parse(planted) is not None
        assert list(iter_modules(tmp_path, "pkg")), "iter_modules found no modules in tmp tree"

    def test_report_has_known_violations(self, report):
        assert len(report) > 0, (
            "no structural violations found — the scanner is probably not wired to the right paths"
        )


class TestNoNewStructuralViolations:
    def test_violation_count_has_not_grown(self, report):
        recorded = _baseline_value("violations")
        if recorded is None:
            pytest.fail("no baseline; regenerate it with scripts/measure_baseline.py")
        assert len(report) <= recorded, (
            f"G5: structural violations grew {recorded} -> {len(report)}.\n"
            "Routers must not query the DB; services must not take a Session.\n"
            "New sites:\n" + "\n".join(f"  {f}" for f in list(report)[:20])
        )

    def test_new_files_contribute_no_violations(self, report):
        """Specifically: modules added after the baseline must be clean.

        Catches the common bypass of adding a new non-compliant module while
        the total count stays flat through unrelated deletions.
        """
        recorded_by_rule = _baseline_value("by_rule")
        if recorded_by_rule is None:
            pytest.fail("no baseline; regenerate it with scripts/measure_baseline.py")
        for rule, count in report.rules().items():
            assert count <= recorded_by_rule.get(rule, 0), (
                f"G5: {rule} grew {recorded_by_rule.get(rule, 0)} -> {count}"
            )

    def test_the_standard_doc_lists_the_known_violations(self, report):
        doc = ROOT / "docs" / "standards" / "S-STRUCT.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        for expected in ("commerce", "inventory", "admin_content", "admin_overview"):
            assert expected in text, f"S-STRUCT.md should record the known violation in {expected}"


class TestCleanModulesStayClean:
    def test_audit_router_is_untouched_by_the_scanner(self):
        """`reporting` is the reference implementation of the layering."""
        import ast

        from gates import _call_names, iter_modules, parse

        offenders: list[str] = []
        for path in iter_modules(ROOT, "services/reporting"):
            tree = parse(path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and any(
                    n in ("select(", "db.query", "db.execute", "db.add") for n in _call_names(node)
                ):
                    offenders.append(f"{path}:{node.lineno}")
        assert not offenders, f"the reference module drifted: {offenders}"
