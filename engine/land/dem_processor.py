"""
DEM Processor
=============
Processes Digital Elevation Models for terrain analysis.
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DEMProcessor:
    """پردازشگر مدل ارتفاعی دیجیتال"""
    
    def __init__(self, dem_path: Optional[Path] = None):
        self.dem_path = dem_path
        self.dem_data: Optional[np.ndarray] = None
        self.resolution: Optional[float] = None
        self.nodata_value: Optional[float] = None
    
    def load_dem(self, dem_path: Path) -> None:
        """Load DEM from GeoTIFF file."""
        try:
            import rasterio
        except ImportError:
            raise ImportError("rasterio is required")
        
        with rasterio.open(dem_path) as src:
            self.dem_data = src.read(1)
            self.resolution = src.res[0]
            self.nodata_value = src.nodata
            if self.nodata_value is not None:
                self.dem_data = np.ma.masked_equal(self.dem_data, self.nodata_value)
        
        logger.info(f"Loaded DEM: {dem_path.name}, shape={self.dem_data.shape}")
    
    def load_from_array(self, dem_array: np.ndarray, resolution: float, nodata: Optional[float] = None) -> None:
        """Load DEM from numpy array."""
        self.dem_data = dem_array.copy()
        self.resolution = resolution
        self.nodata_value = nodata
        if nodata is not None:
            self.dem_data = np.ma.masked_equal(self.dem_data, nodata)
    
    def get_statistics(self) -> Dict[str, float]:
        """Compute DEM statistics."""
        if self.dem_data is None:
            raise ValueError("DEM not loaded")
        return {
            "min": float(np.nanmin(self.dem_data)),
            "max": float(np.nanmax(self.dem_data)),
            "mean": float(np.nanmean(self.dem_data)),
            "std": float(np.nanstd(self.dem_data)),
            "range": float(np.nanmax(self.dem_data) - np.nanmin(self.dem_data)),
        }
    
    def fill_voids(self, method: str = "interpolation") -> np.ndarray:
        """Fill voids in DEM."""
        if self.dem_data is None:
            raise ValueError("DEM not loaded")
        if not isinstance(self.dem_data, np.ma.MaskedArray):
            return self.dem_data.copy()
        
        try:
            from scipy.ndimage import generic_filter
        except ImportError:
            return self.dem_data.data.copy()
        
        filled = self.dem_data.data.copy()
        
        def fill_func(values):
            center = values[len(values) // 2]
            if np.ma.is_masked(center):
                valid = values[~np.ma.is_masked(values)]
                return np.mean(valid) if len(valid) > 0 else center
            return center
        
        filled = generic_filter(filled, fill_func, size=3, mode="nearest")
        return filled
    
    def resample(self, target_resolution: float) -> np.ndarray:
        """Resample DEM to target resolution."""
        if self.dem_data is None:
            raise ValueError("DEM not loaded")
        try:
            from scipy.ndimage import zoom
        except ImportError:
            raise ImportError("scipy required")
        
        scale = self.resolution / target_resolution
        return zoom(self.dem_data, scale, order=1)
