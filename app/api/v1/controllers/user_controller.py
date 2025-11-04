"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from typing import Any

from dishka import FromDishka as Depends
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_409_CONFLICT

from app.api.utils.swagger.default_response import get_responses
from app.api.v1.schemas.user_schema import CreateUserSchema
from app.api.v1.schemas.user_schema import DeleteUserSchema
from app.api.v1.schemas.user_schema import GetUserByIdSchema
from app.api.v1.schemas.user_schema import UserSchema
from app.api.v1.usecases.user.create import CreateUserUsecase
from app.api.v1.usecases.user.delete import DeleteUserUsecase
from app.api.v1.usecases.user.get_all import GetAllUsersUsecase
from app.api.v1.usecases.user.get_by_id import GetUserByIdUsecase

router = APIRouter(
    route_class=DishkaRoute,
)


@router.get(
    '/',
    response_model=list[UserSchema],
    name='Получить всех пользователей',
    description='Получить список всех пользователей системы с полной информацией о'
    ' каждом пользователе включая идентификатор, имя пользователя и email',
)
async def get_all_users(
    usecase: Depends[GetAllUsersUsecase],
) -> Any:
    return await usecase()


@router.get(
    '/{user_id}',
    response_model=UserSchema,
    name='Получить пользователя по ID',
    description='Получить детальную информацию о пользователе по его уникальному'
    ' идентификатору. Возвращает все данные пользователя включая имя,'
    ' email и дату создания',
    responses=get_responses(include_statuses=[HTTP_404_NOT_FOUND]),
)
async def get_user_by_id(
    user_id: int,
    usecase: Depends[GetUserByIdUsecase],
) -> Any:
    return await usecase(
        data=GetUserByIdSchema(
            id=user_id,
        ),
    )


@router.post(
    '/',
    response_model=UserSchema,
    name='Создать пользователя',
    description='Создать нового пользователя в системе. Необходимо указать уникальное'
    ' имя пользователя, email адрес и пароль. Пароль будет автоматически'
    ' хеширован перед сохранением в базу данных',
    responses=get_responses(include_statuses=[HTTP_409_CONFLICT]),
)
async def create_user(
    body: CreateUserSchema,
    usecase: Depends[CreateUserUsecase],
) -> Any:
    return await usecase(data=body)


@router.delete(
    '/{user_id}',
    status_code=HTTP_204_NO_CONTENT,
    name='Удалить пользователя',
    description='Удалить пользователя из системы по его уникальному идентификатору.'
    ' Действие необратимо - все данные пользователя будут безвозвратно'
    ' удалены',
)
async def delete_user(
    user_id: int,
    usecase: Depends[DeleteUserUsecase],
) -> None:
    await usecase(
        data=DeleteUserSchema(
            id=user_id,
        ),
    )
