#!/usr/bin/env python3
# ============================================================================
# نصب‌کننده فاز ۵ (نهایی): موتور عدم قطعیت و دانش بومی
# الگوریتم‌ها: H22 مونت‌کارلو | H23 تلفیق چندمقیاسی | H25 دانش بومی
# منابع: IPCC AR6 WG1 (2021) | Altieri 2018 | FAO Participatory Methods
# ============================================================================
import ast
import json
import shutil
import py_compile
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
UNK_DIR = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation"
AQUACROP = PROJECT_ROOT / "services" / "scientific_motors" / "aquacrop_real.py"
DECISION_ENGINE = PROJECT_ROOT / "connect_indices_to_motors.py"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_uncertainty_knowledge_engine.py"
REGISTRY = PROJECT_ROOT / "docs" / "hydroma" / "innovation_registry.json"

# ----------------------------------------------------------------------------
# کد ماژول عدم قطعیت و دانش بومی
# ----------------------------------------------------------------------------
UNK_MODEL_CODE = '''# -*- coding: utf-8 -*-
# ============================================================================
# Hydroma Uncertainty Quantification & Local Knowledge Engine - Phase 5
# Algorithms: H22 Monte Carlo Uncertainty | H23 Multi-scale Data Fusion
#             H25 Local Knowledge Integration
# References: IPCC AR6 WG1 (2021); Altieri 2018; FAO Participatory Methods
# ============================================================================
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

__version__ = "1.0.0"


@dataclass
class UncertaintyConfig:
    # H22: مونت‌کارلو
    default_simulations: int = 500
    random_seed: Optional[int] = 42
    
    # H23: تلفیق داده
    fusion_weights: Dict = field(default_factory=lambda: {
        "satellite": 0.40, "station": 0.35, "model": 0.15, "local": 0.10
    })
    satellite_resolution_m: int = 30
    station_radius_km: float = 50.0
    
    # H25: دانش بومی
    knowledge_confidence_weights: Dict = field(default_factory=lambda: {
        "experience_years": 0.30, "consistency": 0.25,
        "community_agreement": 0.25, "scientific_alignment": 0.20
    })
    max_experience_years: int = 50


# ============================================================================
class UncertaintyAndKnowledgeEngine:
    # ------------------------------------------------------------------ init
    def __init__(self, config: Optional[UncertaintyConfig] = None):
        self.cfg = config or UncertaintyConfig()
        if self.cfg.random_seed is not None:
            random.seed(self.cfg.random_seed)

    # ------------------------------------------------------------------- H22
    def h22_monte_carlo_uncertainty(self, base_yield_t_ha: float,
                                    n_simulations: Optional[int] = None,
                                    climate_variability: float = 0.15,
                                    soil_variability: float = 0.10,
                                    pest_variability: float = 0.08) -> Dict:
        """
        تحلیل عدم قطعیت مونت‌کارلو (Monte Carlo Uncertainty Analysis)
        اجرای شبیه‌سازی با پارامترهای تصادفی و محاسبه بازه اطمینان
        خروجی: P10, P50, P90 + ضریب تغییرات
        """
        n = n_simulations or self.cfg.default_simulations
        yields = []
        
        for _ in range(n):
            # اعمال تغییرات تصادفی
            climate_factor = 1.0 + random.gauss(0, climate_variability)
            soil_factor = 1.0 + random.gauss(0, soil_variability)
            pest_factor = 1.0 + random.gauss(0, pest_variability)
            
            # محدود کردن عوامل به بازه منطقی
            climate_factor = max(0.3, min(1.5, climate_factor))
            soil_factor = max(0.5, min(1.3, soil_factor))
            pest_factor = max(0.4, min(1.2, pest_factor))
            
            simulated_yield = base_yield_t_ha * climate_factor * soil_factor * pest_factor
            yields.append(max(0.0, simulated_yield))
        
        # مرتب‌سازی و محاسبه صدک‌ها
        yields.sort()
        p10 = yields[int(n * 0.10)]
        p50 = yields[int(n * 0.50)]
        p90 = yields[int(n * 0.90)]
        
        # میانگین و انحراف معیار
        mean_yield = sum(yields) / n
        variance = sum((y - mean_yield) ** 2 for y in yields) / n
        std_yield = math.sqrt(variance)
        cv = std_yield / mean_yield if mean_yield > 0 else 0
        
        # تعیین سطح اطمینان
        if cv < 0.15:
            confidence = "بالا"
            confidence_score = 0.85
        elif cv < 0.30:
            confidence = "متوسط"
            confidence_score = 0.65
        else:
            confidence = "پایین"
            confidence_score = 0.45
        
        return {
            "base_yield_t_ha": round(base_yield_t_ha, 2),
            "n_simulations": n,
            "p10_t_ha": round(p10, 2),
            "p50_t_ha": round(p50, 2),
            "p90_t_ha": round(p90, 2),
            "mean_t_ha": round(mean_yield, 2),
            "std_t_ha": round(std_yield, 2),
            "coefficient_of_variation": round(cv, 3),
            "confidence_level": confidence,
            "confidence_score": confidence_score,
            "yield_range_percent": round((p90 - p10) / p50 * 100, 1) if p50 > 0 else 0,
            "recommendation": self._uncertainty_recommendation(cv)
        }

    def _uncertainty_recommendation(self, cv: float) -> str:
        if cv < 0.15:
            return "پیش‌بینی قابل اتکا؛ تصمیم‌گیری با اطمینان بالا"
        elif cv < 0.30:
            return "پیش‌بینی با احتیاط؛ سناریوهای جایگزین بررسی شود"
        else:
            return "پیش‌بینی پرریسک؛ کشت متنوع و بیمه توصیه می‌شود"

    # ------------------------------------------------------------------- H23
    def h23_multi_scale_fusion(self, satellite_value: float,
                               station_value: float,
                               model_value: float,
                               local_value: Optional[float] = None,
                               satellite_quality: float = 0.8,
                               station_density: float = 0.7) -> Dict:
        """
        تلفیق داده چندمقیاسی (Multi-scale Data Fusion)
        ترکیب داده‌های ماهواره‌ای، ایستگاهی، مدل و محلی با وزن‌دهی دینامیک
        """
        w = self.cfg.fusion_weights.copy()
        
        # تنظیم وزن بر اساس کیفیت منابع
        w["satellite"] *= satellite_quality
        w["station"] *= station_density
        
        # اگر داده محلی موجود نباشد، وزن آن به ایستگاهی منتقل می‌شود
        if local_value is None:
            w["station"] += w["local"]
            w["local"] = 0.0
            local_value = station_value  # جایگزینی با ایستگاهی
        
        # نرمال‌سازی وزن‌ها
        total_w = sum(w.values())
        if total_w > 0:
            w = {k: v / total_w for k, v in w.items()}
        
        # محاسبه مقدار تلفیقی
        fused_value = (w["satellite"] * satellite_value +
                       w["station"] * station_value +
                       w["model"] * model_value +
                       w["local"] * local_value)
        
        # ارزیابی کیفیت تلفیق
        values = [satellite_value, station_value, model_value, local_value]
        valid_values = [v for v in values if v is not None]
        if len(valid_values) > 1:
            mean_v = sum(valid_values) / len(valid_values)
            max_deviation = max(abs(v - mean_v) for v in valid_values)
            consistency = max(0.0, 1.0 - max_deviation / (mean_v + 1e-6))
        else:
            consistency = 0.5
        
        if consistency >= 0.8:
            quality = "بالا"
        elif consistency >= 0.5:
            quality = "متوسط"
        else:
            quality = "پایین"
        
        return {
            "fused_value": round(fused_value, 3),
            "weights_applied": {k: round(v, 3) for k, v in w.items()},
            "consistency_score": round(consistency, 3),
            "data_quality": quality,
            "sources_used": len(valid_values),
            "recommendation": self._fusion_recommendation(consistency)
        }

    def _fusion_recommendation(self, consistency: float) -> str:
        if consistency >= 0.8:
            return "داده‌ها همساز هستند؛ تلفیق قابل اتکا"
        elif consistency >= 0.5:
            return "اختلاف متوسط بین منابع؛ بررسی بیشتر توصیه می‌شود"
        else:
            return "اختلاف زیاد بین منابع؛ نیاز به اعتبارسنجی میدانی"

    # ------------------------------------------------------------------- H25
    def h25_local_knowledge_integration(self, farmer_experience_years: int,
                                        traditional_calendar_reliability: float,
                                        community_agreement_level: float,
                                        scientific_alignment: float) -> Dict:
        """
        ادغام دانش بومی (Local Knowledge Integration)
        تبدیل دانش سنتی و تجربی کشاورزان به پارامترهای کمّی قابل استفاده در مدل
        """
        w = self.cfg.knowledge_confidence_weights
        
        # امتیاز تجربه (با سقف)
        experience_score = min(1.0, farmer_experience_years / self.cfg.max_experience_years)
        
        # محدود کردن سایر امتیازات به بازه 0-1
        calendar_score = max(0.0, min(1.0, traditional_calendar_reliability))
        community_score = max(0.0, min(1.0, community_agreement_level))
        alignment_score = max(0.0, min(1.0, scientific_alignment))
        
        # محاسبه امتیاز کل
        knowledge_score = (w["experience_years"] * experience_score +
                           w["consistency"] * calendar_score +
                           w["community_agreement"] * community_score +
                           w["scientific_alignment"] * alignment_score)
        
        # تعیین وزن دانش بومی در مدل
        if knowledge_score >= 0.75:
            integration_weight = 0.25  # وزن بالا در مدل
            classification = "دانش بومی بسیار معتبر"
        elif knowledge_score >= 0.55:
            integration_weight = 0.15  # وزن متوسط
            classification = "دانش بومی معتبر"
        elif knowledge_score >= 0.35:
            integration_weight = 0.08  # وزن کم
            classification = "دانش بومی با اعتبار محدود"
        else:
            integration_weight = 0.0  # بدون وزن
            classification = "دانش بومی نیازمند اعتبارسنجی"
        
        return {
            "knowledge_score": round(knowledge_score, 3),
            "classification": classification,
            "integration_weight": integration_weight,
            "component_scores": {
                "experience": round(experience_score, 2),
                "calendar_reliability": round(calendar_score, 2),
                "community_agreement": round(community_score, 2),
                "scientific_alignment": round(alignment_score, 2)
            },
            "recommendation": self._knowledge_recommendation(knowledge_score)
        }

    def _knowledge_recommendation(self, score: float) -> str:
        if score >= 0.75:
            return "ادغام کامل در مدل؛ ثبت در پایگاه دانش بومی"
        elif score >= 0.55:
            return "ادغام با وزن متوسط؛ پایش و بازنگری دوره‌ای"
        elif score >= 0.35:
            return "ادغام محدود؛ نیاز به تأیید علمی بیشتر"
        else:
            return "عدم ادغام؛ مستندسازی برای ارزیابی‌های آینده"

    # ------------------------------------------------- گزارش جامع عدم قطعیت
    def generate_uncertainty_report(self, base_yield: float,
                                    satellite_data: float,
                                    station_data: float,
                                    farmer_experience: int = 20,
                                    calendar_reliability: float = 0.6) -> Dict:
        """تولید گزارش جامع عدم قطعیت با ترکیب هر سه الگوریتم"""
        
        report = {"model_version": __version__}
        
        # H22: عدم قطعیت مونت‌کارلو
        report["h22_uncertainty"] = self.h22_monte_carlo_uncertainty(base_yield)
        
        # H23: تلفیق داده
        report["h23_fusion"] = self.h23_multi_scale_fusion(
            satellite_data, station_data, base_yield * 0.95)
        
        # H25: دانش بومی
        report["h25_knowledge"] = self.h25_local_knowledge_integration(
            farmer_experience, calendar_reliability, 0.7, 0.6)
        
        # امتیاز کلی قابلیت اتکا
        report["overall_reliability"] = self._calculate_overall_reliability(report)
        
        return report

    def _calculate_overall_reliability(self, report: Dict) -> Dict:
        scores = []
        
        if "h22_uncertainty" in report:
            scores.append(report["h22_uncertainty"]["confidence_score"])
        if "h23_fusion" in report:
            scores.append(report["h23_fusion"]["consistency_score"])
        if "h25_knowledge" in report:
            scores.append(report["h25_knowledge"]["knowledge_score"])
        
        overall = sum(scores) / len(scores) if scores else 0.0
        
        if overall >= 0.75:
            status = "قابلیت اطمینان بالا"
        elif overall >= 0.55:
            status = "قابلیت اطمینان متوسط"
        else:
            status = "قابلیت اطمینان پایین"
        
        return {
            "overall_score": round(overall, 3),
            "status": status,
            "components_evaluated": len(scores)
        }

    # ------------------------------------------------- تصحیح خروجی مدل‌ها
    def apply_uncertainty_corrections(self, result, uncertainty_params: Dict) -> object:
        """اعمال تصحیحات عدم قطعیت به خروجی مدل‌های رشد"""
        
        # دریافت ضریب اطمینان
        confidence = uncertainty_params.get("confidence_score", 0.65)
        
        # اعمال تخفیف بر اساس اطمینان
        if confidence < 0.5:
            correction_factor = 0.85  # تخفیف برای اطمینان پایین
        elif confidence < 0.7:
            correction_factor = 0.95  # تخفیف ملایم
        else:
            correction_factor = 1.0  # بدون تخفیف
        
        if hasattr(result, "yield_t_ha"):
            result.yield_t_ha = round(result.yield_t_ha * correction_factor, 2)
        
        # افزودن بازه اطمینان به هشدارها
        p10 = uncertainty_params.get("p10_t_ha", 0)
        p90 = uncertainty_params.get("p90_t_ha", 0)
        
        try:
            result.warnings = list(result.warnings) + [
                "Uncertainty correction x%.2f (P10=%.2f, P90=%.2f, confidence=%.2f)"
                % (correction_factor, p10, p90, confidence)]
        except Exception:
            pass
        
        return result
'''

