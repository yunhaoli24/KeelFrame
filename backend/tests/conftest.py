"""Pytest fixtures for black-box API tests."""

import os
import sys
import time
import asyncio
import subprocess
from typing import Any
from pathlib import Path
from dataclasses import field, dataclass
from collections.abc import Generator

import pytest
import psycopg
from alembic import command
from redis.asyncio import Redis
from alembic.config import Config
from sqlalchemy.engine import make_url
from starlette.testclient import TestClient

from backend.main import app
from backend.core.conf import settings
from backend.database.db import async_engine, create_database_url
from backend.core.path_conf import ALEMBIC_DIR, ALEMBIC_INI


PYTEST_USERNAME = "admin"
PYTEST_PASSWORD = "123456"  # noqa: S105
PYTEST_BASE_URL = f"http://testserver{settings.FASTAPI_API_V1_PATH}"
TEST_SQLALCHEMY_DATABASE_URL = make_url(
    f"{settings.DATABASE_TYPE}+psycopg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@"
    f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_SCHEMA}"
)


@dataclass
class DataStore:
    """Shared API test data."""

    admin_headers: dict[str, str] = field(default_factory=dict)
    test_headers: dict[str, str] = field(default_factory=dict)
    backend_settings: dict[str, str] = field(default_factory=dict)
    admin_user_id: int | None = None
    test_user_id: int | None = None
    created: dict[str, Any] = field(default_factory=dict)


def _reset_test_database() -> None:
    _drop_test_database()
    test_database = TEST_SQLALCHEMY_DATABASE_URL.database
    assert test_database
    maintenance_url = create_database_url().set(database="postgres", drivername="postgresql")
    with (
        psycopg.connect(maintenance_url.render_as_string(hide_password=False), autocommit=True) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(f"CREATE DATABASE {test_database}")


def _drop_test_database() -> None:
    maintenance_url = create_database_url().set(database="postgres", drivername="postgresql")
    test_database = TEST_SQLALCHEMY_DATABASE_URL.database
    assert test_database
    with (
        psycopg.connect(maintenance_url.render_as_string(hide_password=False), autocommit=True) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(f"DROP DATABASE IF EXISTS {test_database} WITH (FORCE)")


def _clear_test_redis() -> None:
    from backend.database.redis import redis_client  # noqa: PLC0415

    async def clear() -> None:
        await redis_client.open()
        await redis_client.flushdb()
        await redis_client.aclose()

    asyncio.run(clear())


def _clear_test_celery_broker() -> None:
    async def clear() -> None:
        redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.CELERY_BROKER_REDIS_DATABASE,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            decode_responses=True,
        )
        try:
            await redis.flushdb()
        finally:
            await redis.aclose()

    asyncio.run(clear())


def _start_test_celery_process(command: list[str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "backend.app.task.celery:celery_app",
            *command,
        ],
        cwd=Path.cwd(),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _start_test_celery_worker() -> subprocess.Popen[bytes]:
    return _start_test_celery_process(
        [
            "worker",
            "--pool=threads",
            "--concurrency=2",
            "--loglevel=WARNING",
            "--hostname=fba-test-worker@%h",
        ]
    )


def _wait_for_test_celery_worker(worker: subprocess.Popen[bytes], headers: dict[str, str]) -> None:
    deadline = time.monotonic() + 20
    with TestClient(app, base_url=PYTEST_BASE_URL) as client:
        while time.monotonic() < deadline:
            if worker.poll() is not None:
                output = (worker.stdout.read() if worker.stdout else b"").decode(errors="replace")
                msg = f"Celery test worker exited before becoming ready:\n{output}"
                raise RuntimeError(msg)
            response = client.get("/tasks/health", headers=headers)
            if response.status_code == 200 and response.json().get("data") is True:
                return
            time.sleep(0.5)

    _stop_test_celery_process(worker)
    msg = "Celery test worker did not become ready within 20 seconds"
    raise RuntimeError(msg)


def _start_test_celery_beat() -> subprocess.Popen[bytes]:
    return _start_test_celery_process(
        [
            "beat",
            "--loglevel=WARNING",
            "--max-interval=1",
        ]
    )


def _stop_test_celery_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _migrate_test_database() -> None:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.attributes["sqlalchemy_url"] = TEST_SQLALCHEMY_DATABASE_URL.render_as_string(hide_password=False)
    command.upgrade(config, "head")


def _disable_seed_task_schedulers() -> None:
    url = TEST_SQLALCHEMY_DATABASE_URL.set(drivername="postgresql")
    with psycopg.connect(url.render_as_string(hide_password=False)) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE task_scheduler SET enabled = false")
        conn.commit()


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database() -> Generator[None]:
    """Rebuild and migrate the test database before API tests."""
    _clear_test_redis()
    _clear_test_celery_broker()
    _reset_test_database()
    _migrate_test_database()
    _disable_seed_task_schedulers()
    with TestClient(app, base_url=PYTEST_BASE_URL) as readiness_client:
        headers = login_headers(readiness_client, PYTEST_USERNAME, PYTEST_PASSWORD)
    worker = _start_test_celery_worker()
    _wait_for_test_celery_worker(worker, headers)
    asyncio.run(async_engine.dispose())
    beat = _start_test_celery_beat()
    try:
        yield
    finally:
        _stop_test_celery_process(beat)
        _stop_test_celery_process(worker)
        awaitable = async_engine.dispose()
        asyncio.run(awaitable)
        _clear_test_redis()
        _clear_test_celery_broker()
        _drop_test_database()


@pytest.fixture(scope="session")
def client(migrated_test_database: None) -> Generator[TestClient]:
    """Create a test client for the app."""
    _ = migrated_test_database
    with TestClient(app, base_url=PYTEST_BASE_URL) as c:
        yield c


@pytest.fixture(scope="session")
def data_store() -> DataStore:
    """Create a shared API test data store."""
    return DataStore(
        backend_settings={
            "api_v1_path": settings.FASTAPI_API_V1_PATH,
            "object_storage_default_endpoint": settings.OBJECT_STORAGE_DEFAULT_ENDPOINT,
            "object_storage_default_access_key": settings.OBJECT_STORAGE_DEFAULT_ACCESS_KEY,
            "object_storage_default_secret_key": settings.OBJECT_STORAGE_DEFAULT_SECRET_KEY,
            "object_storage_default_bucket": settings.OBJECT_STORAGE_DEFAULT_BUCKET,
            "object_storage_default_region": settings.OBJECT_STORAGE_DEFAULT_REGION,
        }
    )


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
