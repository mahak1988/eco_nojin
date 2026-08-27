"""
Field Monitoring Service.

Handles ingestion and processing of data from field sensors, surveys,
and citizen science reports.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from database.config import SessionLocal
from database.models import MonitoringDataDB
from engine.hydroma.soil.health import calculate_soil_health_index
from engine.hydroma.water.quality import assess_water_quality

logger = logging.getLogger(__name__)


class FieldDataType(Enum):
    SOIL_MOISTURE = "soil_moisture"
    SOIL_NUTRIENTS = "soil_nutrients"
    SOIL_PH_EC = "soil_ph_ec"
    WATER_LEVEL = "water_level"
    WATER_QUALITY = "water_quality"
    CROP_HEIGHT = "crop_height"
    BIOMASS = "biomass"
    CITIZEN_REPORT = "citizen_report"


@dataclass
class FieldMonitoringReport:
    """Represents a single field monitoring data point."""
    project_id: str
    location: dict[str, float]  # {"lat": float, "lon": float}
    report_date: datetime
    data_type: FieldDataType
    data_payload: dict[str, Any]  # Actual measurements
    reporter_id: str  # Could be sensor ID, user ID, etc.
    quality_flag: str = "ok"  # "ok", "suspect", "error"
    notes: str = ""


class FieldMonitoringService:
    """Service for handling field data."""

    def __init__(self):
        pass

    def ingest_report(self, report: FieldMonitoringReport) -> bool:
        """Ingests a single field report and stores it."""
        logger.info(f"Ingesting field report from {report.reporter_id} for {report.project_id}")

        # Basic validation
        if not self._validate_report(report):
            logger.error(f"Invalid report from {report.reporter_id}")
            return False

        # Process and potentially enrich data (e.g., calculate indices)
        processed_data = self._process_data(report)

        # Store in DB
        try:
            db_entry = MonitoringDataDB(
                project_id=report.project_id,
                monitoring_type="field",
                monitoring_date=report.report_date.date(),
                location=f"{report.location['lat']},{report.location['lon']}", # Simplified
                data_source=report.reporter_id,
                data_quality_score=self._score_quality(report.quality_flag),
                measurement_data=processed_data,
                quality_flags={"original_flag": report.quality_flag, "validation_passed": True}
            )
            db = SessionLocal()
            db.add(db_entry)
            db.commit()
            logger.info(f"Stored field report for project {report.project_id} in DB.")
            return True
        except Exception as e:
            logger.error(f"Failed to store field report in DB: {e}")
            db.rollback()
            return False

    def _validate_report(self, report: FieldMonitoringReport) -> bool:
        """Validates the structure and content of a report."""
        required_fields = ["location", "report_date", "data_type", "data_payload"]
        for field in required_fields:
            if not hasattr(report, field) or getattr(report, field) is None:
                return False
        if not isinstance(report.location, dict) or 'lat' not in report.location or 'lon' not in report.location:
            return False
        return True

    def _process_data(self, report: FieldMonitoringReport) -> dict[str, Any]:
        """Applies calculations or enrichments to raw data."""
        processed = report.data_payload.copy()

        # Example: Calculate soil health index if soil data is present
        if report.data_type == FieldDataType.SOIL_NUTRIENTS:
            ph = processed.get("ph")
            om = processed.get("organic_matter_pct")
            n = processed.get("nitrogen_ppm")
            p = processed.get("phosphorus_ppm")
            k = processed.get("potassium_ppm")
            if all(v is not None for v in [ph, om, n, p, k]):
                health_idx = calculate_soil_health_index(ph, om, n, p, k)
                processed["soil_health_index"] = health_idx

        # Example: Assess water quality if water data is present
        if report.data_type == FieldDataType.WATER_QUALITY:
            ph = processed.get("ph")
            ec = processed.get("electrical_conductivity_dsm")
            tds = processed.get("tds_ppm")
            if all(v is not None for v in [ph, ec, tds]):
                quality_class = assess_water_quality(ph, ec, tds)
                processed["quality_class"] = quality_class

        return processed

    def _score_quality(self, flag: str) -> float:
        """Converts a quality flag to a numerical score."""
        mapping = {"ok": 1.0, "suspect": 0.5, "error": 0.0}
        return mapping.get(flag, 0.5) # Default to 0.5 if flag is unknown


# Example usage
def example_field_ingest():
    report = FieldMonitoringReport(
        project_id="PROJ-124",
        location={"lat": 36.0, "lon": 52.0},
        report_date=datetime.now(),
        data_type=FieldDataType.SOIL_NUTRIENTS,
        data_payload={"ph": 6.8, "organic_matter_pct": 2.1, "nitrogen_ppm": 120, "phosphorus_ppm": 45, "potassium_ppm": 180},
        reporter_id="SENSOR_SOIL_001",
        quality_flag="ok",
        notes="Routine measurement"
    )

    service = FieldMonitoringService()
    success = service.ingest_report(report)
    print(f"Field report ingestion successful: {success}")
