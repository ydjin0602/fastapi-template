"""Base configuration for schemathesis tests with testcontainers and dishka integration."""

import asyncio
import os

from collections.abc import AsyncGenerator
from collections.abc import Generator

import pytest
import schemathesis

from asgi_lifespan import LifespanManager
from dishka import Provider
from dishka import Scope
from dishka import make_async_container
from dishka import provide
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient
from schemathesis.specs.openapi.schemas import BaseOpenAPISchema
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer

from app.api.di.request import RequestProvider
from app.api.di.usecase import UsecaseProvider
from app.api.utils.enums.env_enum import EnvEnum
from app.api.utils.sqlalchemy.base_db_model import BaseDBModel
from app.main import get_fastapi_app
from tests.consts import BASE_URL

# Set environment for testing
os.environ['ENVIRONMENT'] = EnvEnum.PYTEST.value


@pytest.fixture(scope='session')
def pg_container_url() -> Generator[str]:
    """Initialize PostgreSQL test container."""
    with PostgresContainer(image='postgres:16-alpine') as postgres:
        yield postgres.get_connection_url(driver='asyncpg')


@pytest.fixture(scope='session')
async def pg_engine(pg_container_url: str) -> AsyncGenerator[AsyncEngine]:
    """Create test database engine."""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(pg_container_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope='session', autouse=False)
async def db_init(pg_engine: AsyncEngine):
    """Фикстура для скидывания состояния БД.

    Args:
        pg_engine: AsyncEngine
    """
    meta = BaseDBModel.metadata

    async with pg_engine.connect() as conn:
        await conn.execute(text('CREATE SCHEMA IF NOT EXISTS template_schema;'))
        await conn.run_sync(meta.create_all)

        await conn.commit()


@pytest.fixture(scope='function')
async def clear_db(pg_engine: AsyncEngine, db_init):
    """Фикстура для транкейта состояния БД."""
    yield
    meta = BaseDBModel.metadata
    async with pg_engine.connect() as conn:
        for table in reversed(meta.tables.values()):
            await conn.execute(
                text(
                    f'truncate table {table.schema}.{table.name} restart identity cascade;'
                )
            )

        await conn.commit()


@pytest.fixture(scope='function')
async def session(pg_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Create test database session."""
    async with AsyncSession(bind=pg_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(scope='session')
def event_loop():
    """Create event loop for pytest-asyncio."""
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='function')
async def test_app(pg_engine: AsyncEngine) -> AsyncGenerator[FastAPI]:
    """Create test FastAPI app."""

    class TestApplicationProvider(Provider):
        """Test provider that overrides database engine for testing."""

        scope = Scope.APP

        @provide
        async def pg_engine_scope(self) -> AsyncGenerator[AsyncEngine]:
            """Override DI scope to use test engine from fixture."""
            yield pg_engine

    test_container = make_async_container(
        TestApplicationProvider(),
        RequestProvider(),
        UsecaseProvider(),
    )

    app = get_fastapi_app()
    fastapi_integration.setup_dishka(container=test_container, app=app)
    yield app

    await test_container.close()


@pytest.fixture(scope='function')
async def test_client(test_app) -> AsyncGenerator[AsyncClient]:
    """Create test client with overridden dependencies."""

    async with (
        LifespanManager(test_app) as manager,
        AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url=BASE_URL,
            follow_redirects=True,
        ) as client,
    ):
        yield client


@pytest.fixture(scope='function')
def schema_fixture(test_app: FastAPI) -> Generator[BaseOpenAPISchema]:
    """Load OpenAPI schema once for all tests in this module."""
    yield schemathesis.openapi.from_asgi('/openapi.json', test_app)
