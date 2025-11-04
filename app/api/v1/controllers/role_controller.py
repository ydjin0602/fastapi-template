"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from collections.abc import Sequence

from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_409_CONFLICT

from app.api.utils.swagger.default_response import get_responses
from app.api.v1.models import UserRoleModel
from app.api.v1.schemas.role_schema import CreateRoleSchema
from app.api.v1.schemas.role_schema import GetRoleByIdSchema
from app.api.v1.schemas.role_schema import RoleSchema
from app.api.v1.usecases.role.create import CreateRoleUsecase
from app.api.v1.usecases.role.get_all import GetAllRolesUsecase
from app.api.v1.usecases.role.get_by_id import GetRoleByIdUsecase

router = APIRouter(
    route_class=DishkaRoute,
)


@router.get(
    '/',
    response_model=list[RoleSchema],
    name='Получить все роли',
    description='Получить список всех ролей системы с полной информацией о каждой роли'
    ' включая идентификатор, название и дату создания',
)
async def get_all_roles(
    usecase: Depends[GetAllRolesUsecase],
) -> Sequence[UserRoleModel]:
    return await usecase()


@router.get(
    '/{role_id}',
    response_model=RoleSchema,
    name='Получить роль по ID',
    description='Получить детальную информацию о роли по её уникальному идентификатору.'
    ' Возвращает все данные роли включая название и дату создания',
    responses=get_responses(
        include_statuses=[HTTP_404_NOT_FOUND],
    ),
)
async def get_role_by_id(
    role_id: int,
    usecase: Depends[GetRoleByIdUsecase],
) -> UserRoleModel | None:
    return await usecase(
        data=GetRoleByIdSchema(
            id=role_id,
        ),
    )


@router.post(
    '/',
    response_model=RoleSchema,
    name='Создать роль',
    description='Создать новую роль в системе. Необходимо указать уникальное название'
    ' роли. Роль используется для управления правами доступа пользователей',
    responses=get_responses(
        include_statuses=[HTTP_409_CONFLICT],
    ),
)
async def create_role(
    body: CreateRoleSchema,
    usecase: Depends[CreateRoleUsecase],
) -> UserRoleModel:
    return await usecase(data=body)
