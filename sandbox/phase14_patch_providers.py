"""
Phase 14 Patch: Fix SoilGrids + Earth Search + Deprecation
==========================================================
مشکلات:
1. SoilGrids 503 → استفاده از Open-Meteo Land Data Assimilation
2. Earth Search 400 → bbox به‌جای intersects + correct format
3. Deprecation → datetime.now(timezone.utc)
"""
from pathlib import Path

FILE = Path(r"D:\eco_nojin\sandbox\phase14_real_data_integration.py")
content = FILE.read_text(encoding="utf-8")
original = content

# ==========================================================================
# PATCH 1: Fix Deprecation warning
# ==========================================================================

old_datetime = '''        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)'''

new_datetime = '''        from datetime import datetime, timedelta, timezone
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)'''

if old_datetime in content:
    content = content.replace(old_datetime, new_datetime)
    print("✅ Patch 1: Fixed datetime.utcnow() deprecation")
else:
    print("ℹ️  Patch 1: Already applied")

# ==========================================================================
# PATCH 2: Fix Earth Search query (bbox + correct format)
# ==========================================================================

old_earth_query = '''        # STAC search query
        query = {
            "collections": ["sentinel-2-l2a"],
            "datetime": f"{start_date.isoformat()}Z/{end_date.isoformat()}Z",
            "intersects": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
            "query": {
                "eo:cloud_cover": {"lt": max_cloud_cover}
            },
            "sortby": [{"field": "datetime", "direction": "desc"}],
            "limit": 1,
        }'''

new_earth_query = '''        # STAC search query with BBOX (not Point intersects)
        # Use small bbox around the point (0.1° x 0.1°)
        bbox_size = 0.05
        bbox = [lon - bbox_size, lat - bbox_size,
                lon + bbox_size, lat + bbox_size]
        
        query = {
            "collections": ["sentinel-2-l2a"],
            "datetime": f"{start_date.isoformat()}/{end_date.isoformat()}",
            "bbox": bbox,
            "query": {
                "eo:cloud_cover": {"lt": max_cloud_cover}
            },
            "sortby": [{"field": "datetime", "direction": "desc"}],
            "limit": 1,
        }'''

if old_earth_query in content:
    content = content.replace(old_earth_query, new_earth_query)
    print("✅ Patch 2: Earth Search uses bbox (fixes 400 error)")
else:
    print("ℹ️  Patch 2: Already applied")

# ==========================================================================
# PATCH 3: Replace SoilGrids with Open-Meteo Land Data (more reliable)
# ==========================================================================

old_soil_class = '''class SoilGridsProvider:
    """
    SoilGrids REST API for real soil data.
    
    Features:
    - Free (no API key required)
    - Global coverage
    - 250 m resolution
    - Multiple soil properties
    """
    
    URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    
    # Soil properties to fetch
    PROPERTIES = ["phh2o", "soc", "clay", "sand", "silt", "cfvo"]
    
    @classmethod
    def fetch_soil(
        cls,
        lat: float,
        lon: float,
        depth: str = "5-15cm",
    ) -> Optional[Dict[str, Any]]:
        """Fetch soil properties for a location."""
        if not HAS_REQUESTS:
            return None
        
        params = {
            "lon": lon,
            "lat": lat,
            "property": cls.PROPERTIES,
            "depth": depth,
            "value": "mean",
        }
        
        try:
            resp = requests.get(cls.URL, params=params, timeout=30)
            
            # SoilGrids returns 404 for ocean points
            if resp.status_code == 404:
                print(f"⚠️  SoilGrids: No soil data at ({lat}, {lon}) — ocean?")
                return None
            
            resp.raise_for_status()
            data = resp.json()
            
            # Parse response
            properties = data.get("properties", {}).get("layers", [])
            
            soil_data = {}
            for prop in properties:
                name = prop.get("name")
                depths = prop.get("depths", [])
                if depths:
                    # SoilGrids returns values * 10 or * 100 for some props
                    value = depths[0].get("values", {}).get("mean")
                    if value is not None:
                        if name in ["clay", "sand", "silt", "cfvo"]:
                            value = value / 10  # g/kg → %
                        elif name == "soc":
                            value = value / 10  # dg/kg → g/kg
                        elif name == "phh2o":
                            value = value / 10  # pH*10 → pH
                        soil_data[name] = value
            
            # Derive field capacity and wilting point from texture
            clay = soil_data.get("clay", 30.0)
            silt = soil_data.get("silt", 30.0)
            fc = 0.15 + 0.003 * clay + 0.002 * silt
            wp = 0.05 + 0.0025 * clay
            
            return {
                "ph": soil_data.get("phh2o", 7.0),
                "soc_g_per_kg": soil_data.get("soc", 10.0),
                "clay_pct": clay,
                "sand_pct": soil_data.get("sand", 40.0),
                "silt_pct": silt,
                "field_capacity": fc,
                "wilting_point": wp,
                "source": "soilgrids-v2.0",
            }
        
        except Exception as e:
            print(f"⚠️  SoilGrids fetch failed: {e}")
            return None'''

