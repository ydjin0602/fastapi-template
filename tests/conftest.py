"""Base configuration for schemathesis tests with testcontainers and dishka integration."""

import os

# Окружение для тестов. ВАЖНО: выставляем ДО импорта app.* — иначе app.config
# проинициализируется со значением из .env (или упадет без него)
os.environ['COMMON__ENVIRONMENT'] = 'PYTEST'

from collections.abc import AsyncGenerator
from collections.abc import Generator

import pytest
import schemathesis
import uvicorn

from alembic.config import Config as AlembicConfig
from asgi_lifespan import LifespanManager
from dishka import Provider
from dishka import Scope
from dishka import make_async_container
from dishka import provide
from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient
from schemathesis.schemas import BaseSchema
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.api.di.application import ApplicationProvider
from app.api.di.request import RequestProvider
from app.api.di.usecase import UsecaseProvider
from app.api.utils.sqlalchemy.base_db_model import BaseDBModel
from app.main import get_fastapi_app
from tests.consts import BASE_URL


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


@pytest.fixture(scope='function')
async def test_app(
    pg_engine: AsyncEngine,
    db_init,
) -> AsyncGenerator[FastAPI]:
    """Create test FastAPI app."""

    class TestApplicationProvider(Provider):
        """Test provider that overrides database engine for testing."""

        scope = Scope.APP

        @provide(override=True)
        async def pg_engine_scope(self) -> AsyncGenerator[AsyncEngine]:
            """Override DI scope to use test engine from fixture."""
            yield pg_engine

    # Берем реальные провайдеры приложения (redis/kafka-провайдеры ленивые —
    # без обращения к ним ничего не поднимают) и подменяем только движок БД
    test_container = make_async_container(
        ApplicationProvider(),
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
def schema_fixture() -> Generator[BaseSchema]:
    """OpenAPI-схема приложения для schemathesis."""
    yield schemathesis.openapi.from_dict(get_fastapi_app().openapi())


@pytest.fixture(scope='session')
async def live_server_url(
    pg_container_url: str,
    db_init,
) -> AsyncGenerator[str]:
    """Живой uvicorn-сервер для schemathesis-тестов.

    schemathesis вызывает ASGI-приложения в собственном event loop, а asyncpg-пул
    привязан к loop'у, в котором создан. Поэтому для schemathesis поднимаем
    реальный сервер: его движок БД создается и закрывается внутри event loop
    сервера, а запросы идут по HTTP.
    """
    import asyncio
    import threading

    class LiveServerProvider(Provider):
        """Провайдер движка для live-сервера (создается в loop'е сервера)."""

        scope = Scope.APP

        @provide(override=True)
        async def pg_engine_scope(self) -> AsyncGenerator[AsyncEngine]:
            engine = create_async_engine(pg_container_url)
            yield engine
            await engine.dispose()

    container = make_async_container(
        ApplicationProvider(),
        LiveServerProvider(),
        RequestProvider(),
        UsecaseProvider(),
    )
    app = get_fastapi_app()
    fastapi_integration.setup_dishka(container=container, app=app)

    server = uvicorn.Server(
        uvicorn.Config(app, host='127.0.0.1', port=0, log_level='warning'),
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:  # noqa: ASYNC110 — Event не безопасен между потоками
        await asyncio.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f'http://127.0.0.1:{port}'
    server.should_exit = True
    thread.join(timeout=10)


#####################################################################
# Фикстуры pytest-alembic (тесты миграций, см. tests/api/utils/test_migrations.py)
#####################################################################
@pytest.fixture(scope='function')
def alembic_db_urls(pg_container_url: str) -> Generator[tuple[str, str]]:
    """Отдельная БД для тестов миграций (в том же контейнере).

    API-тесты создают таблицы через metadata.create_all — если гонять миграции
    в той же БД, init-миграция упадет с "already exists". Поэтому на каждый
    тест создаем чистую БД. Возвращаем (asyncpg_url, psycopg_url).
    """
    sync_url = pg_container_url.replace('+asyncpg', '+psycopg')
    admin_engine = create_engine(sync_url, isolation_level='AUTOCOMMIT')
    with admin_engine.connect() as conn:
        conn.execute(text('DROP DATABASE IF EXISTS alembic_test'))
        conn.execute(text('CREATE DATABASE alembic_test'))
    admin_engine.dispose()
    yield (
        pg_container_url.rsplit('/', 1)[0] + '/alembic_test',
        sync_url.rsplit('/', 1)[0] + '/alembic_test',
    )
    admin_engine = create_engine(sync_url, isolation_level='AUTOCOMMIT')
    with admin_engine.connect() as conn:
        conn.execute(text('DROP DATABASE alembic_test WITH (FORCE)'))
    admin_engine.dispose()


@pytest.fixture
def alembic_config(alembic_db_urls) -> AlembicConfig:
    """Конфиг алембика поверх тестового контейнера.

    env.py берет sqlalchemy.url из конфига, если он не пустой —
    поэтому миграции пойдут в тестовый PG-контейнер.
    """
    alembic_config = AlembicConfig('alembic.ini')
    alembic_config.set_main_option('sqlalchemy.url', alembic_db_urls[0])
    return alembic_config


@pytest.fixture
def alembic_engine(alembic_db_urls):
    """Sync-движок для pytest-alembic (сам плагин работает только синхронно).

    Миграции при этом выполняются через env.py на asyncpg-движке,
    а этот движок нужен только для сравнения DDL (autogenerate diff).
    """
    engine = create_engine(alembic_db_urls[1])
    try:
        yield engine
    finally:
        engine.dispose()
