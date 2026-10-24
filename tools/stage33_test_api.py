
import requests

try:
    resp = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": 26.0,
            "longitude": 85.0,
            "start_date": "2017-01-01",
            "end_date": "2017-01-05",
            "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,shortwave_radiation_sum",
            "timezone": "UTC",
        },
        timeout=15,
    )
    print(f"Status: {resp.status_code}")
    daily = resp.json().get("daily", {})
    print(f"Keys: {list(daily.keys())}")
    print(f"Dates: {daily.get('time', [])[:3]}")
    print(f"Tmin: {daily.get('temperature_2m_min', [])[:3]}")
    print(f"SW: {daily.get('shortwave_radiation_sum', [])[:3]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
