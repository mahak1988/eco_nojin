"""Model maturity vocabulary (S0..S6): a reporting view over the registry.

The master specification fixes a maturity vocabulary on the ``models`` table --
``maturity_level TEXT CHECK(maturity_level IN ("S0","S1","S2","S3","S4","S5",
"S6"))`` (spec §4.4) -- and ECO-06's Definition of Done asks for at least one
model registered at ``S3`` or above (spec §6.6). The registry already answers
the underlying question with its structured status triple
(``implementation_status`` / ``verification_status`` / ``validation_status``,
seeded from the model cards, folded from the validation runner's records and
checked against the gateway's dispatch wiring -- see
``engine/models/registry.py``). This module only translates that triple into
the spec's vocabulary.

Mapping policy
--------------
The mapping is ADDITIVE and read-only: it reads the registry and never writes
to it. No status field is set, no card is re-parsed, and no model is promoted
by evidence this module invents. A level is the level of the strongest status
the registry already carries, so the view can understate a model but never
overstate one:

* a check that FAILED (contradicted the model) or is BLOCKED (could not be
  completed) earns no credit, on whichever dimension it appears -- the rule the
  spec states for validation, and the rule the registry itself applies when
  folding evidence ("an absent check is never reported as a passed one");
* ``STUB`` (nothing ships, or the implementation does not function) is ``S0``;
* no implementation evidence (``UNVERIFIED``, or a spec registered without any
  status) is ``S1`` -- registered, but nothing has been checked;
* implemented with a design-level verification claim, or none, and no reference
  validation, is ``S2``;
* verified against an independent reference *and* validated is ``S3`` -- the
  ECO-06 bar.

Nothing in this repository maps above ``S3``
--------------------------------------------
``S4``..``S6`` are declared in the vocabulary but are not reachable from the
registry's status dimensions today, and this module deliberately does not
invent a route to them. Reaching them needs evidence the repository does not
hold: ``S4`` an independent (third-party, independently re-run) reference-data
validation, ``S5`` a documented calibration with quantified uncertainty, and
``S6`` independent validation + calibration + reproducibility. The registry's
three dimensions carry no calibration, uncertainty or independent-rerun
evidence at all, and its ``TESTED`` / ``VALIDATED`` statuses are precisely the
evidence ``S3`` means. So :data:`MATURITY_RULES` tops out at ``S3`` and
``engine/tests/test_maturity_mapping.py`` encodes the gap as a test
(``test_no_model_above_s3_today``, spec gap G-S2/S6b): if it ever fails, the
repository gained that evidence and the mapping -- not just the test -- has to
be extended deliberately.

Because this is a reporting view, a low level is not a claim that a model is
wrong; it is a statement about what the registry can currently evidence.
"""

from __future__ import annotations

from typing import Any, NamedTuple

from engine.models.registry import ModelStatus, get_registry

__all__ = ["S_LEVELS", "maturity_of", "maturity_summary"]

#: The spec's maturity vocabulary, in order (spec §4.4 ``models.maturity_level``
#: CHECK constraint). ``S_LEVELS[S_LEVELS.index("S3"):]`` is the ECO-06
#: "``S3+``" bar from spec §6.6.
S_LEVELS: tuple[str, ...] = ("S0", "S1", "S2", "S3", "S4", "S5", "S6")

#: What each level means in the registry's own terms. ``S4``..``S6`` are the
#: spec's levels this repository cannot evidence today; see the module docstring.
S_LEVEL_MEANING: dict[str, str] = {
    "S0": "Stub or blocked: declared only, nothing ships, or a check failed or "
    "could not be completed, so no maturity is creditable.",
    "S1": "Implemented (or claimed) but unverified: no check has been run.",
    "S2": "Implemented and verified at design level, but not validated against "
    "reference data.",
    "S3": "Verified against an independent reference and validated against "
    "reference data -- the ECO-06 'S3+' bar.",
    "S4": "Independently validated: reference data produced and checked by a "
    "party independent of the implementation.",
    "S5": "Calibrated, with documented parameters and quantified uncertainty.",
    "S6": "Independently validated, calibrated, and reproducible.",
}


