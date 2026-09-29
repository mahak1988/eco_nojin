"""تحلیل زهکشی با الگوریتم D8 و محاسبه شبکه‌های آبری."""

from typing import Any

import numpy as np

from engine.land.hydrology import flow_accumulation, flow_direction, strahler_order
from engine.land.models import (
    DrainageAnalysis,
    DrainageDensityClass,
    DrainagePattern,
)

# The direction-code convention, the steepest-descent scan and the accumulation
# all live in engine.land.hydrology now: one scan, one code table, one
# topological sweep, one place to change when the convention changes. The
# wrappers below are kept so that anything already importing these private
# names keeps working; they add no behaviour.


def _d8_flow_direction(dem: np.ndarray) -> np.ndarray:
    """D8 flow direction by steepest descent.

    Codes: 1=N, 2=NE, 3=E, 4=SE, 5=S, 6=SW, 7=W, 8=NW (clockwise from north).
    Only interior cells are scored; the border keeps 0.
    """
    return flow_direction(dem)


def _d8_flow_accumulation(flow_dir: np.ndarray, dem: np.ndarray | None = None) -> np.ndarray:
    """D8 flow accumulation in topological order.

    This was a single row-major pass over the grid, which is not a topological
    order: a cell was added to its downstream neighbour before the cells south
    and west of it had contributed, so most of each catchment was never counted.
    The docstring claimed a sort by elevation that the code did not perform, and
    the ``flat_order`` argument was computed and then discarded.
    """
    return flow_accumulation(flow_dir, dem)


def _calculate_strahler_order(
    flow_acc: np.ndarray, flow_dir: np.ndarray, threshold: float = 10.0
) -> tuple[np.ndarray, int]:
    """Strahler ordering. Rule unchanged; implementation moved to hydrology."""
    return strahler_order(flow_acc, flow_dir, threshold)


def _classify_drainage_pattern(
    flow_dir: np.ndarray, flow_acc: np.ndarray, dem: np.ndarray
) -> DrainagePattern:
    """طبقه‌بندی الگوی زهکشی بر اساس توزیع جریان و توپوگرافی."""
    # تحلیل گیج شدن شبکه‌های جریان
    stream_mask = (
        flow_acc > np.percentile(flow_acc[flow_acc > 0], 90) if np.any(flow_acc > 0) else None
    )

    # بررسی یکنواختی جریان
    if stream_mask is not None and np.any(stream_mask):
        # استانداردهای ساده بر اساس توزیع جریان
        rows, cols = flow_acc.shape
        # بررسی خطی یا شبکه‌ای بودن
        row_var = np.var(np.sum(stream_mask, axis=1))
        col_var = np.var(np.sum(stream_mask, axis=0))
        total_var = row_var + col_var

        if total_var < rows * cols * 0.01:
            return DrainagePattern.PARALLEL
        # در مناطق مسطح یا کوهستانی، الگوها متفاوتند
        # این یک طبقه‌بندی ساده است
        if row_var > col_var * 3:
            return DrainagePattern.PARALLEL
        return DrainagePattern.DENDRITIC

    return DrainagePattern.DENDRITIC


def _classify_drainage_density(density: float) -> DrainageDensityClass:
    """طبقه‌بندی چگالی زهکشی بر اساس استانداردهای FAO."""
    if density < 2:
        return DrainageDensityClass.VERY_LOW
    elif density < 5:
        return DrainageDensityClass.LOW
    elif density < 15:
        return DrainageDensityClass.MODERATE
    elif density < 30:
        return DrainageDensityClass.HIGH
    else:
        return DrainageDensityClass.VERY_HIGH


def _calculate_bifurcation_ratio(strahler: np.ndarray) -> float:
    """محاسبه نسبت دوشاخه‌ای (Bifurcation Ratio)."""
    orders = strahler[strahler > 0]
    if len(orders) == 0:
        return 0.0

    # شمارش تعداد سلول‌ها در هر سطح
    unique_orders = np.unique(orders)
    counts = {int(o): int(np.sum(orders == o)) for o in unique_orders}

    if len(counts) < 2:
        return 0.0

    # نسبت میانگین عددی سلول‌های مجاور
    ratios = []
    for o in sorted(counts.keys()):
        next_o = o + 1
        if next_o in counts and counts[next_o] > 0:
            ratios.append(counts[o] / counts[next_o])

    if ratios:
        return float(np.mean(ratios))
    return 0.0


