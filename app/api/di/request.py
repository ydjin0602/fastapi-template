from collections.abc import AsyncGenerator

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import ConnectionPool
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession


class RequestProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def pg_session_scope(
        self,
        engine: AsyncEngine,
    ) -> AsyncGenerator[AsyncSession]:
        """DI Scope для AsyncGenerator[AsyncSession, None]."""
        async with AsyncSession(engine) as session:
            yield session

    # FIXME: Redis не нужен — удали этот скоуп вместе с redis_pool_scope
    #  из application.py
    @provide
    async def redis_scope(
        self,
        connection_pool: ConnectionPool,
    ) -> AsyncGenerator[Redis]:
        """DI Scope для Redis клиента."""
        async with Redis(connection_pool=connection_pool) as redis:
            yield redis
