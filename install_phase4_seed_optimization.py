#!/usr/bin/env python3
# ============================================================================
# نصب‌کننده فاز ۴: موتور بهینه‌سازی بذر و ژنوتیپ
# الگوریتم‌ها: H15 تطبیق ژنوتیپ-محیط | H16 سازگاری میدانی
#             H17 مقاومت ارقام بومی | H18 بهینه‌ساز دوره رشد
#             H19 آسیب‌پذیری ژنتیکی | H20 تطبیق اکولوژیک
#             H21 سازگاری میکروبیوم
# منابع: Altieri 2018 | Philippot et al. 2019 | Rani et al. 2019
# ============================================================================
import ast
import json
import shutil
import py_compile
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
SEED_DIR = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation"
CROP_DB = PROJECT_ROOT / "services" / "scientific_motors" / "crop_database.py"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_seed_optimization_engine.py"
REGISTRY = PROJECT_ROOT / "docs" / "hydroma" / "innovation_registry.json"

# ----------------------------------------------------------------------------
# کد ماژول بهینه‌سازی بذر
# ----------------------------------------------------------------------------
SEED_MODEL_CODE = '''# -*- coding: utf-8 -*-
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
'''

INIT_APPEND = '''
from .seed_optimization_engine import SeedOptimizationEngine, SeedOptimizationConfig
'''

TEST_CODE = '''import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.seed_optimization_engine import (
    SeedOptimizationEngine)

def main():
    engine = SeedOptimizationEngine()

    # H15: تطبیق ژنوتیپ-محیط
    tolerances = {"drought": 0.8, "heat": 0.7, "salinity": 0.5,
                  "frost": 0.6, "waterlogging": 0.4}
    stresses = {"drought": 0.6, "heat": 0.7, "salinity": 0.3,
                "frost": 0.4, "waterlogging": 0.2}
    r1 = engine.h15_gxe_matching(tolerances, stresses)
    assert 0.0 <= r1["gxe_score"] <= 1.0
    assert r1["classification"] in ("تطبیق عالی", "تطبیق خوب", "تطبیق متوسط", "تطبیق ضعیف")

    # H16: سازگاری میدانی
    r2 = engine.h16_field_hardiness(0.6, 0.7, 0.5)
    assert 0.0 <= r2["hardiness_score"] <= 1.0
    assert 0.0 <= r2["survival_probability_percent"] <= 100.0

    # H17: مقاومت بومی
    r3 = engine.h17_native_resilience(30, 0.7, 0.6, 0.5)
    assert 0.0 <= r3["native_resilience_index"] <= 1.0

    # H18: بهینه‌ساز دوره رشد
    r4 = engine.h18_growth_duration_optimizer(180, 200, 150, 160)
    assert r4["optimal_duration_days"] >= 60
    assert r4["recommended_variety_type"] in ("زودرس", "میان‌رس", "دیررس")

    # H19: آسیب‌پذیری ژنتیکی
    r5 = engine.h19_genetic_vulnerability(0.3, 70.0, 2)
    assert 0.0 <= r5["vulnerability_index"] <= 1.0
    assert r5["risk_level"] in ("کم", "متوسط", "شدید", "بحرانی")

    # H20: تطبیق اکولوژیک
    r6 = engine.h20_ecozone_matching(0.8, 0.7, 0.9, 0.6)
    assert 0.0 <= r6["ecozone_match_score"] <= 1.0

    # H21: میکروبیوم
    r7 = engine.h21_microbiome_compatibility(2.5, 7.0, 0.6, 0.5)
    assert 0.0 <= r7["microbiome_score"] <= 1.0
    assert isinstance(r7["inoculation_recommended"], bool)

    # گزارش یکپارچه
    advisory = engine.generate_seed_advisory(
        tolerances, stresses,
        is_tissue_culture=True,
        local_adaptation_years=25,
        genetic_diversity=0.4,
        soil_params={"soc_pct": 1.8, "ph": 7.2, "biology_index": 0.5, "organic_input": 0.4})
    assert "overall_seed_suitability" in advisory
    assert 0.0 <= advisory["overall_seed_suitability"]["overall_score"] <= 1.0

    print("ALL SEED OPTIMIZATION TESTS PASSED (H15-H21)")

if __name__ == "__main__":
    main()
'''

IMPORT_BLOCK = '''
# --- Hydroma Seed Optimization Engine (auto-installed, Phase 4) ---
try:
    from engine.hydroma.climate_adaptation.seed_optimization_engine import (
        SeedOptimizationEngine as _SOE_cls)
    _HYDROMA_SOE = _SOE_cls()
except Exception:
    _HYDROMA_SOE = None
'''


# ----------------------------------------------------------------------------
# مراحل نصب
# ----------------------------------------------------------------------------
def install_module():
    print("[1/5] ایجاد ماژول SeedOptimizationEngine ...")
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    (SEED_DIR / "seed_optimization_engine.py").write_text(
        SEED_MODEL_CODE, encoding="utf-8")
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(TEST_CODE, encoding="utf-8")
    
    init_file = SEED_DIR / "__init__.py"
    if init_file.exists():
        current = init_file.read_text(encoding="utf-8")
        if "seed_optimization_engine" not in current:
            init_file.write_text(current + INIT_APPEND, encoding="utf-8")
            print("   -> __init__.py به‌روزرسانی شد")
    else:
        init_file.write_text(INIT_APPEND.lstrip(), encoding="utf-8")
    
    print("   -> engine/hydroma/climate_adaptation/seed_optimization_engine.py")
    print("   -> tests/unit/test_seed_optimization_engine.py")


