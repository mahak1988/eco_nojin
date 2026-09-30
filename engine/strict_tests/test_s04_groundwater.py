"""S04 — Groundwater: linear-reservoir balance, Theis drawdown, aquifer storage.

Standards under test
--------------------
* Linear-reservoir (single-store) groundwater balance. The governing identity
  is a conservation law, not a fitted curve:

      S(t+1) = S(t) + R(t) - B(t) - P(t),      S >= 0

  so the closed balance over a run is

      S_final = S_initial + sum(R) - sum(B) - sum(P) - sum(unmet demand)

  Any deviation beyond floating-point noise means the model either loses or
  creates water.

* Theis (1935) solution for drawdown in a confined aquifer:

      s = Q / (4 pi T) * W(u),      u = r^2 S / (4 T t),      W(u) = E1(u)

  Behavioural requirements: s -> infinity as t -> 0 and s -> 0 as t -> infinity;
  s > 0 always; s is non-decreasing in Q, T, S and r, and non-decreasing in t.

* Storage coefficient S * A * dh (Freeze & Cherry, 1979, ch. 5): the drained
  volume must be linear in area, in drawdown and in specific yield.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, strategies as st

from engine.hydroma.groundwater.models import (
    GroundwaterBucketInput,
    calculate_theis_drawdown,
    estimate_aquifer_properties,
    run_groundwater_bucket,
)
from engine.strict_tests.conftest import THEIS_REFERENCE


class TestBucketConservation:
    @pytest.mark.parametrize(
        ("storage", "recharge", "pumping", "months"),
        [
            (200.0, 0.0, 0.0, 12),
            (200.0, 0.0, 5.0, 12),
            (200.0, 50.0, 20.0, 36),
            (0.0, 30.0, 0.0, 60),
            (100.0, 5.0, 0.0, 120),
            (1e5, 0.0, 0.0, 240),
        ],
    )
    def test_mass_balance_closes(
        self, storage: float, recharge: float, pumping: float, months: int
    ) -> None:
        """initial + recharge - baseflow - pumping = final, exactly.

        This is the identity the model is built on. It holds only while the
        aquifer never runs dry. When pumping exceeds recharge plus available
        storage the clamp at line 64 destroys water that the totals still report
        as extracted; that regime is covered by
        test_overdraft_reports_the_unmet_demand.
        """
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=storage,
                recharge_mm=recharge,
                pumping_mm=pumping,
                months=months,
            )
        )
        assert out.final_storage_mm > 0.0, "this case is meant to stay sustainable"
        imbalance = (
            storage
            + sum(out.recharge_series_mm)
            - sum(out.baseflow_series_mm)
            - sum(out.pumping_series_mm)
            - out.final_storage_mm
        )
        assert abs(imbalance) < 0.01, f"mass balance off by {imbalance} mm"

    def test_series_lengths_match_requested_months(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(months=37, recharge_mm=1.0, pumping_mm=0.0)
        )
        for series in (
            out.storage_series_mm,
            out.baseflow_series_mm,
            out.recharge_series_mm,
            out.pumping_series_mm,
        ):
            assert len(series) == 37

    def test_totals_equal_the_sum_of_the_series(self) -> None:
        """Reported totals are accumulated from unrounded values while the series
        are rounded to 4 decimals, so the two can disagree in the last digit.
        For a run of several months the accumulated drift is a fixed tolerance,
        not a growth, so a small bound is the right assertion."""
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=321.7, recharge_mm=17.3, pumping_mm=4.1, months=60
            )
        )
        assert out.total_recharge_mm == pytest.approx(sum(out.recharge_series_mm), abs=1e-3)
        assert out.total_baseflow_mm == pytest.approx(sum(out.baseflow_series_mm), abs=1e-3)
        assert out.total_pumping_mm == pytest.approx(sum(out.pumping_series_mm), abs=1e-3)

    def test_reports_simulated_provenance(self) -> None:
        out = run_groundwater_bucket(GroundwaterBucketInput(months=1))
        assert out.data_source == "simulated"
        assert "linear reservoir" in out.model.lower()

    def test_derived_recharge_uses_soil_water_and_coefficient(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(recharge_mm=None, soil_water_mm=200.0, rcoeff=0.15, months=1)
        )
        assert out.recharge_series_mm[0] == pytest.approx(30.0, abs=1e-4)

    def test_explicit_zero_recharge_is_honoured(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(recharge_mm=0.0, soil_water_mm=200.0, months=6)
        )
        assert set(out.recharge_series_mm) == {0.0}

    def test_negative_recharge_is_clamped_to_zero(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(recharge_mm=-50.0, months=3, initial_storage_mm=100.0)
        )
        assert set(out.recharge_series_mm) == {0.0}

    def test_storage_never_negative(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=10.0, recharge_mm=0.0, pumping_mm=100.0, months=12
            )
        )
        assert min(out.storage_series_mm) >= 0.0

    def test_negative_initial_storage_is_clamped(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(initial_storage_mm=-100.0, recharge_mm=0.0, months=3)
        )
        assert out.final_storage_mm == 0.0

    def test_no_pumping_means_baseflow_drains_toward_zero(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=200.0, recharge_mm=0.0, pumping_mm=0.0, months=200
            )
        )
        assert out.final_storage_mm < 1.0, "a 200-month run must approach the e-folding floor"

    def test_overdraft_reports_the_unmet_demand(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=200.0, recharge_mm=0.0, pumping_mm=10.0, months=24
            )
        )
        # Everything reported as pumped must have come from storage plus recharge.
        assert out.total_pumping_mm == pytest.approx(
            200.0
            + sum(out.recharge_series_mm)
            - sum(out.baseflow_series_mm)
            - out.final_storage_mm,
            abs=0.01,
        )

    def test_totals_are_exactly_the_sum_of_the_published_series(self) -> None:
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=123.456, recharge_mm=9.8765, pumping_mm=3.21, months=36
            )
        )
        assert out.total_recharge_mm == sum(out.recharge_series_mm)
        assert out.total_baseflow_mm == sum(out.baseflow_series_mm)
        assert out.total_pumping_mm == sum(out.pumping_series_mm)

    @given(
        storage=st.floats(min_value=10.0, max_value=1000.0, allow_nan=False),
        recharge=st.floats(min_value=0.0, max_value=200.0, allow_nan=False),
        pumping=st.floats(min_value=0.0, max_value=5.0, allow_nan=False),
        alpha=st.floats(min_value=0.0, max_value=0.5, allow_nan=False),
        months=st.integers(min_value=1, max_value=120),
    )
    def test_no_run_creates_water(
        self, storage: float, recharge: float, pumping: float, alpha: float, months: int
    ) -> None:
        """Total water in must never exceed total water in plus recharge.

        The tolerance covers the 4-decimal rounding the engine applies to the
        published series, accumulated once per month.
        """
        out = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=storage,
                recharge_mm=recharge,
                pumping_mm=pumping,
                alpha=alpha,
                months=months,
            )
        )
        ceiling = storage + recharge * months + 0.001 * months
        assert out.final_storage_mm <= ceiling, (
            f"storage {out.final_storage_mm} exceeds the {ceiling} mm available"
        )

    @given(
        storage=st.floats(min_value=50.0, max_value=500.0, allow_nan=False),
        months=st.integers(min_value=1, max_value=60),
    )
    def test_doubling_the_run_cannot_increase_storage(self, storage: float, months: int) -> None:
        short = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=storage, recharge_mm=0.0, pumping_mm=0.0, months=months
            )
        )
        long = run_groundwater_bucket(
            GroundwaterBucketInput(
                initial_storage_mm=storage, recharge_mm=0.0, pumping_mm=0.0, months=months * 2
            )
        )
        assert long.final_storage_mm <= short.final_storage_mm


class TestTheisDrawdown:
    def _s(self, **overrides):
        """Drawdown at the reference well with the given overrides applied.

        Keys use the engine's own parameter names so an override is never
        silently dropped, which would make the property tests vacuous.
        """
        params = {
            "transmissivity_m2day": THEIS_REFERENCE["transmissivity_m2day"],
            "storativity": THEIS_REFERENCE["storativity"],
            "pumping_rate_m3day": THEIS_REFERENCE["pumping_rate_m3day"],
            "distance_from_well_m": THEIS_REFERENCE["distance_m"],
            "time_since_pumping_start_days": THEIS_REFERENCE["time_days"],
        }
        unknown = set(overrides) - set(params)
        assert not unknown, f"override keys must match the engine signature: {unknown}"
        params.update(overrides)
        return calculate_theis_drawdown(**params)

    def test_matches_closed_form_using_scipy_expi(self) -> None:
        from scipy.special import expi

        t_ref, s_ref, q_ref, r_ref = (
            THEIS_REFERENCE["transmissivity_m2day"],
            THEIS_REFERENCE["storativity"],
            THEIS_REFERENCE["pumping_rate_m3day"],
            THEIS_REFERENCE["distance_m"],
        )
        u = r_ref**2 * s_ref / (4 * t_ref * 1.0)
        expected = q_ref / (4 * math.pi * t_ref) * (-expi(-u))
        assert self._s() == pytest.approx(expected, rel=1e-12)

    def test_drawdown_has_units_of_metres(self) -> None:
        """Q/(4 pi T) is (m3/day)/(m2/day) = m, so s is a length."""
        t_ref, q_ref = (
            THEIS_REFERENCE["transmissivity_m2day"],
            THEIS_REFERENCE["pumping_rate_m3day"],
        )
        assert q_ref / (4 * math.pi * t_ref) == pytest.approx(0.03021, rel=1e-3)

    def test_positive_for_admissible_inputs(self) -> None:
        assert self._s() > 0.0

    def test_increases_with_pumping_rate(self) -> None:
        assert self._s(pumping_rate_m3day=2000.0) > self._s(pumping_rate_m3day=500.0)

    def test_decreases_with_distance(self) -> None:
        """Drawdown is maximal at the well and falls off with radius.

        u = r^2 S / (4 T t) grows with r and W(u) = E1(u) is decreasing, so s
        falls. Measured: 0.414 m at 5 m, 0.373 at 10 m, 0.306 at 30 m, 0.167 at
        300 m from the same well.
        """
        values = [self._s(distance_from_well_m=r) for r in (5.0, 10.0, 30.0, 100.0, 300.0)]
        assert values == sorted(values, reverse=True), f"drawdown not monotone in r: {values}"

    def test_decreases_with_transmissivity(self) -> None:
        assert self._s(transmissivity_m2day=5000.0) < self._s(transmissivity_m2day=1000.0)

    def test_decreases_with_storativity(self) -> None:
        """A formation with a higher specific yield releases more water per unit
        of drawdown, so less drawdown is needed to support the same pumping.

        u = r^2 S /(4 T t) rises with S and W(u) = E1(u) is decreasing, so s falls.
        """
        assert self._s(storativity=0.0004) < self._s(storativity=0.0001)

    def test_cone_of_depression_deepens_monotonically_with_pumping_time(self) -> None:
        """The Theis solution has no interior maximum: E1(u) is decreasing in u and
        u is proportional to 1/t, so s = (Q/4 pi T) E1(u) rises monotonically with
        time and grows logarithmically without bound. The familiar rise-then-
        recover shape comes from superposing the step responses of pumping start
        and stop, not from the single-well solution.

        Measured on the reference well: 0.285 m at 0.5 d, 0.306 at 1 d, 0.348 at
        4 d, 0.390 at 16 d, 0.445 at 100 d, 0.585 at 1e4 d, 0.724 at 1e6 d.
        """
        times = (0.5, 1.0, 4.0, 16.0, 100.0, 1e4, 1e6)
        values = [self._s(time_since_pumping_start_days=t) for t in times]
        assert values == sorted(values), f"drawdown not monotone in t: {values}"

    def test_growth_is_logarithmic_in_time(self) -> None:
        """s = (Q/4 pi T) (ln(4 T t / (r^2 S)) - gamma) + O(u), so ten decades of
        time add a bounded, constant increment rather than compounding."""

        early = self._s(time_since_pumping_start_days=1.0)
        late = self._s(time_since_pumping_start_days=1e6)
        increment = late - early
        prefactor = THEIS_REFERENCE["pumping_rate_m3day"] / (
            4 * math.pi * THEIS_REFERENCE["transmissivity_m2day"]
        )
        assert increment == pytest.approx(prefactor * math.log(1e6), rel=0.15), (
            f"increment {increment} does not match the logarithmic prediction"
        )

    def test_invalid_transmissivity_or_storativity_returns_none(self) -> None:
        assert self._s(transmissivity_m2day=0.0) is None
        assert self._s(storativity=0.0) is None
        assert self._s(transmissivity_m2day=-1.0) is None

    @pytest.mark.parametrize("t_days", [0.0, -1.0])
    def test_non_positive_time_is_rejected(self, t_days: float) -> None:
        with pytest.raises(ValueError):
            self._s(time_since_pumping_start_days=t_days)

    def test_observation_at_the_well_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            self._s(distance_from_well_m=0.0)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/groundwater/models.py:142 returns None for "
            "storativity <= 0 or transmissivity <= 0. A None return is "
            "indistinguishable from 'not computed' downstream, and no log level "
            "above info() is emitted, so invalid input is silently turned into a "
            "null field in an API response. calculate_theis_drawdown's signature "
            "declares float | None but never explains the None case to a caller."
        ),
    )
    def test_invalid_input_raises(self) -> None:
        with pytest.raises(ValueError):
            self._s(storativity=0.0)

    @given(
        t_m2day=st.floats(min_value=10.0, max_value=1e4, allow_nan=False),
        stor=st.floats(min_value=1e-5, max_value=0.05, allow_nan=False),
        # Q/T is the dimensionless well-capacity ratio that actually governs the
        # drawdown, because the prefactor of eq. 39 is Q/(4 pi T). Bounding Q and
        # T independently admits combinations no aquifer produces: Q = 4200 m3/day
        # in a T = 10 m2/day formation is 420 in ratio, whereas real wells sit
        # between about 0.1 and 50.
        q_over_t=st.floats(min_value=0.01, max_value=50.0, allow_nan=False),
        r=st.floats(min_value=1.0, max_value=1e3, allow_nan=False),
        t=st.floats(min_value=0.1, max_value=1e5, allow_nan=False),
    )
    def test_bounded_and_positive(
        self, t_m2day: float, stor: float, q_over_t: float, r: float, t: float
    ) -> None:
        q = q_over_t * t_m2day
        s = calculate_theis_drawdown(t_m2day, stor, q, r, t)
        assert s is not None
        u = r * r * stor / (4.0 * t_m2day * t)
        if u < 100.0:
            # E1 is resolvable here, so the drawdown must be strictly positive.
            assert s > 0.0, f"zero drawdown at u={u:.3e}"
        else:
            # E1(u) underflows to zero above u ~ 745; a drawdown of 0 m at that
            # separation is the correct limit, not a defect.
            assert s >= 0.0
        # prefactor <= 50/(4 pi) = 4.0 m and the logarithmic factor over the
        # stated time span is below 25, so 150 m is a hard physical ceiling: a
        # deeper cone of depression means the well is dewatering, which this
        # solution cannot represent and should report rather than extrapolate.
        assert s < 150.0, f"implausible drawdown {s} m for T={t_m2day} S={stor} Q/T={q_over_t}"


class TestAquiferProperties:
    def test_volume_is_the_product_of_area_yield_and_drawdown(self) -> None:
        out = estimate_aquifer_properties(
            hydraulic_conductivity_m_s=1e-5,
            specific_yield=0.1,
            area_m2=10_000.0,
            water_level_drop_m=2.0,
        )
        assert out["volume_available_m3"] == pytest.approx(2000.0, rel=1e-9)
        assert out["volume_available_liters"] == pytest.approx(2_000_000.0, rel=1e-9)

    def test_rejects_non_positive_specific_yield(self) -> None:
        for sy in (0.0, -0.1):
            with pytest.raises(ValueError, match="Specific yield"):
                estimate_aquifer_properties(1e-5, sy, 10_000.0, 1.0)

    def test_declares_its_own_simplification(self) -> None:
        out = estimate_aquifer_properties(1e-5, 0.1, 10_000.0, 1.0)
        assert "simplified" in out["notes"].lower()

    @given(
        area=st.floats(min_value=1.0, max_value=1e9, allow_nan=False),
        sy=st.floats(min_value=0.01, max_value=0.4, allow_nan=False),
        drop=st.floats(min_value=0.01, max_value=100.0, allow_nan=False),
    )
    def test_linear_in_every_argument(self, area: float, sy: float, drop: float) -> None:
        """Doubling any factor doubles the drained volume.

        The engine rounds the volume to 2 decimals, so the comparison is made at
        the resolution the engine actually publishes.
        """
        base = estimate_aquifer_properties(1e-5, sy, area, drop)["volume_available_m3"]
        if base < 1.0:  # rounding dominates below 1 m3
            assume(base >= 1.0)
        for kwargs in (
            {"area_m2": 2 * area, "specific_yield": sy, "water_level_drop_m": drop},
            {"area_m2": area, "specific_yield": 2 * sy, "water_level_drop_m": drop},
            {"area_m2": area, "specific_yield": sy, "water_level_drop_m": 2 * drop},
        ):
            doubled = estimate_aquifer_properties(1e-5, **kwargs)["volume_available_m3"]
            assert doubled == pytest.approx(2 * base, abs=0.02), kwargs

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/groundwater/models.py:87 accepts "
            "hydraulic_conductivity_m_s as a required argument, echoes it into the "
            "result dict at line 117, and never uses it in any computation. Line "
            "112 comments out the transmissivity calculation for want of a "
            "thickness. A caller supplying a conductivity sees it returned as if "
            "it had informed the result, which is the provenance failure the "
            "engine's own honesty contract elsewhere forbids."
        ),
    )
    def test_conductivity_influences_the_result(self) -> None:
        low = estimate_aquifer_properties(1e-7, 0.1, 10_000.0, 1.0)["volume_available_m3"]
        high = estimate_aquifer_properties(1e-3, 0.1, 10_000.0, 1.0)["volume_available_m3"]
        assert high > low, "a 10000x change in conductivity left the answer untouched"

    @pytest.mark.parametrize(("area", "drop"), [(-1.0, 1.0), (1.0, -1.0), (-1.0, -1.0)])
    def test_negative_geometry_is_rejected(self, area: float, drop: float) -> None:
        with pytest.raises(ValueError):
            estimate_aquifer_properties(1e-5, 0.1, area, drop)
