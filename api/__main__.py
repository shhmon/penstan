import uvicorn
from penstan.app import create_app
from penstan.logs import get_log_config
from penstan.settings import get_settings

settings = get_settings()
app = create_app()

if __name__ == '__main__':
    uvicorn.run(
        "penstan.__main__:app",
        reload=settings.RELOAD,

        # network
        host="0.0.0.0",
        port=settings.PORT,
        proxy_headers=True,

        # logging
        log_level=settings.LOG_LEVEL.lower(),
        log_config=get_log_config(),
    )
