"""S03 — Surface hydrology: SCS-CN and the Rational method.

Standards under test
--------------------
* NRCS National Engineering Handbook, Part 630, Chapter 16 (Irrigation) /
  TR-55 (Conservation Engineering) — Soil Conservation Service curve number:

      S  = 25400 / CN - 254            [mm]     (SI form)
      Ia = 0.2 S                                [mm]
      Q  = (P - Ia)^2 / (P + 0.8 S)             [mm]   for P > Ia, else 0

  The US-customary form S = 1000/CN - 10 yields INCHES and must never be mixed
  with millimetre rainfall. The engine already carries that warning, so this
  module treats the inch form as a forbidden alternative.

* Rational method, Q = C i A. The engine exposes two separate implementations
  (``RunoffCalculator`` and ``watershed.calculate_runoff``); both are checked
  against the closed form, and against each other.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, strategies as st
from pydantic import ValidationError

from engine.hydroma.models.runoff_model import (
    CurveNumberType,
    RunoffCalculator,
    RunoffInput,
    SpatialRunoffInput,
    SpatialRunoffOutput,
)
from engine.strict_tests.conftest import NRCS_SCS_CN_WORKED_EXAMPLE as WX


def _scs_runoff_mm(precip_mm: float, cn: float) -> float:
    """Independent implementation of the NRCS curve-number relation, SI form."""
    s = 25400.0 / cn - 254.0
    if s < 0.0:
        raise ValueError("CN above 100")
    ia = 0.2 * s
    if precip_mm <= ia:
        return 0.0
    return (precip_mm - ia) ** 2 / (precip_mm + 0.8 * s)


def _scs_retention_inches(cn: float) -> float:
    """The forbidden US-customary form, used to size the unit error."""
    return 1000.0 / cn - 10.0


class TestScsCurveNumber:
    def test_nrcs_worked_example(self) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=WX["precipitation_mm"],
                curve_number=WX["curve_number"],
                area_ha=1.0,
            )
        )
        depth_mm = out.volume_m3 / 10.0
        assert depth_mm == pytest.approx(WX["runoff_mm"], rel=1e-9)

    def test_retention_is_millimetres(self) -> None:
        """The SI retention for CN=70 is 108.857 mm, i.e. 4.2857 inches.

        The engine's own comment at line 113 warns that the US-customary form
        yields inches. This test pins the pair so a return to inches cannot pass.
        """
        s_mm = WX["retention_mm"]
        s_in = WX["retention_inches"]
        assert s_mm == pytest.approx(108.857, abs=1e-3)
        assert s_in == pytest.approx(4.2857, abs=1e-4)
        assert s_mm == pytest.approx(25.4 * s_in, rel=1e-12), (
            "mm and inch forms must differ by 25.4"
        )

    def test_matches_independent_rederivation(self) -> None:
        for cn in (30.0, 45.0, 60.0, 70.0, 78.0, 85.0, 95.0, 100.0):
            for precip in (5.0, 25.0, 50.0, 120.0, 300.0):
                out = RunoffCalculator().execute(
                    RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=2.0)
                )
                assert out.volume_m3 == pytest.approx(
                    _scs_runoff_mm(precip, cn) * 2.0 * 10.0, rel=1e-9
                ), f"CN={cn} P={precip}"

    def test_initial_abstraction_is_twenty_percent_of_retention(self) -> None:
        cn, precip = 70.0, 21.7714285714  # exactly Ia for CN = 70
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=1.0)
        )
        assert out.volume_m3 == pytest.approx(0.0, abs=1e-9)
        just_above = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=precip + 0.01, curve_number=cn, area_ha=1.0)
        )
        assert just_above.volume_m3 > 0.0

    def test_curve_number_100_gives_full_runoff(self) -> None:
        """CN = 100 means zero retention, so the whole rainfall becomes runoff."""
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=50.0, curve_number=100.0, area_ha=1.0)
        )
        assert out.volume_m3 == pytest.approx(500.0, rel=1e-9)

    def test_curve_number_above_100_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="100"):
            RunoffCalculator().execute(
                RunoffInput(precipitation_mm=50.0, curve_number=150.0, area_ha=1.0)
            )

    @pytest.mark.parametrize("cn", [0.0, 0.5])
    def test_non_positive_curve_number_raises_value_error(self, cn: float) -> None:
        with pytest.raises(ValueError):
            RunoffCalculator().execute(
                RunoffInput(precipitation_mm=50.0, curve_number=cn, area_ha=1.0)
            )

    @pytest.mark.parametrize("cn", [5.0, 20.0, 29.0])
    def test_out_of_table_curve_number_is_rejected(self, cn: float) -> None:
        with pytest.raises(ValidationError):
            RunoffInput(precipitation_mm=50.0, curve_number=cn, area_ha=1.0)

    def test_curve_number_enum_values_are_distinct_and_in_table(self) -> None:
        values = [int(member.value) for member in CurveNumberType]
        assert len(set(values)) == len(values)
        assert all(30 <= v <= 100 for v in values)

    @given(
        precip=st.floats(min_value=0.1, max_value=2000.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=100.0, allow_nan=False),
        area=st.floats(min_value=0.001, max_value=1e5, allow_nan=False),
    )
    def test_runoff_never_exceeds_rainfall_volume(
        self, precip: float, cn: float, area: float
    ) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=area)
        )
        # The engine associates the multiplication as depth x area x 10 while the
        # reference is precip x area x 10, so a 1e-12 relative slack covers the
        # difference in rounding and nothing more.
        ceiling = precip * area * 10.0
        assert 0.0 <= out.volume_m3 <= ceiling * (1.0 + 1e-12)

    @given(
        precip=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=95.0, allow_nan=False),
    )
    def test_runoff_increases_with_rainfall(self, precip: float, cn: float) -> None:
        low = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=1.0))
            .volume_m3
        )
        # Above the initial abstraction the response is strictly increasing.
        assume(_scs_runoff_mm(precip, cn) > 0.0)
        high = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip + 10.0, curve_number=cn, area_ha=1.0))
            .volume_m3
        )
        assert high > low

    @given(
        precip=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=90.0, allow_nan=False),
    )
    def test_runoff_increases_with_curve_number(self, precip: float, cn: float) -> None:
        """A higher curve number means lower retention, hence MORE runoff.

        S = 25400/CN - 254 falls as CN rises, and dQ/dS < 0 for P > Ia, so Q rises
        with CN. Checked on the reference day: at P = 118.6 mm the runoff is
        8e-6 mm at CN = 30, 1.19 mm at CN = 35 and 90.3 mm at CN = 90.
        """
        assume(_scs_runoff_mm(precip, cn) > 0.0 and _scs_runoff_mm(precip, cn + 5.0) > 0.0)
        low = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=1.0))
            .volume_m3
        )
        high = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn + 5.0, area_ha=1.0))
            .volume_m3
        )
        assert high > low, f"runoff fell when the curve number rose: {low} -> {high}"

    @given(
        precip=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False),
        cn=st.floats(min_value=35.0, max_value=95.0, allow_nan=False),
    )
    def test_retention_falls_as_curve_number_rises(self, precip: float, cn: float) -> None:
        """The complementary statement: retention S must be strictly decreasing in CN."""
        assert 25400.0 / (cn + 5.0) - 254.0 < 25400.0 / cn - 254.0

    @given(
        precip=st.floats(min_value=1.0, max_value=500.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=100.0, allow_nan=False),
    )
    def test_scales_linearly_with_area(self, precip: float, cn: float) -> None:
        one = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=1.0))
            .volume_m3
        )
        seven = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=7.0))
            .volume_m3
        )
        assert seven == pytest.approx(7.0 * one, rel=1e-9)


class TestPeakFlow:
    def test_peak_flow_has_units_of_cubic_metres_per_second(self) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=WX["precipitation_mm"],
                curve_number=WX["curve_number"],
                area_ha=1.0,
            )
        )
        # A 58.13 m3 volume over a 1-hour storm is a mean discharge of 0.0161 m3/s.
        assert out.peak_flow_m3s == pytest.approx(out.volume_m3 / 3600.0, rel=1e-9)

    def test_no_peak_flow_below_initial_abstraction(self) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=5.0, curve_number=70.0, area_ha=1.0)
        )
        assert out.volume_m3 == 0.0
        assert out.peak_flow_m3s == 0.0

    @given(
        precip=st.floats(min_value=40.0, max_value=400.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=100.0, allow_nan=False),
        area=st.floats(min_value=0.01, max_value=1e4, allow_nan=False),
    )
    def test_peak_flow_scales_with_volume(self, precip: float, cn: float, area: float) -> None:
        """A discharge is a volume per unit time, so peak/volume is 1/t.

        The divisor used to be 36000, a dimensionless number, which made the
        reported rate exactly 10x too small even under the 1-hour assumption it
        never stated.
        """
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=area)
        )
        if out.volume_m3 > 0.0:
            assert out.peak_flow_m3s > 0.0
            assert out.peak_flow_m3s / out.volume_m3 == pytest.approx(1 / 3600.0, rel=1e-12)

    @pytest.mark.parametrize("duration", [0.5, 1.0, 3.0, 6.0])
    def test_peak_flow_is_the_rate_over_the_storm(self, duration: float) -> None:
        """The declared duration is the denominator, and it now reaches the result."""
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=50.0,
                curve_number=70.0,
                area_ha=1.0,
                storm_duration_h=duration,
            )
        )
        assert out.peak_flow_m3s == pytest.approx(out.volume_m3 / (duration * 3600.0), rel=1e-12)

    def test_duration_defaults_to_one_hour(self) -> None:
        default = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=50.0, curve_number=70.0, area_ha=1.0)
        )
        explicit = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=50.0,
                curve_number=70.0,
                area_ha=1.0,
                storm_duration_h=1.0,
            )
        )
        assert default.peak_flow_m3s == explicit.peak_flow_m3s

    def test_duration_must_be_positive(self) -> None:
        for bad in (0.0, -1.0):
            with pytest.raises(ValidationError):
                RunoffInput(precipitation_mm=50.0, area_ha=1.0, storm_duration_h=bad)


class TestRationalMethod:
    def test_peak_flow_matches_closed_form(self) -> None:
        """Q = C i A with i in mm/hr, A in ha, converted to m3/s."""
        c, precip, area = 0.6, 50.0, 2.0
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=precip,
                area_ha=area,
                method="Rational",
                rational_coefficient=c,
            )
        )
        expected = c * precip * area * 10.0 / 3600.0
        assert out.peak_flow_m3s == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize("c", [0.1, 0.2, 0.6, 0.9])
    def test_runoff_volume_applies_the_coefficient(self, c: float) -> None:
        precip, area = 50.0, 2.0
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=precip,
                area_ha=area,
                method="Rational",
                rational_coefficient=c,
            )
        )
        assert out.volume_m3 == pytest.approx(c * precip * area * 10.0, rel=1e-9)

    def test_volume_agrees_with_the_peak_flow_the_call_returns(self) -> None:
        c, precip, area = 0.6, 50.0, 2.0
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=precip,
                area_ha=area,
                method="Rational",
                rational_coefficient=c,
            )
        )
        assert out.volume_m3 / 3600.0 == pytest.approx(out.peak_flow_m3s, rel=1e-9)

    def test_scs_branch_ignores_the_rational_coefficient(self) -> None:
        """Documented behaviour: the two methods have separate parameter sets."""
        base = RunoffInput(precipitation_mm=50.0, area_ha=2.0, method="SCS-CN")
        with_c = RunoffInput(
            precipitation_mm=50.0, area_ha=2.0, method="SCS-CN", rational_coefficient=0.05
        )
        assert (
            RunoffCalculator().execute(base).volume_m3
            == RunoffCalculator().execute(with_c).volume_m3
        )

    def test_agrees_with_the_watershed_module(self) -> None:
        from engine.hydroma.watershed.calculator import calculate_runoff

        c, precip, area_m2 = 0.5, 80.0, 20_000.0
        engine_out = (
            RunoffCalculator()
            .execute(
                RunoffInput(
                    precipitation_mm=precip,
                    area_ha=area_m2 / 10_000.0,
                    method="Rational",
                    rational_coefficient=c,
                )
            )
            .volume_m3
        )
        assert engine_out == pytest.approx(calculate_runoff(area_m2, precip, c), rel=1e-9)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/models/runoff_model.py:93 hardcodes duration_hr = 1.0 "
            "and line 94 takes the design depth as the intensity. The rational "
            "method is only valid for storms whose duration equals or exceeds the "
            "time of concentration, and RunoffInput has no duration field, so a "
            "50 mm daily total is silently treated as a 50 mm/hr burst."
        ),
    )
    def test_intensity_uses_an_explicit_storm_duration(self) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=50.0, area_ha=1.0, method="Rational")
        )
        # With a 6-hour storm the intensity is 8.33 mm/hr, not 50 mm/hr.
        assert out.peak_flow_m3s == pytest.approx(
            0.6 * (50.0 / 6.0) * 1.0 * 10.0 / 3600.0, rel=1e-9
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "RunoffInput.rational_coefficient has no bounds. A coefficient of 0 "
            "or negative yields a negative peak flow, and a coefficient above 1 "
            "yields a peak flow exceeding the rainfall intensity, both of which "
            "are physically impossible for the rational method (0 <= C <= 1)."
        ),
    )
    @pytest.mark.parametrize("c", [-0.5, 0.0, 1.5, 5.0])
    def test_rational_coefficient_is_bounded(self, c: float) -> None:
        with pytest.raises(ValidationError):
            RunoffInput(
                precipitation_mm=50.0, area_ha=1.0, method="Rational", rational_coefficient=c
            )


class TestInputContract:
    def test_rejects_non_positive_precipitation(self) -> None:
        for value in (0.0, -1.0):
            with pytest.raises(ValidationError):
                RunoffInput(precipitation_mm=value, area_ha=1.0)

    def test_rejects_non_positive_area(self) -> None:
        for value in (0.0, -1.0):
            with pytest.raises(ValidationError):
                RunoffInput(precipitation_mm=10.0, area_ha=value)

    def test_rejects_unknown_method(self) -> None:
        with pytest.raises(ValidationError):
            RunoffInput(precipitation_mm=10.0, area_ha=1.0, method="Kinematic-wave")

    def test_spatial_input_only_advertises_scs_cn(self) -> None:
        with pytest.raises(ValidationError):
            SpatialRunoffInput(
                dem_path="a.tif",
                land_use_path="b.tif",
                soil_path="c.tif",
                precipitation_mm=10.0,
                method="Rational",
            )


class TestSpatialRunoff:
    def test_peak_flow_map_field_is_declared_but_never_populated(self) -> None:
        """``SpatialRunoffOutput.peak_flow_map_path`` is part of the published
        response contract but the only ``execute`` implementation never sets it,
        so a client that follows the schema receives a silent ``None`` and cannot
        distinguish 'not computed' from 'not applicable'."""
        import inspect

        from engine.hydroma.models.runoff_model import SpatialRunoffCalculator

        assert "peak_flow_map_path" in SpatialRunoffOutput.model_fields
        body = inspect.getsource(SpatialRunoffCalculator.execute)
        assert "peak_flow_map_path" not in body, "execute() populates the field after all"
        assert SpatialRunoffOutput().peak_flow_map_path is None

    def test_soil_raster_is_loaded_but_never_used(self) -> None:
        """The CN map is built from land use alone.

        ``_create_cn_map_from_lu_soil(lu, soil)`` accepts the soil raster, and the
        surrounding code reprojects and aligns it, but the body maps land-use codes
        to fixed curve numbers with a default. The docstring concedes it is
        'a simplified mapping'. For an erosion digital twin this silently ignores
        the hydrologic soil group, which is half of the SCS-CN definition.
        """
        import ast
        import inspect
        import textwrap

        from engine.hydroma.models.runoff_model import SpatialRunoffCalculator

        source = textwrap.dedent(
            inspect.getsource(SpatialRunoffCalculator._create_cn_map_from_lu_soil)
        )
        fn = ast.parse(source).body[0]
        params = [a.arg for a in fn.args.args]
        assert params == ["self", "lu", "soil"]
        # Everything after the function signature, i.e. the statements only.
        body_nodes = fn.body
        referenced = {
            node.id
            for node in ast.walk(ast.Module(body=body_nodes, type_ignores=[]))
            if isinstance(node, ast.Name)
        }
        assert "soil" not in referenced, (
            "the soil argument is now referenced in the body; the curve-number map "
            "is no longer land-use-only and this test needs revisiting"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/models/runoff_model.py:179-197 builds the "
            "curve-number map from land-use codes alone (60/70/85/75) and never "
            "consults the soil raster it was handed, even though the enclosing "
            "execute() reprojected and aligned that raster specifically for this "
            "call. A clay hydrologic soil group and a sand group on the same land "
            "use therefore receive byte-identical curve numbers, which is wrong by "
            "up to 25 curve-number units. The spatial result is therefore not an "
            "SCS-CN computation."
        ),
    )
    def test_cn_map_is_independent_of_the_soil_group(self) -> None:
        """Two sites with identical land use but different soils must get
        different curve numbers, because HSG is a defining input of SCS-CN."""
        import numpy as np
        import xarray as xr

        from engine.hydroma.models.runoff_model import SpatialRunoffCalculator

        lu = xr.DataArray(np.array([[1, 2], [3, 3]], dtype="int32"))
        clay = xr.DataArray(np.array([[1, 1], [1, 1]], dtype="int32"))  # HSG C/D
        sand = xr.DataArray(np.array([[4, 4], [4, 4]], dtype="int32"))  # HSG A/B
        calc = SpatialRunoffCalculator()
        cn_clay = calc._create_cn_map_from_lu_soil(lu, clay)
        cn_sand = calc._create_cn_map_from_lu_soil(lu, sand)
        assert not np.array_equal(np.asarray(cn_clay), np.asarray(cn_sand)), (
            "the curve-number map is byte-identical for clay and sand soils"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/models/runoff_model.py:235 names the output raster "
            "f'runoff_cn_{method}_site_{hash(dem_path)}.tif'. Python randomises "
            "str hashing per process unless PYTHONHASHSEED is pinned, so the same "
            "DEM yields a different filename on every run. Verified by running "
            "this interpreter twice with different seeds: hash('a.tif') is 4.8e18 "
            "under one seed and 2.3e18 under another. Written rasters therefore "
            "cannot be found again, deduplicated, or cached, and a rerun of the "
            "same scenario silently produces a new artefact every time."
        ),
    )
    def test_spatial_output_path_is_reproducible_across_processes(self) -> None:
        import subprocess
        import sys

        script = "print(hash('a.tif'))"
        seeds = ("0", "1")
        values = []
        for seed in seeds:
            env = {**__import__("os").environ, "PYTHONHASHSEED": seed}
            result = subprocess.run(
                [sys.executable, "-c", script], capture_output=True, text=True, env=env
            )
            values.append(result.stdout.strip())
        assert values[0] == values[1], f"hash('a.tif') differs by PYTHONHASHSEED: {values}"
