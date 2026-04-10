from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

from arber.config.settings import get_settings


@dataclass
class _EngineHolder:
    engine: AsyncEngine | None = None
    sessionmaker: async_sessionmaker[_AsyncSession] | None = None


_holder = _EngineHolder()


def create_engine() -> AsyncEngine:
    if _holder.engine is not None:
        return _holder.engine

    settings = get_settings().db
    engine = create_async_engine(
        settings.async_dsn,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        echo=settings.echo,
        pool_pre_ping=True,
    )
    _holder.engine = engine
    _holder.sessionmaker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
    )
    return engine


def get_engine() -> AsyncEngine:
    if _holder.engine is None:
        return create_engine()
    return _holder.engine


def get_sessionmaker() -> async_sessionmaker[_AsyncSession]:
    if _holder.sessionmaker is None:
        create_engine()
    assert _holder.sessionmaker is not None
    return _holder.sessionmaker


async def dispose_engine() -> None:
    if _holder.engine is not None:
        await _holder.engine.dispose()
        _holder.engine = None
        _holder.sessionmaker = None
