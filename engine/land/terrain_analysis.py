"""تحلیل توپوگرافی پیشرفته (محاسبه شیب، جهت، انحراف منحنی، TWI، TPI)."""

from typing import Any

import numpy as np

from engine.land.hydrology import flow_accumulation, flow_direction
from engine.land.models import (
    CurvatureResult,
    LandformType,
    SlopeClass,
    TerrainAnalysis,
    TerrainIndices,
    TerrainType,
)


def aspect_to_cardinal(degrees: float) -> str:
    """تبدیل درجه جهت به جهت Cardinal."""
    if np.isnan(degrees):
        return "unknown"
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    idx = int((degrees + 11.25) / 22.5) % 16
    return directions[idx]


_aspect_to_cardinal = aspect_to_cardinal


def classify_slope_usda(slope_percent: float) -> SlopeClass:
    """طبقه‌بندی شیب بر اساس استاندارد USDA."""
    if slope_percent < 2:
        return SlopeClass.CLASS_0
    elif slope_percent < 5:
        return SlopeClass.CLASS_1
    elif slope_percent < 10:
        return SlopeClass.CLASS_2
    elif slope_percent < 20:
        return SlopeClass.CLASS_3
    elif slope_percent < 40:
        return SlopeClass.CLASS_4
    else:
        return SlopeClass.CLASS_5


def aspect_to_cardinal_8(degrees: float) -> str:
    """تبدیل درجه جهت به 8 جهت اصلی (N, NE, E, SE, S, SW, W, NW)."""
    if np.isnan(degrees):
        return "unknown"
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((degrees + 22.5) / 45.0) % 8
    return directions[idx]


def _get_dominant_aspect(aspects: np.ndarray) -> str:
    """تعیین جهت غالب از آرایه جهات (8-direction)."""
    aspects = np.asarray(aspects, dtype=float)
    valid = aspects[~np.isnan(aspects)]
    if valid.size == 0:
        return "unknown"
    median = float(np.median(valid))
    return aspect_to_cardinal_8(median)


