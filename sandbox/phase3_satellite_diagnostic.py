"""
Phase 3 Diagnostic: Satellite Integration Readiness
هدف: بررسی وضعیت فعلی satellite module و آماده‌سازی برای اتصال واقعی
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


def check_satellite_module():
    print("🛰️ بررسی ماژول satellite فعلی\n")
    
    sat_path = PROJECT_ROOT / "engine" / "hydroma" / "satellite"
    if not sat_path.exists():
        print(f"❌ یافت نشد: {sat_path}")
        return
    
    files = list(sat_path.rglob("*.py"))
    print(f"✅ تعداد فایل‌های satellite: {len(files)}")
    for f in sorted(files):
        rel = f.relative_to(PROJECT_ROOT)
        size = f.stat().st_size
        print(f"   📄 {rel} ({size} bytes)")
    
    # بررسی provider‌ها
    print("\n🔍 بررسی Provider‌های موجود:")
    try:
        from engine.hydroma.satellite.providers import base, earth_search
        print(f"   ✅ base provider: {base.__file__}")
        print(f"   ✅ earth_search provider: {earth_search.__file__}")
        
        # بررسی کلاس‌های موجود
        base_classes = [name for name in dir(base) if not name.startswith("_")]
        print(f"   📦 کلاس‌های base: {base_classes}")
        
    except ImportError as e:
        print(f"   ❌ خطا: {e}")
    
    # بررسی analyzer
    print("\n🔍 بررسی Satellite Analyzer:")
    try:
        from engine.hydroma.satellite import analyzer
        analyzer_classes = [name for name in dir(analyzer) 
                          if name.startswith("Satellite") or name.endswith("Analyzer")]
        print(f"   📦 Analyzer classes: {analyzer_classes}")
    except ImportError as e:
        print(f"   ❌ خطا: {e}")


def check_rasterio():
    print("\n🛰️ بررسی کتابخانه‌های پردازش تصویر")
    
    libs = ["rasterio", "numpy", "shapely", "pyproj", "rioxarray"]
    
    for lib in libs:
        try:
            mod = __import__(lib)
            version = getattr(mod, "__version__", "??")
            print(f"   ✅ {lib} == {version}")
        except ImportError:
            print(f"   ❌ {lib} نصب نیست")


def check_cdse_credentials():
    print("\n🔐 بررسی Credential‌های CDSE (اختیاری)")
    
    import os
    env_vars = ["CDSE_USERNAME", "CDSE_PASSWORD", "CDSE_CLIENT_ID", "CDSE_CLIENT_SECRET"]
    
    has_creds = False
    for var in env_vars:
        if os.getenv(var):
            print(f"   ✅ {var} تنظیم شده")
            has_creds = True
        else:
            print(f"   ⚠️ {var} تنظیم نیست")
    
    if not has_creds:
        print("\n   💡 راهنما: برای دسترسی به CDSE، به یک اکانت رایگان نیاز دارید:")
        print("      1. ثبت‌نام در https://dataspace.copernicus.eu/")
        print("      2. تنظیم CDSE_USERNAME و CDSE_PASSWORD در environment")
        print("      3. یا استفاده از OAuth2 Client Credentials")


def main():
    print("=" * 70)
    print("🔬 Phase 3 Diagnostic: Real Satellite Integration Readiness")
    print("=" * 70)
    
    check_satellite_module()
    check_rasterio()
    check_cdse_credentials()
    
    print("\n" + "=" * 70)
    print("📊 جمع‌بندی و توصیه‌ها")
    print("=" * 70)
    print("\n💡 گام بعدی:")
    print("   1. بررسی خروجی این تشخیص")
    print("   2. ثبت‌نام در CDSE (اگر نیاز به داده‌های واقعی دارید)")
    print("   3. شروع نوشتن RealCDSEProvider")


if __name__ == "__main__":
    main()