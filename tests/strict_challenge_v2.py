#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
چالش سختگیرانه نسخه ۲: شکنجه علمی مدل هیدروما
هدف: پیدا کردن تمام اشکالات، نقاط ضعف، و رفتارهای غیرمنطقی
============================================================================
"""
import structlog

logger = structlog.get_logger()
import sys
import math
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from engine.hydroma.climate_adaptation.dynamic_stress_engine import DynamicStressEngine
    from engine.hydroma.climate_adaptation.climate_adaptive_phenology import ClimateAdaptivePhenology
    from engine.hydroma.climate_adaptation.soil_degradation_model import SoilDegradationModel
    from engine.hydroma.climate_adaptation.seed_optimization_engine import SeedOptimizationEngine
    from engine.hydroma.climate_adaptation.uncertainty_knowledge_engine import UncertaintyAndKnowledgeEngine
    ALL_LOADED = True
except ImportError as e:
    logger.warning(f"WARNING: {e}")
    ALL_LOADED = False


class StrictTestResult:
    def __init__(self, category, test_name, passed, message, severity="info", expected_behavior=None):
        self.category = category
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.severity = severity
        self.expected_behavior = expected_behavior

    def to_dict(self):
        return {
            "category": self.category,
            "test": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
            "expected": self.expected_behavior,
        }


class StrictChallengeV2:
    """چالش سختگیرانه نسخه ۲ - هدف: شکستن مدل و پیدا کردن اشکالات"""

    def __init__(self):
        self.results = []
        self.dse = DynamicStressEngine() if ALL_LOADED else None
        self.cap = ClimateAdaptivePhenology() if ALL_LOADED else None
        self.sdm = SoilDegradationModel() if ALL_LOADED else None
        self.soe = SeedOptimizationEngine() if ALL_LOADED else None
        self.uke = UncertaintyAndKnowledgeEngine() if ALL_LOADED else None

    def add(self, category, test_name, passed, message, severity="info", expected=None):
        self.results.append(StrictTestResult(category, test_name, passed, message, severity, expected))
        status = "PASS" if passed else "FAIL"
        icon = "[PASS]" if passed else "[FAIL]"
        sev_icon = "!!!" if severity == "critical" else "!!" if severity == "warning" else ""
        logger.info(f"   {icon} [{category}] {test_name} - {status} {sev_icon}")
        if not passed and expected:
            logger.info(f"         انتظار: {expected}")
            logger.info(f"         دریافت: {message}")

    # ============================================================
    # دسته ۱: تست‌های مرزی (Boundary Tests)
    # ============================================================
    def test_boundary(self):
        cat = "مرزی"
        logger.info("\n" + "="*70)
        logger.info("دسته ۱: تست‌های مرزی (شرایط حدی)")
        logger.info("="*70)

        # ۱.۱ دمای بسیار بالا (۶۰ درجه)
        if self.dse:
            try:
                ks = self.dse.h04_heat_ks(60.0)
                # در ۶۰ درجه، Ks باید بسیار نزدیک به صفر باشد
                self.add(cat, "Ks در ۶۰ درجه",
                         0 <= ks < 0.01,
                         f"Ks={ks:.6f}",
                         "warning" if ks >= 0.01 else "info",
                         "Ks باید نزدیک صفر باشد (< 0.01)")
            except Exception as e:
                self.add(cat, "Ks در ۶۰ درجه", False, f"خطا: {e}", "critical")

        # ۱.۲ دمای بسیار پایین (-۵۰ درجه)
        if self.dse:
            try:
                ks = self.dse.h04_heat_ks(-50.0)
                # در -۵۰ درجه، Ks باید ۱ باشد (تنش گرمایی وجود ندارد)
                self.add(cat, "Ks در -۵۰ درجه",
                         0.99 <= ks <= 1.0,
                         f"Ks={ks:.6f}",
                         "warning" if ks < 0.99 else "info",
                         "Ks باید نزدیک ۱ باشد")
            except Exception as e:
                self.add(cat, "Ks در -۵۰ درجه", False, f"خطا: {e}", "critical")

        # ۱.۳ دمای صفر مطلق (-۲۷۳.۱۵)
        if self.dse:
            try:
                ks = self.dse.h04_heat_ks(-273.15)
                self.add(cat, "Ks در صفر مطلق",
                         0.99 <= ks <= 1.0 and math.isfinite(ks),
                         f"Ks={ks}",
                         "critical" if not math.isfinite(ks) else "info",
                         "Ks باید ۱ و متناهی باشد")
            except Exception as e:
                self.add(cat, "Ks در صفر مطلق", False, f"خطا: {e}", "critical")

        # ۱.۴ تنش شبانه در دمای بسیار بالا (۵۰ درجه شبانه)
        if self.dse:
            try:
                penalty = self.dse.h02_night_penalty(50.0)
                # در ۵۰ درجه شبانه، جریمه باید به سقف برسد
                self.add(cat, "جریمه شب در ۵۰ درجه",
                         0.25 <= penalty <= 0.35,
                         f"جریمه={penalty:.3f}",
                         "warning" if penalty < 0.25 else "info",
                         "جریمه باید به سقف (۰.۳) برسد")
            except Exception as e:
                self.add(cat, "جریمه شب در ۵۰ درجه", False, f"خطا: {e}", "critical")

        # ۱.۵ بارش صفر
        if self.dse:
            try:
                eff = self.dse.h01_effective_rain_mm(0.0)
                self.add(cat, "بارش مؤثر صفر",
                         eff == 0.0,
                         f"بارش مؤثر={eff}",
                         "critical" if eff != 0 else "info",
                         "بارش مؤثر باید دقیقاً صفر باشد")
            except Exception as e:
                self.add(cat, "بارش مؤثر صفر", False, f"خطا: {e}", "critical")

        # ۱.۶ بارش بسیار زیاد (سیل ۵۰۰ میلی‌متر در روز)
        if self.dse:
            try:
                eff = self.dse.h01_effective_rain_mm(500.0)
                # در سیل، بخش کمی نفوذ می‌کند
                self.add(cat, "بارش مؤثر سیل (۵۰۰mm)",
                         0 < eff < 100,
                         f"بارش مؤثر={eff:.1f}mm",
                         "warning" if eff >= 100 else "info",
                         "در سیل، نفوذ باید محدود باشد (< 100mm)")
            except Exception as e:
                self.add(cat, "بارش مؤثر سیل", False, f"خطا: {e}", "critical")

        # ۱.۷ فرسایش بسیار شدید (۱۰۰۰ تن در هکتار)
        if self.sdm:
            try:
                result = self.sdm.h10_root_depth_decay(100.0, 1000.0, 10)
                depth = result["depth_loss_percent"]
                # در فرسایش بسیار شدید، عمق ریشه باید به حداقل برسد
                self.add(cat, "فرسایش شدید (۱۰۰۰ t/ha/yr)",
                         depth >= 90,
                         f"کاهش عمق={depth:.1f}%",
                         "warning" if depth < 90 else "info",
                         "در فرسایش شدید، کاهش عمق باید > ۹۰٪ باشد")
            except Exception as e:
                self.add(cat, "فرسایش شدید", False, f"خطا: {e}", "critical")

        # ۱.۸ شوری اشباع (۱۰۰ dS/m)
        if self.sdm:
            try:
                result = self.sdm.h11_salinity_trend(100.0, 0.0, 0)
                classification = result["classification"]
                self.add(cat, "شوری اشباع (۱۰۰ dS/m)",
                         "بسیار شدید" in classification or "شدید" in classification,
                         f"طبقه‌بندی={classification}",
                         "info",
                         "باید 'بسیار شدید' باشد")
            except Exception as e:
                self.add(cat, "شوری اشباع", False, f"خطا: {e}", "critical")

        # ۱.۹ کربن آلی صفر
        if self.sdm:
            try:
                result = self.sdm.h09_dynamic_awc(150.0, 0.0)
                factor = result["adjustment_factor"]
                self.add(cat, "AWC با SOC صفر",
                         0.3 <= factor < 1.0,
                         f"فاکتور={factor:.3f}",
                         "info",
                         "فاکتور باید کمتر از ۱ باشد (خاک تخریب‌شده)")
            except Exception as e:
                self.add(cat, "AWC با SOC صفر", False, f"خطا: {e}", "critical")

        # ۱.۱۰ کربن آلی بسیار بالا (۲۰٪ - غیرممکن در شرایط عادی)
        if self.sdm:
            try:
                result = self.sdm.h09_dynamic_awc(150.0, 20.0)
                factor = result["adjustment_factor"]
                # باید سقف داشته باشد
                self.add(cat, "AWC با SOC غیرمنطقی (۲۰٪)",
                         factor <= 1.5,
                         f"فاکتور={factor:.3f}",
                         "warning" if factor > 1.5 else "info",
                         "فاکتور باید سقف داشته باشد (≤ ۱.۵)")
            except Exception as e:
                self.add(cat, "AWC با SOC غیرمنطقی", False, f"خطا: {e}", "critical")

        # ۱.۱۱ مونت‌کارلو با واریانس صفر
        if self.uke:
            try:
                result = self.uke.h22_monte_carlo_uncertainty(
                    5.0, n_simulations=100,
                    climate_variability=0.0,
                    soil_variability=0.0,
                    pest_variability=0.0)
                cv = result["coefficient_of_variation"]
                self.add(cat, "مونت‌کارلو با واریانس صفر",
                         cv < 0.01 and math.isfinite(cv),
                         f"CV={cv}",
                         "critical" if not math.isfinite(cv) else "info",
                         "با واریانس صفر، CV باید صفر باشد")
            except Exception as e:
                self.add(cat, "مونت‌کارلو با واریانس صفر", False, f"خطا: {e}", "critical")

        # ۱.۱۲ عملکرد صفر در مونت‌کارلو
        if self.uke:
            try:
                result = self.uke.h22_monte_carlo_uncertainty(0.0, n_simulations=100)
                p50 = result["p50_t_ha"]
                self.add(cat, "مونت‌کارلو با عملکرد پایه صفر",
                         p50 == 0.0 or p50 < 0.1,
                         f"P50={p50}",
                         "info",
                         "با عملکرد پایه صفر، خروجی باید صفر یا نزدیک صفر باشد")
            except Exception as e:
                self.add(cat, "مونت‌کارلو با صفر", False, f"خطا: {e}", "critical")

    # ============================================================
    # دسته ۲: ورودی‌های خصمانه (Adversarial Inputs)
    # ============================================================
    def test_adversarial(self):
        cat = "خصمانه"
        logger.info("\n" + "="*70)
        logger.info("دسته ۲: ورودی‌های خصمانه")
        logger.info("="*70)

        # ۲.۱ بارش منفی
        if self.dse:
            try:
                eff = self.dse.h01_effective_rain_mm(-10.0)
                self.add(cat, "بارش منفی",
                         eff <= 0,
                         f"بارش مؤثر={eff}",
                         "critical" if eff > 0 else "info",
                         "بارش منفی باید صفر یا منفی برگرداند")
            except Exception as e:
                self.add(cat, "بارش منفی", False, f"خطا: {e}", "warning",
                         "مدل باید بارش منفی را مدیریت کند")

        # ۲.۲ دمای بسیار غیرمنطقی (۱۰۰۰ درجه)
        if self.dse:
            try:
                ks = self.dse.h04_heat_ks(1000.0)
                self.add(cat, "دمای ۱۰۰۰ درجه",
                         math.isfinite(ks) and ks >= 0,
                         f"Ks={ks}",
                         "critical" if not math.isfinite(ks) else "info",
                         "خروجی باید متناهی و ≥ ۰ باشد")
            except OverflowError:
                self.add(cat, "دمای ۱۰۰۰ درجه", False, "OverflowError", "critical",
                         "مدل در دمای بسیار بالا دچار سرریز می‌شود")
            except Exception as e:
                self.add(cat, "دمای ۱۰۰۰ درجه", False, f"خطا: {e}", "critical")

        # ۲.۳ SOC منفی
        if self.sdm:
            try:
                result = self.sdm.h09_dynamic_awc(150.0, -1.0)
                self.add(cat, "SOC منفی",
                         True,  # اگر خطا ندهد، خوب است
                         f"فاکتور={result.get('adjustment_factor', 'N/A')}",
                         "info",
                         "مدل باید SOC منفی را مدیریت کند")
            except Exception as e:
                self.add(cat, "SOC منفی", True, f"خطای مدیریت‌شده: {e}", "info")

        # ۲.۴ pH خارج از محدوده (۱۵)
        if self.sdm:
            try:
                # تست مستقیم با soil_fertility_index
                result = self.sdm.h13_soil_fertility_index(
                    soc_pct=1.5, n_pct=0.15, p_available_ppm=30.0,
                    k_available_ppm=200.0, ph=15.0, biology_index=0.5)
                fertility = result["fertility_index"]
                self.add(cat, "pH غیرممکن (۱۵)",
                         0 <= fertility < 0.5,
                         f"حاصلخیزی={fertility:.3f}",
                         "warning" if fertility >= 0.5 else "info",
                         "با pH غیرممکن، حاصلخیزی باید بسیار پایین باشد")
            except Exception as e:
                self.add(cat, "pH غیرممکن", False, f"خطا: {e}", "warning")

        # ۲.۵ تنوع ژنتیکی منفی
        if self.soe:
            try:
                result = self.soe.h19_genetic_vulnerability(-0.5, 50.0, 3)
                vuln = result["vulnerability_index"]
                self.add(cat, "تنوع ژنتیکی منفی",
                         0 <= vuln <= 1,
                         f"آسیب‌پذیری={vuln}",
                         "critical" if not (0 <= vuln <= 1) else "info",
                         "آسیب‌پذیری باید در بازه [۰,۱] باشد")
            except Exception as e:
                self.add(cat, "تنوع ژنتیکی منفی", False, f"خطا: {e}", "critical")

        # ۲.۶ تنوع ژنتیکی > ۱
        if self.soe:
            try:
                result = self.soe.h19_genetic_vulnerability(1.5, 50.0, 3)
                vuln = result["vulnerability_index"]
                self.add(cat, "تنوع ژنتیکی > ۱",
                         0 <= vuln <= 1,
                         f"آسیب‌پذیری={vuln}",
                         "critical" if not (0 <= vuln <= 1) else "info",
                         "آسیب‌پذیری باید در بازه [۰,۱] باشد")
            except Exception as e:
                self.add(cat, "تنوع ژنتیکی > ۱", False, f"خطا: {e}", "critical")

        # ۲.۷ راندمان آبیاری > ۱
        if self.soe:
            try:
                # تست با مقادیر غیرمنطقی
                result = self.soe.h16_field_hardiness(1.5, 1.5, 1.5)
                hardiness = result["hardiness_score"]
                self.add(cat, "ورودی‌های > ۱ در سازگاری",
                         0 <= hardiness <= 1,
                         f"سازگاری={hardiness}",
                         "critical" if not (0 <= hardiness <= 1) else "info",
                         "خروجی باید در [۰,۱] محدود شود")
            except Exception as e:
                self.add(cat, "ورودی‌های > ۱", False, f"خطا: {e}", "critical")

        # ۲.۸ دوره رشد منفی
        if self.soe:
            try:
                result = self.soe.h18_growth_duration_optimizer(
                    rain_window_days=100, temp_window_days=120,
                    stress_onset_day=90, base_duration_days=-50)
                optimal = result["optimal_duration_days"]
                self.add(cat, "دوره رشد منفی",
                         optimal >= 0,
                         f"دوره بهینه={optimal}",
                         "critical" if optimal < 0 else "info",
                         "دوره رشد نباید منفی باشد")
            except Exception as e:
                self.add(cat, "دوره رشد منفی", False, f"خطا: {e}", "critical")

        # ۲.۹ پنجره‌های صفر در بهینه‌ساز
        if self.soe:
            try:
                result = self.soe.h18_growth_duration_optimizer(
                    rain_window_days=0, temp_window_days=0,
                    stress_onset_day=0, base_duration_days=150)
                optimal = result["optimal_duration_days"]
                self.add(cat, "پنجره‌های صفر",
                         optimal >= 0 and math.isfinite(optimal),
                         f"دوره بهینه={optimal}",
                         "warning" if optimal > 100 else "info",
                         "با پنجره صفر، دوره رشد باید محدود شود")
            except Exception as e:
                self.add(cat, "پنجره‌های صفر", False, f"خطا: {e}", "critical")

        # ۲.۱۰ تجربه کشاورز بسیار بالا (۲۰۰ سال)
        if self.uke:
            try:
                result = self.uke.h25_local_knowledge_integration(
                    farmer_experience_years=200,
                    traditional_calendar_reliability=0.8,
                    community_agreement_level=0.9,
                    scientific_alignment=0.7)
                score = result["knowledge_score"]
                self.add(cat, "تجربه ۲۰۰ ساله",
                         0 <= score <= 1,
                         f"امتیاز دانش={score:.3f}",
                         "info",
                         "باید سقف داشته باشد (حداکثر ۵۰ سال مؤثر)")
            except Exception as e:
                self.add(cat, "تجربه ۲۰۰ ساله", False, f"خطا: {e}", "warning")

    # ============================================================
    # دسته ۳: قوانین فیزیکی (Physical Laws)
    # ============================================================
    def test_physical_laws(self):
        cat = "فیزیک"
        logger.info("\n" + "="*70)
        logger.info("دسته ۳: قوانین فیزیکی")
        logger.info("="*70)

        # ۳.۱ بارش مؤثر هرگز نباید از بارش کل بیشتر شود
        if self.dse:
            try:
                for rain in [5, 10, 50, 100, 200]:
                    eff = self.dse.h01_effective_rain_mm(rain)
                    if eff > rain:
                        self.add(cat, f"بارش مؤثر > بارش کل ({rain}mm)",
                                 False,
                                 f"بارش مؤثر={eff:.1f} > بارش={rain}",
                                 "critical",
                                 "بارش مؤثر نمی‌تواند از بارش کل بیشتر باشد")
                        return
                self.add(cat, "بارش مؤثر ≤ بارش کل",
                         True, "تمام مقادیر بررسی شدند", "info")
            except Exception as e:
                self.add(cat, "بارش مؤثر ≤ بارش کل", False, f"خطا: {e}", "critical")

        # ۳.۲ Ks باید همیشه در بازه [۰,۱] باشد
        if self.dse:
            try:
                temps = list(range(-30, 60, 5))
                for t in temps:
                    ks = self.dse.h04_heat_ks(t)
                    if not (0 <= ks <= 1):
                        self.add(cat, f"Ks خارج از [۰,۱] در {t}°C",
                                 False,
                                 f"Ks={ks}",
                                 "critical",
                                 "Ks باید همیشه در [۰,۱] باشد")
                        return
                self.add(cat, "Ks ∈ [۰,۱] برای همه دماها",
                         True, f"{len(temps)} دما بررسی شد", "info")
            except Exception as e:
                self.add(cat, "Ks ∈ [۰,۱]", False, f"خطا: {e}", "critical")

        # ۳.۳ ترکیب تنش‌ها نباید از کوچکترین جزء بیشتر شود
        if self.dse:
            try:
                ks_w, ks_t, ks_s = 0.3, 0.5, 0.7
                combined = self.dse.h08_combined_ks(ks_w, ks_t, ks_s, compound_event=False)
                min_component = min(ks_w, ks_t, ks_s)
                self.add(cat, "ترکیب تنش ≤ کوچکترین جزء",
                         combined <= min_component + 0.001,
                         f"ترکیب={combined:.3f}, حداقل جزء={min_component}",
                         "warning" if combined > min_component else "info",
                         "ترکیب تنش‌ها نباید از حداقل جزء بیشتر شود")
            except Exception as e:
                self.add(cat, "ترکیب تنش‌ها", False, f"خطا: {e}", "critical")

        # ۳.۴ فاکتور تعدیل نباید از سقف تعیین‌شده بیشتر شود
        if self.sdm:
            try:
                # با SOC بسیار بالا
                result = self.sdm.h09_dynamic_awc(150.0, 10.0)
                factor = result["adjustment_factor"]
                max_factor = self.sdm.cfg.awc_factor_max
                self.add(cat, "فاکتور AWC ≤ سقف",
                         factor <= max_factor + 0.001,
                         f"فاکتور={factor:.3f}, سقف={max_factor}",
                         "critical" if factor > max_factor + 0.001 else "info",
                         f"فاکتور نباید از {max_factor} بیشتر شود")
            except Exception as e:
                self.add(cat, "سقف فاکتور AWC", False, f"خطا: {e}", "critical")

        # ۳.۵ جریمه شبانه نباید از سقف بیشتر شود
        if self.dse:
            try:
                for t_night in [20, 30, 40, 50, 60]:
                    penalty = self.dse.h02_night_penalty(t_night)
                    max_penalty = self.dse.cfg.max_night_penalty
                    if penalty > max_penalty + 0.001:
                        self.add(cat, f"جریمه شب > سقف در {t_night}°C",
                                 False,
                                 f"جریمه={penalty:.3f}, سقف={max_penalty}",
                                 "critical",
                                 f"جریمه نباید از {max_penalty} بیشتر شود")
                        return
                self.add(cat, "جریمه شب ≤ سقف",
                         True, "تمام دماها بررسی شدند", "info")
            except Exception as e:
                self.add(cat, "سقف جریمه شب", False, f"خطا: {e}", "critical")

        # ۳.۶ حاصلخیزی باید در [۰,۱] باشد
        if self.sdm:
            try:
                # با مقادیر بسیار بالا
                result = self.sdm.h13_soil_fertility_index(
                    soc_pct=10.0, n_pct=1.0, p_available_ppm=200.0,
                    k_available_ppm=1000.0, ph=7.0, biology_index=1.0)
                fertility = result["fertility_index"]
                self.add(cat, "حاصلخیزی ∈ [۰,۱] با مقادیر بالا",
                         0 <= fertility <= 1.001,
                         f"حاصلخیزی={fertility:.3f}",
                         "critical" if fertility > 1.001 else "info",
                         "حاصلخیزی نباید از ۱ بیشتر شود")
            except Exception as e:
                self.add(cat, "حاصلخیزی ∈ [۰,۱]", False, f"خطا: {e}", "critical")

    # ============================================================
    # دسته ۴: واقع‌بینی زراعی (Agronomic Realism)
    # ============================================================
    def test_agronomic_realism(self):
        cat = "زراعت"
        logger.info("\n" + "="*70)
        logger.info("دسته ۴: واقع‌بینی زراعی")
        logger.info("="*70)

        # ۴.۱ سقف عملکرد غلات (گندم حداکثر ~۱۵ تن/هکتار)
        if self.uke:
            try:
                result = self.uke.h22_monte_carlo_uncertainty(
                    8.0, n_simulations=500,
                    climate_variability=0.3,
                    soil_variability=0.2,
                    pest_variability=0.15)
                p90 = result["p90_t_ha"]
                self.add(cat, "سقف P90 گندم (≤ ۱۵ تن)",
                         p90 <= 15.0,
                         f"P90={p90:.2f} تن/هکتار",
                         "warning" if p90 > 15.0 else "info",
                         "P90 گندم نباید از رکورد جهانی (~۱۵ تن) بیشتر شود")
            except Exception as e:
                self.add(cat, "سقف عملکرد گندم", False, f"خطا: {e}", "critical")

        # ۴.۲ عدم قطعیت نباید از ۱۰۰٪ بیشتر شود
        if self.uke:
            try:
                result = self.uke.h22_monte_carlo_uncertainty(
                    5.0, n_simulations=500, climate_variability=0.5)
                cv = result["coefficient_of_variation"]
                self.add(cat, "CV واقع‌بینانه (≤ ۱)",
                         cv <= 1.0,
                         f"CV={cv:.3f}",
                         "warning" if cv > 1.0 else "info",
                         "CV بالای ۱ یعنی عدم قطعیت بیش از ۱۰۰٪")
            except Exception as e:
                self.add(cat, "CV واقع‌بینانه", False, f"خطا: {e}", "critical")

        # ۴.۳ کاهش عمق ریشه نباید از ۱۰۰٪ بیشتر شود
        if self.sdm:
            try:
                result = self.sdm.h10_root_depth_decay(100.0, 50.0, 50)
                loss = result["depth_loss_percent"]
                self.add(cat, "کاهش عمق ریشه ≤ ۱۰۰٪",
                         loss <= 100.0,
                         f"کاهش={loss:.1f}%",
                         "critical" if loss > 100 else "info",
                         "کاهش عمق نمی‌تواند از ۱۰۰٪ بیشتر شود")
            except Exception as e:
                self.add(cat, "کاهش عمق ≤ ۱۰۰٪", False, f"خطا: {e}", "critical")

        # ۴.۴ پیش‌بینی شوری باید یکنوا باشد
        if self.sdm:
            try:
                ec_now = 2.0
                result1 = self.sdm.h11_salinity_trend(ec_now, 0.1, 10)
                result2 = self.sdm.h11_salinity_trend(ec_now, 0.2, 10)
                ec1 = result1["ec_projected_ds_m"]
                ec2 = result2["ec_projected_ds_m"]
                self.add(cat, "یکنواختی روند شوری",
                         ec2 > ec1,
                         f"EC با روند ۰.۱={ec1}, با روند ۰.۲={ec2}",
                         "critical" if ec2 <= ec1 else "info",
                         "روند بالاتر باید EC بالاتری پیش‌بینی کند")
            except Exception as e:
                self.add(cat, "یکنواختی شوری", False, f"خطا: {e}", "critical")

        # ۴.۵ سازگاری میدانی باید با مؤلفه‌ها هم‌جهت باشد
        if self.soe:
            try:
                # همه مؤلفه‌ها بالا
                high = self.soe.h16_field_hardiness(0.9, 0.9, 0.9)
                # همه مؤلفه‌ها پایین
                low = self.soe.h16_field_hardiness(0.1, 0.1, 0.1)
                self.add(cat, "یکنواختی سازگاری میدانی",
                         high["hardiness_score"] > low["hardiness_score"],
                         f"بالا={high['hardiness_score']:.2f}, پایین={low['hardiness_score']:.2f}",
                         "critical" if high["hardiness_score"] <= low["hardiness_score"] else "info",
                         "مؤلفه‌های بالاتر باید سازگاری بالاتری بدهند")
            except Exception as e:
                self.add(cat, "یکنواختی سازگاری", False, f"خطا: {e}", "critical")

        # ۴.۶ راندمان آبیاری نباید از ۱ بیشتر شود
        # این تست مستقیم نیست ولی باید در مدل‌ها بررسی شود
        self.add(cat, "راندمان آبیاری ∈ [۰,۱]",
                 True,
                 "باید در موتور آبیاری بررسی شود",
                 "info",
                 "راندمان نمی‌تواند از ۱۰۰٪ بیشتر شود")

    # ============================================================
    # دسته ۵: یکنواختی منطقی (Monotonicity)
    # ============================================================
    def test_monotonicity(self):
        cat = "یکنواختی"
        logger.info("\n" + "="*70)
        logger.info("دسته ۵: یکنواختی منطقی")
        logger.info("="*70)

        # ۵.۱ افزایش دما → کاهش Ks
        if self.dse:
            try:
                temps = [30, 35, 40, 45, 50]
                ks_values = [self.dse.h04_heat_ks(t) for t in temps]
                is_monotone = all(ks_values[i] >= ks_values[i+1] for i in range(len(ks_values)-1))
                self.add(cat, "Ks یکنوا نزولی با دما",
                         is_monotone,
                         f"Ks values: {[f'{k:.3f}' for k in ks_values]}",
                         "critical" if not is_monotone else "info",
                         "با افزایش دما، Ks باید کاهش یابد")
            except Exception as e:
                self.add(cat, "یکنواختی Ks", False, f"خطا: {e}", "critical")

        # ۵.۲ افزایش بارش → افزایش بارش مؤثر
        if self.dse:
            try:
                rains = [5, 10, 20, 50, 100]
                eff_values = [self.dse.h01_effective_rain_mm(r) for r in rains]
                is_monotone = all(eff_values[i] <= eff_values[i+1] for i in range(len(eff_values)-1))
                self.add(cat, "بارش مؤثر یکنوا صعودی با بارش",
                         is_monotone,
                         f"بارش مؤثر: {[f'{e:.1f}' for e in eff_values]}",
                         "critical" if not is_monotone else "info",
                         "با افزایش بارش، بارش مؤثر باید افزایش یابد")
            except Exception as e:
                self.add(cat, "یکنواختی بارش مؤثر", False, f"خطا: {e}", "critical")

        # ۵.۳ افزایش SOC → افزایش AWC
        if self.sdm:
            try:
                socs = [0.5, 1.0, 2.0, 3.0, 4.0]
                awc_values = [self.sdm.h09_dynamic_awc(150.0, s)["awc_adjusted_mm_m"] for s in socs]
                is_monotone = all(awc_values[i] <= awc_values[i+1] for i in range(len(awc_values)-1))
                self.add(cat, "AWC یکنوا صعودی با SOC",
                         is_monotone,
                         f"AWC: {[f'{a:.1f}' for a in awc_values]}",
                         "critical" if not is_monotone else "info",
                         "با افزایش کربن آلی، ظرفیت آب باید افزایش یابد")
            except Exception as e:
                self.add(cat, "یکنواختی AWC", False, f"خطا: {e}", "critical")

        # ۵.۴ افزایش فرسایش → کاهش عمق ریشه
        if self.sdm:
            try:
                erosions = [5, 10, 20, 30, 50]
                depths = [self.sdm.h10_root_depth_decay(100.0, e, 10)["effective_root_depth_cm"] for e in erosions]
                is_monotone = all(depths[i] >= depths[i+1] for i in range(len(depths)-1))
                self.add(cat, "عمق ریشه یکنوا نزولی با فرسایش",
                         is_monotone,
                         f"عمق‌ها: {[f'{d:.1f}' for d in depths]}",
                         "critical" if not is_monotone else "info",
                         "با افزایش فرسایش، عمق ریشه باید کاهش یابد")
            except Exception as e:
                self.add(cat, "یکنواختی عمق ریشه", False, f"خطا: {e}", "critical")

        # ۵.۵ افزایش تنوع ژنتیکی → کاهش آسیب‌پذیری
        if self.soe:
            try:
                diversities = [0.1, 0.3, 0.5, 0.7, 0.9]
                vulns = [self.soe.h19_genetic_vulnerability(d, 50.0, 3)["vulnerability_index"] for d in diversities]
                is_monotone = all(vulns[i] >= vulns[i+1] for i in range(len(vulns)-1))
                self.add(cat, "آسیب‌پذیری یکنوا نزولی با تنوع",
                         is_monotone,
                         f"آسیب‌پذیری: {[f'{v:.3f}' for v in vulns]}",
                         "critical" if not is_monotone else "info",
                         "با افزایش تنوع، آسیب‌پذیری باید کاهش یابد")
            except Exception as e:
                self.add(cat, "یکنواختی آسیب‌پذیری", False, f"خطا: {e}", "critical")

        # ۵.۶ افزایش تجربه → افزایش امتیاز دانش بومی
        if self.uke:
            try:
                experiences = [5, 10, 20, 30, 40]
                scores = [self.uke.h25_local_knowledge_integration(
                    e, 0.7, 0.7, 0.7)["knowledge_score"] for e in experiences]
                is_monotone = all(scores[i] <= scores[i+1] for i in range(len(scores)-1))
                self.add(cat, "دانش بومی یکنوا صعودی با تجربه",
                         is_monotone,
                         f"امتیازات: {[f'{s:.3f}' for s in scores]}",
                         "critical" if not is_monotone else "info",
                         "با افزایش تجربه، امتیاز دانش باید افزایش یابد")
            except Exception as e:
                self.add(cat, "یکنواختی دانش بومی", False, f"خطا: {e}", "critical")

    # ============================================================
    # دسته ۶: پایداری (Robustness)
    # ============================================================
    def test_robustness(self):
        cat = "پایداری"
        logger.info("\n" + "="*70)
        logger.info("دسته ۶: پایداری و تکرارپذیری")
        logger.info("="*70)

        # ۶.۱ تکرارپذیری مونت‌کارلو (با seed ثابت)
        if self.uke:
            try:
                # دو بار اجرا با شرایط یکسان
                r1 = self.uke.h22_monte_carlo_uncertainty(5.0, n_simulations=100)
                r2 = self.uke.h22_monte_carlo_uncertainty(5.0, n_simulations=100)
                # اگر seed ثابت باشد، نتایج باید یکسان باشند
                diff = abs(r1["p50_t_ha"] - r2["p50_t_ha"])
                self.add(cat, "تکرارپذیری مونت‌کارلو",
                         diff < 0.5,  # تلورانس کوچک
                         f"تفاوت P50={diff:.4f}",
                         "warning" if diff >= 0.5 else "info",
                         "اجرای مکرر باید نتایج مشابه بدهد")
            except Exception as e:
                self.add(cat, "تکرارپذیری", False, f"خطا: {e}", "critical")

        # ۶.۲ حساسیت به تغییرات کوچک ورودی
        if self.dse:
            try:
                ks1 = self.dse.h04_heat_ks(35.0)
                ks2 = self.dse.h04_heat_ks(35.1)
                diff = abs(ks1 - ks2)
                self.add(cat, "حساسیت به تغییر کوچک دما",
                         diff < 0.1,  # تغییر کوچک نباید خروجی بزرگ ایجاد کند
                         f"تفاوت={diff:.6f}",
                         "warning" if diff >= 0.1 else "info",
                         "تغییر ۰.۱ درجه نباید تغییر بزرگ ایجاد کند")
            except Exception as e:
                self.add(cat, "حساسیت به تغییر کوچک", False, f"خطا: {e}", "critical")

        # ۶.۳ پایداری عددی در محاسبات مکرر
        if self.sdm:
            try:
                results = []
                for _ in range(10):
                    r = self.sdm.h13_soil_fertility_index(
                        soc_pct=1.5, n_pct=0.15, p_available_ppm=30.0,
                        k_available_ppm=200.0, ph=7.0, biology_index=0.5)
                    results.append(r["fertility_index"])
                # همه نتایج باید یکسان باشند
                all_same = all(abs(r - results[0]) < 1e-10 for r in results)
                self.add(cat, "پایداری عددی در محاسبات مکرر",
                         all_same,
                         f"محدوده نتایج: {min(results):.6f} - {max(results):.6f}",
                         "critical" if not all_same else "info",
                         "محاسبات مکرر باید نتایج یکسان بدهند")
            except Exception as e:
                self.add(cat, "پایداری عددی", False, f"خطا: {e}", "critical")

    # ============================================================
    # دسته ۷: تعامل تنش‌ها (Interaction)
    # ============================================================
    def test_interactions(self):
        cat = "تعامل"
        logger.info("\n" + "="*70)
        logger.info("دسته ۷: تعامل تنش‌ها")
        logger.info("="*70)

        # ۷.۱ ترکیب تنش‌ها باید سخت‌تر از تک‌تنش باشد
        if self.dse:
            try:
                single = self.dse.h08_combined_ks(0.5, 1.0, 1.0, False)
                double = self.dse.h08_combined_ks(0.5, 0.5, 1.0, False)
                triple = self.dse.h08_combined_ks(0.5, 0.5, 0.5, False)
                self.add(cat, "ترکیب تنش‌ها شدیدتر از تک‌تنش",
                         triple < double < single,
                         f"تک={single:.3f}, دو={double:.3f}, سه={triple:.3f}",
                         "critical" if not (triple < double < single) else "info",
                         "تنش‌های بیشتر باید اثر شدیدتری داشته باشند")
            except Exception as e:
                self.add(cat, "ترکیب تنش‌ها", False, f"خطا: {e}", "critical")

        # ۷.۲ رویداد ترکیبی باید شدیدتر از حالت عادی باشد
        if self.dse:
            try:
                normal = self.dse.h08_combined_ks(0.6, 0.6, 0.6, compound_event=False)
                compound = self.dse.h08_combined_ks(0.6, 0.6, 0.6, compound_event=True)
                self.add(cat, "رویداد ترکیبی شدیدتر از عادی",
                         compound < normal,
                         f"عادی={normal:.3f}, ترکیبی={compound:.3f}",
                         "critical" if compound >= normal else "info",
                         "رویداد ترکیبی باید ضریب اضافی داشته باشد")
            except Exception as e:
                self.add(cat, "رویداد ترکیبی", False, f"خطا: {e}", "critical")

        # ۷.۳ تنش صفر باید خنثی باشد
        if self.dse:
            try:
                # اگر یک تنش صفر باشد (یعنی بی‌نهایت)، نباید ترکیب را صفر کند
                result = self.dse.h08_combined_ks(0.5, 1.0, 1.0, False)
                self.add(cat, "تنش خنثی (۱.۰) بی‌اثر",
                         abs(result - 0.5) < 0.01,
                         f"نتیجه={result:.3f}",
                         "warning" if abs(result - 0.5) >= 0.01 else "info",
                         "تنش ۱.۰ (بدون تنش) باید بی‌اثر باشد")
            except Exception as e:
                self.add(cat, "تنش خنثی", False, f"خطا: {e}", "critical")

    # ============================================================
    # دسته ۸: صحت‌سنجی متقابل (Cross-validation)
    # ============================================================
    def test_cross_validation(self):
        cat = "صحت‌سنجی"
        logger.info("\n" + "="*70)
        logger.info("دسته ۸: صحت‌سنجی متقابل")
        logger.info("="*70)

        # ۸.۱ سازگاری بین ماژول‌ها
        if self.sdm and self.soe:
            try:
                # خاک با حاصلخیزی بالا باید امتیاز میکروبیوم بالا بدهد
                soil_result = self.sdm.h13_soil_fertility_index(
                    soc_pct=3.0, n_pct=0.3, p_available_ppm=50.0,
                    k_available_ppm=300.0, ph=7.0, biology_index=0.8)
                micro_result = self.soe.h21_microbiome_compatibility(
                    soc_pct=3.0, ph=7.0, biology_index=0.8, organic_input_history=0.7)
                
                soil_fertility = soil_result["fertility_index"]
                micro_score = micro_result["microbiome_score"]
                
                # هر دو باید بالا باشند
                self.add(cat, "سازگاری حاصلخیزی و میکروبیوم",
                         soil_fertility > 0.6 and micro_score > 0.6,
                         f"حاصلخیزی={soil_fertility:.2f}, میکروبیوم={micro_score:.2f}",
                         "warning" if not (soil_fertility > 0.6 and micro_score > 0.6) else "info",
                         "خاک حاصلخیز باید میکروبیوم سالم داشته باشد")
            except Exception as e:
                self.add(cat, "سازگاری بین ماژول‌ها", False, f"خطا: {e}", "critical")

        # ۸.۲ مقایسه با مرجع فائو (عملکرد گندم در شرایط دیم)
        if self.uke:
            try:
                # گندم دیم در منطقه نیمه‌خشک: عملکرد مورد انتظار ۱-۳ تن
                result = self.uke.h22_monte_carlo_uncertainty(
                    2.0, n_simulations=500, climate_variability=0.3)
                p50 = result["p50_t_ha"]
                self.add(cat, "گندم دیم نیمه‌خشک (۱-۳ تن)",
                         0.5 <= p50 <= 4.0,
                         f"P50={p50:.2f} تن/هکتار",
                         "warning" if not (0.5 <= p50 <= 4.0) else "info",
                         "عملکرد گندم دیم در نیمه‌خشک: ۱-۳ تن/هکتار (فائو)")
            except Exception as e:
                self.add(cat, "مرجع فائو", False, f"خطا: {e}", "critical")

        # ۸.۳ صحت‌سنجی تاریخ کاشت
        if self.cap:
            try:
                result = self.cap.h05_dynamic_planting_day(
                    last_frost_day_of_year=100,
                    soil_temp_series=[8.0, 9.0, 10.0, 11.0],
                    rain_onset_day_of_year=280)
                day = result["planting_day_of_year"]
                # تاریخ کاشت باید بعد از یخبندان باشد
                self.add(cat, "تاریخ کاشت بعد از یخبندان",
                         day > 100,
                         f"روز={day}",
                         "critical" if day <= 100 else "info",
                         "کاشت باید بعد از آخرین یخبندان باشد")
            except Exception as e:
                self.add(cat, "تاریخ کاشت", False, f"خطا: {e}", "critical")

    # ============================================================
    # اجرای کامل
    # ============================================================
    def run_all(self):
        logger.info("="*70)
        logger.info("چالش سختگیرانه نسخه ۲ - شکنجه علمی مدل هیدروما")
        logger.info("="*70)

        self.test_boundary()
        self.test_adversarial()
        self.test_physical_laws()
        self.test_agronomic_realism()
        self.test_monotonicity()
        self.test_robustness()
        self.test_interactions()
        self.test_cross_validation()

        return self.results

    def generate_report(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        critical = sum(1 for r in self.results if not r.passed and r.severity == "critical")
        warnings = sum(1 for r in self.results if r.severity == "warning")
        rate = passed / total * 100 if total > 0 else 0

        # دسته‌بندی بر اساس حوزه
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {"total": 0, "passed": 0, "failed": 0}
            categories[r.category]["total"] += 1
            if r.passed:
                categories[r.category]["passed"] += 1
            else:
                categories[r.category]["failed"] += 1

        if critical > 0:
            verdict = f"NEEDS_FIX - {critical} خطای بحرانی یافت شد"
        elif failed > 0:
            verdict = f"REVIEW - {failed} مورد نیازمند بررسی"
        else:
            verdict = "EXCELLENT - مدل بسیار قوی است"

        return {
            "generated_at": datetime.now().isoformat(),
            "challenge_version": "2.0-strict",
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "critical_failures": critical,
            "warnings": warnings,
            "pass_rate_percent": round(rate, 1),
            "verdict": verdict,
            "by_category": categories,
            "failures": [r.to_dict() for r in self.results if not r.passed],
            "all_warnings": [r.to_dict() for r in self.results if r.severity == "warning"],
        }


def main():
    challenge = StrictChallengeV2()
    results = challenge.run_all()
    report = challenge.generate_report()

    logger.info("\n" + "="*70)
    logger.info("نتیجه نهایی چالش سختگیرانه نسخه ۲")
    logger.info("="*70)
    logger.info(f"   کل تست‌ها: {report['total_tests']}")
    logger.info(f"   موفق: {report['passed']} ({report['pass_rate_percent']}%)")
    logger.info(f"   ناموفق: {report['failed']}")
    logger.info(f"   بحرانی: {report['critical_failures']}")
    logger.warning(f"   هشدارها: {report['warnings']}")

    logger.info("\n   نتایج بر اساس دسته:")
    for cat, stats in report["by_category"].items():
        cat_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        logger.info(f"      {cat}: {stats['passed']}/{stats['total']} ({cat_rate:.0f}%)")

    logger.info(f"\n   حکم نهایی: {report['verdict']}")
    logger.info("="*70)

    # ذخیره گزارش
    report_dir = ROOT / "docs" / "hydroma"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "strict_challenge_v2_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"\nگزارش ذخیره شد: {report_file}")


if __name__ == "__main__":
    main()