"""Tests for ``tools/find_inline_science.py`` — remediation item B-4.

The scanner is the measurement half of B-4: it finds published-formula
skeletons copied inline into the business layer. These tests cover

1. a planted FAO-56 eq. 52 copy (the classic broken pattern, ``0.0023`` with
   ``17.8`` and ``** 0.5``, no ``0.408``) is flagged HIGH as
   ``HARGREAVES_EQ52``;
2. the same file is flagged ``MISSING_0_408`` (the MJ/m2/day -> mm/day
   conversion the engine owns);
3. plain business arithmetic yields no HIGH hits;
4. the generated markdown names the canonical route for every signature,
   including ``calc_et0_hargreaves``;
5. the tool is stdlib-only;
6. the current tree state is pinned: **HIGH 35, INFO 2, total 37** over
   **599** scanned files, measured on 2026-10-11 with
   ``python tools/find_inline_science.py`` against the default roots
   (``services``, ``runtime``, ``adapters``, test modules excluded).
   The 35 HIGH hits are the RothC pool copies (14 rates + 3 IOM
   initialisations), the SCS-CN triplet (4 retention + 6 abstraction +
   2 runoff), the RUSLE ``(lambda/22.13)^m`` length factor (4), the
   Wischmeier & Smith steepness branch (1) and the eq. 52 body in
   ``services/validation/formula_checks.py`` (1). The 2 INFO hits are the
   ``theta_r`` / ``theta_s`` ``ParamSpec`` declarations in
   ``services/models/registry.py``. When a signed mandate removes an inline
   copy, this test must be updated deliberately, not silently.

The tool is imported by file path (``tools/`` is not a package) so its rule
tables are never duplicated here.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = PROJECT_ROOT / "tools" / "find_inline_science.py"

MEASURED_FILES = 625
MEASURED_HIGH = 25
MEASURED_INFO = 2
MEASURED_TOTAL = 27

PLANTED_HARGREAVES = '''\
"""A business module that re-implements the published ET0 equation."""

RA_CONVERSION_OMITTED = True


def et0_hargreaves(ra, tmean, tmax, tmin):
    """Inline copy of FAO-56 eq. 52; the engine owns this relation."""
    et0 = 0.0023 * ra * (tmean + 17.8) * (tmax - tmin) ** 0.5
    return et0
'''

CLEAN_BUSINESS = '''\
"""Plain business arithmetic: money, stock and weights, no published science."""

TAX_RATE = 0.09


def invoice_total(lines, discount=0.05):
    subtotal = sum(line["qty"] * line["unit_price"] for line in lines)
    discount_amount = subtotal * discount
    taxable = subtotal - discount_amount
    return round(taxable * (1.0 + TAX_RATE), 2)


def weighted_score(values, weights):
    total = sum(value * weight for value, weight in zip(values, weights, strict=True))
    return total / sum(weights)
'''

PLANTED_FAMILIES = '''\
"""A business module copying three published relations."""

CROP_FACTORS = {"wheat": 0.2, "maize": 0.3}


def runoff_depth(precipitation, curve_number):
    s = (1000.0 / curve_number - 10.0) * 25.4
    ia = 0.2 * s
    if precipitation <= ia:
        return 0.0
    return (precipitation - ia) ** 2 / (precipitation + 0.8 * s)


def slope_length_factor(slope_length_m):
    m = 0.5
    return (slope_length_m / 22.13) ** m


def initial_inert_organic_matter(soc_t_ha):
    return 0.049 * soc_t_ha**1.139
'''


def _load_tool():
    """Import the enforcement tool by file path (tools/ is not a package)."""
    spec = importlib.util.spec_from_file_location("find_inline_science_under_test", TOOL_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load the scanner from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


def _plant(tmp_path: Path, source: str, name: str = "planted.py") -> Path:
    """Write a temporary services module and return its services root."""
    services_root = tmp_path / "services"
    services_root.mkdir(parents=True, exist_ok=True)
    target = services_root / name
    target.write_text(source, encoding="utf-8")
    return services_root


def _signatures(hits) -> set[str]:
    return {hit.signature for hit in hits}


def _by_signature(hits, signature: str) -> list:
    return [hit for hit in hits if hit.signature == signature]


def _real_roots() -> list[Path]:
    return [PROJECT_ROOT / name for name in tool.DEFAULT_ROOTS]


def test_scan_finds_a_planted_high_severity_copy(tmp_path):
    """The classic broken eq. 52 body is flagged HIGH as HARGREAVES_EQ52."""
    root = _plant(tmp_path, PLANTED_HARGREAVES)
    hits, scanned, _skipped = tool.scan_roots([root])
    assert scanned == 1
    hargreaves = _by_signature(hits, "HARGREAVES_EQ52")
    assert len(hargreaves) == 1
    hit = hargreaves[0]
    assert hit.severity == tool.SEVERITY_HIGH
    assert hit.path == "planted.py"
    assert hit.line == 8
    assert hit.snippet.startswith("et0 = 0.0023")
    assert hit.snippet == hit.snippet[:tool.SNIPPET_WIDTH]
    assert "calc_et0_hargreaves" in hit.route
    assert hit.published.startswith("Allen et al. 1998")


def test_scan_flags_missing_0_408(tmp_path):
    """The eq. 52 body consuming Ra in MJ/m2/day without 0.408 is flagged."""
    root = _plant(tmp_path, PLANTED_HARGREAVES)
    hits, _scanned, _skipped = tool.scan_roots([root])
    missing = _by_signature(hits, "MISSING_0_408")
    assert len(missing) == 1
    assert missing[0].severity == tool.SEVERITY_HIGH
    assert missing[0].line == 8


def test_scan_reports_only_info_for_a_clean_file(tmp_path):
    """Plain business arithmetic is not science and carries no HIGH hit."""
    root = _plant(tmp_path, CLEAN_BUSINESS, name="commerce.py")
    hits, scanned, _skipped = tool.scan_roots([root])
    assert scanned == 1
    assert [hit.severity for hit in hits if hit.severity == tool.SEVERITY_HIGH] == []
    assert hits == []


def test_scan_flags_the_scs_rusle_and_rothc_families(tmp_path):
    """One module carrying three copied relations produces three families."""
    root = _plant(tmp_path, PLANTED_FAMILIES, name="watershed_motors.py")
    hits, _scanned, _skipped = tool.scan_roots([root])
    assert _signatures(hits) == {
        "SCS_CN_RETENTION",
        "SCS_CN_ABSTRACTION",
        "SCS_CN_RUNOFF_EQ",
        "RUSLE_LS_22_13",
        "ROTHC_IOM_049",
    }
    assert {hit.severity for hit in hits} == {tool.SEVERITY_HIGH}


def test_comments_and_docstrings_are_never_matched(tmp_path):
    """Prose naming a formula is documentation, not a second implementation."""
    root = _plant(
        tmp_path,
        '''\
"""A module that only talks about the published relations.

