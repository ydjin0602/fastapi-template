from collections.abc import Awaitable
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from loguru import logger
from starlette import status
from starlette.requests import Request

from app.api.utils.enums.internal_exception_status_enum import InternalErrorEnum
from app.api.utils.exceptions import BaseError

type TError = BaseError


def _make_exception_handler(
    _: type[TError],
) -> Callable[[Request, TError], Awaitable[ORJSONResponse]]:
    async def exception_handler(_: Request, exc: TError) -> ORJSONResponse:
        logger.error(exc)
        return ORJSONResponse(
            status_code=exc.status_code,
            content={'message': exc.message, 'code': exc.internal_status_code},
        )

    return exception_handler


async def _unknown_exception_handler(_: Request, err: Exception) -> ORJSONResponse:
    logger.exception('Unknown error occurred', exc_info=err, extra={'error': err})
    return ORJSONResponse(
        content={
            'message': str(err),
            'code': InternalErrorEnum.INTERNAL_ERROR,
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def _validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> ORJSONResponse:
    for error in exc.errors():
        error['message'] = error.pop('msg')
    return ORJSONResponse(
        content=jsonable_encoder(
            {'message': str(exc.errors()), 'code': InternalErrorEnum.BAD_REQUEST}
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Устанавливает обработчики ошибок."""
    for exc_type in [
        BaseError,
    ]:
        app.exception_handler(exc_type)(_make_exception_handler(exc_type))
    app.exception_handler(RequestValidationError)(_validation_exception_handler)
    app.exception_handler(Exception)(_unknown_exception_handler)
