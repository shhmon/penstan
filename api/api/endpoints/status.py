from fastapi import APIRouter, Depends
from penstan.settings import Settings, get_settings

router = APIRouter()

@router.get('')
async def status(settings: Settings = Depends(get_settings)) -> dict:
    return {
        'healthy': True,
        'app_version': settings.APP_VERSION,
    }

