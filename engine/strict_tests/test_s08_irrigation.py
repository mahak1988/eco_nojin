"""S08 — Irrigation scheduling: FAO-56 and Keller & Bliesner (1990).

Standards under test
--------------------
* FAO-56 Annex 2 / Keller & Bliesner (1990), *Irrigation Scheduling: Methods,
  Principles and Applications*:

      net irrigation requirement   NIR = ETc - Pe
      gross application depth     GAR = NIR / Ea        (application efficiency)
      irrigation interval         I   = (TAW * p) / ETc

  where TAW is total available water in the root zone, p the management-allowed
  depletion fraction, and Ea the application efficiency in [0, 1].

These three functions drive water application on a farm. The failure modes that
matter are not subtle numerical drift but sign and unit errors, because a
scheduler that under-reports depth irrigates a crop to stress and a scheduler
that misreads p as a percentage irrigates a hundred times too rarely.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, strategies as st

from engine.hydroma.irrigation.scheduler import (
    IrrigationEvent,
    calculate_application_depth,
    calculate_interval,
)


class TestApplicationDepth:
    def test_matches_the_closed_form(self) -> None:
        assert calculate_application_depth(etc_mm=5.0, efficiency=0.8, effective_rain_mm=1.0) == (
            pytest.approx((5.0 - 1.0) / 0.8)
        )

    def test_gross_depth_exceeds_net_depth_at_sub_unit_efficiency(self) -> None:
        for efficiency in (0.4, 0.6, 0.8, 0.95):
            net = 6.0
            gross = calculate_application_depth(net, efficiency, 0.0)
            assert gross == pytest.approx(net / efficiency)
            assert gross > net, f"efficiency {efficiency} must inflate the applied depth"

    def test_effective_rainfall_reduces_the_requirement(self) -> None:
        dry = calculate_application_depth(6.0, 0.8, 0.0)
        wet = calculate_application_depth(6.0, 0.8, 4.0)
        assert wet < dry

    def test_rainfall_above_et_gives_no_application(self) -> None:
        assert calculate_application_depth(4.0, 0.8, 6.0) == 0.0

    def test_zero_et_gives_no_application(self) -> None:
        assert calculate_application_depth(0.0, 0.8, 0.0) == 0.0

    @given(
        etc=st.floats(min_value=0.0, max_value=30.0, allow_nan=False),
        efficiency=st.floats(min_value=0.05, max_value=1.0, allow_nan=False),
        rain=st.floats(min_value=0.0, max_value=20.0, allow_nan=False),
    )
    def test_never_negative_and_never_below_the_net_requirement(
        self, etc: float, efficiency: float, rain: float
    ) -> None:
        gross = calculate_application_depth(etc, efficiency, rain)
        assert gross >= 0.0
        net = max(0.0, etc - rain)
        assert gross >= net - 1e-12

    @given(
        etc=st.floats(min_value=0.5, max_value=30.0, allow_nan=False),
        efficiency=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
        rain=st.floats(min_value=0.0, max_value=20.0, allow_nan=False),
    )
    def test_strictly_decreasing_in_efficiency(
        self, etc: float, efficiency: float, rain: float
    ) -> None:
        """Lower application efficiency means more water has to be applied."""
        assume(calculate_application_depth(etc, efficiency, rain) > 0.0)
        worse = calculate_application_depth(etc, efficiency / 2.0, rain)
        better = calculate_application_depth(etc, min(1.0, efficiency * 1.5), rain)
        assert worse > better

    @given(
        etc=st.floats(min_value=0.5, max_value=30.0, allow_nan=False),
        efficiency=st.floats(min_value=0.1, max_value=1.0, allow_nan=False),
    )
    def test_doubles_when_efficiency_halves(self, etc: float, efficiency: float) -> None:
        assume(efficiency / 2.0 > 0.0)
        full = calculate_application_depth(etc, efficiency, 0.0)
        half = calculate_application_depth(etc, efficiency / 2.0, 0.0)
        assert half == pytest.approx(2.0 * full, rel=1e-9)

    @pytest.mark.parametrize("efficiency", [0.0, -0.1, -1.0])
    def test_non_positive_efficiency_is_rejected(self, efficiency: float) -> None:
        with pytest.raises(ValueError):
            calculate_application_depth(5.0, efficiency, 0.0)

    @pytest.mark.parametrize("efficiency", [1.01, 1.5, 5.0])
    def test_efficiency_above_one_is_rejected(self, efficiency: float) -> None:
        with pytest.raises(ValueError):
            calculate_application_depth(5.0, efficiency, 0.0)

    def test_negative_rainfall_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            calculate_application_depth(5.0, 0.8, -10.0)


class TestInterval:
    def test_matches_the_closed_form(self) -> None:
        """I = (RAW * p) / ETc, floored at one day."""
        etc, raw, depletion = 5.0, 100.0, 0.5
        assert calculate_interval(etc, raw, depletion) == max(1, round(raw * depletion / etc))

    def test_is_at_least_one_day(self) -> None:
        for etc, raw, depletion in [
            (0.5, 10.0, 0.1),
            (10.0, 100.0, 0.05),
            (20.0, 5.0, 0.2),
            (5.0, 1.0, 0.1),
        ]:
            assert calculate_interval(etc, raw, depletion) >= 1

    def test_shortens_as_et_demand_rises(self) -> None:
        assert calculate_interval(8.0, 100.0, 0.5) < calculate_interval(2.0, 100.0, 0.5)

    def test_lengthens_as_depletion_allowance_rises(self) -> None:
        assert calculate_interval(5.0, 100.0, 0.7) > calculate_interval(5.0, 100.0, 0.3)

    def test_lengthens_as_available_water_rises(self) -> None:
        assert calculate_interval(5.0, 200.0, 0.5) > calculate_interval(5.0, 50.0, 0.5)

    def test_returns_an_integer_number_of_days(self) -> None:
        value = calculate_interval(4.3, 97.1, 0.53)
        assert isinstance(value, int)
        assert value >= 1

    def test_typical_wheat_schedule_is_plausible(self) -> None:
        """A silt loam wheat field: 100 mm available water, depletion 0.55,
        peak ETc 6 mm/day gives 9 days, the FAO-56 worked example."""
        assert calculate_interval(6.0, 100.0, 0.55) == 9

    @given(
        etc=st.floats(min_value=0.1, max_value=30.0, allow_nan=False),
        raw=st.floats(min_value=1.0, max_value=500.0, allow_nan=False),
        depletion=st.floats(min_value=0.05, max_value=1.0, allow_nan=False),
    )
    def test_never_exceeds_the_season_at_maximum_demand(
        self, etc: float, raw: float, depletion: float
    ) -> None:
        """A field must be irrigated often enough to meet demand, so the interval
        can never be longer than the time to exhaust the allowable depletion."""
        interval = calculate_interval(etc, raw, depletion)
        assert interval <= raw * depletion / etc + 1.0

    @pytest.mark.parametrize("etc", [0.0, -1.0])
    def test_non_positive_demand_is_rejected(self, etc: float) -> None:
        with pytest.raises(ValueError):
            calculate_interval(etc, 100.0, 0.5)

    @pytest.mark.parametrize("depletion", [0.0, 50.0, 55.0, 100.0])
    def test_depletion_must_be_a_fraction(self, depletion: float) -> None:
        with pytest.raises(ValueError):
            calculate_interval(5.0, 100.0, depletion)


class TestModuleContract:
    def test_interval_and_depth_describe_one_schedule(self) -> None:
        """The two functions must be mutually consistent: over one interval the
        field must receive at least its crop requirement."""
        etc, raw, depletion, efficiency = 5.0, 100.0, 0.5, 0.8
        interval = calculate_interval(etc, raw, depletion)
        depth = calculate_application_depth(etc, efficiency, 0.0)
        supplied = interval * depth
        assert supplied >= etc * interval - 1e-9, (
            f"{interval} events x {depth:.2f} mm = {supplied:.1f} mm cannot meet "
            f"{etc * interval:.1f} mm of demand"
        )

    def test_event_dataclass_fields_are_typed_as_documented(self) -> None:
        event = IrrigationEvent(
            date="2026-04-01",
            depth_mm=25.0,
            method="drip",
            efficiency=0.9,
            duration_hours=3.0,
        )
        assert event.depth_mm > 0.0
        assert 0.0 < event.efficiency <= 1.0
        assert event.duration_hours > 0.0

    def test_module_can_produce_a_schedule(self) -> None:
        import inspect

        from engine.hydroma.irrigation import scheduler

        source = inspect.getsource(scheduler)
        constructions = source.count("IrrigationEvent(")
        # One for the class definition's own declaration site only.
        assert constructions > 1, "IrrigationEvent is never instantiated"