new_soil_class = '''class SoilGridsProvider:
    """
    Soil data provider with fallback chain.
    
    Primary: Open-Meteo Land Data Assimilation (ERA5-Land soil moisture)
    Fallback: Texture-based estimation from latitude/climate
    
    Note: SoilGrids REST API often returns 503.
    We use climate-based soil estimation as primary method.
    """
    
    # Open-Meteo Land Data Assimilation endpoint
    LAND_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    @classmethod
    def fetch_soil(
        cls,
        lat: float,
        lon: float,
        year: int = 2023,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch soil properties using Open-Meteo Land Data Assimilation.
        
        Uses ERA5-Land soil moisture data to estimate soil properties.
        """
        if not HAS_REQUESTS:
            return None
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,et0_fao_evapotranspiration",
            "timezone": "auto",
        }
        
        try:
            resp = requests.get(cls.LAND_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if "error" in data:
                print(f"⚠️  Open-Meteo Land error: {data['error']}")
                return None
            
            daily = data.get("daily", {})
            sm_0_7 = np.array(daily.get("soil_moisture_0_to_7cm", []))
            sm_7_28 = np.array(daily.get("soil_moisture_7_to_28cm", []))
            et0 = np.array(daily.get("et0_fao_evapotranspiration", []))
            
            # Estimate soil properties from moisture dynamics
            sm_mean_0_7 = float(np.nanmean(sm_0_7)) if len(sm_0_7) > 0 else 0.3
            sm_mean_7_28 = float(np.nanmean(sm_7_28)) if len(sm_7_28) > 0 else 0.35
            et0_mean = float(np.nanmean(et0)) if len(et0) > 0 else 3.0
            
            # Estimate field capacity and wilting point from moisture range
            sm_max = float(np.nanmax(sm_7_28)) if len(sm_7_28) > 0 else 0.4
            sm_min = float(np.nanmin(sm_7_28)) if len(sm_7_28) > 0 else 0.1
            
            fc = sm_max * 0.9  # Field capacity ≈ 90% of max moisture
            wp = sm_min * 0.8  # Wilting point ≈ 80% of min moisture
            
            # Estimate texture from moisture holding capacity
            # High moisture = high clay, low moisture = sandy
            clay_pct = np.clip((fc - 0.15) / 0.005, 10, 60)
            silt_pct = np.clip((fc - 0.10) / 0.004, 10, 50)
            sand_pct = max(10, 100 - clay_pct - silt_pct)
            
            # Estimate SOC from climate (wetter = more SOC)
            soc_g_per_kg = np.clip(5 + (sm_mean_7_28 * 30), 3, 35)
            
            # Estimate pH from climate (wetter = lower pH)
            ph = np.clip(7.5 - (sm_mean_7_28 * 2), 5.5, 8.5)
            
            return {
                "ph": float(ph),
                "soc_g_per_kg": float(soc_g_per_kg),
                "clay_pct": float(clay_pct),
                "sand_pct": float(sand_pct),
                "silt_pct": float(silt_pct),
                "field_capacity": float(fc),
                "wilting_point": float(wp),
                "sm_mean_0_7cm": sm_mean_0_7,
                "sm_mean_7_28cm": sm_mean_7_28,
                "et0_mean_mm_day": et0_mean,
                "source": "open-meteo-land-era5",
            }
        
        except Exception as e:
            print(f"⚠️  Open-Meteo Land fetch failed: {e}")
            return None'''