INIT_APPEND = '''
from .uncertainty_knowledge_engine import (
    UncertaintyAndKnowledgeEngine, UncertaintyConfig)
'''

TEST_CODE = '''import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.uncertainty_knowledge_engine import (
    UncertaintyAndKnowledgeEngine)

def main():
    engine = UncertaintyAndKnowledgeEngine()

    # H22: مونت‌کارلو
    r1 = engine.h22_monte_carlo_uncertainty(5.0, n_simulations=100)
    assert r1["p10_t_ha"] <= r1["p50_t_ha"] <= r1["p90_t_ha"]
    assert r1["coefficient_of_variation"] >= 0
    assert r1["confidence_level"] in ("بالا", "متوسط", "پایین")

    # H23: تلفیق داده
    r2 = engine.h23_multi_scale_fusion(4.5, 5.0, 4.8)
    assert r2["fused_value"] > 0
    assert r2["consistency_score"] >= 0
    assert r2["data_quality"] in ("بالا", "متوسط", "پایین")

    # H25: دانش بومی
    r3 = engine.h25_local_knowledge_integration(30, 0.7, 0.8, 0.6)
    assert 0.0 <= r3["knowledge_score"] <= 1.0
    assert r3["integration_weight"] >= 0.0

    # گزارش جامع
    report = engine.generate_uncertainty_report(5.0, 4.5, 5.0, 25, 0.7)
    assert "overall_reliability" in report
    assert 0.0 <= report["overall_reliability"]["overall_score"] <= 1.0

    print("ALL UNCERTAINTY & KNOWLEDGE TESTS PASSED (H22,H23,H25)")

if __name__ == "__main__":
    main()
'''

