from collections.abc import AsyncGenerator

from dishka import Provider
from dishka import Scope
from dishka import provide
from faststream.confluent import KafkaBroker
from redis.asyncio import ConnectionPool
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
            isolation_level='AUTOCOMMIT',
            # echo=True,
        )
        yield engine
        await engine.dispose()

    # FIXME: Redis не нужен — удали этот скоуп, redis_scope из request.py
    #  и секцию RedisSettings из config.py
    @provide
    async def redis_pool_scope(self) -> AsyncGenerator[ConnectionPool]:
        """DI Scope для Redis ConnectionPool."""
        pool = ConnectionPool(
            host=config.redis.host,
            port=config.redis.port,
            username=config.redis.username,
            password=config.redis.password,
            decode_responses=True,
            max_connections=config.redis.max_connections,
        )
        yield pool
        await pool.disconnect()

    # FIXME: Kafka не нужен — удали этот скоуп, блок в app/main.py
    #  и секцию KafkaSettings из config.py
    @provide
    async def kafka_broker_scope(self) -> KafkaBroker:
        """DI Scope для KafkaBroker."""
        return KafkaBroker(
            bootstrap_servers=config.kafka.bootstrap_servers,
            # allow_auto_create_topics=False,
        )
