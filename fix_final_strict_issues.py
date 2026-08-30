#!/usr/bin/env python3
"""
============================================================================
پچ نهایی: رفع خطای بحرانی و بهبود هشدار
۱. افزودن ویژگی `cfg` به DynamicStressEngine (سازگاری با سایر ماژول‌ها)
۲. بهبود رفتار پنجره‌های صفر در ClimateAdaptivePhenology
============================================================================
"""
import ast
import shutil
import py_compile
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
DSE_FILE = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation" / "dynamic_stress_engine.py"
CAP_FILE = PROJECT_ROOT / "engine" / "hydroma" / "climate_adaptation" / "climate_adaptive_phenology.py"
TEST_FILE = PROJECT_ROOT / "tests" / "strict_challenge_v2.py"


def add_cfg_property_to_dse():
    """افزودن ویژگی `cfg` به DynamicStressEngine برای سازگاری با سایر ماژول‌ها"""
    print("[1/3] افزودن ویژگی `cfg` به DynamicStressEngine ...")
    
    if not DSE_FILE.exists():
        print(f"   !! فایل یافت نشد: {DSE_FILE}")
        return False
    
    content = DSE_FILE.read_text(encoding="utf-8")
    
    # بررسی اینکه قبلاً اضافه نشده باشد
    if "@property" in content and "def cfg(self)" in content:
        print("   -> ویژگی `cfg` از قبل موجود است")
        return True
    
    # پشتیبان‌گیری
    backup = DSE_FILE.with_suffix(".py.bak_cfg")
    shutil.copy2(DSE_FILE, backup)
    
    # یافتن کلاس DynamicStressEngine و اضافه کردن ویژگی
    # استراتژی: بعد از __init__، یک ویژگی @property اضافه می‌کنیم
    
    # الگوی جستجو: پیدا کردن `def __init__` در کلاس
    # و اضافه کردن ویژگی بعد از آن
    
    # روش: پیدا کردن خط `self.p = params or CropStressParams()`
    # و اضافه کردن ویژگی در انتهای کلاس
    
    # بهترین روش: اضافه کردن ویژگی در انتهای فایل، داخل کلاس
    # برای این کار، از روش جایگزینی استفاده می‌کنیم
    
    # پیدا کردن `def h01_intensity_discount` (اولین متد بعد از __init__)
    # و اضافه کردن ویژگی قبل از آن
    
    marker = "    # ------------------------------------------------------------------ H01"
    if marker in content:
        property_code = '''
    @property
    def cfg(self):
        """ویژگی سازگاری با سایر ماژول‌ها (alias برای self.p)"""
        return self.p

    @cfg.setter
    def cfg(self, value):
        self.p = value

'''
        content = content.replace(marker, property_code + marker)
        DSE_FILE.write_text(content, encoding="utf-8")
        
        # بررسی سینتکس
        try:
            py_compile.compile(str(DSE_FILE), doraise=True)
            print("   ✅ ویژگی `cfg` اضافه شد و سینتکس تأیید شد")
            return True
        except Exception as e:
            shutil.copy2(backup, DSE_FILE)
            print(f"   !! خطای سینتکس؛ rollback: {e}")
            return False
    else:
        # روش جایگزین: پیدا کردن `def h01_`
        alt_marker = "    def h01_"
        if alt_marker in content:
            property_code = '''
    @property
    def cfg(self):
        """ویژگی سازگاری با سایر ماژول‌ها (alias برای self.p)"""
        return self.p

    @cfg.setter
    def cfg(self, value):
        self.p = value

'''
            # پیدا کردن اولین رخداد و اضافه کردن قبل از آن
            idx = content.find(alt_marker)
            if idx > 0:
                content = content[:idx] + property_code + content[idx:]
                DSE_FILE.write_text(content, encoding="utf-8")
                try:
                    py_compile.compile(str(DSE_FILE), doraise=True)
                    print("   ✅ ویژگی `cfg` اضافه شد (روش جایگزین)")
                    return True
                except Exception as e:
                    shutil.copy2(backup, DSE_FILE)
                    print(f"   !! خطای سینتکس؛ rollback: {e}")
                    return False
        
        print("   !! نشانگر مناسب یافت نشد")
        return False


