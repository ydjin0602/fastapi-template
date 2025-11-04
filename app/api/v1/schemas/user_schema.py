"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from pydantic import Field

from app.api.v1.schemas.base_schema import BaseSchema
from app.api.v1.schemas.base_schema import StrictDatetime


class CreateUserSchema(BaseSchema):
    user_name: str
    role_id: int


class UserSchema(BaseSchema):
    id: int
    created_at: StrictDatetime
    updated_at: StrictDatetime | None
    user_name: str = Field(min_length=6)


class GetUserByIdSchema(BaseSchema):
    id: int


class DeleteUserSchema(BaseSchema):
    id: int
