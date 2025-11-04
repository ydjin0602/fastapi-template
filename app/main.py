from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn

from dishka.integrations import fastapi as fastapi_integration
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from app.api.di import DI_CONTAINER
from app.api.router import ROUTER as FASTAPI_ROUTER
from app.api.utils.enums.env_enum import EnvEnum
from app.api.utils.exception_handlers import setup_exception_handlers
from app.api.utils.loggers import init_logger
from app.api.utils.middlewares.router_logging_middleware import RouterLoggingMiddleware
from app.api.utils.swagger.tags_metadata import get_tags_metadata
from app.config import config

# При запуске приложения нужно будет поднять 2 процесса рядом.
# Брокер тизика
# TODO: taskiq worker app.pipelines.broker:broker app.pipelines
# Шедулер тазика
# TODO: taskiq scheduler app.pipelines.broker:scheduler app.pipelines --skip-first-run


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Новый вариант евентов в фастапи. Старые стали депрекейтед.

    https://fastapi.tiangolo.com/advanced/events/#lifespan
    """

    if config.common.struct_log:
        await init_logger()

    await _warmup_dependencies()

    yield

    await app.state.dishka_container.close()


async def _warmup_dependencies() -> None:
    """Принудительная инициализация критичных зависимостей при старте."""
    # FIXME: В dishka lazy зависимости инициализируются только при первом обращении
    #  Поэтому мы принудительно инициализируем критичные зависимости при старте
    #  Например, нам важно чтобы тг бот при старте приложения привязывался за вебхук.
    #  await DI_CONTAINER.get(MyTGBot)
    pass


def get_fastapi_app(logging_middleware: bool = True) -> FastAPI:
    """Получаем объект фастапи c прогруженными роутами.

    Returns:
        FastAPI
    """
    fast_api_app = FastAPI(
        default_response_class=ORJSONResponse,
        title=config.common.project_name,
        description='Описание супер крутого микросервиса',
        openapi_tags=get_tags_metadata(),
        version='0.0.1',
        docs_url=None,
        redoc_url=None,
        debug=config.common.environment in (EnvEnum.LOCAL, EnvEnum.DEV),
        lifespan=lifespan,
    )
    setup_exception_handlers(fast_api_app)
    if logging_middleware:
        fast_api_app.add_middleware(RouterLoggingMiddleware, current_logger=logger)

    # TODO: Раскомментить при необходимости
    # Set all CORS enabled origins
    # if config.common.backend_cors_origins:
    #     fast_api_app.add_middleware(
    #         CORSMiddleware,
    #         allow_origins=[
    #             str(origin) for origin in config.common.backend_cors_origins
    #         ],
    #         allow_credentials=True,
    #         allow_methods=['*'],
    #         allow_headers=['*'],
    #     )

    # if config.common.backend_cors_origins:
    #     fast_api_app.add_middleware(
    #         CSRFMiddleware,
    #         allowed_hosts=[
    #             str(origin) for origin in config.common.backend_cors_origins
    #         ],
    #     )
    if config.common.prometheus_enabled:
        # Докуменатция по експортеру и дополнительным метрикам
        # "https://github.com/stephenhillier/starlette_exporter?tab=readme-ov-file#custom-metrics"

        from starlette_exporter import PrometheusMiddleware
        from starlette_exporter import handle_metrics
        from starlette_exporter.optional_metrics import request_body_size
        from starlette_exporter.optional_metrics import response_body_size

        fast_api_app.add_middleware(
            PrometheusMiddleware,
            # https://github.com/stephenhillier/starlette_exporter?tab=readme-ov-file#options
            app_name=config.common.project_name,
            prefix='fast_api',
            skip_paths=['/health', '/openapi.json', '/docs', '/metrics'],
            skip_methods=['OPTIONS'],
            # Ведра гистограммы
            # buckets=[
            #     0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5,
            #     10.0
            # ],
            optional_metrics=[
                response_body_size,
                request_body_size,
            ],  # можно вырубить
        )
        fast_api_app.add_route('/metrics', handle_metrics)

    fast_api_app.include_router(FASTAPI_ROUTER)

    return fast_api_app


app = get_fastapi_app()
fastapi_integration.setup_dishka(container=DI_CONTAINER, app=app)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, loop='uvloop')
