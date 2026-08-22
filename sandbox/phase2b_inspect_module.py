"""
Phase 2b: Inspect hydroma_core module
هدف: لیست کردن توابع موجود در ماژول C++ برای اتصال به bridge‌ها
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CPP_BRIDGE = PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge"

# افزودن مسیر bridge به sys.path برای import
sys.path.insert(0, str(CPP_BRIDGE))

def inspect_module():
    print("🔬 تست import کردن 'hydroma_core' از مسیر bridge\n")
    
    try:
        import hydroma_core
        print(f"✅ ماژول با موفقیت import شد!")
        print(f"📦 مسیر ماژول: {hydroma_core.__file__}\n")
        
        print("=" * 70)
        print("📋 لیست توابع و کلاس‌های موجود در hydroma_core")
        print("=" * 70)
        
        # گروه‌بندی بر اساس نوع
        functions = []
        classes = []
        constants = []
        
        for attr in sorted(dir(hydroma_core)):
            if attr.startswith("_"):
                continue
            
            obj = getattr(hydroma_core, attr)
            obj_type = type(obj).__name__
            
            if callable(obj) and not isinstance(obj, type):
                functions.append((attr, obj))
            elif isinstance(obj, type):
                classes.append((attr, obj))
            else:
                constants.append((attr, obj))
        
        print(f"\n🔧 توابع ({len(functions)}):")
        for name, func in functions:
            try:
                doc = func.__doc__ or "بدون مستندات"
                doc_line = doc.split('\n')[0][:80]
                print(f"   ✓ {name}")
                print(f"     {doc_line}")
            except:
                print(f"   ✓ {name}")
        
        print(f"\n📦 کلاس‌ها ({len(classes)}):")
        for name, cls in classes:
            print(f"   ✓ {name}")
        
        print(f"\n🔢 ثابت‌ها ({len(constants)}):")
        for name, val in constants:
            print(f"   ✓ {name} = {val}")
        
        return hydroma_core, functions, classes
        
    except Exception as e:
        print(f"❌ خطا در import: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None, [], []

def check_bridge_files():
    """بررسی محتوای bridge‌های فعلی برای فهمیدن API مورد انتظار"""
    print("\n" + "=" * 70)
    print("📄 بررسی bridge‌های فعلی برای فهمیدن API مورد انتظار")
    print("=" * 70)
    
    bridge_files = [
        CPP_BRIDGE / "soil_physics_fast.py",
        CPP_BRIDGE / "hydrology_fast.py",
        CPP_BRIDGE / "indices_fast.py",
    ]
    
    for bf in bridge_files:
        if not bf.exists():
            continue
        
        print(f"\n📄 {bf.name}")
        content = bf.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        # استخراج توابع
        funcs = [line.strip() for line in lines if line.strip().startswith("def ")]
        print(f"   توابع ({len(funcs)}):")
        for f in funcs[:5]:
            print(f"      {f}")
        if len(funcs) > 5:
            print(f"      ... و {len(funcs) - 5} تابع دیگر")

if __name__ == "__main__":
    mod, funcs, classes = inspect_module()
    check_bridge_files()
    
    if mod:
        print("\n" + "=" * 70)
        print("📊 جمع‌بندی و گام بعدی")
        print("=" * 70)
        print(f"\n✅ ماژول C++ آماده استفاده است.")
        print(f"   تعداد توابع: {len(funcs)}")
        print(f"   تعداد کلاس‌ها: {len(classes)}")
        print(f"\n💡 گام بعدی:")
        print(f"   نوشتن اسکریپت اتصال bridge‌ها به hydroma_core")