def improve_zero_window_behavior():
    """بهبود رفتار پنجره‌های صفر در ClimateAdaptivePhenology"""
    print("[2/3] بهبود رفتار پنجره‌های صفر ...")
    
    if not CAP_FILE.exists():
        print(f"   !! فایل یافت نشد: {CAP_FILE}")
        return False
    
    content = CAP_FILE.read_text(encoding="utf-8")
    
    # پشتیبان‌گیری
    backup = CAP_FILE.with_suffix(".py.bak_zero")
    shutil.copy2(CAP_FILE, backup)
    
    # یافتن بخش مربوط به محاسبه پنجره مؤثر
    # الگوی فعلی:
    # effective_window = min(rain_window_days, temp_window_days, stress_onset_day)
    # effective_window -= self.cfg.duration_buffer_days
    
    old_pattern = '''        # پنجره مؤثر رشد = حداقل پنجره‌های موجود
        effective_window = min(rain_window_days, temp_window_days, stress_onset_day)
        effective_window -= self.cfg.duration_buffer_days'''
    
    new_pattern = '''        # پنجره مؤثر رشد = حداقل پنجره‌های موجود
        effective_window = min(rain_window_days, temp_window_days, stress_onset_day)
        effective_window -= self.cfg.duration_buffer_days
        
        # محافظت در برابر پنجره‌های صفر یا منفی
        if effective_window <= 0:
            effective_window = 30  # حداقل پنجره رشد برای بقا
            risk_assessment = "ریسک بسیار بالا - پنجره رشد محدود"'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        CAP_FILE.write_text(content, encoding="utf-8")
        try:
            py_compile.compile(str(CAP_FILE), doraise=True)
            print("   ✅ رفتار پنجره‌های صفر بهبود یافت")
            return True
        except Exception as e:
            shutil.copy2(backup, CAP_FILE)
            print(f"   !! خطای سینتکس؛ rollback: {e}")
            return False
    else:
        # تلاش برای یافتن الگوی ساده‌تر
        simple_old = "effective_window -= self.cfg.duration_buffer_days"
        simple_new = '''effective_window -= self.cfg.duration_buffer_days
        
        # محافظت در برابر پنجره‌های صفر یا منفی
        if effective_window <= 0:
            effective_window = 30  # حداقل پنجره رشد برای بقا'''
        
        if simple_old in content:
            content = content.replace(simple_old, simple_new, 1)
            CAP_FILE.write_text(content, encoding="utf-8")
            try:
                py_compile.compile(str(CAP_FILE), doraise=True)
                print("   ✅ رفتار پنجره‌های صفر بهبود یافت (روش ساده)")
                return True
            except Exception as e:
                shutil.copy2(backup, CAP_FILE)
                print(f"   !! خطای سینتکس؛ rollback: {e}")
                return False
        
        print("   !! الگوی مناسب یافت نشد")
        return False


def rerun_strict_challenge():
    """اجرای مجدد چالش سختگیرانه"""
    print("[3/3] اجرای مجدد چالش سختگیرانه ...")
    proc = subprocess.run([sys.executable, str(TEST_FILE)], cwd=PROJECT_ROOT)
    return proc.returncode == 0


def main():
    print("=" * 70)
    print("پچ نهایی: رفع خطای بحرانی و بهبود هشدار")
    print("=" * 70)
    
    fix1 = add_cfg_property_to_dse()
    fix2 = improve_zero_window_behavior()
    
    if fix1 and fix2:
        print("\nهر دو اصلاح اعمال شد. اجرای مجدد چالش ...")
        rerun_strict_challenge()
    else:
        print("\nبرخی اصلاحات اعمال نشد. لطفاً بررسی کنید.")
    
    print("=" * 70)


if __name__ == "__main__":
    main()