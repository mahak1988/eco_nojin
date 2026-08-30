# -*- coding: utf-8 -*-
# ============================================================================
# Hydroma Climate Adaptive Phenology Engine - Phase 2
# Algorithms: H05 Dynamic Planting | H06 Flash Drought Warning
#             H07 Chilling Hours   | H24 Real-time Correction
# References: Modest et al. 2022 (phenology shift)
#             Yuan et al. 2023 (flash drought)
#             Luedeling et al. 2011 (chilling hours)
# ============================================================================
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

__version__ = "1.0.0"

# ------------------------------------------------------------------ ثابت‌ها
DAY_MS = 86400000  # میلی‌ثانیه در روز


@dataclass
class PhenologyConfig:
    frost_buffer_days: int = 14          # فاصله ایمن پس از آخرین یخبندان
    soil_temp_threshold_c: float = 10.0  # آستانه دمای خاک برای جوانه‌زنی
    soil_temp_window_days: int = 7       # بازه پایش دمای خاک
    rain_onset_threshold_mm: float = 10.0  # حداقل بارش برای شروع دیم
    rain_window_days: int = 30           # بازه جستجوی شروع بارش
    flash_drought_vpd_trend: float = 0.5  # آستانه روند فشار بخار
    flash_drought_sm_trend: float = -0.3  # آستانه روند رطوبت خاک
    flash_drought_horizon_days: int = 14  # افق هشدار
    chilling_model: str = "utah"         # مدل ساعات سرمایی


