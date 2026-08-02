"""Database engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    """Create and return a SQLAlchemy engine for the given URL."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory bound to the given engine."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after use."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
