"""
Phase 2c: Signature Reporter
هدف: گزارش دقیق امضای توابع bridge و hydroma_core برای طراحی اتصال صحیح
پروتکل: Read-only (هیچ تغییری در کد ایجاد نمی‌کند)
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge"))
sys.path.insert(0, str(PROJECT_ROOT))


def get_public_functions(module):
    """استخراج توابع عمومی یک ماژول با امضای کامل"""
    results = []
    for name in sorted(dir(module)):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if callable(obj) and not isinstance(obj, type):
            try:
                sig = inspect.signature(obj)
                doc = (obj.__doc__ or "").split("\n")[0].strip()[:100]
                results.append((name, sig, doc))
            except (ValueError, TypeError):
                results.append((name, "(???)", ""))
    return results


def report_module(title, module):
    print(f"\n{'=' * 70}")
    print(f"📦 {title}")
    print(f"   Path: {module.__file__}")
    print(f"{'=' * 70}")
    
    funcs = get_public_functions(module)
    print(f"\n🔧 توابع عمومی ({len(funcs)}):")
    for name, sig, doc in funcs:
        print(f"\n   ✓ {name}{sig}")
        if doc:
            print(f"     📝 {doc}")


def main():
    print("🔬 گزارش امضای توابع bridge‌ها و hydroma_core\n")

    # 1. hydroma_core (C++ bindings)
    try:
        import hydroma_core
        report_module("hydroma_core (C++)", hydroma_core)
    except ImportError as e:
        print(f"❌ hydroma_core یافت نشد: {e}")
        return

    # 2. Bridge‌های فعلی
    try:
        from engine.hydroma.cpp_bridge import (
            soil_physics_fast,
            hydrology_fast,
            indices_fast,
        )
        report_module("soil_physics_fast (bridge فعلی)", soil_physics_fast)
        report_module("hydrology_fast (bridge فعلی)", hydrology_fast)
        report_module("indices_fast (bridge فعلی)", indices_fast)
    except ImportError as e:
        print(f"⚠️ خطا در import bridge‌ها: {e}")

    # 3. Mapping پیشنهادی خودکار
    print(f"\n{'=' * 70}")
    print("🔗 Mapping پیشنهادی (بر اساس نام تابع)")
    print(f"{'=' * 70}")
    
    cxx_funcs = {name for name in dir(hydroma_core) 
                 if not name.startswith("_") and callable(getattr(hydroma_core, name))}
    
    bridges = [
        ("soil_physics_fast", soil_physics_fast),
        ("hydrology_fast", hydrology_fast),
        ("indices_fast", indices_fast),
    ]
    
    for bridge_name, bridge_mod in bridges:
        print(f"\n📦 {bridge_name}:")
        bridge_funcs = [name for name in dir(bridge_mod) 
                       if not name.startswith("_") and callable(getattr(bridge_mod, name))]
        
        for fn in bridge_funcs:
            # تطبیق نام (با حذف prefix‌های معمول)
            base = fn.replace("_fast", "").replace("_array", "").replace("_cxx", "")
            
            # جستجوی تطبیق
            matches = [cxx for cxx in cxx_funcs if base in cxx or cxx in fn]
            
            if matches:
                print(f"   ✅ {fn:<35} → {matches[0]}")
            else:
                print(f"   ❓ {fn:<35} → (تطبیق یافت نشد - نیاز به بررسی)")


if __name__ == "__main__":
    main()