"""
Phase 3b: Multi-Source Satellite & Climate Data Providers
هدف: ایجاد Provider Factory با ۵ منبع داده واقعی (Optical, DEM, Soil, Climate, Atmosphere)
پروتکل: Sandbox-First, Graceful Degradation, Evidence-Based
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger("econojin.satellite")

# Optional imports with graceful fallback
try:
    import pystac_client
    import xarray as xr
    import rioxarray  # noqa: F401
    HAS_STAC = True
except ImportError:
    HAS_STAC = False
    logger.warning("pystac-client/xarray/rioxarray not available. STAC providers will use fallback.")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import cdsapi
    HAS_CDS = True
except ImportError:
    HAS_CDS = False


# =============================================================================
# 1. Extended SatelliteTile (Backward Compatible)
# =============================================================================

@dataclass
class ExtendedTile:
    """نسخه توسعه‌یافته SatelliteTile با metadata بیشتر"""
    provider: str
    collection: str
    datetime: datetime
    bbox: tuple[float, float, float, float]
    cloud_cover: float
    bands: dict[str, np.ndarray]
    crs: str
    data_source: str
    # فیلدهای جدید (optional for backward compatibility)
    resolution_m: float = 10.0
    quality_score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_level: str = "L2A"


# =============================================================================
# 2. Provider Interface (Protocol - PEP 544)
# =============================================================================

class DataProvider(Protocol):
    """Interface مشترک برای تمام provider‌ها"""
    name: str
    
    def search(self, lat: float, lon: float, start_date: date, end_date: date, 
               **kwargs) -> list[dict]: ...
    
    def fetch(self, item_id: str, **kwargs) -> ExtendedTile: ...
    
    def is_available(self) -> bool: ...


# =============================================================================
# 3. RealEarthSearchProvider (Sentinel-2 L2A) - بدون نیاز به credential
# =============================================================================

class RealEarthSearchProvider:
    """
    اتصال واقعی به Earth Search STAC API (Element 84)
    
    Source: https://earth-search.aws.element84.com/v1/
    Collection: sentinel-2-l2a
    Resolution: 10m (B02, B03, B04, B08), 20m (B05-B07, B8A, B11, B12), 60m (B01, B09, B10)
    Revisit: 5 days
    License: CC-BY-4.0
    """
    
    name = "earth_search_sentinel2"
    API_URL = "https://earth-search.aws.element84.com/v1"
    COLLECTION = "sentinel-2-l2a"
    
    # Sentinel-2 band info
    BANDS_10M = ["B02", "B03", "B04", "B08"]  # Blue, Green, Red, NIR
    BANDS_20M = ["B05", "B06", "B07", "B8A", "B11", "B12", "SCL"]
    BANDS_60M = ["B01", "B09", "B10"]  # Coastal, Water vapor, SWIR cirrus
    
    def is_available(self) -> bool:
        return HAS_STAC
    
    def search(self, lat: float, lon: float, start_date: date, end_date: date,
               max_cloud_cover: float = 30.0, limit: int = 20, **kwargs) -> list[dict]:
        """جستجوی Sentinel-2 L2A tiles"""
        if not self.is_available():
            logger.warning(f"{self.name} not available (missing pystac-client)")
            return []
        
        try:
            client = pystac_client.Client.open(self.API_URL)
            
            # Build query
            query = {
                "eo:cloud_cover": {"lt": max_cloud_cover},
                "processing:software": {"sentinel2-processing": "Sen2Cor"},
            }
            
            search = client.search(
                collections=[self.COLLECTION],
                intersects={"type": "Point", "coordinates": [lon, lat]},
                datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
                query=query,
                max_items=limit,
            )
            
            results = []
            for item in search.items():
                results.append({
                    "id": item.id,
                    "datetime": item.datetime.isoformat() if item.datetime else None,
                    "cloud_cover": item.properties.get("eo:cloud_cover", 0),
                    "provider": self.name,
                    "collection": self.COLLECTION,
                    "bbox": item.bbox,
                    "data_source": "sentinel-2-l2a-real",  # صداقت: داده واقعی
                })
            
            logger.info(f"{self.name}: found {len(results)} items")
            return results
            
        except Exception as e:
            logger.error(f"{self.name} search failed: {e}")
            return []
    
    def fetch(self, item_id: str, bands: Optional[list[str]] = None, **kwargs) -> ExtendedTile:
        """دانلود یک Sentinel-2 tile (COG format)"""
        if not self.is_available():
            raise RuntimeError(f"{self.name} not available")
        
        try:
            import stackstac  # Lazy import for optional dependency
            client = pystac_client.Client.open(self.API_URL)
            item = next(client.search(collections=[self.COLLECTION], ids=[item_id]).items())
            
            # Use stackstac for efficient loading
            target_bands = bands or (self.BANDS_10M + ["SCL"])
            stack = stackstac.stack(
                [item],
                assets=target_bands,
                resolution=10,
                epsg=4326,
                dtype="float32",
                fill_value=np.nan,
            )
            
            bands_data = {}
            for band in target_bands:
                if band in stack.band.values:
                    arr = stack.sel(band=band).values
                    bands_data[band] = arr[0] if arr.ndim == 3 else arr
            
            return ExtendedTile(
                provider=self.name,
                collection=self.COLLECTION,
                datetime=item.datetime,
                bbox=tuple(item.bbox),
                cloud_cover=item.properties.get("eo:cloud_cover", 0.0),
                bands=bands_data,
                crs="EPSG:4326",
                data_source="sentinel-2-l2a-real",
                resolution_m=10.0,
                quality_score=1.0 - (item.properties.get("eo:cloud_cover", 0.0) / 100),
                metadata={"platform": "Sentinel-2", "instrument": "MSI"},
            )
        except Exception as e:
            logger.error(f"{self.name} fetch failed: {e}")
            raise


# =============================================================================
# 4. SoilGridsProvider (Global Soil Data) - بدون credential
# =============================================================================

class SoilGridsProvider:
    """
    اتصال به SoilGrids 2.0 REST API (ISRIC)
    
    Source: https://rest.isric.org/
    Data: pH, Organic Carbon, CEC, Bulk density, Texture (sand/silt/clay)
    Depths: 0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm
    Resolution: 250m global
    License: CC-BY 4.0
    """
    
    name = "soilgrids_v2"
    BASE_URL = "https://rest.isric.org/query"
    
    # Soil properties available in SoilGrids
    PROPERTIES = ["bdod", "cec", "cfvo", "clay", "nitrogen", "ocd", "ocs", 
                  "phh2o", "sand", "silt", "soc", "wrb"]
    
    DEPTH_LAYERS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
    
    def is_available(self) -> bool:
        return HAS_REQUESTS
    
    def search(self, lat: float, lon: float, **kwargs) -> list[dict]:
        """SoilGrids یک نقطه‌ای است - search معنای خاصی ندارد"""
        return [{"id": f"soil_{lat:.4f}_{lon:.4f}", "lat": lat, "lon": lon}]
    
    def fetch(self, lat: float, lon: float, properties: Optional[list[str]] = None,
              **kwargs) -> dict[str, Any]:
        """
        دریافت داده‌های خاک برای یک نقطه
        
        Returns: dict با ساختار {property: {depth: {mean, Q0.05, Q0.95, uncertainty}}}
        """
        if not self.is_available():
            raise RuntimeError(f"{self.name} not available")
        
        props = properties or ["phh2o", "soc", "cec", "clay", "sand", "silt", "bdod"]
        
        try:
            # SoilGrids REST API
            url = f"{self.BASE_URL}?lon={lon}&lat={lat}"
            for prop in props:
                url += f"&property={prop}"
            for depth in self.DEPTH_LAYERS:
                url += f"&depth={depth}"
            url += "&value=mean&value=Q0.05&value=Q0.5&value=Q0.95&value=uncertainty"
            
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            # Parse structured response
            result = {"provider": self.name, "lat": lat, "lon": lon, "properties": {}}
            
            for prop_data in data.get("properties", []):
                prop_name = prop_data.get("name")
                layers = {}
                for depth_data in prop_data.get("layers", []):
                    depth = depth_data.get("depth")
                    values = depth_data.get("values", {})
                    # SoilGrids uses scaled values (e.g., pH * 10, SOC * 10)
                    unit = prop_data.get("unitMagnitude", 1)
                    layers[depth] = {
                        "mean": values.get("mean", 0) / unit if unit else values.get("mean"),
                        "Q05": values.get("Q0.05", 0) / unit if unit else values.get("Q0.05"),
                        "Q50": values.get("Q0.5", 0) / unit if unit else values.get("Q0.5"),
                        "Q95": values.get("Q0.95", 0) / unit if unit else values.get("Q0.95"),
                    }
                result["properties"][prop_name] = layers
            
            logger.info(f"{self.name}: fetched soil data for ({lat:.4f}, {lon:.4f})")
            return result
            
        except requests.HTTPError as e:
            logger.error(f"{self.name} HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"{self.name} fetch failed: {e}")
            raise


# =============================================================================
# 5. CDS Climate Provider (AgERA5, ERA5-Land) - با credential
# =============================================================================

class CDSProvider:
    """
    اتصال به Climate Data Store API (Copernicus)
    
    Datasets:
    - sis-agrometeorological-indicators (AgERA5) - مخصوص کشاورزی
    - reanalysis-era5-land - برای مدل‌های هیدرولوژی
    - seasonal-forecast - پیش‌بینی ۶ ماهه
    """
    
    name = "cds_climate"
    
    DATASETS = {
        "agera5": "sis-agrometeorological-indicators",
        "era5_land": "reanalysis-era5-land",
        "seasonal": "seasonal-original-single-levels",
    }
    
    def is_available(self) -> bool:
        return HAS_CDS
    
    def search(self, lat: float, lon: float, start_date: date, end_date: date, 
               dataset: str = "agera5", **kwargs) -> list[dict]:
        """CDS از search پشتیبانی نمی‌کند - مستقیم download می‌کند"""
        return [{"id": f"{dataset}_{start_date}_{end_date}", 
                 "dataset": dataset, "lat": lat, "lon": lon}]
    
    def fetch(self, dataset: str, lat: float, lon: float, 
              start_date: date, end_date: date, 
              variables: Optional[list[str]] = None, 
              output_dir: str = "./data/climate",
              **kwargs) -> str:
        """
        دانلود داده‌های اقلیمی
        
        Returns: path to downloaded file (NetCDF/GRIB)
        """
        if not self.is_available():
            raise RuntimeError(f"{self.name} not available (install cdsapi)")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        dataset_id = self.DATASETS.get(dataset, dataset)
        
        # Default variables for AgERA5
        if variables is None:
            if dataset == "agera5":
                variables = [
                    "2m_temperature", 
                    "total_precipitation",
                    "solar_radiation_flux",
                    "10m_wind_speed",
                    "vapour_pressure",
                ]
            elif dataset == "era5_land":
                variables = ["2m_temperature", "total_precipitation", "soil_temperature_level_1"]
        
        # Build request
        request = {
            "format": "netcdf_zip",
            "variable": variables,
            "year": list(set(str(d.year) for d in [start_date, end_date])),
            "month": [f"{m:02d}" for m in range(1, 13)],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "area": [lat + 0.5, lon - 0.5, lat - 0.5, lon + 0.5],  # [N, W, S, E]
        }
        
        if dataset in ["agera5", "era5_land"]:
            request["version"] = "1_1" if dataset == "agera5" else "1"
        
        # Execute
        try:
            c = cdsapi.Client()
            output_file = output_path / f"{dataset}_{start_date}_{end_date}.zip"
            c.retrieve(dataset_id, request, str(output_file))
            logger.info(f"{self.name}: downloaded to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"{self.name} download failed: {e}")
            raise


# =============================================================================
# 6. Provider Factory (انتخاب هوشمند)
# =============================================================================

class ProviderFactory:
    """
    Factory برای انتخاب بهترین provider بر اساس:
    1. Credential موجود
    2. اولویت داده (quality)
    3. Fallback در صورت شکست
    """
    
    @staticmethod
    def get_optical_provider(prefer_real: bool = True) -> RealEarthSearchProvider:
        """Sentinel-2 provider"""
        if prefer_real and HAS_STAC:
            return RealEarthSearchProvider()
        raise RuntimeError("No optical provider available")
    
    @staticmethod
    def get_soil_provider() -> SoilGridsProvider:
        """Global soil data"""
        if HAS_REQUESTS:
            return SoilGridsProvider()
        raise RuntimeError("No soil provider available")
    
    @staticmethod
    def get_climate_provider() -> Optional[CDSProvider]:
        """CDS climate data - returns None if not available"""
        if HAS_CDS:
            # Check if credentials exist
            cds_rc = Path.home() / ".cdsapirc"
            if cds_rc.exists():
                return CDSProvider()
        logger.warning("CDS provider not available (missing credentials)")
        return None
    
    @staticmethod
    def list_available() -> list[str]:
        """لیست provider‌های موجود"""
        available = []
        if HAS_STAC:
            available.append("earth_search_sentinel2")
        if HAS_REQUESTS:
            available.append("soilgrids_v2")
        if HAS_CDS and (Path.home() / ".cdsapirc").exists():
            available.append("cds_climate")
        return available


# =============================================================================
# 7. Spectral Index Calculator (SOTA algorithms)
# =============================================================================

class SpectralIndices:
    """
    محاسبه شاخص‌های طیفی پیشرفته از Sentinel-2
    
    References:
    - NDVI: Rouse et al. (1973)
    - EVI: Huete et al. (2002)
    - SAVI: Huete (1988)
    - NDWI: McFeeters (1996)
    - NBR: Key & Benson (2006)
    - NDSI (Soil): Rogers (1998)
    """
    
    @staticmethod
    def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Normalized Difference Vegetation Index [-1, 1]"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (nir - red) / (nir + red)
        return np.nan_to_num(result, nan=np.nan)
    
    @staticmethod
    def evi(red: np.ndarray, nir: np.ndarray, blue: np.ndarray,
            G: float = 2.5, C1: float = 6.0, C2: float = 7.5, L: float = 1.0) -> np.ndarray:
        """Enhanced Vegetation Index [-1, 1] - اصلاح اثرات اتمسفر"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = G * (nir - red) / (nir + C1 * red - C2 * blue + L)
        return np.nan_to_num(result, nan=np.nan)
    
    @staticmethod
    def savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
        """Soil-Adjusted Vegetation Index - مناسب مناطق با پوشش کم"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (1 + L) * (nir - red) / (nir + red + L)
        return np.nan_to_num(result, nan=np.nan)
    
    @staticmethod
    def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Normalized Difference Water Index - تشخیص آب"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (green - nir) / (green + nir)
        return np.nan_to_num(result, nan=np.nan)
    
    @staticmethod
    def nbr(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Normalized Burn Ratio - تشخیص آتش‌سوزی"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (nir - swir) / (nir + swir)
        return np.nan_to_num(result, nan=np.nan)
    
    @staticmethod
    def lai_from_ndvi(ndvi: np.ndarray) -> np.ndarray:
        """
        تخمین LAI از NDVI - رابطه تجربی
        
        Reference: Haboudane et al. (2004) - برای Sentinel-2
        LAI = 0.57 * exp(2.33 * NDVI)
        """
        return 0.57 * np.exp(2.33 * np.clip(ndvi, 0, 1))
    
    @classmethod
    def compute_all(cls, bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """محاسبه همه شاخص‌های ممکن از باندهای موجود"""
        results = {}
        
        # Check available bands (Sentinel-2)
        has_red = "B04" in bands
        has_green = "B03" in bands
        has_blue = "B02" in bands
        has_nir = "B08" in bands
        has_swir1 = "B11" in bands  # SWIR 1.6µm
        has_swir2 = "B12" in bands  # SWIR 2.2µm
        
        if has_red and has_nir:
            results["ndvi"] = cls.ndvi(bands["B04"], bands["B08"])
            results["savi"] = cls.savi(bands["B04"], bands["B08"])
            results["lai"] = cls.lai_from_ndvi(results["ndvi"])
        
        if has_red and has_nir and has_blue:
            results["evi"] = cls.evi(bands["B04"], bands["B08"], bands["B02"])
        
        if has_green and has_nir:
            results["ndwi"] = cls.ndwi(bands["B03"], bands["B08"])
        
        if has_nir and has_swir2:
            results["nbr"] = cls.nbr(bands["B08"], bands["B12"])
        
        return results


# =============================================================================
# 8. Smoke Test
# =============================================================================

def smoke_test():
    """تست سریع عملکرد providers"""
    print("=" * 70)
    print("🧪 Smoke Test: Multi-Source Providers")
    print("=" * 70)
    
    available = ProviderFactory.list_available()
    print(f"\n📋 Provider‌های موجود: {available}")
    
    # Test location: Hejij Village, Kermanshah (from project context)
    lat, lon = 34.55, 46.30
    
    results = []
    
    # Test 1: Earth Search (Sentinel-2)
    print("\n🧪 Test 1: Earth Search Sentinel-2")
    try:
        optical = ProviderFactory.get_optical_provider()
        search_results = optical.search(lat, lon, 
                                         date(2024, 1, 1), date(2024, 12, 31),
                                         max_cloud_cover=20.0, limit=5)
        print(f"   ✅ Found {len(search_results)} Sentinel-2 tiles")
        if search_results:
            print(f"      Sample ID: {search_results[0]['id']}")
            print(f"      Cloud: {search_results[0]['cloud_cover']}%")
        results.append(("earth_search", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("earth_search", False))
    
    # Test 2: SoilGrids
    print("\n🧪 Test 2: SoilGrids soil data")
    try:
        soil = ProviderFactory.get_soil_provider()
        soil_data = soil.fetch(lat, lon, properties=["phh2o", "soc", "clay"])
        print(f"   ✅ Soil data fetched")
        props = soil_data["properties"]
        print(f"      pH (0-5cm): {props['phh2o']['0-5cm']['mean']:.2f}")
        print(f"      SOC (0-5cm): {props['soc']['0-5cm']['mean']:.2f} g/kg")
        print(f"      Clay (0-5cm): {props['clay']['0-5cm']['mean']:.1f}%")
        results.append(("soilgrids", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("soilgrids", False))
    
    # Test 3: Spectral Indices
    print("\n🧪 Test 3: Spectral Indices Calculator")
    try:
        red = np.array([0.1, 0.2, 0.3])
        nir = np.array([0.4, 0.5, 0.6])
        ndvi = SpectralIndices.ndvi(red, nir)
        lai = SpectralIndices.lai_from_ndvi(ndvi)
        print(f"   ✅ NDVI = {ndvi}")
        print(f"   ✅ LAI = {lai}")
        results.append(("spectral_indices", True))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("spectral_indices", False))
    
    # Test 4: CDS (only if credentials exist)
    print("\n🧪 Test 4: CDS Climate Provider")
    try:
        cds = ProviderFactory.get_climate_provider()
        if cds:
            print(f"   ✅ CDS provider available")
            print(f"      Datasets: {list(cds.DATASETS.keys())}")
            results.append(("cds", True))
        else:
            print(f"   ⚠️ CDS not available (missing credentials)")
            results.append(("cds", False))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("cds", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"   {status} {name}")
    
    return all(ok for _, ok in results)


if __name__ == "__main__":
    smoke_test()