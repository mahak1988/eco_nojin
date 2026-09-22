#!/usr/bin/env python3
"""Verify database migration schema."""

import os
import sys
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///test_migration.db")

def verify_schema():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    print(f"Database: {DATABASE_URL}")
    print(f"Tables found: {len(tables)}")

    # Core tables that should exist after migration
    required_tables = [
        "alembic_version",
        "user",
        "organization",
        "organization_membership",
        "audit_log",
        "ledger_entry",
        "carbon_project",
        "carbon_credit",
        "farm",
        "land_profile",
        "iot_device",
        "int_outbox_event",
        "fin_idempotency_key",
        "setting",
        "password_reset_token",
        "refresh_token",
        "oauth_connection",
        "api_key",
    ]

    missing = []
    for table in required_tables:
        if table not in tables:
            missing.append(table)
            print(f"  MISSING: {table}")
        else:
            print(f"  OK: {table}")

    # Check alembic_version
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"Alembic version: {version}")

    if missing:
        print(f"\nFAIL: {len(missing)} required tables missing")
        sys.exit(1)

    print(f"\nPASS: All {len(required_tables)} required tables present")
    sys.exit(0)


if __name__ == "__main__":
    verify_schema()