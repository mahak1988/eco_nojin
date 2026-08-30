#!/usr/bin/env python3
"""
اسکریپت اتصال ایمن SoilDegradationModel به land_capability.py
روش: نرمال‌سازی جایگاه from __future__ + درج بلوک بعد از تمام importها
"""
import shutil
import py_compile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
TARGET = PROJECT_ROOT / "services" / "scientific_motors" / "land_capability.py"

IMPORT_BLOCK = '''# --- Hydroma Soil Degradation Model (auto-installed, Phase 3) ---
try:
    from engine.hydroma.climate_adaptation.soil_degradation_model import (
        SoilDegradationModel as _SDM_cls)
    _HYDROMA_SDM = _SDM_cls()
except Exception:
    _HYDROMA_SDM = None'''


def find_docstring_end(lines):
    """یافتن انتهای رشته مستند اولیه فایل"""
    if not lines:
        return 0
    first = lines[0].strip()
    # رشته مستند یک‌خطی
    if (first.startswith('"""') and first.endswith('"""') and len(first) > 3) or \
       (first.startswith("'''") and first.endswith("'''") and len(first) > 3):
        return 1
    # رشته مستند چندخطی
    if first.startswith('"""') or first.startswith("'''"):
        marker = first[:3]
        for i in range(1, len(lines)):
            if marker in lines[i]:
                return i + 1
    return 0


def normalize_future_import(lines):
    """حذف تمام خطوط from __future__ و بازگرداندن یک نسخه در ابتدای فایل"""
    # حذف تمام نسخه‌های موجود
    lines = [l for l in lines if not l.strip().startswith("from __future__")]
    # پیدا کردن جای مناسب بعد از مستند
    insert_pos = find_docstring_end(lines)
    # درج در ابتدای کد
    lines.insert(insert_pos, "from __future__ import annotations")
    return lines, insert_pos


def find_import_block_end(lines, start_pos):
    """یافتن انتهای بلوک دستورات import برای درج بلوک جدید"""
    last_import = start_pos
    for i in range(start_pos + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            last_import = i
        elif stripped.startswith("#") or not stripped:
            continue
        else:
            break
    return last_import + 1


def main():
    print("=" * 70)
    print("اتصال ایمن SoilDegradationModel به land_capability.py (نسخه ۳)")
    print("=" * 70)

    if not TARGET.exists():
        print(f"❌ فایل یافت نشد: {TARGET}")
        return

    content = TARGET.read_text(encoding="utf-8")

    if "_HYDROMA_SDM" in content:
        print("ℹ️ اتصال از قبل موجود است؛ رد شد.")
        return

    # پشتیبان‌گیری
    backup = TARGET.with_suffix(".py.bak_sdm_v3")
    shutil.copy2(TARGET, backup)
    print(f"📦 پشتیبان: {backup.name}")

    lines = content.split("\n")

    # مرحله ۱: نرمال‌سازی from __future__
    lines, future_pos = normalize_future_import(lines)
    print(f"✅ from __future__ به خط {future_pos + 1} منتقل شد")

    # مرحله ۲: یافتن جای مناسب برای درج بلوک (بعد از همه importها)
    block_insert_pos = find_import_block_end(lines, future_pos)
    print(f"📍 جایگاه درج بلوک: خط {block_insert_pos + 1}")

    # مرحله ۳: درج بلوک
    block_lines = IMPORT_BLOCK.split("\n")
    lines = lines[:block_insert_pos] + [""] + block_lines + [""] + lines[block_insert_pos:]

    # مرحله ۴: نوشتن و بررسی سینتکس
    new_content = "\n".join(lines)
    TARGET.write_text(new_content, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✅ اتصال اعمال و سینتکس تأیید شد.")
    except Exception as exc:
        shutil.copy2(backup, TARGET)
        print(f"❌ خطای سینتکس؛ rollback انجام شد: {exc}")
        return

    # مرحله ۵: تست وارد کردن
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        for mod in list(sys.modules.keys()):
            if "land_capability" in mod or "soil_degradation" in mod:
                del sys.modules[mod]
        from services.scientific_motors.land_capability import _HYDROMA_SDM
        if _HYDROMA_SDM is not None:
            print(f"✅ ماژول خاک فعال شد: {_HYDROMA_SDM.__class__.__name__}")
        else:
            print("⚠️ ماژول وارد شد اما نمونه‌سازی نشد")
    except Exception as exc:
        print(f"⚠️ تست وارد کردن: {exc}")

    print("=" * 70)
    print("🎉 اتصال land_capability.py کامل شد")
    print("=" * 70)


if __name__ == "__main__":
    main()