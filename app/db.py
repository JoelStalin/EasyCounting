"""Database configuration helpers for async and sync usage."""
from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import make_url

from app.infra.settings import settings

ASYNC_DATABASE_URL = settings.sqlalchemy_async_url

engine_options: dict[str, object] = {"pool_pre_ping": True}
if ASYNC_DATABASE_URL.startswith("sqlite"):
    engine_options.update({"connect_args": {"check_same_thread": False}, "poolclass": NullPool})
else:
    engine_options.update({"pool_size": 10, "max_overflow": 20, "pool_timeout": 30})

engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, **engine_options)

AsyncSessionFactory = async_sessionmaker(bind=engine, expire_on_commit=False)

sync_url = make_url(ASYNC_DATABASE_URL)
drivername = sync_url.drivername
if "+" in drivername:
    dialect, _driver = drivername.split("+", 1)
else:
    dialect = drivername
if dialect.startswith("postgresql"):
    sync_drivername = "postgresql+psycopg"
else:
    sync_drivername = dialect
sync_engine_options: dict[str, object] = {"pool_pre_ping": True}
if sync_drivername.startswith("sqlite"):
    sync_engine_options.update({"connect_args": {"check_same_thread": False}, "poolclass": NullPool})
sync_engine = create_engine(sync_url.set(drivername=sync_drivername), **sync_engine_options)

SyncSessionFactory = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False, class_=Session)


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Yield an async session for request scoped usage."""

    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:  # pragma: no cover - defensive rollback
            await session.rollback()
            raise


@contextmanager
def get_sync_session() -> Iterator[Session]:
    """Yield a synchronous session backed by the same engine."""

    session = SyncSessionFactory()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive rollback
        session.rollback()
        raise
    finally:
        session.close()


async def check_database_connection() -> bool:
    """Ping the database to validate connectivity for readiness probes."""

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
