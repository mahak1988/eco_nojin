"""مدل‌های اصلی دیتابیس - نسخه کامل"""
from sqlalchemy import Text, JSON, Column, String, Boolean, DateTime, Float, Integer
from database.base import Base
from datetime import datetime, timezone
import uuid

def _uuid():
    return str(uuid.uuid4())



def generate_uuid():
    """Generate a UUID string for primary keys"""
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, nullable=True)

    language = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    role = Column(String, nullable=False, default="farmer")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class LandProfile(Base):
    __tablename__ = "land_profiles"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    area_ha = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- Placeholder classes for any missing names ---
class AuditLog(Base):
    __tablename__ = "auditlog"
    id = Column(Integer, primary_key=True)
    detail = Column(String)
    role = Column(String)
    actor_id = Column(String)
    actor_email = Column(String)
    action = Column(String)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    details = Column(JSON)
    resource_id = Column(String(100))
    resource_type = Column(String(50))
    target = Column(String)
    user_id = Column(String)
    amount = Column(Float)
    token = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

class EcoWallet(Base):
    __tablename__ = "ecowallet"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    token = Column(String)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TopographyAnalysisResult(Base):
    __tablename__ = "topography_analysis_results"
    id = Column(Integer, primary_key=True)
    profile_id = Column(String)
    data = Column(String)

class CarbonProject(Base):
    __tablename__ = "carbon_projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class SoilAnalysis(Base):
    __tablename__ = "soil_analyses"
    id = Column(Integer, primary_key=True)
    farm_id = Column(String)

class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    name = Column(String)

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)

class SatelliteAnalysis(Base):
    __tablename__ = "satellite_analyses"
    id = Column(Integer, primary_key=True)
    farm_id = Column(String)
    ndvi = Column(Float)

# سایر کلاس‌های placeholder
class SimulationRun(Base):
    """Persisted result of a HyDroMa simulation chain run (RUSLE > AquaCrop > RothC)."""
    __tablename__ = "simulationrun"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(64), index=True)
    scenario = Column(String(120), default="baseline")
    area_ha = Column(Float)
    status = Column(String(32), default="completed")
    outputs = Column(JSON)
    message = Column(Text)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<SimulationRun id={self.id} site='{self.site_id}' status='{self.status}'>"


for _name in [
    "NojinApplicationPlanDB", "NojinCalibrationRecordDB",
    "ModelVersionDB", "ScenarioResultDB", "ScenarioRun", "MRVObservation",
    "DecisionRecommendationDB", "OptimizationResultDB", "MonitoringDataDB",
    "NojinFieldTrialDB", "ScenarioDB", "Product", "EcoTransaction",
    "CalibrationRecordDB",
]:
    globals()[_name] = type(_name, (Base,), {
        "__tablename__": _name.lower(),
        "id": Column(Integer, primary_key=True),
        "created_at": Column(DateTime, default=lambda: datetime.now(timezone.utc)),
    })


class ErrorLog(Base):
    __tablename__ = "errorlog"
    id = Column(Integer, primary_key=True)
    path = Column(String(500))
    method = Column(String(10))
    status = Column(Integer)
    message = Column(Text)
    acked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))



class Setting(Base):
    """System-wide settings storage (key-value pairs)"""
    __tablename__ = "settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String, nullable=True)
    category = Column(String, default='general')  # general, security, ai, telegram, etc.
    is_secret = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Setting key='{self.key}'>"
