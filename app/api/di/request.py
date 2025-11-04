from collections.abc import AsyncGenerator

from dishka import Provider
from dishka import Scope
from dishka import provide
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
