# -*- coding: utf-8 -*-
# ============================================================================
# Hydroma Soil Degradation & Sustainability Model - Phase 3
# Algorithms: H09 SOC-dynamic AWC | H10 Erosion Root Decay
#             H11 Salinity Trend  | H12 Compaction
#             H13 Fertility Index | H14 Subsidence Risk
# References: IPCC AR6 WG2 (2022); FAO GSP (2021); GLASOD (1991)
# ============================================================================
import math
from dataclasses import dataclass, field
from typing import Dict, Optional

__version__ = "1.0.0"


@dataclass
class SoilDegradationConfig:
    # H09: ظرفیت آب پویا
    awc_soc_coeff: float = 0.5       # هر 1% تغییر SOC -> 50% تغییر AWC
    awc_factor_min: float = 0.3
    awc_factor_max: float = 1.5
    soc_reference_pct: float = 2.0   # مرجع جهانی
    
    # H10: فرسایش
    erosion_to_depth_factor: float = 0.077  # تن/هکتار -> سانتی‌متر (چگالی 1.3)
    min_root_depth_cm: float = 10.0
    
    # H11: شوری
    salinity_thresholds: Dict = field(default_factory=lambda: {
        "non_saline": 2.0, "slightly_saline": 4.0,
        "moderately_saline": 8.0, "strongly_saline": 16.0
    })
    
    # H12: تراکم
    max_compaction: float = 0.8
    
    # H13: حاصلخیزی
    fertility_weights: Dict = field(default_factory=lambda: {
        "soc": 0.25, "n": 0.15, "p": 0.15,
        "k": 0.15, "ph": 0.15, "bio": 0.15
    })
    fertility_refs: Dict = field(default_factory=lambda: {
        "soc_pct": 3.0, "n_pct": 0.3, "p_ppm": 50.0, "k_ppm": 300.0
    })
    
    # H14: فرونشست
    soil_sensitivity: Dict = field(default_factory=lambda: {
        "clay": 1.0, "silt": 0.8, "loam": 0.5,
        "sand": 0.2, "gravel": 0.1
    })
    subsidence_critical_mm_yr: float = 30.0
    subsidence_severe_mm_yr: float = 15.0
    subsidence_moderate_mm_yr: float = 5.0


