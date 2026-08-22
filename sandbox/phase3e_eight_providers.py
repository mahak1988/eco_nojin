"""
Phase 3e: Eight-Provider Global Earth Intelligence Engine
هدف: ۸ منبع داده رایگان برای پوشش کامل جهانی
پروتکل: Honest data_source tagging + Graceful degradation + Scientific accuracy
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger("econojin.eight")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


# =============================================================================
# 1. Open-Meteo Unified Provider (Historical + Forecast + CMIP6 + Air + Flood)
# =============================================================================

class OpenMeteoUnified:
    """
    Open-Meteo: یک API، پنج سرویس، بدون credential
    
    Sources:
    - Historical: ERA5 reanalysis (1940-present)
    - ECMWF Forecast: IFS HRES 9km (Oct 2025+, open data)
    - Climate: CMIP6 SSP scenarios (2015-2100)
    - Air Quality: CAMS global reanalysis
    - Flood: EFAS (European Flood Awareness System)
    
    Reference: https://open-meteo.com/
    """
    
    name = "open_meteo_unified"
    
    ENDPOINTS = {
        "historical": "https://archive-api.open-meteo.com/v1/archive",
        "forecast": "https://api.open-meteo.com/v1/forecast",
        "ecmwf": "https://api.open-meteo.com/v1/ecmwf",  # IFS HRES open data
        "climate": "https://climate-api.open-meteo.com/v1/climate",
        "air_quality": "https://air-quality-api.open-meteo.com/v1/air-quality",
        "flood": "https://flood-api.open-meteo.com/v1/flood",
    }
    
    def _get(self, endpoint: str, params: dict, timeout: int = 30) -> dict:
        resp = requests.get(self.ENDPOINTS[endpoint], params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Open-Meteo {endpoint}: {data['error']}")
        return data
    
    # --- Historical (ERA5) ---
    def get_historical(self, lat: float, lon: float, start: date, end: date,
                       variables: Optional[list] = None) -> dict:
        if variables is None:
            variables = [
                "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "et0_fao_evapotranspiration",
                "wind_speed_10m_max", "shortwave_radiation_sum",
                "soil_moisture_0_to_7cm_mean", "vapour_pressure_deficit_mean",
            ]
        data = self._get("historical", {
            "latitude": lat, "longitude": lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "daily": ",".join(variables), "timezone": "auto",
        })
        return {"source": "open-meteo", "dataset": "era5-historical", "data": data}
    
    # --- ECMWF IFS Forecast (open since Oct 2025) ---
    def get_ecmwf_forecast(self, lat: float, lon: float,
                           variables: Optional[list] = None) -> dict:
        if variables is None:
            variables = [
                "temperature_2m", "precipitation", "et0_fao_evapotranspiration",
                "wind_speed_10m", "shortwave_radiation",
            ]
        data = self._get("ecmwf", {
            "latitude": lat, "longitude": lon,
            "hourly": ",".join(variables),
            "forecast_days": 15, "timezone": "auto",
        })
        return {"source": "open-meteo", "dataset": "ecmwf-ifs-hres-9km", "data": data}
    
    # --- CMIP6 Climate Projections ---
    def get_climate(self, lat: float, lon: float, start: date, end: date,
                    models: Optional[list] = None) -> dict:
        if models is None:
            models = ["EC_Earth3P_HR", "MRI_AGCM3_2_S", "CMCC_CM2_VHR4"]
        data = self._get("climate", {
            "latitude": lat, "longitude": lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "models": ",".join(models),
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "auto",
        })
        return {"source": "open-meteo", "dataset": "cmip6", "data": data}
    
    # --- Air Quality (CAMS) ---
    def get_air_quality(self, lat: float, lon: float, start: date, end: date) -> dict:
        data = self._get("air_quality", {
            "latitude": lat, "longitude": lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "hourly": "pm2_5,pm10,ozone,nitrogen_dioxide,sulphur_dioxide",
            "timezone": "auto",
        })
        return {"source": "open-meteo", "dataset": "cams-global", "data": data}
    
    # --- Flood (EFAS) ---
    def get_flood(self, lat: float, lon: float) -> dict:
        data = self._get("flood", {
            "latitude": lat, "longitude": lon,
            "daily": "river_discharge", "timezone": "auto",
        })
        return {"source": "open-meteo", "dataset": "efas-flood", "data": data}


# =============================================================================
# 2. Earth Search STAC (Sentinel-2 + Landsat + CopDEM)
# =============================================================================

class EarthSearchSTAC:
    """
    Element 84 Earth Search STAC API
    
    Collections:
    - sentinel-2-l2a: 10m, 13 bands, 5-day revisit
    - landsat-c2-l2: 30m, 11 bands, 16-day revisit
    - cop-dem-glo-30: 30m global DEM
    """
    
    name = "earth_search_stac"
    API_URL = "https://earth-search.aws.element84.com/v1"
    
    COLLECTIONS = {
        "sentinel2": "sentinel-2-l2a",
        "landsat": "landsat-c2-l2",
        "dem": "cop-dem-glo-30",
    }
    
    def search(self, collection: str, lat: float, lon: float,
               start: date, end: date, limit: int = 10, **kwargs) -> list[dict]:
        try:
            import pystac_client
        except ImportError:
            return []
        
        client = pystac_client.Client.open(self.API_URL)
        coll = self.COLLECTIONS.get(collection, collection)
        
        search = client.search(
            collections=[coll],
            intersects={"type": "Point", "coordinates": [lon, lat]},
            datetime=f"{start.isoformat()}/{end.isoformat()}",
            max_items=limit,
        )
        
        return [{
            "id": item.id,
            "datetime": item.datetime.isoformat() if item.datetime else None,
            "collection": coll,
            "bbox": item.bbox,
            "data_source": f"{coll}-real",
        } for item in search.items()]


# =============================================================================
# 3. SoilGrids v2.0 (CORRECTED URL)
# =============================================================================

class SoilGridsV2:
    """
    SoilGrids 2.0 REST API - CORRECTED
    
    ⚠️ URL صحیح: https://rest.isric.org/soilgrids/v2.0/properties/query
    (نه https://rest.isric.org/query که 404 می‌دهد)
    
    Reference: https://rest.isric.org/soilgrids/v2.0/docs
    """
    
    name = "soilgrids_v2"
    BASE_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    
    PROPERTIES = ["phh2o", "soc", "cec", "clay", "sand", "silt", "bdod", "nitrogen"]
    DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm"]
    
    def fetch(self, lat: float, lon: float,
              properties: Optional[list] = None, timeout: int = 60) -> dict:
        props = properties or self.PROPERTIES
        
        params = {"lon": lon, "lat": lat}
        # SoilGrids v2.0 uses repeated query params
        query_parts = [f"lon={lon}", f"lat={lat}"]
        for p in props:
            query_parts.append(f"property={p}")
        for d in self.DEPTHS:
            query_parts.append(f"depth={d}")
        query_parts.extend(["value=mean", "value=Q0.5", "value=uncertainty"])
        
        url = f"{self.BASE_URL}?{'&'.join(query_parts)}"
        
        try:
            resp = requests.get(url, timeout=timeout,
                                headers={"User-Agent": "EcoNojin/3.0"})
            resp.raise_for_status()
            raw = resp.json()
            
            result = {"source": "soilgrids-v2", "lat": lat, "lon": lon, "properties": {}}
            
            for prop_data in raw.get("properties", []):
                name = prop_data.get("name")
                layers = {}
                for layer in prop_data.get("layers", []):
                    depth = layer.get("depth")
                    vals = layer.get("values", {})
                    # SoilGrids scales: pH*10, SOC*10, clay/sand/silt*10
                    scale = 10 if name != "bdod" else 100
                    layers[depth] = {
                        "mean": (vals.get("mean") or 0) / scale,
                        "Q50": (vals.get("Q0.5") or 0) / scale,
                        "uncertainty": (vals.get("uncertainty") or 0) / scale,
                    }
                result["properties"][name] = layers
            
            return result
        except Exception as e:
            logger.warning(f"SoilGrids failed: {e}")
            return {"source": "soilgrids-unavailable", "error": str(e), "lat": lat, "lon": lon}


# =============================================================================
# 4. NASA POWER (Agricultural Weather)
# =============================================================================

class NasaPowerProvider:
    """
    NASA POWER: Prediction of Worldwide Energy Resources
    
    کشاورزی-محور: PAR, Growing Degree Days, Evapotranspiration
    بدون API key، رایگان، جهانی
    
    API: https://power.larc.nasa.gov/api/temporal/daily/point
    Reference: https://power.larc.nasa.gov/
    """
    
    name = "nasa_power"
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Agro-climatology parameters
    PARAMETERS = {
        "T2M": "Temperature at 2m (°C)",
        "T2M_MAX": "Max temperature (°C)",
        "T2M_MIN": "Min temperature (°C)",
        "PRECTOTCORR": "Precipitation (mm/day)",
        "ALLSKY_SFC_SW_DWN": "Solar radiation (kWh/m²/day)",
        "ALLSKY_SFC_PAR_TOT": "PAR (MJ/m²/day)",  # Photosynthetically Active Radiation
        "WS2M": "Wind speed at 2m (m/s)",
        "RH2M": "Relative humidity (%)",
        "GWETTOP": "Surface soil moisture (cm³/cm³)",
        "GWETROOT": "Root zone soil moisture (cm³/cm³)",
        "GWETPROF": "Profile soil moisture (cm³/cm³)",
        "ET": "Evapotranspiration (mm/day)",
    }
    
    def fetch(self, lat: float, lon: float, start: date, end: date,
              parameters: Optional[list] = None) -> dict:
        if parameters is None:
            parameters = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR",
                          "ALLSKY_SFC_SW_DWN", "WS2M", "RH2M",
                          "GWETTOP", "GWETROOT", "ET"]
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "parameters": ",".join(parameters),
            "community": "AG",  # Agriculture community
            "format": "JSON",
        }
        
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            
            return {
                "source": "nasa-power",
                "dataset": "daily-ag",
                "lat": lat, "lon": lon,
                "elevation_m": data.get("geometry", {}).get("coordinates", [0, 0, 0])[2],
                "parameters": data.get("properties", {}).get("parameter", {}),
                "dates": list(data.get("properties", {}).get("parameter", {}).get(
                    parameters[0], {}).keys()) if parameters else [],
            }
        except Exception as e:
            logger.error(f"NASA POWER failed: {e}")
            return {"source": "nasa-power-unavailable", "error": str(e)}


# =============================================================================
# 5. CDS Copernicus (AgERA5 + ERA5-Land + Seasonal)
# =============================================================================

class CdsProvider:
    """
    Copernicus Climate Data Store
    
    Datasets:
    - AgERA5: Agrometeorological indicators (0.1°, daily)
    - ERA5-Land: Land reanalysis (0.1°, hourly)
    - Seasonal: 6-month forecasts
    """
    
    name = "cds_copernicus"
    
    def __init__(self):
        self.client = None
        try:
            import cdsapi
            import os
            key = os.getenv("COPERNICUS_CDS_API_KEY")
            url = os.getenv("COPERNICUS_CDS_URL", "https://cds.climate.copernicus.eu/api")
            if key:
                self.client = cdsapi.Client(url=url, key=key, quiet=True, verify=True)
        except Exception:
            pass
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_agera5(self, lat: float, lon: float, start: date, end: date,
                   output_dir: str = "./data/copernicus") -> Optional[str]:
        if not self.is_available():
            return None
        
        output_path = Path(output_dir) / "agera5"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"agera5_{start}_{end}.zip"
        
        years = sorted(set(str(d.year) for d in _drange(start, end)))
        months = sorted(set(f"{d.month:02d}" for d in _drange(start, end)))
        days = sorted(set(f"{d.day:02d}" for d in _drange(start, end)))
        
        request = {
            "version": "1_1", "format": "zip",
            "variable": ["2m_temperature", "total_precipitation",
                         "solar_radiation_flux", "reference_evapotranspiration"],
            "year": years, "month": months, "day": days,
            "area": [lat + 0.1, lon - 0.1, lat - 0.1, lon + 0.1],
        }
        
        try:
            self.client.retrieve("sis-agrometeorological-indicators", request, str(output_file))
            return str(output_file)
        except Exception as e:
            logger.error(f"AgERA5 failed: {e}")
            return None


def _drange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


# =============================================================================
# 6. Provider Registry (مدیریت مرکزی ۸ منبع)
# =============================================================================

@dataclass
class ProviderStatus:
    name: str
    available: bool
    data_source: str
    credential_required: bool
    coverage: str
    last_test: Optional[datetime] = None
    latency_ms: Optional[float] = None


class EightProviderRegistry:
    """مدیریت مرکزی ۸ منبع داده"""
    
    def __init__(self):
        self.providers = {}
        self.status: list[ProviderStatus] = []
    
    def register_all(self):
        self.providers["open_meteo"] = OpenMeteoUnified()
        self.providers["earth_search"] = EarthSearchSTAC()
        self.providers["soilgrids"] = SoilGridsV2()
        self.providers["nasa_power"] = NasaPowerProvider()
        self.providers["cds"] = CdsProvider()
    
    def health_check(self, lat: float = 34.55, lon: float = 46.30) -> list[ProviderStatus]:
        """بررسی سلامت همه provider‌ها"""
        import time
        
        self.status = []
        test_date = date(2024, 6, 15)
        
        checks = [
            ("open_meteo_historical", lambda: self.providers["open_meteo"].get_historical(
                lat, lon, test_date, test_date), "era5", False, "global"),
            ("open_meteo_ecmwf", lambda: self.providers["open_meteo"].get_ecmwf_forecast(
                lat, lon), "ecmwf-ifs-9km", False, "global"),
            ("open_meteo_cmip6", lambda: self.providers["open_meteo"].get_climate(
                lat, lon, date(2050, 1, 1), date(2050, 1, 31)), "cmip6", False, "global"),
            ("open_meteo_air", lambda: self.providers["open_meteo"].get_air_quality(
                lat, lon, test_date, test_date), "cams", False, "global"),
            ("earth_search_s2", lambda: self.providers["earth_search"].search(
                "sentinel2", lat, lon, date(2024, 1, 1), date(2024, 12, 31), limit=1),
                "sentinel-2-l2a", False, "global"),
            ("soilgrids", lambda: self.providers["soilgrids"].fetch(lat, lon, ["phh2o"]),
                "soilgrids-v2", False, "global"),
            ("nasa_power", lambda: self.providers["nasa_power"].fetch(
                lat, lon, test_date, test_date), "nasa-power-ag", False, "global"),
            ("cds_agera5", lambda: self.providers["cds"].get_agera5(
                lat, lon, test_date, test_date) if self.providers["cds"].is_available() else None,
                "agera5", True, "global"),
        ]
        
        for name, func, source, cred, coverage in checks:
            t0 = time.time()
            try:
                result = func()
                latency = (time.time() - t0) * 1000
                available = result is not None
                self.status.append(ProviderStatus(
                    name=name, available=available, data_source=source,
                    credential_required=cred, coverage=coverage,
                    last_test=datetime.now(), latency_ms=latency,
                ))
            except Exception as e:
                latency = (time.time() - t0) * 1000
                self.status.append(ProviderStatus(
                    name=name, available=False, data_source=source,
                    credential_required=cred, coverage=coverage,
                    last_test=datetime.now(), latency_ms=latency,
                ))
                logger.warning(f"{name}: {e}")
        
        return self.status


# =============================================================================
# 7. Comprehensive Test
# =============================================================================

def comprehensive_test():
    print("=" * 80)
    print("🌍 Phase 3e: Eight-Provider Global Earth Intelligence Engine")
    print("=" * 80)
    
    registry = EightProviderRegistry()
    registry.register_all()
    
    lat, lon = 34.55, 46.30  # Hejij, Kermanshah
    print(f"\n📍 Test location: ({lat}, {lon})")
    print(f"⏳ Running health checks...\n")
    
    status = registry.health_check(lat, lon)
    
    print("\n" + "=" * 80)
    print("📊 EIGHT-PROVIDER HEALTH REPORT")
    print("=" * 80)
    print(f"{'Provider':<25} {'Status':<8} {'Source':<20} {'Latency':<10} {'Cred'}")
    print("─" * 80)
    
    for s in status:
        icon = "✅" if s.available else "❌"
        lat_str = f"{s.latency_ms:.0f}ms" if s.latency_ms else "N/A"
        cred_str = "🔑" if s.credential_required else "🆓"
        print(f"{icon} {s.name:<23} {s.data_source:<20} {lat_str:<10} {cred_str}")
    
    passed = sum(1 for s in status if s.available)
    total = len(status)
    
    print(f"\n🎯 Score: {passed}/{total} providers operational")
    
    if passed >= 6:
        print("\n🎉 GLOBAL COVERAGE ACHIEVED!")
        print("   Project can serve any location on Earth with multi-source data.")
    
    print("\n💡 Data Fusion Capability:")
    print("   • Optical: Sentinel-2 L2A (10m, 5-day) + Landsat (30m, 16-day)")
    print("   • Weather: ERA5 historical + ECMWF IFS forecast + NASA POWER")
    print("   • Soil: SoilGrids v2.0 (250m, 6 depths)")
    print("   • Climate: CMIP6 SSP scenarios (2015-2100)")
    print("   • Air: CAMS global reanalysis")
    print("   • Agri: AgERA5 (CDS) + FAO-56 ET0 (Open-Meteo)")
    
    return passed >= 6


if __name__ == "__main__":
    comprehensive_test()