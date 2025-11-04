from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette.responses import Response
from starlette.status import HTTP_200_OK

ROUTER = APIRouter(
    route_class=DishkaRoute,
)


@ROUTER.get(
    '/',
    status_code=HTTP_200_OK,
    include_in_schema=False,
)
async def default_k8s_health_check() -> Response:
    """Хелсчек для k8s. Всегда отдает OK. Нужен, чтоб понять жив ли под."""
    return Response(content='OK', status_code=HTTP_200_OK)
