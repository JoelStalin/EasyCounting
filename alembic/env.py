from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.infra.settings import settings
from app.models import anecf, approval, audit, base, billing, invoice, receipt, rfce, storage, tenant, user

config = context.config

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        pass

config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", settings.sqlalchemy_async_url))

target_metadata = base.Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    connectable: AsyncEngine = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def run_with_connection() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_with_connection())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
