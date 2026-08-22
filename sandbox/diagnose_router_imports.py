"""
Router Import Diagnoser
هدف: تست import هر روتر به صورت جداگانه برای یافتن روتر crash کننده
"""
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

ROUTERS = [
    "services.api_gateway.routers.ai",
    "services.api_gateway.routers.ai_chat",
    "services.api_gateway.routers.analytics",
    "services.api_gateway.routers.auth",
    "services.api_gateway.routers.benchmark",
    "services.api_gateway.routers.blockchain",
    "services.api_gateway.routers.carbon",
    "services.api_gateway.routers.carbon_engine",
    "services.api_gateway.routers.ecowallet",
    "services.api_gateway.routers.farms",
    "services.api_gateway.routers.marketplace",
    "services.api_gateway.routers.materials",
    "services.api_gateway.routers.satellite",
    "services.api_gateway.routers.scenarios",
    "services.api_gateway.routers.soil",
    "services.api_gateway.routers.sync",
    "services.api_gateway.routers.ussd",
    "services.api_gateway.routers.voice",
    "services.api_gateway.routers.watershed",
    "services.api_gateway.routers.platform",
]

def diagnose():
    print("🔍 تست import روترها به صورت انفرادی:\n")
    failed_routers = []
    
    for router_path in ROUTERS:
        try:
            __import__(router_path)
            print(f"✅ {router_path}")
        except Exception as e:
            print(f"❌ {router_path}")
            print(f"   خطا: {type(e).__name__}: {e}")
            failed_routers.append((router_path, e))
    
    print("\n" + "="*80)
    if failed_routers:
        print(f"❌ {len(failed_routers)} روتر با خطا مواجه شدند:")
        for router, error in failed_routers:
            print(f"\n🔴 {router}:")
            traceback.print_exception(type(error), error, error.__traceback__)
    else:
        print("✅ تمام روترها با موفقیت import شدند.")

if __name__ == "__main__":
    diagnose()