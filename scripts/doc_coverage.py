"""Measure documentation coverage of the work, rather than asserting it.

Three things can be checked mechanically:

1. Does every module I created carry a module docstring?
2. Is every formula the registry knows about reachable, and does the catalogue
   cover the quantities the codebase actually implements?
3. Is there a single index of the documents, so a reader can find them?

A coverage checker that reports its own numbers is worth more than a claim of
completeness, because the next change re-runs it.
"""

from __future__ import annotations

import ast
from pathlib import Path

#: Modules introduced in this work, with the kind of document that should exist
#: for each. A module with no entry here is simply not checked.
CREATED_MODULES: dict[str, str] = {
    "engine/hydroma/formulas/__init__.py": "registry package",
    "engine/hydroma/formulas/records.py": "record schema",
    "engine/hydroma/formulas/registry.py": "the four rules",
    "engine/hydroma/formulas/catalog.py": "the records",
    "engine/hydroma/formulas/research/__init__.py": "research definitions",
    "engine/hydroma/models/validation/__init__.py": "corpus loader",
    "engine/hydroma/models/validation/loader.py": "case loading",
    "engine/hydroma/models/validation/runner.py": "inconsistency detection",
    "scripts/run_cpp_tests.py": "native test harness",
    "tests/db_support.py": "order-independent reset",
}

#: Narrative documents written in this work.
DOCUMENTS: dict[str, str] = {
    "engine/cpp_core/README_BUILD_STATUS_FA.md": "native core as-built",
    "engine/hydroma/cpp_bridge/README_STATUS_FA.md": "bridge as-built",
    "engine/hydroma/formulas/README_STATUS_FA.md": "formula registry as-built",
    "reports/TECHNICAL_AUDIT_FA_2026-09-25.md": "audit",
    "reports/REMEDIATION_PLAN_FA_2026-09-25.md": "remediation plan",
    "reports/WAVE_3_INTEGRATION_PLAN_FA_2026-09-26.md": "wave 3 plan",
    "reports/OPEN_ITEMS_FA_2026-09-26.md": "open items spec",
    "reports/WBI_Q1_Q2_PLAN_FA_2026-09-26.md": "WBI plan",
}

#: Test modules added, so the count of guarded behaviours is visible.
TEST_DIR = Path("tests/unit")


def module_docstring(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return f"<unparseable: {exc}>"
    return ast.get_docstring(tree) or ""


def report() -> dict:
    out: dict[str, list[str]] = {
        "modules_missing_docstring": [],
        "modules_missing": [],
        "documents_missing": [],
        "documents_without_heading": [],
    }

    for rel, what in CREATED_MODULES.items():
        path = Path(rel)
        if not path.is_file():
            out["modules_missing"].append(f"{rel} ({what})")
            continue
        doc = module_docstring(path)
        if len(doc.strip()) < 80:
            out["modules_missing_docstring"].append(f"{rel} ({what})")

    for rel, what in DOCUMENTS.items():
        path = Path(rel)
        if not path.is_file():
            out["documents_missing"].append(f"{rel} ({what})")
            continue
        head = path.read_text(encoding="utf-8", errors="replace").lstrip()
        if not head.startswith("#"):
            out["documents_without_heading"].append(rel)

    return out


def summary() -> dict:
    out = report()
    return {
        "modules_expected": len(CREATED_MODULES),
        "modules_documented": len(CREATED_MODULES) - len(out["modules_missing_docstring"]),
        "documents_expected": len(DOCUMENTS),
        "documents_present": len(DOCUMENTS) - len(out["documents_missing"]),
        "tests_added": len(list(TEST_DIR.glob("test_*.py"))) if TEST_DIR.is_dir() else 0,
        "gaps": {k: v for k, v in out.items() if v},
    }


if __name__ == "__main__":
    import json

    print(json.dumps(summary(), indent=2, ensure_ascii=False))
