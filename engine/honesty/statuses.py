"""Claim-status vocabulary and the recorded-is-not-validated refinement rule.

Evidence classes and claim statuses are not interchangeable words for the same
thing. A claim carries a status; evidence carries a class. The only permitted
legacy alias is ``"validated"``, which is ambiguous and therefore must be
refined into one of the two validated terms before it is used:

* ``"VALIDATED_EXTERNAL"`` when the evidence is external (a published standard,
  an independent measurement, a third-party dataset);
* ``"REGRESSION_ANCHOR_STABLE"`` otherwise, i.e. the only evidence on hand is
  that a previously recorded result has not changed.

``BRAKES`` carries the ten safety brakes (SB-01..SB-10) and ``AR_RULES`` the
thirteen architecture rules (AR-01..AR-13) required by the ECO-NOJIN
constitution v3.1 (its sections 2 and 3). The earlier seven-term brake list
(public API signature, kernel equation, evidence chain, more than 5 main
files, weakened test, synthetic data, unit system) is SUPERSEDED by those ten
brakes; the old-to-new coverage mapping is pinned by
``engine/tests/test_honesty_contracts.py``.

Stdlib only: this module imports nothing at all.
"""

VOCABULARY = (
    "VALIDATED_EXTERNAL",
    "VALIDATED_METHOD_CONFORMANCE",
    "REGRESSION_ANCHOR_STABLE",
    "PARTIAL",
    "UNVALIDATED",
    "BLOCKED",
)

_LEGACY_ALIAS = "validated"

BRAKES = (
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

AR_RULES = (
    ("AR-01", "Separation of Concerns - the scientific core is not connected to the internet"),
    ("AR-02", "Dependency Inversion - the core depends on a Port, not the implementation"),
    ("AR-03", "Model Immutability - equations recorded in the Model Card are immutable"),
    ("AR-04", "API Stability - a public API change is a STOP"),
    ("AR-05", "Evidence-Based Decision - every Tasmimyar decision carries evidence"),
    ("AR-06", "Unit Safety - all calculations use pint"),
    ("AR-07", "AI Guardrails - AI may not change a scientific equation or parameter"),
    ("AR-08", "Fail Closed"),
    ("AR-09", "Provenance Traceability"),
    ("AR-10", "Testable Architecture - positive and negative tests for every rule"),
    ("AR-11", "no frontend/auth/payment/blockchain in the scientific core"),
    ("AR-12", "services shall not call model internals"),
    ("AR-13", "all model calls go through the Gateway"),
)

BRAKE_COUNT = len(BRAKES)
AR_COUNT = len(AR_RULES)


def _check(term: str) -> None:
    if term not in VOCABULARY and term != _LEGACY_ALIAS:
        raise ValueError(
            f"unknown status {term!r}; expected one of {VOCABULARY} "
            f"or the legacy alias {_LEGACY_ALIAS!r}"
        )


def refine_claim(claim_status: str, evidence_class: str) -> str:
    """Return the precise claim status implied by ``claim_status`` + evidence.

    ``ValueError`` is raised when either argument falls outside
    :data:`VOCABULARY` (the single allowed legacy alias, ``"validated"``, is
    accepted for ``claim_status`` only).
    """
    _check(claim_status)
    _check(evidence_class)
    if claim_status == _LEGACY_ALIAS:
        if evidence_class == "VALIDATED_EXTERNAL":
            return "VALIDATED_EXTERNAL"
        return "REGRESSION_ANCHOR_STABLE"
    return claim_status