class MaturityRule(NamedTuple):
    """One rule of :data:`MATURITY_RULES`.

    ``implementation`` / ``verification`` / ``validation`` hold the status
    values accepted on that dimension of the registry triple; ``None`` accepts
    any value. The table is ordered and the FIRST matching rule decides, so
    every non-crediting rule (failed, blocked, stub) is listed before every
    credit-earning one: a caveat is read over a claim, never under it.
    """

    implementation: frozenset[str] | None
    verification: frozenset[str] | None
    validation: frozenset[str] | None
    level: str
    why: str


#: No rule matches an unrecognised status combination. Never guessed upward:
#: an unreadable combination is reported as earning nothing.
_UNMATCHED_LEVEL = "S0"

_STUB = frozenset({ModelStatus.STUB.value})
_UNVERIFIED = frozenset({ModelStatus.UNVERIFIED.value})
_IMPLEMENTED = frozenset({ModelStatus.IMPLEMENTED.value})
_TESTED = frozenset({ModelStatus.TESTED.value})
_VALIDATED = frozenset({ModelStatus.VALIDATED.value})
_UNVALIDATED = frozenset({ModelStatus.UNVALIDATED.value})
_FAILED_OR_BLOCKED = frozenset({ModelStatus.FAILED.value, ModelStatus.BLOCKED.value})

#: The ordered rule table: registry status triple -> maturity level.
#:
#: Rules 1-2 are the spec's "validation FAILED or BLOCKED -> S0" and
#: "implementation STUB -> S0", applied to every dimension; rule 3 is the
#: spec's "implementation UNVERIFIED (or missing) -> S1"; rule 4 is the spec's
#: "verification TESTED and validation VALIDATED -> S3"; rule 6 is the spec's
#: "implementation IMPLEMENTED, verification UNVERIFIED/IMPLEMENTED, validation
#: UNVALIDATED -> S2". Rule 5 is the one triple the spec's table does not name
#: (see its ``why``). The table's highest level is ``S3`` -- no rule above it is
#: reachable, because nothing in this repository evidences ``S4``..``S6``.
MATURITY_RULES: tuple[MaturityRule, ...] = (
    # 1. A check that FAILED contradicted the model; a check that is BLOCKED
    #    could not be completed. Neither is evidence, so neither earns credit.
    #    Verification BLOCKED is what the gateway-wiring overlay records for an
    #    id the gateway cannot dispatch (registry._overlay_gateway_wiring): the
    #    model cannot be exercised at all, so its other statuses are not
    #    creditable either.
    MaturityRule(
        None,
        None,
        _FAILED_OR_BLOCKED,
        "S0",
        "validation FAILED or BLOCKED: the check contradicted the model or "
        "could not be completed",
    ),
    MaturityRule(
        _FAILED_OR_BLOCKED,
        None,
        None,
        "S0",
        "implementation FAILED or BLOCKED: no creditable implementation",
    ),
    MaturityRule(
        None,
        _FAILED_OR_BLOCKED,
        None,
        "S0",
        "verification FAILED or BLOCKED: no independent check could be completed",
    ),
    # 2. STUB: declared but nothing ships, or the implementation does not
    #    function. Either way there is nothing to credit.
    MaturityRule(
        _STUB,
        None,
        None,
        "S0",
        "implementation STUB: declared, but no implementation ships",
    ),
    MaturityRule(
        None,
        _STUB,
        None,
        "S0",
        "verification STUB: the implementation does not function",
    ),
    # 3. UNVERIFIED implementation (or a spec registered with no status at all
    #    -- the registry defaults it to UNVERIFIED): registered, nothing checked.
    MaturityRule(
        _UNVERIFIED,
        None,
        None,
        "S1",
        "implementation UNVERIFIED: registered, no implementation evidence",
    ),
    # 4. The spec's S3 rule: verified against an independent reference AND
    #    validated. This is the canonical ECO-06 route.
    MaturityRule(
        None,
        _TESTED,
        _VALIDATED,
        "S3",
        "verification TESTED and validation VALIDATED: verified and validated "
        "against reference data",
    ),
    # 5. The residual the spec's rule table does not name: a design-level
    #    verification claim (or none) alongside a VALIDATED validation. The
    #    registry's own validation record carries reference evidence here, and
    #    demoting it to "implemented, unvalidated" would misstate that record,
    #    so it is reported at S3 -- the level its validation evidence describes.
    #    Today exactly one id lands here, and its verification reads IMPLEMENTED
    #    ("implementation matches design"), not TESTED (engine/models/cards/
    #    CANON-005_theis_solution.md section 9).
    MaturityRule(
        None,
        _IMPLEMENTED | _UNVERIFIED,
        _VALIDATED,
        "S3",
        "validation VALIDATED with a design-level verification claim: reference "
        "evidence exists, but no independent verification check",
    ),
    # 6. Everything still standing is implemented, with a design-level or
    #    independent verification, and no reference validation.
    MaturityRule(
        _IMPLEMENTED,
        _IMPLEMENTED | _TESTED | _UNVERIFIED,
        _UNVALIDATED,
        "S2",
        "implementation IMPLEMENTED, verification UNVERIFIED/IMPLEMENTED, "
        "validation UNVALIDATED: implemented, not validated",
    ),
)