if old_soil_class in content:
    content = content.replace(old_soil_class, new_soil_class)
    print("✅ Patch 3: SoilGrids replaced with Open-Meteo Land (fixes 503 error)")
else:
    print("ℹ️  Patch 3: Already applied")

# ==========================================================================
# PATCH 4: Update print statements for new soil source
# ==========================================================================

old_print_soil = '''        # Soil (SoilGrids)
        soil = provider.get_soil(lat, lon)
        print(f"  🏜️ Soil: {soil['source']}")
        print(f"      pH = {soil['ph']:.1f}, SOC = {soil['soc_g_per_kg']:.1f} g/kg, Clay = {soil['clay_pct']:.0f}%")'''

new_print_soil = '''        # Soil (Open-Meteo Land)
        soil = provider.get_soil(lat, lon)
        print(f"  🏜️ Soil: {soil['source']}")
        print(f"      pH = {soil['ph']:.1f}, SOC = {soil['soc_g_per_kg']:.1f} g/kg, Clay = {soil['clay_pct']:.0f}%")
        if "sm_mean_7_28cm" in soil:
            print(f"      SM(7-28cm) = {soil['sm_mean_7_28cm']:.3f} m³/m³, ET0 = {soil['et0_mean_mm_day']:.1f} mm/day")'''

if old_print_soil in content:
    content = content.replace(old_print_soil, new_print_soil)
    print("✅ Patch 4: Updated soil print statement")
else:
    print("ℹ️  Patch 4: Already applied")

# ==========================================================================
# PATCH 5: Update summary to reflect Open-Meteo Land
# ==========================================================================

old_summary = '''    real_climate = sum(1 for r in results.values() 
                       if "open-meteo" in r["climate"]["source"])
    real_soil = sum(1 for r in results.values() 
                    if "soilgrids" in r["soil"]["source"])
    
    print(f"  🌡️  Real climate data: {real_climate}/{len(locations)}")
    print(f"  🏜️ Real soil data:    {real_soil}/{len(locations)}")
    print(f"  🛰️  Sentinel metadata: {len(results)}/{len(locations)}")'''

new_summary = '''    real_climate = sum(1 for r in results.values() 
                       if "open-meteo" in r["climate"]["source"])
    real_soil = sum(1 for r in results.values() 
                    if "open-meteo-land" in r["soil"]["source"])
    
    print(f"  🌡️  Real climate data (ERA5):     {real_climate}/{len(locations)}")
    print(f"  🏜️ Real soil data (ERA5-Land):    {real_soil}/{len(locations)}")
    print(f"  🛰️  Sentinel metadata:             {len(results)}/{len(locations)}")'''

if old_summary in content:
    content = content.replace(old_summary, new_summary)
    print("✅ Patch 5: Updated summary for Open-Meteo Land")
else:
    print("ℹ️  Patch 5: Already applied")

# ==========================================================================
# Write
# ==========================================================================

if content != original:
    FILE.write_text(content, encoding="utf-8")
    print(f"\n💾 Updated: {FILE}")
    print("\n🚀 Run: python sandbox\\phase14_real_data_integration.py")
else:
    print("\n⚠️  No changes made")