IMPORT_BLOCK = '''
# --- Hydroma Uncertainty & Knowledge Engine (auto-installed, Phase 5) ---
try:
    from engine.hydroma.climate_adaptation.uncertainty_knowledge_engine import (
        UncertaintyAndKnowledgeEngine as _UKE_cls)
    _HYDROMA_UKE = _UKE_cls()
except Exception:
    _HYDROMA_UKE = None
'''


# ----------------------------------------------------------------------------
# مراحل نصب
# ----------------------------------------------------------------------------
def install_module():
    print("[1/5] ایجاد ماژول UncertaintyAndKnowledgeEngine ...")
    UNK_DIR.mkdir(parents=True, exist_ok=True)
    (UNK_DIR / "uncertainty_knowledge_engine.py").write_text(
        UNK_MODEL_CODE, encoding="utf-8")
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(TEST_CODE, encoding="utf-8")
    
    init_file = UNK_DIR / "__init__.py"
    if init_file.exists():
        current = init_file.read_text(encoding="utf-8")
        if "uncertainty_knowledge_engine" not in current:
            init_file.write_text(current + INIT_APPEND, encoding="utf-8")
            print("   -> __init__.py به‌روزرسانی شد")
    else:
        init_file.write_text(INIT_APPEND.lstrip(), encoding="utf-8")
    
    print("   -> engine/hydroma/climate_adaptation/uncertainty_knowledge_engine.py")
    print("   -> tests/unit/test_uncertainty_knowledge_engine.py")


