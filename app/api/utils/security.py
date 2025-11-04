import binascii

from base64 import b64decode
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.security.http import HTTPBase
from fastapi.security.utils import get_authorization_scheme_param
from starlette import status

from app.api.utils.exceptions import AuthenticationError
from app.api.v1.schemas.auth import HTTPBasicKeyCredentials
from app.config import config


class HTTPBasicAuth(HTTPBase):
    """HTTP Basic Key authentication."""

    def __init__(
        self,
    ) -> None:
        super().__init__(
            scheme='basic',
            scheme_name='basic',
            auto_error=True,
            description='Basic Key auth',
        )

    async def __call__(self, request: Request) -> HTTPBasicKeyCredentials:
        """Авторизует по ключу из Basic Auth."""
        authorization = request.headers.get('Authorization')
        scheme, param = get_authorization_scheme_param(authorization)
        unauthorized_headers = {'WWW-Authenticate': 'Basic'}
        if not authorization or scheme.lower() != 'basic':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Токен отсутствует',
                headers=unauthorized_headers,
            )
        invalid_user_credentials_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Некорректный API Ключ',
            headers=unauthorized_headers,
        )
        try:
            data = b64decode(param).decode('ascii')
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise invalid_user_credentials_exc  # noqa: B904
        login, separator, password = data.partition(':')
        if not separator:
            raise invalid_user_credentials_exc
        return HTTPBasicKeyCredentials(login=login, password=password)


basic_security = HTTPBasicAuth()


async def authenticate_swagger(
    credentials: Annotated[HTTPBasicKeyCredentials, Depends(basic_security)],
) -> None:
    """Basic авторизация по логину и паролю из конфига для сваггера."""
    if (
        credentials.login != config.swagger.doc_login
        or credentials.password != config.swagger.doc_password
    ):
        raise AuthenticationError(
            message='Введен неверный логин или пароль.',
        )
