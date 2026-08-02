"""Tests for database engine and session factory."""

import contextlib

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ai_content_studio.database.session import get_session, make_engine, make_session_factory

DATABASE_URL = "sqlite:///:memory:"


def test_make_engine_returns_engine() -> None:
    engine = make_engine(DATABASE_URL)
    assert isinstance(engine, Engine)


def test_make_session_factory_returns_sessionmaker() -> None:
    engine = make_engine(DATABASE_URL)
    factory = make_session_factory(engine)
    assert isinstance(factory, sessionmaker)


def test_get_session_yields_session() -> None:
    engine = make_engine(DATABASE_URL)
    factory = make_session_factory(engine)
    gen = get_session(factory)
    session = next(gen)
    assert isinstance(session, Session)
    with contextlib.suppress(StopIteration):
        next(gen)
