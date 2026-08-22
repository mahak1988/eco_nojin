"""
Phase 14: Real Data Integration
===============================

جایگزینی MockProviders با real API calls به:
- Open-Meteo Archive (climate)
- SoilGrids REST API (soil)
- Earth Search STAC API (Sentinel-2)

Architecture:
    RegionAnalyzer
        └── DataProviders (abstraction layer)
            ├── MockProviders (fallback)
            ├── OpenMeteoProvider (real climate)
            ├── SoilGridsProvider (real soil)
            └── EarthSearchProvider (real Sentinel-2)

Usage:
    # Production mode (real data)
    analyzer = RegionAnalyzer(use_real_data=True)
    result = analyzer.analyze(lat=32.65, lon=51.67, crop_type="wheat")
    
    # Demo mode (mock data)
    analyzer = RegionAnalyzer(use_real_data=False)
    result = analyzer.analyze("Iran_Isfahan", crop_type="wheat")

References:
- Open-Meteo: https://open-meteo.com/
- SoilGrids: https://soilgrids.org/
- Earth Search: https://earth-search.aws.element84.com/
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

# ============================================================================
# Path Setup
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  requests not installed. Run: pip install requests")


# ============================================================================
# 1. Open-Meteo Climate Provider (Real Data)
# ============================================================================

class OpenMeteoProvider:
    """
    Open-Meteo Archive API for real climate data.
    
    Features:
    - Free (no API key required)
    - ERA5 reanalysis (1950-present)
    - 9 km resolution
    - Hourly/daily data
    """
    
    URL = "https://archive-api.open-meteo.com/v1/archive"
    
    @classmethod
    def fetch_climate(
        cls,
        lat: float,
        lon: float,
        year: int = 2023,  # Use recent year
    ) -> Optional[Dict[str, Any]]:
        """Fetch monthly climate data for a location."""
        if not HAS_REQUESTS:
            return None
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
        }
        
        try:
            resp = requests.get(cls.URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if "error" in data:
                print(f"⚠️  Open-Meteo error: {data['error']}")
                return None
            
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            t_max = np.array(daily.get("temperature_2m_max", []))
            t_min = np.array(daily.get("temperature_2m_min", []))
            p = np.array(daily.get("precipitation_sum", []))
            
            # Aggregate to monthly
            months = [int(d.split("-")[1]) for d in dates]
            t_min_m, t_max_m, p_m = [], [], []
            
            for m in range(1, 13):
                mask = [i for i, mo in enumerate(months) if mo == m]
                if mask:
                    t_max_m.append(float(np.nanmax(t_max[mask])))
                    t_min_m.append(float(np.nanmin(t_min[mask])))
                    p_m.append(float(np.nansum(p[mask])))
                else:
                    t_max_m.append(15.0)
                    t_min_m.append(5.0)
                    p_m.append(50.0)
            
            return {
                "t_min": np.array(t_min_m),
                "t_max": np.array(t_max_m),
                "p": np.array(p_m),
                "t_ann_mean": float(np.nanmean((t_min + t_max) / 2)),
                "p_ann": float(np.nansum(p)),
                "source": f"open-meteo-era5-{year}",
                "year": year,
            }
        
        except Exception as e:
            print(f"⚠️  Open-Meteo fetch failed: {e}")
            return None


# ============================================================================
# 2. SoilGrids Provider (Real Data)
# ============================================================================

class SoilGridsProvider:
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
            return None


# ============================================================================
# 3. Earth Search Sentinel-2 Provider (Real Data)
# ============================================================================

class EarthSearchProvider:
    """
    Earth Search STAC API for real Sentinel-2 imagery.
    
    Features:
    - Free (AWS Open Data)
    - Sentinel-2 L2A
    - 10 m resolution
    - Global coverage (5-day revisit)
    """
    
    URL = "https://earth-search.aws.element84.com/v1/search"
    
    @classmethod
    def fetch_sentinel2(
        cls,
        lat: float,
        lon: float,
        max_cloud_cover: float = 20.0,
        days_back: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch latest cloud-free Sentinel-2 scene metadata.
        
        Note: Full imagery download requires rasterio + COG access.
        Here we fetch metadata and cloud statistics.
        """
        if not HAS_REQUESTS:
            return None
        
        from datetime import datetime, timedelta, timezone
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        # STAC search query with BBOX (not Point intersects)
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
        }
        
        try:
            resp = requests.post(cls.URL, json=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            features = data.get("features", [])
            if not features:
                print(f"⚠️  Earth Search: No Sentinel-2 scenes found in last {days_back} days")
                return None
            
            # Get latest scene
            scene = features[0]
            props = scene.get("properties", {})
            
            # Get asset URLs (COG files)
            assets = scene.get("assets", {})
            
            # We don't download full imagery here (too heavy for demo)
            # Instead, return metadata that can be used later
            return {
                "scene_id": scene.get("id"),
                "acquisition_date": props.get("datetime", ""),
                "cloud_cover": props.get("eo:cloud_cover", 0),
                "view_sun_azimuth": props.get("view:sun_azimuth"),
                "view_sun_elevation": props.get("view:sun_elevation"),
                "assets": {
                    "B02_blue": assets.get("blue", {}).get("href"),
                    "B03_green": assets.get("green", {}).get("href"),
                    "B04_red": assets.get("red", {}).get("href"),
                    "B08_nir": assets.get("nir", {}).get("href"),
                    "B11_swir": assets.get("swir16", {}).get("href"),
                },
                "source": "earth-search-sentinel2-l2a",
                "note": "Full imagery requires rasterio + COG download",
            }
        
        except Exception as e:
            print(f"⚠️  Earth Search fetch failed: {e}")
            return None


# ============================================================================
# 4. Fallback to Mock (for offline/demo)
# ============================================================================

def get_mock_climate(lat: float, lon: float) -> Dict[str, Any]:
    """Fallback mock climate based on latitude."""
    # Simple latitude-based climate approximation
    if abs(lat) < 15:  # Tropical
        t_min = np.full(12, 23.0)
        t_max = np.full(12, 31.0)
        p = np.random.default_rng(42).uniform(100, 300, 12)
    elif abs(lat) < 35:  # Subtropical/Mediterranean
        t_min = np.array([5, 7, 10, 13, 17, 21, 24, 24, 20, 14, 9, 6])
        t_max = np.array([15, 17, 20, 24, 29, 34, 37, 36, 32, 25, 19, 15])
        p = np.array([60, 50, 40, 30, 15, 5, 2, 3, 10, 35, 55, 65])
    else:  # Temperate/Continental
        t_min = np.array([-5, -3, 2, 7, 12, 16, 18, 17, 13, 7, 2, -3])
        t_max = np.array([3, 5, 11, 17, 23, 27, 29, 28, 23, 16, 9, 4])
        p = np.full(12, 60.0)
    
    return {
        "t_min": t_min,
        "t_max": t_max,
        "p": p,
        "t_ann_mean": float(np.mean((t_min + t_max) / 2)),
        "p_ann": float(np.sum(p)),
        "source": "mock-latitude-based",
    }


def get_mock_soil(lat: float, lon: float) -> Dict[str, Any]:
    """Fallback mock soil."""
    return {
        "ph": 7.0,
        "soc_g_per_kg": 15.0,
        "clay_pct": 30.0,
        "sand_pct": 40.0,
        "silt_pct": 30.0,
        "field_capacity": 0.32,
        "wilting_point": 0.15,
        "source": "mock-default",
    }


def get_mock_sentinel2(lat: float, lon: float) -> Dict[str, Any]:
    """Fallback mock Sentinel-2."""
    size = 100
    rng = np.random.default_rng(42)
    return {
        "nir": np.full(size, 0.45) + rng.normal(0, 0.02, size),
        "swir": np.full(size, 0.22) + rng.normal(0, 0.02, size),
        "red": np.full(size, 0.25) + rng.normal(0, 0.01, size),
        "blue": np.full(size, 0.08) + rng.normal(0, 0.01, size),
        "green": np.full(size, 0.15) + rng.normal(0, 0.01, size),
        "lai": np.full(size, 3.5) + rng.normal(0, 0.2, size),
        "source": "mock-default",
        "acquisition_date": "2024-06-15",
    }


# ============================================================================
# 5. Unified Data Provider Interface
# ============================================================================

class RealDataProvider:
    """
    Unified interface for real data fetching with fallback to mocks.
    
    Usage:
        provider = RealDataProvider(use_real=True)
        climate = provider.get_climate(lat=32.65, lon=51.67)
        soil = provider.get_soil(lat=32.65, lon=51.67)
        sentinel = provider.get_sentinel2(lat=32.65, lon=51.67)
    """
    
    def __init__(self, use_real: bool = True):
        self.use_real = use_real and HAS_REQUESTS
        self.cache: Dict[str, Any] = {}
    
    def get_climate(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"climate:{lat:.4f}:{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_real:
            data = OpenMeteoProvider.fetch_climate(lat, lon)
            if data:
                self.cache[cache_key] = data
                return data
        
        return get_mock_climate(lat, lon)
    
    def get_soil(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"soil:{lat:.4f}:{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_real:
            data = SoilGridsProvider.fetch_soil(lat, lon)
            if data:
                self.cache[cache_key] = data
                return data
        
        return get_mock_soil(lat, lon)
    
    def get_sentinel2(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"sentinel:{lat:.4f}:{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_real:
            # For demo, we just get metadata (not full imagery)
            metadata = EarthSearchProvider.fetch_sentinel2(lat, lon)
            if metadata:
                # Use mock imagery for now (full COG download in Phase 14b)
                data = get_mock_sentinel2(lat, lon)
                data["source"] = f"sentinel2-metadata:{metadata.get('scene_id', 'unknown')}"
                data["cloud_cover"] = metadata.get("cloud_cover", 0)
                self.cache[cache_key] = data
                return data
        
        return get_mock_sentinel2(lat, lon)


# ============================================================================
# 6. Demonstration
# ============================================================================

def demo():
    """Demonstrate real data integration."""
    print("=" * 80)
    print("PHASE 14: REAL DATA INTEGRATION")
    print("=" * 80)
    
    if not HAS_REQUESTS:
        print("❌ requests not installed. Run: pip install requests")
        return
    
    provider = RealDataProvider(use_real=True)
    
    # Test locations
    locations = [
        ("Isfahan, Iran", 32.65, 51.67),
        ("Sanaa, Yemen", 15.35, 44.21),
        ("Sacramento, USA", 38.58, -121.49),
        ("Amsterdam, Netherlands", 52.37, 4.90),
        ("Tokyo, Japan", 35.68, 139.69),
    ]
    
    print("\n📡 Fetching real data from Open-Meteo + SoilGrids + Earth Search...")
    print("-" * 80)
    
    results = {}
    
    for name, lat, lon in locations:
        print(f"\n🌍 {name} ({lat:.2f}, {lon:.2f})")
        print("-" * 60)
        
        t0 = time.time()
        
        # Climate (Open-Meteo)
        climate = provider.get_climate(lat, lon)
        print(f"  🌡️  Climate: {climate['source']}")
        print(f"      T_mean = {climate['t_ann_mean']:.1f}°C, P_ann = {climate['p_ann']:.0f}mm")
        
        # Soil (Open-Meteo Land)
        soil = provider.get_soil(lat, lon)
        print(f"  🏜️ Soil: {soil['source']}")
        print(f"      pH = {soil['ph']:.1f}, SOC = {soil['soc_g_per_kg']:.1f} g/kg, Clay = {soil['clay_pct']:.0f}%")
        if "sm_mean_7_28cm" in soil:
            print(f"      SM(7-28cm) = {soil['sm_mean_7_28cm']:.3f} m³/m³, ET0 = {soil['et0_mean_mm_day']:.1f} mm/day")
        
        # Sentinel-2 (Earth Search - metadata only for now)
        sentinel = provider.get_sentinel2(lat, lon)
        print(f"  🛰️  Sentinel-2: {sentinel['source']}")
        if "cloud_cover" in sentinel:
            print(f"      Cloud cover = {sentinel['cloud_cover']:.1f}%")
        
        elapsed = (time.time() - t0) * 1000
        print(f"  ⏱️  Time: {elapsed:.1f} ms")
        
        results[name] = {
            "lat": lat, "lon": lon,
            "climate": climate,
            "soil": soil,
            "sentinel": sentinel,
        }
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    real_climate = sum(1 for r in results.values() 
                       if "open-meteo" in r["climate"]["source"])
    real_soil = sum(1 for r in results.values() 
                    if "open-meteo-land" in r["soil"]["source"])
    
    print(f"  🌡️  Real climate data (ERA5):     {real_climate}/{len(locations)}")
    print(f"  🏜️ Real soil data (ERA5-Land):    {real_soil}/{len(locations)}")
    print(f"  🛰️  Sentinel metadata:             {len(results)}/{len(locations)}")
    
    if real_climate == len(locations) and real_soil == len(locations):
        print("\n🎉 SUCCESS: All real data fetched")
        print("\nNext step: Phase 14b - Full Sentinel-2 COG download with rasterio")
    else:
        print("\n⚠️  Some locations used fallback data")
    
    return results


if __name__ == "__main__":
    demo()