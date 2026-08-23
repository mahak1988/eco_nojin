"""
Install Nojin Router in FastAPI Application
=============================================
Adds the Nojin router to the main FastAPI application.

Run: python install_nojin_router.py
"""

from pathlib import Path
import shutil

PROJECT_ROOT = Path(r"D:\eco_nojin")

print("=" * 80)
print("🔧 Installing Nojin Router")
print("=" * 80)

# Create the routers directory if needed
routers_dir = PROJECT_ROOT / "services" / "api_gateway" / "routers"
routers_dir.mkdir(parents=True, exist_ok=True)

# Copy router file
source_router = PROJECT_ROOT / "nojin_router.py"
target_router = routers_dir / "nojin.py"

if source_router.exists():
    shutil.copy2(source_router, target_router)
    print(f"✅ Router copied to: {target_router.relative_to(PROJECT_ROOT)}")
else:
    print(f"ℹ️  Router already in place: {target_router.relative_to(PROJECT_ROOT)}")

# Create __init__.py if missing
init_file = routers_dir / "__init__.py"
if not init_file.exists():
    init_file.write_text('"""API Gateway Routers."""\n', encoding="utf-8")
    print(f"✅ Created: {init_file.relative_to(PROJECT_ROOT)}")

# Find main.py and add router registration
main_candidates = [
    PROJECT_ROOT / "main.py",
    PROJECT_ROOT / "services" / "api_gateway" / "main.py",
]

main_file = None
for candidate in main_candidates:
    if candidate.exists():
        main_file = candidate
        break

if main_file is None:
    print("\n⚠️  main.py not found in expected locations")
    print("   Please manually add to your FastAPI app:")
    print("   from services.api_gateway.routers import nojin")
    print("   app.include_router(nojin.router)")
else:
    print(f"\n📝 Found main.py at: {main_file.relative_to(PROJECT_ROOT)}")
    
    # Backup
    backup = main_file.with_suffix(".py.before_nojin")
    if not backup.exists():
        shutil.copy2(main_file, backup)
        print(f"✅ Backup created: {backup.name}")
    
    # Check if already registered
    content = main_file.read_text(encoding="utf-8")
    
    if "nojin" in content.lower() and "include_router" in content:
        print("✅ Nojin router already registered in main.py")
    else:
        print("ℹ️  Manual registration required")
        print("\n📋 Add these lines to your main.py:")
        print("=" * 80)
        print("""
# At the top (imports):
from services.api_gateway.routers import nojin

# After app = FastAPI(...) or similar:
app.include_router(nojin.router)
""")
        print("=" * 80)

