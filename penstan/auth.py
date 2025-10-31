import json
from typing import Dict, Optional
from pydantic import StrictStr
from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.param_functions import Depends
from penstan.settings import get_settings

X_API_KEY = APIKeyHeader(
    name='X-API-Key',
    scheme_name='X-API-Key',
    description='API key to authorize with.',
)

# api key cache
__keys: Optional[Dict[str, str]] = None

def api_key_header(x_api_key: StrictStr = Depends(X_API_KEY)) -> None:
    """
    Authenticate X-API-Key header.

    Args:
        x_api_key:  The API key to authenticate with.

    Raises:
        HTTPException:  If x_api_key is invalid.
    """

    if not validate_api_key(x_api_key):
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
