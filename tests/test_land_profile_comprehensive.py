import os
import structlog

logger = structlog.get_logger()
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from database.models import User, LandProfile, Base
from database.hub import hub

# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session # فقط برای دسترسی احتمالی به get_db، اگر نیاز شد

# ایجاد یک دیتابیس موقت در حافظه برای تست
@pytest.fixture(scope="function")
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_land_profile_table_schema(test_db_session):
    """بررسی ساختار جدول land_profiles."""
    inspector = inspect(test_db_session.bind)
    columns = {col['name']: col for col in inspector.get_columns('land_profiles')}
    
    assert 'id' in columns
    assert 'name' in columns
    assert 'location_lat' in columns
    assert 'location_lon' in columns
    assert 'area_ha' in columns
    assert 'created_at' in columns
    assert 'user_id' in columns # فیلد جدید اضافه شده
    
    # بررسی نوع فیلدها (به صورت کلی)
    assert columns['id']['type'].__class__.__name__ == 'VARCHAR' # SQLAlchemy برای String ممکن است VARCHAR استفاده کند
    assert columns['name']['type'].__class__.__name__ == 'VARCHAR'
    assert columns['location_lat']['type'].__class__.__name__ == 'FLOAT'
    assert columns['location_lon']['type'].__class__.__name__ == 'FLOAT'
    assert columns['area_ha']['type'].__class__.__name__ == 'FLOAT'
    assert columns['created_at']['type'].__class__.__name__ == 'DATETIME'
    assert columns['user_id']['type'].__class__.__name__ == 'VARCHAR'

def test_land_profile_creation_valid_data(test_db_session):
    """بررسی ایجاد یک پروفایل زمین با داده‌های معتبر."""
    user = User(email="farmer@example.com", hashed_password = os.environ.get("HASHED_PASSWORD", "hashed_pw"), full_name="John Doe")
    test_db_session.add(user)
    test_db_session.commit()

    land_profile = LandProfile(
        name="My Farm",
        location_lat=35.7,
        location_lon=51.4,
        area_ha=5.2,
        user_id=user.id
    )
    test_db_session.add(land_profile)
    test_db_session.commit()
    test_db_session.refresh(land_profile)

    assert land_profile.id is not None
    assert land_profile.name == "My Farm"
    assert land_profile.location_lat == 35.7
    assert land_profile.location_lon == 51.4
    assert land_profile.area_ha == 5.2
    assert land_profile.user_id == user.id
    assert isinstance(land_profile.created_at, datetime)
    # تأیید اینکه created_at یک datetime است (اما منطقه زمانی ممکن است در SQLite از دست برود)
    # این بخش را حذف یا تغییر می‌دهیم
    # assert land_profile.created_at.tzinfo is timezone.utc

def test_land_profile_creation_with_defaults(test_db_session):
    """بررسی اعمال مقادیر پیش‌فرض مانند created_at."""
    user = User(email="farmer2@example.com", hashed_password = os.environ.get("HASHED_PASSWORD", "hashed_pw2"))
    test_db_session.add(user)
    test_db_session.commit()

    land_profile = LandProfile(name="Default Farm", user_id=user.id)
    test_db_session.add(land_profile)
    test_db_session.commit()
    test_db_session.refresh(land_profile)

    # name و user_id الزامی هستند، باید مقدار داشته باشند
    assert land_profile.name == "Default Farm"
    assert land_profile.user_id == user.id
    
    # فیلدهای اختیاری باید None یا مقدار پیش‌فرض باشند
    assert land_profile.location_lat is None
    assert land_profile.location_lon is None
    assert land_profile.area_ha is None

    # created_at باید به صورت خودکار تنظیم شود
    assert land_profile.created_at is not None
    assert isinstance(land_profile.created_at, datetime)

def test_land_profile_user_relationship(test_db_session):
    """بررسی رابطه بین LandProfile و User."""
    user = User(email="owner@example.com", hashed_password = os.environ.get("HASHED_PASSWORD", "pw"))
    test_db_session.add(user)
    test_db_session.commit()

    lp1 = LandProfile(name="Farm Alpha", area_ha=10.0, user_id=user.id)
    lp2 = LandProfile(name="Farm Beta", area_ha=15.5, user_id=user.id)
    test_db_session.add(lp1)
    test_db_session.add(lp2)
    test_db_session.commit()

    # از طریق user به land profiles دسترسی پیدا کنید
    test_db_session.refresh(user)
    assert len(user.land_profiles) == 2
    profile_names = {lp.name for lp in user.land_profiles}
    assert "Farm Alpha" in profile_names
    assert "Farm Beta" in profile_names

    # از طریق land profile به user دسترسی پیدا کنید
    test_db_session.refresh(lp1)
    assert lp1.user.email == "owner@example.com"
    assert lp1.user.id == user.id

def test_land_profile_nullable_fields(test_db_session):
    """بررسی اینکه فیلدهای اختیاری می‌توانند None باشند."""
    user = User(email="flexible@example.com", hashed_password = os.environ.get("HASHED_PASSWORD", "pw"))
    test_db_session.add(user)
    test_db_session.commit()

    # ایجاد یک پروفایل فقط با فیلدهای الزامی
    land_profile = LandProfile(name="Minimal Farm", user_id=user.id)
    test_db_session.add(land_profile)
    test_db_session.commit()
    test_db_session.refresh(land_profile)

    assert land_profile.location_lat is None
    assert land_profile.location_lon is None
    assert land_profile.area_ha is None

def test_land_profile_cascading_orphaned_behavior(test_db_session):
    """
    بررسی رفتار پایگاه داده وقتی یک کاربر حذف می‌شود.
    با تغییر nullable=True برای user_id، حذف کاربر باید منجر به قرار گرفتن user_id
    در رکورد LandProfile به NULL شود.
    """
    user = User(email="to_be_deleted@example.com", hashed_password = os.environ.get("HASHED_PASSWORD", "pw"))
    test_db_session.add(user)
    test_db_session.commit()

    land_profile = LandProfile(name="Orphaned Farm", user_id=user.id)
    test_db_session.add(land_profile)
    test_db_session.commit()
    test_db_session.refresh(land_profile)

    # حذف کاربر
    test_db_session.delete(user)
    test_db_session.commit()

    # بازیابی پروفایل زمین
    orphaned_lp = test_db_session.query(LandProfile).filter(LandProfile.id == land_profile.id).first()
    assert orphaned_lp is not None
    # user_id باید None شده باشد
    assert orphaned_lp.user_id is None
    # اتصال lazy به کاربر نباید خطا بدهد، اما باید None باشد
    assert orphaned_lp.user is None
    assert orphaned_lp.name == "Orphaned Farm"
    logger.info(f"Orphaned LP Name: {orphaned_lp.name}, User ID: {orphaned_lp.user_id}, Related User: {orphaned_lp.user}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])