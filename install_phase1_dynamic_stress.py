#!/usr/bin/env python3
# ============================================================================
# نصب‌کننده فاز ۱: موتور تنش پویای هیدروما (DynamicStressEngine)
# الگوریتم‌ها: H01, H02, H03, H04, H08
# عملکرد: ایجاد ماژول + تست + اتصال خودکار به aquacrop_real.py (با پشتیبان و rollback)
# ============================================================================
import shutil
import subprocess
import sys
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
DSE_DIR = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation"
AQUACROP = PROJECT_ROOT / "services" / "scientific_motors" / "aquacrop_real.py"
TEST_FILE = PROJECT_ROOT / "tests" / "unit" / "test_dynamic_stress_engine.py"

# ----------------------------------------------------------------------------
# کد ماژول موتور تنش پویا
# ----------------------------------------------------------------------------
ENGINE_CODE = '''# -*- coding: utf-8 -*-
# ============================================================================
# Hydroma Dynamic Stress Engine - Phase 1
# Algorithms: H01 Effective Rain | H02 Night Temp | H03 VPD-ET | H04 Heat Ks | H08 Interaction
# References: IPCC AR6 (2021); Yuan et al. 2019; Zhang et al. 2020; Zscheischler et al. 2018
# ============================================================================
import math
from dataclasses import dataclass
from typing import Optional

__version__ = "1.0.0"


@dataclass
class CropStressParams:
    t_opt_night_c: float = 12.0          # H02: دمای بهینه شبانه
    t_heat_threshold_c: float = 35.0     # H04: آستانه تنش گرمایی
    heat_sensitivity_k: float = 0.5      # H04: شیب منحنی سیگموئید
    vpd_threshold_kpa: float = 1.5       # H03: آستانه VPD
    vpd_coeff: float = 0.05              # H03: ضریب تصحیح تبخیر
    night_coeff_per_deg: float = 0.10    # H02: کاهش ۱۰٪ به ازای هر درجه
    max_night_penalty: float = 0.30
    max_heat_penalty: float = 0.35
    compound_interaction: float = 0.85   # H08: ضریب رویداد ترکیبی


def es_kpa(t_c: float) -> float:
    # فشار بخار اشباع (kPa) - فرمول Tetens
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def vpd_kpa(t_max_c: float, t_min_c: float, rh_pct: float = 50.0) -> float:
    es_mean = (es_kpa(t_max_c) + es_kpa(t_min_c)) / 2.0
    ea = es_mean * max(0.0, min(100.0, rh_pct)) / 100.0
    return max(0.0, es_mean - ea)


class DynamicStressEngine:
    """موتور تنش پویای هیدروما - جایگزین پاسخ‌های خطی فائو"""

    def __init__(self, params: Optional[CropStressParams] = None):
        self.p = params or CropStressParams()

    # ------------------------------------------------------------------ H01
    def h01_intensity_discount(self, rain_mm: float) -> float:
        # تلفیک شدت بارش: بارش‌های سنگین -> رواناب بیشتر -> نفوذ کمتر
        if rain_mm <= 0.0:
            return 0.0
        return 1.0 / (1.0 + (rain_mm / 50.0) ** 1.5)

    def h01_effective_rain_mm(self, rain_mm: float,
                              infiltration: float = 0.8,
                              stage_factor: float = 1.0) -> float:
        if rain_mm <= 0.0:
            return 0.0
        return rain_mm * infiltration * stage_factor * self.h01_intensity_discount(rain_mm)

    # ------------------------------------------------------------------ H02
    def h02_night_penalty(self, t_night_c: float) -> float:
        over = max(0.0, t_night_c - self.p.t_opt_night_c)
        return min(self.p.max_night_penalty, self.p.night_coeff_per_deg * over)

    # ------------------------------------------------------------------ H03
    def h03_et_correction_factor(self, vpd: float) -> float:
        factor = 1.0 + self.p.vpd_coeff * max(0.0, vpd - self.p.vpd_threshold_kpa)
        return min(1.30, factor)

    def h03_corrected_et(self, et_c_mm: float, vpd: float) -> float:
        return et_c_mm * self.h03_et_correction_factor(vpd)

    # ------------------------------------------------------------------ H04
    def h04_heat_ks(self, t_max_c: float) -> float:
        # پاسخ غیرخطی سیگموئید (جایگزین کاهش خطی فائو)
        return 1.0 / (1.0 + math.exp(self.p.heat_sensitivity_k *
                                     (t_max_c - self.p.t_heat_threshold_c)))

    # ------------------------------------------------------------------ H08
    def h08_combined_ks(self, ks_water: float, ks_temp: float,
                        ks_salinity: float = 1.0,
                        compound_event: bool = False) -> float:
        base = ks_water * ks_temp * ks_salinity
        return base * (self.p.compound_interaction if compound_event else 1.0)

    # ------------------------------------------------- تصحیح فصلی خروجی مدل
    def apply_seasonal_correction(self, result, tmin_daily, tmax_daily):
        if not tmin_daily or not tmax_daily:
            return result
        heat_days = sum(1 for t in tmax_daily if t > self.p.t_heat_threshold_c)
        night_over = [max(0.0, t - self.p.t_opt_night_c) for t in tmin_daily]
        mean_over = sum(night_over) / len(night_over)
        heat_factor = 1.0 - min(self.p.max_heat_penalty, 0.02 * heat_days)
        night_factor = 1.0 - min(self.p.max_night_penalty,
                                 self.p.night_coeff_per_deg * mean_over)
        factor = heat_factor * night_factor
        result.yield_t_ha = round(result.yield_t_ha * factor, 2)
        result.biomass_t_ha = round(result.biomass_t_ha * factor, 2)
        try:
            result.warnings = list(result.warnings) + [
                "Hydroma DSE x%.2f (heat_days=%d, night_over=%.1fC)"
                % (factor, heat_days, mean_over)]
        except Exception:
            pass
        return result

    # ------------------------------------------------- منحنی مقایسه‌ای بنچمارک
    def benchmark_curves(self, t_start: float = 25.0, t_end: float = 45.0,
                         step: float = 1.0):
        temps, linear, sigmoid = [], [], []
        t = t_start
        while t <= t_end + 1e-9:
            temps.append(t)
            linear.append(max(0.0, min(1.0, 1.0 - (t - 35.0) / 10.0)))
            sigmoid.append(self.h04_heat_ks(t))
            t += step
        return temps, linear, sigmoid
'''

