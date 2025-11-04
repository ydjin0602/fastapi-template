from fastapi import APIRouter

from app.api.v1.controllers import role_controller
from app.api.v1.controllers import user_controller

ROUTER = APIRouter()
ROUTER.include_router(role_controller.router, prefix='/roles', tags=['Client|Roles'])
ROUTER.include_router(user_controller.router, prefix='/users', tags=['Client|Users'])