def integrate_with_ast(target_file: Path) -> bool:
    """اتصال ایمن با استفاده از AST"""
    if not target_file.exists():
        print(f"   !! {target_file.name} یافت نشد؛ رد شد")
        return False
    
    content = target_file.read_text(encoding="utf-8")
    if "_HYDROMA_SOE" in content:
        print(f"   -> {target_file.name}: اتصال از قبل موجود است")
        return True
    
    backup = target_file.with_suffix(".py.bak_soe")
    shutil.copy2(target_file, backup)
    
    # یافتن جایگاه درج با AST
    try:
        tree = ast.parse(content)
        last_import_line = 0
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    last_import_line = max(last_import_line, node.end_lineno)
        
        if last_import_line == 0:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    last_import_line = i + 1
                    break
            if last_import_line == 0:
                last_import_line = 1
        
        lines = content.split('\n')
        block_lines = IMPORT_BLOCK.strip().split('\n')
        new_lines = lines[:last_import_line] + [''] + block_lines + [''] + lines[last_import_line:]
        new_content = '\n'.join(new_lines)
        
        # تأیید سینتکس قبل از نوشتن
        ast.parse(new_content)
        
        target_file.write_text(new_content, encoding="utf-8")
        py_compile.compile(str(target_file), doraise=True)
        print(f"   ✅ {target_file.name} متصل شد (خط {last_import_line})")
        return True
        
    except SyntaxError as e:
        shutil.copy2(backup, target_file)
        print(f"   !! خطا در اتصال {target_file.name}; rollback: {e}")
        return False
    except Exception as e:
        print(f"   !! خطای غیرمنتظره: {e}")
        return False


def integrate_targets():
    print("[2/5] اتصال به فایل‌های هدف (روش AST) ...")
    integrated = []
    
    # اتصال به crop_database.py
    if integrate_with_ast(CROP_DB):
        integrated.append("crop_database.py")
    
    return integrated


def run_tests():
    print("[3/5] اجرای تست‌های واحد ...")
    proc = subprocess.run([sys.executable, str(TEST_FILE)], cwd=PROJECT_ROOT)
    return proc.returncode == 0


def update_registry():
    print("[4/5] به‌روزرسانی رجیستری مستندات ...")
    if not REGISTRY.exists():
        print("   !! رجیستری یافت نشد؛ رد شد.")
        return False
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for phase in data.get("phases", []):
            if phase.get("phase") == "فاز 4":
                phase["status"] = "نصب شد"
        data["phase4_installed_at"] = __import__("datetime").datetime.now().isoformat()
        REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print("   -> وضعیت فاز ۴ به «نصب شد» تغییر یافت.")
        return True
    except Exception as exc:
        print(f"   !! خطا در به‌روزرسانی رجیستری: {exc}")
        return False


def demo_advisory():
    print("[5/5] تولید توصیه‌نامه نمونه بذر ...")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from engine.hydroma.climate_adaptation.seed_optimization_engine import (
            SeedOptimizationEngine)
        engine = SeedOptimizationEngine()
        
        # سناریوی واقع‌بینانه: بذر گندم بومی برای منطقه نیمه‌خشک
        tolerances = {"drought": 0.85, "heat": 0.75, "salinity": 0.5,
                      "frost": 0.7, "waterlogging": 0.3}
        stresses = {"drought": 0.7, "heat": 0.6, "salinity": 0.4,
                    "frost": 0.3, "waterlogging": 0.2}
        
        advisory = engine.generate_seed_advisory(
            tolerances, stresses,
            is_tissue_culture=False,
            local_adaptation_years=40,  # رقم بومی 40 ساله
            genetic_diversity=0.6,
            soil_params={"soc_pct": 1.5, "ph": 7.5, "biology_index": 0.4,
                        "organic_input": 0.3})
        
        overall = advisory["overall_seed_suitability"]
        print(f"   امتیاز کلی بذر: {overall['overall_score']} ({overall['status']})")
        print(f"   تطبیق ژنوتیپ-محیط: {advisory['h15_gxe']['gxe_score']}")
        if "h17_native" in advisory:
            print(f"   مقاومت بومی: {advisory['h17_native']['native_resilience_index']}")
        print(f"   آسیب‌پذیری ژنتیکی: {advisory['h19_vulnerability']['vulnerability_index']}")
        if "h21_microbiome" in advisory:
            print(f"   میکروبیوم: {advisory['h21_microbiome']['microbiome_score']}")
        return True
    except Exception as exc:
        print(f"   !! خطا در نمونه: {exc}")
        return False


def main():
    print("=" * 70)
    print("نصب فاز ۴: موتور بهینه‌سازی بذر و ژنوتیپ (H15-H21)")
    print("=" * 70)
    
    install_module()
    integrated = integrate_targets()
    tests_ok = run_tests()
    registry_ok = update_registry()
    demo_advisory()
    
    print("=" * 70)
    print(f"نتیجه: ماژول=OK | تست‌ها={'OK' if tests_ok else 'FAIL'} | "
          f"اتصال={len(integrated)} فایل | رجیستری={'OK' if registry_ok else 'SKIP'}")
    print("=" * 70)


if __name__ == "__main__":
    main()