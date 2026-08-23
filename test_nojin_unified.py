"""
Test Nojin API on Unified Server (Port 8000)
==============================================
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/nojin"

print("=" * 80)
print("🧪 Testing Nojin API on UNIFIED Server (Port 8000)")
print("=" * 80)
print(f"📅 {datetime.now().isoformat()}")
print(f"🔗 Base URL: {BASE_URL}")
print(f"📚 Swagger UI: {BASE_URL}/docs")

results = []

# Test 1: Health
print("\n1️⃣  Health Check...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Status: {data['status']}")
        print(f"   ✅ Materials: {data['materials_count']}")
        results.append(("Health", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Health", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Health", False))

# Test 2: Materials
print("\n2️⃣  List Materials...")
try:
    r = requests.get(f"{BASE_URL}{API_PREFIX}/materials?limit=5", timeout=5)
    if r.status_code == 200:
        materials = r.json()
        print(f"   ✅ Got {len(materials)} materials")
        results.append(("Materials", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Materials", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Materials", False))

# Test 3: Classify (THE BUG WE FIXED)
print("\n3️⃣  Classify Soil (BUG FIX TEST)...")
try:
    r = requests.post(f"{BASE_URL}{API_PREFIX}/classify", json={
        "ph": 8.2,
        "ec_dsm": 6.0,
        "om_pct": 0.8,
    }, timeout=5)
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ Classified as: {result['classified_as']}")
        print(f"      Recipe: {result['recommended_recipe']}")
        results.append(("Classify ⭐", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        print(f"      Response: {r.text[:200]}")
        results.append(("Classify ⭐", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Classify ⭐", False))

# Test 4: Recommend
print("\n4️⃣  Get Recommendation...")
try:
    r = requests.post(f"{BASE_URL}{API_PREFIX}/recommend", json={
        "soil_code": "SOIL-01",
        "area_ha": 10.0,
        "crop_type": "wheat",
    }, timeout=5)
    if r.status_code == 200:
        rec = r.json()
        print(f"   ✅ Recipe: {rec['recipe_name']}")
        print(f"      Cost: ${rec['estimated_cost_usd']:,.0f}")
        results.append(("Recommend", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Recommend", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Recommend", False))

# Test 5: Full Analysis
print("\n5️⃣  Full Analysis (10 ha)...")
try:
    r = requests.post(f"{BASE_URL}{API_PREFIX}/full-analysis", json={
        "soil_code": "SOIL-01",
        "area_ha": 10.0,
        "crop_type": "wheat",
        "current_yield_t_ha": 2.0,
        "current_irrigation_m3_ha": 8000.0,
        "current_fertilizer_cost_usd_ha": 300.0,
    }, timeout=10)
    if r.status_code == 200:
        full = r.json()
        cb = full['cost_benefit']
        print(f"   ✅ ROI: {cb['roi_annual_percent']:.1f}%")
        print(f"      Payback: {cb['payback_simple_months']} months")
        print(f"      NPV: ${cb['npv_10year_usd']:,.0f}")
        print(f"      Water saved: {full['water_savings']['water_saved_percent']:.1f}%")
        print(f"      Viable: {cb['is_economically_viable']}")
        results.append(("Full Analysis", True))
    else:
        print(f"   ❌ Status: {r.status_code}")
        results.append(("Full Analysis", False))
except Exception as e:
    print(f"   ❌ Error: {e}")
    results.append(("Full Analysis", False))

# Summary
print("\n" + "=" * 80)
print("📊 TEST SUMMARY - UNIFIED SERVER")
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
    print("\n🎉 ALL TESTS PASSED ON UNIFIED SERVER!")
    print("   Frontend can now use single base URL: http://localhost:8000")
    print("   No more CORS issues or port conflicts!")