def _status_triple(model_id: str) -> tuple[str, str, str]:
    """The three status values of one registered model, in rule-table order.

    Raises ``KeyError`` for an id the registry does not know, so an unknown
    model reads as an error rather than as a default level.
    """
    statuses = get_registry().status_of(model_id)
    if statuses is None:
        raise KeyError(f"no registered model with id {model_id!r}")
    return (
        statuses["implementation_status"].value,
        statuses["verification_status"].value,
        statuses["validation_status"].value,
    )


def _level_for_triple(triple: tuple[str, str, str]) -> str:
    """Apply :data:`MATURITY_RULES` to one (impl, ver, val) status triple."""
    for rule in MATURITY_RULES:
        if (
            (rule.implementation is None or triple[0] in rule.implementation)
            and (rule.verification is None or triple[1] in rule.verification)
            and (rule.validation is None or triple[2] in rule.validation)
        ):
            return rule.level
    return _UNMATCHED_LEVEL


def maturity_of(model_id: str) -> str:
    """The maturity level (``S0``..``S6``) the registry's own statuses support.

    A pure function of the registry: ``ModelRegistry.status_of(model_id)``
    gives the (implementation, verification, validation) triple and
    :data:`MATURITY_RULES` maps it to a level. The level never exceeds the
    evidence the registry already carries, so this reports maturity and never
    invents it.

    Raises ``KeyError`` for an unknown model id.
    """
    return _level_for_triple(_status_triple(model_id))


def maturity_summary() -> dict[str, Any]:
    """Every registered model bucketed by maturity level.

    Returns a plain, JSON-serialisable mapping with three keys:

    ``by_level``
        ``{level: [model_id, ...]}`` for every level in :data:`S_LEVELS`,
        including the empty ones, so a reader sees the whole ladder.
    ``counts``
        ``{level: number of models}``; the counts sum to the number of
        registered models.
    ``s3_plus``
        The model ids at ``S3`` or above -- the ECO-06 "≥ 1 model at S3+" bar
        of spec §6.6, which is met exactly when this list is non-empty.
    """
    registry = get_registry()
    by_level: dict[str, list[str]] = {level: [] for level in S_LEVELS}
    for model_id in registry.list_ids():
        by_level[maturity_of(model_id)].append(model_id)
    return {
        "by_level": by_level,
        "counts": {level: len(ids) for level, ids in by_level.items()},
        "s3_plus": [
            model_id
            for level in S_LEVELS[S_LEVELS.index("S3") :]
            for model_id in by_level[level]
        ],
    }
