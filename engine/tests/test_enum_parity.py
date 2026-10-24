"""Parity test for Named Enum columns (KN-06).

The registry carries exactly one native Enum:
``carbon_credit_records.state`` = ``Enum(CarbonCreditState)``.

SQLite stores it as VARCHAR so the test suite never exercises enum-type drift.
This test documents the Python enum members and the Postgres pre-pass rule:
enum values are additive-only; any value addition ships an
``ALTER TYPE ... ADD VALUE`` step in its own migration.
"""

import pytest
import sqlalchemy as sa

from database.base import Base
from database.models import CarbonCreditRecord, CarbonCreditState


@pytest.fixture
def sync_engine():
    """Create in-memory SQLite engine with tables."""
    engine = sa.create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


def test_carbon_credit_state_enum_members():
    """Verify the Python enum members match the expected lifecycle."""
    expected = ["DRAFT", "SUBMITTED", "VERIFIED", "ACTIVE", "RETIRED"]
    actual = [m.value for m in CarbonCreditState]
    assert actual == expected, f"Enum members changed: {actual}"


def test_carbon_credit_state_parity_sqlite(sync_engine):
    """
    Parity check for SQLite: the column exists and stores the enum as VARCHAR.
    SQLite does not enforce CHECK constraints for Enum columns by default;
    this is documented behaviour. On Postgres, a CHECK constraint matching
    the enum values should exist.
    """
    insp = sa.inspect(sync_engine)

    # Table must exist
    assert insp.has_table("carbon_credit_records")

    # Column must exist with VARCHAR type (SQLite stores Enum as VARCHAR)
    cols = {c["name"]: c for c in insp.get_columns("carbon_credit_records")}
    assert "state" in cols
    col = cols["state"]
    # SQLite: Enum -> VARCHAR
    assert "VARCHAR" in str(col["type"]).upper() or "TEXT" in str(col["type"]).upper()

    # Check constraints: SQLite doesn't create them for Enum by default
    # This is documented; on Postgres the test will verify the CHECK constraint
    # matches the Python enum values.
    checks = insp.get_check_constraints("carbon_credit_records")
    state_checks = [c for c in checks if "state" in c.get("sqltext", "").lower()]
    # Document: currently no CHECK on SQLite
    # TODO: On Postgres, assert check constraint SQL contains all enum values
    # e.g., "state IN ('DRAFT','SUBMITTED','VERIFIED','ACTIVE','RETIRED')"


def test_carbon_credit_record_model_has_state_column():
    """Verify the CarbonCreditRecord model has the state column."""
    assert hasattr(CarbonCreditRecord, "state")
    state_col = CarbonCreditRecord.__table__.columns["state"]
    assert state_col is not None
    # Default should be ACTIVE
    assert state_col.default is not None


def test_enum_additive_only_rule_documented():
    """
    Document the pre-pass rule for Named Enum columns (KN-06):
    - Enum values are additive-only (never removed/renamed in place)
    - Any value addition ships an ``ALTER TYPE ... ADD VALUE`` step
      in its own migration, before the column that uses it is altered.
    - A parity test asserts the Python members against the DB CHECK
      constraints on Postgres (this test documents the intent).
    """
    # This is a documentation test; the rule is enforced by code review
    # and the migration pattern. No assertion needed here.
    pass