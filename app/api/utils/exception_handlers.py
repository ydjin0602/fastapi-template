from collections.abc import Awaitable
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.api.utils.enums.internal_exception_status_enum import InternalErrorEnum
from app.api.utils.exceptions import BaseError

type TError = BaseError


def _make_exception_handler(
    _: type[TError],
) -> Callable[[Request, TError], Awaitable[JSONResponse]]:
    async def exception_handler(_: Request, exc: TError) -> JSONResponse:
        logger.error(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                {'message': exc.message, 'code': exc.internal_status_code}
            ),
        )

    return exception_handler


async def _unknown_exception_handler(_: Request, err: Exception) -> JSONResponse:
    logger.exception('Unknown error occurred', exc_info=err, extra={'error': err})
    return JSONResponse(
        content=jsonable_encoder(
            {
                'message': str(err),
                'code': InternalErrorEnum.INTERNAL_ERROR,
            }
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def _validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    for error in exc.errors():
        error['message'] = error.pop('msg')
    return JSONResponse(
        content=jsonable_encoder(
            {'message': str(exc.errors()), 'code': InternalErrorEnum.BAD_REQUEST}
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def _http_exception_handler(
    _: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Приводим стандартные HTTPException к общему формату ошибок.

    Например, 400 от FastAPI на не-JSON/не-UTF8 тело запроса.
    """
    status_to_code = {
        status.HTTP_400_BAD_REQUEST: InternalErrorEnum.BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: InternalErrorEnum.UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN: InternalErrorEnum.FORBIDDEN,
        status.HTTP_404_NOT_FOUND: InternalErrorEnum.INVALID_VALUE,
    }
    return JSONResponse(
        content=jsonable_encoder(
            {
                'message': exc.detail,
                'code': status_to_code.get(
                    exc.status_code,
                    InternalErrorEnum.INTERNAL_ERROR,
                ),
            }
        ),
        status_code=exc.status_code,
        headers=getattr(exc, 'headers', None),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Устанавливает обработчики ошибок."""
    for exc_type in [
        BaseError,
    ]:
        app.exception_handler(exc_type)(_make_exception_handler(exc_type))
    app.exception_handler(RequestValidationError)(_validation_exception_handler)
    app.exception_handler(HTTPException)(_http_exception_handler)
    app.exception_handler(Exception)(_unknown_exception_handler)
