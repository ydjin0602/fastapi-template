import contextlib
import json
import time

from collections.abc import Callable
from json import JSONDecodeError
from typing import Any
from uuid import uuid4

import loguru

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.config import config


class AsyncIteratorWrapper:
    """Делаем вместо обычного итератора - асинхронный.

    Link: https://www.python.org/dev/peps/pep-0492/#example-2
    """

    def __init__(self, obj) -> None:
        self._it = iter(obj)

    def __aiter__(self) -> object:
        return self

    async def __anext__(self) -> object:
        try:
            value = next(self._it)
        except StopIteration as e:
            raise StopAsyncIteration from e
        return value


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    """Логирование роутов фастапи.

    https://medium.com/@dhavalsavalia/fastapi-logging-middleware-logging-requests-and-responses-with-ease-and-style-201b9aa4001a
    """

    _logger: 'loguru.Logger'

    def __init__(self, app: FastAPI, *, current_logger: 'loguru.Logger') -> None:
        self._logger = current_logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Стандартный метод, который нужно имплементировать для мидлы.

        Дока - https://fastapi.tiangolo.com/tutorial/middleware/

        Args:
            request:Request - объект реквеста старлета
            call_next: Callable - вызываемая функция над реквестом. По сути вызывает
            сам контроллер
            с текущим реквестом

        Returns:
            Response - объект респонса старлета

        Raises:
            None - ничего не райзит, фукнция всегда работает, даже если внутри нее
            исключение

        """
        request_id: str = str(uuid4())
        response_dict = {}
        exception = None

        start_time = time.perf_counter()

        request_dict = await self._compile_request_log(request)

        try:
            response: Response = await call_next(request)

            # Отключаем логирование для ненужных ендпоинтов
            if any(
                [
                    endpoint in str(request.url)
                    for endpoint in config.common.disabled_log_endpoint
                ]
            ):
                return response

            response_dict['status_code'] = response.status_code
            response_dict['headers'] = self._sanitaze_log(dict(response.headers))

            # Логируем тело только для app/json
            if (
                response.headers.get('Content-Type') == 'application/json'
                # проверка на 204 статус ошибки
                and response.headers.get('content-length') is not None
            ):
                # хак, чтобы забрать тело асинхронно. Взял по ссылке из medium
                resp_body = [
                    section async for section in response.__dict__['body_iterator']
                ]
                response.__setattr__('body_iterator', AsyncIteratorWrapper(resp_body))

                try:
                    resp_body = json.loads(resp_body[0].decode())
                except (JSONDecodeError, TypeError):
                    # Ругается на тип, ожидается словарь, но это не корректно,
                    # т.к. боди может быть любым
                    resp_body = str(resp_body)  # type: ignore

                if (
                    int(response.headers['content-length'])
                    > config.common.logger_body_content_max_size
                ):
                    response_dict['body'] = {
                        'detail': f'Слишком большое тело для отображения. '
                        f'{response.headers["content-length"]} байт из доступных '
                        f'{config.common.logger_body_content_max_size}'
                    }
                else:
                    # в ответе критичных данных нет.
                    # Если нужно, можно авторизационные ручки исключить из логирования
                    response_dict['body'] = resp_body

        except Exception as e:
            exception = e

            response = ORJSONResponse(
                content={
                    'message': str(e),
                },
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            )
            response_dict['status_code'] = HTTP_500_INTERNAL_SERVER_ERROR

        execution_time = time.perf_counter() - start_time
        response_dict['time_taken'] = f'{execution_time:0.4f}s'

        response.headers['X-API-Request-ID'] = request_id

        with self._logger.contextualize(
            request=request_dict, response=response_dict, x_request_id=request_id
        ):
            if exception:
                self._logger.opt(exception=exception).error('Error log')
            else:
                self._logger.info('Access log')

        return response

    async def _compile_request_log(self, request: Request) -> dict[str, str]:
        """Собираем пейлоад для реквеста.

        Args:
            request: Request - объект реквеста старлета

        Returns:
            dict[str, str]: словарь с данными для логирования

        """
        path = request.url.path
        if request.query_params:
            path += f'?{request.query_params}'

        request_logging = {
            'method': request.method,
            'path': path,
            'ip': request.client.host,
            'headers': self._sanitaze_log(dict(request.headers)),
        }

        with contextlib.suppress(JSONDecodeError, TypeError, UnicodeDecodeError):
            body = await request.json()
            request_logging['body'] = self._sanitaze_log(body)

        return request_logging

    def _sanitaze_log(self, data: Any) -> Any:
        """Функция санитайзер. Убираем чувствительные штуки из логов.

        Args:
            data: Any - обычно словарь

        Returns:
            Any

        """
        if isinstance(data, dict):
            for key in data:
                if (
                    'password' in key
                    or 'token' in key
                    or 'authorization' in key
                    or 'set-cookie' in key
                    or 'cookie' in key
                ):
                    data[key] = '********'

        return data
