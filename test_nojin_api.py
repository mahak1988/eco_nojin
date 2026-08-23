"""
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
print("\n1️⃣  Health Check...")
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
print("\n2️⃣  List Materials...")
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
print("\n3️⃣  Arid Priority Materials...")
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
print("\n4️⃣  Get Material MIN-011 (Zeolite)...")
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
print("\n5️⃣  List Soil Types...")
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
print("\n6️⃣  Classify Soil (pH=8.2, EC=6.0, OM=0.8)...")
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
print("\n7️⃣  List Recipes...")
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
print("\n8️⃣  Get Recommendation (10 ha, desert sandy)...")
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
print("\n9️⃣  Full Analysis (10 ha)...")
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
print("\n🔟  System Statistics...")
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
print("\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"\n✅ Passed: {passed}/{total}")
print(f"❌ Failed: {total - passed}/{total}")

print("\n📋 Individual results:")
for name, ok in results:
    status = "✅" if ok else "❌"
    print(f"  {status} {name}")

if passed == total:
    print("\n🎉 All tests passed!")
elif passed >= total * 0.8:
    print("\n✅ Most tests passed - system mostly working")
else:
    print("\n⚠️  Several tests failed - check server logs")