def calculate_slope_aspect(
    dem: np.ndarray, resolution: float = 30.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    محاسبه شیب و جهت با روش Horn (3x3).

    Returns:
        (slope_degrees, aspect_degrees): Both 2D arrays with NaN at borders.
    """
    dem = np.asarray(dem, dtype=float)
    rows, cols = dem.shape
    slope_rad = np.full_like(dem, np.nan, dtype=np.float64)
    aspect_rad = np.full_like(dem, np.nan, dtype=np.float64)

    # Grid axes: rows increase southward, columns increase eastward. So dz_dx is
    # the derivative toward east and dz_dy the derivative toward south, both
    # positive toward the higher ground.
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            z = dem[i - 1 : i + 2, j - 1 : j + 2]

            # Horn's finite difference (central differences)
            dz_dx = ((z[2, 2] + 2 * z[1, 2] + z[0, 2]) - (z[2, 0] + 2 * z[1, 0] + z[0, 0])) / (
                8.0 * resolution
            )
            dz_dy = ((z[2, 2] + 2 * z[2, 1] + z[2, 0]) - (z[0, 2] + 2 * z[0, 1] + z[0, 0])) / (
                8.0 * resolution
            )

            slope_rad[i, j] = np.arctan2(np.sqrt(dz_dx**2 + dz_dy**2), 1.0)
            # Aspect is the compass azimuth of steepest descent, 0 = north and
            # increasing clockwise. A compass azimuth theta has the (east,
            # south) components (sin theta, -cos theta), so the downslope
            # vector (-dz_dx, -dz_dy) gives sin(theta) ~ -dz_dx and
            # cos(theta) ~ dz_dy. atan2 must therefore be handed the east
            # component first and the south component second.
            #
            # arctan2(-dz_dy, dz_dx) — the form this used to take — transposes
            # those two components. It is a reflection of the aspect field, not
            # a rotation, so no constant offset recovers it: a slope descending
            # due south scored 270 (west) and a slope descending due west
            # scored 180 (south).
            aspect_rad[i, j] = np.arctan2(-dz_dx, dz_dy)

    slope_deg = np.degrees(slope_rad)
    aspect_deg = (np.degrees(aspect_rad) + 360) % 360

    return slope_deg, aspect_deg


def calculate_curvature(dem: np.ndarray, resolution: float = 30.0) -> dict[str, np.ndarray]:
    """
    Calculate profile and plan curvature using Horn's method.

    Profile curvature: along the slope direction (affects acceleration/deceleration)
    Plan curvature: perpendicular to slope direction (affects convergence/divergence)
    Total curvature: sqrt(profile² + plan²)

    Returns:
        Dict with 'profile', 'plan', 'total', 'convergence_index' arrays.
    """
    dem = np.asarray(dem, dtype=float)
    rows, cols = dem.shape

    profile_c = np.full_like(dem, np.nan, dtype=np.float64)
    plan_c = np.full_like(dem, np.nan, dtype=np.float64)
    total_c = np.full_like(dem, np.nan, dtype=np.float64)
    convergence = np.full_like(dem, np.nan, dtype=np.float64)

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            z = dem[i - 1 : i + 2, j - 1 : j + 2]

            # First derivatives
            dz_dx = ((z[0, 2] + 2 * z[1, 2] + z[2, 2]) - (z[0, 0] + 2 * z[1, 0] + z[2, 0])) / (
                8.0 * resolution
            )
            dz_dy = ((z[2, 0] + 2 * z[2, 1] + z[2, 2]) - (z[0, 0] + 2 * z[0, 1] + z[0, 2])) / (
                8.0 * resolution
            )

            # Second derivatives
            d2z_dx2 = (
                (z[0, 0] + 2 * z[0, 1] + z[0, 2])
                - 2 * (z[1, 0] + 2 * z[1, 1] + z[1, 2])
                + (z[2, 0] + 2 * z[2, 1] + z[2, 2])
            ) / (4.0 * resolution**2)
            d2z_dy2 = (
                (z[0, 0] + 2 * z[1, 0] + z[2, 0])
                - 2 * (z[0, 1] + 2 * z[1, 1] + z[2, 1])
                + (z[0, 2] + 2 * z[1, 2] + z[2, 2])
            ) / (4.0 * resolution**2)
            d2z_dxdy = (z[2, 2] - z[2, 0] - z[0, 2] + z[0, 0]) / (4.0 * resolution**2)

            # Gradient magnitude
            slope_mag = np.sqrt(dz_dx**2 + dz_dy**2)

            if slope_mag < 1e-10:
                # Flat area
                profile_c[i, j] = 0.0
                plan_c[i, j] = 0.0
                total_c[i, j] = 0.0
                convergence[i, j] = 0.0
                continue

            # Curvature calculations (Wilson, 1986)
            denom = slope_mag * (dz_dx**2 + dz_dy**2)

            # Profile curvature (along slope direction)
            profile_c[i, j] = (
                (d2z_dx2 * dz_dx**2 + 2 * d2z_dxdy * dz_dx * dz_dy + d2z_dy2 * dz_dy**2)
                / (denom**1.5 * resolution)
                if denom > 0
                else 0.0
            )

            # Plan curvature (perpendicular to slope)
            plan_c[i, j] = (
                (d2z_dx2 * dz_dy**2 - 2 * d2z_dxdy * dz_dx * dz_dy + d2z_dy2 * dz_dx**2)
                / (denom**0.5 * resolution**2)
                if denom > 0
                else 0.0
            )

            total_c[i, j] = np.sqrt(profile_c[i, j] ** 2 + plan_c[i, j] ** 2)

            # Convergence index: positive = divergent, negative = convergent
            convergence[i, j] = plan_c[i, j] * slope_mag

    return {
        "profile": profile_c,
        "plan": plan_c,
        "total": total_c,
        "convergence_index": convergence,
    }


def calculate_twi(dem: np.ndarray, resolution: float = 30.0) -> np.ndarray:
    """
    Topographic Wetness Index: TWI = ln(As / tan(β))

    Where:
      As = specific catchment area (flow accumulation × cell size² / cell size = flow accumulation × cell size)
      β = local slope angle

    Reference: Beven & Kirkby (1975) - LISEM model.
    """
    dem = np.asarray(dem, dtype=float)
    _rows, _cols = dem.shape

    # Flow accumulation (number of upstream cells) from the shared D8
    # implementation, which is the one engine.land.drainage also uses.
    flow_dir = flow_direction(dem)
    acc = flow_accumulation(flow_dir, dem)

    # Specific catchment area = acc * cell_size (in meters)
    # TWI requires slope in radians
    slope_deg, _ = calculate_slope_aspect(dem, resolution)
    slope_rad = np.radians(slope_deg)
    tan_beta = np.tan(slope_rad)

    # Specific catchment area (m)
    sca = acc * resolution  # m² / m = m

    # TWI = ln(sca / tan(beta))
    # Handle edge cases
    mask = (tan_beta > 0) & (sca > 0) & np.isfinite(tan_beta) & np.isfinite(sca)
    twi = np.full_like(dem, np.nan, dtype=np.float64)
    twi[mask] = np.log(sca[mask] / tan_beta[mask])

    # For flat areas, use a large value
    flat_mask = tan_beta <= 0
    twi[flat_mask] = np.nanmax(twi[mask]) if np.any(mask) else 10.0

    # Clamp to reasonable range
    twi = np.clip(np.nan_to_num(twi, nan=0.0, posinf=20.0, neginf=0.0), 0.0, 20.0)

    return twi


def calculate_tpi(dem: np.ndarray, resolution: float = 30.0, scale_m: float = 90.0) -> np.ndarray:
    """
    Topographic Position Index (TPI):
    TPI = elevation(cell) - mean(elevation in neighborhood radius)

    The scale parameter determines the neighborhood size:
    A larger scale highlights broader landforms.

    Reference: Gessler et al. (2009) - "Color-shaded relief and
    the visualization of diverse landscapes using a computationally efficient
    modified TPI slope algorithm."
    """
    dem = np.asarray(dem, dtype=float)
    dem_filled = np.where(np.isfinite(dem), dem, np.nan)

    # Fill NaN with median for computation
    if np.any(np.isnan(dem_filled)):
        median_val = float(np.nanmedian(dem_filled))
        dem_filled = np.where(np.isnan(dem_filled), median_val, dem_filled)

    rows, cols = dem.shape
    neighborhood_radius = max(1, int(scale_m / resolution))

    tpi = np.full_like(dem, np.nan, dtype=np.float64)

    # Simple moving average approach
    for i in range(neighborhood_radius, rows - neighborhood_radius):
        for j in range(neighborhood_radius, cols - neighborhood_radius):
            window = dem_filled[
                i - neighborhood_radius : i + neighborhood_radius + 1,
                j - neighborhood_radius : j + neighborhood_radius + 1,
            ]
            mean_elev = np.mean(window)
            tpi[i, j] = dem_filled[i, j] - mean_elev

    return tpi


def _classify_landform(tpi_val: float, slope_deg: float) -> str:
    """طبقه‌بندی لندفرم بر اساس TPI و شیب."""
    if slope_deg < 3:
        return "flat"
    elif abs(tpi_val) < 5:
        if slope_deg < 8:
            return "gentle"
        elif slope_deg < 15:
            return "rolling"
        else:
            return "steep"
    elif tpi_val > 5:
        return "ridge"
    else:
        return "valley"


def _calculate_roughness_index(dem: np.ndarray) -> float:
    """محاسبه شاخص ناهمواری (Roughness Index)."""
    dem = np.asarray(dem, dtype=float)
    valid = dem[np.isfinite(dem)]
    if valid.size == 0:
        return 0.0
    # Standard deviation of elevation
    return float(np.std(valid)) / max(float(np.mean(valid)), 1.0)


def calculate_terrain_metrics(dem_array: Any, resolution: float = 30.0) -> dict[str, Any]:
    """محاسبه معیارهای توپوگرافی از DEM."""
    dem = np.asarray(dem_array, dtype=float)
    if dem.size == 0:
        return {}

    valid_mask = np.isfinite(dem)
    if not np.any(valid_mask):
        return {}

    valid_dem = dem[valid_mask]

    # Slope and aspect (Horn's method)
    slope_deg, aspect_deg = calculate_slope_aspect(dem, resolution)

    # Curvature
    curvature = calculate_curvature(dem, resolution)

    # TWI
    twi = calculate_twi(dem, resolution)

    # TPI
    tpi = calculate_tpi(dem, resolution)

    # Roughness
    roughness = _calculate_roughness_index(dem)

    # Dominant aspect
    valid_aspects = aspect_deg[valid_mask]
    aspect_median = (
        float(np.nanmedian(valid_aspects)) if np.any(np.isfinite(valid_aspects)) else 0.0
    )

    # Stream order / landform
    valid_tpi = tpi[valid_mask] if np.any(valid_mask) else np.array([0.0])
    valid_slope = slope_deg[valid_mask] if np.any(valid_mask) else np.array([0.0])
    tpi_mean = float(np.nanmean(valid_tpi)) if np.any(np.isfinite(valid_tpi)) else 0.0
    slope_mean = float(np.nanmean(valid_slope)) if np.any(np.isfinite(valid_slope)) else 0.0
    landform = _classify_landform(tpi_mean, slope_mean)

    return {
        "terrain_type": _classify_terrain_type(slope_mean),
        "elevation_min": float(np.min(valid_dem)),
        "elevation_max": float(np.max(valid_dem)),
        "elevation_mean": float(np.mean(valid_dem)),
        "elevation_std": float(np.std(valid_dem)),
        "slope_mean": slope_mean,
        "slope_max": float(np.nanmax(slope_deg[valid_mask])) if np.any(valid_mask) else 0.0,
        "slope_std": float(np.nanstd(slope_deg[valid_mask])) if np.any(valid_mask) else 0.0,
        "aspect_dominant": aspect_to_cardinal(aspect_median),
        "aspect_median": aspect_median,
        "curvature_mean": float(np.nanmean(curvature["total"][valid_mask]))
        if np.any(valid_mask)
        else 0.0,
        "profile_curvature_mean": float(np.nanmean(curvature["profile"][valid_mask]))
        if np.any(valid_mask)
        else 0.0,
        "plan_curvature_mean": float(np.nanmean(curvature["plan"][valid_mask]))
        if np.any(valid_mask)
        else 0.0,
        "twi_mean": float(np.nanmean(twi[valid_mask])) if np.any(valid_mask) else 0.0,
        "tpi_mean": tpi_mean,
        "roughness_index": roughness,
        "landform": landform,
    }


def _classify_terrain_type(mean_slope: float) -> TerrainType:
    """طبقه‌بندی نوع توپوگرافی بر اساس شیب متوسط."""
    if mean_slope < 3:
        return TerrainType.FLAT
    elif mean_slope < 8:
        return TerrainType.ROLLING
    elif mean_slope < 20:
        return TerrainType.HILLY
    else:
        return TerrainType.MOUNTAINOUS


class TerrainAnalyzer:
    """کلاس تحلیل توپوگرافی پیشرفته."""

    def __init__(self, resolution: float = 30.0):
        self.resolution = resolution

    def _classify_terrain(self, slopes: np.ndarray) -> TerrainType:
        """طبقه‌بندی توپوگرافی بر اساس میانگین شیب."""
        mean_slope = float(np.nanmean(slopes))
        if np.isnan(mean_slope):
            return TerrainType.FLAT
        return _classify_terrain_type(mean_slope)

    def analyze(self, dem_array: Any, profile_id: str | None = None) -> TerrainAnalysis:
        """تحلیل توپوگرافی و بازگرداندن TerrainAnalysis model."""
        dem = np.asarray(dem_array, dtype=float)
        if dem.size == 0:
            raise ValueError("DEM array is empty")

        valid_mask = np.isfinite(dem)
        if not np.any(valid_mask):
            raise ValueError("DEM array contains no valid data")

        valid_dem = dem[valid_mask]

        # Slope and aspect using Horn's method
        slope_deg, aspect_deg = calculate_slope_aspect(dem, self.resolution)

        # Curvature
        curvature_data = calculate_curvature(dem, self.resolution)

        # TWI and TPI
        twi = calculate_twi(dem, self.resolution)
        tpi = calculate_tpi(dem, self.resolution)

        # Valid arrays
        valid_slope = slope_deg[valid_mask]
        valid_aspect = aspect_deg[valid_mask]
        valid_tpi = tpi[valid_mask]
        valid_twi = twi[valid_mask]

        # Statistics
        slope_mean = float(np.nanmean(valid_slope))
        slope_max = float(np.nanmax(valid_slope))
        elevation_min = float(np.min(valid_dem))
        elevation_max = float(np.max(valid_dem))
        elevation_mean = float(np.mean(valid_dem))
        elevation_range = elevation_max - elevation_min

        float(np.nanmedian(valid_aspect))
        aspect_dominant = _get_dominant_aspect(valid_aspect)

        # Curvature results
        valid_profile_c = curvature_data["profile"][valid_mask]
        valid_plan_c = curvature_data["plan"][valid_mask]
        valid_total_c = curvature_data["total"][valid_mask]
        valid_conv = curvature_data["convergence_index"][valid_mask]

        curvature = CurvatureResult(
            profile_curvature=float(np.nanmean(valid_profile_c)),
            plan_curvature=float(np.nanmean(valid_plan_c)),
            total_curvature=float(np.nanmean(valid_total_c)),
            convergence_index=float(np.nanmean(valid_conv))
            if np.any(np.isfinite(valid_conv))
            else None,
            data_source="modelled",
            model="terrain_analysis curvature",
        )

        # Landform classification
        tpi_mean = float(np.nanmean(valid_tpi)) if np.any(np.isfinite(valid_tpi)) else 0.0
        landform = _classify_landform(tpi_mean, slope_mean)

        # Wetness class
        twi_mean = float(np.nanmean(valid_twi)) if np.any(np.isfinite(valid_twi)) else 0.0
        if twi_mean > 15:
            wetness_class = "very_wet"
        elif twi_mean > 10:
            wetness_class = "wet"
        elif twi_mean > 6:
            wetness_class = "moderate"
        else:
            wetness_class = "dry"

        terrain_type = self._classify_terrain(valid_slope)

        # Roughness index
        roughness = _calculate_roughness_index(dem)

        # Map landform string to LandformType
        landform_map = {
            "valley": LandformType.VALLEY,
            "ridge": LandformType.RIDGE,
            "flat": LandformType.FLAT,
            "lower_slope": LandformType.LOWER_SLOPE,
            "mid_slope": LandformType.MID_SLOPE,
            "upper_slope": LandformType.UPPER_SLOPE,
        }

        # Slope distribution
        slope_classes: dict[str, float] = {}
        if np.any(valid_mask):
            for cls in SlopeClass:
                count = np.sum(valid_slope >= float(cls.value.replace("CLASS_", "")) * np.pi / 180)
                slope_classes[str(cls.value)] = float(count)

        # Use actual USDA classification by slope percent
        slope_pct = np.tan(np.radians(valid_slope)) * 100.0
        slope_dist: dict[str, float] = {}
        for pct, cls in [
            (2, SlopeClass.CLASS_0),
            (5, SlopeClass.CLASS_1),
            (10, SlopeClass.CLASS_2),
            (20, SlopeClass.CLASS_3),
            (40, SlopeClass.CLASS_4),
        ]:
            slope_dist[str(cls.value)] = float(np.mean(slope_pct < pct))
        slope_dist[str(SlopeClass.CLASS_5.value)] = float(np.mean(slope_pct >= 40))

        return TerrainAnalysis(
            profile_id=profile_id or "default",
            terrain_type=terrain_type,
            elevation_min=elevation_min,
            elevation_max=elevation_max,
            elevation_mean=elevation_mean,
            elevation_range=elevation_range,
            slope_mean=slope_mean,
            slope_max=slope_max,
            slope_class_dominant=classify_slope_usda(np.tan(np.radians(slope_mean)) * 100.0),
            slope_distribution=slope_dist,
            aspect_dominant=aspect_dominant,
            aspect_distribution={},
            curvature=curvature,
            indices=TerrainIndices(
                twi=twi_mean,
                tpi=tpi_mean,
                roughness_index=roughness,
                landform=landform_map.get(landform, LandformType.MID_SLOPE),
                wetness_class=wetness_class,
            ),
            roughness_index=roughness,
            data_source="modelled",
            model="terrain_analysis",
        )
