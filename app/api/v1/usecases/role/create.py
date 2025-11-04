from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.role_crud import RoleCRUD
from app.api.v1.models import UserRoleModel
from app.api.v1.schemas.role_schema import CreateRoleSchema


class CreateRoleUsecase(
    Usecase[
        CreateRoleSchema,
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
        data: CreateRoleSchema,
    ) -> UserRoleModel:
        """Create role."""
        return await self.role_crud.create(
            obj_in=data,
        )
