"""Db."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio.session import AsyncSession

from backend.database.db import create_database_url, create_async_engine_and_session


TEST_SQLALCHEMY_DATABASE_URL = create_database_url(unittest=True)

async_test_engine, async_test_db_session = create_async_engine_and_session(TEST_SQLALCHEMY_DATABASE_URL)


async def override_get_db() -> AsyncGenerator[AsyncSession]:
    """Session 生成器."""
    async with async_test_db_session() as session:
        yield session


async def override_get_db_transaction() -> AsyncGenerator[AsyncSession]:
    """Transactional session generator."""
    async with async_test_db_session.begin() as session:
        yield session
