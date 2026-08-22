"""
Phase 3a: Install Dependencies for Multi-Source Satellite Engine
هدف: نصب تمام کتابخانه‌های مورد نیاز برای فاز ۳ گسترش‌یافته
پروتکل: Read-only check + explicit install with confirmation
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VENV_PIP = Path(sys.executable).parent / "Scripts" / "pip.exe"
if not VENV_PIP.exists():
    VENV_PIP = Path(sys.executable).parent / "pip.exe"

# کتابخانه‌های ضروری با دلیل استفاده
REQUIRED_PACKAGES = {
    "stackstac": "STAC to xarray stack (برای پردازش بهینه Sentinel-2)",
    "pystac-client": "STAC API client (اتصال به Earth Search)",
    "xarray": "Multi-dimensional data handling (داده‌های ماهواره‌ای 4D)",
    "rioxarray": "rasterio + xarray integration (geospatial xarray)",
    "dask": "Parallel computing (پردازش موازی تصاویر بزرگ)",
    "scipy": "Scientific computing (filtering, interpolation, optimization)",
    "scikit-image": "Image processing (cloud detection, morphology)",
    "tenacity": "Retry with exponential backoff (rate limit handling)",
    "diskcache": "Persistent caching (جلوگیری از دانلود مجدد)",
    "cdsapi": "Climate Data Store API (AgERA5, ERA5-Land, Seasonal)",
    "ecmwf-api-client": "ECMWF API (alternative for ERA5)",
    "tqdm": "Progress bars (UX بهتر برای دانلود)",
}


def check_installed():
    """بررسی کتابخانه‌های نصب‌شده"""
    installed = []
    missing = []
    
    print("=" * 70)
    print("🔍 بررسی کتابخانه‌های فعلی")
    print("=" * 70)
    
    for pkg, reason in REQUIRED_PACKAGES.items():
        try:
            mod = __import__(pkg.replace("-", "_"))
            version = getattr(mod, "__version__", "??")
            print(f"   ✅ {pkg:<22} {version:<10} - {reason[:40]}")
            installed.append(pkg)
        except ImportError:
            print(f"   ❌ {pkg:<22} missing    - {reason[:40]}")
            missing.append(pkg)
    
    return installed, missing


def install_packages(missing: list, dry_run: bool = False):
    """نصب کتابخانه‌های گمشده"""
    if not missing:
        print("\n✅ همه کتابخانه‌ها نصب هستند!")
        return
    
    print("\n" + "=" * 70)
    print(f"📦 کتابخانه‌های نیازمند نصب ({len(missing)}):")
    print("=" * 70)
    for pkg in missing:
        print(f"   • {pkg}")
    
    if dry_run:
        print(f"\n🔍 [DRY-RUN] دستور نصب:")
        print(f"   pip install {' '.join(missing)}")
        return
    
    print(f"\n🚀 شروع نصب با pip...")
    result = subprocess.run(
        [str(VENV_PIP), "install"] + missing,
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        print(f"✅ نصب با موفقیت انجام شد.")
    else:
        print(f"⚠️ برخی خطاها رخ داد:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)


def verify_cds_credentials():
    """بررسی credential‌های CDS برای AgERA5"""
    print("\n" + "=" * 70)
    print("🔐 بررسی CDS/ADS credentials")
    print("=" * 70)
    
    cds_rc = Path.home() / ".cdsapirc"
    ads_rc = Path.home() / ".adsapirc"
    
    if cds_rc.exists():
        print(f"   ✅ {cds_rc} یافت شد")
        content = cds_rc.read_text()
        if "url:" in content and "key:" in content:
            print(f"   ✅ ساختار معتبر (URL + Key)")
        else:
            print(f"   ⚠️ ساختار ناقص")
    else:
        print(f"   ❌ {cds_rc} یافت نشد")
        print(f"\n   💡 راهنما: فایل را با این محتوا ایجاد کنید:")
        print(f"   url: https://cds.climate.copernicus.eu/api")
        print(f"   key: <UID>:<API-key>")
        print(f"   کلید را از https://cds.climate.copernicus.eu/api-how-to بگیرید")
    
    if ads_rc.exists():
        print(f"   ✅ {ads_rc} یافت شد")
    else:
        print(f"   ⚠️ {ads_rc} یافت نشد (برای CAMS لازم است)")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    
    print("🚀 Phase 3a: Dependencies Setup\n")
    
    installed, missing = check_installed()
    
    if not args.skip_install:
        install_packages(missing, dry_run=args.dry_run)
    
    verify_cds_credentials()
    
    print("\n" + "=" * 70)
    print("📊 جمع‌بندی")
    print("=" * 70)
    print(f"   نصب‌شده: {len(installed)}")
    print(f"   نیازمند: {len(missing)}")
    
    if not args.dry_run and not missing:
        print("\n🎉 همه dependencies آماده هستند!")
        print("   گام بعدی: python sandbox\\phase3b_multi_source_providers.py")


if __name__ == "__main__":
    main()