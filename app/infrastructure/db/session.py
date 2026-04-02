from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.db.base import Base


class DatabaseManager:
    def __init__(self, database_url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_all(self) -> None:
        from app.infrastructure.db import models  # noqa: F401

        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session
