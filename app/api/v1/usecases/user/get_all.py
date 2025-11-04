from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.user_crud import UserCRUD
from app.api.v1.models import UserModel


class GetAllUsersUsecase(
    Usecase[
        None,
        Sequence[UserModel],
    ],
):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.user_crud = UserCRUD(
            db=session,
        )

    async def __call__(
        self,
        data: None = None,
    ) -> Sequence[UserModel]:
        """Get all users."""
        return await self.user_crud.get_multi()
