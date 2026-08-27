"""
Mobile Monitoring Service.

Handles data ingestion from mobile apps, including photos, GPS locations,
and user-submitted observations.
"""
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from database.config import SessionLocal
from database.models import MonitoringDataDB

logger = logging.getLogger(__name__)


class MobileReportType(Enum):
    CROP_CONDITION_PHOTO = "crop_condition_photo"
    SOIL_CONDITION_PHOTO = "soil_condition_photo"
    WATER_SOURCE_PHOTO = "water_source_photo"
    INFRASTRUCTURE_PHOTO = "infrastructure_photo"
    GENERAL_OBSERVATION = "general_observation"
    CITIZEN_REPORT = "citizen_report"


@dataclass
class MobileMonitoringReport:
    """Represents a single mobile monitoring submission."""
    project_id: str
    location: dict[str, float]  # {"lat": float, "lon": float}
    report_timestamp: datetime
    report_type: MobileReportType
    user_id: str
    photo_urls: list[str]  # List of image URLs
    text_description: str
    geo_verification_confirmed: bool  # e.g., via GPS lock, photo metadata
    quality_flag: str = "ok"  # "ok", "suspect", "unverified"
    additional_data: dict[str, Any] = None  # Any structured data submitted alongside


class MobileMonitoringService:
    """Service for handling mobile app data."""

    def __init__(self):
        pass

    def ingest_report(self, report: MobileMonitoringReport) -> bool:
        """Ingests a single mobile report and stores it."""
        logger.info(f"Ingesting mobile report from {report.user_id} for {report.project_id}")

        # Basic validation
        if not self._validate_report(report):
            logger.error(f"Invalid mobile report from {report.user_id}")
            return False

        # Process and potentially enrich data (e.g., calculate hash for photo uniqueness)
        processed_data = self._process_data(report)

        # Store in DB
        try:
            db_entry = MonitoringDataDB(
                project_id=report.project_id,
                monitoring_type="mobile",
                monitoring_date=report.report_timestamp.date(),
                location=f"{report.location['lat']},{report.location['lon']}", # Simplified
                data_source=f"mobile_app_user_{report.user_id}",
                data_quality_score=self._score_quality(report.quality_flag, report.geo_verification_confirmed),
                measurement_data=processed_data,
                quality_flags={
                    "original_flag": report.quality_flag,
                    "geo_verification_confirmed": report.geo_verification_confirmed,
                    "photo_count": len(report.photo_urls)
                }
            )
            db = SessionLocal()
            db.add(db_entry)
            db.commit()
            logger.info(f"Stored mobile report for project {report.project_id} in DB.")
            return True
        except Exception as e:
            logger.error(f"Failed to store mobile report in DB: {e}")
            db.rollback()
            return False

    def _validate_report(self, report: MobileMonitoringReport) -> bool:
        """Validates the structure and content of a mobile report."""
        required_fields = ["location", "report_timestamp", "report_type", "user_id"]
        for field in required_fields:
            if not hasattr(report, field) or getattr(report, field) is None:
                return False
        if not isinstance(report.location, dict) or 'lat' not in report.location or 'lon' not in report.location:
            return False
        # Check if photos exist if report type implies photos
        if report.report_type in [
            MobileReportType.CROP_CONDITION_PHOTO,
            MobileReportType.SOIL_CONDITION_PHOTO,
            MobileReportType.WATER_SOURCE_PHOTO,
            MobileReportType.INFRASTRUCTURE_PHOTO
        ] and not report.photo_urls:
            return False
        return True

    def _process_data(self, report: MobileMonitoringReport) -> dict[str, Any]:
        """Processes raw mobile data, e.g., generating hashes for images."""
        processed = {
            "report_type": report.report_type.value,
            "text_description": report.text_description,
            "photo_hashes": [hashlib.sha256(url.encode()).hexdigest() for url in report.photo_urls],
            "additional_data": report.additional_data or {},
            "submitted_by_user_id": report.user_id,
            "geo_verification_confirmed": report.geo_verification_confirmed
        }
        return processed

    def _score_quality(self, flag: str, geo_confirmed: bool) -> float:
        """Calculates a quality score based on flag and verification."""
        base_score = {"ok": 1.0, "suspect": 0.5, "unverified": 0.3}.get(flag, 0.5)
        geo_bonus = 0.2 if geo_confirmed else 0.0
        return min(1.0, base_score + geo_bonus)


# Example usage
def example_mobile_ingest():
    report = MobileMonitoringReport(
        project_id="PROJ-125",
        location={"lat": 37.0, "lon": 53.0},
        report_timestamp=datetime.now(),
        report_type=MobileReportType.CROP_CONDITION_PHOTO,
        user_id="USER_MOBILE_001",
        photo_urls=["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
        text_description="Wheat field looks healthy, some weeds present.",
        geo_verification_confirmed=True,
        quality_flag="ok",
        additional_data={"growth_stage": "flowering", "estimated_yield": "high"}
    )

    service = MobileMonitoringService()
    success = service.ingest_report(report)
    print(f"Mobile report ingestion successful: {success}")
