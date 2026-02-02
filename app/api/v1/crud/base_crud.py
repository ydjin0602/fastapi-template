from collections.abc import Sequence
from typing import Any
from typing import get_args

from asyncpg import ForeignKeyViolationError
from asyncpg import UniqueViolationError
from pydantic import BaseModel
from sqlalchemy import Row
from sqlalchemy import RowMapping
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.exceptions import DatabaseError
from app.api.utils.exceptions import NotFoundError
from app.api.utils.exceptions import UniqueError
from app.api.utils.sqlalchemy.base_db_model import BaseDBModel

type ModelType = BaseDBModel
type CreateSchemaType = BaseModel
type UpdateSchemaType = BaseModel


class BaseCRUD[ModelT: ModelType]:
    model: type[ModelT]

    def __new__(
        cls,
        *args,
        **kwargs,
    ) -> 'BaseCRUD':
        """Создаем и инициализируем инстанс, прокидывая модель."""
        instance = super().__new__(cls)

        instance.model = get_args(cls.__orig_bases__[0])[0]  # type: ignore
        return instance

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def get(self, _id: Any) -> ModelType:
        """Получаем элемент по айди.

        Args:
            _id: Any

        Returns:
            Row | RowMapping

        Raises:
            NotFoundError
        """
        stmt = await self.db.execute(select(self.model).where(self.model.id == _id))
        result = stmt.scalars().first()

        if not result:
            raise NotFoundError(
                message=f'Запись {self.model.__tablename__} не найдена!',
            )
        return result

    async def get_multi(
        self, *, offset: int | None = None, limit: int | None = None
    ) -> Sequence[Row | RowMapping | Any]:
        """Получаем множество элементов c пагинацией.

        Args:
            offset: int - оффсет
            limit: int - ограничение выборки

        Returns:
            Sequence[Row | RowMapping | Any]
        """
        stmt = select(self.model)

        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        data = await self.db.execute(stmt)
        return data.scalars().all()

    async def create(
        self,
        *,
        obj_in: CreateSchemaType,
        exclude: Sequence[str] | None = None,
        by_alias: bool = False,
    ) -> ModelType:
        """Создаем запись в БД.

        Args:
            obj_in: CreateSchemaType
            exclude: set - исключаемые поля
            by_alias: bool - сериализация схемы по alias

        Returns:
             Row | RowMapping

        Raises:
            UniqueError, NotFoundError, DatabaseError
        """
        try:
            db_object = await self.db.execute(
                insert(self.model).values(
                    **(
                        obj_in.model_dump(
                            exclude_none=True, exclude=exclude, by_alias=by_alias
                        )
                    )
                )
            )
            await self.db.flush()
            refresh_object = await self.get(_id=db_object.inserted_primary_key[0])
            return refresh_object

        except IntegrityError as e:
            match e.orig.sqlstate:
                case UniqueViolationError.sqlstate:
                    raise UniqueError(model_name=self.model.__name__) from e
                case ForeignKeyViolationError.sqlstate:
                    raise NotFoundError(
                        message='Вы пытаетесь связать поля c несуществующими '
                        'значениями FK!',
                    ) from e
                case _:
                    raise DatabaseError(
                        message=str(e.orig),
                    ) from e

    async def update(
        self,
        *,
        _id: int,
        obj_in: UpdateSchemaType,
        except_fields: list[str] | None = None,
        only_fields: list[str] | None = None,
    ) -> ModelType | None:
        """Обновляем запись по айди.

        Args:
            _id: int - айди поля
            obj_in: - схема c данными для обновления
            except_fields: list[str] | None - поля, которые необходимо проигнорировать
            only_fields: list[str] | None - поля, которые необходимо включить
        Returns:
            Row | RowMapping

        Raises:
            NotFoundError, UniqueError, DatabaseError
        """
        await self.get(_id=_id)

        try:
            stmt = (
                update(self.model)
                .where(self.model.id == _id)
                .values(
                    **obj_in.model_dump(
                        exclude_unset=True, include=only_fields, exclude=except_fields
                    )
                )
                .returning(self.model)
            )
            payload = await self.db.execute(stmt)
            await self.db.flush()
            return payload.scalars().first()
        except IntegrityError as e:
            match e.orig.sqlstate:
                case ForeignKeyViolationError.sqlstate:
                    raise NotFoundError(
                        message='Вы пытаетесь прикрепить foreign key к таблице, '
                        'в которой нет такого id',
                    ) from e
                case UniqueViolationError.sqlstate:
                    raise UniqueError(model_name=self.model.__name__) from e
                case _:
                    raise DatabaseError(
                        message=str(e),
                    ) from e

    async def delete(self, *, _id: int) -> None:
        """Удаляем объект по айди.

        Args:
            _id: int - айди сущности в БД
        """
        result = await self.db.execute(delete(self.model).where(self.model.id == _id))
        if result.rowcount != 1:
            raise NotFoundError(message=f'Сущность {self.model.__name__} не найдена!')
        await self.db.flush()
