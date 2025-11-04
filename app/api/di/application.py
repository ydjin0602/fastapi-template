from collections.abc import AsyncGenerator

from dishka import Provider
from dishka import Scope
from dishka import provide
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import config


class ApplicationProvider(Provider):
    scope = Scope.APP

    @provide
    async def pg_engine_scope(self) -> AsyncGenerator[AsyncEngine]:
        """DI Scope для AsyncEngine."""
        engine = create_async_engine(
            config.postgres.database_uri,
            pool_size=config.postgres.pool_size,
            max_overflow=config.postgres.overflow_pool_size,
            pool_pre_ping=True,
            # echo=True,
        )
        yield engine
        await engine.dispose()
