"""Acceptance thresholds for the P0 defect classes.

Why this is data and not prose
------------------------------
These numbers decide whether a defect is allowed to ship. A threshold written in
a document drifts; one written here is asserted by
``test_s14_thresholds.py`` and is a single edit when a standard changes.

Each value is a *release gate*, not a scientific tolerance. Where a scientific
tolerance exists it lives with the code that computes the quantity, as the
reference in the ``basis`` field records.
"""

from __future__ import annotations

#: A defect in this class stops a release. It is a wrong number that reaches a
#: user, or a structure that is not what its own output says it is.
P0_CLASSES: dict[str, dict[str, str]] = {
    "dimensional": {
        "statement": (
            "A reported quantity carries a unit its own name does not imply, or a "
            "magnitude that is dimensionally impossible."
        ),
        "examples": (
            "a discharge computed by dividing a volume by a dimensionless "
            "number; a water volume reported as a sediment volume"
        ),
        "release": "blocked",
    },
    "storage_shortfall": {
        "statement": (
            "A design is returned whose own stated requirement its own geometry does not meet."
        ),
        "gate": "storage_provided_m3 / storage_required_m3 >= 0.99",
        "release": "blocked",
    },
    "spillway_fit": {
        "statement": "A spillway is wider than the crest it is cut through.",
        "gate": "spillway_width_m <= top_width_m",
        "release": "blocked",
    },
    "negative_discharge": {
        "statement": "A flow model returns a negative discharge or a negative cell.",
        "gate": "outflow >= 0 everywhere, or the step is refused",
        "release": "blocked",
    },
    "mass_balance": {
        "statement": ("A water balance does not close, or reports water that did not exist."),
        "gate": "|initial + sum(R) - sum(B) - sum(P) - final| < 0.01 mm",
        "release": "blocked",
    },
    "erosion_sign": {
        "statement": "A design promises an erosion increase as a benefit.",
        "gate": "0 <= erosion_reduction_pct <= 90",
        "release": "blocked",
    },
    "region_leak": {
        "statement": (
            "A user-supplied value outside its domain is silently accepted and a "
            "value inside a different domain is returned."
        ),
        "examples": (
            "an unknown region falling back to temperate; an unknown soil texture "
            "falling back to loam"
        ),
        "release": "blocked",
    },
    "zero_efficiency": {
        "statement": (
            "An impossible efficiency returns zero, which reads as 'nothing to "
            "do' rather than 'this input is wrong'."
        ),
        "release": "blocked",
    },
    "import_collision": {
        "statement": (
            "A table name is declared twice in one registry, or two model files "
            "importing in one process raises."
        ),
        "release": "blocked",
    },
    "unreachable_capability": {
        "statement": (
            "A module the engine needs cannot be imported, or a directory is "
            "shadowed by a file of the same name."
        ),
        "release": "blocked",
    },
}

#: Anything outside P0 is recorded with its measurement and left for the
#: correction pass, which is the rule the project already follows for
#: untraceable numbers: label rather than invent.
P1_CLASSES: dict[str, str] = {
    "k_a_uncorrected": "A published-formula defect; the missing term is known and the fix is specified.",
    "unit_error_10x": "A factor-of-ten unit slip, caught by a dimensional identity.",
    "o_n_complexity": "An implementation that cannot complete at production input size.",
    "provenance": "An unsourced attribution presented as a citation.",
    "provenance_rollback": "A configuration value restored to a source default without a stated reason.",
}


def is_p0(defect_class: str) -> bool:
    return defect_class in P0_CLASSES


def gate_for(defect_class: str) -> str | None:
    entry = P0_CLASSES.get(defect_class)
    return entry.get("gate") if entry else None
