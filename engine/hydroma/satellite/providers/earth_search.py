"""Earth Search STAC API provider for Sentinel-2 data.

This provider uses the public Element 84 STAC API which requires no API key.
Data: Sentinel-2 L2A (10m resolution, 5-day revisit)
Source: https://earth-search.aws.element84.com/v1
"""
import requests
import numpy as np
from datetime import date, datetime, timezone
from typing import Optional
from .base import SatelliteProvider, SatelliteTile

# Public STAC endpoint - no API key required
EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
SENTINEL2_COLLECTION = "sentinel-2-l2a"


class EarthSearchProvider(SatelliteProvider):
    """Fetches Sentinel-2 data from public STAC API."""
    
    BAND_MAPPING = {
        "red": "red",           # Band 4 (665nm)
        "green": "green",       # Band 3 (560nm)
        "blue": "blue",         # Band 2 (490nm)
        "nir": "nir",           # Band 8 (842nm)
        "nir08": "nir08",       # Band 8A (865nm)
        "swir16": "swir16",     # Band 11 (1610nm)
        "swir22": "swir22",     # Band 12 (2190nm)
        "scl": "scl",           # Scene Classification
    }
    
    @property
    def available_bands(self) -> list[str]:
        return list(self.BAND_MAPPING.keys())
    
    def search(
        self,
        lat: float,
        lon: float,
        start_date: date,
        end_date: date,
        max_cloud_cover: float = 20.0,
        limit: int = 10,
    ) -> list[dict]:
        """Search for Sentinel-2 tiles covering the given point.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            start_date: Start of search window
            end_date: End of search window
            max_cloud_cover: Maximum acceptable cloud cover (%)
            limit: Maximum number of results
            
        Returns:
            List of STAC items (metadata only, no pixel data yet)
        """
        # Create small bounding box around point (approx 1km)
        buffer = 0.005  # ~500m
        bbox = [lon - buffer, lat - buffer, lon + buffer, lat + buffer]
        
        payload = {
            "collections": [SENTINEL2_COLLECTION],
            "bbox": bbox,
            "datetime": f"{start_date.isoformat()}/{end_date.isoformat()}",
            "query": {
                "eo:cloud_cover": {"lt": max_cloud_cover}
            },
            "sortby": [{"field": "datetime", "direction": "desc"}],
            "limit": limit,
        }
        
        try:
            response = requests.post(
                f"{EARTH_SEARCH_URL}/search",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("features", [])
        except requests.RequestException as e:
            # Graceful degradation: return empty list
            return []
    
    def fetch_tile(self, item_id: str) -> Optional[SatelliteTile]:
        """Fetch a specific STAC item by ID.
        
        Note: For real production, you would download the GeoTIFF assets.
        This is a simplified mock that returns synthetic data for demo.
        """
        # In production: download actual GeoTIFF from AWS S3
        # For MVP: return synthetic data representing typical Sentinel-2 values
        size = 64  # 64x64 pixel tile
        np.random.seed(hash(item_id) % (2**32))
        
        bands = {
            "red": np.random.uniform(200, 800, (size, size)),
            "green": np.random.uniform(300, 1000, (size, size)),
            "blue": np.random.uniform(150, 600, (size, size)),
            "nir": np.random.uniform(1500, 4000, (size, size)),  # High NIR for vegetation
            "swir16": np.random.uniform(500, 2000, (size, size)),
        }
        
        return SatelliteTile(
            provider="earth_search",
            collection=SENTINEL2_COLLECTION,
            datetime=datetime.now(timezone.utc),
            bbox=(0, 0, 1, 1),
            cloud_cover=5.0,
            bands=bands,
            data_source="simulated",  # synthetic demo data, NOT real imagery
        )
