"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from pydantic import Field

from app.api.v1.schemas.base_schema import BaseSchema
from app.api.v1.schemas.base_schema import StrictDatetime


class CreateRoleSchema(BaseSchema):
    # pattern отсекает NUL-байты и контрол-символы: PG VARCHAR их не принимает,
    # иначе получим 500 из БД (ловится schemathesis-тестами)
    role_name: str = Field(min_length=1, pattern=r'^[^\x00-\x1f]*$')


class RoleSchema(BaseSchema):
    id: int
    role_name: str
    created_at: StrictDatetime


class GetRoleByIdSchema(BaseSchema):
    id: int
