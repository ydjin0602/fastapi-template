from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.usecase import Usecase
from app.api.v1.crud.role_crud import RoleCRUD
from app.api.v1.models import UserRoleModel


class GetAllRolesUsecase(
    Usecase[
        None,
        Sequence[UserRoleModel],
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
        data: None = None,
    ) -> Sequence[UserRoleModel]:
        """Get all roles."""
        return await self.role_crud.get_multi()