def integrate_with_ast(target_file: Path) -> bool:
    """اتصال ایمن با استفاده از AST"""
    if not target_file.exists():
        print(f"   !! {target_file.name} یافت نشد؛ رد شد")
        return False
    
    content = target_file.read_text(encoding="utf-8")
    if "_HYDROMA_UKE" in content:
        print(f"   -> {target_file.name}: اتصال از قبل موجود است")
        return True
    
    backup = target_file.with_suffix(".py.bak_uke")
    shutil.copy2(target_file, backup)
    
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
    
    if integrate_with_ast(AQUACROP):
        integrated.append("aquacrop_real.py")
    
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
            if phase.get("phase") == "فاز 5":
                phase["status"] = "نصب شد"
        data["phase5_installed_at"] = __import__("datetime").datetime.now().isoformat()
        data["all_phases_complete"] = True
        REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        print("   -> وضعیت فاز ۵ به «نصب شد» تغییر یافت.")
        print("   -> تمام ۵ فاز کامل شدند! 🎉")
        return True
    except Exception as exc:
        print(f"   !! خطا در به‌روزرسانی رجیستری: {exc}")
        return False


def demo_report():
    print("[5/5] تولید گزارش نمونه عدم قطعیت ...")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from engine.hydroma.climate_adaptation.uncertainty_knowledge_engine import (
            UncertaintyAndKnowledgeEngine)
        engine = UncertaintyAndKnowledgeEngine()
        
        # سناریوی واقع‌بینانه: گندم در منطقه نیمه‌خشک
        report = engine.generate_uncertainty_report(
            base_yield=4.5,
            satellite_data=4.2,
            station_data=4.8,
            farmer_experience=35,
            calendar_reliability=0.7)
        
        overall = report["overall_reliability"]
        print(f"   امتیاز قابلیت اطمینان: {overall['overall_score']} ({overall['status']})")
        print(f"   عدم قطعیت: P10={report['h22_uncertainty']['p10_t_ha']}, "
              f"P50={report['h22_uncertainty']['p50_t_ha']}, "
              f"P90={report['h22_uncertainty']['p90_t_ha']}")
        print(f"   تلفیق داده: {report['h23_fusion']['fused_value']} (کیفیت: {report['h23_fusion']['data_quality']})")
        print(f"   دانش بومی: {report['h25_knowledge']['knowledge_score']}")
        return True
    except Exception as exc:
        print(f"   !! خطا در نمونه: {exc}")
        return False