def _calculate_time_of_concentration(
    flow_accumulation: np.ndarray,
    flow_dir: np.ndarray,
    cell_size_m: float,
    slope_degrees: float,
) -> float:
    """
    محاسبه زمان غرقطی (Time of Concentration) با روش  کرپی-براون.

    Tc = 0.0195 * L^0.77 * S^-0.385  (برای واحد متری، نتیجه در ساعت)

    حتی اگر slope_degrees=0 باشد، حداقل مقدار معنادار برمی‌گرداند.
    """
    _rows, _cols = flow_accumulation.shape

    # یافتن طول مسیر جریان (از بالا به پایین در جهت جریان)
    # استفاده از آرگاه مجموعی جریان برای یافتن طولانی‌ترین مسیر
    max_flow_path_length = 0.0

    # محاسبه طول مسیر برای سلول‌های پایین‌دست

    # استفاده از جریان تجمعی برای تخمین طول مسیر
    if np.any(flow_accumulation > 1):
        # طول مسیر تقریباً متناسب با جذر جریان تجمعی
        max_acc = float(np.max(flow_accumulation))
        # تقریباً: L = cell_size * sqrt(acc) / some_factor
        max_flow_path_length = cell_size_m * np.sqrt(max_acc) / 2.0

    # شیب به صورت درصد
    slope_pct = np.tan(np.radians(slope_degrees)) * 100.0 if slope_degrees > 0 else 0.01

    # TC = 0.0195 * L^0.77 * S^-0.385 (L در متر، S درصد)
    # اگر L <= 0 باشد، مقدار پیش‌فرض
    if max_flow_path_length <= 0:
        max_flow_path_length = cell_size_m

    tc = 0.0195 * (max_flow_path_length**0.77) * (max(slope_pct, 0.001) ** (-0.385))

    # تبدیل به ساعت و clamp
    return max(0.1, min(float(tc), 24.0))


def calculate_drainage_metrics(
    dem_array: Any,
    resolution: float = 30.0,
    area_km2: float = 1.0,
) -> dict[str, Any]:
    """محاسبه معیارهای زهکشی از DEM با الگوریتم D8."""
    dem = np.asarray(dem_array, dtype=float)
    rows, cols = dem.shape

    if dem.size == 0:
        return {
            "drainage_pattern": DrainagePattern.DENDRITIC.value,
            "drainage_density": 0.0,
            "density_class": "low",
            "stream_orders": [1],
            "stream_order_max": 1,
            "bifurcation_ratio": 0.0,
            "flow_accumulation": [],
            "time_of_concentration_hours": 0.0,
            "main_channel_length_km": 0.0,
        }

    # محاسبه جهت جریان D8
    flow_dir = _d8_flow_direction(dem)

    # محاسبه انباشت جریان
    flow_acc = _d8_flow_accumulation(flow_dir, dem)

    # محاسبه شبکه‌های آبری (آستانه بر حسب تعداد سلول)
    # معمولاً آستانه = 10 تا 15 سلول برای DEMهای 30m
    acc_threshold = max(10.0, rows * cols * 0.001)
    stream_mask = flow_acc >= acc_threshold

    # شمارش طول شبکه‌های آبری (به کیلومتر)
    (resolution**2) / 10000.0  # متر مربع به هکتار
    stream_length_m = float(np.sum(stream_mask)) * resolution
    stream_length_km = stream_length_m / 1000.0

    # محاسبه چگالی زهکشی (km/km²)
    watershed_area = float(np.sum(np.isfinite(dem)) * resolution * resolution) / 1e6  # km²
    drainage_density = stream_length_km / max(watershed_area, 0.001)

    # شناسایی سلول‌های جریان
    flow_acc[np.isfinite(flow_acc)]
    slope_mean = float(np.nanmean(np.tan(np.radians(45.0)) * 100))  # placeholder

    # محاسبه شیب متوسط ساده برای TC
    grad_y, grad_x = np.gradient(dem, edge_order=1)
    slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
    slope_deg = np.degrees(slope_rad)
    valid_slope = slope_deg[np.isfinite(slope_deg)]
    slope_mean = float(np.nanmean(valid_slope)) if len(valid_slope) > 0 else 5.0

    # محاسبه استراهلر order
    strahler, strahler_max = _calculate_strahler_order(flow_acc, flow_dir, acc_threshold)

    # الگوی زهکشی
    pattern = _classify_drainage_pattern(flow_dir, flow_acc, dem)

    # نسبت دوشاخه‌ای
    bifurcation_ratio = _calculate_bifurcation_ratio(strahler)

    # زمان غرقطی
    tc = _calculate_time_of_concentration(flow_acc, flow_dir, resolution, slope_mean)

    # شبکه‌های آبری با شماره‌گذاری
    flow_acc[flow_acc >= acc_threshold]
    stream_orders_present = (
        sorted(set(strahler[stream_mask].astype(int).tolist())) if np.any(stream_mask) else [1]
    )

    return {
        "drainage_pattern": pattern.value,
        "drainage_density": round(drainage_density, 2),
        "density_class": _classify_drainage_density(drainage_density).value,
        "stream_orders": stream_orders_present,
        "stream_order_max": int(strahler_max),
        "bifurcation_ratio": round(bifurcation_ratio, 2) if bifurcation_ratio > 0 else 2.0,
        "flow_accumulation": flow_acc.tolist(),
        "time_of_concentration_hours": round(tc, 2),
        "main_channel_length_km": round(stream_length_km, 2),
    }


