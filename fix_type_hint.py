#!/usr/bin/env python3
"""
اسکریپت اصلاح خطای NameError در type hint کلاس‌های خود-ارجاع
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.resolve()
CROP_DB = PROJECT_ROOT / "services" / "scientific_motors" / "crop_database.py"
AQUACROP = PROJECT_ROOT / "services" / "scientific_motors" / "aquacrop_real.py"

def fix_self_referencing_types(filepath: Path) -> int:
    """تبدیل ارجاعات خود-ارجاع به رشته در تمام فایل"""
    if not filepath.exists():
        print(f"❌ فایل یافت نشد: {filepath}")
        return 0
    
    content = filepath.read_text(encoding="utf-8")
    original = content
    
    # الگوهای خود-ارجاعی که باید اصلاح شوند
    patterns = [
        ('Optional[CropDatabaseService]', 'Optional["CropDatabaseService"]'),
        ('Optional[AquaCropSimulator]', 'Optional["AquaCropSimulator"]'),
        ('-> CropDatabaseService:', '-> "CropDatabaseService":'),
        ('-> AquaCropSimulator:', '-> "AquaCropSimulator":'),
    ]
    
    count = 0
    for old, new in patterns:
        if old in content:
            content = content.replace(old, new)
            count += 1
    
    if count > 0:
        filepath.write_text(content, encoding="utf-8")
        print(f"   ✅ {filepath.name}: {count} الگوی خود-ارجاعی اصلاح شد")
    else:
        print(f"   ℹ️ {filepath.name}: نیازی به اصلاح نبود")
    
    return count

def verify_syntax(filepath: Path) -> bool:
    """بررسی سینتکس"""
    try:
        content = filepath.read_text(encoding="utf-8")
        compile(content, filepath.name, "exec")
        return True
    except SyntaxError as e:
        print(f"   ❌ {filepath.name}: خطای سینتکس: {e}")
        return False

def test_import():
    """تست ایمپورت و عملکرد"""
    sys.path.insert(0, str(PROJECT_ROOT))
    
    # حذف ماژول‌های کش‌شده
    modules_to_remove = [k for k in list(sys.modules.keys()) 
                        if 'crop_database' in k or 'aquacrop' in k or 'data_repository' in k]
    for m in modules_to_remove:
        del sys.modules[m]
    
    try:
        from services.scientific_motors.crop_database import CropDatabaseService, get_service
        from services.scientific_motors.crop_database import get_crop_by_id, filter_drought_tolerant
        print("   ✅ crop_database.py با موفقیت ایمپورت شد")
        
        from services.scientific_motors.aquacrop_real import AquaCropSimulator, run_aquacrop
        print("   ✅ aquacrop_real.py با موفقیت ایمپورت شد")
        
        # تست عملکردی
        svc = get_service()
        stats = svc.get_statistics()
        print(f"   ✅ آمار: {stats.get('total_crops', 0)} گونه کارشناسی")
        
        # تست جستجو
        results = svc.search_species("گندم")
        print(f"   ✅ جستجوی 'گندم': {len(results)} نتیجه")
        
        # تست شبیه‌سازی
        sim = AquaCropSimulator()
        result = sim.run("W001", "SITE037", "rainfed")
        print(f"   ✅ شبیه‌سازی گندم دوروم @ SITE037:")
        print(f"      عملکرد: {result.yield_t_ha:.2f} تن/هکتار")
        print(f"      بیوماس: {result.biomass_t_ha:.2f} تن/هکتار")
        print(f"      روزهای تنش: {result.water_stress_days}")
        print(f"      اطمینان: {result.confidence}")
        
        # تست مقایسه سناریوهای آبیاری
        scenarios = sim.compare_irrigation_scenarios("W001", "SITE037")
        if "analysis" in scenarios:
            analysis = scenarios["analysis"]
            print(f"   ✅ مقایسه آبیاری: افزایش عملکرد {analysis.get('yield_increase_percent', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 اصلاح خطای NameError در type hint کلاس‌های خود-ارجاع")
    print("="*70)
    
    # اصلاح فایل‌ها
    fix_self_referencing_types(CROP_DB)
    fix_self_referencing_types(AQUACROP)
    
    # بررسی سینتکس
    print("\n📋 بررسی سینتکس:")
    ok1 = verify_syntax(CROP_DB)
    ok2 = verify_syntax(AQUACROP)
    
    if not (ok1 and ok2):
        print("\n❌ خطای سینتکس باقی مانده است")
        return
    
    # تست ایمپورت
    print("\n🧪 تست ایمپورت و عملکرد:")
    success = test_import()
    
    if success:
        print("\n" + "="*70)
        print("🎉 اصلاح با موفقیت کامل اعمال شد!")
        print("📋 گام بعدی: اجرای کامل تست اتصال")
        print("   python connect_indices_to_motors.py")
        print("="*70)
    else:
        print("\n⚠️ برخی تست‌ها ناموفق بودند")

if __name__ == "__main__":
    main()