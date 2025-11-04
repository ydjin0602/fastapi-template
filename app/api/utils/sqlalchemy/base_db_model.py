from typing import Any

from sqlalchemy.orm import DeclarativeBase


class BaseDBModel(DeclarativeBase):
    __tablename__: Any
    __table_args__: dict[str, str] | tuple = {'schema': 'template_schema'}

    # FIXME: Если ты не пишешь запросы алхимии через core синтаксис то все что ниже
    #  тебе маловероятно понадобится.

    @classmethod
    def group_by_fields(cls, exclude: list[str] | None = None) -> list:
        """Берем имена всех колонок для группировки.

        Как это использовать:
        Вместо перечисления всех полей конкретной модели в select можно выполнить
        select(*User.group_by_fields())

        Зачем это нужно?
        Например, мы захотим выполнить какую то агрегацию аля
        select(
            *User.group_by_fields(),
            func.array_agg(
                func.jsonb_build_object(
                    "Hello",
                    "World",
                )
            ).label('additional_info')
        )

        Args:
            exclude: list[str] | None исключаемые поля

        Returns:
            list[колонка]
        """

        payload = []
        if not exclude:
            exclude = []

        for column in cls.__table__.columns:
            if column.key in exclude:
                continue

            payload.append(column)

        return payload

    @classmethod
    def jsonb_build_object(
        cls,
        exclude: list[str] | None = None,
        alias: object | None = None,
    ) -> list[Any]:
        """Build jsonb object для модели.

        Продолжая тему агрегаций из метода выше:
        Мы заходим выполнить агрегацию какой-то конкретной модели, которую приджоинили
        И снова вместо перечисления всех полей модели, учитывая своеобразный синтаксис
        самого метода jsonb_build_object мы можем сделать следующее
        select(
            *User.group_by_fields(),
            func.array_agg(
                func.jsonb_build_object(
                    *UserRoles.jsonb_build_object()
                )
            ).label('additional_info')
        )

        Args:
            exclude: Исключаемые поля.
            alias: Передаем объект алиаса

        Returns:
            list[ключ колонки, колонка]
        """

        payload = []

        if not exclude:
            exclude = []

        for column in cls.__table__.columns:
            if column.key in exclude:
                continue

            payload.append(column.key)

            if alias:
                payload.append(getattr(alias, column.key))

            else:
                payload.append(column)

        return payload
