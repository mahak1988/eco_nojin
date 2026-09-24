"""Surface Water Analysis (vectorized with NumPy)."""

import logging
from typing import Any

import numpy as np

from .dem_processor import DEMProcessor

logger = logging.getLogger(__name__)

# D8 direction offsets: 1=N, 2=NE, 3=E, 4=SE, 5=S, 6=SW, 7=W, 8=NW
_DIR_OFFSETS = {
    1: (-1, 0),
    2: (-1, 1),
    3: (0, 1),
    4: (1, 1),
    5: (1, 0),
    6: (1, -1),
    7: (0, -1),
    8: (-1, -1),
}
_CARDINAL_DIRS = {1, 3, 5, 7}


class SurfaceWaterAnalyzer:
    """
    A class to analyze surface water sources based on DEM and other geographical data.

    Uses vectorized NumPy operations for performance.
    """

    def __init__(self, dem_processor: DEMProcessor):
        self.dem_proc = dem_processor
        if self.dem_proc._data is None:
            raise ValueError(
                "DEMProcessor must have loaded data before initializing SurfaceWaterAnalyzer."
            )

    def identify_flow_accumulation(self) -> np.ndarray:
        """
        Identifies areas of high flow accumulation using D8 algorithm
        with vectorized NumPy operations.

        Returns:
            A 2D numpy array representing flow accumulation (number of
            upslope cells draining into each cell).
        """
        logger.info("Identifying flow accumulation zones...")
        dem_data = self.dem_proc._data
        if dem_data is None:
            logger.error("DEM data is not loaded.")
            return np.array([])

        _rows, _cols = dem_data.shape
        flow_dir = self._calculate_d8_flow_direction(dem_data)
        flow_acc = self._calculate_d8_flow_accumulation(flow_dir)

        logger.info("Flow accumulation identification completed.")
        return flow_acc

    def _calculate_d8_flow_direction(self, dem: np.ndarray) -> np.ndarray:
        """
        Vectorized D8 flow direction calculation.

        Returns float codes 1-8 for cardinal/diagonal flow; 0 for pits/borders.
        """
        rows, cols = dem.shape
        flow_dir = np.zeros((rows, cols), dtype=np.float64)

        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center = dem[i, j]
                if not np.isfinite(center):
                    continue

                neighbors = np.array(
                    [
                        dem[i - 1, j - 1],
                        dem[i - 1, j],
                        dem[i - 1, j + 1],
                        dem[i, j - 1],
                        dem[i, j + 1],
                        dem[i + 1, j - 1],
                        dem[i + 1, j],
                        dem[i + 1, j + 1],
                    ]
                )
                directions = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=float)

                valid_mask = np.isfinite(neighbors) & (neighbors < center)
                if not np.any(valid_mask):
                    continue

                dists = np.where(np.isin(directions, list(_CARDINAL_DIRS)), 1.0, np.sqrt(2))
                slopes = np.where(valid_mask, (center - neighbors) / dists, -np.inf)
                best_idx = int(np.argmax(slopes))
                flow_dir[i, j] = directions[best_idx]

        return flow_dir

    def _calculate_d8_flow_accumulation(self, flow_dir: np.ndarray) -> np.ndarray:
        """
        D8 flow accumulation using topological ordering (iterative).

        Each cell starts with 1 and accumulates flow from upstream cells.
        """
        rows, cols = flow_dir.shape
        acc = np.ones((rows, cols), dtype=np.float64)

        downstream = np.full((rows, cols, 2), -1, dtype=np.int32)
        upstream_count = np.zeros((rows, cols), dtype=np.int32)

        for i in range(rows):
            for j in range(cols):
                d = int(flow_dir[i, j])
                if d == 0:
                    continue
                di, dj = _DIR_OFFSETS[d]
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    downstream[i, j, 0] = ni
                    downstream[i, j, 1] = nj
                    upstream_count[ni, nj] += 1

        from collections import deque

        queue = deque()
        for i in range(rows):
            for j in range(cols):
                if upstream_count[i, j] == 0:
                    queue.append((i, j))

        while queue:
            i, j = queue.popleft()
            ni, nj = int(downstream[i, j, 0]), int(downstream[i, j, 1])
            if 0 <= ni < rows and 0 <= nj < cols:
                acc[ni, nj] += acc[i, j]
                upstream_count[ni, nj] -= 1
                if upstream_count[ni, nj] == 0:
                    queue.append((ni, nj))

        return acc

    def analyze_surface_water_potential(
        self, flow_threshold: float | None = None
    ) -> dict[str, Any]:
        """
        Analyzes potential surface water sources based on DEM and flow accumulation.

        Uses D8 flow accumulation to identify stream networks.

        Args:
            flow_threshold: Threshold on flow accumulation to determine stream
                           cells. If None, auto-calculated based on 85th percentile
                           of the flow accumulation distribution.

        Returns:
            A dictionary containing analysis results.
        """
        logger.info("Analyzing surface water potential...")
        dem_data = self.dem_proc._data

        if dem_data is None:
            logger.error("Could not calculate flow accumulation.")
            return {}

        rows, cols = dem_data.shape

        # Calculate flow accumulation
        flow_acc = self.identify_flow_accumulation()

        # Auto-calculate threshold if not provided
        if flow_threshold is None:
            valid_acc = flow_acc[flow_acc > 0]
            flow_threshold = float(np.percentile(valid_acc, 85)) if len(valid_acc) > 0 else 10.0

        # Identify potential watercourse pixels
        watercourse_mask = flow_acc >= flow_threshold
        watercourse_indices = np.where(watercourse_mask)

        # Collect locations with coordinates
        locations = []
        for r, c in zip(watercourse_indices[0], watercourse_indices[1], strict=False):
            if self.dem_proc._dataset:
                x, y = self.dem_proc._dataset.xy(r, c)
                locations.append(
                    {
                        "row": int(r),
                        "col": int(c),
                        "longitude": float(x),
                        "latitude": float(y),
                        "flow_accumulation": float(flow_acc[r, c]),
                    }
                )

        # Calculate drainage density
        cell_area_km2 = (
            (self._get_cell_size() ** 2) / 1e6 if hasattr(self, "_get_cell_size") else 0.0
        )
        if cell_area_km2 <= 0 and self.dem_proc._dataset:
            cell_area_km2 = (self.dem_proc._dataset.res[0] * self.dem_proc._dataset.res[1]) / 1e6

        watershed_area_km2 = float(np.sum(np.isfinite(dem_data))) * cell_area_km2
        if watershed_area_km2 <= 0:
            watershed_area_km2 = (
                (rows * cols * resolution**2) / 1e6 if hasattr(self, "resolution") else 1.0
            )

        stream_length_km = (
            float(np.sum(watercourse_mask)) * self._get_cell_size() / 1000.0
            if hasattr(self, "_get_cell_size")
            else 0.0
        )
        if stream_length_km == 0 and self.dem_proc._dataset:
            cell_size = self.dem_proc._dataset.res[0] if self.dem_proc._dataset.res else 30.0
            stream_length_km = float(np.sum(watercourse_mask)) * cell_size / 1000.0

        drainage_density = (
            stream_length_km / max(watershed_area_km2, 0.001) if watershed_area_km2 > 0 else 0.0
        )

        # Flow statistics
        valid_acc = flow_acc[flow_acc > 0]
        if len(valid_acc) > 0:
            max_flow_acc = float(np.max(valid_acc))
            mean_flow_acc = float(np.mean(valid_acc))
        else:
            max_flow_acc = 0.0
            mean_flow_acc = 0.0

        # Quality class based on flow accumulation patterns
        if mean_flow_acc > 100:
            quality_class = "High"
        elif mean_flow_acc > 50:
            quality_class = "Moderate"
        elif mean_flow_acc > 10:
            quality_class = "Potential"
        else:
            quality_class = "Low"

        analysis_results = {
            "count_of_potential_sources": len(locations),
            "locations": locations,
            "flow_accumulation": flow_acc.tolist(),
            "flow_accumulation_max": round(max_flow_acc, 2),
            "flow_accumulation_mean": round(mean_flow_acc, 2),
            "drainage_density_km_km2": round(drainage_density, 2),
            "watershed_area_km2": round(watershed_area_km2, 4),
            "stream_length_km": round(stream_length_km, 2),
            "quality_class": quality_class,
            "method": "D8_flow_accumulation",
            "parameters": {
                "threshold": round(flow_threshold, 2),
                "cell_size_m": self._get_cell_size() if hasattr(self, "_get_cell_size") else 30.0,
            },
        }

        logger.info(f"Surface water analysis completed. Found {len(locations)} potential sources.")
        return analysis_results

    def _get_cell_size(self) -> float:
        """Get cell size from DEM dataset, defaulting to 30m."""
        if self.dem_proc._dataset:
            res = self.dem_proc._dataset.res
            if res:
                return float(res[0]) if isinstance(res, (tuple, list)) else float(res)
        return 30.0
