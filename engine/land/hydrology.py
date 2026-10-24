"""D8 flow routing for the land engine: one scan, one code table, one sweep.

Why this module exists
----------------------
Four modules in this package each carried a private copy of the D8
steepest-descent scan, and three of them carried a private copy of the
accumulation. The copies were not identical, and the disagreements were
not cosmetic.

**The label permutation.** ``drainage.py`` documented the direction codes
as ``1=N 2=NE 3=E 4=SE 5=S 6=SW 7=W 8=NW`` — clockwise from north — and
that is the convention every consumer still assumes, because it is the
only way a code becomes a grid offset. But ``terrain_analysis.py``,
``erosion_risk.py`` and ``surface_water_analysis.py`` scanned the 3x3
window in *row-major* order (NW, N, NE, W, E, SW, S, SE) and handed out
the codes 1..8 in that order. Row-major and clockwise-from-north are two
different permutations of the same eight directions, so seven of the
eight codes were mislabelled: a cell that drains east was recorded as
code 5, which every reader decodes as south.

**The distance weighting.** The steepness of a candidate neighbour is the
elevation drop divided by the distance to it. That distance is 1 for a
cardinal neighbour and sqrt(2) for a diagonal one, and it depends on the
*position* in the scan, not on the code that position is given. Three of
the copies computed it with ``np.isin(codes, {1, 3, 5, 7})``, i.e. keyed
on the code, so in row-major scan order index 0 (NW, a diagonal) was
given 1.0 and index 4 (E, a cardinal) was given sqrt(2). Four of the
eight weights were wrong on their own, before the labels were considered.

**The accumulation order.** Flow accumulation is only correct if every
cell is added to its downstream neighbour after all of that neighbour's
own upstream cells have been added. ``drainage.py`` did that with a
single row-major pass over the grid, which is not a topological order: a
cell is processed before cells south and west of it have contributed, so
a large fraction of the catchment is never counted. It also computed a
``flat_order`` sort and threw it away, and its docstring claimed
topological sorting by elevation that the code did not do. On a V-shaped
valley it reported a maximum accumulation of 5 where the deque-based
sweep already present in ``terrain_analysis.py`` reported 13.

**Cycles.** A drainage cycle has no topological order, so an accumulation
over one is undefined. Three of the copies detected that state and
returned a silently truncated array, and one carried a ``pass`` where the
detection was supposed to be handled. A cycle is now a raised error
(:class:`FlowCycleError`) with the offending cells named, because a
truncated watershed is worse than a failed one.

Convention kept
---------------
The documented code convention is the contract, and the scan order is
what was changed to match it. The neighbour scan therefore runs
``N, NE, E, SE, S, SW, W, NW`` — the same order as the codes, clockwise
from north — instead of row-major. Relabelling the scan to match a
row-major convention instead would have been the smaller edit but would
have silently reinterpret every code already stored, every offset table
already written, and every recorded baseline.

References
----------
O'Callaghan & Mark (1984), *D8 — the successor to the single direction
flow-routing procedure*: steepest descent on the 3x3 neighbourhood, with
the drop divided by the true neighbour distance.
Quinn et al. (1991), *The prediction of hillslope flow paths for
distributed hydrological modelling using digital terrain models* — the
in-degree queue that gives a topological order without sorting.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np

# Numba is an OPTIONAL accelerator (``pip install .[fast]``). When it is absent
# the import degrades ``njit`` to an identity decorator and sets ``_NUMBA_OK``
# to False, so every public call site below selects the original pure-Python
# path. The kernels are always defined (matching the ``cpp_bridge`` convention)
# but only invoked while ``_NUMBA_OK`` is True.
try:
    from numba import njit

    _NUMBA_OK = True
except Exception:
    _NUMBA_OK = False

    def njit(*args, **kwargs):
        """Identity stand-in for ``numba.njit`` used when Numba is unavailable."""
        if len(args) == 1 and callable(args[0]):
            return args[0]

        def decorator(func):
            return func

        return decorator


__all__ = [
    "CARDINAL_CODES",
    "CODE_NAMES",
    "DIR_OFFSETS",
    "FlowCycleError",
    "flow_accumulation",
    "flow_direction",
    "strahler_order",
]


#: The engine's direction-code convention: clockwise from north. This is the
#: contract — a code is only useful because every reader can turn it into the
#: row/column offset below. The scan in :func:`flow_direction` runs in this
#: same order so the two can never drift apart again.
DIR_OFFSETS: dict[int, tuple[int, int]] = {
    1: (-1, 0),  # N
    2: (-1, 1),  # NE
    3: (0, 1),  # E
    4: (1, 1),  # SE
    5: (1, 0),  # S
    6: (1, -1),  # SW
    7: (0, -1),  # W
    8: (-1, -1),  # NW
}

#: Codes whose neighbour is orthogonally adjacent (distance 1); the rest are
#: diagonal (distance sqrt(2)).
CARDINAL_CODES: frozenset[int] = frozenset({1, 3, 5, 7})

#: Human-readable name per code, for error messages and reports.
CODE_NAMES: dict[int, str] = {
    1: "N",
    2: "NE",
    3: "E",
    4: "SE",
    5: "S",
    6: "SW",
    7: "W",
    8: "NW",
}

_SQRT2 = float(np.sqrt(2.0))

# Scan position == code - 1, clockwise from north. The arrays below are indexed
# by scan position, so the distance a candidate is divided by is a property of
# the position and not of the code it happens to be labelled with.
_CODES = np.arange(1, 9, dtype=np.float64)
_DISTANCES = np.array([1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2])
_OFFSETS = tuple(DIR_OFFSETS[code] for code in range(1, 9))

# Code 0 ("pit", no downslope neighbour) contributes a zero offset so the
# offsets can be gathered for the whole grid without a branch.
_DI_BY_CODE = np.array([0] + [di for di, _ in _OFFSETS], dtype=np.int64)
_DJ_BY_CODE = np.array([0] + [dj for _, dj in _OFFSETS], dtype=np.int64)


class FlowCycleError(ValueError):
    """A flow-direction grid contains a closed loop.

    Accumulation over a cycle is undefined — there is no cell in the loop whose
    total is known before the loop is traversed — so this is raised rather than
    returned as a partially filled array. A truncated watershed reads as a real
    number downstream, which is the failure mode this replaces.
    """


def flow_direction(dem: Any) -> np.ndarray:
    """D8 flow direction by steepest descent (O'Callaghan & Mark 1984).

    For every interior cell the eight neighbours are scored by
    ``(centre - neighbour) / distance`` and the highest score wins, so a
    diagonal neighbour competes on its true gradient rather than on its raw
    elevation drop. A cell with no strictly lower neighbour is a pit and gets
    code 0; the grid border also gets 0, because a border cell has no full
    3x3 neighbourhood to score.

    Args:
        dem: 2-D elevation array. Non-finite cells never receive flow and never
            donate it.

    Returns:
        Float array of the same shape holding 1..8 per
        :data:`DIR_OFFSETS` (clockwise from north), 0 for pits and borders.
    """
    dem = np.asarray(dem, dtype=float)
    if dem.ndim != 2:
        raise ValueError(f"DEM must be 2-D, got shape {dem.shape}")

    rows, cols = dem.shape
    if rows < 3 or cols < 3:
        return np.zeros((rows, cols), dtype=np.float64)

    # NaN padding makes the out-of-grid neighbours fail the isfinite test, which
    # is the same as not having a lower neighbour there.
    padded = np.full((rows + 2, cols + 2), np.nan, dtype=np.float64)
    padded[1:-1, 1:-1] = dem
    centre = padded[1:-1, 1:-1]
    neighbourhood = np.stack(
        [padded[1 + di : 1 + di + rows, 1 + dj : 1 + dj + cols] for di, dj in _OFFSETS],
        axis=-1,
    )

    lower = np.isfinite(neighbourhood) & (neighbourhood < centre[..., None])
    slope = np.where(lower, (centre[..., None] - neighbourhood) / _DISTANCES, -np.inf)

    # argmax returns the first maximum, so a tie resolves toward the earlier
    # direction in clockwise order (N before NE before E, and so on).
    best = np.argmax(slope, axis=-1)
    best_slope = np.take_along_axis(slope, best[..., None], axis=-1)[..., 0]

    scored = np.isfinite(centre) & lower.any(axis=-1) & (best_slope > 0.0)
    # The border is masked rather than left to the NaN padding: a corner does
    # have a lower neighbour available and would otherwise be scored on a
    # 3x3 window that does not exist.
    scored[0, :] = False
    scored[-1, :] = False
    scored[:, 0] = False
    scored[:, -1] = False
    return np.where(scored, _CODES[best], 0.0)


@njit(cache=True)
def _flow_accumulation_kernel(codes, di_by_code, dj_by_code):
    """In-degree (Quinn et al. 1991) accumulation over an int64 code grid.

    Bit-identical to the pure-Python ``deque`` sweep in :func:`flow_accumulation`:
    the queue is seeded and released in exactly row-major then topological order,
    and the only floating-point operation -- ``acc[target] += acc[cell]`` -- is a
    single float64 addition applied in the same sequence, so no re-association
    occurs.

    Args:
        codes: int64 (rows, cols) direction codes, already range-checked 0-8.
        di_by_code: int64 length-9 row offset per code (index 0 unused).
        dj_by_code: int64 length-9 column offset per code.

    Returns:
        ``(acc, processed, pending)`` -- accumulation, cells released from the
        queue, and the leftover in-degree (``pending > 0`` marks a cycle).
    """
    rows, cols = codes.shape
    acc = np.ones((rows, cols), dtype=np.float64)
    downstream_r = np.full((rows, cols), -1, dtype=np.int64)
    downstream_c = np.full((rows, cols), -1, dtype=np.int64)
    # In-degree of each cell: how many cells are still waiting to drain into it.
    pending = np.zeros((rows, cols), dtype=np.int64)
    for i in range(rows):
        for j in range(cols):
            code = codes[i, j]
            if code > 0:
                ni = i + di_by_code[code]
                nj = j + dj_by_code[code]
                if (ni >= 0) and (ni < rows) and (nj >= 0) and (nj < cols):
                    downstream_r[i, j] = ni
                    downstream_c[i, j] = nj
                    pending[ni, nj] += 1

    # FIFO queue buffer sized to the grid; each cell is enqueued at most once.
    queue = np.empty(rows * cols, dtype=np.int64)
    tail = 0
    for i in range(rows):
        for j in range(cols):
            if pending[i, j] == 0:
                queue[tail] = i * cols + j
                tail += 1
    head = 0
    processed = 0
    while head < tail:
        flat = queue[head]
        head += 1
        processed += 1
        i = flat // cols
        j = flat - i * cols
        target_r = downstream_r[i, j]
        if target_r < 0:
            continue
        target_c = downstream_c[i, j]
        acc[target_r, target_c] += acc[i, j]
        pending[target_r, target_c] -= 1
        if pending[target_r, target_c] == 0:
            queue[tail] = target_r * cols + target_c
            tail += 1
    return acc, processed, pending


def flow_accumulation(flow_dir: Any, dem: Any = None) -> np.ndarray:
    """D8 flow accumulation over a true topological order (Quinn et al. 1991).

    Every cell starts with a count of 1 (itself). A cell is released from the
    queue only once every cell draining into it has been released, so a cell is
    always added downstream with its total already complete. Cells with no
    upstream cell are released first; the sweep ends when the queue empties.

    Args:
        flow_dir: 2-D array of direction codes as returned by
            :func:`flow_direction`. 0 means pit or border.
        dem: Optional DEM, used only to describe a cycle in the error message.
            It does not enter the accumulation.

    Returns:
        Float array of the same shape holding the number of cells draining
        into each cell, itself included. Cells whose flow leaves the grid keep
        their own total.

    Raises:
        FlowCycleError: if the codes contain a closed loop, so no topological
            order exists and the accumulation is undefined.
    """
    flow_dir = np.asarray(flow_dir, dtype=float)
    if flow_dir.ndim != 2:
        raise ValueError(f"flow_dir must be 2-D, got shape {flow_dir.shape}")

    rows, cols = flow_dir.shape
    acc = np.ones((rows, cols), dtype=np.float64)
    if rows == 0 or cols == 0:
        return acc

    codes = np.rint(flow_dir).astype(np.int64)
    out_of_range = (codes < 0) | (codes > 8)
    if out_of_range.any():
        raise ValueError(
            f"flow direction codes must be 0-8, found {np.unique(codes[out_of_range]).tolist()}"
        )

    if _NUMBA_OK:
        acc, processed, pending = _flow_accumulation_kernel(
            codes, _DI_BY_CODE, _DJ_BY_CODE
        )
    else:
        row_idx, col_idx = np.indices((rows, cols))
        ni = row_idx + _DI_BY_CODE[codes]
        nj = col_idx + _DJ_BY_CODE[codes]
        routed = (codes > 0) & (ni >= 0) & (ni < rows) & (nj >= 0) & (nj < cols)

        downstream_r = np.where(routed, ni, -1)
        downstream_c = np.where(routed, nj, -1)

        flat_targets = ni[routed] * cols + nj[routed]
        pending = np.bincount(flat_targets, minlength=rows * cols).reshape(rows, cols)

        queue = deque(
            (int(i), int(j)) for i, j in zip(*np.nonzero(pending == 0), strict=True)
        )

        processed = 0
        while queue:
            i, j = queue.popleft()
            processed += 1
            target_r = downstream_r[i, j]
            if target_r < 0:
                continue
            target_c = int(downstream_c[i, j])
            acc[target_r, target_c] += acc[i, j]
            pending[target_r, target_c] -= 1
            if pending[target_r, target_c] == 0:
                queue.append((int(target_r), target_c))

    if processed < rows * cols:
        raise FlowCycleError(_cycle_message(flow_dir, dem, pending > 0))

    return acc


def _cycle_message(flow_dir: np.ndarray, dem: Any, stuck: np.ndarray) -> str:
    """Name the cells a cycle traps, with elevations when a DEM is available."""
    cells = np.argwhere(stuck)
    head = cells[0]
    parts = [
        f"flow direction grid contains a drainage cycle: {len(cells)} of "
        f"{flow_dir.size} cells never reached a topological order, "
        f"first at row {int(head[0])}, column {int(head[1])}"
    ]

    if dem is not None:
        grid = np.asarray(dem, dtype=float)
        if grid.shape == flow_dir.shape:
            elevations = grid[stuck & np.isfinite(grid)]
            if elevations.size:
                parts.append(
                    f"trapped elevations {float(elevations.min())}..{float(elevations.max())}"
                )

    named = [f"({int(r)}, {int(c)})={int(flow_dir[r, c])}" for r, c in cells[:5]]
    parts.append("trapped cells " + ", ".join(named))
    return "; ".join(parts)


@njit(cache=True)
def _strahler_one_pass(strahler, stream_mask, flow_dir, di_by_code, dj_by_code):
    """One relaxation sweep of the Strahler stream order.

    Bit-identical to the pure-Python double loop in :func:`strahler_order`.
    Stream-order values are non-negative integer-valued float64s, so the only
    arithmetic -- ``max_up + 1.0`` -- is exact; the max/count bookkeeping is a
    single pass that reproduces ``max(upstream_orders)`` and its tie count. The
    convergence test (``np.allclose``) stays outside the kernel, unchanged.
    """
    rows, cols = strahler.shape
    new_strahler = strahler.copy()
    for i in range(rows):
        for j in range(cols):
            if not stream_mask[i, j]:
                continue
            max_up = -1.0
            count_max = 0
            for code in range(1, 9):
                ni = i + di_by_code[code]
                nj = j + dj_by_code[code]
                if (ni >= 0) and (ni < rows) and (nj >= 0) and (nj < cols):
                    d_target = int(flow_dir[ni, nj])
                    if d_target > 0:
                        ti = ni + di_by_code[d_target]
                        tj = nj + dj_by_code[d_target]
                        if (ti == i) and (tj == j) and (strahler[ni, nj] > 0.0):
                            val = strahler[ni, nj]
                            if val > max_up:
                                max_up = val
                                count_max = 1
                            elif val == max_up:
                                count_max += 1
            if max_up < 0.0:
                new_strahler[i, j] = 1.0
            elif count_max >= 2:
                new_strahler[i, j] = max_up + 1.0
            else:
                new_strahler[i, j] = max_up
    return new_strahler


def strahler_order(flow_acc: Any, flow_dir: Any, threshold: float = 10.0) -> tuple[np.ndarray, int]:
    """
    محاسبه شماره ترتیب Strahler برای شبکه‌های آبری.

    خروجی: (آرایه ترتیب Strahler، حداکثر ترتیب)
    """
    flow_acc = np.asarray(flow_acc, dtype=float)
    flow_dir = np.asarray(flow_dir, dtype=float)
    rows, cols = flow_acc.shape
    strahler = np.zeros((rows, cols), dtype=np.float64)

    # شناسایی سلول‌های جریان > آستانه به عنوان "رودخانه"
    stream_mask = flow_acc >= threshold
    strahler[stream_mask] = 1.0  # اولیه: همه رودخانه‌ها سطح 1

    # محاسبه ترتیب Strahler به صورت تکراری
    # سلول سطح 1: بدون شاخه ورودی
    # اگر یکی به سلول وصل شود: سطح همان‌جا
    # اگر دو یا چند شاخه ورودی باشد: سطح + 1
    max_iter = 50
    for _ in range(max_iter):
        if _NUMBA_OK:
            new_strahler = _strahler_one_pass(
                strahler, stream_mask, flow_dir, _DI_BY_CODE, _DJ_BY_CODE
            )
        else:
            new_strahler = strahler.copy()
            for i in range(rows):
                for j in range(cols):
                    if not stream_mask[i, j]:
                        continue
                    # شناسایی همسایه‌های بالادست
                    upstream_orders = []
                    for _d, (di, dj) in DIR_OFFSETS.items():
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols:
                            # آیا این سلول به (i,j) جریان دارد؟
                            d_target = int(flow_dir[ni, nj])
                            if d_target > 0:
                                target_i, target_j = (
                                    ni + DIR_OFFSETS[d_target][0],
                                    nj + DIR_OFFSETS[d_target][1],
                                )
                                if (target_i, target_j) == (i, j) and strahler[ni, nj] > 0:
                                    upstream_orders.append(strahler[ni, nj])

                    if len(upstream_orders) == 0:
                        new_strahler[i, j] = 1.0
                    else:
                        max_up = max(upstream_orders)
                        count_max = sum(1 for o in upstream_orders if o == max_up)
                        if count_max >= 2:
                            new_strahler[i, j] = max_up + 1.0
                        else:
                            new_strahler[i, j] = max_up

        if np.allclose(new_strahler, strahler, equal_nan=True):
            break
        strahler = new_strahler

    max_order = int(np.nanmax(strahler)) if np.any(strahler > 0) else 1
    return strahler, max_order
