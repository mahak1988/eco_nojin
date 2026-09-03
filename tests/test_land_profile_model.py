import os
import structlog

logger = structlog.get_logger()
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, LandProfile, Base # _uuid از اینجا وارد می‌شود
from database.hub import hub

# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session # در صورت نیاز به get_db

# ایجاد یک دیتابیس موقت در حافظه برای تست
@pytest.fixture(scope="module")
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_land_profile_creation_and_relationship(test_db_session):
    # ایجاد یک کاربر جدید
    user = User(email="test@example.com", hashed_password = os.environ.get("HASHED_PASSWORD", "hashed_pw"), full_name="Test User")
    test_db_session.add(user)
    test_db_session.commit()

    # ایجاد یک پروفایل زمین برای این کاربر
    land_profile = LandProfile(
        name="Test Farm",
        location_lat=35.6892,
        location_lon=51.3890,
        area_ha=10.5,
        user_id=user.id  # اتصال به کاربر
    )
    test_db_session.add(land_profile)
    test_db_session.commit()

    # بازیابی پروفایل زمین و بررسی رابطه
    retrieved_profile = test_db_session.query(LandProfile).filter(LandProfile.name == "Test Farm").first()
    
    assert retrieved_profile is not None
    assert retrieved_profile.user_id == user.id
    assert retrieved_profile.user.email == "test@example.com"
    assert len(user.land_profiles) == 1
    assert user.land_profiles[0].name == "Test Farm"

    logger.info("Test passed: LandProfile model and relationship work correctly.")
