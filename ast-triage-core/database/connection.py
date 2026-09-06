"""
database/connection.py - SQLAlchemy 2.0 async engine and session factory.

Provides:
    - get_async_engine(): Creates/returns a cached AsyncEngine instance.
    - get_async_session(): Async context manager yielding AsyncSession instances.
    - init_db(): Creates all tables defined in the ORM models.

Usage:
    from database.connection import get_async_session, init_db

    # Initialize tables on startup
    await init_db()

    # Use sessions for queries
    async with get_async_session() as session:
        result = await session.execute(select(PullRequest))
"""
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.settings import get_settings
from database.models import Base


@lru_cache()
def get_async_engine() -> AsyncEngine:
    """
    Creates and returns a cached SQLAlchemy AsyncEngine.

    The engine is configured based on the DATABASE_URL setting.
    For SQLite, connect_args includes check_same_thread=False
    to allow async usage across threads.
    """
    settings = get_settings()
    connect_args = {}

    # SQLite requires check_same_thread=False for async usage
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args=connect_args,
    )
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Returns an async session factory bound to the async engine."""
    engine = get_async_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields an AsyncSession.

    Intended for use as a FastAPI dependency:
        session: AsyncSession = Depends(get_async_session)

    The session is automatically closed when the context exits.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Creates all database tables defined in the ORM models.

    Should be called once during application startup. Safe to call
    multiple times — existing tables are not modified.
    """
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