class DrainageAnalyzer:
    """کلاس تحلیل زهکشی با الگوریتم D8 بهینه‌شده."""

    def __init__(self, resolution: float = 30.0):
        self.resolution = resolution

    def _calculate_flow_direction(self, dem_array: Any) -> np.ndarray:
        """محاسبه جهت جریان D8 (برای سازگاری با واسط قبلی)."""
        dem = np.asarray(dem_array, dtype=float)
        return _d8_flow_direction(dem)

    def analyze(
        self, dem_array: Any, profile_id: str | None = None, area_km2: float = 1.0
    ) -> DrainageAnalysis:
        """تحلیل زهکشی با الگوریتم D8 و بازگرداندن مدل DrainageAnalysis."""
        dem = np.asarray(dem_array, dtype=float)
        rows, cols = dem.shape

        # محاسبه جهت و انباشت جریان
        flow_dir = _d8_flow_direction(dem)
        flow_acc = _d8_flow_accumulation(flow_dir, dem)

        # سطح آبشاری (آستانه تشخیص رودخانه)
        acc_threshold = max(10.0, rows * cols * 0.001)
        stream_mask = flow_acc >= acc_threshold

        # محاسبه مساحت حوض آبخیز
        cell_area_km2 = (self.resolution**2) / 1e6
        watershed_area = float(np.sum(np.isfinite(dem))) * cell_area_km2
        if watershed_area <= 0:
            watershed_area = area_km2 if area_km2 > 0 else 1.0

        # طول شبکه‌های آبری
        stream_length_m = float(np.sum(stream_mask)) * self.resolution
        stream_length_km = stream_length_m / 1000.0
        drainage_density = stream_length_km / max(watershed_area, 0.001)

        # شیب متوسط
        grad_y, grad_x = np.gradient(dem, edge_order=1)
        slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
        slope_deg = np.degrees(slope_rad)
        valid_slope = slope_deg[np.isfinite(slope_deg)]
        slope_mean = float(np.nanmean(valid_slope)) if len(valid_slope) > 0 else 5.0

        # استراهلر
        strahler, strahler_max = _calculate_strahler_order(flow_acc, flow_dir, acc_threshold)

        # الگوی زهکشی
        pattern = _classify_drainage_pattern(flow_dir, flow_acc, dem)

        # نسبت دوشاخه‌ای
        bifurcation_ratio = _calculate_bifurcation_ratio(strahler)

        # زمان غرقطی
        tc = _calculate_time_of_concentration(flow_acc, flow_dir, self.resolution, slope_mean)

        # لیست شماره‌های آبری
        stream_orders_present = (
            sorted(set(strahler[stream_mask].astype(int).tolist()))
            if np.any(stream_mask)
            else [1, 2, 3]
        )

        return DrainageAnalysis(
            profile_id=profile_id or "default",
            drainage_pattern=pattern,
            drainage_density=round(drainage_density, 2),
            density_class=_classify_drainage_density(drainage_density),
            stream_orders=stream_orders_present,
            stream_order_max=int(strahler_max) if strahler_max > 0 else 3,
            bifurcation_ratio=round(bifurcation_ratio, 2) if bifurcation_ratio > 0 else 2.0,
            flow_accumulation=flow_acc.tolist(),
            watershed_area_km2=round(watershed_area, 4),
            time_of_concentration_hours=round(tc, 2),
            main_channel_length_km=round(stream_length_km, 2),
            data_source="modelled",
            model="drainage_analysis",
        )
