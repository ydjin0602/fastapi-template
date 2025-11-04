from collections.abc import Sequence
from typing import Any
from typing import get_args

from asyncpg import ForeignKeyViolationError
from asyncpg import UniqueViolationError
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_409_CONFLICT
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

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

    async def get(
        self,
        _id: Any,
    ) -> ModelT:
        """Получаем элемент по айди.

        Args:
            _id: Any

        Returns:
            Row | RowMapping

        Raises:
            HTTPException

        """
        stmt = await self.db.execute(
            select(
                self.model,
            ).where(
                self.model.id == _id,
            )
        )
        result = stmt.scalars().first()

        if not result:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f'Запись {self.model.__tablename__} не найдена!',
            )
        return result

    async def get_multi(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> Sequence[ModelT]:
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
        exclude: set | None = None,
    ) -> ModelT:
        """Создаем запись в БД.

        Args:
            obj_in: CreateSchemaType
            exclude: set - исключаемые поля

        Returns:
             Row | RowMapping

        Raises:
            HTTPException

        """
        try:
            stmt = await self.db.execute(
                insert(
                    self.model,
                )
                .values(
                    **(
                        obj_in.model_dump(
                            exclude_none=True,
                            exclude=exclude,
                        )
                    ),
                )
                .returning(
                    self.model,
                )
            )
            await self.db.flush()
            return stmt.scalars().first()

        except IntegrityError as e:
            match e.orig.sqlstate:
                case UniqueViolationError.sqlstate:
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT,
                        detail=f'Поля переданные в модель {self.model} содержат '
                        f'неуникальные значения!',
                    ) from e
                case ForeignKeyViolationError.sqlstate:
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT,
                        detail='Вы пытаетесь связать поля c несуществующими '
                        'значениями FK!',
                    ) from e
                case _:
                    raise HTTPException(
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=str(e.orig),
                    ) from e

    async def update(
        self,
        *,
        _id: int,
        obj_in: UpdateSchemaType,
    ) -> ModelT | None:
        """Обновляем запись по айди.

        Args:
            _id: int - айди поля
            obj_in: - схема c данными для обновления

        Returns:
            Row | RowMapping

        Raises:
            HTTPException

        """
        await self.get(_id=_id)

        try:
            stmt = (
                update(self.model)
                .where(self.model.id == _id)
                .values(**obj_in.model_dump(exclude_unset=True))
                .returning(self.model)
            )
            payload = await self.db.execute(stmt)
            await self.db.flush()
            return payload.scalars().first()

        except IntegrityError as e:
            match e.orig.sqlstate:
                case ForeignKeyViolationError.sqlstate:
                    raise HTTPException(
                        status_code=HTTP_404_NOT_FOUND,
                        detail='Вы пытаетесь прикрепить foreign key к таблице, '
                        'в которой нет такого id',
                    ) from e
                case UniqueViolationError.sqlstate:
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT,
                        detail=f'Поля переданные в модель {self.model} содержат '
                        f'неуникальные значения',
                    ) from e
                case _:
                    raise HTTPException(
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=str(e),
                    ) from e

    async def delete(
        self,
        *,
        _id: int,
    ) -> None:
        """Удаляем объект по айди.

        Args:
            _id: int - айди сущности в БД

        """
        result = await self.db.execute(
            delete(
                self.model,
            ).where(
                self.model.id == _id,
            )
        )
        if result.rowcount != 1:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail='Сущность не найдена!'
            )
        await self.db.flush()
