from typing import Protocol
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

TInputDTO = TypeVar('TInputDTO', contravariant=True)
TOutputDTO = TypeVar('TOutputDTO', covariant=True)


class _TransactionalMixin(Protocol):
    """Миксин для автоматических транзакций."""

    # FIXME: Это хак, для того чтобы в каждом юзкейсе отдельно не открывать транзакцию.
    #  Более того, в силу допущения случаев когда один юзкейс дергает другой юзкейс,
    #  мы избавляем каждый юзкейс от реализации логики с выяснением вложенная это
    #  транзакция или нет. Это все из-за особенностей dishka.
    #  Если вам такой хак не подходит, то используйте
    #  class Usecase(Protocol[TInputDTO, TOutputDTO]).
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        # Оборачиваем __call__ метод автоматически
        original_call = cls.__call__

        async def wrapped_call(self: 'Usecase', **kwargs) -> TOutputDTO:
            if hasattr(self, 'session') and isinstance(self.session, AsyncSession):
                if self.session.in_transaction():
                    async with self.session.begin_nested():
                        return await original_call(self, **kwargs)
                async with self.session.begin():
                    return await original_call(self, **kwargs)
            return await original_call(self, **kwargs)

        cls.__call__ = wrapped_call  # type: ignore[method-assign]


class Usecase(_TransactionalMixin, Protocol[TInputDTO, TOutputDTO]):
    """Класс - сервис, в котором будет реализован сценарий бизнес - логики.

    Предназначен для изоляции бизнес - логики от остального кода.
    """

    async def __call__(self, data: TInputDTO) -> TOutputDTO:
        """Абстрактный метод для реализации бизнес - логики."""
        pass
