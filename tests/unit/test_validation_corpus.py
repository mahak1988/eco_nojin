"""Tests for the validation corpus loader and runner.

The corpus was written with citations and never connected to anything. These
tests do two jobs:

* make the corpus loadable, so it can no longer rot silently;
* pin the finding that several stored expectations are internally inconsistent,
  so nobody "fixes" a correct implementation to match an unsatisfiable case.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from engine.hydroma.models import validation as v

# ------------------------------------------------------------------ loading


def test_corpus_loads():
    """Every YAML in the corpus parses, and each case file yields at least one case.

    The count was pinned at 10 for months, which meant every file added since --
    the six model cases for the EWSI/EPIA/ECSI/ESRI/HLHS/HPheno/HYRUE/HDVI
    indices -- arrived with a red test that had to be edited to match. A
    regression that silently drops a case file is now caught; adding one is not.
    """
    s = v.corpus_summary()

    files = sorted((Path(v.__file__).parent / "test_cases").glob("*.yaml"))
    assert s["case_files"] == len(files), (s, [f.name for f in files])
    assert s["case_files"] >= 17, s
    assert s["cases"] >= 25, s
    assert s["references"] == 18, s


def test_every_case_has_a_model_name_and_inputs():
    for case in v.load_all_cases():
        assert case.model, case
        assert case.name, case
        assert isinstance(case.inputs, dict), case
        assert case.inputs, f"{case.name} has no inputs"


def test_every_case_file_carries_a_citation():
    """The corpus is only worth loading because it is cited."""
    for case in v.load_all_cases():
        assert case.reference.strip(), f"{case.model}/{case.name} has no reference"


def test_references_load_and_are_small_arrays():
    for name in v.available_references():
        arr = v.load_reference(name)
        assert arr.ndim == 1, name
        assert np.all(np.isfinite(arr)), name


def test_reference_metadata_reports_real_shapes():
    """The directory is called reference_profiles but these are scalars.

    The metadata exists so a caller is not misled by the directory name.
    """
    meta = v.reference_metadata()
    scalar = [n for n, m in meta.items() if m["size"] == 1]

    assert "penman_monteith_fao56_ch3" in scalar
    assert meta["penman_monteith_fao56_ch3"]["shape"] == (1,)


def test_unknown_reference_raises_with_the_available_names():
    with pytest.raises(KeyError, match="have"):
        v.load_reference("not_a_real_reference")


def test_load_cases_filters_by_model():
    cases = v.load_cases("penman_monteith")

    assert cases
    assert all(c.model == "penman_monteith" for c in cases)


# ------------------------------------------------------------------- running


def test_runner_classifies_every_case():
    outcomes = v.run_all()

    assert len(outcomes) == len(v.load_all_cases())
    allowed = {"match", "mismatch", "inconsistent_case", "not_run"}
    assert {o.status for o in outcomes} <= allowed


def test_summary_counts_add_up():
    counts = v.summary()

    assert (
        counts["match"] + counts["mismatch"] + counts["inconsistent_case"] + counts["not_run"]
        == counts["total"]
    )


def test_report_is_renderable():
    text = v.report()

    assert "validation corpus" in text
    assert str(v.summary()["total"]) in text


# ------------------------------------------- the internally inconsistent cases


def test_fao56_case_is_flagged_inconsistent_not_mismatched():
    """The pinned finding: the case contradicts itself, so the code is not wrong.

    Two independent contradictions, both verified numerically:

    * the case supplies rh_min and rh_max, so FAO-56 eq. 12 applies the
      ``[e0(Tmin)RHmax + e0(Tmax)RHmin]/200`` route (1.3973 kPa), which the native
      kernel cannot express because it takes a single ``rh_mean_pct`` and computes
      1.6317 kPa instead;
    * the case expects ``Rn`` equal to the measured ``Rs`` to the digit, which
      requires ``Rnl = 0`` and so cannot hold for a real atmosphere.
    """
    case = next(c for c in v.load_cases("penman_monteith") if c.name == "fao56_example_chapter3")
    outcome = v.run_case(case)

    assert outcome.status == "inconsistent_case", (
        f"expected the case to be flagged inconsistent, got {outcome.status}: {outcome.detail}"
    )
    assert len(outcome.contradictions) >= 2, outcome.contradictions
    assert any("ea" in c for c in outcome.contradictions)
    assert any("Rn" in c for c in outcome.contradictions)


def test_the_rn_contradiction_is_arithmetic_not_judgement():
    """Rn == Rs exactly implies Rnl == 0, independent of any implementation."""
    case = next(c for c in v.load_cases("penman_monteith") if c.name == "fao56_example_chapter3")

    rn_expected = float(case.expected["rn_mj_m2_day"])
    rs = float(case.inputs["solar_radiation"])

    assert math.isclose(rn_expected, rs, rel_tol=1e-6)
    assert rn_expected == rs, "the stored Rn is exactly the stored Rs"


def test_the_ea_routes_really_differ_for_this_case():
    """Pins the numbers quoted in the contradiction message."""
    tmin, tmax, rh_min, rh_max = 13.5, 28.5, 40.0, 80.0

    route_b = v.runner._fao56_ea_from_min_max(tmin, tmax, rh_min, rh_max)
    route_a = v.runner._fao56_ea_from_mean(tmin, tmax, (rh_min + rh_max) / 2.0)

    assert math.isclose(route_b, 1.3973, rel_tol=5e-3), route_b
    assert not math.isclose(route_b, route_a, rel_tol=1e-2), (route_b, route_a)


def test_the_native_kernel_agrees_with_an_independent_hand_calculation():
    """The C++ matches the textbook equations for the signature it takes.

    This is what makes the case, not the code, the thing in question: Ra and Rn
    computed here and by the kernel agree to zero, so the disagreement is about
    the case's inputs and expectations, not about the arithmetic.
    """
    from engine.hydroma.cpp_bridge import get_module

    core = get_module()
    if core is None:
        pytest.skip("C++ extension is not built")

    tmin, tmax, rh_mean = 13.5, 28.5, 60.0
    _u2, rs, z, lat, doy = 2.0, 15.2, 100.0, 40.0, 172

    phi = np.deg2rad(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    decl = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(decl))
    ra = (
        (24 * 60 / np.pi)
        * 0.0820
        * dr
        * (ws * np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.sin(ws))
    )
    es = (v.runner._svp(tmax) + v.runner._svp(tmin)) / 2.0
    ea = es * rh_mean / 100.0
    rso = (0.75 + 2e-5 * z) * ra
    rnl = (
        4.903e-9
        * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4)
        / 2
        * (0.34 - 0.14 * np.sqrt(ea))
        * (1.35 * np.clip(rs / rso, 0.3, 1.0) - 0.35)
    )
    rn = (1 - 0.23) * rs - rnl

    assert float(core.extraterrestrial_radiation(lat, doy)) == pytest.approx(ra, abs=1e-9)
    assert float(core.fao56_net_radiation(tmin, tmax, rh_mean, rs, z, lat, doy)) == pytest.approx(
        rn, abs=1e-9
    )


# ------------------------------------------- cases with no wired implementation


def test_cases_without_a_wired_model_are_reported_not_silently_passed():
    """A missing implementation must not read as a pass."""
    outcomes = {f"{o.model}/{o.name}": o for o in v.run_all()}

    unwired = [k for k, o in outcomes.items() if o.status == "not_run"]
    assert unwired, "expected the corpus to have models with no wired implementation"
    for key in unwired:
        assert outcomes[key].detail, f"{key} is not_run with no reason given"


# ------------------------------------------------------------- hargreaves wired


def test_hargreaves_matches_its_published_worked_example():
    """One Hargreaves case validates exactly against FAO-56 eq. 21 and 52.

    This is the corpus doing its job. An earlier revision of the runner omitted
    the 0.408 radiation-to-evaporation factor from eq. 52 and reported all four
    cases as 2.45x mismatches; the stored expectation was right and the runner
    was wrong. Loading the corpus is what surfaced it.
    """
    outcome = v.run_case(
        next(v.expand_case(c) for c in v.load_cases("hargreaves") if c.name == "standard_example")
    )

    assert outcome.status == "match", f"{outcome.status}: {outcome.detail}"
    assert outcome.measured == pytest.approx(5.37, rel=1e-2)


def test_unreproducible_hargreaves_expectations_are_flagged_not_mismatched():
    """The other three cannot be derived from eq. 52 with eq. 21's Ra.

    Backing the Ra out of eq. 52 gives -3.7%, -5.2% and -11.5% against the
    recomputed Ra. Those are not a common factor, so no single Ra convention
    reproduces the stored values, and calling them mismatches would invite
    breaking a correct implementation to match an unsatisfiable expectation.
    """
    outcomes = {
        o.name: o for o in (v.run_case(v.expand_case(c)) for c in v.load_cases("hargreaves"))
    }

    flagged = {n: o for n, o in outcomes.items() if o.status == "inconsistent_case"}
    assert set(flagged) == {
        "tropical_conditions",
        "high_elevation",
        "extreme_temperature_range",
    }, sorted(outcomes)

    deviations = []
    for name, o in flagged.items():
        assert o.contradictions, f"{name} flagged without a stated contradiction"
        assert "eq. 21" in o.detail
        deviations.append(float(o.detail.split("(")[1].split("%")[0]))

    # Not a common factor, which is what rules out one systematic wrong convention.
    assert max(deviations) - min(deviations) > 5.0, (
        f"deviations are near-identical ({deviations}), which would point at a "
        f"single wrong Ra convention rather than an inconsistent expectation"
    )


def test_corpus_has_no_unattributed_mismatches():
    """Every disagreement is either a code failure or a bad case, and says which.

    The point of separating 'mismatch' from 'inconsistent_case' is that no red
    result can be dismissed without knowing which side is wrong.
    """
    outcomes = v.run_all()
    stray = [f"{o.model}/{o.name}" for o in outcomes if o.status == "mismatch"]

    assert not stray, f"unattributed mismatches present: {stray}"


def test_corpus_claimed_status_is_reported_alongside_the_verdicts():
    """35 cases are labelled 'validated' in the corpus. The verdicts are separate.

    The claim is surfaced so the gap between it and what actually runs is
    visible, rather than the claim being taken at face value.
    """
    claimed = v.corpus_summary()["claimed_status"]

    assert claimed.get("validated", 0) > 0
    verdicts = v.summary()
    assert verdicts["not_run"] + verdicts["inconsistent_case"] > 0
    # Nothing is currently proven by the corpus beyond the single Hargreaves case.
    assert verdicts["match"] < claimed["validated"]