INIT_CODE = '''from .dynamic_stress_engine import DynamicStressEngine, CropStressParams, vpd_kpa
'''

TEST_CODE = '''import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.dynamic_stress_engine import (
    DynamicStressEngine, vpd_kpa)

def main():
    e = DynamicStressEngine()
    # H01
    assert e.h01_effective_rain_mm(0.0) == 0.0
    d10 = e.h01_intensity_discount(10.0)
    d80 = e.h01_intensity_discount(80.0)
    assert d80 < d10, "H01: discount must decrease with intensity"
    # H02
    assert e.h02_night_penalty(10.0) == 0.0
    assert 0.0 < e.h02_night_penalty(20.0) <= 0.30
    # H03
    v = vpd_kpa(40.0, 25.0, 30.0)
    assert e.h03_et_correction_factor(v) > 1.0
    assert e.h03_et_correction_factor(1.0) == 1.0
    # H04
    ks = [e.h04_heat_ks(t) for t in range(25, 46)]
    assert all(a >= b for a, b in zip(ks, ks[1:])), "H04 must be monotonic decreasing"
    assert abs(e.h04_heat_ks(35.0) - 0.5) < 1e-9
    # H08
    assert e.h08_combined_ks(0.5, 0.5, 1.0, True) < e.h08_combined_ks(0.5, 0.5, 1.0, False)
    print("ALL DSE TESTS PASSED (H01,H02,H03,H04,H08)")

if __name__ == "__main__":
    main()
'''

