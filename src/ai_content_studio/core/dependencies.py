"""FastAPI dependency providers for settings and database session."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ai_content_studio.core.config import get_settings
from ai_content_studio.core.settings import Settings
from ai_content_studio.database.session import get_session, make_engine, make_session_factory


def get_db() -> Generator[Session, None, None]:
    """Yield a database session using a lazily created engine and session factory."""
    engine = make_engine(get_settings().database_url)
    factory = make_session_factory(engine)
    yield from get_session(factory)


SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Session, Depends(get_db)]
