"""Database engine, declarative base, and session factory."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from data_catalog.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yields a database session and ensures it is closed after use.

    Usage::

        with get_session() as session:
            session.add(obj)
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
