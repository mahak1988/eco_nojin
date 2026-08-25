import numpy as np
import rasterio
from rasterio.windows import Window
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DEMProcessor:
    """
    A class to handle Digital Elevation Model (DEM) processing tasks.
    It loads DEM data and provides methods to extract topographical metrics.
    """

    def __init__(self, dem_file_path: str):
        """
        Initializes the DEMProcessor with a path to the DEM file.

        Args:
            dem_file_path: Path to the DEM file (GeoTIFF format).
        """
        self.dem_file_path = dem_file_path
        self._dataset = None
        self._data = None

    def load_dem(self):
        """
        Loads the DEM data from the specified file path.
        """
        try:
            with rasterio.open(self.dem_file_path) as dataset:
                self._dataset = dataset
                self._data = dataset.read(1)  # Read the first band (elevation values)
                logger.info(f"DEM loaded successfully from {self.dem_file_path}. Shape: {self._data.shape}")
        except Exception as e:
            logger.error(f"Error loading DEM from {self.dem_file_path}: {e}")
            raise

    def get_elevation_stats(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calculates basic statistics (min, max, mean) of the elevation data.

        Returns:
            A tuple containing (min, max, mean) elevation values.
        """
        if self._data is None:
            logger.warning("DEM data not loaded. Call load_dem() first.")
            return None, None, None

        # Mask out nodata values if present
        masked_data = np.ma.masked_equal(self._data, self._dataset.nodata)
        
        min_val = float(masked_data.min()) if masked_data.min() is not np.ma.masked else None
        max_val = float(masked_data.max()) if masked_data.max() is not np.ma.masked else None
        mean_val = float(masked_data.mean()) if masked_data.mean() is not np.ma.masked else None
        
        return min_val, max_val, mean_val

    def get_window_data(self, row_start: int, col_start: int, height: int, width: int) -> np.ndarray:
        """
        Extracts a window of data from the DEM.

        Args:
            row_start: Starting row index.
            col_start: Starting column index.
            height: Height of the window.
            width: Width of the window.

        Returns:
            A numpy array representing the window of data.
        """
        if self._data is None:
            logger.warning("DEM data not loaded. Call load_dem() first.")
            return np.array([])
            
        window = Window(col_start, row_start, width, height)
        with rasterio.open(self.dem_file_path) as dataset:
            window_data = dataset.read(1, window=window)
        return window_data

    @property
    def shape(self) -> Tuple[int, int]:
        """Returns the shape of the loaded DEM data."""
        if self._data is None:
            return (0, 0)
        return self._data.shape

    @property
    def crs(self):
        """Returns the Coordinate Reference System of the DEM."""
        if self._dataset is None:
            return None
        return self._dataset.crs

    @property
    def transform(self):
        """Returns the Affine transformation of the DEM."""
        if self._dataset is None:
            return None
        return self._dataset.transform
