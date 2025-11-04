"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from app.api.v1.schemas.base_schema import BaseSchema
from app.api.v1.schemas.base_schema import StrictDatetime


class CreateRoleSchema(BaseSchema):
    role_name: str


class RoleSchema(BaseSchema):
    id: int
    role_name: str
    created_at: StrictDatetime


class GetRoleByIdSchema(BaseSchema):
    id: int
