"""Honesty contract tests: a recorded result is not a validated one.

These tests pin the vocabulary in ``engine/honesty/statuses.py`` so that the
legacy alias ``"validated"`` cannot survive into any new claim, and so that
external evidence is the only route to the ``VALIDATED_EXTERNAL`` status.
They also pin the constitution v3.1 vocabulary: the ten safety brakes
(SB-01..SB-10) and the thirteen architecture rules (AR-01..AR-13).
"""

import ast
import sys
from pathlib import Path

import pytest

from engine.honesty.statuses import (
    AR_COUNT,
    AR_RULES,
    BRAKE_COUNT,
    BRAKES,
    VOCABULARY,
    refine_claim,
)


def test_vocabulary_terms_are_exactly_the_six_documented_ones():
    assert len(VOCABULARY) == 6
    assert set(VOCABULARY) == {
        "VALIDATED_EXTERNAL",
        "VALIDATED_METHOD_CONFORMANCE",
        "REGRESSION_ANCHOR_STABLE",
        "PARTIAL",
        "UNVALIDATED",
        "BLOCKED",
    }


def test_unknown_term_raises_value_error():
    for term in ("validated_external", "RECORDED", "", "PARTIAL ", "anchored"):
        with pytest.raises(ValueError):
            refine_claim(term, "PARTIAL")
        with pytest.raises(ValueError):
            refine_claim("PARTIAL", term)


def test_recorded_is_not_validated():
    assert refine_claim("validated", "REGRESSION_ANCHOR_STABLE") == "REGRESSION_ANCHOR_STABLE"
    assert refine_claim("validated", "VALIDATED_METHOD_CONFORMANCE") == "REGRESSION_ANCHOR_STABLE"


def test_external_evidence_keeps_the_claim():
    assert refine_claim("validated", "VALIDATED_EXTERNAL") == "VALIDATED_EXTERNAL"


def test_non_validated_claims_pass_through():
    assert refine_claim("PARTIAL", "UNVALIDATED") == "PARTIAL"
    assert refine_claim("BLOCKED", "VALIDATED_EXTERNAL") == "BLOCKED"


V31_SAFETY_BRAKES = (
    "SB-01 change to more than 5 main files",
    "SB-02 deletion of more than 100 lines of code",
    "SB-03 public API change (name/input/output/exception)",
    "SB-04 pip install outside the approved stack",
    "SB-05 change of units or decision weights",
    "SB-06 synthetic data used in place of a scientific reference",
    "SB-07 change of a scientific equation (FAO/USDA/WMO) without a reference",
    "SB-08 test coverage below 80%",
    "SB-09 detect_imports.py mismatch",
    "SB-10 no Fix Log or Evidence for a change over 50 lines",
)


def test_brakes_are_the_ten_v31_safety_brakes():
    assert len(BRAKES) == 10
    assert BRAKE_COUNT == 10
    assert BRAKES == V31_SAFETY_BRAKES
    assert all(isinstance(brake, str) and brake.strip() for brake in BRAKES)


def test_architecture_rules_include_the_preserved_three():
    """AR-11/AR-12/AR-13 preserve the three rules v3.1 kept from the earlier spec."""
    rules = dict(AR_RULES)
    assert rules["AR-11"] == "no frontend/auth/payment/blockchain in the scientific core"
    assert rules["AR-12"] == "services shall not call model internals"
    assert rules["AR-13"] == "all model calls go through the Gateway"


def test_rule_ids_are_unique_and_ordered():
    """AR-01..AR-13 in order, with no duplicate id (constitution v3.1 section 3)."""
    assert len(AR_RULES) == 13
    assert AR_COUNT == 13
    rules = dict(AR_RULES)
    assert len(rules) == 13
    ids = [rule_id for rule_id, _ in AR_RULES]
    assert ids == [f"AR-{number:02d}" for number in range(1, 14)]
    assert rules["AR-01"].startswith("Separation of Concerns")
    assert rules["AR-10"].startswith("Testable Architecture")


OLD_SEVEN_BRAKES = (
    # (superseded seven-term brake, keywords carried by the v3.1 brake that replaces it)
    ("public API signature change", ("public API",)),
    ("equation or parameter change in a scientific kernel", ("scientific", "equation")),
    ("breakage of the evidence chain", ("Evidence",)),
    ("architecture change touching more than 5 main files", ("main files", "5")),
    ("repaired/weakened test instead of a fixed defect", ("test",)),
    ("scientific claim on synthetic data", ("synthetic data",)),
    ("calendar/unit system change", ("unit",)),
)


def test_old_seven_brakes_are_covered_by_the_ten():
    """Every superseded seven-term brake is carried by exactly one of the ten.

    The mapping is asserted by substring keywords rather than full-string
    equality because the v3.1 wording is deliberately broader (documented in
    ``engine/honesty/statuses.py``). Old -> v3.1: API signature -> SB-03;
    kernel equation -> SB-07; evidence chain -> SB-10; more than 5 main files
    -> SB-01; weakened test -> SB-08; synthetic data -> SB-06; unit system
    -> SB-05.
    """
    assert len(OLD_SEVEN_BRAKES) == 7
    covering_brakes = set()
    for old_term, keywords in OLD_SEVEN_BRAKES:
        covering = [brake for brake in BRAKES if all(word in brake for word in keywords)]
        assert len(covering) == 1, (
            f"the old brake {old_term!r} must be carried by exactly one v3.1 "
            f"brake, found {covering}"
        )
        assert old_term not in BRAKES, (
            f"the old brake wording {old_term!r} was supposed to be superseded"
        )
        covering_brakes.add(covering[0])
    assert len(covering_brakes) == 7


def test_statuses_module_imports_nothing_outside_the_stdlib():
    path = Path(__file__).resolve().parents[1] / "honesty" / "statuses.py"
    source = path.read_text(encoding="utf-8")
    assert "engine.hydroma" not in source
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names)
    assert "engine" not in imported
    assert "engine." not in source