# ------------------------------------------------------------------ ابزارها
def safe_mean(values: Sequence[float]) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def slope_per_day(values: Sequence[float]) -> float:
    # شیب خطی (رگرسیون ساده) بر واحد روز
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n < 3:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = safe_mean(vals)
    num = sum((i - x_mean) * (vals[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


# ============================================================================
class ClimateAdaptivePhenology:
    # ------------------------------------------------------------------ init
    def __init__(self, config: Optional[PhenologyConfig] = None):
        self.cfg = config or PhenologyConfig()

    # ------------------------------------------------------------------- H05
    def h05_dynamic_planting_day(self,
                                 last_frost_day_of_year: int,
                                 soil_temp_series: Sequence[float],
                                 rain_onset_day_of_year: Optional[int] = None,
                                 target_day_of_year: Optional[int] = None) -> Dict:
        """
        تعیین تاریخ کاشت پویا بر اساس:
        1. آخرین یخبندان + فاصله ایمن
        2. رسیدن دمای خاک به آستانه جوانه‌زنی
        3. همزمانی با شروع فصل بارش (برای دیم)
        خروجی: روز سال کاشت + دلایل
        """
        reasons = []
        candidate = target_day_of_year or 280  # پیش‌فرض: اواسط پاییز

        # 1. فاصله ایمن از یخبندان
        if last_frost_day_of_year:
            frost_safe = last_frost_day_of_year + self.cfg.frost_buffer_days
            if candidate < frost_safe:
                candidate = frost_safe
                reasons.append("تنظیم بر اساس آخرین یخبندان + %d روز ایمن"
                               % self.cfg.frost_buffer_days)

        # 2. دمای خاک
        if soil_temp_series and len(soil_temp_series) >= 3:
            mean_soil = safe_mean(soil_temp_series[-self.cfg.soil_temp_window_days:])
            if mean_soil < self.cfg.soil_temp_threshold_c:
                deficit = self.cfg.soil_temp_threshold_c - mean_soil
                delay_days = int(math.ceil(deficit * 3))  # تقریب 3 روز به ازای هر درجه
                candidate += delay_days
                reasons.append("تأخیر %d روزه برای رسیدن دمای خاک به %.1f درجه"
                               % (delay_days, self.cfg.soil_temp_threshold_c))
            else:
                reasons.append("دمای خاک مناسب است (%.1f درجه)" % mean_soil)

        # 3. همزمانی با شروع بارش (برای دیم)
        if rain_onset_day_of_year:
            gap = abs(candidate - rain_onset_day_of_year)
            if gap > self.cfg.rain_window_days:
                reasons.append("هشدار: فاصله %d روزه از شروع بارش؛ ریسک دیم بالا" % gap)
            else:
                reasons.append("همزمانی مناسب با شروع بارش (%d روز)" % gap)

        return {
            "planting_day_of_year": candidate,
            "reasons": reasons,
            "frost_risk_reduced": bool(reasons and "یخبندان" in reasons[0]),
            "confidence": "B" if len(reasons) >= 2 else "C",
        }

    # ------------------------------------------------------------------- H06
    def h06_flash_drought_risk(self,
                               vpd_last_7d: Sequence[float],
                               soil_moisture_fraction_last_14d: Sequence[float],
                               forecast_rain_mm_next_14d: float) -> Dict:
        """
        ریسک خشکسالی ناگهانی بر اساس:
        - روند فشار بخار (افزایش = تنش)
        - روند رطوبت خاک (کاهش = تنش)
        - پیش‌بینی بارش (کاهش = تشدید)
        خروجی: ریسک 0 تا 1 + سطح هشدار
        """
        vpd_slope = slope_per_day(vpd_last_7d)
        sm_slope = slope_per_day(soil_moisture_fraction_last_14d)

        risk = 0.0
        drivers = []

        if vpd_slope > self.cfg.flash_drought_vpd_trend:
            risk += 0.35
            drivers.append("افزایش سریع فشار بخار (%.2f/روز)" % vpd_slope)

        if sm_slope < self.cfg.flash_drought_sm_trend:
            risk += 0.35
            drivers.append("کاهش سریع رطوبت خاک (%.2f/روز)" % sm_slope)

        if forecast_rain_mm_next_14d < 5.0:
            risk += 0.20
            drivers.append("پیش‌بینی بارش ناچیز (%.1f میلی‌متر در ۱۴ روز)"
                           % forecast_rain_mm_next_14d)

        # نرمال‌سازی
        risk = min(1.0, risk)

        if risk >= 0.7:
            level = "بحرانی"
            action = "آبیاری اضطراری + پایش روزانه"
        elif risk >= 0.4:
            level = "هشدار"
            action = "افزایش دور آبیاری + مالچ‌پاشی"
        elif risk >= 0.2:
            level = "پایش"
            action = "پایش هفتگی"
        else:
            level = "عادی"
            action = "روال عادی"

        return {
            "risk_0_1": round(risk, 2),
            "level": level,
            "action": action,
            "drivers": drivers,
            "horizon_days": self.cfg.flash_drought_horizon_days,
            "vpd_slope_per_day": round(vpd_slope, 3),
            "sm_slope_per_day": round(sm_slope, 3),
        }

    # ------------------------------------------------------------------- H07
    def h07_chilling_hours(self,
                           hourly_temps_c: Sequence[float]) -> Dict:
        """
        محاسبه ساعات سرمایی مؤثر با مدل یوتا:
        0-2.4: 1 واحد | 2.5-9.1: 0.5 | 9.2-12.4: 0 | 12.5-15.9: -0.5 | >=16: -1
        خروجی: مجموع واحدها + تفسیر
        """
        units = 0.0
        for t in hourly_temps_c:
            if t is None:
                continue
            if t <= 2.4:
                units += 1.0
            elif t <= 9.1:
                units += 0.5
            elif t <= 12.4:
                units += 0.0
            elif t <= 15.9:
                units -= 0.5
            else:
                units -= 1.0
        units = max(0.0, units)

        if units >= 1000:
            status = "کافی برای اکثر درختان معتدل"
        elif units >= 700:
            status = "کافی برای ارقام کم‌نیاز"
        elif units >= 400:
            status = "مرزی؛ ریسک خزان‌شکنی ناقص"
        else:
            status = "ناکافی؛ نیاز به ارقام کم‌سرمایی یا جبران"

        return {
            "chilling_units": round(units, 0),
            "status": status,
            "model": self.cfg.chilling_model,
            "hours_analyzed": len(hourly_temps_c),
        }

    # ------------------------------------------------------------------- H24
    def h24_realtime_correction(self,
                                ndvi_actual: float,
                                ndvi_predicted: float) -> Dict:
        """
        تصحیح بلادرنگ بر اساس تفاوت شاخص گیاهی مشاهده‌شده و پیش‌بینی‌شده
        خروجی: ضریب تصحیح عملکرد (0.5 تا 1.5)
        """
        if ndvi_predicted <= 0:
            return {"correction_factor": 1.0, "note": "پیش‌بینی نامعتبر"}
        ratio = ndvi_actual / ndvi_predicted
        factor = max(0.5, min(1.5, ratio))
        note = ""
        if factor < 0.85:
            note = "عملکرد واقعی کمتر از پیش‌بینی؛ تنش فعال"
        elif factor > 1.10:
            note = "عملکرد واقعی بهتر از پیش‌بینی"
        else:
            note = "تطابق مناسب"
        return {
            "correction_factor": round(factor, 2),
            "ndvi_ratio": round(ratio, 2),
            "note": note,
        }

    # -------------------------------------------------- گزارش فصلی یکپارچه
    def generate_season_advisory(self,
                                 last_frost_day: int,
                                 soil_temp_series: Sequence[float],
                                 vpd_7d: Sequence[float],
                                 sm_14d: Sequence[float],
                                 forecast_rain: float,
                                 winter_temps: Optional[Sequence[float]] = None) -> Dict:
        """تولید توصیه‌نامه فصلی کامل با ترکیب هر چهار الگوریتم"""
        advisory = {}
        advisory["planting"] = self.h05_dynamic_planting_day(
            last_frost_day, soil_temp_series)
        advisory["flash_drought"] = self.h06_flash_drought_risk(
            vpd_7d, sm_14d, forecast_rain)
        if winter_temps:
            advisory["chilling"] = self.h07_chilling_hours(winter_temps)
        advisory["generated_by"] = "ClimateAdaptivePhenology v%s" % __version__
        return advisory
