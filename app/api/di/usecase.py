from dishka import Provider
from dishka import Scope
from dishka import provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.usecases.role.create import CreateRoleUsecase
from app.api.v1.usecases.role.get_all import GetAllRolesUsecase
from app.api.v1.usecases.role.get_by_id import GetRoleByIdUsecase
from app.api.v1.usecases.user.create import CreateUserUsecase
from app.api.v1.usecases.user.delete import DeleteUserUsecase
from app.api.v1.usecases.user.get_all import GetAllUsersUsecase
from app.api.v1.usecases.user.get_by_id import GetUserByIdUsecase


class UsecaseProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def create_user_usecase_scope(
        self,
        session: AsyncSession,
    ) -> CreateUserUsecase:
        """DI Scope для CreateUserUsecase."""
        return CreateUserUsecase(session=session)

    @provide
    async def delete_user_usecase_scope(
        self,
        session: AsyncSession,
    ) -> DeleteUserUsecase:
        """DI Scope для DeleteUserUsecase."""
        return DeleteUserUsecase(session=session)

    @provide
    async def get_all_users_usecase_scope(
        self,
        session: AsyncSession,
    ) -> GetAllUsersUsecase:
        """DI Scope для GetAllUsersUsecase."""
        return GetAllUsersUsecase(session=session)

    @provide
    async def get_user_by_id_usecase_scope(
        self,
        session: AsyncSession,
    ) -> GetUserByIdUsecase:
        """DI Scope для GetUserByIdUsecase."""
        return GetUserByIdUsecase(session=session)

    @provide
    async def create_role_usecase_scope(
        self,
        session: AsyncSession,
    ) -> CreateRoleUsecase:
        """DI Scope для CreateRoleUsecase."""
        return CreateRoleUsecase(session=session)

    @provide
    async def get_all_roles_usecase_scope(
        self,
        session: AsyncSession,
    ) -> GetAllRolesUsecase:
        """DI Scope для GetAllRolesUsecase."""
        return GetAllRolesUsecase(session=session)

    @provide
    async def get_role_by_id_usecase_scope(
        self,
        session: AsyncSession,
    ) -> GetRoleByIdUsecase:
        """DI Scope для GetRoleByIdUsecase."""
        return GetRoleByIdUsecase(session=session)
