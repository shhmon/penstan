from fastapi.routing import APIRouter

router = APIRouter()

@router.get('')
async def status():
    return 'hello'
