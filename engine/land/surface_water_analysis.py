"""Surface Water Analysis (vectorized with NumPy)."""

import logging
from typing import Any

import numpy as np

from .dem_processor import DEMProcessor
from .hydrology import flow_accumulation, flow_direction

logger = logging.getLogger(__name__)

# The D8 scan, the direction-code table (1=N, 2=NE, 3=E, 4=SE, 5=S, 6=SW,
# 7=W, 8=NW) and the topological accumulation live in engine.land.hydrology.
# The copies this module carried scanned the 3x3 window in row-major order and
# labelled the positions 1..8, which is not the same permutation as the code
# table, so the codes this module produced did not mean what they said.


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
        flow_acc = self._calculate_d8_flow_accumulation(flow_dir, dem_data)

        logger.info("Flow accumulation identification completed.")
        return flow_acc

    def _calculate_d8_flow_direction(self, dem: np.ndarray) -> np.ndarray:
        """
        D8 flow direction by steepest descent.

        Returns float codes 1-8 (1=N, 2=NE, 3=E, 4=SE, 5=S, 6=SW, 7=W,
        8=NW, clockwise from north); 0 for pits and borders.
        """
        return flow_direction(dem)

    def _calculate_d8_flow_accumulation(
        self, flow_dir: np.ndarray, dem: np.ndarray | None = None
    ) -> np.ndarray:
        """
        D8 flow accumulation in topological order.

        Each cell starts with 1 and accumulates flow from upstream cells. A
        drainage cycle has no topological order, so it raises FlowCycleError
        rather than returning a truncated accumulation.
        """
        return flow_accumulation(flow_dir, dem)

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
