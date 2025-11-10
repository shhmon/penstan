import json
from typing import Dict, Optional
from pydantic import StrictStr
from fastapi import HTTPException, Header, Query, status
from penstan.settings import get_settings

# api key cache
__keys: Optional[Dict[str, str]] = None

async def api_key_dependency(
    api_key_header: StrictStr | None = Header(None, alias="X-API-Key"),
    api_key_query: StrictStr | None = Query(None, alias="api_key")
) -> None:
    api_key = api_key_header or api_key_query
    if not api_key or not validate_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

def validate_api_key(api_key: str) -> bool:
    global __keys
    if __keys is None:
        __keys = read_api_keys()
    return api_key in __keys


def add_api_key(api_key: str, owner: str) -> None:
    global __keys
    if __keys is None:
        __keys = read_api_keys()
    __keys[api_key] = owner


def read_api_keys() -> Dict[str, str]:
    """
    Read dict of valid API keys from the /etc/penstan/keys file

    Returns:
        Dict of valid API keys.
    """
    settings = get_settings()
    with open(settings.API_KEY_PATH, encoding='utf-8') as key_file:
        keys: Dict[str, str] = json.load(key_file)
        # reverse keys and values for more convenient lookups
        return {key: identifier for identifier, key in keys.items()}
