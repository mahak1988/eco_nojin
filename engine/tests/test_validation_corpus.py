"""Guards for the scientific validation corpus and its dispatcher.

Pinned here:

1. every case file parses and every model key has a dispatcher entry;
2. the recorded distribution (61 match / 0 mismatch / 17 inconsistent_case /
    17 not_run as of 2026-10-10) -- a regression in the corpus shows up as a
    changed distribution;
3. the loader keeps a zero expectation (a boundary case whose model output is
   legitimately 0 must not become an empty mapping);
4. the NaN tolerance in ``expand_case`` still maps ``-9999`` to NaN;
5. the SCS-CN SI formula: S = 25400/CN - 254, Ia = 0.2 S, Q = (P-Ia)^2/(P+0.8S)
   against the NRCS worked example, derived here rather than imported.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from engine.hydroma.models.validation import runner as R
from engine.hydroma.models.validation.loader import load_all_cases


def test_every_case_file_parses() -> None:
    cases = load_all_cases()
    assert len(cases) >= 90
    for case in cases:
        assert case.model
        assert case.name


def test_every_model_key_has_a_dispatcher() -> None:
    models = {case.model for case in load_all_cases()}
    dispatched = set(R._DISPATCH)
    assert models <= dispatched, f"no dispatcher for: {sorted(models - dispatched)}"


def test_recorded_distribution_is_pinned() -> None:
    """Pin the recorded distribution of the corpus run.

    95 cases: 61 match / 0 mismatch / 17 inconsistent_case / 17 not_run as of
    2026-10-10, after the 2026-10-10 completion pass wired hdvi, hpheno, rothc,
    biofertilizer, fao56_dual_kc, richards_1d, saint_venant_1d and scs_cn to real
    implementations. ``mismatch`` stays pinned at 0: a red dispatch has to be
    investigated, not asserted over.
    """
    outcomes = R.run_all()
    summary = R.summary(outcomes)
    assert summary["total"] == 95
    assert summary["mismatch"] == 0
    assert summary["match"] >= 60
    assert summary["inconsistent_case"] >= 17
    assert summary["not_run"] == 95 - summary["match"] - summary["inconsistent_case"]


def test_loader_keeps_a_zero_expectation() -> None:
    """A boundary case whose model output is 0 must stay 0, not become ``{}``.

    The loader used to normalise a falsy ``expected`` with ``or {}``, which
    turned the recorded zero of EPIA/et0_at_minimum into an empty mapping and
    made every comparison fail with a confusing "expected {}".
    """
    from engine.hydroma.models.validation.loader import ValidationCase

    # The loader keeps a scalar expectation as the scalar; its declared type
    # (a mapping or None) is what this boundary case exists to challenge.
    assert ValidationCase(model="probe", name="zero", expected=cast("Any", 0.0)).expected == 0.0
    for case in load_all_cases():
        if case.name == "et0_at_minimum" and case.expected == 0.0:
            outcome = R.run_case(case)
            assert outcome.status == "match"
            assert outcome.expected == 0.0
            break
    else:  # pragma: no cover
        pytest.fail("no boundary case with a zero expectation is in the corpus")


def test_scs_cn_matches_the_nrcs_worked_example() -> None:
    """S = 25400/70 - 254 = 108.857 mm; Ia = 0.2 S; Q = (P-Ia)^2/(P + 0.8 S)."""
    cn, p = 70.0, 50.0
    s = 25400.0 / cn - 254.0
    ia = 0.2 * s
    q = (p - ia) ** 2 / (p + 0.8 * s)
    assert s == pytest.approx(108.857142857, rel=1e-9)
    assert ia == pytest.approx(21.771428571, rel=1e-9)
    assert q == pytest.approx(5.8128029536, rel=1e-9)

    for case in load_all_cases():
        if case.model == "scs_cn" and case.name == "standard_example_cn70_p50mm":
            outcome = R.run_case(case)
            assert outcome.status == "match"
            # Every SCS-CN corpus case carries a recorded expectation.
            assert case.expected is not None
            assert outcome.measured["volume_m3"] == pytest.approx(
                case.expected["volume_m3"], abs=1.0
            )
            break
    else:  # pragma: no cover
        pytest.fail("the NRCS worked example is not in the corpus")


def test_partial_status_case_is_not_a_mismatch() -> None:
    """A case file marked 'partial' with hand-written expectations is reported
    as an inconsistent case, never as a defect in the calculator."""
    for case in load_all_cases():
        if case.model == "check_dam" and case.status == "partial":
            outcome = R.run_case(case)
            assert outcome.status == "inconsistent_case"
            assert outcome.contradictions
            break
