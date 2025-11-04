from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.role_crud import RoleCRUD
from app.api.v1.models import UserRoleModel
from app.api.v1.schemas.role_schema import GetRoleByIdSchema


class GetRoleByIdUsecase(
    Usecase[
        GetRoleByIdSchema,
        UserRoleModel,
    ],
):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.role_crud = RoleCRUD(
            db=session,
        )

    async def __call__(
        self,
        data: GetRoleByIdSchema,
    ) -> UserRoleModel:
        """Get role by id."""
        return await self.role_crud.get(_id=data.id)