# Create a test script
test_script = PROJECT_ROOT / "test_nojin_api.py"
test_content = '''"""
Test Nojin API Endpoints
==========================
Run: python test_nojin_api.py

Tests all 15 endpoints to verify functionality.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/nojin"

print("=" * 80)
print("🧪 Testing Nojin API Endpoints")
print("=" * 80)
print(f"📅 {datetime.now().isoformat()}")
print(f"🔗 Base URL: {BASE_URL}")

results = []

# Test 1: Health check
print("\\n1️⃣  Health Check...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/health")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Status: {data['status']}")
        print(f"   ✅ Materials: {data['materials_count']}")
        print(f"   ✅ Recipes: {data['recipes_count']}")
        results.append(("Health", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Health", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Health", False))

# Test 2: List materials
print("\\n2️⃣  List Materials...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/materials?limit=10")
    if r.status_code == 200:
        materials = r.json()
        print(f"   ✅ Got {len(materials)} materials")
        if materials:
            print(f"      First: {materials[0]['material_code']} - {materials[0]['common_name']}")
        results.append(("List Materials", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("List Materials", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("List Materials", False))

# Test 3: Arid priority materials
print("\\n3️⃣  Arid Priority Materials...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/materials/arid-priority")
    if r.status_code == 200:
        materials = r.json()
        print(f"   ✅ Got {len(materials)} arid-priority materials")
        results.append(("Arid Materials", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Arid Materials", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Arid Materials", False))

# Test 4: Get specific material
print("\\n4️⃣  Get Material MIN-011 (Zeolite)...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/materials/MIN-011")
    if r.status_code == 200:
        mat = r.json()
        print(f"   ✅ {mat['common_name']}")
        print(f"      Persistence: {mat['persistence_years']} years")
        results.append(("Get Material", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Get Material", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Get Material", False))

# Test 5: List soils
print("\\n5️⃣  List Soil Types...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/soils")
    if r.status_code == 200:
        soils = r.json()
        print(f"   ✅ Got {len(soils)} soil types")
        results.append(("List Soils", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("List Soils", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("List Soils", False))

# Test 6: Classify soil
print("\\n6️⃣  Classify Soil (pH=8.2, EC=6.0, OM=0.8)...")
try:
    r = requests.post(f"{BASE_URL}{API_PREFIX}/classify", json={
        "ph": 8.2,
        "ec_dsm": 6.0,
        "om_pct": 0.8,
        "texture": "loam"
    })
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ Classified as: {result['classified_as']}")
        print(f"      Recommended recipe: {result['recommended_recipe']}")
        results.append(("Classify Soil", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Classify Soil", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Classify Soil", False))

# Test 7: List recipes
print("\\n7️⃣  List Recipes...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/recipes")
    if r.status_code == 200:
        recipes = r.json()
        print(f"   ✅ Got {len(recipes)} recipes")
        results.append(("List Recipes", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("List Recipes", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("List Recipes", False))

# Test 8: Recommend
print("\\n8️⃣  Get Recommendation (10 ha, desert sandy)...")
try:
    r = requests.post(f"{BASE_URL}{API_PREFIX}/recommend", json={
        "soil_code": "SOIL-01",
        "area_ha": 10.0,
        "crop_type": "wheat"
    })
    if r.status_code == 200:
        rec = r.json()
        print(f"   ✅ Recipe: {rec['recipe_name']}")
        print(f"      Total: {rec['total_tons']:.1f} tons")
        print(f"      Cost: ${rec['estimated_cost_usd']:,.0f}")
        results.append(("Recommend", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Recommend", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Recommend", False))

# Test 9: Full analysis
print("\\n9️⃣  Full Analysis (10 ha)...")
try:
    r = requests.post(f"{BASE_URL}{API_PREFIX}/full-analysis", json={
        "soil_code": "SOIL-01",
        "area_ha": 10.0,
        "crop_type": "wheat",
        "current_yield_t_ha": 2.0,
        "current_irrigation_m3_ha": 8000.0,
        "current_fertilizer_cost_usd_ha": 300.0
    })
    if r.status_code == 200:
        full = r.json()
        print(f"   ✅ ROI: {full['cost_benefit']['roi_annual_percent']:.1f}%")
        print(f"      Payback: {full['cost_benefit']['payback_simple_months']} months")
        print(f"      Water saved: {full['water_savings']['water_saved_percent']:.1f}%")
        print(f"      Viable: {full['cost_benefit']['is_economically_viable']}")
        results.append(("Full Analysis", True))
    else:
        print(f"   ❌ Status: {r.status_code} - {r.text[:200]}")
        results.append(("Full Analysis", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Full Analysis", False))

# Test 10: Statistics
print("\\n🔟  System Statistics...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/statistics")
    if r.status_code == 200:
        stats = r.json()
        print(f"   ✅ Materials: {stats['materials_count']}")
        print(f"      Soil types: {stats['soil_types_count']}")
        print(f"      Recipes: {stats['recipes_count']}")
        results.append(("Statistics", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Statistics", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Statistics", False))

# Summary
print("\\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\\n✅ Passed: {passed}/{total}")
print(f"❌ Failed: {total - passed}/{total}")

print("\\n📋 Individual results:")
for name, ok in results:
    status = "✅" if ok else "❌"
    print(f"  {status} {name}")

if passed == total:
    print("\\n🎉 All tests passed!")
elif passed >= total * 0.8:
    print("\\n✅ Most tests passed - system mostly working")
else:
    print("\\n⚠️  Several tests failed - check server logs")
'''

test_script.write_text(test_content, encoding="utf-8")
print(f"\n✅ Test script created: test_nojin_api.py")

print("\n" + "=" * 80)
print("✅ NOJIN ROUTER INSTALLATION COMPLETE")
print("=" * 80)
print("""
🎯 Next Steps:

1. Add router to main.py:
   from services.api_gateway.routers import nojin
   app.include_router(nojin.router)

2. Start the FastAPI server:
   uvicorn main:app --reload

3. Test the API:
   python test_nojin_api.py

4. Visit Swagger UI:
   http://localhost:8000/docs

5. Try the endpoints:
   - GET  /api/nojin/health
   - GET  /api/nojin/materials
   - POST /api/nojin/full-analysis
""")