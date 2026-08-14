"""NASA POWER API provider for meteorological data.

Provides free access to global meteorological data without API key.
Useful for ET0 calculation, drought monitoring, and climate analysis.
Source: https://power.larc.nasa.gov/api/
"""
import requests
from datetime import date
from dataclasses import dataclass
from typing import Optional


@dataclass
class MeteoData:
    """Meteorological data point."""
    date: date
    lat: float
    lon: float
    temp_min: float  # °C
    temp_max: float  # °C
    temp_mean: float  # °C
    humidity: Optional[float]  # %
    wind_speed: Optional[float]  # m/s
    solar_radiation: float  # MJ/m²/day
    precipitation: float  # mm


class NasaPowerProvider:
    """Fetches meteorological data from NASA POWER API."""
    
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    def fetch_daily(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
    ) -> list[MeteoData]:
        """Fetch daily meteorological data for a location.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            start_date: Start of period
            end_date: End of period
            
        Returns:
            List of daily meteorological observations
        """
        params = {
            "parameters": "T2M_MIN,T2M_MAX,T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR",
            "community": "AG",  # Agroclimatology
            "longitude": lon,
            "latitude": lat,
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "format": "JSON",
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            results = []
            properties = data.get("properties", {}).get("parameter", {})
            
            # Parse dates from response
            for date_str in properties.get("T2M", {}).keys():
                try:
                    d = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                    meteo = MeteoData(
                        date=d,
                        lat=lat,
                        lon=lon,
                        temp_min=properties["T2M_MIN"].get(date_str, 0),
                        temp_max=properties["T2M_MAX"].get(date_str, 0),
                        temp_mean=properties["T2M"].get(date_str, 0),
                        humidity=properties.get("RH2M", {}).get(date_str),
                        wind_speed=properties.get("WS2M", {}).get(date_str),
                        solar_radiation=properties.get("ALLSKY_SFC_SW_DWN", {}).get(date_str, 0),
                        precipitation=properties.get("PRECTOTCORR", {}).get(date_str, 0),
                    )
                    results.append(meteo)
                except (ValueError, KeyError):
                    continue
            
            return results
            
        except requests.RequestException:
            return []
