"""
Satellite Monitoring Service.

Orchestrates satellite data acquisition, processing, and storage
for land, soil, water, and crop monitoring.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from . import copernicus, sentinel2_provider, cds, nasa_power, open_meteo
from database.models import MonitoringDataDB, SessionLocal
from engine.hydroma.soil.moisture import estimate_soil_moisture
from engine.hydroma.crop.ndvi_analysis import calculate_ndvi_change
from engine.hydroma.water.surface_area import calculate_surface_area_change

logger = logging.getLogger(__name__)


class SatelliteDataSource(Enum):
    SENTINEL_2 = "sentinel-2"
    LANDSAT = "landsat"
    MODIS = "modis"
    ERA5 = "era5"
    NASA_POWER = "nasa_power"
    OPEN_METEO = "open_meteo"


@dataclass
class MonitoringRequest:
    """Request object for satellite monitoring."""
    project_id: str
    location: Dict[str, float]  # {"lat": float, "lon": float}
    start_date: datetime
    end_date: datetime
    data_sources: List[SatelliteDataSource]
    indices_to_calculate: List[str]  # e.g., ["NDVI", "NDWI", "SAR"]
    resolution_meters: Optional[int] = None
    cloud_cover_threshold: float = 20.0  # Percentage


@dataclass
class MonitoringResult:
    """Result object from satellite monitoring."""
    request: MonitoringRequest
    status: str  # 'completed', 'failed', 'partial'
    data_points: List[Dict[str, Any]]  # Raw data from providers
    calculated_indices: Dict[str, List[Dict[str, Any]]]  # NDVI over time, etc.
    quality_report: Dict[str, Any]
    error_message: Optional[str] = None


class SatelliteMonitoringService:
    """Main service class for handling satellite monitoring tasks."""

    def __init__(self):
        self.providers = {
            SatelliteDataSource.SENTINEL_2: sentinel2_provider,
            SatelliteDataSource.LANDSAT: None, # Placeholder
            SatelliteDataSource.MODIS: None, # Placeholder
            SatelliteDataSource.ERA5: cds, # Or open_meteo
            SatelliteDataSource.NASA_POWER: nasa_power,
            SatelliteDataSource.OPEN_METEO: open_meteo,
        }

    async def fetch_data_async(self, source: SatelliteDataSource, request: MonitoringRequest) -> List[Dict[str, Any]]:
        """Fetches data from a specific provider asynchronously."""
        logger.info(f"Fetching data from {source.value} for {request.project_id}")
        provider_module = self.providers[source]

        if source == SatelliteDataSource.SENTINEL_2:
            # Example call - adjust based on actual provider interface
            data = await asyncio.get_event_loop().run_in_executor(
                None, provider_module.fetch_sentinel2_data,
                request.location["lat"], request.location["lon"],
                request.start_date.strftime("%Y-%m-%d"),
                request.end_date.strftime("%Y-%m-%d"),
                request.cloud_cover_threshold
            )
            return data
        elif source in [SatelliteDataSource.ERA5, SatelliteDataSource.NASA_POWER, SatelliteDataSource.OPEN_METEO]:
            # Example for climate data
            data = await asyncio.get_event_loop().run_in_executor(
                None, provider_module.fetch_climate_data,
                request.location["lat"], request.location["lon"],
                request.start_date, request.end_date
            )
            return data
        else:
            logger.warning(f"Provider for {source.value} not implemented yet.")
            return []

    async def run_monitoring_request(self, request: MonitoringRequest) -> MonitoringResult:
        """Executes a monitoring request by fetching data from multiple sources."""
        logger.info(f"Starting monitoring request for project {request.project_id}")

        all_raw_data = []
        quality_flags = {}
        errors = []

        # Concurrently fetch data from all requested sources
        tasks = [self.fetch_data_async(source, request) for source in request.data_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, res in enumerate(results):
            source = request.data_sources[i]
            if isinstance(res, Exception):
                logger.error(f"Error fetching data from {source.value}: {res}")
                errors.append(f"{source.value}: {str(res)}")
                continue

            all_raw_data.extend(res)
            quality_flags[source.value] = {"fetched_items": len(res)}

        # Calculate indices (example for NDVI)
        calculated_indices = {}
        if "NDVI" in request.indices_to_calculate:
            try:
                ndvi_series = calculate_ndvi_change(all_raw_data)
                calculated_indices["NDVI"] = ndvi_series
            except Exception as e:
                logger.error(f"Error calculating NDVI: {e}")
                errors.append(f"NDVI calculation: {str(e)}")

        # Determine overall status
        status = "completed" if not errors else ("partial" if all_raw_data else "failed")

        # Create result object
        result = MonitoringResult(
            request=request,
            status=status,
            data_points=all_raw_data,
            calculated_indices=calculated_indices,
            quality_report=quality_flags,
            error_message="; ".join(errors) if errors else None
        )

        # Store raw data points in DB (example for the first data point)
        if all_raw_data:
            db_entry = MonitoringDataDB(
                project_id=request.project_id,
                monitoring_type="satellite",
                monitoring_date=datetime.utcnow().date(),
                location=f"{request.location['lat']},{request.location['lon']}", # Simplified
                data_source=",".join([s.value for s in request.data_sources]),
                data_quality_score=calculate_quality_score(quality_flags),
                measurement_data=all_raw_data[0], # Store first or aggregate
                quality_flags=quality_flags
            )
            db = SessionLocal()
            try:
                db.add(db_entry)
                db.commit()
                logger.info(f"Stored monitoring data for project {request.project_id} in DB.")
            except Exception as e:
                logger.error(f"Failed to store monitoring data in DB: {e}")
                db.rollback()
            finally:
                db.close()

        return result


def calculate_quality_score(quality_flags: Dict[str, Any]) -> float:
    """Calculates an overall data quality score."""
    # Simplified scoring based on number of items fetched per source
    scores = []
    for _, flags in quality_flags.items():
        count = flags.get("fetched_items", 0)
        # Score based on count (e.g., 10 items = 1.0, 1 item = 0.1)
        scores.append(min(1.0, count / 10.0))
    return sum(scores) / len(scores) if scores else 0.0


# Example usage (would be called from an API endpoint)
async def example_monitoring_run():
    req = MonitoringRequest(
        project_id="PROJ-123",
        location={"lat": 35.6892, "lon": 51.3890}, # Tehran
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        data_sources=[SatelliteDataSource.SENTINEL_2, SatelliteDataSource.NASA_POWER],
        indices_to_calculate=["NDVI"],
        resolution_meters=10,
        cloud_cover_threshold=30.0
    )

    service = SatelliteMonitoringService()
    result = await service.run_monitoring_request(req)
    print(f"Monitoring completed with status: {result.status}")
    print(f"NDVI series length: {len(result.calculated_indices.get('NDVI', []))}")