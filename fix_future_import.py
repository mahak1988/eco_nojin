#!/usr/bin/env python3
"""
اسکریپت اصلاح خطای from __future__ در وسط فایل
حذف تمام تکرارهای from __future__ به جز اولین
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.resolve()
CROP_DB = PROJECT_ROOT / "services" / "scientific_motors" / "crop_database.py"
AQUACROP = PROJECT_ROOT / "services" / "scientific_motors" / "aquacrop_real.py"

def fix_future_imports(filepath: Path) -> bool:
    """حذف تکرارهای from __future__ به جز اولین"""
    if not filepath.exists():
        print(f"❌ فایل یافت نشد: {filepath}")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # پیدا کردن تمام خطوط from __future__
    future_indices = []
    for i, line in enumerate(lines):
        if line.strip().startswith('from __future__'):
            future_indices.append(i)
    
    if len(future_indices) <= 1:
        print(f"   ℹ️ {filepath.name}: نیازی به اصلاح نیست")
        return True
    
    # حذف تمام به جز اولین
    indices_to_remove = set(future_indices[1:])
    new_lines = [line for i, line in enumerate(lines) if i not in indices_to_remove]
    
    # بررسی اینکه اولین from __future__ در ابتدای فایل باشد
    # اگر نیست، آن را به ابتدای فایل منتقل کن
    first_future_idx = future_indices[0]
    if first_future_idx > 5:  # اگر بعد از خط ۵ باشد، احتمالاً در وسط فایل است
        # حذف از موقعیت فعلی
        future_line = new_lines[first_future_idx]
        new_lines.pop(first_future_idx)
        
        # پیدا کردن اولین خط غیر خالی و غیر کامنت
        insert_pos = 0
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                insert_pos = i
                break
        
        new_lines.insert(insert_pos, future_line)
        print(f"   ✅ {filepath.name}: {len(future_indices)-1} تکرار حذف + به ابتدا منتقل شد")
    else:
        print(f"   ✅ {filepath.name}: {len(future_indices)-1} تکرار حذف شد")
    
    # نوشتن فایل
    filepath.write_text('\n'.join(new_lines), encoding="utf-8")
    return True

def verify_syntax(filepath: Path) -> bool:
    """بررسی سینتکس فایل"""
    try:
        content = filepath.read_text(encoding="utf-8")
        compile(content, filepath.name, "exec")
        print(f"   ✅ {filepath.name}: سینتکس معتبر است")
        return True
    except SyntaxError as e:
        print(f"   ❌ {filepath.name}: خطای سینتکس: {e}")
        return False

def test_import():
    """تست ایمپورت ماژول‌ها"""
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
        print(f"   ✅ شبیه‌سازی گندم دوروم:")
        print(f"      عملکرد: {result.yield_t_ha:.2f} تن/هکتار")
        print(f"      بیوماس: {result.biomass_t_ha:.2f} تن/هکتار")
        print(f"      روزهای تنش: {result.water_stress_days}")
        print(f"      اطمینان: {result.confidence}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 اصلاح خطای from __future__ در فایل‌های بازنویسی شده")
    print("="*70)
    
    # اصلاح فایل‌ها
    fix_future_imports(CROP_DB)
    fix_future_imports(AQUACROP)
    
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