import numpy as np
from typing import Dict, Any, Optional
import logging
from .dem_processor import DEMProcessor # استفاده از ماژول موجود

logger = logging.getLogger(__name__)

class SurfaceWaterAnalyzer:
    """
    A class to analyze surface water sources based on DEM and other geographical data.
    """

    def __init__(self, dem_processor: DEMProcessor):
        """
        Initializes the analyzer with a DEMProcessor.

        Args:
            dem_processor: An instance of DEMProcessor that has loaded data.
        """
        self.dem_proc = dem_processor
        if self.dem_proc._data is None:
            raise ValueError("DEMProcessor must have loaded data before initializing SurfaceWaterAnalyzer.")

    def identify_flow_accumulation(self) -> np.ndarray:
        """
        Identifies areas of high flow accumulation, indicating potential streams/rivers.
        This is a simplified approach using local neighborhood analysis.
        A full implementation would require a proper flow routing algorithm like D8.

        Returns:
            A 2D numpy array representing a crude flow accumulation index.
        """
        logger.info("Identifying flow accumulation zones...")
        dem_data = self.dem_proc._data
        if dem_data is None:
            logger.error("DEM data is not loaded.")
            return np.array([])

        # Create a simple flow accumulation proxy
        # Find cells with lower neighbors (potential sinks/confluences)
        rows, cols = dem_data.shape
        flow_acc = np.zeros_like(dem_data, dtype=float)

        # This is a very basic and inefficient placeholder.
        # A real algorithm like D8 would be significantly more complex.
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center_cell = dem_data[i, j]
                neighbors = [
                    dem_data[i-1, j-1], dem_data[i-1, j], dem_data[i-1, j+1],
                    dem_data[i, j-1],                     dem_data[i, j+1],
                    dem_data[i+1, j-1], dem_data[i+1, j], dem_data[i+1, j+1]
                ]
                # Count how many neighbors are higher (potential inflow)
                higher_neighbors = sum(1 for n in neighbors if n > center_cell)
                flow_acc[i, j] = higher_neighbors

        logger.info("Flow accumulation identification completed.")
        return flow_acc

    def analyze_surface_water_potential(self, flow_threshold: float = 3.0) -> Dict[str, Any]:
        """
        Analyzes potential surface water sources based on DEM and flow accumulation.

        Args:
            flow_threshold: A threshold value on the flow accumulation proxy
                            to determine if a cell is part of a watercourse.

        Returns:
            A dictionary containing analysis results like location and quality estimates.
        """
        logger.info("Analyzing surface water potential...")
        flow_acc = self.identify_flow_accumulation()

        if flow_acc.size == 0:
            logger.error("Could not calculate flow accumulation.")
            return {}

        # Identify potential watercourse pixels
        watercourse_mask = flow_acc >= flow_threshold
        watercourse_indices = np.where(watercourse_mask)

        locations = []
        for r, c in zip(watercourse_indices[0], watercourse_indices[1]):
            # Convert pixel indices to geographic coordinates using transform
            if self.dem_proc._dataset:
                x, y = self.dem_proc._dataset.xy(r, c)
                locations.append({"row": r, "col": c, "longitude": x, "latitude": y})

        analysis_results = {
            "count_of_potential_sources": len(locations),
            "locations": locations,
            "flow_accumulation_matrix": flow_acc.tolist(), # برای سادگی، به لیست تبدیل می‌شود
            "quality_class": "Potential", # Class based on DEM analysis
            "method": "DEM_based_flow_proxy",
            "parameters": {"threshold": flow_threshold}
        }

        logger.info(f"Surface water analysis completed. Found {len(locations)} potential sources.")
        return analysis_results