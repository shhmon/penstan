from fastapi.routing import APIRouter
from penstan.api.endpoints.volume import router as volume_router

api_router = APIRouter(prefix='/api')

api_router.include_router(
    volume_router,
    prefix='/volume',
    tags=['volume'],
)

