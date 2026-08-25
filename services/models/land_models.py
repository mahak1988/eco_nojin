from .base import Base


class LandProfileDB(Base):
    """
    جدول پروفایل زمین
    """
    __tablename__ = 'land_profiles'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), nullable=False) # احتمالاً به جدول پروژه‌ها ارجاع دارد
    location = Column(String(255), nullable=False) # مختصات نقطه به صورت 'lat,lng' یا JSON
    boundary = Column(Text) # چندضلعی به صورت GeoJSON یا WKT
    area_hectares = Column(Float)
    elevation_min = Column(Float)
    elevation_max = Column(Float)
    elevation_mean = Column(Float)
    slope_mean_degrees = Column(Float)
    aspect_dominant = Column(String(50))
    terrain_type = Column(String(100))
    drainage_pattern = Column(String(100))
    erosion_risk_level = Column(String(50))
    accessibility_score = Column(Float)
    land_capability_class = Column(String(50))
    development_constraints = Column(JSONB) # داده‌های پیچیده به صورت JSON
    dem_source = Column(String(100))
    dem_resolution = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TerrainAnalysisDB(Base):
    """
    جدول تحلیل توپوگرافی
    """
    __tablename__ = 'terrain_analyses'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    analysis_type = Column(String(100), nullable=False)
    result_data = Column(JSONB, nullable=False) # نتایج تحلیل
    method = Column(String(100), nullable=False)
    parameters = Column(JSONB) # پارامترهای استفاده شده در تحلیل
    created_at = Column(DateTime, server_default=func.now())


class LandCapabilityAssessmentDB(Base):
    """
    جدول ارزیابی قابلیت زمین
    """
    __tablename__ = 'land_capability_assessments'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    land_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey('land_profiles.id'), nullable=False)
    capability_class = Column(String(50), nullable=False)
    subclass = Column(String(50))
    limiting_factors = Column(JSONB) # عوامل محدود کننده
    suitable_land_uses = Column(JSONB) # کاربری‌های مناسب
    assessment_method = Column(String(100))
    confidence_level = Column(Float)
    assessed_by = Column(String(100))
    assessed_at = Column(DateTime, server_default=func.now())
