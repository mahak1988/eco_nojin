"""D8 flow routing: the direction-code convention, the accumulation order, aspect.

What these tests are for
------------------------
Four modules in ``engine.land`` used to carry a private copy of the D8
steepest-descent scan, and three of them a private copy of the accumulation.
The copies disagreed in three independent ways, and each disagreement is
silent — the function returns a plausible array either way:

1. **The label permutation.** ``drainage.py`` documents the codes as
   ``1=N 2=NE 3=E 4=SE 5=S 6=SW 7=W 8=NW`` and that is what every consumer
   assumes, because it is the only way a code becomes a row/column offset.
   ``terrain_analysis.py``, ``erosion_risk.py`` and
   ``surface_water_analysis.py`` scanned the 3x3 window in *row-major*
   order (NW, N, NE, W, E, SW, S, SE) and handed out the codes 1..8 in
   that order. Row-major and clockwise-from-north are different
   permutations of the same eight directions, so seven of eight codes were
   wrong.
2. **The distance weighting.** Steepness is the elevation drop divided by
   the distance to the neighbour — 1 for a cardinal, sqrt(2) for a
   diagonal — which is a property of the scan *position*. Three copies
   computed it from the *code* with ``np.isin(codes, {1,3,5,7})``, so in
   row-major order NW (a diagonal) was divided by 1.0 and E (a cardinal)
   by sqrt(2). Four of the eight weights were wrong on their own.
3. **The accumulation order.** ``drainage.py`` accumulated in a single
   row-major pass, which is not a topological order: a cell was added
   downstream before the cells south and west of it had contributed, so a
   large fraction of each catchment was never counted.

``TestValleyFlowsIntoItsOwnAxis`` is the test that would have caught all
three: on a V-shaped valley it is wrong in the label, the distance weight
and the accumulation at the same time. Nothing asserted the output of
``_d8_flow_direction`` anywhere before this file — the only tests that
touched it checked that the call did not raise.

The aspect tests are here for the same reason. ``terrain_analysis.py``
computed ``arctan2(-dz_dy, dz_dx)``, which transposes the two gradient
components. A compass azimuth theta has the (east, south) components
``(sin theta, -cos theta)``, so the downslope vector ``(-dz_dx, -dz_dy)``
gives ``atan2(-dz_dx, dz_dy)``. Transposing is a reflection of the aspect
field, not a rotation, so no constant offset repairs it.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.land.drainage import DrainageAnalyzer
from engine.land.erosion_risk import calculate_ls_factor
from engine.land.hydrology import (
    CODE_NAMES,
    FlowCycleError,
    flow_accumulation,
    flow_direction,
)
from engine.land.terrain_analysis import (
    aspect_to_cardinal,
    calculate_slope_aspect,
    calculate_twi,
)

#: The convention, spelled out. The numbers are what the engine returns and
#: what every consumer decodes; the names are for the failure messages.
N, NE, E, SE, S, SW, W, NW = 1, 2, 3, 4, 5, 6, 7, 8


def v_valley(rows: int = 5, cols: int = 7) -> np.ndarray:
    """A V-shaped valley opening north.

    ``dem[i, j] = 0.2 * i + |j - axis|``. Rows increase southward and
    columns eastward, so elevation falls 0.2 m to the north and rises 1 m
    per column away from the axis: the walls converge into a channel that
    drains north along the axis.

    At row 2, columns 1-5, the correct answer is therefore

        E, E, N, W, W   ->   3, 3, 1, 7, 7

    The two wall cells at column 2 prefer east over north because the
    lateral step is 1 m and the diagonal to the north-east cell gains both
    that 1 m and the 0.2 m row step, spread over sqrt(2).
    """
    rows_idx = np.arange(rows)[:, None]
    cols_idx = np.arange(cols)[None, :]
    return 0.2 * rows_idx + 1.0 * np.abs(cols_idx - (cols - 1) / 2)


def cone(size: int = 9, peak: int | None = None) -> np.ndarray:
    """A radially converging hill, so every cell drains to the centre.

    ``dem[i, j] = dist((i, j), peak)`` on a size x size grid. The steepest
    descent from any cell is the neighbour that reduces the distance to the
    centre fastest, so the whole grid converges on one outlet.
    """
    centre = (size - 1) / 2 if peak is None else peak
    rows_idx = np.arange(size)[:, None]
    cols_idx = np.arange(size)[None, :]
    return np.hypot(rows_idx - centre, cols_idx - centre)


class TestDirectionCodeConvention:
    """A code is only useful if it means the direction the docstring says."""

    def test_every_code_is_the_documented_direction(self):
        """The convention is the contract, and it is unchanged.

        This is the anchor the rest of the file measures against: if someone
        relabels the scan, this fails before the physics tests do.
        """
        from engine.land.hydrology import DIR_OFFSETS

        assert CODE_NAMES == {
            1: "N",
            2: "NE",
            3: "E",
            4: "SE",
            5: "S",
            6: "SW",
            7: "W",
            8: "NW",
        }
        assert DIR_OFFSETS[1] == (-1, 0)  # north is row - 1
        assert DIR_OFFSETS[3] == (0, 1)  # east is column + 1
        assert DIR_OFFSETS[5] == (1, 0)
        assert DIR_OFFSETS[7] == (0, -1)
        assert DIR_OFFSETS[2] == (-1, 1)
        assert DIR_OFFSETS[4] == (1, 1)
        assert DIR_OFFSETS[6] == (1, -1)
        assert DIR_OFFSETS[8] == (-1, -1)

    def test_a_cardinal_drop_beats_a_diagonal_drop_of_the_same_size(self):
        """The distance weighting, isolated.

        The west and north-west neighbours are 0.6 m below the centre each.
        West is 1 cell away and north-west is sqrt(2), so west is the
        steeper descent and the code must be 7.

        The old row-major weighting divided north-west by 1.0 and west by
        1.0 as well, so the two tied and the first position in the scan
        won — which recorded 1 (north) for a cell that drains west.
        """
        dem = np.full((5, 5), 10.0)
        dem[2, 2] = 10.0
        dem[2, 1] = 9.4  # west
        dem[1, 1] = 9.4  # north-west

        flow_dir = flow_direction(dem)

        assert flow_dir[2, 2] == W, f"expected west (7), got {flow_dir[2, 2]}"

    def test_a_diagonal_is_preferred_when_it_is_genuinely_steeper(self):
        """The other half of the weighting: a diagonal does win when it should.

        North-west is 1.0 m below over sqrt(2) (slope 0.707); north is 0.6 m
        below over 1 (slope 0.6). The diagonal is the steeper descent.
        """
        dem = np.full((5, 5), 10.0)
        dem[2, 2] = 10.0
        dem[1, 1] = 9.0  # north-west
        dem[1, 2] = 9.4  # north

        flow_dir = flow_direction(dem)

        assert flow_dir[2, 2] == NW, f"expected north-west (8), got {flow_dir[2, 2]}"

    def test_pits_and_border_cells_are_zero(self):
        """The two documented cases for code 0."""
        flat = np.full((5, 5), 100.0)
        assert (flow_direction(flat) == 0).all()

        sloped = np.broadcast_to(-np.arange(5.0)[:, None], (5, 5)).copy()
        flow_dir = flow_direction(sloped)
        assert (flow_dir[0, :] == 0).all()
        assert (flow_dir[-1, :] == 0).all()
        assert (flow_dir[:, 0] == 0).all()
        assert (flow_dir[:, -1] == 0).all()
        assert (flow_dir[1:-1, 1:-1] == S).all(), "an interior ramp falls south"

    def test_nan_cells_receive_and_donate_nothing(self):
        dem = cone()
        dem[3, 3] = np.nan
        dem[5, 4] = np.nan

        flow_dir = flow_direction(dem)

        assert flow_dir[3, 3] == 0
        assert flow_dir[5, 4] == 0
        assert not np.isnan(flow_dir).any()


class TestValleyFlowsIntoItsOwnAxis:
    """The regression that would have caught all three D8 defects at once."""

    def test_flow_dir_row_of_the_valley_is_east_east_north_west_west(self):
        dem = v_valley()

        flow_dir = flow_direction(dem)
        codes = flow_dir[2, 1:6].astype(int).tolist()
        expected = [E, E, N, W, W]

        assert codes == expected, (
            "a V-shaped valley must drain into its own axis; row 2 columns 1-5 "
            f"should be {expected}, got {codes}"
        )

    def test_the_whole_catchment_reaches_the_outlet_on_the_axis(self):
        """Accumulation needs a topological order, and the outlet must be the pit.

        15 interior cells drain onto (0, 3), so the outlet holds 16. The
        row-major pass this replaced reported 4 and put the maximum one
        column east of the axis, at (0, 4), which is not even on the channel.
        """
        dem = v_valley()

        acc = flow_accumulation(flow_direction(dem), dem)

        assert acc[0, 3] == 16.0, f"outlet accumulation {acc[0, 3]}, expected 16"
        assert acc.max() == 16.0
        assert np.unravel_index(int(acc.argmax()), acc.shape) == (0, 3), (
            "the largest accumulation must sit on the valley axis, not beside it"
        )
        # The border cells are terminal by convention, so they stay at 1.
        assert acc[0, 0] == 1.0
        assert acc[4, 6] == 1.0


class TestRadiallyConvergingDem:
    """A cone has one outlet and a known catchment, so the count is checkable."""

    def test_the_outlet_accumulates_every_cell_that_is_scored(self):
        size = 9
        dem = cone(size)
        flow_dir = flow_direction(dem)
        acc = flow_accumulation(flow_dir, dem)

        scored = int((flow_dir > 0).sum())
        # Border cells have no full 3x3 neighbourhood and the peak has no lower
        # neighbour, so those 33 cells are code 0. The other 48 all converge on
        # the peak, and the peak counts itself, so the outlet reads 49 — every
        # cell of the 7x7 interior.
        assert scored == 48

        centre = size // 2
        assert flow_dir[centre, centre] == 0, "the peak is the pit"
        assert acc[centre, centre] == 49.0, (
            "a radially converging hill drains every cell of the interior to its "
            f"peak; peak accumulation {acc[centre, centre]}, expected 49"
        )
        assert acc.max() == 49.0, "the peak must be the only maximum"
        assert acc[centre, centre] == float(scored) + 1.0

    def test_a_known_cell_drains_to_the_known_neighbour(self):
        """Directions away from the peak on a cone, one cell at a time.

        Peak at (4, 4) on a 9x9 grid. Every neighbour of the peak is one step
        closer, so each drains straight into it:

            (3, 4) -> S (5), (4, 5) -> W (7), (4, 3) -> E (3), (5, 4) -> N (1)

        and one cell further out, where the gradient is not axis-aligned:

            (2, 2) -> SE (4), (2, 6) -> SW (6), (6, 2) -> NE (2), (6, 6) -> NW (8)
        """
        dem = cone()

        flow_dir = flow_direction(dem)

        for row, col, expected, name in [
            (3, 4, S, "south"),
            (4, 5, W, "west"),
            (4, 3, E, "east"),
            (5, 4, N, "north"),
            (2, 2, SE, "south-east"),
            (2, 6, SW, "south-west"),
            (6, 2, NE, "north-east"),
            (6, 6, NW, "north-west"),
        ]:
            assert flow_dir[row, col] == expected, (
                f"cell ({row}, {col}) should drain {name} ({expected}), got {flow_dir[row, col]}"
            )

    def test_accumulation_grows_downstream_by_one_on_a_parallel_ridge(self):
        """A west-to-east ramp: interior column j holds exactly j cells.

        This is the accumulation the RUSLE slope-length term reads, and it is
        the quantity a non-topological sweep gets wrong. Column 0 is the border
        and is a pit, so column 8 on a scored row holds 8 cells and the
        westernmost scored column holds only itself.
        """
        ramp = np.broadcast_to(-np.arange(9.0)[None, :], (9, 9)).copy()

        acc = flow_accumulation(flow_direction(ramp), ramp)

        assert acc[4, 8] == 8.0
        assert acc[4, 1] == 1.0
        assert acc[4, 0] == 1.0


class TestCyclesAreLoud:
    """A cycle has no topological order, so the accumulation is undefined."""

    @staticmethod
    def two_cell_cycle() -> np.ndarray:
        """Two adjacent cells pointing at each other: (1, 1) -> E, (1, 2) -> W."""
        flow_dir = np.zeros((5, 5), dtype=np.float64)
        flow_dir[1, 1] = E
        flow_dir[1, 2] = W
        return flow_dir

    def test_flow_accumulation_raises(self):
        with pytest.raises(FlowCycleError) as excinfo:
            flow_accumulation(self.two_cell_cycle())

        message = str(excinfo.value)
        assert "cycle" in message
        assert "row 1, column 1" in message, f"the trapped cell is not named: {message}"

    def test_the_error_names_the_elevations_when_a_dem_is_supplied(self):
        dem = np.zeros((5, 5))
        dem[1, 1] = 12.0
        dem[1, 2] = 12.0

        with pytest.raises(FlowCycleError) as excinfo:
            flow_accumulation(self.two_cell_cycle(), dem)

        assert "12.0" in str(excinfo.value)

    def test_an_acyclic_grid_does_not_raise(self):
        acc = flow_accumulation(flow_direction(cone()))
        assert np.isfinite(acc).all()

    def test_codes_outside_the_convention_are_rejected(self):
        flow_dir = np.zeros((4, 4))
        flow_dir[1, 1] = 9.0
        with pytest.raises(ValueError, match="0-8"):
            flow_accumulation(flow_dir)


class TestAspectIsCompassDownslope:
    """A grid array is not a compass. Rows increase south, columns increase east."""

    @staticmethod
    def ramp(rows: int = 7, cols: int = 7) -> np.ndarray:
        return np.broadcast_to(-np.arange(float(rows))[:, None], (rows, cols)).copy()

    def test_a_north_to_south_slope_has_aspect_180(self):
        dem = self.ramp()

        _slope, aspect = calculate_slope_aspect(dem, 30.0)

        interior = aspect[1:-1, 1:-1]
        assert np.allclose(interior, 180.0), (
            f"a surface descending north to south is due south, 180 deg; got {interior}"
        )
        assert aspect_to_cardinal(180.0) == "S"

    def test_a_west_to_east_slope_has_aspect_90(self):
        dem = np.broadcast_to(-np.arange(7.0)[None, :], (7, 7)).copy()

        _slope, aspect = calculate_slope_aspect(dem, 30.0)

        interior = aspect[1:-1, 1:-1]
        assert np.allclose(interior, 90.0), (
            f"a surface descending west to east is due east, 90 deg; got {interior}"
        )
        assert aspect_to_cardinal(90.0) == "E"

    @pytest.mark.parametrize(
        ("dem", "expected", "name"),
        [
            (np.broadcast_to(-np.arange(7.0)[None, :], (7, 7)).copy(), 90.0, "east"),
            (np.broadcast_to(-np.arange(7.0)[:, None], (7, 7)).copy(), 180.0, "south"),
            (
                np.broadcast_to(
                    (-np.arange(7.0)[:, None] - np.arange(7.0)[None, :]), (7, 7)
                ).copy(),
                135.0,
                "south-east",
            ),
            (
                np.broadcast_to((np.arange(7.0)[:, None] - np.arange(7.0)[None, :]), (7, 7)).copy(),
                45.0,
                "north-east",
            ),
        ],
    )
    def test_every_quadrant_of_a_tilted_plane(self, dem, expected, name):
        """The four diagonal quadrants too, so a swapped pair of arguments
        cannot pass by being self-consistent."""
        _slope, aspect = calculate_slope_aspect(dem, 30.0)
        assert np.allclose(aspect[1:-1, 1:-1], expected), (
            f"expected aspect {name} ({expected}), got {aspect[1, 1]}"
        )

    def test_slope_magnitude_is_unchanged_by_the_aspect_correction(self):
        """Only the aspect was wrong; the gradient magnitude was not."""
        dem = np.broadcast_to(
            (-np.arange(7.0)[:, None] * 3.0 - np.arange(7.0)[None, :]), (7, 7)
        ).copy()

        slope, _aspect = calculate_slope_aspect(dem, 30.0)

        # Gradient is (dz/dx, dz/dy) = (-1/30, -3/30) m/m.
        expected = np.degrees(np.arctan(np.hypot(1.0 / 30.0, 3.0 / 30.0)))
        assert np.allclose(slope[1:-1, 1:-1], expected)


class TestDownstreamConsumersUseTheOneImplementation:
    """TWI, the RUSLE length term and the surface-water scan all read the same grid."""

    def test_twi_peaks_at_the_cone_outlet(self):
        """TWI = ln(specific catchment area / tan(beta)); it is highest where the
        catchment is largest. A routing error shows up as a peak somewhere else."""
        dem = cone() * 10.0  # metres, so the slope is a real angle

        twi = calculate_twi(dem, 30.0)

        centre = 9 // 2
        assert twi[centre, centre] == pytest.approx(np.nanmax(twi))
        assert np.isfinite(twi).any()

    def test_the_rusle_slope_length_reads_the_true_catchment(self):
        """``calculate_ls_factor`` derives lambda from D8 accumulation internally.

        On a 9-column west-to-east ramp the accumulation at column 8 is 7, so
        lambda = 30 * sqrt(7) m. Feeding the same accumulation in by hand must
        reproduce the array exactly, which is only true if the internal scan and
        the shared one agree.
        """
        ramp = np.broadcast_to(-np.arange(9.0)[None, :], (9, 9)).copy()

        from_dem = calculate_ls_factor(dem=ramp, cell_size_m=30.0)
        from_acc = calculate_ls_factor(
            slope_degrees=None,
            dem=ramp,
            cell_size_m=30.0,
            flow_acc=flow_accumulation(flow_direction(ramp), ramp),
        )

        assert np.allclose(from_dem, from_acc)

    def test_drainage_analyzer_reports_the_axial_outlet(self):
        """``DrainageAnalyzer.analyze`` is the only drainage path in production
        (via ``adapters/engine_adapter.py``), so its accumulation is the one
        the valley test above is protecting."""
        dem = v_valley()

        analysis = DrainageAnalyzer(resolution=30.0).analyze(dem, profile_id="v")

        acc = np.asarray(analysis.flow_accumulation)
        assert acc[0, 3] == 16.0, f"production path outlet accumulation {acc[0, 3]}, expected 16"
        assert acc.max() == 16.0

    def test_surface_water_scanner_agrees_with_the_shared_implementation(self):
        from engine.land.dem_processor import DEMProcessor
        from engine.land.surface_water_analysis import SurfaceWaterAnalyzer

        dem = v_valley()
        processor = DEMProcessor("unused.tif")
        processor._data = dem
        analyzer = SurfaceWaterAnalyzer(processor)

        assert np.array_equal(
            analyzer.identify_flow_accumulation(), flow_accumulation(flow_direction(dem), dem)
        )
