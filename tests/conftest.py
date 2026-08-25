import pytest
import importlib

# پچ کردن توابع احراز هویت برای تست‌ها
auth_mod = importlib.import_module("services.api_gateway.auth")
auth_mod.verify_password = lambda plain, hashed: True
auth_mod.hash_password = lambda password: "dummyhash"

# import دیتابیس تست
from tests.test_db import SessionLocal, engine, TEST_SESSION_FACTORY

# جایگزینی SessionLocal و engine در database و database.config
import database
database.SessionLocal = SessionLocal
database.engine = engine

try:
    import database.config as db_config
    db_config.SessionLocal = SessionLocal
    db_config.engine = engine
except ImportError:
    pass

from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def client():
    """ساخت TestClient با override کردن get_db"""
    from services.api_gateway.main import app
    from database import get_db

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