# ============================================================================
class SoilDegradationModel:
    # ------------------------------------------------------------------ init
    def __init__(self, config: Optional[SoilDegradationConfig] = None):
        self.cfg = config or SoilDegradationConfig()

    # ------------------------------------------------------------------- H09
    def h09_dynamic_awc(self, awc_base_mm_m: float, soc_current_pct: float,
                        soc_reference_pct: Optional[float] = None) -> Dict:
        """
        ظرفیت نگهداری آب پویا بر اساس کربن آلی خاک
        فرمول: AWC(t) = AWC0 x (1 + 0.5 x dSOC/1%)
        هر 1% افزایش SOC -> ~170,000 لیتر آب/هکتار بیشتر
        """
        ref = soc_reference_pct if soc_reference_pct else self.cfg.soc_reference_pct
        delta_soc = soc_current_pct - ref
        factor = 1.0 + self.cfg.awc_soc_coeff * (delta_soc / 1.0)
        factor = max(self.cfg.awc_factor_min, min(self.cfg.awc_factor_max, factor))
        awc_adjusted = awc_base_mm_m * factor
        
        return {
            "awc_base_mm_m": round(awc_base_mm_m, 1),
            "awc_adjusted_mm_m": round(awc_adjusted, 1),
            "soc_delta_pct": round(delta_soc, 2),
            "adjustment_factor": round(factor, 3),
            "interpretation": self._awc_interpretation(factor)
        }

    def _awc_interpretation(self, factor: float) -> str:
        if factor >= 1.2:
            return "ظرفیت آب بسیار بهتر از مرجع (خاک غنی از کربن)"
        elif factor >= 1.0:
            return "ظرفیت آب مناسب"
        elif factor >= 0.7:
            return "ظرفیت آب کاهش‌یافته (نیاز به افزایش ماده آلی)"
        else:
            return "ظرفیت آب بحرانی (خاک تخریب‌شده)"

    # ------------------------------------------------------------------- H10
    def h10_root_depth_decay(self, initial_root_depth_cm: float,
                             erosion_rate_t_ha_yr: float, years: int,
                             soil_bulk_density_t_m3: float = 1.3) -> Dict:
        """
        کاهش عمق مؤثر ریشه بر اثر فرسایش
        فرمول: RD(t) = RD0 x exp(-erosion_depth_rate x t / RD0)
        """
        if soil_bulk_density_t_m3 <= 0:
            soil_bulk_density_t_m3 = 1.3
        
        # تبدیل فرسایش (تن/هکتار/سال) به کاهش عمق (سانتی‌متر/سال)
        soil_loss_cm_yr = erosion_rate_t_ha_yr / (soil_bulk_density_t_m3 * 10.0)
        
        if initial_root_depth_cm <= 0:
            initial_root_depth_cm = 50.0
        
        effective_depth = initial_root_depth_cm * math.exp(
            -soil_loss_cm_yr * years / initial_root_depth_cm)
        effective_depth = max(self.cfg.min_root_depth_cm, effective_depth)
        
        depth_loss_pct = (1.0 - effective_depth / initial_root_depth_cm) * 100.0
        
        return {
            "initial_root_depth_cm": round(initial_root_depth_cm, 1),
            "effective_root_depth_cm": round(effective_depth, 1),
            "soil_loss_cm_per_year": round(soil_loss_cm_yr, 3),
            "total_soil_loss_cm": round(soil_loss_cm_yr * years, 1),
            "depth_loss_percent": round(depth_loss_pct, 1),
            "years_analyzed": years,
            "severity": self._erosion_severity(depth_loss_pct)
        }

    def _erosion_severity(self, loss_pct: float) -> str:
        if loss_pct < 5:
            return "ناچیز"
        elif loss_pct < 15:
            return "ملایم"
        elif loss_pct < 30:
            return "متوسط"
        elif loss_pct < 50:
            return "شدید"
        else:
            return "بحرانی"

    # ------------------------------------------------------------------- H11
    def h11_salinity_trend(self, ec_initial_ds_m: float,
                           trend_rate_ds_m_per_yr: float, years: int,
                           irrigation_quality_penalty: float = 0.0) -> Dict:
        """
        پیش‌بینی روند شوری ثانویه خاک
        فرمول: EC(t) = EC0 + trend x years + irrigation_penalty
        """
        ec_projected = (ec_initial_ds_m +
                        trend_rate_ds_m_per_yr * years +
                        irrigation_quality_penalty)
        ec_projected = max(0.0, ec_projected)
        
        th = self.cfg.salinity_thresholds
        if ec_projected < th["non_saline"]:
            classification = "غیرشور"
            yield_impact_pct = 0
        elif ec_projected < th["slightly_saline"]:
            classification = "شوری ملایم"
            yield_impact_pct = 10
        elif ec_projected < th["moderately_saline"]:
            classification = "شوری متوسط"
            yield_impact_pct = 25
        elif ec_projected < th["strongly_saline"]:
            classification = "شوری شدید"
            yield_impact_pct = 50
        else:
            classification = "شوری بسیار شدید"
            yield_impact_pct = 75
        
        return {
            "ec_initial_ds_m": round(ec_initial_ds_m, 2),
            "ec_projected_ds_m": round(ec_projected, 2),
            "trend_rate_per_yr": round(trend_rate_ds_m_per_yr, 3),
            "years_projected": years,
            "classification": classification,
            "estimated_yield_impact_percent": yield_impact_pct,
            "recommendation": self._salinity_recommendation(classification)
        }

    def _salinity_recommendation(self, classification: str) -> str:
        recs = {
            "غیرشور": "مدیریت عادی",
            "شوری ملایم": "پایش سالانه + انتخاب ارقام متحمل",
            "شوری متوسط": "زهکشی + آبشویی + اصلاح‌کننده‌ها (گچ)",
            "شوری شدید": "آبشویی شدید + زهکش زیرزمینی + ارقام شورپسند",
            "شوری بسیار شدید": "اصلاح اساسی یا تغییر کاربری اراضی"
        }
        return recs.get(classification, "پایش")

    # ------------------------------------------------------------------- H12
    def h12_compaction_adjusted_ksat(self, ksat_mm_h: float,
                                     compaction_level: float = 0.0) -> Dict:
        """
        تعدیل هدایت هیدرولیکی اشباع بر اثر تراکم
        فرمول: Ksat_adj = Ksat x (1 - compaction)
        compaction_level: 0 (بدون تراکم) تا 1 (تراکم شدید)
        """
        comp = max(0.0, min(self.cfg.max_compaction, compaction_level))
        ksat_adj = ksat_mm_h * (1.0 - comp)
        
        return {
            "ksat_original_mm_h": round(ksat_mm_h, 2),
            "ksat_adjusted_mm_h": round(ksat_adj, 2),
            "compaction_level": round(comp, 2),
            "reduction_percent": round(comp * 100, 1),
            "interpretation": self._compaction_interpretation(comp)
        }

    def _compaction_interpretation(self, comp: float) -> str:
        if comp < 0.1:
            return "بدون تراکم محسوس"
        elif comp < 0.3:
            return "تراکم ملایم (قابل تحمل)"
        elif comp < 0.5:
            return "تراکم متوسط (نیاز به شخم عمیق)"
        else:
            return "تراکم شدید (نیاز به اقدام فوری)"

    # ------------------------------------------------------------------- H13
    def h13_soil_fertility_index(self, soc_pct: float, n_pct: float,
                                 p_available_ppm: float, k_available_ppm: float,
                                 ph: float, biology_index: float = 0.5) -> Dict:
        """
        شاخص جامع حاصلخیزی خاک (0 تا 1)
        فرمول: Fertility = Sum(w_i x score_i)
        """
        refs = self.cfg.fertility_refs
        w = self.cfg.fertility_weights
        
        soc_score = min(1.0, max(0.0, soc_pct / refs["soc_pct"]))
        n_score = min(1.0, max(0.0, n_pct / refs["n_pct"]))
        p_score = min(1.0, max(0.0, p_available_ppm / refs["p_ppm"]))
        k_score = min(1.0, max(0.0, k_available_ppm / refs["k_ppm"]))
        
        if 6.0 <= ph <= 8.0:
            ph_score = 1.0
        else:
            ph_score = max(0.0, 1.0 - abs(ph - 7.0) / 3.0)
        
        bio_score = max(0.0, min(1.0, biology_index))
        
        fertility = (w["soc"] * soc_score + w["n"] * n_score +
                     w["p"] * p_score + w["k"] * k_score +
                     w["ph"] * ph_score + w["bio"] * bio_score)
        fertility = max(0.0, min(1.0, fertility))
        
        if fertility >= 0.75:
            classification = "حاصلخیز عالی"
        elif fertility >= 0.55:
            classification = "حاصلخیز خوب"
        elif fertility >= 0.35:
            classification = "حاصلخیز متوسط"
        else:
            classification = "حاصلخیز ضعیف"
        
        return {
            "fertility_index": round(fertility, 3),
            "classification": classification,
            "component_scores": {
                "soc": round(soc_score, 2), "nitrogen": round(n_score, 2),
                "phosphorus": round(p_score, 2), "potassium": round(k_score, 2),
                "ph": round(ph_score, 2), "biology": round(bio_score, 2)
            },
            "limiting_factors": self._find_limiting_factors(
                soc_score, n_score, p_score, k_score, ph_score, bio_score)
        }

    def _find_limiting_factors(self, soc, n, p, k, ph, bio) -> list:
        factors = []
        if soc < 0.4:
            factors.append("کربن آلی پایین")
        if n < 0.4:
            factors.append("نیتروژن کم")
        if p < 0.4:
            factors.append("فسفر کم")
        if k < 0.4:
            factors.append("پتاسیم کم")
        if ph < 0.6:
            factors.append("pH نامناسب")
        if bio < 0.4:
            factors.append("بیولوژی خاک ضعیف")
        return factors if factors else ["بدون عامل محدودکننده"]

    # ------------------------------------------------------------------- H14
    def h14_subsidence_risk(self, groundwater_extraction_mm_yr: float,
                            aquifer_thickness_m: float,
                            soil_type: str = "clay") -> Dict:
        """
        ارزیابی ریسک فرونشست زمین
        فرمول: Rate = (Extraction/1000) x Soil_Sensitivity x (50/Aquifer_Thickness)
        """
        sensitivity = self.cfg.soil_sensitivity.get(soil_type.lower(), 0.5)
        
        if aquifer_thickness_m <= 0:
            aquifer_thickness_m = 50.0
        
        subsidence_rate = ((groundwater_extraction_mm_yr / 1000.0) *
                           sensitivity *
                           (50.0 / aquifer_thickness_m))
        
        if subsidence_rate > self.cfg.subsidence_critical_mm_yr:
            risk_level = "بحرانی"
            action = "توقف فوری برداشت + جایگزینی منبع آب"
        elif subsidence_rate > self.cfg.subsidence_severe_mm_yr:
            risk_level = "شدید"
            action = "کاهش 50% برداشت + پایش ماهانه"
        elif subsidence_rate > self.cfg.subsidence_moderate_mm_yr:
            risk_level = "متوسط"
            action = "پایش فصلی + مدیریت برداشت"
        else:
            risk_level = "کم"
            action = "پایش سالانه"
        
        return {
            "subsidence_rate_mm_per_year": round(subsidence_rate, 1),
            "risk_level": risk_level,
            "recommended_action": action,
            "soil_type": soil_type,
            "soil_sensitivity": sensitivity,
            "extraction_mm_yr": groundwater_extraction_mm_yr,
            "aquifer_thickness_m": aquifer_thickness_m
        }


    # ------------------------------------------------------------------ H11+
    def h11_salinity_sodicity_trend(self, ec_initial: float, 
                                     sar_initial: float,
                                     irrigation_water_quality: float,
                                     leaching_fraction: float,
                                     years: int) -> Dict:
        """
        پیش‌بینی روند شوری-سدیک با در نظر گرفتن کیفیت آب آبیاری
        
        پارامترها:
        - ec_initial: شوری اولیه خاک (dS/m)
        - sar_initial: نسبت جذب سدیم اولیه
        - irrigation_water_quality: کیفیت آب آبیاری (EC)
        - leaching_fraction: کسر آبشویی
        - years: تعداد سال‌های پیش‌بینی
        """
        # مدل ساده‌شده روند شوری با آبشویی
        ec_rate = (irrigation_water_quality * 0.1) - (leaching_fraction * ec_initial * 0.05)
        ec_projected = max(0, ec_initial + ec_rate * years)
        
        # روند SAR
        sar_projected = sar_initial * (1 + irrigation_water_quality * 0.02 * years)
        
        # طبقه‌بندی
        if ec_projected < 2:
            ec_class = "غیرشور"
        elif ec_projected < 4:
            ec_class = "شوری ملایم"
        elif ec_projected < 8:
            ec_class = "شوری متوسط"
        elif ec_projected < 16:
            ec_class = "شوری شدید"
        else:
            ec_class = "شوری بسیار شدید"
        
        if sar_projected < 13:
            sar_class = "غیرسدیک"
        else:
            sar_class = "سدیک"
        
        return {
            "ec_initial_ds_m": round(ec_initial, 2),
            "ec_projected_ds_m": round(ec_projected, 2),
            "sar_initial": round(sar_initial, 2),
            "sar_projected": round(sar_projected, 2),
            "ec_classification": ec_class,
            "sar_classification": sar_class,
            "combined_risk": f"{ec_class} + {sar_class}",
            "years_projected": years,
            "leaching_effective": leaching_fraction > 0.15,
            "recommendation": self._salinity_sodicity_recommendation(ec_projected, sar_projected)
        }
    
    def _salinity_sodicity_recommendation(self, ec: float, sar: float) -> str:
        """توصیه‌های مدیریتی بر اساس شوری و سدیمی بودن"""
        if ec > 16 and sar > 13:
            return "شرایط بحرانی: نیاز به اصلاح اساسی با گچ + آبشویی سنگین + زهکشی زیرزمینی"
        elif ec > 8 and sar > 13:
            return "شوری-سدیک شدید: گچ‌پاشی + آبشویی + انتخاب گیاهان شورپسند"
        elif ec > 8:
            return "شوری شدید: آبشویی منظم + بهبود زهکشی + ارقام متحمل"
        elif ec > 4:
            return "شوری متوسط: پایش منظم + مدیریت آبیاری"
        else:
            return "وضعیت قابل قبول: پایش روتین"

    # ------------------------------------------------- گزارش یکپارچه تخریب
    def generate_degradation_report(self,
                                    soc_pct: float,
                                    erosion_rate_t_ha_yr: float,
                                    ec_ds_m: float,
                                    ksat_mm_h: float,
                                    groundwater_extraction_mm_yr: float,
                                    soil_type: str = "loam") -> Dict:
        """تولید گزارش جامع تخریب خاک با ترکیب هر شش الگوریتم"""
        
        report = {
            "model_version": __version__,
            "h09_awc": self.h09_dynamic_awc(150.0, soc_pct),
            "h10_erosion": self.h10_root_depth_decay(100.0, erosion_rate_t_ha_yr, 10),
            "h11_salinity": self.h11_salinity_trend(ec_ds_m, 0.1, 10),
            "h12_compaction": self.h12_compaction_adjusted_ksat(ksat_mm_h, 0.2),
            "h13_fertility": self.h13_soil_fertility_index(
                soc_pct, 0.15, 25.0, 200.0, 7.0, 0.5),
            "h14_subsidence": self.h14_subsidence_risk(
                groundwater_extraction_mm_yr, 50.0, soil_type)
        }
        
        # امتیاز کلی پایداری خاک
        sustainability_score = self._calculate_sustainability_score(report)
        report["overall_sustainability_score"] = sustainability_score
        
        return report

    def _calculate_sustainability_score(self, report: Dict) -> Dict:
        """محاسبه امتیاز کلی پایداری خاک (0 تا 100)"""
        scores = {}
        
        # امتیاز ظرفیت آب (از فاکتور تعدیل)
        awc_factor = report["h09_awc"]["adjustment_factor"]
        scores["water_capacity"] = max(0, min(100, awc_factor * 80))
        
        # امتیاز عمق ریشه (معکوس کاهش)
        depth_loss = report["h10_erosion"]["depth_loss_percent"]
        scores["root_zone"] = max(0, 100 - depth_loss * 2)
        
        # امتیاز شوری (معکوس تأثیر عملکرد)
        salinity_impact = report["h11_salinity"]["estimated_yield_impact_percent"]
        scores["salinity"] = max(0, 100 - salinity_impact)
        
        # امتیاز تراکم (معکوس کاهش)
        compaction_reduction = report["h12_compaction"]["reduction_percent"]
        scores["structure"] = max(0, 100 - compaction_reduction)
        
        # امتیاز حاصلخیزی
        scores["fertility"] = report["h13_fertility"]["fertility_index"] * 100
        
        # امتیاز فرونشست
        subsidence_rate = report["h14_subsidence"]["subsidence_rate_mm_per_year"]
        scores["subsidence"] = max(0, 100 - subsidence_rate * 2)
        
        # میانگین وزنی
        overall = sum(scores.values()) / len(scores)
        
        if overall >= 75:
            status = "پایدار"
        elif overall >= 55:
            status = "نیمه‌پایدار"
        elif overall >= 35:
            status = "در معرض تخریب"
        else:
            status = "تخریب‌شده"
        
        return {
            "overall_score": round(overall, 1),
            "status": status,
            "component_scores": {k: round(v, 1) for k, v in scores.items()}
        }

    # ------------------------------------------------- تصحیح خروجی مدل‌ها
    def apply_soil_corrections(self, result, soil_params: Dict) -> object:
        """
        اعمال تصحیحات خاک به خروجی مدل‌های رشد (مثل AquaCrop)
        """
        correction_factor = 1.0
        
        # تأثیر شوری
        ec = soil_params.get("ec_ds_m", 0)
        if ec > 4:
            correction_factor *= max(0.5, 1.0 - (ec - 4) * 0.05)
        
        # تأثیر حاصلخیزی
        fertility = soil_params.get("fertility_index", 0.5)
        if fertility < 0.4:
            correction_factor *= (0.7 + fertility * 0.75)
        
        # تأثیر تراکم
        compaction = soil_params.get("compaction_level", 0)
        if compaction > 0.3:
            correction_factor *= (1.0 - compaction * 0.3)
        
        correction_factor = max(0.3, min(1.0, correction_factor))
        
        if hasattr(result, "yield_t_ha"):
            result.yield_t_ha = round(result.yield_t_ha * correction_factor, 2)
        if hasattr(result, "biomass_t_ha"):
            result.biomass_t_ha = round(result.biomass_t_ha * correction_factor, 2)
        
        try:
            result.warnings = list(result.warnings) + [
                "Soil correction x%.2f (EC=%.1f, fertility=%.2f, compaction=%.2f)"
                % (correction_factor, ec, fertility, compaction)]
        except Exception:
            pass
        
        return result
