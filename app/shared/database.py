"""Gestión de la conexión a la base de datos PostgreSQL."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from app.db import SyncSessionFactory

_session_factory: Callable[[], Session] = SyncSessionFactory


def set_session_factory(factory: Callable[[], Session]) -> None:
    """Override the sync session factory for tests or embedded runtimes."""

    global _session_factory
    _session_factory = factory


def reset_session_factory() -> None:
    """Restore the default sync session factory."""

    global _session_factory
    _session_factory = SyncSessionFactory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provee un contexto seguro para operaciones DB reutilizando el engine async."""

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive rollback
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI para inyectar sesiones transaccionales."""

    with session_scope() as session:
        yield session
