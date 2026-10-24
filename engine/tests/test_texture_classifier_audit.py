"""Audit tests for the engine's USDA texture classifier (item 1: free alternative).

These tests pin what ``tools/characterize_texture_classifier.py`` measures about the
engine's own classifier, so that any change to the classifier has to be deliberate:

1. the number of compositions that fall through to the ``"loam"`` fallback is
   pinned, both to the number recorded in the generated audit report and to the
   782 figure the module documents;
2. the classifier is total and deterministic over the whole triangle;
3. the audit report exists and records the gap, including the closing statement of
   what a corrected table needs;
4. the tool itself stays free of third-party and GPL code -- it is the
   measurement half of the free alternative to the GPL-3.0 ``soiltexture``
   package, so it must never import one.

The scan function is imported from the tool by file path (``tools/`` is not a
package), the same way ``engine/tests/test_architecture_rules.py`` loads
``tools/detect_imports.py``. The scan is the full 5151-composition grid: it is a
module-scoped fixture so it runs once for the whole file, and it is fast (pure
integer comparisons over 5151 compositions -- well under a second), so there is
no sampling. If it ever becomes slow, sample a documented sub-grid here and keep
the full grid in the tool; do not delete the full scan from the tool.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = PROJECT_ROOT / "tools" / "characterize_texture_classifier.py"
REPORT_PATH = PROJECT_ROOT / "reports" / "eco-nojin" / "TEXTURE-CLASSIFIER-AUDIT.md"

#: The audit finding: 782 of the 5151 integer compositions answer to a guess.
PINNED_FALLBACK_COUNT = 782

#: Total integer compositions of the triangle (sand + silt + clay == 100).
PINNED_TOTAL = 5151

#: Phrases that must never appear in the tool's source: the GPL-3.0 package it
#: replaces, and the plotting stack that would drag third-party code (and a
#: display) into an audit that must stay runnable anywhere.
FORBIDDEN_TOOL_TOKENS = ("soiltexture", "matplotlib", "GPL")

#: The closing section that states what a corrected table needs.
REQUIRED_REPORT_PHRASES = ("USDA public-domain",)


def _load_tool():
    """Import the audit tool by file path (tools/ is not a package)."""
    name = "characterize_texture_classifier_under_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load audit tool from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


@pytest.fixture(scope="module")
def scan_result():
    """The full-grid scan, run once for this file."""
    return tool.scan()


def test_fallback_count_is_pinned(scan_result):
    """The fallback count equals the number recorded in the audit report."""
    report = REPORT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"^\|\s*{re.escape(tool.SUMMARY_FALLBACK_LABEL)}\s*\|\s*(\d+)\s*\|",
        report,
        re.MULTILINE,
    )
    assert match is not None, (
        f"audit report {REPORT_PATH} has no '{tool.SUMMARY_FALLBACK_LABEL}' row; "
        "regenerate it with tools/characterize_texture_classifier.py"
    )
    recorded_in_report = int(match.group(1))

    assert scan_result.fallback_count == PINNED_FALLBACK_COUNT
    assert recorded_in_report == PINNED_FALLBACK_COUNT
    assert scan_result.total == PINNED_TOTAL


def test_classifier_is_deterministic_and_total(scan_result):
    """Every composition returns a non-empty string, and the same one twice."""
    for record in scan_result.records:
        assert isinstance(record.texture, str)
        assert record.texture, f"empty class for {record.as_ternary()}"
        sandy_first = tool.classify_texture(record.sand, record.silt, record.clay)
        sandy_second = tool.classify_texture(record.sand, record.silt, record.clay)
        assert sandy_first == record.texture, (
            f"{record.as_ternary()} classified differently on re-run: "
            f"{record.texture!r} then {sandy_first!r}"
        )
        assert sandy_second == record.texture

    # The public entry point and the engine's resolution function are the same
    # code path; if they ever diverge the scan would be measuring two things.
    assert scan_result.entry_point_disagreements == []


def test_the_report_exists_and_records_the_gap():
    """The audit markdown exists and states the gap plus what a repair needs."""
    assert REPORT_PATH.exists(), (
        f"{REPORT_PATH} missing; run tools/characterize_texture_classifier.py"
    )
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert str(PINNED_FALLBACK_COUNT) in report
    assert tool.FALLBACK_SITE in report
    for phrase in REQUIRED_REPORT_PHRASES:
        assert phrase in report, f"audit report is missing the {phrase!r} closing section"
    # The report must say the tool does not change the classifier.
    assert "does **not** touch the classifier" in report


def test_no_gpl_or_third_party_import_in_the_tool():
    """The free alternative stays free: no GPL or third-party token in the tool."""
    source = TOOL_PATH.read_text(encoding="utf-8")
    for token in FORBIDDEN_TOOL_TOKENS:
        assert token not in source, (
            f"tools/characterize_texture_classifier.py mentions {token!r}; "
            "the audit tool must stay stdlib-only"
        )
    # And it must not import anything outside the stdlib and the engine.
    engine_imports = {
        line.split()[1] for line in source.splitlines() if line.startswith("from engine")
    }
    assert engine_imports <= {
        "engine.hydroma.soil",
        "engine.hydroma.soil.texture",
    }, f"unexpected engine imports: {sorted(engine_imports)}"
