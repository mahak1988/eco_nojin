"""
Route 404 Diagnoser
هدف: نمایش تمام مسیرهای ثبت‌شده در FastAPI برای ریشه‌یابی خطاهای 404
"""
import sys
from pathlib import Path

# اضافه کردن مسیر پروژه به sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

def diagnose():
    print("🔍 در حال بارگذاری FastAPI app...")
    try:
        from services.api_gateway.main import app
        
        print("\n📋 لیست کامل مسیرهای ثبت‌شده:\n")
        print(f"{'مسیر':<60} | {'متدها':<20} | {'نام'}")
        print("-" * 100)
        
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                methods = ", ".join(route.methods) if route.methods else "GET"
                name = getattr(route, "name", "unknown")
                print(f"{route.path:<60} | {methods:<20} | {name}")
        
        print("\n" + "="*100)
        print("💡 راهنما: اگر مسیرهای blockchain, ecowallet, ussd در لیست بالا نیستند، مشکل در register شدن است.")
        print("💡 اگر هستند ولی تست 404 می‌گیرد، مشکل در تست‌ها است (احتمالاً prefix اشتباه می‌زنند).")
        
    except Exception as e:
        print(f"❌ خطا در بارگذاری app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()