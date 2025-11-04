from fastapi import APIRouter

from app.api.utils.health_check import ROUTER as HEALTH_CHECK_ROUTER
from app.api.utils.swagger.docs import ROUTER as DOCS_ROUTER
from app.api.v1 import ROUTER as V1_API_ROUTER

ROUTER = APIRouter()

# FIXME прописать свои роутеры здесь
ROUTER.include_router(V1_API_ROUTER, prefix='/api/v1')
ROUTER.include_router(HEALTH_CHECK_ROUTER, prefix='/health', tags=['health'])
ROUTER.include_router(DOCS_ROUTER)
