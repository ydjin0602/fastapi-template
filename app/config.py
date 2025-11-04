from http import HTTPMethod
from typing import Any

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import URL

from app.api.utils.enums.env_enum import EnvEnum
from app.api.utils.enums.log_level_enum import LogLevelEnum


class CommonSettings(BaseModel):
    project_name: str = 'template_service'
    environment: EnvEnum
    log_level: LogLevelEnum = LogLevelEnum.INFO
    human_readable_logs: bool = False
    disabled_log_endpoint: list[str] = [
        '/health',
        '/liveness',
        '/metrics',
        '/openapi.json',
        '/docs',
    ]
    logger_body_content_max_size: int = 2500
    backend_cors_origins: Any = []

    prometheus_enabled: bool = True
    struct_log: bool = True


class SwaggerSettings(BaseModel):
    doc_login: str = 'admin'
    doc_password: str = 'admin'


class AuthSettings(BaseModel):
    # FIXME: Тут должны быть переменные для авторизации
    safe_http_methods: tuple[HTTPMethod, ...] = (
        HTTPMethod.GET,
        HTTPMethod.HEAD,
        HTTPMethod.OPTIONS,
        HTTPMethod.TRACE,
    )
    csrf_expire_time: int = 31536000  # 365 * 24 * 60 * 60
    csrf_cookie_name: str = 'csrftoken'
    csrf_header_name: str = 'X-CSRFToken'


class PostgresSettings(BaseModel):
    host: str = 'localhost'
    port: int = 5432
    user: str | None = 'postgres'
    password: str | None = 'example'
    db: str | None = 'template_schema'
    database_uri: Any | None = None
    pool_size: int = 10  # Размер пула соединений алхимии
    overflow_pool_size: int = 20  # Размер очереди соединений

    @model_validator(mode='before')
    @classmethod
    def database_uri_validator(cls, data: dict) -> Any:
        """Собираем PG-URI."""

        sqlalchemy_db_uri = URL.create(
            drivername='postgresql+asyncpg',
            username=data.get('user'),
            password=data.get('password'),
            host=data.get('host'),
            port=data.get('port', 5432),
            database=data.get('db', ''),
        )

        data.update(
            {'database_uri': sqlalchemy_db_uri},
        )

        return data


class Settings(BaseSettings):
    def __init__(self, **values: Any) -> None:
        load_dotenv(find_dotenv())
        super().__init__(**values)

    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='UTF-8',
        arbitrary_types_allowed=True,
    )

    common: CommonSettings
    swagger: SwaggerSettings = SwaggerSettings()
    auth: AuthSettings = AuthSettings()
    postgres: PostgresSettings = PostgresSettings()


config = Settings()
