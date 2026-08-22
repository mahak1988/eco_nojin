"""
Enhanced Slope and Aspect Calculator
====================================
Calculates slope, aspect, and classifications per USDA/FAO standards.
Includes 7-class slope system, curvature, TWI, TPI, and landform classification.
"""

import numpy as np
from typing import Tuple, Optional, Dict
import logging
from .models import SlopeClass, LandformType

logger = logging.getLogger(__name__)


class SlopeAspectCalculator:
    """محاسبه‌گر شیب و جهت شیب با طبقه‌بندی‌های استاندارد"""
    
    # USDA Slope Classes (% slope)
    USDA_CLASSES = {
        SlopeClass.CLASS_0: (0, 1),
        SlopeClass.CLASS_1: (1, 3),
        SlopeClass.CLASS_2: (3, 8),
        SlopeClass.CLASS_3: (8, 15),
        SlopeClass.CLASS_4: (15, 25),
        SlopeClass.CLASS_5: (25, 45),
        SlopeClass.CLASS_6: (45, float("inf")),
    }
    
    def __init__(self, resolution: float):
        self.resolution = resolution
    
    def calculate_slope_aspect(self, dem: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate slope (degrees) and aspect (degrees)."""
        dy, dx = np.gradient(dem, self.resolution)
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad)
        
        aspect_rad = np.arctan2(-dx, dy)
        aspect_deg = np.degrees(aspect_rad)
        aspect_deg = np.mod(aspect_deg + 360, 360)
        
        return slope_deg, aspect_deg
    
    def slope_to_percent(self, slope_degrees: np.ndarray) -> np.ndarray:
        """Convert slope degrees to percent."""
        return np.tan(np.radians(slope_degrees)) * 100
    
    def classify_slope_usda(self, slope_percent: np.ndarray) -> np.ndarray:
        """Classify slope using USDA 7-class system."""
        result = np.full(slope_percent.shape, SlopeClass.CLASS_0, dtype=object)
        for cls, (low, high) in self.USDA_CLASSES.items():
            mask = (slope_percent >= low) & (slope_percent < high)
            result[mask] = cls
        return result
    
    def aspect_to_cardinal(self, aspect_degrees: np.ndarray) -> np.ndarray:
        """Convert aspect to 8 cardinal directions."""
        cardinals = np.array(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
        bin_idx = np.round(aspect_degrees / 45).astype(int) % 8
        return cardinals[bin_idx]
    
    def aspect_to_quadrant(self, aspect_degrees: np.ndarray) -> np.ndarray:
        """Convert aspect to 16-point compass."""
        points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        bin_idx = np.round(aspect_degrees / 22.5).astype(int) % 16
        return np.array(points)[bin_idx]
    
    def get_slope_distribution(self, slope_percent: np.ndarray) -> Dict[str, float]:
        """Get distribution of slope classes (percentage)."""
        classes = self.classify_slope_usda(slope_percent)
        total = classes.size
        dist = {}
        for cls in SlopeClass:
            count = np.sum(classes == cls)
            dist[cls.value] = float(count / total * 100)
        return dist
    
    def calculate_curvature(self, dem: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate profile, plan, and total curvature."""
        dy, dx = np.gradient(dem, self.resolution)
        dyy, dyx = np.gradient(dy, self.resolution)
        dxy, dxx = np.gradient(dx, self.resolution)
        
        p = dx**2 + dy**2
        epsilon = 1e-10
        q = np.sqrt(p + epsilon)
        
        profile = -(dxx * dx**2 + 2 * dxy * dx * dy + dyy * dy**2) / (p * q**3 + epsilon)
        plan = -(dxx * dy**2 - 2 * dxy * dx * dy + dyy * dx**2) / (p**1.5 + epsilon)
        total = dxx + dyy
        
        return profile, plan, total
    
    def calculate_roughness_index(self, dem: np.ndarray, window_size: int = 3) -> np.ndarray:
        """Calculate vector ruggedness measure (VRM) or simple roughness."""
        try:
            from scipy.ndimage import generic_filter
        except ImportError:
            return np.zeros_like(dem)
        
        def rough_func(values):
            center = values[len(values) // 2]
            return np.max(np.abs(values - center))
        
        return generic_filter(dem, rough_func, size=window_size)
    
    def calculate_twi(self, dem: np.ndarray, flow_accum: Optional[np.ndarray] = None) -> np.ndarray:
        """Calculate Topographic Wetness Index: TWI = ln(A/tan(β))"""
        slope_deg, _ = self.calculate_slope_aspect(dem)
        slope_rad = np.radians(slope_deg)
        tan_slope = np.tan(slope_rad) + 1e-6
        
        if flow_accum is None:
            # Approximate specific catchment area
            area = np.ones_like(dem)
        else:
            area = flow_accum * self.resolution  # Convert to m²
        
        return np.log(area / tan_slope)
    
    def calculate_tpi(self, dem: np.ndarray, window_size: int = 11) -> np.ndarray:
        """Calculate Topographic Position Index (TPI)."""
        try:
            from scipy.ndimage import uniform_filter
        except ImportError:
            return np.zeros_like(dem)
        
        mean_neighborhood = uniform_filter(dem, size=window_size)
        return dem - mean_neighborhood
    
    def classify_landform(self, tpi: np.ndarray, slope_deg: np.ndarray) -> np.ndarray:
        """Classify landforms based on TPI and slope (Jenness, 2006)."""
        std_tpi = (tpi - np.mean(tpi)) / (np.std(tpi) + 1e-10)
        
        result = np.full(tpi.shape, LandformType.FLAT, dtype=object)
        
        # Valleys
        result[(std_tpi < -1.0)] = LandformType.VALLEY
        # Lower slopes
        result[(std_tpi >= -1.0) & (std_tpi < -0.5)] = LandformType.LOWER_SLOPE
        # Mid slopes (with slope > 5°)
        result[(std_tpi >= -0.5) & (std_tpi <= 0.5) & (slope_deg > 5)] = LandformType.MID_SLOPE
        # Flats (TPI near 0, low slope)
        result[(std_tpi >= -0.5) & (std_tpi <= 0.5) & (slope_deg <= 5)] = LandformType.FLAT
        # Upper slopes
        result[(std_tpi > 0.5) & (std_tpi <= 1.0)] = LandformType.UPPER_SLOPE
        # Ridges
        result[(std_tpi > 1.0)] = LandformType.RIDGE
        
        return result
