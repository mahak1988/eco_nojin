# -*- coding: utf-8 -*-
# ============================================================================
# Hydroma Seed Optimization & Genotype-Environment Matching Engine - Phase 4
# Algorithms: H15 GxE Matching | H16 Field Hardiness | H17 Native Resilience
#             H18 Growth Duration | H19 Genetic Vulnerability
#             H20 Ecozone Matching | H21 Microbiome Compatibility
# References: Altieri 2018; Philippot et al. 2019; Rani et al. 2019
# ============================================================================
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__version__ = "1.0.0"


@dataclass
class SeedOptimizationConfig:
    # H15: تطبیق ژنوتیپ-محیط
    stress_tolerance_weights: Dict = field(default_factory=lambda: {
        "drought": 0.30, "heat": 0.25, "salinity": 0.20,
        "frost": 0.15, "waterlogging": 0.10
    })
    
    # H16: سازگاری میدانی
    hardiness_weights: Dict = field(default_factory=lambda: {
        "acclimatization": 0.35, "root_quality": 0.30, "defense": 0.35
    })
    
    # H17: مقاومت ارقام بومی
    native_weights: Dict = field(default_factory=lambda: {
        "local_adaptation": 0.30, "drought_history": 0.25,
        "pest_resistance": 0.20, "genetic_diversity": 0.25
    })
    
    # H18: بهینه‌ساز دوره رشد
    duration_buffer_days: int = 10
    
    # H19: آسیب‌پذیری ژنتیکی
    vulnerability_threshold: float = 0.7
    
    # H20: تطبیق اکولوژیک
    ecozone_weights: Dict = field(default_factory=lambda: {
        "koppen": 0.35, "soil": 0.25, "altitude": 0.20, "native": 0.20
    })
    
    # H21: سازگاری میکروبیوم
    microbiome_weights: Dict = field(default_factory=lambda: {
        "soc": 0.30, "ph": 0.25, "biology": 0.25, "organic_input": 0.20
    })


