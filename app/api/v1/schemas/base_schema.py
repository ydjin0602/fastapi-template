"""Базовая схема ORJSON, которую можно использовать как базовую pydantic схему."""

from datetime import datetime
from typing import Annotated
from typing import Any
from typing import TypeVar

from fastapi import Path
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import GetCoreSchemaHandler
from pydantic import TypeAdapter
from pydantic_core import CoreSchema
from pydantic_core import core_schema
from pydantic_core.core_schema import ValidationInfo

from app.api.utils.enums.internal_exception_status_enum import InternalErrorEnum


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, validate_assignment=True, from_attributes=True
    )


class ErrorSchema(BaseSchema):
    message: str = Field(description='Сообщение об ошибке')
    code: InternalErrorEnum = Field(description='Системный код ошибки')


_DATETIME_ADAPTER: TypeAdapter[datetime] = TypeAdapter(datetime)


class StrictDatetime(datetime):
    @classmethod
    def validate(cls, value: Any, _: ValidationInfo) -> datetime:
        """Валидатор datetime, больше нельзя будет инициализировать его через int."""
        if str(value).isdigit():
            raise ValueError('Не верный формат даты, попробуйте YYYY-MM-DD H:M:S!')
        return _DATETIME_ADAPTER.validate_python(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.with_info_before_validator_function(
            cls.validate, handler(Any)
        )


TWith = TypeVar('TWith')
TSchema = TypeVar('TSchema', bound=BaseSchema)

# Общий тип идентификатора в path-параметрах. Границы соответствуют int32
# (PG Integer) — если сменил PK модели (см. annotated_fields.py), поправь их
IdPath = Annotated[int, Path(ge=1, le=2_147_483_647)]


class WithSchema[TWith, TSchema](BaseSchema):
    with_data: TWith
    payload: TSchema

    model_config = ConfigDict(arbitrary_types_allowed=True)
