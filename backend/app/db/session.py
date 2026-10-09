from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    sqlite = settings.database_url.startswith("sqlite")
    connect_args = (
        {"check_same_thread": False}
        if sqlite
        else {"prepare_threshold": None}
    )
    kwargs = {"pool_pre_ping": True, "connect_args": connect_args}
    if settings.app_env == "production" and not sqlite:
        kwargs["poolclass"] = NullPool
    return create_engine(settings.database_url, **kwargs)


@lru_cache
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