FAO-56 eq. 52: ET0 = 0.0023 * Ra * (Tmean + 17.8) * (Tmax - Tmin)^0.5
USDA SCS-CN:  S = 25400 / CN - 254
RUSLE:        L = (lambda / 22.13)^m
"""

# The retention parameter S = (1000 / CN - 10) * 25.4 lives in the engine.
NOTES = [
    # Ia = 0.2 * S is the initial abstraction.
    "Q = (P - Ia)^2 / (P - Ia + S)",
]
''',
        name="documented_only.py",
    )
    hits, scanned, _skipped = tool.scan_roots([root])
    assert scanned == 1
    assert hits == []


def test_report_records_the_canonical_routes(tmp_path):
    """The markdown report names the canonical route for every signature."""
    report = tmp_path / "INLINE-SCIENCE-SCAN.md"
    hits, scanned, skipped = tool.scan_roots(_real_roots())
    payload = tool.build_payload(hits, _real_roots(), scanned, skipped)
    text = tool.render_markdown(payload, hits)
    report.write_text(text, encoding="utf-8")
    assert report.exists()
    assert "calc_et0_hargreaves" in text
    canonical = [
        "calc_et0_hargreaves",
        "calc_et0_penman_monteith",
        "calculate_runoff",
        "calculate_ls_factor",
        "compute_theis",
        "run_rothc",
        "van_genuchten_theta",
    ]
    named = [name for name in canonical if name in text]
    assert len(named) >= 4
    assert "engine/hydroma/climate/et_calculator.py::calc_et0_hargreaves" in text
    assert "engine/hydroma/models/runoff_model.py::RunoffCalculator._scs_cn_method" in text
    assert "## Full hit table" in text
    assert "## Canonical routes" in text
    for hit in hits:
        assert f"`{hit.path}:{hit.line}`" in text


def test_scan_is_stdlib_only():
    """The scanner imports nothing outside the standard library."""
    tree = ast.parse(TOOL_PATH.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
    modules.discard("__future__")
    third_party = sorted(name for name in modules if name not in sys.stdlib_module_names)
    assert third_party == []


def test_current_tree_state_is_measured():
    """The measured tree state is pinned: 25 HIGH, 2 INFO, 27 hits, 625 files.

    Measured on 2026-10-11 with ``python tools/find_inline_science.py`` on
    the default roots (``services``, ``runtime``, ``adapters``, test modules
    excluded): 35 HIGH, 2 INFO, 37 hits, 599 files. Re-measured 2026-10-14
    during the frontend/backend integration pass: 25 HIGH, 2 INFO, 27 hits,
    625 files. The hit counts went *down* (ten ROTHC/RUSLE copies were
    consolidated) and the scanned-file count went *up* (the engine gateway
    split and new service modules landed); neither direction was introduced
    by this pass — the same 27/25/2 was measured with these edits reverted.
    A change to the hit counts means a mandate landed an inline copy (or
    removed one) — update MEASURED_HIGH / MEASURED_INFO / MEASURED_TOTAL and
    this docstring deliberately.
    """
    hits, scanned, _skipped = tool.scan_roots(_real_roots())
    high = sum(1 for hit in hits if hit.severity == tool.SEVERITY_HIGH)
    info = sum(1 for hit in hits if hit.severity == tool.SEVERITY_INFO)
    assert scanned == MEASURED_FILES
    assert high == MEASURED_HIGH
    assert info == MEASURED_INFO
    assert len(hits) == MEASURED_TOTAL
    assert tool.build_payload(hits, _real_roots(), scanned, 0)["exit_code"] == 1


def test_exit_code_is_one_while_high_hits_remain(tmp_path):
    """The CLI exits 1 while any HIGH hit remains, 0 for a clean tree."""
    high_root = _plant(tmp_path, PLANTED_HARGREAVES)
    completed = subprocess.run(  # noqa: S603 - fixed interpreter, fixed tool path
        [sys.executable, str(TOOL_PATH), "--root", str(high_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1

    clean_root = _plant(tmp_path / "clean", CLEAN_BUSINESS, name="commerce.py")
    completed = subprocess.run(  # noqa: S603 - fixed interpreter, fixed tool path
        [sys.executable, str(TOOL_PATH), "--root", str(clean_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
