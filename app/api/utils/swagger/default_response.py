from collections import defaultdict

from starlette import status

from app.api.v1.schemas.base_schema import ErrorSchema


def get_responses(include_statuses: list[int] | None = None) -> dict:
    """Метод для прокидывания документации для стандартных статус кодов.

    Args:
        include_statuses: list[int] - список статус кодов

    Returns:
        dict
    """
    responses: dict = defaultdict(int)

    if not include_statuses:
        include_statuses = []

    for status_code in include_statuses:
        match status_code:
            case status.HTTP_401_UNAUTHORIZED:
                responses[status_code] = {
                    'description': 'Ошибка авторизации',
                    'model': ErrorSchema,
                }
            case status.HTTP_403_FORBIDDEN:
                responses[status_code] = {
                    'description': 'Недостаточно прав для выполнения операции',
                    'model': ErrorSchema,
                }

            case status.HTTP_404_NOT_FOUND:
                responses[status_code] = {
                    'description': 'Элемент не найден',
                    'model': ErrorSchema,
                }

            case status.HTTP_409_CONFLICT:
                responses[status_code] = {
                    'description': 'Ошибка при создании элемента. Сработала валидация '
                    'на уровне логики или БД',
                    'model': ErrorSchema,
                }

            case status.HTTP_422_UNPROCESSABLE_CONTENT:
                responses[status_code] = {
                    'description': 'Ошибка валидации',
                    'model': ErrorSchema,
                }

    return responses
