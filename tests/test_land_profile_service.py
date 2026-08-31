import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError
from database.models import User, LandProfile, Base
from services.land_profile_service import LandProfileCreate, create_land_profile

# ایجاد یک دیتابیس موقت در حافظه برای تست
@pytest.fixture(scope="function")
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_create_land_profile_success(test_db_session):
    """تست ایجاد موفق یک پروفایل زمین."""
    user = User(email="farmer@example.com", hashed_password="pw")
    test_db_session.add(user)
    test_db_session.commit()

    land_data = LandProfileCreate(
        name="My Valid Farm",
        location_lat=35.7,
        location_lon=51.4,
        area_ha=5.2,
        user_id=user.id
    )

    created_profile = create_land_profile(db=test_db_session, land_profile_data=land_data)

    assert created_profile.name == "My Valid Farm"
    assert created_profile.location_lat == 35.7
    assert created_profile.location_lon == 51.4
    assert created_profile.area_ha == 5.2
    assert created_profile.user_id == user.id

def test_create_land_profile_invalid_name(test_db_session):
    """تست ایجاد پروفایل با نام نامعتبر (خالی)."""
    user = User(email="farmer@example.com", hashed_password="pw")
    test_db_session.add(user)
    test_db_session.commit()

    with pytest.raises(ValueError, match="Name cannot be empty"):
        LandProfileCreate(
            name="",
            user_id=user.id
        )

def test_create_land_profile_invalid_whitespace_name(test_db_session):
    """تست ایجاد پروفایل با نام فقط شامل فضای خالی."""
    user = User(email="farmer@example.com", hashed_password="pw")
    test_db_session.add(user)
    test_db_session.commit()

    with pytest.raises(ValueError, match="Name cannot be empty"):
        LandProfileCreate(
            name="   ",
            user_id=user.id
        )

def test_create_land_profile_invalid_area(test_db_session):
    """تست ایجاد پروفایل با مساحت منفی."""
    user = User(email="farmer@example.com", hashed_password="pw")
    test_db_session.add(user)
    test_db_session.commit()

    with pytest.raises(ValueError, match="Area must be positive"):
        LandProfileCreate(
            name="Bad Farm",
            area_ha=-10.0,
            user_id=user.id
        )

def test_create_land_profile_invalid_coordinates(test_db_session):
    """تست ایجاد پروفایل با مختصات نامعتبر."""
    user = User(email="farmer@example.com", hashed_password="pw")
    test_db_session.add(user)
    test_db_session.commit()

    with pytest.raises(ValueError, match="Latitude must be between"):
        LandProfileCreate(
            name="Bad Coord Farm",
            location_lat=100.0, # نامعتبر
            user_id=user.id
        )

    with pytest.raises(ValueError, match="Longitude must be between"):
        LandProfileCreate(
            name="Bad Coord Farm 2",
            location_lon=-200.0, # نامعتبر
            user_id=user.id
        )

def test_create_land_profile_with_validation_error_on_model_level(test_db_session):
    """
    تست اینکه اگر مدل دیتابیس (که الان UniqueConstraint دارد)
    یک خطا بدهد (مثل نام تکراری برای یک کاربر)، چه اتفاقی می‌افتد.
    این بیشتر یک تست یکپارچه‌سازی است، اما در اینجا نیز قرار می‌گیرد.
    """
    user = User(email="farmer2@example.com", hashed_password="pw")
    test_db_session.add(user)
    test_db_session.commit()

    # ایجاد اولین پروفایل
    land_data1 = LandProfileCreate(name="Unique Farm", user_id=user.id)
    create_land_profile(db=test_db_session, land_profile_data=land_data1)

    # سعی در ایجاد پروفایل دوم با نام تکراری برای همان کاربر
    land_data2 = LandProfileCreate(name="Unique Farm", user_id=user.id)
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        create_land_profile(db=test_db_session, land_profile_data=land_data2)
        test_db_session.commit() # commit خطای IntegrityError را می‌دهد
    test_db_session.rollback() # برای ادامه تست‌ها