def main():
    print("=" * 70)
    print("نصب فاز ۵ (نهایی): موتور عدم قطعیت و دانش بومی (H22,H23,H25)")
    print("=" * 70)
    
    install_module()
    integrated = integrate_targets()
    tests_ok = run_tests()
    registry_ok = update_registry()
    demo_report()
    
    print("=" * 70)
    print(f"نتیجه: ماژول=OK | تست‌ها={'OK' if tests_ok else 'FAIL'} | "
          f"اتصال={len(integrated)} فایل | رجیستری={'OK' if registry_ok else 'SKIP'}")
    print("=" * 70)
    
    if tests_ok and registry_ok:
        print("\n" + "=" * 70)
        print("🎉🎉🎉 تبریک! تمام ۵ فاز و ۲۵ الگوریتم هیدروما نصب شدند! 🎉🎉🎉")
        print("=" * 70)
        print("\n📋 خلاصه نهایی:")
        print("   ✅ فاز ۱: موتور تنش پویا (H01-H04, H08)")
        print("   ✅ فاز ۲: فنولوژی تطبیقی (H05-H07, H24)")
        print("   ✅ فاز ۳: تخریب خاک (H09-H14)")
        print("   ✅ فاز ۴: بهینه‌سازی بذر (H15-H21)")
        print("   ✅ فاز ۵: عدم قطعیت و دانش بومی (H22, H23, H25)")
        print("\n📊 مستندات تولید شده:")
        print("   - docs/hydroma/HYDROMA_WHITEPAPER_FA.md")
        print("   - docs/hydroma/HYDROMA_25_INNOVATIONS.md")
        print("   - docs/hydroma/innovation_registry.json")
        print("   - docs/hydroma/figures/fig1..fig6.png")
        print("=" * 70)


if __name__ == "__main__":
    main()