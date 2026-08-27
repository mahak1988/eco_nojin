import logging

import numpy as np

from .dem_processor import DEMProcessor

logger = logging.getLogger(__name__)


def calculate_slope_aspect(dem_data: np.ndarray, cell_size_x: float, cell_size_y: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculates slope and aspect from DEM data using a 3x3 neighborhood method.

    Args:
        dem_data: A 2D numpy array of elevation values.
        cell_size_x: Ground distance between cell centers in the x-direction.
        cell_size_y: Ground distance between cell centers in the y-direction.

    Returns:
        A tuple containing two 2D numpy arrays: (slope_degrees, aspect_degrees).
                 Slope and aspect are calculated for the interior cells.
                 Border cells (first/last row/column) are filled with NaN.
    """
    rows, cols = dem_data.shape
    slope_radians = np.full_like(dem_data, np.nan, dtype=np.float64)
    aspect_radians = np.full_like(dem_data, np.nan, dtype=np.float64)

    # Calculate slope and aspect for interior cells only (1:-1)
    z1 = dem_data[2:, :-2]  # z(i-1, j-1)
    z2 = dem_data[2:, 1:-1] # z(i-1, j)
    z3 = dem_data[2:, 2:]   # z(i-1, j+1)
    z4 = dem_data[1:-1, :-2] # z(i, j-1)
    z5 = dem_data[1:-1, 2:]  # z(i, j+1)
    z6 = dem_data[:-2, :-2]  # z(i+1, j-1)
    z7 = dem_data[:-2, 1:-1] # z(i+1, j)
    z8 = dem_data[:-2, 2:]   # z(i+1, j+1)

    # Partial derivatives dx (dz/dx) and dy (dz/dy) using central differences
    dz_dx = (z5 - z4) / (2 * cell_size_x)
    dz_dy = (z2 - z7) / (2 * cell_size_y)

    # Calculate slope in radians and convert to degrees
    slope_radians[1:-1, 1:-1] = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_degrees = np.degrees(slope_radians)

    # Calculate aspect in radians and convert to degrees
    aspect_radians[1:-1, 1:-1] = np.arctan2(-dz_dy, dz_dx)
    aspect_degrees = np.degrees(aspect_radians)

    # Handle aspect to be 0-360 degrees
    aspect_degrees = (aspect_degrees + 360) % 360

    return slope_degrees, aspect_degrees


class SlopeAspectAnalyzer:
    """
    A class to analyze slope and aspect from a DEMProcessor instance.
    """

    def __init__(self, dem_processor: DEMProcessor):
        """
        Initializes the analyzer with a DEMProcessor.

        Args:
            dem_processor: An instance of DEMProcessor that has loaded data.
        """
        self.dem_proc = dem_processor
        if self.dem_proc._data is None:
            raise ValueError("DEMProcessor must have loaded data before initializing SlopeAspectAnalyzer.")

    def analyze(self, cell_size_meters: float = 30.0) -> tuple[np.ndarray, np.ndarray, float, float]:
        """
        Performs the slope and aspect analysis on the loaded DEM.

        Args:
            cell_size_meters: The ground resolution of the DEM pixels in meters.
                              Assumes square pixels for simplicity.

        Returns:
            A tuple containing (slope_array, aspect_array, mean_slope, dominant_aspect).
        """
        if self.dem_proc._data is None:
            logger.error("DEM data is not loaded in the processor.")
            return np.array([]), np.array([]), 0.0, 0.0

        logger.info("Starting slope and aspect calculation...")
        slope_arr, aspect_arr = calculate_slope_aspect(
            self.dem_proc._data, cell_size_meters, cell_size_meters
        )

        # Calculate mean slope (ignoring NaN values)
        mean_slope = float(np.nanmean(slope_arr)) if not np.all(np.isnan(slope_arr)) else 0.0

        # Calculate dominant aspect (mode of non-NaN values)
        flat_asp = aspect_arr.flatten()
        flat_asp = flat_asp[~np.isnan(flat_asp)]
        dominant_aspect = 0.0
        if len(flat_asp) > 0:
            # Simple binning to find mode
            bins = np.arange(0, 361, 45)  # 8 directions: N, NE, E, SE, S, SW, W, NW
            hist, _ = np.histogram(flat_asp, bins=bins)
            dominant_bin_idx = np.argmax(hist)
            dominant_aspect = float(bins[dominant_bin_idx] + 22.5) # Center of the bin

        logger.info("Slope and aspect calculation completed.")
        return slope_arr, aspect_arr, mean_slope, dominant_aspect
