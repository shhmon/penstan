from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from penstan.api.endpoints.status import router as status_router
from penstan.api.router import api_router
from penstan.settings import Settings, get_settings
from penstan.auth import api_key_header

settings: Settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI(
        title='Penstan',
        servers=[{
            'url': settings.SERVER_URL
        }],
        debug=settings.DEBUG,
    )

    app.include_router(api_router, dependencies=[Depends(api_key_header)])
    app.include_router(status_router, prefix='/status')

    # Add CORS Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_URLS.split(','),
        allow_methods=['*'],
        allow_headers=['*'],
    )

    return app