# ============================================================================
class SeedOptimizationEngine:
    # ------------------------------------------------------------------ init
    def __init__(self, config: Optional[SeedOptimizationConfig] = None):
        self.cfg = config or SeedOptimizationConfig()

    # ------------------------------------------------------------------- H15
    def h15_gxe_matching(self, variety_tolerances: Dict[str, float],
                         site_stress_profile: Dict[str, float]) -> Dict:
        """
        تطبیق ژنوتیپ-محیط (GxE Matching)
        مقایسه تحمل‌های رقم با شرایط تنش سایت
        ورودی: تحمل‌های رقم و پروفایل تنش سایت (هر دو 0 تا 1)
        """
        w = self.cfg.stress_tolerance_weights
        score = 0.0
        total_weight = 0.0
        mismatches = []
        
        for stress_type, weight in w.items():
            tolerance = variety_tolerances.get(stress_type, 0.5)
            site_stress = site_stress_profile.get(stress_type, 0.5)
            
            # اگر تحمل رقم >= تنش سایت، امتیاز کامل
            if tolerance >= site_stress:
                stress_score = 1.0
            else:
                # در غیر این صورت، امتیاز متناسب با شکاف
                gap = site_stress - tolerance
                stress_score = max(0.0, 1.0 - gap * 2.0)
                if gap > 0.3:
                    mismatches.append(stress_type)
            
            score += weight * stress_score
            total_weight += weight
        
        score = score / total_weight if total_weight > 0 else 0.0
        
        if score >= 0.8:
            classification = "تطبیق عالی"
        elif score >= 0.6:
            classification = "تطبیق خوب"
        elif score >= 0.4:
            classification = "تطبیق متوسط"
        else:
            classification = "تطبیق ضعیف"
        
        return {
            "gxe_score": round(score, 3),
            "classification": classification,
            "stress_mismatches": mismatches,
            "recommendation": self._gxe_recommendation(score, mismatches)
        }

    def _gxe_recommendation(self, score: float, mismatches: List[str]) -> str:
        if score >= 0.8:
            return "رقم مناسب برای این محیط است"
        elif score >= 0.6:
            return "رقم قابل قبول با مدیریت ریسک"
        elif mismatches:
            return "رقم جایگزین با تحمل بالاتر در: " + ", ".join(mismatches)
        else:
            return "نیاز به ارزیابی بیشتر"

    # ------------------------------------------------------------------- H16
    def h16_field_hardiness(self, acclimatization_score: float,
                            root_quality_score: float,
                            defense_score: float) -> Dict:
        """
        امتیاز سازگاری میدانی (Field Hardiness Score)
        برای نهال‌های کشت بافت و بذور آزمایشگاهی
        پیش‌بینی درصد موفقیت انتقال به مزرعه
        """
        w = self.cfg.hardiness_weights
        score = (w["acclimatization"] * acclimatization_score +
                 w["root_quality"] * root_quality_score +
                 w["defense"] * defense_score)
        score = max(0.0, min(1.0, score))
        
        survival_probability = score * 0.85 + 0.10  # حداقل 10% شانس بقا
        
        if score >= 0.75:
            classification = "آماده انتقال به مزرعه"
        elif score >= 0.55:
            classification = "نیاز به سازگاری تدریجی"
        elif score >= 0.35:
            classification = "نیاز به دوره سازگاری طولانی"
        else:
            classification = "غیرآماده - ریسک بالای تلفات"
        
        return {
            "hardiness_score": round(score, 3),
            "survival_probability_percent": round(survival_probability * 100, 1),
            "classification": classification,
            "acclimatization_days_needed": self._calc_acclimatization_days(score)
        }

    def _calc_acclimatization_days(self, score: float) -> int:
        if score >= 0.75:
            return 7
        elif score >= 0.55:
            return 21
        elif score >= 0.35:
            return 45
        else:
            return 90

    # ------------------------------------------------------------------- H17
    def h17_native_resilience(self, local_adaptation_years: int,
                              drought_survival_history: float,
                              pest_resistance_score: float,
                              genetic_diversity_index: float) -> Dict:
        """
        شاخص مقاومت ارقام بومی (Native Resilience Index)
        ارزیابی ارقام بومی در مقابل ارقام اصلاح‌شده
        """
        w = self.cfg.native_weights
        
        # تبدیل سال‌های سازگاری به امتیاز (حداکثر 50 سال = امتیاز کامل)
        adaptation_score = min(1.0, local_adaptation_years / 50.0)
        
        score = (w["local_adaptation"] * adaptation_score +
                 w["drought_history"] * drought_survival_history +
                 w["pest_resistance"] * pest_resistance_score +
                 w["genetic_diversity"] * genetic_diversity_index)
        score = max(0.0, min(1.0, score))
        
        if score >= 0.75:
            classification = "رقم بومی بسیار مقاوم"
        elif score >= 0.55:
            classification = "رقم بومی مقاوم"
        elif score >= 0.35:
            classification = "رقم بومی با مقاومت متوسط"
        else:
            classification = "رقم بومی با مقاومت پایین"
        
        return {
            "native_resilience_index": round(score, 3),
            "classification": classification,
            "conservation_priority": self._conservation_priority(score),
            "recommendation": self._native_recommendation(score)
        }

    def _conservation_priority(self, score: float) -> str:
        if score >= 0.75:
            return "اولویت حفاظتی بالا"
        elif score >= 0.55:
            return "اولویت حفاظتی متوسط"
        else:
            return "اولویت حفاظتی پایین"

    def _native_recommendation(self, score: float) -> str:
        if score >= 0.75:
            return "حفظ و تکثیر؛ جایگزینی ارقام وارداتی"
        elif score >= 0.55:
            return "حفظ و ارزیابی بیشتر"
        else:
            return "پایش و مستندسازی"

    # ------------------------------------------------------------------- H18
    def h18_growth_duration_optimizer(self, rain_window_days: int,
                                      temp_window_days: int,
                                      stress_onset_day: int,
                                      base_duration_days: int) -> Dict:
        """
        بهینه‌ساز دوره رشد (Growth Duration Optimizer)
        تعیین دوره رشد بهینه بر اساس پنجره‌های اقلیمی
        """
        # پنجره مؤثر رشد = حداقل پنجره‌های موجود
        effective_window = min(rain_window_days, temp_window_days, stress_onset_day)
        effective_window -= self.cfg.duration_buffer_days  # فاصله ایمنی
        
        # تعیین نوع رقم
        if base_duration_days <= effective_window:
            variety_type = "دیررس"
            adjustment = 0
        elif base_duration_days - 30 <= effective_window:
            variety_type = "میان‌رس"
            adjustment = -20
        else:
            variety_type = "زودرس"
            adjustment = -40
        
        optimal_duration = max(60, base_duration_days + adjustment)
        
        return {
            "effective_window_days": effective_window,
            "base_duration_days": base_duration_days,
            "optimal_duration_days": optimal_duration,
            "recommended_variety_type": variety_type,
            "adjustment_days": adjustment,
            "risk_assessment": self._duration_risk(effective_window, optimal_duration)
        }

    def _duration_risk(self, window: int, duration: int) -> str:
        if duration <= window * 0.7:
            return "ریسک پایین"
        elif duration <= window * 0.9:
            return "ریسک متوسط"
        else:
            return "ریسک بالا - دوره رشد نزدیک به محدودیت پنجره"

    # ------------------------------------------------------------------- H19
    def h19_genetic_vulnerability(self, genetic_diversity_index: float,
                                  monoculture_area_percent: float,
                                  number_of_varieties: int) -> Dict:
        """
        ارزیابی آسیب‌پذیری ژنتیکی (Genetic Vulnerability Assessment)
        هشدار در مورد یکنواختی ژنتیکی و کشت تک‌رقمی
        """
        vulnerability = 1.0 - genetic_diversity_index
        
        # افزایش آسیب‌پذیری با تک‌کشتی
        monoculture_penalty = monoculture_area_percent / 100.0 * 0.3
        vulnerability = min(1.0, vulnerability + monoculture_penalty)
        
        # کاهش آسیب‌پذیری با تنوع ارقام
        variety_bonus = min(0.2, (number_of_varieties - 1) * 0.02)
        vulnerability = max(0.0, vulnerability - variety_bonus)
        
        if vulnerability >= 0.7:
            risk_level = "بحرانی"
            epidemic_risk = "بسیار بالا"
        elif vulnerability >= 0.5:
            risk_level = "شدید"
            epidemic_risk = "بالا"
        elif vulnerability >= 0.3:
            risk_level = "متوسط"
            epidemic_risk = "متوسط"
        else:
            risk_level = "کم"
            epidemic_risk = "پایین"
        
        return {
            "vulnerability_index": round(vulnerability, 3),
            "risk_level": risk_level,
            "epidemic_risk": epidemic_risk,
            "diversity_index": round(genetic_diversity_index, 3),
            "recommendation": self._vulnerability_recommendation(vulnerability)
        }

    def _vulnerability_recommendation(self, vulnerability: float) -> str:
        if vulnerability >= 0.7:
            return "تنوع فوری ارقام; کاهش تک‌کشتی; ذخیره بذر بومی"
        elif vulnerability >= 0.5:
            return "افزایش تنوع ارقام; پایش بیماری‌ها"
        elif vulnerability >= 0.3:
            return "حفظ تنوع موجود; ارزیابی دوره‌ای"
        else:
            return "وضعیت مناسب; پایش روتین"

    # ------------------------------------------------------------------- H20
    def h20_ecozone_matching(self, koppen_fit: float, soil_fit: float,
                             altitude_fit: float, native_presence: float) -> Dict:
        """
        تطبیق بذر با منطقه اکولوژیک (Ecozone Seed Matching)
        جلوگیری از واردات بذر نامناسب
        """
        w = self.cfg.ecozone_weights
        score = (w["koppen"] * koppen_fit +
                 w["soil"] * soil_fit +
                 w["altitude"] * altitude_fit +
                 w["native"] * native_presence)
        score = max(0.0, min(1.0, score))
        
        if score >= 0.75:
            classification = "تطبیق اکولوژیک عالی"
            import_risk = "پایین"
        elif score >= 0.55:
            classification = "تطبیق اکولوژیک خوب"
            import_risk = "متوسط"
        elif score >= 0.35:
            classification = "تطبیق اکولوژیک ضعیف"
            import_risk = "بالا"
        else:
            classification = "عدم تطبیق اکولوژیک"
            import_risk = "بسیار بالا"
        
        return {
            "ecozone_match_score": round(score, 3),
            "classification": classification,
            "import_risk": import_risk,
            "recommendation": self._ecozone_recommendation(score)
        }

    def _ecozone_recommendation(self, score: float) -> str:
        if score >= 0.75:
            return "مناسب برای کشت; بدون محدودیت"
        elif score >= 0.55:
            return "قابل کشت با پایش; آزمایش محدود قبل از کشت گسترده"
        elif score >= 0.35:
            return "نیاز به آزمایش‌های سازگاری; کشت محدود"
        else:
            return "غیرمناسب; جلوگیری از واردات و کشت"

    # ------------------------------------------------------------------- H21
    def h21_microbiome_compatibility(self, soc_pct: float, ph: float,
                                     biology_index: float,
                                     organic_input_history: float) -> Dict:
        """
        سازگاری میکروبیوم (Microbiome Compatibility Score)
        ارزیابی سازگاری بذر/نهال با میکروبیوم خاک
        """
        w = self.cfg.microbiome_weights
        
        # امتیاز کربن آلی (بهینه: 2-4%)
        soc_score = min(1.0, soc_pct / 3.0)
        
        # امتیاز pH (بهینه: 6-7.5)
        if 6.0 <= ph <= 7.5:
            ph_score = 1.0
        else:
            ph_score = max(0.0, 1.0 - abs(ph - 6.75) / 3.0)
        
        score = (w["soc"] * soc_score +
                 w["ph"] * ph_score +
                 w["biology"] * biology_index +
                 w["organic_input"] * organic_input_history)
        score = max(0.0, min(1.0, score))
        
        if score >= 0.7:
            classification = "میکروبیوم سالم و سازگار"
            inoculation_needed = False
        elif score >= 0.5:
            classification = "میکروبیوم نیمه‌سالم"
            inoculation_needed = True
        else:
            classification = "میکروبیوم تخریب‌شده"
            inoculation_needed = True
        
        return {
            "microbiome_score": round(score, 3),
            "classification": classification,
            "inoculation_recommended": inoculation_needed,
            "recommendation": self._microbiome_recommendation(score)
        }

    def _microbiome_recommendation(self, score: float) -> str:
        if score >= 0.7:
            return "خاک آماده کشت; نیازی به مایه‌زنی نیست"
        elif score >= 0.5:
            return "مایه‌زنی میکروبی توصیه می‌شود; افزایش ماده آلی"
        else:
            return "احیای میکروبیوم ضروری; کمپوست + مایه‌زنی + کاهش شیمیایی"

    # ------------------------------------------------- گزارش یکپارچه بذر
    def generate_seed_advisory(self, variety_tolerances: Dict[str, float],
                               site_stress_profile: Dict[str, float],
                               is_tissue_culture: bool = False,
                               local_adaptation_years: int = 0,
                               genetic_diversity: float = 0.5,
                               soil_params: Optional[Dict] = None) -> Dict:
        """تولید توصیه‌نامه جامع بذر با ترکیب هر هفت الگوریتم"""
        
        advisory = {"model_version": __version__}
        
        # H15: تطبیق ژنوتیپ-محیط
        advisory["h15_gxe"] = self.h15_gxe_matching(
            variety_tolerances, site_stress_profile)
        
        # H16: سازگاری میدانی (فقط برای کشت بافت)
        if is_tissue_culture:
            advisory["h16_hardiness"] = self.h16_field_hardiness(
                acclimatization_score=0.4,
                root_quality_score=0.5,
                defense_score=0.3)
        
        # H17: مقاومت بومی
        if local_adaptation_years > 0:
            advisory["h17_native"] = self.h17_native_resilience(
                local_adaptation_years, 0.6, 0.5, genetic_diversity)
        
        # H19: آسیب‌پذیری ژنتیکی
        advisory["h19_vulnerability"] = self.h19_genetic_vulnerability(
            genetic_diversity, 60.0, 3)
        
        # H21: میکروبیوم
        if soil_params:
            advisory["h21_microbiome"] = self.h21_microbiome_compatibility(
                soil_params.get("soc_pct", 1.5),
                soil_params.get("ph", 7.0),
                soil_params.get("biology_index", 0.5),
                soil_params.get("organic_input", 0.3))
        
        # امتیاز کلی مناسب بودن بذر
        advisory["overall_seed_suitability"] = self._calculate_overall_suitability(advisory)
        
        return advisory

    def _calculate_overall_suitability(self, advisory: Dict) -> Dict:
        scores = []
        
        if "h15_gxe" in advisory:
            scores.append(advisory["h15_gxe"]["gxe_score"])
        if "h16_hardiness" in advisory:
            scores.append(advisory["h16_hardiness"]["hardiness_score"])
        if "h17_native" in advisory:
            scores.append(advisory["h17_native"]["native_resilience_index"])
        if "h19_vulnerability" in advisory:
            scores.append(1.0 - advisory["h19_vulnerability"]["vulnerability_index"])
        if "h21_microbiome" in advisory:
            scores.append(advisory["h21_microbiome"]["microbiome_score"])
        
        overall = sum(scores) / len(scores) if scores else 0.0
        
        if overall >= 0.75:
            status = "بذر بسیار مناسب"
        elif overall >= 0.55:
            status = "بذر مناسب"
        elif overall >= 0.35:
            status = "بذر با ریسک متوسط"
        else:
            status = "بذر نامناسب"
        
        return {
            "overall_score": round(overall, 3),
            "status": status,
            "components_evaluated": len(scores)
        }

    # ------------------------------------------------- تصحیح خروجی مدل‌ها
    def apply_seed_corrections(self, result, seed_params: Dict) -> object:
        """اعمال تصحیحات بذر به خروجی مدل‌های رشد"""
        correction_factor = 1.0
        
        # تأثیر سازگاری ژنوتیپ-محیط
        gxe_score = seed_params.get("gxe_score", 0.7)
        if gxe_score < 0.5:
            correction_factor *= (0.6 + gxe_score * 0.8)
        
        # تأثیر سازگاری میدانی (برای کشت بافت)
        if seed_params.get("is_tissue_culture", False):
            hardiness = seed_params.get("hardiness_score", 0.5)
            correction_factor *= (0.5 + hardiness * 0.5)
        
        # تأثیر میکروبیوم
        microbiome = seed_params.get("microbiome_score", 0.5)
        if microbiome < 0.4:
            correction_factor *= (0.7 + microbiome * 0.75)
        
        correction_factor = max(0.3, min(1.0, correction_factor))
        
        if hasattr(result, "yield_t_ha"):
            result.yield_t_ha = round(result.yield_t_ha * correction_factor, 2)
        if hasattr(result, "biomass_t_ha"):
            result.biomass_t_ha = round(result.biomass_t_ha * correction_factor, 2)
        
        try:
            result.warnings = list(result.warnings) + [
                "Seed correction x%.2f (GxE=%.2f, hardiness=%.2f, microbiome=%.2f)"
                % (correction_factor,
                   seed_params.get("gxe_score", 0.7),
                   seed_params.get("hardiness_score", 0.5),
                   seed_params.get("microbiome_score", 0.5))]
        except Exception:
            pass
        
        return result
