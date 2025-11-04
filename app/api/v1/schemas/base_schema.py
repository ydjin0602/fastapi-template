"""Базовая схема ORJSON, которую можно использовать как базовую pydantic схему."""

from datetime import datetime
from typing import Any
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import GetCoreSchemaHandler
from pydantic.v1.datetime_parse import parse_datetime
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


class StrictDatetime(datetime):
    @classmethod
    def validate(cls, value: Any, _: ValidationInfo) -> datetime:
        """Валидатор datetime, больше нельзя будет инициализировать его через int."""
        if str(value).isdigit():
            raise ValueError('Не верный формат даты, попробуйте YYYY-MM-DD H:M:S!')
        return parse_datetime(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.with_info_before_validator_function(
            cls.validate, handler(Any), field_name=handler.field_name
        )


TWith = TypeVar('TWith')
TSchema = TypeVar('TSchema', bound=BaseSchema)


class WithSchema[TWith, TSchema](BaseSchema):
    with_data: TWith
    payload: TSchema

    model_config = ConfigDict(arbitrary_types_allowed=True)
