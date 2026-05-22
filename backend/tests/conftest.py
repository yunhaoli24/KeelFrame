"""Pytest fixtures for black-box API tests."""

import asyncio
from typing import Any
from dataclasses import field, dataclass
from collections.abc import Generator

import pytest
import psycopg
from alembic import command
from alembic.config import Config
from starlette.testclient import TestClient

from backend.main import app
from tests.utils.db import (
    TEST_SQLALCHEMY_DATABASE_URL,
    override_get_db,
    async_test_engine,
    override_get_db_transaction,
)
from backend.core.conf import settings
from backend.database.db import get_db, get_db_transaction, create_database_url
from backend.core.path_conf import ALEMBIC_DIR, ALEMBIC_INI


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_db_transaction] = override_get_db_transaction


PYTEST_USERNAME = "admin"
PYTEST_PASSWORD = "123456"  # noqa: S105
PYTEST_BASE_URL = f"http://testserver{settings.FASTAPI_API_V1_PATH}"


@dataclass
class DataStore:
    """Shared API test data."""

    admin_headers: dict[str, str] = field(default_factory=dict)
    test_headers: dict[str, str] = field(default_factory=dict)
    admin_user_id: int | None = None
    test_user_id: int | None = None
    created: dict[str, Any] = field(default_factory=dict)


def _reset_test_database() -> None:
    maintenance_url = create_database_url().set(database="postgres", drivername="postgresql")
    with (
        psycopg.connect(maintenance_url.render_as_string(hide_password=False), autocommit=True) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(f"DROP DATABASE IF EXISTS {settings.DATABASE_SCHEMA}_test WITH (FORCE)")
        cur.execute(f"CREATE DATABASE {settings.DATABASE_SCHEMA}_test")


def _clear_test_redis() -> None:
    from backend.database.redis import redis_client  # noqa: PLC0415

    async def clear() -> None:
        await redis_client.open()
        for prefix in (
            settings.TOKEN_REDIS_PREFIX,
            settings.TOKEN_EXTRA_INFO_REDIS_PREFIX,
            settings.TOKEN_ONLINE_REDIS_PREFIX,
            settings.TOKEN_REFRESH_REDIS_PREFIX,
            settings.JWT_USER_REDIS_PREFIX,
            settings.USER_LOCK_REDIS_PREFIX,
            settings.LOGIN_FAILURE_PREFIX,
        ):
            await redis_client.delete_prefix(prefix)
        await redis_client.aclose()

    asyncio.run(clear())


def _migrate_test_database() -> None:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.attributes["sqlalchemy_url"] = TEST_SQLALCHEMY_DATABASE_URL.render_as_string(hide_password=False)
    command.upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database() -> Generator[None]:
    """Rebuild and migrate the test database before API tests."""
    _clear_test_redis()
    _reset_test_database()
    _migrate_test_database()
    yield
    awaitable = async_test_engine.dispose()
    asyncio.run(awaitable)


@pytest.fixture(scope="session")
def client(migrated_test_database: None) -> Generator[TestClient]:
    """Create a test client for the app."""
    _ = migrated_test_database
    with TestClient(app, base_url=PYTEST_BASE_URL) as c:
        yield c


@pytest.fixture(scope="session")
def data_store() -> DataStore:
    """Create a shared API test data store."""
    return DataStore()


def login_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    """Login through the public API and return authorization headers."""
    response = client.post("/auth/login/swagger", params={"username": username, "password": password})
    response.raise_for_status()
    token = response.json()
    return {"Authorization": f"{token['token_type']} {token['access_token']}"}


@pytest.fixture(scope="session")
def token_headers(client: TestClient, data_store: DataStore) -> dict[str, str]:
    """Admin token headers."""
    data_store.admin_headers = login_headers(client, PYTEST_USERNAME, PYTEST_PASSWORD)
    user_response = client.get("/sys/users/me", headers=data_store.admin_headers)
    user_response.raise_for_status()
    data_store.admin_user_id = user_response.json()["data"]["id"]
    return data_store.admin_headers
