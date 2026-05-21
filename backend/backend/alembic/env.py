"""Alembic migration environment configuration."""

import asyncio
from typing import Any
from pathlib import Path
from logging.config import fileConfig

from alembic import context  # pyright: ignore[reportAttributeAccessIssue]
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from backend.core import path_conf
from backend.database.db import SQLALCHEMY_DATABASE_URL
from backend.common.model import MappedBase


if not Path(path_conf.ALEMBIC_VERSION_DIR).exists():
    Path(path_conf.ALEMBIC_VERSION_DIR).mkdir(parents=True)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# model's MetaData object
# for 'autogenerate' support
target_metadata = MappedBase.metadata

# other values from the config, defined by the needs of env.py,
sqlalchemy_url = alembic_config.attributes.get("sqlalchemy_url", SQLALCHEMY_DATABASE_URL)
if hasattr(sqlalchemy_url, "render_as_string"):
    sqlalchemy_url = sqlalchemy_url.render_as_string(hide_password=False)

alembic_config.set_main_option("sqlalchemy.url", str(sqlalchemy_url).replace("%", "%%"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations online."""

    def process_revision_directives(_context: Any, _revision: Any, directives: list[Any]) -> None:  # noqa: ANN401
        cmd_opts = getattr(alembic_config, "cmd_opts", None)
        if bool(getattr(cmd_opts, "autogenerate", False)):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        transaction_per_migration=True,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
