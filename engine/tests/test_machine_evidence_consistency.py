"""Machine-evidence consistency: registry claims must agree with measured evidence.

The formula audit found a systemic class of over-claim: model cards and the
registry say ``validated`` where the machine evidence (corpus verdicts, model
maturity, verification status) says otherwise. This test encodes the rule and
the *currently known* violations as an explicit, shrinking set.

Rules enforced (each maps to a gap-register row):
1. A model with ``verification_status == 'blocked'`` may not claim
   ``validation_status == 'validated'`` (G-H1).
2. Every maturity level resolves through ``engine.models.maturity`` (S0..S6)
   and no model may sit above S3 without an external anchor in the corpus or a
   reference test (G-S2/G-S6).
3. Every indicator record in ``indicators/*.yaml`` must exist in the
   machine-readable evidence register
   ``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`` (programme item 7:
   machine-readable evidence, not hand-written claims).

The KNOWN_* sets below are the audit's measured exceptions. They exist so the
suite stays green *and* honest: adding a new violation fails the test, and
retiring a violation shrinks the set (the sets must never be edited upward).
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.hydroma.models.validation import runner
from engine.models import get_registry
from engine.models.maturity import maturity_of, maturity_summary

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVIDENCE_REGISTER = _REPO_ROOT / "reports" / "eco-nojin" / "FORMULA-EVIDENCE-REGISTER.json"
_INDICATORS_DIR = _REPO_ROOT / "indicators"

#: Models measured (2026-10-10) claiming ``validated`` with NO external anchor
#: in the machine-readable evidence register. Tracked in GAP-REGISTER G-H1;
#: PHASES/W6 must retire entries, never add. (The earlier "validated while
#: blocked" set was retired when the concurrent work unblocked six models and
#: demoted two; the remaining contradiction is the one this set records.)
KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR = {
    "CANON-006",
    "CANON-008",
    "CANON-010",
    # CANON-015 was retired by the concurrent work mid-audit and restored to
    # `validated` minutes later: the churn itself is the finding. Kept listed
    # until the register gains an external anchor for the watershed calculator.
    "CANON-015",
    "CANON-016",
    "CANON-017",
    "CANON-019",
    "CANON-020",
    "CANON-021",
    "CANON-022",
}

#: The models whose ``validated`` claim is backed by an external anchor. Each
#: value is an ``indicator_id`` row of ``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json``
#: carrying ``evidence_class == "VALIDATED_EXTERNAL"`` — published worked values,
#: published tabulated points, or published class edges, each of which is exactly
#: what the "method conformance" class is not.
#:
#: Phase 3 (2026-10-11) added the five soil / hydrology / crop-water models whose
#: evidence records in ``engine/validation/<MODEL_ID>.md`` re-derive the published
#: equation independently: for each of them the register *already* carried an
#: external anchor, written before the record existed, so the mapping here was
#: the only missing wiring. Growing this table with a model the register records
#: only as ``VALIDATED_METHOD_CONFORMANCE`` (or not at all) is the over-claim the
#: rule exists to catch: the register row comes first, the mapping second.
EXTERNALLY_ANCHORED_MODELS = {
    "CANON-001": "ENO_ET0_FAO56_001",
    "CANON-005": "THEIS_DRAWDOWN_USGS",
    "CANON-004": "SCS_CN_RUNOFF",
    "CANON-002": "ENO_HARGREAVES_ET0",
    "CANON-011_RAD": "FAO56_RA",
    "RUSLE_LS": "RUSLE_LS",
    # The registry spells the model id "ROTHTC" (the RothC name plus a T for the
    # temperature factor); the register row keeps the model's own spelling,
    # "ROTHC_TEMP_FACTOR". The two ids differ by one letter, so the mapping is
    # written out rather than derived -- a key-value assumption would have
    # silently produced an unanchored model instead.
    "ROTHTC_TEMP_FACTOR": "ROTHC_TEMP_FACTOR",
    "SOIL_SALINITY_CLASSIFY": "SOIL_SALINITY_CLASSES",
}


def _validation_claims(model_id: str) -> tuple[str, str]:
    spec = get_registry().get(model_id)
    return (
        str(getattr(spec, "verification_status", "")),
        str(getattr(spec, "validation_status", "")),
    )


def _validated_models() -> set[str]:
    return {
        model_id
        for model_id in get_registry().list_ids()
        if _validation_claims(model_id)[1] == "validated"
    }


def _load_register() -> dict:
    return json.loads(_EVIDENCE_REGISTER.read_text(encoding="utf-8"))


def _external_anchor_indicators() -> set[str]:
    """Indicator IDs in the register classified as VALIDATED_EXTERNAL.

    Derived from the register file — never hardcoded. A method-conformance
    entry must not appear here; only published worked values, published
    tabulated points, or published class edges qualify.
    """
    register = _load_register()
    return {
        entry["indicator_id"]
        for entry in register["entries"]
        if entry["evidence_class"] == "VALIDATED_EXTERNAL"
    }


def _unanchored_validated_models() -> set[str]:
    """Validated models whose EXTERNALLY_ANCHORED_MODELS target is not a
    VALIDATED_EXTERNAL row in the register."""
    external_classes = _external_anchor_indicators()
    return {
        model_id
        for model_id in _validated_models()
        if EXTERNALLY_ANCHORED_MODELS.get(model_id) not in external_classes
    }


def test_no_validated_claim_without_external_anchor() -> None:
    """Rule 1 — a model may claim ``validated`` only with an external anchor."""
    unanchored = _unanchored_validated_models()
    extra = unanchored - KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR
    missing = KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR - unanchored
    assert not extra, (
        "new 'validated' claims without an external anchor: "
        f"{sorted(extra)}"
    )
    assert not missing, (
        "KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR has stale entries that are "
        f"now anchored; retire them: {sorted(missing)}"
    )


def test_known_violations_shrink_over_time() -> None:
    """The exception set is a debt record: it may only shrink.

    This test enforces exact equality between the measured unanchored set
    and the KNOWN debt set. If a fix lands but KNOWN is not updated, the
    stale entries fail this test. If a new violation appears, the extra
    entries fail ``test_no_validated_claim_without_external_anchor``.
    """
    unanchored = _unanchored_validated_models()
    stale = KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR - unanchored
    assert not stale, f"retire these from KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR: {sorted(stale)}"


def test_maturity_levels_are_resolved() -> None:
    """Rule 2 — every registered model maps to a valid S-level."""
    summary = maturity_summary()
    for model_id in get_registry().list_ids():
        assert maturity_of(model_id) in {"S0", "S1", "S2", "S3", "S4", "S5", "S6"}
    assert sum(summary["counts"].values()) == len(get_registry().list_ids())
    # No model above S3 exists yet: S4-S6 require external anchors that the
    # formula-validation register records as absent (G-S2).
    for level in ("S4", "S5", "S6"):
        assert not summary["by_level"].get(level), f"found a {level} model — update the register"


def test_every_indicator_has_an_evidence_record() -> None:
    """Rule 3 — indicators/*.yaml are covered by the machine-readable register.

    ``_TEMPLATE.yaml`` is the constitution's indicator contract template
    (v3.1 §6.2 / AR-03): a placeholder, not an indicator, so it is exempt.
    """
    register = json.loads(_EVIDENCE_REGISTER.read_text(encoding="utf-8"))
    entries = {entry["indicator_id"] for entry in register["entries"]}
    missing = []
    for path in sorted(_INDICATORS_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        indicator_id = path.stem
        if indicator_id not in entries:
            missing.append(indicator_id)
    assert not missing, f"indicators missing evidence records: {missing}"


def test_evidence_register_entries_are_complete() -> None:
    """Every register entry carries the evidence class and its provenance."""
    register = json.loads(_EVIDENCE_REGISTER.read_text(encoding="utf-8"))
    required = {"evidence_class", "basis", "reference", "gap"}
    for entry in register["entries"]:
        assert {"indicator_id", *required} <= set(entry), entry.get("indicator_id")
        assert entry["evidence_class"] in {
            "VALIDATED_EXTERNAL",
            "VALIDATED_METHOD_CONFORMANCE",
            "REGRESSION_ANCHOR_STABLE",
            "PARTIAL",
            "UNVALIDATED",
            "BLOCKED",
        }
        assert entry["reference"], f"{entry['indicator_id']}: evidence needs a citation or 'none'"


def test_corpus_external_anchors_are_reported_distinctly() -> None:
    """The corpus must distinguish external anchors from recorded regression anchors.

    Pending the runner's provenance split (G-H1, W6), this test asserts the
    *currently measurable* core of the rule: the external anchors we rely on
    are exactly the ones the register names, so a silent re-classification
    cannot add external credit.
    """
    counts = runner.machine_summary()["counts"]
    assert counts["match"] >= 1  # at least one stored value reproduces
    external = _external_anchor_indicators()
    assert "ENO_ET0_FAO56_001" in external
    assert len(external) == 10, (
        "the external-anchor set changed: re-check each addition against the "
        "register and update this cap deliberately"
    )


# --------------------------------------------------------------------------- #
# Regression tests for mapping/register integrity                              #
# --------------------------------------------------------------------------- #
def test_every_externally_anchored_mapping_references_a_register_row() -> None:
    """Every EXTERNALLY_ANCHORED_MODELS value must be an indicator_id in the register.

    A mapping to a non-existent indicator_id silently lets a validated model
    read as unanchored without triggering any test assertion.
    """
    register = _load_register()
    register_ids = {entry["indicator_id"] for entry in register["entries"]}
    for model_id, indicator_id in EXTERNALLY_ANCHORED_MODELS.items():
        assert indicator_id in register_ids, (
            f"EXTERNALLY_ANCHORED_MODELS maps {model_id!r} to {indicator_id!r} "
            "but that indicator_id has no entry in the evidence register"
        )


def test_every_anchored_mapping_targets_validated_external() -> None:
    """Every EXTERNALLY_ANCHORED_MODELS value must point to a VALIDATED_EXTERNAL row.

    A mapping to a VALIDATED_METHOD_CONFORMANCE row would let a model claim
    external validation when the register only records method conformance.
    """
    _load_register()
    external_classes = _external_anchor_indicators()
    for model_id, indicator_id in EXTERNALLY_ANCHORED_MODELS.items():
        assert indicator_id in external_classes, (
            f"EXTERNALLY_ANCHORED_MODELS maps {model_id!r} to {indicator_id!r} "
            "but that register row is not VALIDATED_EXTERNAL; method conformance "
            "is not external validation"
        )


def test_method_conformance_is_not_external_validation() -> None:
    """VALIDATED_METHOD_CONFORMANCE register rows must not appear in the
    external anchor set."""
    register = _load_register()
    external = _external_anchor_indicators()
    method_conformance = {
        entry["indicator_id"]
        for entry in register["entries"]
        if entry["evidence_class"] == "VALIDATED_METHOD_CONFORMANCE"
    }
    overlap = external & method_conformance
    assert not overlap, (
        f"register rows cannot be both VALIDATED_EXTERNAL and "
        f"VALIDATED_METHOD_CONFORMANCE: {sorted(overlap)}"
    )


def test_external_anchor_count_matches_mapping_count() -> None:
    """The number of distinct indicator_ids in the register's VALIDATED_EXTERNAL
    entries that are referenced by EXTERNALLY_ANCHORED_MODELS must equal the
    number of mappings. A mapping without a register row or to the wrong class
    is a logic error, not a count gap."""
    external = _external_anchor_indicators()
    mapped_indicators = set(EXTERNALLY_ANCHORED_MODELS.values())
    anchored = external & mapped_indicators
    assert len(anchored) == len(EXTERNALLY_ANCHORED_MODELS), (
        f"only {len(anchored)}/{len(EXTERNALLY_ANCHORED_MODELS)} mappings "
        f"point to VALIDATED_EXTERNAL register rows; mismatched: "
        f"{sorted(mapped_indicators - external)}"
    )


def test_canonical_external_anchor_for_canonical_model() -> None:
    """CANON-005 maps to THEIS_DRAWDOWN_USGS which must be VALIDATED_EXTERNAL
    in the register. This pins the specific evidence behind the mapping rather
    than trusting the count alone."""
    external = _external_anchor_indicators()
    assert "THEIS_DRAWDOWN_USGS" in external, (
        "CANON-005's THEIS_DRAWDOWN_USGS mapping requires a VALIDATED_EXTERNAL "
        "register row; the engine reproduces s=1.40636669 m (USGS Python for "
        "Hydrology notebook 07a) and the reference is vendored at "
        "tests/reference_data/theis_usgs_worked_example.csv"
    )
