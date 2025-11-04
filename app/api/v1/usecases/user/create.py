from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.user_crud import UserCRUD
from app.api.v1.models import UserModel
from app.api.v1.schemas.user_schema import CreateUserSchema


class CreateUserUsecase(
    Usecase[
        CreateUserSchema,
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
        data: CreateUserSchema,
    ) -> UserModel:
        """Create user."""
        return await self.user_crud.create(
            obj_in=data,
        )
