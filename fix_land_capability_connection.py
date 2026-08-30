#!/usr/bin/env python3
"""
اسکریپت اتصال ایمن SoilDegradationModel به land_capability.py
با رعایت صحیح جایگاه from __future__ imports
"""
import shutil
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
TARGET = PROJECT_ROOT / "services" / "scientific_motors" / "land_capability.py"

IMPORT_BLOCK = '''
# --- Hydroma Soil Degradation Model (auto-installed, Phase 3) ---
try:
    from engine.hydroma.climate_adaptation.soil_degradation_model import (
        SoilDegradationModel as _SDM_cls)
    _HYDROMA_SDM = _SDM_cls()
except Exception:
    _HYDROMA_SDM = None
'''

def find_safe_insert_position(lines):
    """یافتن جایگاه امن برای درج بلوک وارد کردن"""
    insert_pos = 0
    
    # عبور از خطوط ابتدایی: کامنت، رشته مستند، و از همه مهم‌تر
    # تمام خطوط from __future__ و import در ابتدای فایل
    for i, line in enumerate(lines):
        stripped = line.strip()
        # ادامه عبور از خطوط خالی، کامنت، و دستورات مستند
        if not stripped or stripped.startswith('#'):
            insert_pos = i + 1
            continue
        # عبور از رشته‌های مستند
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # اگر رشته یک‌خطی است
            if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                insert_pos = i + 1
                continue
            # اگر رشته چندخطی است، تا پایان آن عبور کن
            for j in range(i + 1, len(lines)):
                if '"""' in lines[j] or "'''" in lines[j]:
                    insert_pos = j + 1
                    break
            continue
        # عبور از from __future__
        if stripped.startswith('from __future__'):
            insert_pos = i + 1
            continue
        # عبور از دستورات import
        if stripped.startswith('import ') or stripped.startswith('from '):
            insert_pos = i + 1
            continue
        # به اولین خط غیر-ماژول رسیدیم؛ اینجا متوقف شو
        break
    
    return insert_pos

def main():
    print("=" * 70)
    print("اتصال ایمن SoilDegradationModel به land_capability.py")
    print("=" * 70)
    
    if not TARGET.exists():
        print(f"❌ فایل یافت نشد: {TARGET}")
        return
    
    content = TARGET.read_text(encoding="utf-8")
    
    # بررسی اتصال قبلی
    if "_HYDROMA_SDM" in content:
        print("ℹ️ اتصال از قبل موجود است؛ رد شد.")
        return
    
    # پشتیبان‌گیری
    backup = TARGET.with_suffix(".py.bak_sdm_v2")
    shutil.copy2(TARGET, backup)
    print(f"📦 پشتیبان: {backup.name}")
    
    lines = content.split("\n")
    insert_pos = find_safe_insert_position(lines)
    print(f"📍 جایگاه درج: خط {insert_pos + 1}")
    
    # درج بلوک
    block_lines = IMPORT_BLOCK.strip().split("\n")
    new_lines = lines[:insert_pos] + [""] + block_lines + [""] + lines[insert_pos:]
    new_content = "\n".join(new_lines)
    
    # نوشتن و بررسی سینتکس
    TARGET.write_text(new_content, encoding="utf-8")
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✅ اتصال اعمال و سینتکس تأیید شد.")
    except Exception as exc:
        shutil.copy2(backup, TARGET)
        print(f"❌ خطای سینتکس؛ rollback انجام شد: {exc}")
        return
    
    # تست وارد کردن
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        # حذف کش ماژول در صورت وجود
        for mod in list(sys.modules.keys()):
            if "land_capability" in mod or "soil_degradation" in mod:
                del sys.modules[mod]
        
        from services.scientific_motors.land_capability import _HYDROMA_SDM
        if _HYDROMA_SDM is not None:
            print(f"✅ ماژول خاک در land_capability فعال است: {_HYDROMA_SDM.__class__.__name__}")
        else:
            print("⚠️ ماژول خاک وارد شد اما نمونه‌سازی نشد (حالت غیرفعال)")
    except Exception as exc:
        print(f"⚠️ تست وارد کردن: {exc}")
    
    print("=" * 70)
    print("🎉 اتصال land_capability.py کامل شد")
    print("=" * 70)

if __name__ == "__main__":
    main()