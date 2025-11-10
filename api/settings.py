from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

class Settings(BaseSettings):
    SERVER_URL: str = 'http://localhost:8080'
    CORS_URLS: str = '*'
    APP_VERSION: str = ''
    API_KEY_PATH: str = 'keys.json'
    RELOAD: bool = False
    PORT: int = 8080
    LOG_LEVEL: str = 'INFO'
    DEBUG: bool = False

    class Config:
        env_file = ".env"
