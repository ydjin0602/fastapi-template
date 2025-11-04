from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.user_crud import UserCRUD
from app.api.v1.schemas.user_schema import DeleteUserSchema


class DeleteUserUsecase(
    Usecase[
        DeleteUserSchema,
        None,
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
        data: DeleteUserSchema,
    ) -> None:
        """Delete user."""
        await self.user_crud.delete(
            _id=data.id,
        )
