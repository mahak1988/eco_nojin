"""
Enhanced Drainage Analysis
==========================

Advanced hydrological analysis including:
- D8 flow direction algorithm
- Flow accumulation calculation
- Strahler stream ordering (Strahler, 1957)
- Horton's bifurcation ratio
- Drainage density classification
- Time of concentration (Kirpich equation)
- Drainage pattern classification

References:
- Strahler, A.N. (1957) "Quantitative analysis of watershed geomorphology"
- Horton, R.E. (1945) "Erosional development of streams"
- Kirpich, P.A. (1940) "Time of concentration of small agricultural watersheds"
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import logging

from .models import (
    DrainageAnalysis, DrainagePattern, DrainageDensityClass, StreamOrder
)

logger = logging.getLogger(__name__)


class DrainageAnalyzer:
    """تحلیل‌گر پیشرفته زهکشی با محاسبات Strahler و Horton"""

    # Drainage density thresholds (km/km²) - Chorley (1969)
    DENSITY_CLASSES = {
        DrainageDensityClass.VERY_LOW: (0, 2),
        DrainageDensityClass.LOW: (2, 5),
        DrainageDensityClass.MODERATE: (5, 15),
        DrainageDensityClass.HIGH: (15, 30),
        DrainageDensityClass.VERY_HIGH: (30, float("inf")),
    }

    # D8 direction encoding: (di, dj, direction_code)
    D8_DIRECTIONS = [
        (0, 1, 1),     # E
        (1, 1, 2),     # SE
        (1, 0, 4),     # S
        (1, -1, 8),    # SW
        (0, -1, 16),   # W
        (-1, -1, 32),  # NW
        (-1, 0, 64),   # N
        (-1, 1, 128),  # NE
    ]

    def __init__(self, resolution: float):
        """
        Args:
            resolution: DEM cell size in meters
        """
        self.resolution = resolution

    def analyze(
        self,
        dem: np.ndarray,
        profile_id: str = "",
        area_km2: Optional[float] = None
    ) -> DrainageAnalysis:
        """
        Comprehensive drainage analysis.

        Returns full DrainageAnalysis with Strahler ordering,
        bifurcation ratios, and Kirpich time of concentration.
        """
        logger.info(f"Starting drainage analysis for profile: {profile_id}")

        # 1. Flow direction (D8)
        flow_dir = self._calculate_flow_direction(dem)

        # 2. Flow accumulation
        accumulation = self._calculate_flow_accumulation(flow_dir)

        # 3. Extract stream network (adaptive threshold)
        threshold = max(100, int(accumulation.max() * 0.01))
        streams = accumulation >= threshold

        # 4. Watershed area
        if area_km2 is None:
            area_km2 = (dem.size * self.resolution ** 2) / 1e6

        # 5. Drainage density
        density = self._calculate_drainage_density(streams, area_km2)
        density_class = self._classify_density(density)

        # 6. Strahler stream ordering
        stream_orders = self._calculate_strahler_order(streams, flow_dir)
        max_order = max((s.order for s in stream_orders), default=0)

        # 7. Horton's bifurcation ratio
        bifurcation = self._calculate_bifurcation_ratio(stream_orders)

        # 8. Drainage pattern classification
        pattern = self._classify_pattern(streams, dem)

        # 9. Main channel length & time of concentration
        main_channel_length = self._estimate_main_channel(streams)
        mean_slope = np.nanmean(self._calculate_slope_degrees(dem))
        tc_hours = self._calculate_time_of_concentration(
            main_channel_length, mean_slope
        )

        analysis = DrainageAnalysis(
            profile_id=profile_id,
            drainage_pattern=pattern,
            drainage_density=density,
            density_class=density_class,
            stream_orders=stream_orders,
            stream_order_max=max_order if max_order > 0 else None,
            bifurcation_ratio=bifurcation,
            flow_accumulation={
                "max": int(accumulation.max()),
                "mean": float(accumulation.mean()),
                "threshold_cells": threshold,
            },
            watershed_area_km2=area_km2,
            time_of_concentration_hours=tc_hours,
            main_channel_length_km=main_channel_length,
            analyzed_at=datetime.now(timezone.utc),
        )

        logger.info(
            f"Drainage analysis complete: pattern={pattern}, "
            f"density={density:.2f} km/km², max_order={max_order}"
        )
        return analysis

    # ------------------------------------------------------------------
    # D8 Flow Direction
    # ------------------------------------------------------------------
    def _calculate_flow_direction(self, dem: np.ndarray) -> np.ndarray:
        """D8 algorithm: flow toward steepest downslope neighbor."""
        rows, cols = dem.shape
        flow_dir = np.zeros_like(dem, dtype=np.int16)  # D8 codes: 1-128

        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center = dem[i, j]
                min_drop = 0
                min_dir = 0

                for di, dj, direction in self.D8_DIRECTIONS:
                    ni, nj = i + di, j + dj
                    neighbor = dem[ni, nj]
                    drop = center - neighbor

                    # Distance correction for diagonal neighbors
                    if abs(di) + abs(dj) == 2:
                        drop /= np.sqrt(2)

                    if drop > min_drop:
                        min_drop = drop
                        min_dir = direction

                flow_dir[i, j] = min_dir

        return flow_dir

    # ------------------------------------------------------------------
    # Flow Accumulation
    # ------------------------------------------------------------------
    def _calculate_flow_accumulation(self, flow_dir: np.ndarray) -> np.ndarray:
        """Iterative downstream accumulation of flow."""
        rows, cols = flow_dir.shape
        accumulation = np.ones_like(flow_dir, dtype=np.int32)

        # Iterate until convergence (max: grid diagonal)
        max_iter = rows + cols
        for _ in range(max_iter):
            new_acc = accumulation.copy()
            changed = False

            for i in range(rows):
                for j in range(cols):
                    if flow_dir[i, j] == 0:
                        continue
                    ni, nj = self._get_downstream(i, j, flow_dir[i, j])
                    if 0 <= ni < rows and 0 <= nj < cols:
                        new_acc[ni, nj] += accumulation[i, j]
                        changed = True

            if not changed or np.array_equal(new_acc, accumulation):
                break
            accumulation = new_acc

        return accumulation

    def _get_downstream(self, i: int, j: int, direction: int) -> Tuple[int, int]:
        """Get downstream cell coordinates from D8 code."""
        direction_map = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }
        di, dj = direction_map.get(direction, (0, 0))
        return i + di, j + dj

    # ------------------------------------------------------------------
    # Drainage Density
    # ------------------------------------------------------------------
    def _calculate_drainage_density(
        self, streams: np.ndarray, area_km2: float
    ) -> float:
        """
        Calculate drainage density Dd = ΣL / A (km/km²)

        Stream length approximated as:
        - cardinal neighbors: resolution meters
        - diagonal neighbors: resolution * √2 meters
        """
        if area_km2 <= 0:
            return 0.0

        # Count stream cells (each contributes ~resolution meters)
        stream_cells = int(np.sum(streams))
        # Average: ~70% cardinal, ~30% diagonal contribution
        stream_length_km = (
            stream_cells * self.resolution * 1.15  # empirical factor
        ) / 1000
        return stream_length_km / area_km2

    def _classify_density(self, density: float) -> DrainageDensityClass:
        """Classify drainage density per Chorley thresholds."""
        for cls, (low, high) in self.DENSITY_CLASSES.items():
            if low <= density < high:
                return cls
        return DrainageDensityClass.VERY_HIGH

    # ------------------------------------------------------------------
    # Strahler Stream Ordering
    # ------------------------------------------------------------------
    def _calculate_strahler_order(
        self, streams: np.ndarray, flow_dir: np.ndarray
    ) -> List[StreamOrder]:
        """
        Calculate Strahler stream orders.

        Algorithm (Strahler, 1957):
        - Headwater streams: order 1
        - Two streams of same order merge → order + 1
        - Different orders merge → higher order continues
        """
        rows, cols = streams.shape
        order_grid = np.zeros_like(streams, dtype=np.int8)

        # Initialize: headwater cells (streams with no upstream)
        upstream_count = self._count_upstream(streams, flow_dir)
        headwaters = streams & (upstream_count == 0)
        order_grid[headwaters] = 1

        # Iteratively assign orders following flow direction
        max_iter = rows + cols
        for _ in range(max_iter):
            changed = False
            for i in range(rows):
                for j in range(cols):
                    if not streams[i, j] or order_grid[i, j] > 0:
                        continue

                    # Get upstream orders
                    upstream_orders = self._get_upstream_orders(
                        i, j, order_grid, flow_dir
                    )

                    if not upstream_orders:
                        continue

                    if max(upstream_orders) == 0:
                        continue

                    # Strahler rule
                    max_order = max(upstream_orders)
                    count_max = upstream_orders.count(max_order)

                    if count_max >= 2:
                        order_grid[i, j] = max_order + 1
                    else:
                        order_grid[i, j] = max_order
                    changed = True

            if not changed:
                break

        # Aggregate statistics
        return self._aggregate_stream_orders(order_grid, streams)

    def _count_upstream(
        self, streams: np.ndarray, flow_dir: np.ndarray
    ) -> np.ndarray:
        """Count upstream cells for each cell."""
        rows, cols = streams.shape
        count = np.zeros_like(streams, dtype=np.int8)

        for i in range(rows):
            for j in range(cols):
                if not streams[i, j] or flow_dir[i, j] == 0:
                    continue
                ni, nj = self._get_downstream(i, j, flow_dir[i, j])
                if 0 <= ni < rows and 0 <= nj < cols and streams[ni, nj]:
                    count[ni, nj] += 1

        return count

    def _get_upstream_orders(
        self,
        i: int,
        j: int,
        order_grid: np.ndarray,
        flow_dir: np.ndarray,
    ) -> List[int]:
        """Get orders of all upstream cells flowing into (i, j)."""
        orders = []
        rows, cols = order_grid.shape

        for di, dj, _ in self.D8_DIRECTIONS:
            ni, nj = i + di, j + dj
            if 0 <= ni < rows and 0 <= nj < cols:
                # Check if (ni, nj) flows into (i, j)
                expected_downstream = self._get_downstream(ni, nj, flow_dir[ni, nj])
                if expected_downstream == (i, j) and order_grid[ni, nj] > 0:
                    orders.append(int(order_grid[ni, nj]))

        return orders

    def _aggregate_stream_orders(
        self, order_grid: np.ndarray, streams: np.ndarray
    ) -> List[StreamOrder]:
        """Aggregate Strahler orders into StreamOrder objects."""
        if not np.any(streams):
            return []

        orders = []
        max_order = int(order_grid.max()) if order_grid.max() > 0 else 0

        for order in range(1, max_order + 1):
            mask = order_grid == order
            count = int(np.sum(mask))
            if count == 0:
                continue

            length_km = count * self.resolution * 1.15 / 1000
            orders.append(StreamOrder(
                order=order,
                count=count,
                length_km=round(length_km, 3),
            ))

        return orders

    # ------------------------------------------------------------------
    # Horton Bifurcation Ratio
    # ------------------------------------------------------------------
    def _calculate_bifurcation_ratio(
        self, orders: List[StreamOrder]
    ) -> Optional[float]:
        """
        Calculate mean bifurcation ratio Rb (Horton, 1945).

        Rb = Nu / Nu+1  (number of streams of order u divided by u+1)
        Typical values: 3.0 - 5.0 for natural watersheds
        """
        if len(orders) < 2:
            return None

        ratios = []
        orders_dict = {o.order: o.count for o in orders}
        max_order = max(orders_dict.keys())

        for u in range(1, max_order):
            nu = orders_dict.get(u, 0)
            nu_plus_1 = orders_dict.get(u + 1, 0)
            if nu_plus_1 > 0:
                ratios.append(nu / nu_plus_1)

        return float(np.mean(ratios)) if ratios else None

    # ------------------------------------------------------------------
    # Drainage Pattern Classification
    # ------------------------------------------------------------------
    def _classify_pattern(
        self, streams: np.ndarray, dem: np.ndarray
    ) -> DrainagePattern:
        """
        Classify drainage pattern based on geology and slope indicators.

        Heuristic based on:
        - Slope variance (uniform → dendritic, varied → rectangular)
        - Stream directionality
        - Stream network geometry
        """
        slope_deg = self._calculate_slope_degrees(dem)
        slope_std = np.nanstd(slope_deg)
        slope_mean = np.nanmean(slope_deg)

        # Stream directionality
        dir_ratio = self._calculate_directionality(streams)

        # Classification rules (empirical)
        if slope_std < 3 and dir_ratio > 0.6:
            return DrainagePattern.PARALLEL
        elif slope_std < 5:
            return DrainagePattern.DENDRITIC
        elif slope_std > 15:
            return DrainagePattern.RECTANGULAR
        elif slope_mean > 20 and dir_ratio < 0.4:
            return DrainagePattern.RADIAL
        elif 5 <= slope_std <= 15:
            return DrainagePattern.TRELLIS
        else:
            return DrainagePattern.DENDRITIC

    def _calculate_directionality(self, streams: np.ndarray) -> float:
        """Calculate flow direction consistency (0=random, 1=uniform)."""
        if not np.any(streams):
            return 0.0

        # Simple metric: ratio of dominant flow direction
        # Using gradient orientation approximation
        dy, dx = np.gradient(streams.astype(float))
        angles = np.arctan2(dy, dx)
        angles = angles[streams]

        if len(angles) == 0:
            return 0.0

        # Bin into 8 directions
        bins = np.histogram(angles, bins=8)[0]
        max_bin = bins.max()
        total = bins.sum()

        return float(max_bin / total) if total > 0 else 0.0

    # ------------------------------------------------------------------
    # Slope & Channel Calculations
    # ------------------------------------------------------------------
    def _calculate_slope_degrees(self, dem: np.ndarray) -> np.ndarray:
        """Calculate slope in degrees."""
        dy, dx = np.gradient(dem, self.resolution)
        return np.degrees(np.arctan(np.sqrt(dx ** 2 + dy ** 2)))

    def _estimate_main_channel(self, streams: np.ndarray) -> float:
        """Estimate main channel length (longest connected path) in km."""
        stream_cells = int(np.sum(streams))
        # Main channel typically 30-50% of total stream length
        total_length_km = stream_cells * self.resolution * 1.15 / 1000
        main_channel = total_length_km * 0.4  # empirical factor
        return round(main_channel, 3)

    def _calculate_time_of_concentration(
        self, length_km: float, slope_deg: float
    ) -> float:
        """
        Kirpich equation (1940) for time of concentration.

        tc (minutes) = 0.01947 * L^0.77 * S^-0.385
        where L = channel length (m), S = slope (m/m)

        Returns: time in hours
        """
        if length_km <= 0 or slope_deg <= 0:
            return 0.0

        length_m = length_km * 1000
        slope_pct = np.tan(np.radians(slope_deg)) * 100

        if slope_pct <= 0:
            return 0.0

        tc_min = 0.01947 * (length_m ** 0.77) * (slope_pct ** -0.385)
        return round(tc_min / 60, 3)  # convert to hours
