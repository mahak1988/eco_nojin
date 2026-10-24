import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models import AuditLog, User
from services.auth_legacy.repository import AuthLegacyRepository


def test_bootstrap_promotes_only_the_first_existing_account():
    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as connection:
            await connection.run_sync(User.__table__.create)
            await connection.run_sync(AuditLog.__table__.create)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            session.add_all([
                User(email="first@example.test", role="regular"),
                User(email="second@example.test", role="regular"),
            ])
            await session.commit()
            repository = AuthLegacyRepository(session)

            assert await repository.bootstrap_first_admin(
                "first@example.test", ("admin", "user_admin")
            )
            assert not await repository.bootstrap_first_admin(
                "second@example.test", ("admin", "user_admin")
            )
            first_user = await session.scalar(
                select(User).where(User.email == "first@example.test")
            )
            second_user = await session.scalar(
                select(User).where(User.email == "second@example.test")
            )
            audit = await session.scalar(select(AuditLog))

            assert first_user is not None and first_user.role == "admin"
            assert second_user is not None and second_user.role == "regular"
            assert audit is not None and audit.action == "bootstrap_first_admin"

        await engine.dispose()

    asyncio.run(run())