IMPORT_BLOCK = '''
# --- Hydroma Dynamic Stress Engine (auto-installed, Phase 1) ---
try:
    from engine.hydroma.climate_adaptation.dynamic_stress_engine import (
        DynamicStressEngine as _DSE_cls)
    _HYDROMA_DSE = _DSE_cls()
except Exception:
    _HYDROMA_DSE = None
'''

HOOK_BLOCK = '''        # --- تصحیح اقلیمی هیدروما DSE (H02/H04) ---
        if _HYDROMA_DSE is not None:
            result = _HYDROMA_DSE.apply_seasonal_correction(
                result, config.tmin_daily, config.tmax_daily)

'''


def install_module():
    print("[1/4] ایجاد ماژول DynamicStressEngine ...")
    DSE_DIR.mkdir(parents=True, exist_ok=True)
    (DSE_DIR / "dynamic_stress_engine.py").write_text(ENGINE_CODE, encoding="utf-8")
    (DSE_DIR / "__init__.py").write_text(INIT_CODE, encoding="utf-8")
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(TEST_CODE, encoding="utf-8")
    print("   -> engine/hydroma/climate_adaptation/dynamic_stress_engine.py")
    print("   -> tests/unit/test_dynamic_stress_engine.py")


def integrate_aquacrop():
    print("[2/4] اتصال خودکار به aquacrop_real.py ...")
    if not AQUACROP.exists():
        print("   !! فایل aquacrop_real.py یافت نشد؛ اتصال رد شد.")
        return False
    content = AQUACROP.read_text(encoding="utf-8")
    if "_HYDROMA_DSE" in content:
        print("   -> اتصال از قبل موجود است؛ رد شد.")
        return True
    backup = AQUACROP.with_suffix(".py.bak_dse")
    shutil.copy2(AQUACROP, backup)
    marker_logger = "logger = logging.getLogger(__name__)"
    marker_conf = "# تعیین سطح اطمینان"
    changed = False
    if marker_logger in content:
        content = content.replace(marker_logger, marker_logger + IMPORT_BLOCK, 1)
        changed = True
    if marker_conf in content:
        content = content.replace(marker_conf, HOOK_BLOCK + marker_conf, 1)
        changed = True
    if not changed:
        print("   !! نشانگرهای اتصال یافت نشد؛ اتصال رد شد (ماژول مستقل باقی می‌ماند).")
        return False
    AQUACROP.write_text(content, encoding="utf-8")
    try:
        py_compile.compile(str(AQUACROP), doraise=True)
        print("   -> اتصال اعمال و سینتکس تأیید شد.")
        return True
    except Exception as exc:
        shutil.copy2(backup, AQUACROP)
        print(f"   !! خطای سینتکس؛ rollback انجام شد: {exc}")
        return False


def run_tests():
    print("[3/4] اجرای تست‌های واحد ...")
    proc = subprocess.run([sys.executable, str(TEST_FILE)], cwd=PROJECT_ROOT)
    return proc.returncode == 0


def demo_simulation():
    print("[4/4] شبیه‌سازی نمونه با تصحیح DSE ...")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from services.scientific_motors.aquacrop_real import AquaCropSimulator
        sim = AquaCropSimulator()
        res = sim.run("W001", "SITE037", "rainfed")
        print(f"   عملکرد نهایی (با تصحیح هیدروما): {res.yield_t_ha} t/ha")
        for w in res.warnings:
            if "DSE" in w:
                print(f"   [DSE] {w}")
        return True
    except Exception as exc:
        print(f"   !! شبیه‌سازی نمونه اجرا نشد: {exc}")
        return False


def main():
    print("=" * 70)
    print("نصب فاز ۱: موتور تنش پویای هیدروما (H01,H02,H03,H04,H08)")
    print("=" * 70)
    install_module()
    integrated = integrate_aquacrop()
    tests_ok = run_tests()
    demo_simulation()
    print("=" * 70)
    print(f"نتیجه: ماژول=OK | تست‌ها={'OK' if tests_ok else 'FAIL'} | "
          f"اتصال={'OK' if integrated else 'SKIP'}")
    print("=" * 70)


if __name__ == "__main__":
    main()