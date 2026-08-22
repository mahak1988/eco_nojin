"""
Phase 2 Diagnostic: C++ Bindings Health Check
هدف: بررسی وضعیت واقعی pybind11 bindings قبل از فعال‌سازی bridge‌ها
پروتکل ایمنی: Read-only (هیچ تغییری در پروژه ایجاد نمی‌کند)
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CPP_CORE = PROJECT_ROOT / "engine" / "cpp_core"
CPP_BRIDGE = PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge"


def check_source_files():
    """بررسی وجود سورس‌های C++ و هدرها"""
    print("=" * 70)
    print("📁 گام ۱: بررسی سورس‌های C++ در engine/cpp_core")
    print("=" * 70)

    if not CPP_CORE.exists():
        print(f"❌ پوشه یافت نشد: {CPP_CORE}")
        return False

    hpp_files = list(CPP_CORE.rglob("*.hpp"))
    cpp_files = list(CPP_CORE.rglob("*.cpp"))
    binding_files = list((CPP_CORE / "bindings").rglob("*.cpp")) if (CPP_CORE / "bindings").exists() else []

    print(f"✅ هدرهای یافت‌شده: {len(hpp_files)}")
    for f in hpp_files:
        print(f"   📄 {f.relative_to(PROJECT_ROOT)}")

    print(f"\n✅ سورس‌های یافت‌شده: {len(cpp_files)}")
    for f in cpp_files:
        print(f"   📄 {f.relative_to(PROJECT_ROOT)}")

    print(f"\n✅ فایل‌های binding یافت‌شده: {len(binding_files)}")
    for f in binding_files:
        print(f"   📄 {f.relative_to(PROJECT_ROOT)}")

    # بررسی CMakeLists.txt
    cmake = CPP_CORE / "CMakeLists.txt"
    if cmake.exists():
        print(f"\n✅ CMakeLists.txt موجود است: {cmake}")
    else:
        print(f"\n❌ CMakeLists.txt یافت نشد!")

    return True


def check_compiled_modules():
    """بررسی ماژول‌های کامپایل‌شده (.pyd/.so)"""
    print("\n" + "=" * 70)
    print("🔍 گام ۲: بررسی ماژول‌های کامپایل‌شده")
    print("=" * 70)

    # الگوهای مختلف نام‌گذاری
    patterns = ["*.pyd", "*.so", "*.dll"]
    found_modules = []

    for pattern in patterns:
        for f in PROJECT_ROOT.rglob(pattern):
            if ".venv" in str(f) or "__pycache__" in str(f):
                continue
            if "hydroma" in str(f) or "cpp_core" in str(f) or "build" in str(f):
                found_modules.append(f)

    if found_modules:
        print(f"✅ ماژول‌های کامپایل‌شده یافت‌شده: {len(found_modules)}")
        for f in found_modules:
            size_kb = f.stat().st_size / 1024
            print(f"   📦 {f.relative_to(PROJECT_ROOT)} ({size_kb:.1f} KB)")
    else:
        print("❌ هیچ ماژول کامپایل‌شده‌ای یافت نشد!")
        print("💡 این یعنی bindings هنوز با pybind11 کامپایل نشده‌اند.")

    return found_modules


def check_bridge_state():
    """بررسی وضعیت فعلی cpp_bridge‌ها"""
    print("\n" + "=" * 70)
    print("🌉 گام ۳: بررسی وضعیت cpp_bridge‌ها")
    print("=" * 70)

    if not CPP_BRIDGE.exists():
        print(f"❌ پوشه یافت نشد: {CPP_BRIDGE}")
        return []

    bridge_files = list(CPP_BRIDGE.glob("*.py"))
    bridge_info = []

    for f in bridge_files:
        if f.name == "__init__.py":
            continue

        content = f.read_text(encoding="utf-8")
        lines = content.splitlines()

        # تشخیص وضعیت
        has_pass = "pass" in content
        has_not_implemented = "NotImplementedError" in content
        has_real_import = any(
            imp in content for imp in [
                "from engine.cpp_core",
                "from .cpp_bindings",
                "from cpp_bindings",
                "import hydroma_cpp",
            ]
        )
        has_fallback = "fallback" in content.lower() or "pure_python" in content.lower()

        if has_pass and not has_real_import:
            status = "STUB (فقط pass)"
        elif has_not_implemented and not has_real_import:
            status = "STUB (NotImplementedError)"
        elif has_real_import:
            status = "CONNECTED (دارای import به C++)"
        elif has_fallback:
            status = "FALLBACK (فقط Python)"
        else:
            status = "UNKNOWN"

        # شمارش توابع
        func_count = sum(1 for line in lines if "def " in line and not line.strip().startswith("#"))

        info = {
            "file": f.name,
            "status": status,
            "lines": len(lines),
            "functions": func_count,
            "has_real_cxx_import": has_real_import,
        }
        bridge_info.append(info)

        print(f"\n📄 {f.name}")
        print(f"   وضعیت: {status}")
        print(f"   خطوط: {len(lines)} | توابع: {func_count}")
        print(f"   اتصال C++ واقعی: {'✅' if has_real_import else '❌'}")

    return bridge_info


def test_import_binding():
    """تست import کردن مستقیم ماژول C++ در صورت وجود"""
    print("\n" + "=" * 70)
    print("🧪 گام ۴: تست import کردن ماژول C++")
    print("=" * 70)

    # نام‌های احتمالی برای ماژول C++
    possible_names = [
        "hydroma_cpp",
        "hydroma",
        "engine.cpp_core.bindings.hydroma",
        "cpp_bindings",
    ]

    sys.path.insert(0, str(PROJECT_ROOT))

    for name in possible_names:
        try:
            mod = importlib.import_module(name)
            print(f"✅ ماژول '{name}' با موفقیت import شد!")
            print(f"   📦 توابع موجود:")
            for attr in dir(mod):
                if not attr.startswith("_"):
                    print(f"      - {attr}")
            return name, mod
        except Exception as e:
            print(f"❌ '{name}' یافت نشد: {type(e).__name__}")

    print("\n💡 نتیجه: هیچ ماژول C++ قابل import یافت نشد.")
    return None, None


def main():
    print("🔬 شروع تشخیص وضعیت C++ bindings")
    print(f"📁 مسیر پروژه: {PROJECT_ROOT}\n")

    # گام ۱
    check_source_files()

    # گام ۲
    compiled = check_compiled_modules()

    # گام ۳
    bridges = check_bridge_state()

    # گام ۴
    binding_name, binding_mod = test_import_binding()

    # جمع‌بندی نهایی
    print("\n" + "=" * 70)
    print("📊 جمع‌بندی تشخیص و توصیه‌ها")
    print("=" * 70)

    if not compiled:
        print("\n⚠️ تشخیص: bindings هنوز کامپایل نشده‌اند.")
        print("   توصیه: ابتدا باید C++ core با CMake/pybind11 کامپایل شود.")
        print("   گزینه‌ها:")
        print("   1. نصب CMake و کامپایل دستی")
        print("   2. استفاده از scikit-build یا setuptools برای ساخت خودکار")
        print("   3. استفاده از Numba به عنوان جایگزین موقت (بدون نیاز به C++)")
    else:
        if binding_name:
            print(f"\n✅ ماژول '{binding_name}' آماده استفاده است.")
            print("   توصیه: bridge‌ها را می‌توان به این ماژول متصل کرد.")
        else:
            print("\n⚠️ ماژول‌های کامپایل‌شده یافت شدند اما import نشدند.")
            print("   توصیه: بررسی PYTHONPATH و مسیر ماژول‌ها.")

    # شناسایی bridge‌های نیازمند کار
    needs_work = [b for b in bridges if not b["has_real_cxx_import"]]
    if needs_work:
        print(f"\n🔧 Bridge‌های نیازمند بازنویسی: {len(needs_work)}")
        for b in needs_work:
            print(f"   - {b['file']} ({b['functions']} تابع)")


if __name__ == "__main__":
    main()