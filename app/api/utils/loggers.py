import logging
import sys
import traceback

from datetime import UTC
from datetime import datetime
from typing import Any

from loguru import logger
from orjson import orjson

from app.api.utils.enums.env_enum import EnvEnum
from app.config import config


async def init_logger() -> None:
    """Метод инициализации логеров."""

    def serialize_extra(record: Any) -> str:
        """Сериализуем дополнительную информацию.

        Args:
            record: Record - запись лога

        Returns:
            dict - словарь с выводом
        """
        exception = record['exception']
        extra = record['extra']
        exc, exc_value, tb = (None, None, None)
        if exception:
            exc, exc_value, tb = exception

            if tb:
                tb = traceback.format_tb(tb)

        subset = {
            'level': record['level'].name,
            'message': record['message'],
            'additional_data': dict(extra),
            'datetime_utc': datetime.now(tz=UTC).strftime('%d.%m.%Y, %H:%M:%S'),
            'timestamp': record['time'].timestamp(),
            'exception': str(exc),
            'exc_value': str(exc_value),
            'traceback': tb,
        }
        return orjson.dumps(subset).decode('utf-8')

    def formatter(record: Any) -> str:
        """Колбек для форматирования вывода.

        Args:
            record: Record - запись лога

        Returns:
            str - отформатированный вывод
        """
        record['extra']['serialized'] = serialize_extra(record)
        return '{extra[serialized]}\n'

    # Глушим стандартные логеры ювикорна
    logging.getLogger('uvicorn.access').handlers = []
    logging.getLogger('uvicorn.error').handlers = []
    if not config.common.human_readable_logs:
        logger.remove()
        logger.add(sys.stdout, format=formatter, level=config.common.log_level.value)

    if config.common.environment.value != EnvEnum.LOCAL.name:
        # Вырубаем стандартный стектрейс
        logging.getLogger('uvicorn.error').propagate = False
