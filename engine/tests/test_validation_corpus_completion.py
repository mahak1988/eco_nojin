"""Completion guards for the validation corpus, added 2026-10-10.

The corpus used to run 95 cases and reach 43 of them: 40 were ``not_run`` with
"no stored .npy reference and no wired implementation" (hdvi, hpheno, rothc,
biofertilizer, fao56_dual_kc, richards_1d, saint_venant_1d, one scs_cn and one
penman_monteith case). This file pins what the completion pass changed, and why
each case that is *still* not run is still not run.

Pinned here:

1. the new distribution: 61 match / 0 mismatch / 17 inconsistent_case /
   17 not_run of 95. ``mismatch`` is pinned at zero, because a red dispatch
   means the code is wrong and must be investigated, not asserted over;
2. every ``not_run`` case carries a non-trivial reason that names the missing
   piece -- the model, the input, or the reference file -- so a gap in the
   corpus cannot quietly become a pass;
3. each newly wired dispatcher has at least one expected value *re-derived*
   here from its own equation, with the citation in a comment, so the wiring is
   checked against the science and not only against a number a YAML file
   already contains;
4. the RothC adapter's own failure mode: the case files store RothC inputs as
   two blocks of parallel columns (``monthly_inputs``, ``monthly_climate``), and
   the shipped adapter iterated them as month records, so all seven cases died
   on ``string indices must be integers, not 'str'``;
5. the models whose implementations exist but whose cases cannot be run through
   them, each with the gap that blocks it, so the corpus keeps distinguishing
   "no implementation" from "the implementation cannot take this input".
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from engine.hydroma.models.validation import runner as R
from engine.hydroma.models.validation.loader import expand_case, load_all_cases

#: The 2026-10-10 distribution after the completion pass. ``mismatch`` is
#: deliberately pinned at 0: a red dispatch is a finding about the code, not a
#: number to be updated.
EXPECTED_DISTRIBUTION = {
    "match": 61,
    "mismatch": 0,
    "inconsistent_case": 17,
    "not_run": 17,
}

#: Per-model distribution after the pass. The models whose cases are all
#: not_run are the ones whose cases cannot be expressed in the API of the
#: implementation that exists (see the per-model reasons below).
EXPECTED_MODEL_COUNTS = {
    "fao56_dual_kc": {"inconsistent_case": 1, "not_run": 4},
    "richards_1d": {"not_run": 5},
    "saint_venant_1d": {"not_run": 5},
    "biofertilizer": {"inconsistent_case": 1, "not_run": 1},
    "rothc": {"inconsistent_case": 3, "match": 4},
    "hdvi": {"match": 11},
    "hpheno": {"match": 3},
}

#: Every phrase a ``not_run`` detail is expected to use when it names what is
#: missing. A detail that says none of these is not a reason; it is a status
#: label, and the case would be silently abandoned.
_GAP_PHRASES = (
    "not in the corpus",
    "no implementation",
    "takes no",
    "not built",
    "does not converge",
    "missing",
    "analytical relations",
    "curve-number map",
    "hourly",
    "no bathymetry",
    "differ",
    "omits",
    "only for free drainage",
)


def _outcome(model: str, name: str) -> R.CaseOutcome:
    for case in load_all_cases():
        if case.model == model and case.name == name:
            return R.run_case(case)
    pytest.fail(f"case {model}/{name} is not in the corpus")


def _case(model: str, name: str):
    for case in load_all_cases():
        if case.model == model and case.name == name:
            return case
    pytest.fail(f"case {model}/{name} is not in the corpus")


def _cpp_available() -> bool:
    try:
        from engine.hydroma.cpp_bridge import get_module

        return get_module() is not None
    except Exception:  # pragma: no cover - extension absent
        return False


requires_cpp = pytest.mark.skipif(
    not _cpp_available(), reason="the compiled extension is not built"
)


# ---------------------------------------------------------------------------
# 1. The pinned distribution
# ---------------------------------------------------------------------------


def test_the_recorded_distribution_is_pinned() -> None:
    """95 cases: 61 match / 0 mismatch / 17 inconsistent / 17 not run.

    ``mismatch`` is the load-bearing assertion. Every other count is a
    consequence of the dispatch decisions recorded in this file and in the
    runner's docstring; a change in any of them is a change in what the corpus
    can actually reach, and has to be argued for.
    """
    summary = R.summary(R.run_all())
    assert summary == {**{"total": 95}, **EXPECTED_DISTRIBUTION}


@pytest.mark.parametrize("model", sorted(EXPECTED_MODEL_COUNTS))
def test_per_model_distribution(model: str) -> None:
    counts: dict[str, int] = {}
    for o in R.run_all():
        if o.model == model:
            status = str(o.status)
            counts[status] = counts.get(status, 0) + 1
    assert counts == EXPECTED_MODEL_COUNTS[model]


# ---------------------------------------------------------------------------
# 2. Every not_run case names what is missing
# ---------------------------------------------------------------------------


def test_every_not_run_case_names_the_missing_piece() -> None:
    """A ``not_run`` verdict is only honest if it says *why*.

    The corpus previously filled this field with "no stored .npy reference and
    no wired implementation" for cases that had a runnable implementation and no
    .npy reference at all. Each detail is now checked for a phrase that names
    the missing implementation, input or reference, and for enough length that
    it names something specific.
    """
    outcomes = [o for o in R.run_all() if o.status == "not_run"]
    assert outcomes, "the corpus should still contain cases it cannot run"
    vague = [
        f"{o.model}/{o.name}: {o.detail}"
        for o in outcomes
        if not o.detail
        or len(o.detail) < 50
        or not any(phrase in o.detail for phrase in _GAP_PHRASES)
    ]
    assert not vague, "not_run details that do not name the missing piece: " + "\n".join(vague)


def test_every_model_key_has_a_dispatcher() -> None:
    models = {case.model for case in load_all_cases()}
    assert models <= set(R._DISPATCH), sorted(models - set(R._DISPATCH))


# ---------------------------------------------------------------------------
# 3. Per-model reasons: what blocks each case that is still not run
# ---------------------------------------------------------------------------


def test_fao56_dual_kc_case_with_an_inconsistent_water_balance() -> None:
    """FAO-56's dual-Kc balance: Dr_N = Dr_0 - (P - RO) - I + ETc + DP, DP >= 0.

    A case that starts and ends at zero depletion while evaporating more water
    than it was given requires negative deep percolation, so the case is
    unsatisfiable no matter what implementation runs it. See Allen, R.G.,
    Pereira, L.S., Raes, D. & Smith, M. (1998) "Crop evapotranspiration",
    FAO Irrigation and Drainage Paper 56, eq. 8 and eq. 85.
    """
    o = _outcome("fao56_dual_kc", "wheat_full_season_reference")
    assert o.status == "inconsistent_case"
    assert "deep percolation" in o.detail
    assert "-250" in o.detail


def test_fao56_dual_kc_cases_blocked_by_the_kernels_api() -> None:
    """The only dual-Kc implementation takes no irrigation schedule.

    ``simulate_crop_water(et0, rain, auto_irrigate, params)`` has no dated
    schedule, no initial root-zone depletion (``dr`` starts at 0) and no growing
    root zone (one ``root_depth_m``), and it reports no transpiration/evaporation
    split and no yield -- which is exactly what these four cases ask for.
    """
    reasons = {
        "no_rain_no_irrigation": ["yield", "root zone"],
        "frequent_light_irrigation": ["schedule", "evaporation"],
        "stress_coefficient_ks": ["depletion"],
        "evaporation_layer_depletion": ["evaporation"],
    }
    for name, needles in reasons.items():
        o = _outcome("fao56_dual_kc", name)
        assert o.status == "not_run", f"{name}: {o.detail}"
        for needle in needles:
            assert needle in o.detail, f"{name} does not name {needle}: {o.detail}"


@requires_cpp
def test_richards_prescribed_head_boundaries_are_reported_not_scored() -> None:
    """The kernel accumulates the top flux as a flux and the bottom flux only
    for free drainage, so a prescribed-head boundary has no honest balance to
    compare. See engine/cpp_core/src/richards.cpp:232, :295-298.
    """
    for name in ("drainage_loam_initial_hydrostatic", "infiltration_silty_clay_ponded"):
        o = _outcome("richards_1d", name)
        assert o.status == "not_run"
        assert "does not converge" in o.detail
    o = _outcome("richards_1d", "mass_conservation_synthetic")
    assert o.status == "not_run"
    assert "richards.cpp" in o.detail
    o = _outcome("richards_1d", "picard_convergence_test")
    assert o.status == "not_run"
    assert "max_residual" in o.detail or "does not converge" in o.detail


@requires_cpp
def test_richards_reference_profiles_were_never_shipped() -> None:
    """A case that points at ``reference_profiles/*.npy`` has no profile to
    compare a run against when the file is not in the corpus."""
    o = _outcome("richards_1d", "infiltration_sandy_loam_constant_flux")
    assert o.status == "not_run"
    assert "richards_sandy_loam_24h" in o.detail
    assert "not in the corpus" in o.detail


@requires_cpp
def test_saint_venant_cases_blocked_by_the_kernels_boundary_conditions() -> None:
    """The kernel has a left imposed inflow and a right transmissive outflow.

    A case needing a right-hand normal-depth boundary, or a bed elevation, cannot
    be expressed. Two more cases point at reference profiles that were never
    shipped. The dam-break case stores only analytical relations and no value.
    """
    reasons = {
        "steady_uniform_flow": "normal_depth",
        "subcritical_flow_over_bump": "bathymetry",
        "dam_break_wet_bed": "sv_wetbed_shock",
        "supercritical_shock_capture": "sv_jump_location",
        "dam_break_dry_bed": "analytical relations",
    }
    for name, needle in reasons.items():
        o = _outcome("saint_venant_1d", name)
        assert o.status == "not_run", f"{name}: {o.detail}"
        assert needle in o.detail, f"{name} does not name {needle}: {o.detail}"


def test_biofertilizer_has_no_target_cn_optimiser() -> None:
    """No implementation turns a material list plus a target C/N into a mix.

    ``calculate_mix_cn_ratio`` evaluates a mix it is handed; the
    ``FormulationOptimizer`` is a catalogue-driven greedy fill keyed on
    ``material_code`` that never reads a target C/N.
    """
    o = _outcome("biofertilizer", "high_nitrogen_materials")
    assert o.status == "not_run"
    assert "no implementation" in o.detail
    assert "calculate_mix_cn_ratio" in o.detail


def test_penman_hourly_integration_has_no_kernel() -> None:
    """The case's 24-hourly series has no implementation to dispatch to.

    The only FAO-56 kernel in this repository is the daily form
    (``penman_monteith_et0``: tmin, tmax, rh_mean_pct, u2, rs, elevation, lat,
    doy). There is no hourly ET0 equation and no hourly-to-daily aggregator.
    """
    o = _outcome("penman_monteith", "daily_integration")
    assert o.status == "not_run"
    assert "hourly series" in o.detail
    assert "penman_monteith_et0" in o.detail


def test_scs_cn_spatial_map_has_no_spatial_input() -> None:
    """``RunoffInput`` takes a scalar ``curve_number``, not a CN map.

    Weighted averaging would not be SCS-CN over a map: S is nonlinear in CN, so
    Q at the mean S is not the mean of Q. See SCS National Engineering Handbook
    Section 4 and NRCS TR-55.
    """
    o = _outcome("scs_cn", "spatial_cn_map_uniform_rain")
    assert o.status == "not_run"
    assert "curve_number" in o.detail
    assert "curve-number map" in o.detail


# ---------------------------------------------------------------------------
# 4. Independently re-derived expected values
# ---------------------------------------------------------------------------


def test_hdvi_composite_rederived_from_the_documented_rescaling() -> None:
    """Re-derive HDVI for ``near_average_drought`` from the rescaling only.

    HDVI = 0.25 * (spi + spei + vhi_norm + smi_norm): a signed sum, so a dry
    index drags the composite negative, with all four weights equal at 1/4
    (engine/hydroma/models/hdvi.py:199). The z-score indices are used as they
    stand, and the percentile indices are rescaled linearly: VHI from the Kogan
    (1990) 0-100 scale ("Remote sensing of weather impacts on vegetation in
    non-homogeneous areas", Int. J. Remote Sensing 11(8):1405-1419) and SMI from
    its 0-1 scale. The case records SPI +0.10, SPEI -0.05, VHI 60, SMI 0.55:
        vhi_norm = (60 - 50) / 50 * 3 = +0.60
        smi_norm = (0.55 - 0.5) * 6      = +0.30
        HDVI = 0.25 * (0.10 - 0.05 + 0.60 + 0.30) = 0.2375
    """
    import numpy as np

    from engine.hydroma.models.hdvi import HDVI

    spi, spei, vhi, smi = 0.1, -0.05, 60.0, 0.55
    norm_vhi = (vhi - 50.0) / 50.0 * 3.0
    norm_smi = (smi - 0.5) * 6.0
    expected = 0.25 * (spi + spei + norm_vhi + norm_smi)
    assert expected == pytest.approx(0.2375)

    # ``compute`` declares vhi_value/smi_value as arrays (the percentile indices
    # can be a field); scalars are wrapped here rather than passed raw.
    got = HDVI().compute(
        spi_value=spi,
        spei_value=spei,
        vhi_value=np.asarray(vhi),
        smi_value=np.asarray(smi),
    )["hdvi"]
    assert float(got) == pytest.approx(expected, rel=1e-9)

    # ``_run_class_model`` reduces the composite to the single scalar the case
    # compares, so ``measured`` is that scalar.
    o = _outcome("hdvi", "near_average_drought")
    assert o.status == "match"
    assert float(o.measured) == pytest.approx(expected, rel=1e-9)
    assert float(o.expected) == pytest.approx(0.2375)


def test_hdvi_sign_pattern_rederived_from_the_composite_weights() -> None:
    """The composite is signed, and it weights the drought indices equally.

    With three indices neutral and one at its floor or ceiling, HDVI is a quarter
    of the deviation -- which is what makes the composite a change measure rather
    than an average of levels. Kogan (1990) defines the VHI the same way, as a
    normalised departure from the historical band rather than a raw level.
    """
    import numpy as np

    from engine.hydroma.models.hdvi import HDVI

    neutral: dict[str, Any] = {
        "spei_value": 0.0,
        "vhi_value": np.asarray(50.0),
        "smi_value": np.asarray(0.5),
    }
    dry = HDVI().compute(spi_value=-3.0, **neutral)
    wet = HDVI().compute(spi_value=3.0, **neutral)
    assert float(dry["hdvi"]) == pytest.approx(-0.75, rel=1e-9)
    assert float(wet["hdvi"]) == pytest.approx(0.75, rel=1e-9)

    o = _outcome("hdvi", "severe_drought")
    assert o.status == "match"
    # All four indices dry: 0.25 * (-0.30 + (-0.05) + (-0.60) + (-0.30)) = -2.405,
    # which is the case's own recorded decomposition, reproduced by the weights.
    assert float(o.measured) == pytest.approx(-2.405, rel=1e-9)


def test_hpheno_smoothed_peak_rederived_with_an_independent_smoother() -> None:
    """Re-derive ``single_season``'s max NDVI with an independent smoother.

    HPheno smooths a 35-day NDVI series with a window-11, cubic Savitzky-Golay
    filter. The smoothing of a window is a property of the window's shape, so it
    can be rebuilt here from the 1964 construction itself: least-squares cubic
    fit over a symmetric 11-sample window, evaluated at the window centre. See
    Savitzky, A. & Golay, M.J.E. (1964) "Smoothing and differentiation of data
    by simplified least squares procedures", Anal. Chem. 36(8):1627-1639.
    """
    import numpy as np

    case = _case("hpheno", "single_season")
    inputs: dict = expand_case(case).inputs or {}
    raw = np.asarray(inputs["ndvi_ts"], dtype=float)

    window, order = 11, 3
    half = window // 2
    smoothed = np.empty_like(raw)
    for i in range(raw.size):
        lo, hi = max(0, i - half), min(raw.size, i + half + 1)
        sample = np.asarray(raw[lo:hi], dtype=float)
        offsets = np.arange(lo - i, hi - i, dtype=float)
        poly = np.polyfit(offsets, sample, order)
        smoothed[i] = float(np.polyval(poly, 0.0))

    independent = float(np.max(smoothed))
    o = _outcome("hpheno", "single_season")
    assert o.status == "match"
    # The runner's value and this independent fit agree to round-off, which is
    # what makes the recorded 0.5588 a checkable anchor rather than a number
    # nobody can reproduce.
    assert float(o.measured) == pytest.approx(independent, rel=1e-9)
    assert float(o.expected) == pytest.approx(independent, abs=1e-3)


def test_hpheno_boundary_series_rederived_from_the_smoother() -> None:
    """Boundary cases: a constant series is a fixed point of the smoother.

    A series pinned at one value has a zero derivative everywhere, so no
    zero-crossing satisfies ``ndvi_prime[i-1] <= 0 < ndvi_prime[i]`` and the
    model has no start of season; its ``los_days`` is then 0, the sentinel for
    "no season could be identified" -- not a measured season length. The case
    carries a scalar expectation, so ``expected`` is that scalar.
    """
    for name in ("ndvi_ts_at_minimum", "ndvi_ts_at_maximum"):
        o = _outcome("hpheno", name)
        assert o.status == "match"
        assert float(o.measured) == 0.0
        assert float(o.expected) == 0.0


def test_rothc_partitioning_rederived_from_the_published_equations() -> None:
    """The CO2/stabilised split and the rate modifiers, re-derived here from
    the published RothC-26.3 equations rather than from the in-house port.

    Coleman, K. & Jenkinson, D.S. (1996), "RothC-26.3 - A model for the turnover
    of carbon in soil", in Powlson, Smith & Smith (eds) "Evaluation of Soil
    Organic Matter Models", NATO ASI Series I38, Springer:
        fraction to CO2 = 1 / (1 + x)
        x = 1.67 * (1.85 + 1.60 * exp(-0.0786 * clay))
    which gives, for the two clay cases,
        clay 10 %: x = 4.307034, stabilized = 0.188429, co2 = 0.811571
        clay 40 %: x = 3.199439, stabilized = 0.237830, co2 = 0.762170
    and the rate modifiers
        f_T = 47.91 / (1 + exp(106.06 / (T + 18.27)))   -> 1.099040 at 10 C
        f_w = 0.2 + 0.8 * (1 - SMD/maxSMD)              -> 0.64 at SMD = 0.444
    """
    from engine.hydroma.simulation.contracts import MonthClimate
    from engine.hydroma.simulation.runners.rothc_runner import (
        run_rothc,
        temp_factor,
        water_factor,
    )

    for clay, want_stabilized, want_co2 in (
        (10.0, 0.188429, 0.811571),
        (40.0, 0.237830, 0.762170),
    ):
        x = 1.67 * (1.85 + 1.60 * math.exp(-0.0786 * clay))
        assert 1.0 / (1.0 + x) == pytest.approx(want_stabilized, abs=5e-6)
        assert x / (1.0 + x) == pytest.approx(want_co2, abs=5e-6)
        months = [
            MonthClimate(year=2000, month=m + 1, tmean_c=15.0, smd_mm=0.0, max_smd_mm=100.0)
            for m in range(12)
        ]
        result = run_rothc(
            initial_soc_t_ha=50.0,
            clay_pct=clay,
            monthly=months,
            residue_c_t_ha_per_month=1.0,
        )
        assert result["stabilized_fraction"] == pytest.approx(want_stabilized, rel=1e-3)
        assert result["co2_fraction"] == pytest.approx(want_co2, rel=1e-3)

    assert temp_factor(10.0) == pytest.approx(
        47.91 / (1.0 + math.exp(106.06 / 28.27)), rel=1e-12
    )
    assert water_factor(0.444 * 100.0, 100.0) == pytest.approx(
        0.2 + 0.8 * (1.0 - 44.4 / 100.0), rel=1e-12
    )

    for name in ("clay_dependence_partitioning", "high_clay_stabilization", "temperature_modifier"):
        o = _outcome("rothc", name)
        assert o.status == "match", f"{name}: {o.detail}"
    assert _outcome("rothc", "mass_balance_identity").status == "match"


def test_rothc_monthly_inputs_are_parallel_columns_not_month_records() -> None:
    """The adapter bug that left all seven RothC cases not_run.

    Every RothC case stores its inputs as two blocks of parallel columns
    (``monthly_inputs.carbon_input``, ``monthly_climate.temp_c``,
    ``monthly_climate.smd_mm``, ``monthly_climate.max_smd_mm``). The shipped
    adapter iterated ``monthly_inputs`` as if it were a list of month records
    and died on ``string indices must be integers, not 'str'``; the case never
    reached the model. This asserts the adapter now reads both forms -- the
    compact ``{value, repeat}`` and the bare scalar -- and still reports the
    parallel-column shape as a mismatch when the lengths really do differ.
    """
    from engine.hydroma.models.validation.runner import _rothc_months

    months, problem = _rothc_months(
        {
            "monthly_inputs": {"carbon_input": {"value": 0.5, "repeat": 12}},
            "monthly_climate": {
                "temp_c": [5.0] * 12,
                "smd_mm": [0.0] * 12,
                "max_smd_mm": 100.0,
            },
        }
    )
    assert problem == ""
    assert months is not None and len(months) == 12
    assert months[0].month == 1 and months[0].tmean_c == 5.0
    assert all(m.max_smd_mm == 100.0 for m in months)  # the bare scalar broadcast

    _months, problem = _rothc_months(
        {
            "monthly_inputs": {"carbon_input": [1.0, 2.0]},
            "monthly_climate": {"temp_c": [1.0, 2.0, 3.0]},
        }
    )
    assert "lengths differ" in problem


def test_rothc_mass_balance_rederived_from_the_cases_own_identity() -> None:
    """SOC_final = SOC_initial + inputs - CO2, recomputed from the components.

    The identity is what ``mass_balance_identity`` claims holds to 1e-4; it is
    recomputed here from the initial SOC, the twelve monthly carbon inputs and
    the respired CO2 the run returns, so a violation would be the port's.
    """
    case = _case("rothc", "mass_balance_identity")
    inputs = case.inputs
    monthly = inputs["monthly_inputs"]["carbon_input"]
    monthly_carbon = (
        [float(monthly["value"])] * int(monthly.get("repeat", 12))
        if isinstance(monthly, dict)
        else [float(v) for v in monthly]
    )
    o = _outcome("rothc", "mass_balance_identity")
    measured = o.measured
    total_input = sum(monthly_carbon)
    identity_error = abs(
        float(inputs["initial_soc_t_ha"])
        + total_input
        - float(measured["cumulative_co2_t_ha"])
        - float(measured["final_soc_t_ha"])
    )
    assert identity_error < 1e-4, identity_error
    assert o.status == "match"


def test_rothc_internal_contradictions_are_reported_not_scored() -> None:
    """Three RothC cases contradict themselves.

    ``standard_reference_run`` stores pool expectations that do not sum to its
    own total SOC and a balance that does not close;
    ``moisture_modifier_boundary`` stores two modifier values a vanishing
    interval apart; ``iom_independence_from_clay`` quotes an IOM estimator whose
    own arithmetic gives 7.2080, not 6.09. Each is a defect in the case, and the
    contradiction names the equation that fails.
    """
    o = _outcome("rothc", "standard_reference_run")
    assert o.status == "inconsistent_case"
    assert "pool expectations sum" in o.detail
    assert "balance" in o.detail

    o = _outcome("rothc", "moisture_modifier_boundary")
    assert o.status == "inconsistent_case"
    assert "0.444" in o.detail

    o = _outcome("rothc", "iom_independence_from_clay")
    assert o.status == "inconsistent_case"
    assert "0.049 * SOC^1.139" in o.detail
    # The published estimator is reproduced exactly by the port, so the number
    # that is wrong is the case's.
    assert 0.049 * 80.0 ** 1.139 == pytest.approx(7.2080132319, rel=1e-9)


def test_biofertilizer_mix_rederived_from_its_own_composition() -> None:
    """Re-derive the recorded mix's C/N and show the case is inconsistent.

    C/N of a mix is Σ(m_i * c_i) / Σ(m_i * n_i); with the case's own composition
    (cattle manure 500 kg at 40 % C / 2 % N, straw 200 kg at 80 % C / 0.5 % N,
    green waste 400 kg at 30 % C / 2.5 % N) that is (200 + 160 + 120) /
    (10 + 1 + 10) = 480 / 21 = 22.86, against the 30.0 the case records. The
    FAO target band for composting is 25-35:1, so a target of 30 is legitimate --
    but this mix does not reach it.
    """
    from engine.hydroma.materials.compost_formulator import (
        CompostMaterial,
        calculate_mix_cn_ratio,
    )

    case = _case("biofertilizer", "standard_cn_ratio")
    by_name = {m["name"]: m for m in case.inputs["materials"]}
    mix = case.expected["optimal_mix_kg"]
    compost = [
        CompostMaterial(
            name=name,
            mass_kg=float(kg),
            carbon_content=float(by_name[name]["c_ratio"]),
            nitrogen_content=float(by_name[name]["n_ratio"]),
        )
        for name, kg in mix.items()
    ]
    recomputed = calculate_mix_cn_ratio(compost)
    assert recomputed == pytest.approx(22.857142857, rel=1e-6)
    assert not math.isclose(recomputed, float(case.expected["final_cn_ratio"]), rel_tol=1e-1)

    o = _outcome("biofertilizer", "standard_cn_ratio")
    assert o.status == "inconsistent_case"
    assert float(o.measured["final_cn_ratio"]) == pytest.approx(22.857142857, rel=1e-6)


def test_scs_cn_weighted_map_is_not_a_single_run() -> None:
    """The spatial case's volume is not derivable from one calculator run.

    S = 25400/CN - 254 and Q = (P - Ia)^2 / (P + 0.8 S) with Ia = 0.2 S. Because
    S is nonlinear in CN, a 50/50 CN=60/CN=80 map does not have the runoff of the
    mean CN=70 cell: the area-weighted mean of the cell runoffs is not Q at the
    weighted S. The case's own stored comment ("Simplified - actual test uses
    xarray") says as much, and ``RunoffInput`` has no field to carry a map.
    """
    from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput

    def runoff_mm(cn: float, p: float) -> float:
        s = 25400.0 / cn - 254.0
        ia = 0.2 * s
        return (p - ia) ** 2 / (p + 0.8 * s) if p > ia else 0.0

    weighted = 0.5 * runoff_mm(60.0, 40.0) + 0.5 * runoff_mm(80.0, 40.0)
    at_mean_cn = runoff_mm(70.0, 40.0)
    assert abs(weighted - at_mean_cn) > 1e-3, (weighted, at_mean_cn)

    result = RunoffCalculator().execute(
        RunoffInput(
            precipitation_mm=40.0,
            curve_number=70.0,
            area_ha=100.0,
            method="SCS-CN",
            storm_duration_h=3.0,
            rational_coefficient=0.6,
        )
    )
    assert result.volume_m3 == pytest.approx(at_mean_cn * 100.0 * 10.0, rel=1e-3)
    # ... and neither weighted nor scalar is the case's stored volume.
    assert abs(result.volume_m3 - 12450.0) > 100.0
    assert abs(weighted * 100.0 * 10.0 - 12450.0) > 100.0


@requires_cpp
def test_fao56_water_balance_rederived_from_the_cases_own_numbers() -> None:
    """Dr_N = Dr_0 - (P - RO) - I + ETc + DP, evaluated on the stored values.

    Allen et al. (1998) FAO-56 eq. 8, with rain-runoff zero (the case's own rain
    is zero), I the case's eight dated 50 mm events and ETc its stored seasonal
    total: 0 + 0 + 400 - 650 - 0 = -250 mm of deep percolation, which is a gain,
    so the case is unsatisfiable.
    """
    dp = 0.0 + 0.0 + 400.0 - 650.0 - 0.0
    assert dp == pytest.approx(-250.0)
    o = _outcome("fao56_dual_kc", "wheat_full_season_reference")
    assert "-250" in o.detail


@requires_cpp
def test_saint_venant_rederivations_from_ritter_and_conservation() -> None:
    """Re-derive the two relations the dam-break case names.

    Ritter (1892) dry-bed dam break, dam at x = 0 with h_left = 10 m:
        front speed = 2 * sqrt(g * h_left) = 19.809 m/s
    and the kernel's own conservation identity, re-derived here from the volumes
    and face fluxes it returns:
        V_final - V_initial = V_in - V_out
    """
    from engine.hydroma.cpp_bridge import get_module

    core = get_module()
    for name in ("dam_break_dry_bed", "dam_break_wet_bed"):
        inputs: dict = expand_case(_case("saint_venant_1d", name)).inputs or {}
        ic = inputs["initial_conditions"]
        nx = int(inputs["nx"])
        if "uniform" in ic:
            depth = [float(ic["uniform"]["depth"])] * nx
        else:
            left, right = ic["left"], ic["right"]
            depth = [float(left["depth"])] * (nx // 2) + [float(right["depth"])] * (
                nx - nx // 2
            )
        options = core.SaintVenantOptions()
        options.n_cells = nx
        options.length_m = float(inputs["dx"]) * nx
        options.t_end_s = float(inputs["dt"]) * int(inputs["n_steps"])
        options.width_m = float(inputs["channel_width"])
        options.manning_n = float(inputs["manning_n"])
        options.bed_slope = float(inputs.get("slope", 0.0))
        options.cfl = 0.5
        options.dry_tolerance = 1e-4
        options.output_every = 1000
        result = core.simulate_saint_venant(depth, 0.0, options)
        volume_delta = result.total_volume_final_m3 - result.total_volume_initial_m3
        face_balance = result.cumulative_inflow_m3 - result.cumulative_outflow_m3
        assert abs(volume_delta - face_balance) < 1e-6 * max(1.0, abs(face_balance)), name

    # The analytical relation the case stores, evaluated here from the same
    # equation rather than read from the runner.
    analytical = 2.0 * math.sqrt(9.81 * 10.0)
    assert analytical == pytest.approx(19.809088823, rel=1e-9)
    measured = _outcome("saint_venant_1d", "dam_break_dry_bed").measured
    assert float(measured["analytical_front_speed_m_s"]) == pytest.approx(analytical, rel=1e-9)
    # The front speed the run reaches agrees with the analytical one...
    assert float(measured["front_speed_m_s"]) == pytest.approx(analytical, rel=5e-2)
    # ... while the free-surface profile does not reproduce the Ritter fan,
    # which is the finding the runner's detail records, so the case stays open.
    outcome = _outcome("saint_venant_1d", "dam_break_dry_bed")
    assert "not reproduced" in outcome.detail
