"""Tests for provenance handling in the formula registry.

A formula does not need a published standard to be recorded. Most deployed
science is original: a new index, a new composite, published factors reassembled
for a purpose they were not written for. The registry previously made that
impossible -- a ``verified`` record required ``reference_values``, and those were
defined as published values -- so a novel contribution could not be registered at
all, and the honest response to that was to leave it undocumented.

The fix separates two questions that were conflated:

* ``provenance`` -- where the equation comes from: ``standard``, ``novel`` or
  ``composite``.
* ``status`` -- what has been checked.
"""

from __future__ import annotations

import pytest

from engine.hydroma.formulas import (
    FormulaRecord,
    all_records,
    composite,
    get,
    novel,
    research_definition,
    summary,
)
from engine.hydroma.formulas.records import Provenance


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Restore the global registry: this module registers records to exercise rules."""
    from engine.hydroma.formulas import registry

    saved = dict(registry._REGISTRY)
    try:
        yield
    finally:
        registry._REGISTRY.clear()
        registry._REGISTRY.update(saved)


def _record(**overrides) -> FormulaRecord:
    base = {
        "quantity": "test_quantity",
        "canonical": "somewhere.py",
        "literature_ref": "something",
        "units": "dimensionless",
        "domain": "scalar",
        "backend_priority": ("python",),
        "parity_tests": ("a_test",),
    }
    base.update(overrides)
    return FormulaRecord(**base)


# ----------------------------------------------------------------- the fields


def test_provenance_is_a_separate_axis_from_status():
    s = summary()

    assert s["by_standard"] + s["by_novel"] + s["by_composite"] == s["total"], (
        "every record must declare where it comes from"
    )
    assert s["verified"] + s["divergent"] + s["stub"] == s["total"], (
        "provenance and status are independent axes and must both be complete"
    )


def test_every_record_declares_a_provenance():
    for quantity, record in all_records().items():
        assert record.provenance in ("standard", "novel", "composite"), quantity


# ------------------------------------------------- a novel formula can exist


def test_a_novel_formula_can_be_verified_without_a_published_standard():
    """The case that was structurally impossible before.

    A novel contribution is not held back waiting for a standard that may never
    arrive. It is verified against its own research definition.
    """
    record = _record(
        quantity="an_original_index",
        provenance="novel",
        research_definition="engine/hydroma/formulas/research/__init__.py::an_original_index",
        reference_values="anchor cases defined in the research definition",
        status="verified",
    )

    assert record.is_verified
    assert record.provenance == "novel"


def test_a_novel_formula_without_a_definition_is_refused():
    """A contribution nobody can review or reproduce is not a contribution."""
    with pytest.raises(ValueError, match="research_definition"):
        _record(quantity="undefined_novel", provenance="novel", status="verified")


def test_a_novel_formula_still_needs_an_anchor():
    """Novelty removes the external anchor, not the need for one.

    A novel formula is checked against the cases its own research definition
    declares, which is what ``reference_values`` means for it. It is not exempt.
    """
    with pytest.raises(ValueError, match="anchor in reference_values"):
        _record(
            quantity="unanchored_novel",
            provenance="novel",
            research_definition="engine/hydroma/formulas/research/__init__.py::x",
            status="verified",
        )


def test_a_novel_formula_may_sit_as_a_stub_without_an_anchor():
    """A newly drafted contribution is allowed in before it is anchored."""
    record = _record(
        quantity="draft_novel",
        provenance="novel",
        research_definition="engine/hydroma/formulas/research/__init__.py::x",
        stub_reason="Drafted but not yet anchored against any reference case.",
    )

    assert record.status == "stub"


def test_parity_tests_are_still_required_for_a_novel_formula():
    """Novelty lowers the external bar, not the internal one."""
    with pytest.raises(ValueError, match="parity_tests"):
        _record(
            quantity="untested_novel",
            provenance="novel",
            parity_tests=(),
            research_definition="engine/hydroma/formulas/research/__init__.py::x",
        )


# -------------------------------------------------------- the research store


def test_every_novel_or_composite_record_names_a_definition_that_exists():
    from engine.hydroma.formulas.research import DEFINITIONS

    for quantity, record in all_records().items():
        if record.provenance not in ("novel", "composite"):
            continue
        assert record.research_definition, (
            f"{quantity} is {record.provenance} but names no research definition"
        )
        target = record.research_definition.split("::")[-1]
        assert target in DEFINITIONS, (
            f"{quantity} points at research definition {target!r}, which does not exist"
        )


def test_a_research_definition_states_its_domain_and_rationale():
    """A definition is only useful if it says what the formula is for and where
    it stops being true."""
    from engine.hydroma.formulas.research import DEFINITIONS

    for name, text in DEFINITIONS.items():
        lowered = text.lower()
        assert len(text) > 400, f"{name}: definition is too short to be a definition"
        assert "what it computes" in lowered, f"{name}: no statement of what it computes"
        assert "domain of validity" in lowered, f"{name}: no domain of validity"
        assert "provenance:" in lowered, f"{name}: does not declare its provenance"
        # Every definition must account for its coefficients: either as sourced
        # or explicitly as unsourced. A definition that says neither is the
        # situation the registry exists to prevent.
        assert "sourced" in lowered or "anchor" in lowered, (
            f"{name}: does not account for where its coefficients come from"
        )


def test_research_definition_accessor_resolves_by_quantity():
    text = research_definition("nojin_biofertilizer_suitability")

    assert text
    assert "unsuitable" in text
    assert "unrated" in text


def test_unknown_quantity_has_no_definition():
    assert research_definition("not_a_formula") is None


# ------------------------------------------------- the existing catalogue


def test_the_nojin_suitability_is_labelled_composite_not_standard():
    """Its parts are published; the product is ours."""
    record = get("nojin_biofertilizer_suitability")

    assert record is not None
    assert record.provenance == "composite"
    assert record.is_verified
    assert "nojin_biofertilizer_suitability" in composite()


def test_standard_formulas_are_not_demanding_research_definitions():
    """ISO, FAO and RothC records are ordinary standards."""
    for quantity, record in all_records().items():
        if record.provenance == "standard":
            assert record.research_definition is None, quantity


def test_registry_exposes_the_origins_queries():
    assert isinstance(novel(), dict)
    assert isinstance(composite(), dict)
    assert set(Provenance.__args__) == {"standard", "novel", "composite"}


# ------------------------------------------- the project's own contributions


def test_the_composites_are_registered_as_contributions():
    """The gap the survey found: the instrument existed and was never pointed at
    the house constructions. Each of these is a weighted product over a
    newly-chosen factor set, which is where a contribution lives."""
    expected = {
        "wbi_water_bankruptcy",
        "hlhs_landscape_health",
        "esri_salinity_risk",
        "hdvi_drought_vulnerability",
        "ewsi_water_stress",
        "multi_stress_amplification",
        "hyrue_stress_coupling",
        "core_soil_health_score",
        "nojin_biofertilizer_suitability",
    }
    registered = set(novel()) | set(composite())

    assert expected <= registered, f"not registered as contributions: {expected - registered}"


def test_no_contribution_is_presented_as_a_plain_standard():
    """A composite must not be filed under 'standard' and thereby imply a
    published source for its weights."""
    for quantity in set(novel()) | set(composite()):
        assert all_records()[quantity].provenance != "standard", quantity


def test_a_contribution_with_unsourced_coefficients_is_stub_not_verified():
    """Honesty in both directions.

    A contribution is not penalised for lacking a published standard, but it is
    not promoted to verified either while its *equation* has no derivation. A
    definition that says which part is verified and which is not is the escape
    hatch, and it has to be explicit: a record may be verified for the part it
    proves and nothing more.
    """

    for quantity, record in {**novel(), **composite()}.items():
        if "UNSOURCED" not in (research_definition(quantity) or ""):
            continue
        # Only a record that CLAIMS verification has to say what it verifies. A
        # stub asserts nothing and is not overstating anything.
        if record.status != "verified":
            continue
        claims = _verified_claims(research_definition(quantity) or "")
        assert claims, (
            f"{quantity}: a verified record must state in its research definition "
            f"exactly what has been verified and what has not"
        )


def test_every_stub_says_why_it_is_a_stub():
    """A stub that does not say why is an unexamined gap, not an honest one.

    The reason is a required field rather than prose to be inferred, so this cannot
    rot. The schema enforces it too: ``FormulaRecord.__post_init__`` refuses a
    stub with an empty ``stub_reason``.
    """
    from engine.hydroma.formulas import all_records

    stubs = {q: r for q, r in all_records().items() if r.status == "stub"}
    assert stubs, "expected the catalogue to contain stubs while gaps remain"

    for quantity, record in stubs.items():
        assert record.stub_reason.strip(), f"{quantity} is a stub with no stated reason"
        assert len(record.stub_reason) > 30, (
            f"{quantity} gives a reason too short to be one: {record.stub_reason!r}"
        )


def test_the_schema_refuses_a_stub_with_no_reason():
    from engine.hydroma.formulas import FormulaRecord

    with pytest.raises(ValueError, match="stub_reason"):
        FormulaRecord(
            quantity="quiet_stub",
            canonical="somewhere.py",
            literature_ref="none",
            units="dimensionless",
            domain="scalar",
            backend_priority=("python",),
            parity_tests=("a_test",),
            status="stub",
        )


def test_a_duplicate_registration_needs_an_explicit_replace():
    """The rule exists so a second implementation cannot quietly become canonical."""
    from engine.hydroma.formulas import DuplicateFormulaError, register

    first = _record(
        quantity="some_index",
        canonical="one.py",
        literature_ref="none",
        units="dimensionless",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("a_test",),
        status="verified",
        reference_values="an anchor",
    )
    register(first, replace=True)

    second = _record(
        quantity="some_index",
        canonical="two.py",
        literature_ref="none",
        units="dimensionless",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("a_test",),
        status="verified",
        reference_values="an anchor",
    )
    with pytest.raises(DuplicateFormulaError):
        register(second)


def _verified_claims(text: str) -> list[str]:
    """The lines a definition asserts as verified.

    A contribution may be verified for a narrower thing than its whole
    construction -- a filter's correctness, say, when its default parameters are
    still unsourced. What it may not do is be marked verified while asserting
    nothing, because then the word carries no claim at all.
    """
    out: list[str] = []
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## what is verified"):
            collecting = True
            continue
        if collecting:
            if stripped.startswith("#"):
                continue
            if not stripped:
                continue
            if stripped.startswith("##"):
                break
            out.append(stripped)
    return out


def test_the_hpheno_record_narrows_its_own_verified_claim():
    """The filter is proven; the default window is not. Both must be stated."""
    from engine.hydroma.formulas import get

    record = get("hpheno_phenology")
    claims = _verified_claims(research_definition("hpheno_phenology") or "")

    assert record.is_verified
    assert claims, "a verified contribution must name what it actually proves"
    joined = " ".join(claims).lower()
    assert "savitzky" in joined or "filter" in joined, (
        "the verified claim should be about the filter, since that is what the "
        f"tests prove; got: {joined}"
    )


def test_a_contribution_never_claims_an_external_validation_it_lacks():
    """Two modules assert country-level accuracy with no artefact in the tree."""
    unsupported = ("20/25", "22/25", "80.0% accuracy", "88.0%")
    for quantity, record in {**novel(), **composite()}.items():
        text = research_definition(quantity) or ""
        if not any(token in text for token in unsupported):
            continue
        # The definition must say the artefact is absent, and the record must
        # carry the disclaimer too so it cannot be missed by someone reading only
        # the catalogue.
        assert "no country table" in text.lower(), quantity
        assert "no country table" in record.notes.lower(), quantity
        assert record.status == "stub", (
            f"{quantity} quotes an accuracy figure it cannot substantiate but is "
            f"marked {record.status}"
        )
