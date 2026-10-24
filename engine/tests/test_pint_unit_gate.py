"""Unit gate for the pint audit half of external-alignment item X-1.

These tests are offline and use plain asserts. They pin: (1) every unit string in
the live engine tree parses (or is a declared placeholder), (2) conversions round
trip, (3) incompatible unit classes are rejected, (4) the four formula-audit
defects would be caught, and (5) the alias/domain units behave as intended.
"""

import re
from pathlib import Path

import pytest

from engine.gateway.pint_audit import (
    UnknownUnitError,
    audit,
    check_compatible,
    convert,
    parse_unit,
)

UNIT_PATTERN = re.compile(r'''unit\s*[=:]\s*["']([^"']{1,25})["']''')

ENGINE_DIR = Path(__file__).resolve().parents[1]

PLACEHOLDER_TOKENS = {"unknown", "si", "none", ""}

SIX_DOMAIN_STRINGS = {
    "kg per person per year",
    "FTE",
    "fraction of TAW",
    "curve number points",
    "kg/m3",
    "fraction of consumption",
}


def _scan_engine_unit_strings() -> list[str]:
    """Replicate the plan's measurement: regex over engine/**/*.py, no caches."""
    found: list[str] = []
    for path in sorted(ENGINE_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found.extend(UNIT_PATTERN.findall(text))
    return found


def test_all_engine_unit_strings_parse():
    found = _scan_engine_unit_strings()
    assert found, "scan found no unit strings; is ENGINE_DIR correct?"
    assert SIX_DOMAIN_STRINGS <= set(found), (
        "the six domain unit strings must be present in the live tree: "
        f"missing={sorted(SIX_DOMAIN_STRINGS - set(found))}"
    )

    failures = []
    for token in sorted(set(found)):
        if token in PLACEHOLDER_TOKENS:
            assert parse_unit(token).dimensionless, token
            continue
        try:
            parse_unit(token)
        except UnknownUnitError:
            failures.append(token)

    assert failures == []


def test_conversions_round_trip():
    assert convert(1, "cm", "mm") == 10.0
    assert convert(1, "MJ/m**2/day", "W/m**2") == pytest.approx(1 / 0.0864)
    assert convert(1, "m", "cm") == 100.0
    assert convert(0, "degC", "delta_degC") == 0.0


def test_incompatible_units_are_detected():
    assert check_compatible("m", "cm") is True
    assert check_compatible("m", "kg") is False
    assert check_compatible("mm", "MJ/m**2/day") is False


def test_the_four_audit_defects_would_be_caught():
    assert check_compatible("m", "cm") is True, "soil depth (m vs cm) right pairing"
    assert check_compatible("m", "kg") is False, "soil depth wrong pairing"

    assert check_compatible("percent", "m/m") is True, "Kirpich slope (percent vs m/m) right"
    assert check_compatible("percent", "mm") is False, "Kirpich slope wrong pairing"

    assert check_compatible("MJ/m**2/day", "W/m**2") is True, "solar radiation right pairing"
    assert check_compatible("MJ/m**2/day", "mm/day") is False, "solar radiation wrong pairing"

    assert check_compatible("mm", "dimensionless") is False, "mm vs dimensionless wrong pairing"
    assert check_compatible("dimensionless", "dimensionless") is True, "mm vs dimensionless right"


def test_alias_and_domain_units():
    assert parse_unit("kg/m3").is_compatible_with(parse_unit("kg/m**3")) is True
    assert parse_unit("FTE").dimensionless is True
    assert (
        parse_unit("kg per person per year").is_compatible_with(parse_unit("kg/(person*year)"))
    ) is True


def test_audit_reports_and_tolerates_unknown():
    assert audit({"depth": "m", "rate": "mm/day"}) == []
    problems = audit({"depth": "banana", "rate": "m"})
    assert len(problems) == 1
    assert "depth" in problems[0]
    assert check_compatible("banana", "m") is False
    with pytest.raises(UnknownUnitError):
        parse_unit("banana")
