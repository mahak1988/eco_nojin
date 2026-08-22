"""
Phase 3c: Copernicus Multi-Service Bridge
هدف: استفاده از credentials موجود در .env برای اتصال به CDS, ADS, EWDS
پروتکل: Read from .env + Graceful fallback + Scientific accuracy
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("econojin.copernicus")

# Dependency check
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    logger.warning("python-dotenv not installed")

try:
    import cdsapi
    HAS_CDSAPI = True
except ImportError:
    HAS_CDSAPI = False
    logger.warning("cdsapi not installed")


# =============================================================================
# 1. Service Configuration
# =============================================================================

SERVICES = {
    "cds": {
        "env_url": "COPERNICUS_CDS_URL",
        "env_key": "COPERNICUS_CDS_API_KEY",
        "default_url": "https://cds.climate.copernicus.eu/api",
        "description": "Climate Data Store (ERA5, AgERA5, Seasonal)",
    },
    "ads": {
        "env_url": "COPERNICUS_ADS_URL",
        "env_key": "COPERNICUS_ADS_API_KEY",
        "default_url": "https://ads.atmosphere.copernicus.eu/api",
        "description": "Atmosphere Data Store (CAMS air quality)",
    },
    "ewds": {
        "env_url": "COPERNICUS_EWDS_URL",
        "env_key": "COPERNICUS_EWDS_API_KEY",
        "default_url": "https://ewds.climate.copernicus.eu/api",
        "description": "Emergency Data Store (flood, fire risk)",
    },
}


# =============================================================================
# 2. CopernicusClient
# =============================================================================

class CopernicusClient:
    """
    Multi-service Copernicus client using .env credentials
    
    Supports:
    - CDS: AgERA5 (agri-meteo), ERA5-Land, Seasonal forecasts
    - ADS: CAMS air quality, aerosols, GHG
    - EWDS: EFAS flood, EFFIS fire
    """
    
    def __init__(self, env_path: Optional[str] = None):
        self.env_path = Path(env_path) if env_path else self._find_env()
        
        # Load .env
        if HAS_DOTENV and self.env_path.exists():
            load_dotenv(self.env_path)
            logger.info(f"📄 Loaded .env from {self.env_path}")
        else:
            logger.warning(f".env not found at {self.env_path}")
        
        # Initialize clients per service
        self.clients: dict[str, Any] = {}
        self._init_clients()
    
    def _find_env(self) -> Path:
        """یافتن .env در مسیرهای استاندارد"""
        candidates = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent / ".env",
            Path(__file__).parent.parent.parent / ".env",
        ]
        for c in candidates:
            if c.exists():
                return c
        return Path.cwd() / ".env"
    
    def _init_clients(self):
        """ساخت client برای هر سرویس موجود"""
        if not HAS_CDSAPI:
            logger.error("cdsapi not installed - cannot create clients")
            return
        
        for name, config in SERVICES.items():
            url = os.getenv(config["env_url"], config["default_url"])
            key = os.getenv(config["env_key"])
            
            if not key:
                logger.warning(f"❌ {config['env_key']} not in .env - skipping {name}")
                continue
            
            try:
                # cdsapi.Client با URL و Key صریح (بدون نیاز به .cdsapirc)
                client = cdsapi.Client(
                    url=url,
                    key=key,
                    quiet=True,
                    verify=True,
                )
                self.clients[name] = client
                masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
                logger.info(f"✅ {name.upper()} client initialized (key: {masked_key})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name}: {e}")
    
    def is_available(self, service: str = "cds") -> bool:
        """بررسی در دسترس بودن یک سرویس"""
        return service in self.clients
    
    def list_available_services(self) -> list[str]:
        """لیست سرویس‌های فعال"""
        return list(self.clients.keys())
    
    # -------------------------------------------------------------------------
    # Scientific Data Methods
    # -------------------------------------------------------------------------
    
    def get_agricultural_indicators(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        variables: Optional[list[str]] = None,
        output_dir: str = "./data/copernicus",
    ) -> Optional[str]:
        """
        دریافت AgERA5 (Agrometeorological indicators) - داده‌های تخصصی کشاورزی
        
        Available variables:
        - 2m_temperature (K)
        - total_precipitation (m)
        - solar_radiation_flux (W/m2)
        - 10m_wind_speed (m/s)
        - vapour_pressure (Pa)
        - reference_evapotranspiration (m)
        - potential_evaporation (m)
        
        Resolution: 0.1° (~11 km)
        Period: 1979-present, daily
        """
        if not self.is_available("cds"):
            logger.error("CDS not available")
            return None
        
        if variables is None:
            variables = [
                "2m_temperature",
                "total_precipitation",
                "solar_radiation_flux",
                "reference_evapotranspiration",
                "vapour_pressure",
            ]
        
        # AgERA5 version 1_1 (latest)
        request = {
            "version": "1_1",
            "format": "zip",
            "variable": variables,
            "year": sorted(list(set(
                str(d.year) for d in _date_range(start_date, end_date)
            ))),
            "month": sorted(list(set(
                f"{d.month:02d}" for d in _date_range(start_date, end_date)
            ))),
            "day": sorted(list(set(
                f"{d.day:02d}" for d in _date_range(start_date, end_date)
            ))),
            "area": [lat + 0.1, lon - 0.1, lat - 0.1, lon + 0.1],  # [N, W, S, E]
        }
        
        output_path = Path(output_dir) / "agera5"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"agera5_{start_date}_{end_date}.zip"
        
        try:
            logger.info(f"📥 Downloading AgERA5 for ({lat}, {lon})...")
            self.clients["cds"].retrieve(
                "sis-agrometeorological-indicators",
                request,
                str(output_file),
            )
            logger.info(f"✅ Downloaded: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"AgERA5 download failed: {e}")
            return None
    
    def get_era5_land(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        variables: Optional[list[str]] = None,
        output_dir: str = "./data/copernicus",
    ) -> Optional[str]:
        """
        دریافت ERA5-Land برای مدل‌های هیدرولوژی
        
        Variables:
        - soil_temperature_level_1 (K)
        - volumetric_soil_water_layer_1 (m3/m3)
        - 2m_temperature (K)
        - total_precipitation (m)
        - surface_solar_radiation_downwards (J/m2)
        """
        if not self.is_available("cds"):
            return None
        
        if variables is None:
            variables = [
                "2m_temperature",
                "total_precipitation",
                "soil_temperature_level_1",
                "volumetric_soil_water_layer_1",
                "surface_solar_radiation_downwards",
            ]
        
        request = {
            "format": "zip",
            "variable": variables,
            "year": sorted(list(set(
                str(d.year) for d in _date_range(start_date, end_date)
            ))),
            "month": sorted(list(set(
                f"{d.month:02d}" for d in _date_range(start_date, end_date)
            ))),
            "day": sorted(list(set(
                f"{d.day:02d}" for d in _date_range(start_date, end_date)
            ))),
            "time": [f"{h:02d}:00" for h in range(0, 24, 6)],  # 6-hourly
            "area": [lat + 0.1, lon - 0.1, lat - 0.1, lon + 0.1],
        }
        
        output_path = Path(output_dir) / "era5_land"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"era5_land_{start_date}_{end_date}.zip"
        
        try:
            logger.info(f"📥 Downloading ERA5-Land...")
            self.clients["cds"].retrieve(
                "reanalysis-era5-land",
                request,
                str(output_file),
            )
            logger.info(f"✅ Downloaded: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"ERA5-Land download failed: {e}")
            return None
    
    def get_seasonal_forecast(
        self,
        lat: float,
        lon: float,
        variable: str = "2m_temperature",
        output_dir: str = "./data/copernicus",
    ) -> Optional[str]:
        """
        دریافت پیش‌بینی فصلی (6 ماه آینده)
        
        برای کشاورزی حیاتی: پیش‌بینی خشکسالی و موج گرما
        """
        if not self.is_available("cds"):
            return None
        
        now = datetime.now()
        request = {
            "originating_centre": "ecmwf",
            "system": "5",
            "format": "zip",
            "variable": variable,
            "year": str(now.year),
            "month": f"{now.month:02d}",
            "day": "01",
            "leadtime_hour": [str(h) for h in range(24, 24 * 31 * 6, 24)],  # 6 months
            "area": [lat + 0.5, lon - 0.5, lat - 0.5, lon + 0.5],
        }
        
        output_path = Path(output_dir) / "seasonal"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"seasonal_{now.strftime('%Y%m')}.zip"
        
        try:
            logger.info(f"📥 Downloading seasonal forecast...")
            self.clients["cds"].retrieve(
                "seasonal-original-single-levels",
                request,
                str(output_file),
            )
            logger.info(f"✅ Downloaded: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Seasonal forecast failed: {e}")
            return None
    
    def get_air_quality(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        output_dir: str = "./data/copernicus",
    ) -> Optional[str]:
        """
        دریافت CAMS air quality از ADS
        
        Variables: PM2.5, PM10, O3, NO2, SO2
        """
        if not self.is_available("ads"):
            logger.warning("ADS not available")
            return None
        
        request = {
            "format": "zip",
            "variable": [
                "particulate_matter_2.5",
                "particulate_matter_10",
                "ozone",
                "nitrogen_dioxide",
            ],
            "date": [
                d.strftime("%Y-%m-%d") 
                for d in _date_range(start_date, end_date)
            ][:30],  # محدودیت ADS
            "time": ["12:00"],
            "type": "reanalysis",
            "area": [lat + 0.1, lon - 0.1, lat - 0.1, lon + 0.1],
        }
        
        output_path = Path(output_dir) / "cams"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"cams_{start_date}_{end_date}.zip"
        
        try:
            logger.info(f"📥 Downloading CAMS air quality...")
            self.clients["ads"].retrieve(
                "cams-global-reanalysis-eac4",
                request,
                str(output_file),
            )
            logger.info(f"✅ Downloaded: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"CAMS download failed: {e}")
            return None


def _date_range(start: date, end: date):
    """Iterate over dates in range"""
    from datetime import timedelta
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


# =============================================================================
# 3. Smoke Test
# =============================================================================

def smoke_test():
    print("=" * 70)
    print("🧪 Copernicus Multi-Service Bridge - Smoke Test")
    print("=" * 70)
    
    client = CopernicusClient()
    
    available = client.list_available_services()
    print(f"\n📋 Available services: {available}")
    print()
    
    if not available:
        print("❌ No services available. Check .env file.")
        return False
    
    # Location: Hejij Village
    lat, lon = 34.55, 46.30
    
    # Test 1: AgERA5 (small request - 1 day)
    if "cds" in available:
        print("🧪 Test 1: AgERA5 (1 day sample)")
        result = client.get_agricultural_indicators(
            lat, lon,
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 15),
            variables=["2m_temperature", "total_precipitation"],
        )
        if result:
            print(f"   ✅ {result}")
        else:
            print(f"   ❌ Failed")
    
    # Test 2: ERA5-Land (1 day)
    if "cds" in available:
        print("\n🧪 Test 2: ERA5-Land (1 day sample)")
        result = client.get_era5_land(
            lat, lon,
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 15),
            variables=["2m_temperature", "volumetric_soil_water_layer_1"],
        )
        if result:
            print(f"   ✅ {result}")
        else:
            print(f"   ❌ Failed")
    
    # Test 3: Seasonal forecast
    if "cds" in available:
        print("\n🧪 Test 3: Seasonal forecast (current month)")
        result = client.get_seasonal_forecast(lat, lon)
        if result:
            print(f"   ✅ {result}")
        else:
            print(f"   ⚠️ May not be available for this account")
    
    # Test 4: CAMS air quality
    if "ads" in available:
        print("\n🧪 Test 4: CAMS air quality (1 day)")
        result = client.get_air_quality(
            lat, lon,
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 15),
        )
        if result:
            print(f"   ✅ {result}")
        else:
            print(f"   ❌ Failed")
    
    return True


if __name__ == "__main__":
    smoke_test()