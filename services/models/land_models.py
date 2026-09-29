from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from database.base import Base


class TerrainAnalysisDB(Base):
    """
    جدول تحلیل توپوگرافی
    """

    __tablename__ = "terrain_analyses"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey("land_profiles.id"), nullable=False)
    analysis_type = Column(String(100), nullable=False)
    result_data = Column(JSONB, nullable=False)  # نتایج تحلیل
    method = Column(String(100), nullable=False)
    parameters = Column(JSONB)  # پارامترهای استفاده شده در تحلیل
    created_at = Column(DateTime, server_default=func.now())


class LandCapabilityAssessmentDB(Base):
    """
    جدول ارزیابی قابلیت زمین
    """

    __tablename__ = "land_capability_assessments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey("land_profiles.id"), nullable=False)
    capability_class = Column(String(50), nullable=False)
    subclass = Column(String(50))
    limiting_factors = Column(JSONB)  # عوامل محدود کننده
    suitable_land_uses = Column(JSONB)  # کاربری‌های مناسب
    assessment_method = Column(String(100))
    confidence_level = Column(Float)
    assessed_by = Column(String(100))
    assessed_at = Column(DateTime, server_default=func.now())
