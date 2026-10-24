"""Gate tests: the §6.2 precondition for the ten novel indices.

The constitution (``docs/specs/ECO-NOJIN_MASTER_v3.1_UNIFIED.md`` §6.2) forbids
implementing or registering any of the ten novel indices — FDII, CDHE, CMSI,
WSNI, RRI, IWEq, WAI, WVI, PSI, CW — without a published definition plus an
independent reference anchor (SB-06 / AR-03). ``tools/novel_index_gate.py``
builds that gate; these tests pin its registry, its verdicts on the live cards
and on a fabricated one, the readiness report, and its stdlib-only budget.
"""

import ast
import importlib.util
import sys
import types
from pathlib import Path

from engine.honesty import VOCABULARY

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "tools" / "novel_index_gate.py"
INDICATORS_DIR = REPO_ROOT / "indicators"

TEN_CODES = ["FDII", "CDHE", "CMSI", "WSNI", "RRI", "IWEq", "WAI", "WVI", "PSI", "CW"]


def _load_gate() -> types.ModuleType:
    """Load the gate tool by path; it is a script in ``tools/``, not a package."""
    spec = importlib.util.spec_from_file_location("novel_index_gate_under_test", GATE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise AssertionError(f"cannot load the gate tool from {GATE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def test_all_ten_novel_indices_are_declared():
    assert [index.code for index in gate.NOVEL_INDICES] == TEN_CODES
    assert len(gate.NOVEL_INDICES) == 10
    for index in gate.NOVEL_INDICES:
        assert index.name, f"{index.code} carries no published name"
        assert index.role, f"{index.code} carries no business role"
    roles = {index.code: index.role for index in gate.NOVEL_INDICES}
    assert "H2" in roles["FDII"]
    assert "H6" in roles["CW"]
    # The gate's evidence vocabulary is the honesty module's own, not a copy
    # that can drift away from it.
    assert set(gate.load_evidence_vocabulary(REPO_ROOT)) == set(VOCABULARY)


def test_no_indicator_file_violates_the_precondition():
    result = gate.scan_indicators(INDICATORS_DIR, VOCABULARY)
    live = {card.indicator_id for card in result.cards if card.status == gate.STATUS_SUPPORTED}
    assert live == {
        "ENO_ET0_FAO56_001",
        "ENO_ETC_KC_001",
        "ENO_SPI_001",
        "ENO_WB_001",
        "ENO_WP_001",
    }
    assert result.violations == []
    # Every supported card carries an evidence class from the honesty vocabulary.
    for card in result.cards:
        if card.status == gate.STATUS_SUPPORTED:
            assert card.evidence_class in VOCABULARY
    template = [card for card in result.cards if card.path.name == "_TEMPLATE.yaml"]
    assert len(template) == 1
    assert template[0].status == gate.STATUS_EXEMPT
    assert template[0].violation is None


def test_a_fabricated_indicator_is_rejected(tmp_path):
    fabricated = tmp_path / "ENO_FAKE_001.yaml"
    fabricated.write_text(
        "\n".join(
            [
                'indicator_id: "ENO_FAKE_001"',
                "name:",
                '  en: "Fabricated Composite"',
                '  fa: ""',
                'domain: "composite"',
                'formula: "X = Y"',
                'unit: "mm"',
                "input_variables: []",
                'reference: "methodology"',
                'validation_status: "VALIDATED_EXTERNAL"',
                'evidence_class: ""',
                "",
            ]
        ),
        encoding="utf-8",
    )
    verdict = gate.check_indicator_card(fabricated, VOCABULARY)
    assert verdict.status == gate.STATUS_BLOCKED
    assert verdict.violation == gate.VIOLATION_CODE
    assert gate.VIOLATION_CODE == "BLOCKED_NO_PUBLISHED_DEFINITION"
    assert any("methodology" in reason for reason in verdict.reasons)


def test_readiness_report_records_the_ten_as_not_implemented(tmp_path):
    report_path = tmp_path / "NOVEL-INDEX-READINESS.md"
    exit_code = gate.main(["--report", str(report_path)])
    assert exit_code == 0
    text = report_path.read_text(encoding="utf-8")
    for index in gate.NOVEL_INDICES:
        rows = [line for line in text.splitlines() if line.startswith(f"| {index.code} |")]
        assert len(rows) == 1, f"{index.code} must appear exactly once as a table row"
        assert "NOT IMPLEMENTED" in rows[0]
        assert gate.NOT_IMPLEMENTED_VERDICT in rows[0]
        assert index.role in rows[0]
    assert text.count(gate.NOT_IMPLEMENTED_VERDICT) == len(gate.NOVEL_INDICES)


def test_gate_is_stdlib_only():
    source = GATE_PATH.read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names)
    assert "engine" not in imported
    assert "import engine" not in source
    assert "from engine" not in source
