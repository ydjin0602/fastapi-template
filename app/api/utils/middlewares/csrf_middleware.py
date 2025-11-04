from __future__ import annotations

import typing as t
import uuid

from collections.abc import Sequence
from http import HTTPMethod

from starlette import status
from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from app.config import config


class CSRFMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _get_new_token() -> str:
        return str(uuid.uuid4())

    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: t.Sequence[str],
        cookie_name: str = config.auth.csrf_cookie_name,
        header_name: str = config.auth.csrf_header_name,
        max_age: int = config.auth.csrf_expire_time,
        allow_header_param: bool = True,
        allow_form_param: bool = False,
        **kwargs,
    ) -> None:
        assert isinstance(allowed_hosts, Sequence), (
            'allowed_hosts must be a sequence (list or tuple)'
        )

        self.allowed_hosts = allowed_hosts
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.max_age = max_age
        self.allow_header_param = allow_header_param
        self.allow_form_param = allow_form_param
        super().__init__(app, **kwargs)

    def _is_valid_referer(self, request: Request) -> bool:
        url = URL(request.headers.get('origin') or request.headers.get('referer') or '')
        return url.hostname in self.allowed_hosts if url.hostname else False

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Генерируем новый CSRF токен на каждый SAFE_HTTP_METHODS.

        Для любого другого метода проверяем CSRF.
        """
        if HTTPMethod(request.method) in config.auth.safe_http_methods:
            token = request.cookies.get(self.cookie_name, None)
            token_required = token is None

            if token_required:
                token = self._get_new_token()

            request.scope.update(
                {
                    'csrftoken': token,
                    'csrf_cookie_name': self.cookie_name,
                }
            )
            response = await call_next(request)

            if token_required and token:
                response.set_cookie(
                    self.cookie_name,
                    token,
                    max_age=self.max_age,
                )
            return response

        cookie_token = request.cookies.get(self.cookie_name)
        if not cookie_token:
            return Response(
                'No CSRF cookie found', status_code=status.HTTP_403_FORBIDDEN
            )

        header_token = (
            request.headers.get(self.header_name) if self.allow_header_param else None
        )

        if not self.allow_form_param or header_token:
            form_data = await request.form()
            form_token = form_data.get(self.cookie_name, None)
            request.scope.update({'form': form_data})
        else:
            form_token = None

        if not header_token and not form_token:
            return Response(
                'CSRF токен не найден ни в данных формы, ни в заголовках запроса',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if (header_token and (cookie_token != header_token)) or (
            form_token and (cookie_token != form_token)
        ):
            return Response(
                'CSRF токен в заголовке или форме не соответствует токену в куках',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if request.base_url.is_secure and not self._is_valid_referer(request):
            return Response(
                'Referrer или origin некорректны',
                status_code=status.HTTP_403_FORBIDDEN,
            )

        request.scope.update(
            {
                'csrftoken': cookie_token,
                'csrf_cookie_name': self.cookie_name,
            }
        )

        return await call_next(request)
