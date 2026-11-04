"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from pydantic import Field

from app.api.v1.schemas.base_schema import BaseSchema
from app.api.v1.schemas.base_schema import StrictDatetime


class CreateUserSchema(BaseSchema):
    # pattern отсекает NUL-байты и контрол-символы: PG VARCHAR их не принимает,
    # иначе получим 500 из БД (ловится schemathesis-тестами)
    user_name: str = Field(min_length=1, pattern=r'^[^\x00-\x1f]*$')
    # Границы соответствуют int32 (PG Integer, см. IdPath в base_schema.py)
    role_id: int = Field(ge=1, le=2_147_483_647)


class UserSchema(BaseSchema):
    id: int
    created_at: StrictDatetime
    updated_at: StrictDatetime | None
    # Границы должны совпадать с CreateUserSchema, иначе короткое имя
    # сохранится в БД, но ответ упадет с 500 на валидации response-модели
    user_name: str = Field(min_length=1)


class GetUserByIdSchema(BaseSchema):
    id: int


class DeleteUserSchema(BaseSchema):
    id: int
