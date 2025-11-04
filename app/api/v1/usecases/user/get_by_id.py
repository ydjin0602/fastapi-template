from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.user_crud import UserCRUD
from app.api.v1.models import UserModel
from app.api.v1.schemas.user_schema import GetUserByIdSchema


class GetUserByIdUsecase(
    Usecase[
        GetUserByIdSchema,
        UserModel,
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
        data: GetUserByIdSchema,
    ) -> UserModel:
        """Get user by id."""
        return await self.user_crud.get(
            _id=data.id,
        )
