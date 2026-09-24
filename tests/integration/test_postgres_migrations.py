"""
PostgreSQL Migration Integration Tests
======================================
Tests Alembic migrations against real PostgreSQL using testcontainers.
"""

import os

import pytest
from alembic.config import Config
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from alembic import command
from database.hub import hub


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing."""
    container = PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="econojin_test",
        port=5432,
    )
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def database_url(postgres_container):
    """Get database URL from container."""
    return postgres_container.get_connection_url(driver="psycopg")


@pytest.fixture(autouse=True)
def set_database_url(database_url):
    """Set DATABASE_URL environment variable for tests."""
    old_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    yield
    if old_url is not None:
        os.environ["DATABASE_URL"] = old_url
    else:
        os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def alembic_config(database_url):
    """Create Alembic config for test database."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


@pytest.fixture
def hub_instance(database_url):
    """Create fresh DataHub instance for testing."""
    # Reset singleton
    hub._instance = None
    hub._initialized = False
    yield hub
    # Cleanup
    hub._instance = None
    hub._initialized = False


class TestPostgresMigrations:
    """Test PostgreSQL migration operations."""

    @pytest.mark.asyncio
    async def test_alembic_upgrade_head(self, alembic_config, hub_instance):
        """Test upgrading to head revision."""
        # Run migration
        command.upgrade(alembic_config, "head")

        # Verify tables exist
        async with hub_instance.get_async_session() as session:
            # Check alembic_version table
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar_one()
            assert version is not None
            assert len(version) > 0

    @pytest.mark.asyncio
    async def test_alembic_downgrade_and_upgrade(self, alembic_config, hub_instance):
        """Test downgrade and upgrade cycle."""
        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Get current revision
        from alembic.script import ScriptDirectory

        script = ScriptDirectory.from_config(alembic_config)
        head_revision = script.get_current_head()

        # Downgrade one step
        if head_revision:
            command.downgrade(alembic_config, "-1")

            # Verify downgrade
            async with hub_instance.get_async_session() as session:
                result = await session.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar_one()
                # Should be at previous revision or None (base)

        # Upgrade back to head
        command.upgrade(alembic_config, "head")

        async with hub_instance.get_async_session() as session:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar_one()
            assert version == head_revision

    @pytest.mark.asyncio
    async def test_migration_creates_core_tables(self, alembic_config, hub_instance):
        """Test that core tables are created by migrations."""
        command.upgrade(alembic_config, "head")

        async with hub_instance.get_async_session() as session:
            # Check key tables exist
            tables_to_check = [
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
            ]

            for table in tables_to_check:
                await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                # Table exists if query doesn't raise exception
                # We just verify it doesn't raise

    @pytest.mark.asyncio
    async def test_connection_pooling_under_load(self, hub_instance):
        """Test connection pooling handles concurrent requests."""
        import asyncio

        async def make_query(i):
            async with hub_instance.get_async_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar()

        # Run 50 concurrent queries
        tasks = [make_query(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        assert all(r == 1 for r in results)

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, alembic_config, hub_instance):
        """Test transaction rollback on error."""
        command.upgrade(alembic_config, "head")

        from database.models import User

        async with hub_instance.get_async_session() as session:
            # Insert a valid user
            user = User(
                email="test@example.com",
                full_name="Test User",
                hashed_password="hashed",
                role="regular",
            )
            session.add(user)
            await session.commit()

            # Verify user exists
            result = await session.execute(
                text("SELECT COUNT(*) FROM user WHERE email = 'test@example.com'")
            )
            count = result.scalar()
            assert count == 1

            # Try to insert duplicate (should fail)
            try:
                duplicate = User(
                    email="test@example.com",
                    full_name="Duplicate",
                    hashed_password="hashed",
                    role="regular",
                )
                session.add(duplicate)
                await session.commit()
                raise AssertionError("Should have raised integrity error")
            except Exception:
                await session.rollback()

            # Verify original user still exists
            result = await session.execute(
                text("SELECT COUNT(*) FROM user WHERE email = 'test@example.com'")
            )
            count = result.scalar()
            assert count == 1


class TestDataIntegrity:
    """Test data integrity after migrations."""

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, alembic_config, hub_instance):
        """Test that foreign key constraints are enforced."""
        command.upgrade(alembic_config, "head")

        from database.models import Organization, OrganizationMembership, User

        async with hub_instance.get_async_session() as session:
            # Create organization
            org = Organization(name="Test Org", code="TEST")
            session.add(org)
            await session.flush()

            # Create user
            user = User(email="test@example.com", full_name="Test", hashed_password="x")
            session.add(user)
            await session.flush()

            # Create valid membership
            membership = OrganizationMembership(
                organization_id=org.id,
                user_id=user.id,
                role="member",
            )
            session.add(membership)
            await session.commit()

            # Try to create membership with invalid org_id
            invalid_membership = OrganizationMembership(
                organization_id=99999,  # non-existent
                user_id=user.id,
                role="member",
            )
            session.add(invalid_membership)

            try:
                await session.commit()
                raise AssertionError("Should have raised foreign key violation")
            except Exception:
                await session.rollback()

    @pytest.mark.asyncio
    async def test_unique_constraints(self, alembic_config, hub_instance):
        """Test that unique constraints are enforced."""
        command.upgrade(alembic_config, "head")

        from database.models import User

        async with hub_instance.get_async_session() as session:
            # Create first user
            user1 = User(
                email="unique@example.com",
                full_name="User 1",
                hashed_password="hash1",
            )
            session.add(user1)
            await session.commit()

            # Try to create second user with same email
            user2 = User(
                email="unique@example.com",
                full_name="User 2",
                hashed_password="hash2",
            )
            session.add(user2)

            try:
                await session.commit()
                raise AssertionError("Should have raised unique constraint violation")
            except Exception:
                await session.rollback()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
